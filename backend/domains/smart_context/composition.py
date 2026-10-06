from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from backend.domains.smart_context.models import RecurringIncomeDecisionState


class SmartContextFeature(str, Enum):
    PROFILE = "PROFILE"
    HOME = "HOME"
    PLANNING = "PLANNING"
    GOAL = "GOAL"
    FIRE = "FIRE"


class SmartSemanticType(str, Enum):
    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    EXTERNAL_OBSERVATION = "EXTERNAL_OBSERVATION"
    EXTERNAL_EXPECTATION = "EXTERNAL_EXPECTATION"
    ASSUMPTION = "ASSUMPTION"
    USER_OVERRIDE = "USER_OVERRIDE"


class SmartValueType(str, Enum):
    MONEY = "MONEY"
    RATIO = "RATIO"
    DATE = "DATE"
    TEXT = "TEXT"
    ENUM = "ENUM"
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"


class SmartValueOwner(str, Enum):
    PROFILE = "PROFILE"
    GOVERNED_LEDGER = "GOVERNED_LEDGER"
    FINANCIAL_HEALTH = "FINANCIAL_HEALTH"
    GOALS = "GOALS"
    PLANNING_PORTFOLIO_RESOLVER = "PLANNING_PORTFOLIO_RESOLVER"
    PLANNING = "PLANNING"
    FIRE = "FIRE"


class SmartValueSource(str, Enum):
    USER_PROFILE = "USER_PROFILE"
    GOVERNED_TRANSACTIONS = "GOVERNED_TRANSACTIONS"
    FINANCIAL_HEALTH = "FINANCIAL_HEALTH"
    GOAL = "GOAL"
    INVESTMENT_PORTFOLIO = "INVESTMENT_PORTFOLIO"
    USER_INPUT_REQUIRED = "USER_INPUT_REQUIRED"


class SmartValueKey(str, Enum):
    DECLARED_MONTHLY_GROSS_INCOME = "DECLARED_MONTHLY_GROSS_INCOME"
    CONFIRMED_RECURRING_INCOME_SOURCE = "CONFIRMED_RECURRING_INCOME_SOURCE"
    RECURRING_INCOME_REVIEW_AVAILABLE = "RECURRING_INCOME_REVIEW_AVAILABLE"
    HEALTH_MONTHLY_INCOME = "HEALTH_MONTHLY_INCOME"
    HEALTH_MONTHLY_EXPENSES = "HEALTH_MONTHLY_EXPENSES"
    HEALTH_NET_CASHFLOW = "HEALTH_NET_CASHFLOW"
    HEALTH_SAVINGS_AMOUNT = "HEALTH_SAVINGS_AMOUNT"
    HEALTH_SAVINGS_RATE = "HEALTH_SAVINGS_RATE"
    INVESTMENT_WEALTH = "INVESTMENT_WEALTH"
    GOAL_SUMMARY = "GOAL_SUMMARY"
    GOAL_NAME = "GOAL_NAME"
    GOAL_TARGET_AMOUNT = "GOAL_TARGET_AMOUNT"
    GOAL_TARGET_DATE = "GOAL_TARGET_DATE"
    GOAL_CURRENT_AMOUNT = "GOAL_CURRENT_AMOUNT"
    GOAL_PLANNED_CONTRIBUTION = "GOAL_PLANNED_CONTRIBUTION"
    GOAL_PRIORITY = "GOAL_PRIORITY"
    GOAL_STATUS = "GOAL_STATUS"
    PLANNING_CONTRIBUTION = "PLANNING_CONTRIBUTION"
    PLANNING_EXPECTED_RETURN = "PLANNING_EXPECTED_RETURN"
    PLANNING_INFLATION = "PLANNING_INFLATION"
    FIRE_RETIREMENT_SPENDING = "FIRE_RETIREMENT_SPENDING"
    FIRE_WITHDRAWAL_RATE = "FIRE_WITHDRAWAL_RATE"
    FIRE_EXPECTED_RETURN = "FIRE_EXPECTED_RETURN"
    FIRE_INFLATION = "FIRE_INFLATION"
    FIRE_CONTRIBUTION = "FIRE_CONTRIBUTION"


class SmartDefaultState(str, Enum):
    KNOWN_FACT = "KNOWN_FACT"
    SUGGESTED_REFERENCE = "SUGGESTED_REFERENCE"
    ASSUMPTION_REQUIRED = "ASSUMPTION_REQUIRED"
    USER_OVERRIDE_ACTIVE = "USER_OVERRIDE_ACTIVE"
    INCOMPLETE_OR_UNAVAILABLE = "INCOMPLETE_OR_UNAVAILABLE"


