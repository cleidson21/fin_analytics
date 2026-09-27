from datetime import datetime
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.application.dtos.cashflow_summary_dto import (
    MonthlyCashflowPeriodDTO,
    MonthlyFinancialMetricsDTO,
)
from backend.domains.health.repository import HealthFinancialQuery
from backend.domains.health.service import HistoricalFinancialMetricsService
from backend.domains.planning.facts import (
    GoalPlanningFact,
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    PlanningFactAsOf,
    PlanningFactProvenance,
)
from backend.infrastructure.persistence.models.goal import GoalModel
from backend.infrastructure.persistence.models.wealth.portfolio_snapshot import (
    PortfolioSnapshotModel,
)


def _require_decimal(value: object, field_name: str) -> Decimal:
    """Reject a broken persistence boundary instead of hiding it through coercion."""
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be supplied by persistence as Decimal")
    return value


def _optional_decimal(value: object, field_name: str) -> Optional[Decimal]:
    if value is None:
        return None
    return _require_decimal(value, field_name)


class PlanningGoalReadQuery:
    """Read Goals directly from Numeric columns without the legacy float entity path."""

    def get_goal(
        self,
        db: Session,
        goal_id: UUID,
        user_id: UUID,
    ) -> Optional[GoalPlanningFact]:
        statement = select(GoalModel).where(
            GoalModel.id == goal_id,
            GoalModel.user_id == user_id,
        )
        model = db.execute(statement).scalar_one_or_none()
        if model is None:
            return None

        return GoalPlanningFact(
            goal_id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            goal_type=model.goal_type,
            status=model.status,
            target_amount=_require_decimal(model.target_amount, "target_amount"),
            target_date=model.target_date,
            current_amount=_optional_decimal(model.current_amount, "current_amount"),
            goal_planned_monthly_contribution=_optional_decimal(
                model.monthly_contribution,
                "monthly_contribution",
            ),
            priority=model.priority,
            linked_account_id=model.linked_account_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def current_amount_as_initial_wealth(
        goal: GoalPlanningFact,
    ) -> Optional[InitialWealthFact]:
        """Explicitly select one Goal's manual current amount as an origin."""
        if goal.current_amount is None:
            return None

        return InitialWealthFact(
            source=InitialWealthSource.GOAL_CURRENT_AMOUNT,
            amount=goal.current_amount,
            as_of=PlanningFactAsOf(observed_at=goal.updated_at),
            scope=InitialWealthScope.GOAL,
            provenance=PlanningFactProvenance(
                source_table=GoalModel.__tablename__,
                source_type="USER_GOVERNED_GOAL",
                goal_id=goal.goal_id,
                created_at=goal.created_at,
                updated_at=goal.updated_at,
            ),
        )


class PlanningPortfolioReadQuery:
    """Read certified investment wealth for one explicitly selected account scope."""

    @staticmethod
    def initial_wealth_from_snapshot(
        model: PortfolioSnapshotModel,
    ) -> InitialWealthFact:
        """Build one portfolio fact without inventing a daily observation timestamp."""
        return InitialWealthFact(
            source=InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT,
            amount=_require_decimal(model.patrimonio, "patrimonio"),
            as_of=PlanningFactAsOf(reference_month=model.reference_month),
            scope=InitialWealthScope.INVESTMENT_PORTFOLIO,
            provenance=PlanningFactProvenance(
                source_table=PortfolioSnapshotModel.__tablename__,
                source_type=model.source_type,
                account_id=model.account_id,
                reference_month=model.reference_month,
                run_id=model.run_id,
                created_at=model.created_at,
                updated_at=model.updated_at,
            ),
        )

    def get_latest_investment_wealth(
        self,
        db: Session,
        account_id: str,
    ) -> Optional[InitialWealthFact]:
        if not account_id or not account_id.strip():
            raise ValueError("account_id is required")

        statement = (
            select(PortfolioSnapshotModel)
            .where(PortfolioSnapshotModel.account_id == account_id)
            .order_by(PortfolioSnapshotModel.reference_month.desc())
            .limit(1)
        )
        model = db.execute(statement).scalar_one_or_none()
        if model is None:
            return None

        return self.initial_wealth_from_snapshot(model)


class PlanningHealthReadAdapter:
    """Expose certified monthly Health metrics without querying transactions here."""

    def __init__(
        self,
        query: Optional[HealthFinancialQuery] = None,
        metrics_service: Optional[HistoricalFinancialMetricsService] = None,
    ) -> None:
        self._query = query or HealthFinancialQuery()
        self._metrics_service = metrics_service or HistoricalFinancialMetricsService()

    def get_monthly_facts(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
    ) -> Sequence[MonthlyFinancialMetricsDTO]:
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        certified_totals = self._query.get_monthly_totals(db, start_date, end_date)
        periods = [
            MonthlyCashflowPeriodDTO(
                reference_month=row["month"],
                income=_require_decimal(row["income"], "income"),
                expense=_require_decimal(row["expense"], "expense"),
            )
            for row in certified_totals
        ]
        return tuple(self._metrics_service.build(periods))
