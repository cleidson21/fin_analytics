from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from backend.application.dtos.cashflow_summary_dto import MonthlyFinancialMetricsDTO
from backend.application.exceptions.planning_portfolio_source_error import (
    PlanningPortfolioSourceUnavailableError,
)
from backend.application.services.income_candidate_service import (
    IncomeCandidateCollection,
    IncomeCandidateService,
)
from backend.application.services.planning_portfolio_source_resolver import (
    PlanningPortfolioSourceResolver,
)
from backend.application.services.profile_declared_context_service import (
    ProfileDeclaredContextService,
)
from backend.domains.planning.facts import GoalPlanningFact, InitialWealthFact
from backend.domains.planning.readers import (
    PlanningGoalReadQuery,
    PlanningHealthReadAdapter,
)
from backend.domains.smart_context import DeclaredFinancialContext


class ProfileSmartContextSource:
    def __init__(self, service: ProfileDeclaredContextService | None = None) -> None:
        self._service = service or ProfileDeclaredContextService()

    def read(
        self,
        db: Session,
        current_user_id: UUID,
    ) -> DeclaredFinancialContext | None:
        return self._service.get_context(db, current_user_id)


class RecurringIncomeSmartContextSource:
    def __init__(self, service: IncomeCandidateService | None = None) -> None:
        self._service = service or IncomeCandidateService()

    def read(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        as_of_date: date,
    ) -> IncomeCandidateCollection:
        return self._service.list_candidates_as_of(
            db,
            current_user_id,
            as_of_date=as_of_date,
        )


class HealthSmartContextSource:
    def __init__(self, adapter: PlanningHealthReadAdapter | None = None) -> None:
        self._adapter = adapter or PlanningHealthReadAdapter()

    def read_month(
        self,
        db: Session,
        *,
        as_of_date: date,
    ) -> MonthlyFinancialMetricsDTO | None:
        start = datetime(as_of_date.year, as_of_date.month, 1)
        if as_of_date.month == 12:
            month_end = datetime(as_of_date.year + 1, 1, 1)
        else:
            month_end = datetime(as_of_date.year, as_of_date.month + 1, 1)
        end = min(
            month_end,
            datetime.combine(as_of_date + timedelta(days=1), datetime.min.time()),
        )
        facts = tuple(self._adapter.get_monthly_facts(db, start, end))
        return facts[0] if facts else None


class GoalSmartContextSource:
    def __init__(self, reader: PlanningGoalReadQuery | None = None) -> None:
        self._reader = reader or PlanningGoalReadQuery()

    def read_owned(
        self,
        db: Session,
        current_user_id: UUID,
    ) -> tuple[GoalPlanningFact, ...]:
        return self._reader.list_goals(db, current_user_id)


class PortfolioSmartContextSource:
    def __init__(
        self,
        resolver: PlanningPortfolioSourceResolver | None = None,
    ) -> None:
        self._resolver = resolver or PlanningPortfolioSourceResolver()

    def read(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        as_of_date: date,
    ) -> InitialWealthFact | None:
        try:
            return self._resolver.resolve(db, current_user_id, as_of_date)
        except PlanningPortfolioSourceUnavailableError as error:
            # The composer resolves authenticated ownership first. At this point,
            # only the resolver's explicit no-snapshot outcomes are ordinary
            # unavailable facts; ownership failures must still fail closed.
            if str(error).startswith("No eligible investment portfolio"):
                return None
            raise
