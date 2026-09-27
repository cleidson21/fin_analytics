from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional


class RateBasis(str, Enum):
    """Approved interpretation of a scenario return rate."""

    EFFECTIVE_ANNUAL = "EFFECTIVE_ANNUAL"


class ReturnType(str, Enum):
    """Whether the supplied expected return is nominal or real."""

    NOMINAL = "NOMINAL"
    REAL = "REAL"


class OutputMode(str, Enum):
    """Currency basis requested for future projection outputs."""

    NOMINAL = "NOMINAL"
    REAL = "REAL"


class ContributionTiming(str, Enum):
    """Approved position of contributions within each monthly cycle."""

    END_OF_MONTH = "END_OF_MONTH"


def _require_exact_date(value: object, field_name: str) -> date:
    if type(value) is not date:
        raise ValueError(f"{field_name} must be a date")
    return value


def _require_decimal(value: object, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_cent_scale(value: Decimal, field_name: str) -> None:
    if value.as_tuple().exponent < -2:
        raise ValueError(f"{field_name} must have at most two decimal places")


def _calendar_months_between(start: date, end: date) -> int:
    """Return complete monthly cycles from start's month to end's month."""

    return (end.year - start.year) * 12 + end.month - start.month


@dataclass(frozen=True)
class ProjectionAssumptions:
    """Validated, immutable inputs for a future monthly projection engine."""

    as_of_date: date
    scenario_monthly_contribution: Decimal
    expected_return_rate: Decimal
    return_type: ReturnType
    output_mode: OutputMode
    inflation_rate: Optional[Decimal] = None
    horizon_months: Optional[int] = None
    target_date: Optional[date] = None
    rate_basis: RateBasis = RateBasis.EFFECTIVE_ANNUAL
    contribution_timing: ContributionTiming = ContributionTiming.END_OF_MONTH

    def __post_init__(self) -> None:
        _require_exact_date(self.as_of_date, "as_of_date")
        self._validate_contract_enums()
        self._validate_contribution()
        self._validate_rates()
        self._validate_horizon()
        self._validate_nominal_real_matrix()

    @property
    def resolved_horizon_months(self) -> int:
        """Resolve the single approved horizon source to monthly cycles."""

        if self.horizon_months is not None:
            return self.horizon_months
        if self.target_date is None:  # Defensive; construction validation forbids this.
            raise ValueError("exactly one horizon source is required")
        return _calendar_months_between(self.as_of_date, self.target_date)

    def _validate_contract_enums(self) -> None:
        if not isinstance(self.return_type, ReturnType):
            raise ValueError("return_type must be ReturnType")
        if not isinstance(self.output_mode, OutputMode):
            raise ValueError("output_mode must be OutputMode")
        if self.rate_basis is not RateBasis.EFFECTIVE_ANNUAL:
            raise ValueError("rate_basis must be EFFECTIVE_ANNUAL")
        if self.contribution_timing is not ContributionTiming.END_OF_MONTH:
            raise ValueError("contribution_timing must be END_OF_MONTH")

    def _validate_contribution(self) -> None:
        contribution = _require_decimal(
            self.scenario_monthly_contribution,
            "scenario_monthly_contribution",
        )
        _require_cent_scale(contribution, "scenario_monthly_contribution")
        if contribution < Decimal("0"):
            raise ValueError("scenario_monthly_contribution cannot be negative")

    def _validate_rates(self) -> None:
        expected_return = _require_decimal(
            self.expected_return_rate,
            "expected_return_rate",
        )
        if expected_return <= Decimal("-1"):
            raise ValueError("expected_return_rate must be greater than -1")

        if self.inflation_rate is not None:
            inflation = _require_decimal(self.inflation_rate, "inflation_rate")
            if inflation <= Decimal("-1"):
                raise ValueError("inflation_rate must be greater than -1")

    def _validate_horizon(self) -> None:
        has_months = self.horizon_months is not None
        has_target = self.target_date is not None
        if has_months == has_target:
            raise ValueError("exactly one horizon source is required")

        if has_months:
            if type(self.horizon_months) is not int:
                raise ValueError("horizon_months must be an integer")
            if not 1 <= self.horizon_months <= 1200:
                raise ValueError("horizon_months must be between 1 and 1200")
            return

        target_date = _require_exact_date(self.target_date, "target_date")
        resolved_months = _calendar_months_between(self.as_of_date, target_date)
        if resolved_months < 1:
            raise ValueError("target_date must contain at least one projected month")
        if resolved_months > 1200:
            raise ValueError("target_date cannot exceed 1200 projected months")

    def _validate_nominal_real_matrix(self) -> None:
        if (
            self.return_type is ReturnType.REAL
            and self.output_mode is OutputMode.NOMINAL
        ):
            raise ValueError("REAL return to NOMINAL output is not supported")

        if (
            self.return_type is ReturnType.NOMINAL
            and self.output_mode is OutputMode.REAL
        ):
            if self.inflation_rate is None:
                raise ValueError("inflation_rate is required for NOMINAL to REAL")
            return

        if self.inflation_rate is not None:
            raise ValueError("inflation_rate is forbidden for this return/output mode")
