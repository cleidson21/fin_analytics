"""ADR-023 single-tenant portfolio-source resolver.

This application service reads persisted facts only.  It deliberately has no
HTTP concerns and does not alter Planning engine mathematics.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.application.exceptions.planning_portfolio_source_error import (
    PlanningPortfolioSourceAmbiguousError,
    PlanningPortfolioSourceInconsistentError,
    PlanningPortfolioSourceUnavailableError,
)
from backend.domain.enums.provider_type import ProviderType
from backend.domains.planning.facts import InitialWealthFact
from backend.domains.planning.readers import PlanningPortfolioReadQuery
from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus
from backend.infrastructure.persistence.models.user import UserModel
from backend.infrastructure.persistence.models.wealth.portfolio_snapshot import (
    PortfolioSnapshotModel,
)


class PlanningPortfolioSourceResolver:
    """Resolve exactly one authorized MyProfit portfolio fact for an as-of date."""

    _SOURCE_TYPE = ProviderType.MYPROFIT_EVOLUCAO.value

    def __init__(self, reader: PlanningPortfolioReadQuery | None = None) -> None:
        self._reader = reader or PlanningPortfolioReadQuery()

    def resolve(
        self,
        db: Session,
        current_user_id: UUID,
        as_of_date: date,
    ) -> InitialWealthFact:
        current_user = self._as_uuid(current_user_id, "current_user_id")
        self._require_single_tenant_user(db, current_user)

        snapshots = tuple(
            db.execute(
                select(PortfolioSnapshotModel).order_by(
                    PortfolioSnapshotModel.account_id.asc(),
                    PortfolioSnapshotModel.reference_month.asc(),
                )
            ).scalars()
        )
        candidate_scopes = tuple(
            sorted(
                {
                    snapshot.account_id
                    for snapshot in snapshots
                    if snapshot.source_type == self._SOURCE_TYPE
                }
            )
        )
        if not candidate_scopes:
            raise PlanningPortfolioSourceUnavailableError(
                "No eligible investment portfolio scope is available."
            )

        runs = self._runs_by_id(db, snapshots)
        scopes = []
        for scope in candidate_scopes:
            scope_snapshots = tuple(
                snapshot
                for snapshot in snapshots
                if snapshot.account_id == scope
            )
            self._validate_scope(scope_snapshots, runs, current_user)
            scopes.append(scope)

        if len(scopes) > 1:
            raise PlanningPortfolioSourceAmbiguousError(
                "More than one eligible investment portfolio scope exists."
            )

        eligible = tuple(
            snapshot
            for snapshot in snapshots
            if snapshot.account_id == scopes[0]
            and self._is_eligible_as_of(snapshot, as_of_date)
        )
        if not eligible:
            raise PlanningPortfolioSourceUnavailableError(
                "No eligible investment portfolio snapshot is available for as_of_date."
            )

        selected = max(eligible, key=lambda snapshot: self._reference_month_key(snapshot.reference_month))
        return self._reader.initial_wealth_from_snapshot(selected)

    @staticmethod
    def _as_uuid(value: object, field_name: str) -> UUID:
        try:
            return value if isinstance(value, UUID) else UUID(str(value))
        except (TypeError, ValueError, AttributeError) as error:
            raise PlanningPortfolioSourceInconsistentError(
                f"{field_name} is not a valid UUID."
            ) from error

    def _require_single_tenant_user(self, db: Session, current_user: UUID) -> None:
        users = tuple(db.execute(select(UserModel.id)).scalars())
        if len(users) != 1:
            raise PlanningPortfolioSourceUnavailableError(
                "The single-tenant portfolio invariant is not satisfied."
            )
        if self._as_uuid(users[0], "stored_user_id") != current_user:
            raise PlanningPortfolioSourceUnavailableError(
                "The authenticated user does not own the canonical portfolio tenant."
            )

    @staticmethod
    def _runs_by_id(
        db: Session,
        snapshots: Iterable[PortfolioSnapshotModel],
    ) -> dict[str, SyncLogModel]:
        run_ids = sorted(
            {
                snapshot.run_id
                for snapshot in snapshots
                if snapshot.run_id is not None and snapshot.run_id.strip()
            }
        )
        if not run_ids:
            return {}
        runs = db.execute(
            select(SyncLogModel).where(SyncLogModel.id.in_(run_ids))
        ).scalars()
        return {run.id: run for run in runs}

    def _validate_scope(
        self,
        snapshots: Iterable[PortfolioSnapshotModel],
        runs: dict[str, SyncLogModel],
        current_user: UUID,
    ) -> None:
        for snapshot in snapshots:
            self._reference_month_key(snapshot.reference_month)
            if snapshot.source_type != self._SOURCE_TYPE:
                raise PlanningPortfolioSourceInconsistentError(
                    "Portfolio scope contains an incompatible source type."
                )
            if snapshot.run_id is None or not snapshot.run_id.strip():
                raise PlanningPortfolioSourceInconsistentError(
                    "Portfolio scope contains a snapshot without run provenance."
                )
            run = runs.get(snapshot.run_id)
            if run is None:
                raise PlanningPortfolioSourceInconsistentError(
                    "Portfolio scope contains an unknown sync run."
                )
            provider = run.provider.value if hasattr(run.provider, "value") else str(run.provider)
            status = run.status.value if hasattr(run.status, "value") else str(run.status)
            if provider != self._SOURCE_TYPE or status != SyncStatus.SUCCESS.value:
                raise PlanningPortfolioSourceInconsistentError(
                    "Portfolio scope contains a non-successful or incompatible sync run."
                )
            if self._as_uuid(run.user_id, "sync_run_user_id") != current_user:
                raise PlanningPortfolioSourceInconsistentError(
                    "Portfolio scope contains a sync run owned by another user."
                )

    @staticmethod
    def _reference_month_key(reference_month: object) -> tuple[int, int]:
        if not isinstance(reference_month, str):
            raise PlanningPortfolioSourceInconsistentError(
                "Portfolio reference_month must use YYYY-MM."
            )
        try:
            parsed = datetime.strptime(reference_month, "%Y-%m")
        except ValueError as error:
            raise PlanningPortfolioSourceInconsistentError(
                "Portfolio reference_month must use YYYY-MM."
            ) from error
        if parsed.strftime("%Y-%m") != reference_month:
            raise PlanningPortfolioSourceInconsistentError(
                "Portfolio reference_month must use YYYY-MM."
            )
        return parsed.year, parsed.month

    def _is_eligible_as_of(
        self,
        snapshot: PortfolioSnapshotModel,
        as_of_date: date,
    ) -> bool:
        reference_year, reference_month = self._reference_month_key(snapshot.reference_month)
        if (reference_year, reference_month) > (as_of_date.year, as_of_date.month):
            return False
        if not isinstance(snapshot.updated_at, datetime):
            raise PlanningPortfolioSourceInconsistentError(
                "Portfolio snapshot_version_updated_at is required."
            )
        return snapshot.updated_at.date() <= as_of_date
