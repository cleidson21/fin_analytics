from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType


class InitialWealthSource(str, Enum):
    """Approved initial-wealth origins from ADR-019."""

    GOAL_CURRENT_AMOUNT = "GOAL_CURRENT_AMOUNT"
    INVESTMENT_PORTFOLIO_SNAPSHOT = "INVESTMENT_PORTFOLIO_SNAPSHOT"
    USER_PROVIDED_SCENARIO = "USER_PROVIDED_SCENARIO"


class InitialWealthScope(str, Enum):
    """Explicit scope carried by each initial-wealth fact."""

    GOAL = "GOAL"
    INVESTMENT_PORTFOLIO = "INVESTMENT_PORTFOLIO"
    USER_PROVIDED_SCENARIO = "USER_PROVIDED_SCENARIO"


@dataclass(frozen=True)
class PlanningFactAsOf:
    """Typed temporal anchor without inventing day precision for monthly facts."""

    reference_month: Optional[str] = None
    observed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.reference_month is None and self.observed_at is None:
            raise ValueError("Planning facts require a temporal anchor")


@dataclass(frozen=True)
class PlanningFactProvenance:
    """Inspectable source identity for a Planning read fact."""

    source_table: str
    source_type: Optional[str]
    goal_id: Optional[UUID] = None
    account_id: Optional[str] = None
    reference_month: Optional[str] = None
    run_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class InitialWealthFact:
    """One explicitly selected wealth origin; never an aggregate across origins."""

    source: InitialWealthSource
    amount: Decimal
    as_of: PlanningFactAsOf
    scope: InitialWealthScope
    provenance: PlanningFactProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Initial wealth amount must be Decimal")

        expected_scope = {
            InitialWealthSource.GOAL_CURRENT_AMOUNT: InitialWealthScope.GOAL,
            InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT:
                InitialWealthScope.INVESTMENT_PORTFOLIO,
            InitialWealthSource.USER_PROVIDED_SCENARIO:
                InitialWealthScope.USER_PROVIDED_SCENARIO,
        }[self.source]
        if self.scope is not expected_scope:
            raise ValueError("Initial wealth source and scope are inconsistent")


@dataclass(frozen=True)
class GoalPlanningFact:
    """Decimal-safe, read-only Goal facts consumed by future Planning orchestration."""

    goal_id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    goal_type: GoalType
    status: GoalStatus
    target_amount: Decimal
    target_date: Optional[date]
    current_amount: Optional[Decimal]
    goal_planned_monthly_contribution: Optional[Decimal]
    priority: Optional[int]
    linked_account_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        money_fields = (
            ("target_amount", self.target_amount),
            ("current_amount", self.current_amount),
            (
                "goal_planned_monthly_contribution",
                self.goal_planned_monthly_contribution,
            ),
        )
        for field_name, value in money_fields:
            if value is not None and not isinstance(value, Decimal):
                raise TypeError(f"{field_name} must be Decimal or None")