class SmartOverridePolicy(str, Enum):
    NOT_ALLOWED = "NOT_ALLOWED"
    SELECT_SOURCE = "SELECT_SOURCE"
    USE_AS_REFERENCE = "USE_AS_REFERENCE"
    SCENARIO_OVERRIDE = "SCENARIO_OVERRIDE"


class SmartUnavailableReason(str, Enum):
    NOT_DECLARED = "NOT_DECLARED"
    NO_CONFIRMED_SOURCE = "NO_CONFIRMED_SOURCE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    NO_GOALS = "NO_GOALS"
    ASSUMPTION_REQUIRED = "ASSUMPTION_REQUIRED"


class SmartFreshness(str, Enum):
    CURRENT_EVIDENCE = "CURRENT_EVIDENCE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    PARTIAL_PERIOD = "PARTIAL_PERIOD"
    CLOSED_PERIOD = "CLOSED_PERIOD"


@dataclass(frozen=True)
class SmartValueScope:
    kind: str
    reference: str | None = None


@dataclass(frozen=True)
class SmartValueEvidence:
    window_start: date
    window_end: date
    first_occurrence_date: date
    latest_occurrence_date: date
    occurrence_count: int
    distinct_month_count: int
    typical_received_amount: Decimal
    risk_flags: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.typical_received_amount) is not Decimal:
            raise TypeError("Recurring evidence money must be Decimal.")
        if type(self.risk_flags) is not tuple:
            raise TypeError("Recurring evidence risk flags must be immutable.")


SmartValueData = Decimal | date | datetime | str | bool | int


@dataclass(frozen=True)
class SmartValue:
    key: SmartValueKey
    value: SmartValueData | None
    value_type: SmartValueType
    semantic_type: SmartSemanticType
    owner: SmartValueOwner
    source: SmartValueSource
    source_label: str
    state: SmartDefaultState
    override_policy: SmartOverridePolicy
    scope: SmartValueScope | None = None
    observed_at: date | datetime | None = None
    declared_at: datetime | None = None
    reference_period: str | None = None
    freshness: SmartFreshness | None = None
    evidence: SmartValueEvidence | None = None
    confirmation_status: RecurringIncomeDecisionState | None = None
    unavailable_reason: SmartUnavailableReason | None = None
    reason: str | None = None
    offered_value: SmartValueData | None = None
    effective_value: SmartValueData | None = None
    override_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.source_label.strip():
            raise ValueError("Smart Value source_label is required.")
        if isinstance(self.value, float):
            raise TypeError("Smart Value financial authority cannot contain float.")
        if self.value is not None:
            self._validate_value_type(self.value, "value")
        if self.offered_value is not None:
            self._validate_value_type(self.offered_value, "offered_value")
        if self.effective_value is not None:
            self._validate_value_type(self.effective_value, "effective_value")
        unavailable = self.state in {
            SmartDefaultState.ASSUMPTION_REQUIRED,
            SmartDefaultState.INCOMPLETE_OR_UNAVAILABLE,
        }
        if unavailable and self.value is not None:
            raise ValueError("Unavailable Smart Values cannot carry an effective value.")
        if unavailable and self.unavailable_reason is None:
            raise ValueError("Unavailable Smart Values require an explicit reason code.")
        if not unavailable and self.unavailable_reason is not None:
            raise ValueError("Available Smart Values cannot carry an unavailable reason.")
        if self.state is SmartDefaultState.USER_OVERRIDE_ACTIVE:
            if self.offered_value is None or self.effective_value is None:
                raise ValueError(
                    "An active override must preserve offered and effective values."
                )
            if not self.override_reason:
                raise ValueError("An active override requires a reason.")
        elif any(
            item is not None
            for item in (self.offered_value, self.effective_value, self.override_reason)
        ):
            raise ValueError("Override details require USER_OVERRIDE_ACTIVE state.")

    def _validate_value_type(self, value: SmartValueData, field_name: str) -> None:
        expected = {
            SmartValueType.MONEY: Decimal,
            SmartValueType.RATIO: Decimal,
            SmartValueType.DATE: date,
            SmartValueType.TEXT: str,
            SmartValueType.ENUM: str,
            SmartValueType.BOOLEAN: bool,
            SmartValueType.INTEGER: int,
        }[self.value_type]
        if type(value) is not expected:
            raise TypeError(
                f"{field_name} must match Smart Value type {self.value_type.value}."
            )


@dataclass(frozen=True)
class SmartFeatureContext:
    feature: SmartContextFeature
    as_of_date: date
    values: tuple[SmartValue, ...]

    def __post_init__(self) -> None:
        if type(self.as_of_date) is not date:
            raise TypeError("Smart Context as_of_date must be a civil date.")
        if type(self.values) is not tuple or any(
            not isinstance(value, SmartValue) for value in self.values
        ):
            raise TypeError("Smart Context values must be an immutable Smart Value tuple.")
