from __future__ import annotations

import calendar
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from backend.application.exceptions.planning_portfolio_source_error import (
    PlanningPortfolioSourceAmbiguousError,
    PlanningPortfolioSourceInconsistentError,
    PlanningPortfolioSourceUnavailableError,
)
from backend.application.services.planning_portfolio_source_resolver import (
    PlanningPortfolioSourceResolver,
)
from backend.application.services.single_tenant_user_scope import (
    SingleTenantUserScopeGuard,
)
from backend.application.services.smart_context_sources import (
    GoalSmartContextSource,
    HealthSmartContextSource,
)
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.provider_type import ProviderType
from backend.domains.planning.facts import InitialWealthScope, InitialWealthSource


_REFERENCE_MONTH = re.compile(r"^(\d{4})-(\d{2})$")


class WealthHomeAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class WealthHomeFreshness(str, Enum):
    CURRENT = "CURRENT"
    PARTIAL_PERIOD = "PARTIAL_PERIOD"
    CLOSED_PERIOD = "CLOSED_PERIOD"
    UNKNOWN = "UNKNOWN"


class WealthHomeCompleteness(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class WealthHomeSourceMetadata:
    authority: str
    reader: str
    version: str
    scope: str
    read_at: datetime
    updated_at: datetime | None
    freshness: WealthHomeFreshness
    completeness: WealthHomeCompleteness


@dataclass(frozen=True)
class WealthHomeHealthData:
    status: WealthHomeAvailability
    reference_month: str
    currency: str
    net_cashflow: Decimal | None
    reason: str | None
    source: WealthHomeSourceMetadata


@dataclass(frozen=True)
class GoalStatusCount:
    status: GoalStatus
    count: int


@dataclass(frozen=True)
class WealthHomeGoalsData:
    status: WealthHomeAvailability
    total_count: int
    by_status: tuple[GoalStatusCount, ...]
    reason: str | None
    source: WealthHomeSourceMetadata


@dataclass(frozen=True)
class WealthHomeInvestmentsData:
    status: WealthHomeAvailability
    requested_reference_month: str
    snapshot_reference_month: str | None
    currency: str
    investment_wealth: Decimal | None
    source_type: str | None
    portfolio_scope: str | None
    run_id: str | None
    reason: str | None
    source: WealthHomeSourceMetadata


@dataclass(frozen=True)
class WealthHomeData:
    contract_version: str
    status: WealthHomeAvailability
    reference_month: str
    scope: str
    generated_at: datetime
    health: WealthHomeHealthData
    goals: WealthHomeGoalsData
    investments: WealthHomeInvestmentsData


class WealthHomeReadService:
    """Compose a narrow authenticated Home read model over existing authorities."""

    def __init__(
        self,
        *,
        ownership_guard: SingleTenantUserScopeGuard | None = None,
        health_source: HealthSmartContextSource | None = None,
        goal_source: GoalSmartContextSource | None = None,
        portfolio_source_resolver: PlanningPortfolioSourceResolver | None = None,
        today: Callable[[], date] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._ownership_guard = ownership_guard or SingleTenantUserScopeGuard()
        self._health_source = health_source or HealthSmartContextSource()
        self._goal_source = goal_source or GoalSmartContextSource()
        self._portfolio_source_resolver = (
            portfolio_source_resolver or PlanningPortfolioSourceResolver()
        )
        self._today = today or date.today
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def read(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        reference_month: str,
    ) -> WealthHomeData:
        as_of_date, is_partial_period = self._resolve_as_of_date(reference_month)
        read_at = self._clock()
        if read_at.tzinfo is None or read_at.utcoffset() is None:
            raise ValueError("Wealth Home clock must return an aware datetime.")

        # Health is consolidated in the current local tenant. The exact-single-user
        # guard is therefore mandatory before any composed source can be read.
        self._ownership_guard.resolve(db, current_user_id)
        health_fact = self._health_source.read_month(db, as_of_date=as_of_date)
        goals = self._goal_source.read_owned(db, current_user_id)
        if any(goal.user_id != current_user_id for goal in goals):
            raise RuntimeError("Goal source returned a fact outside the authenticated scope.")

        health = self._health_data(
            health_fact,
            reference_month=reference_month,
            read_at=read_at,
            is_partial_period=is_partial_period,
        )
        goal_data = self._goals_data(goals, read_at=read_at)
        investments = self._investments_data(
            db,
            current_user_id,
            requested_reference_month=reference_month,
            as_of_date=as_of_date,
            read_at=read_at,
            is_partial_period=is_partial_period,
        )
        overall_status = (
            WealthHomeAvailability.AVAILABLE
            if health.status is WealthHomeAvailability.AVAILABLE
            and goal_data.status is WealthHomeAvailability.AVAILABLE
            and investments.status is WealthHomeAvailability.AVAILABLE
            else WealthHomeAvailability.INSUFFICIENT_DATA
        )

        return WealthHomeData(
            contract_version="wealth-home-v2",
            status=overall_status,
            reference_month=reference_month,
            scope="AUTHENTICATED_SINGLE_USER",
            generated_at=read_at,
            health=health,
            goals=goal_data,
            investments=investments,
        )

    def _resolve_as_of_date(self, reference_month: str) -> tuple[date, bool]:
        if type(reference_month) is not str:
            raise TypeError("reference_month must be a YYYY-MM string.")
        match = _REFERENCE_MONTH.fullmatch(reference_month)
        if match is None:
            raise ValueError("reference_month must use YYYY-MM.")

        year, month = (int(part) for part in match.groups())
        if month < 1 or month > 12:
            raise ValueError("reference_month must use a valid calendar month.")

        today = self._today()
        if type(today) is not date:
            raise TypeError("today must be a civil date.")
        requested = (year, month)
        current = (today.year, today.month)
        if requested > current:
            raise ValueError("reference_month cannot be in the future.")

        last_day = calendar.monthrange(year, month)[1]
        if requested == current:
            return today, today.day < last_day
        return date(year, month, last_day), False

    @staticmethod
    def _health_data(
        fact,
        *,
        reference_month: str,
        read_at: datetime,
        is_partial_period: bool,
    ) -> WealthHomeHealthData:
        freshness = (
            WealthHomeFreshness.PARTIAL_PERIOD
            if is_partial_period
            else WealthHomeFreshness.CLOSED_PERIOD
        )
        source = WealthHomeSourceMetadata(
            authority="FINANCIAL_HEALTH",
            reader="PlanningHealthReadAdapter",
            version="10.2",
            scope="CONSOLIDATED_LOCAL_TENANT",
            read_at=read_at,
            updated_at=None,
            freshness=freshness,
            completeness=WealthHomeCompleteness.UNKNOWN,
        )
        if fact is None:
            return WealthHomeHealthData(
                status=WealthHomeAvailability.INSUFFICIENT_DATA,
                reference_month=reference_month,
                currency="BRL",
                net_cashflow=None,
                reason="NO_CERTIFIED_HEALTH_FACT",
                source=source,
            )
        if fact.reference_month != reference_month:
            raise RuntimeError("Health source returned a mismatched reference month.")
        if not isinstance(fact.net_cashflow, Decimal):
            raise TypeError("Health net cashflow must remain Decimal.")
        return WealthHomeHealthData(
            status=WealthHomeAvailability.AVAILABLE,
            reference_month=reference_month,
            currency="BRL",
            net_cashflow=fact.net_cashflow,
            reason=None,
            source=source,
        )

    @staticmethod
    def _goals_data(goals, *, read_at: datetime) -> WealthHomeGoalsData:
        counts = Counter(goal.status for goal in goals)
        updated_at = max((goal.updated_at for goal in goals), default=None)
        by_status = tuple(
            GoalStatusCount(status=status, count=counts[status])
            for status in GoalStatus
        )
        return WealthHomeGoalsData(
            status=WealthHomeAvailability.AVAILABLE,
            total_count=len(goals),
            by_status=by_status,
            reason=None,
            source=WealthHomeSourceMetadata(
                authority="GOALS",
                reader="PlanningGoalReadQuery",
                version="10.3.1",
                scope="AUTHENTICATED_USER_OWNED_GOALS",
                read_at=read_at,
                updated_at=updated_at,
                freshness=WealthHomeFreshness.CURRENT,
                completeness=WealthHomeCompleteness.COMPLETE,
            ),
        )

    def _investments_data(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        requested_reference_month: str,
        as_of_date: date,
        read_at: datetime,
        is_partial_period: bool,
    ) -> WealthHomeInvestmentsData:
        try:
            fact = self._portfolio_source_resolver.resolve(
                db,
                current_user_id,
                as_of_date,
            )
        except PlanningPortfolioSourceUnavailableError:
            return self._unavailable_investments(
                requested_reference_month=requested_reference_month,
                read_at=read_at,
                status=WealthHomeAvailability.INSUFFICIENT_DATA,
                reason="NO_ELIGIBLE_INVESTMENT_SNAPSHOT",
            )
        except (
            PlanningPortfolioSourceAmbiguousError,
            PlanningPortfolioSourceInconsistentError,
        ):
            return self._unavailable_investments(
                requested_reference_month=requested_reference_month,
                read_at=read_at,
                status=WealthHomeAvailability.UNAVAILABLE,
                reason="INVESTMENT_SOURCE_NOT_ELIGIBLE",
            )
        except Exception:
            return self._unavailable_investments(
                requested_reference_month=requested_reference_month,
                read_at=read_at,
                status=WealthHomeAvailability.UNAVAILABLE,
                reason="INVESTMENT_SOURCE_FAILURE",
            )

        try:
            return self._available_investments(
                fact,
                requested_reference_month=requested_reference_month,
                read_at=read_at,
                is_partial_period=is_partial_period,
            )
        except (TypeError, ValueError):
            return self._unavailable_investments(
                requested_reference_month=requested_reference_month,
                read_at=read_at,
                status=WealthHomeAvailability.UNAVAILABLE,
                reason="INVESTMENT_SOURCE_NOT_ELIGIBLE",
            )

    @staticmethod
    def _available_investments(
        fact,
        *,
        requested_reference_month: str,
        read_at: datetime,
        is_partial_period: bool,
    ) -> WealthHomeInvestmentsData:
        if fact.source is not InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT:
            raise ValueError("Investment source returned an incompatible fact.")
        if fact.scope is not InitialWealthScope.INVESTMENT_PORTFOLIO:
            raise ValueError("Investment source returned an incompatible scope.")
        if not isinstance(fact.amount, Decimal) or not fact.amount.is_finite():
            raise TypeError("Investment wealth must remain a finite Decimal.")

        snapshot_month = fact.as_of.reference_month
        if (
            not isinstance(snapshot_month, str)
            or _REFERENCE_MONTH.fullmatch(snapshot_month) is None
        ):
            raise ValueError("Investment snapshot reference month is invalid.")
        snapshot_year, snapshot_month_number = (
            int(part) for part in snapshot_month.split("-")
        )
        if snapshot_month_number < 1 or snapshot_month_number > 12:
            raise ValueError("Investment snapshot reference month is invalid.")
        requested_year, requested_month_number = (
            int(part) for part in requested_reference_month.split("-")
        )
        if (snapshot_year, snapshot_month_number) > (
            requested_year,
            requested_month_number,
        ):
            raise ValueError("Investment snapshot is newer than the requested month.")

        provenance = fact.provenance
        if provenance.source_type != ProviderType.MYPROFIT_EVOLUCAO.value:
            raise ValueError("Investment snapshot source type is not eligible.")
        if not provenance.account_id or not provenance.account_id.strip():
            raise ValueError("Investment snapshot portfolio scope is missing.")
        if not provenance.run_id or not provenance.run_id.strip():
            raise ValueError("Investment snapshot run provenance is missing.")
        if provenance.reference_month != snapshot_month:
            raise ValueError("Investment snapshot provenance month is inconsistent.")
        if not isinstance(provenance.updated_at, datetime):
            raise ValueError("Investment snapshot update timestamp is missing.")

        freshness = (
            WealthHomeFreshness.PARTIAL_PERIOD
            if snapshot_month == requested_reference_month and is_partial_period
            else WealthHomeFreshness.CLOSED_PERIOD
        )
        return WealthHomeInvestmentsData(
            status=WealthHomeAvailability.AVAILABLE,
            requested_reference_month=requested_reference_month,
            snapshot_reference_month=snapshot_month,
            currency="BRL",
            investment_wealth=fact.amount,
            source_type=provenance.source_type,
            portfolio_scope=provenance.account_id,
            run_id=provenance.run_id,
            reason=None,
            source=WealthHomeSourceMetadata(
                authority="INVESTMENT_PORTFOLIO",
                reader="PlanningPortfolioSourceResolver",
                version="10.3.10B1",
                scope="AUTHENTICATED_CANONICAL_MYPROFIT_PORTFOLIO",
                read_at=read_at,
                updated_at=provenance.updated_at,
                freshness=freshness,
                completeness=WealthHomeCompleteness.UNKNOWN,
            ),
        )

    @staticmethod
    def _unavailable_investments(
        *,
        requested_reference_month: str,
        read_at: datetime,
        status: WealthHomeAvailability,
        reason: str,
    ) -> WealthHomeInvestmentsData:
        return WealthHomeInvestmentsData(
            status=status,
            requested_reference_month=requested_reference_month,
            snapshot_reference_month=None,
            currency="BRL",
            investment_wealth=None,
            source_type=None,
            portfolio_scope=None,
            run_id=None,
            reason=reason,
            source=WealthHomeSourceMetadata(
                authority="INVESTMENT_PORTFOLIO",
                reader="PlanningPortfolioSourceResolver",
                version="10.3.10B1",
                scope="AUTHENTICATED_CANONICAL_MYPROFIT_PORTFOLIO",
                read_at=read_at,
                updated_at=None,
                freshness=WealthHomeFreshness.UNKNOWN,
                completeness=WealthHomeCompleteness.UNKNOWN,
            ),
        )
