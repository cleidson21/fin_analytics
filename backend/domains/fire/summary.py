"""Pure Decimal FIRE summary mathematics locked by ADR-025."""

from dataclasses import dataclass
from decimal import Decimal, MAX_EMAX, MIN_EMIN, ROUND_CEILING, ROUND_HALF_EVEN, localcontext
from enum import Enum


MONEY_QUANTUM = Decimal("0.01")
PROGRESS_QUANTUM = Decimal("0.00000001")
DECIMAL_CALCULATION_PRECISION = 34

_ZERO = Decimal("0")
_MONEY_ZERO = Decimal("0.00")
_TWELVE = Decimal("12")


class FireSummaryStatus(str, Enum):
    """The only approved deterministic FIRE summary states."""

    ALREADY_FINANCIALLY_INDEPENDENT = "ALREADY_FINANCIALLY_INDEPENDENT"
    BELOW_FIRE_TARGET = "BELOW_FIRE_TARGET"


def _require_decimal(value: object, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_cent_scale(value: Decimal, field_name: str) -> None:
    if value.as_tuple().exponent < -2:
        raise ValueError(f"{field_name} must have at most two decimal places")


def _integer_digits(value: Decimal) -> int:
    """Return the digits required to represent a Decimal's integer magnitude."""

    if value.is_zero() or value.adjusted() < 0:
        return 1
    return value.adjusted() + 1


def _target_integer_digits(
    monthly_retirement_spending: Decimal,
    assumed_annual_withdrawal_rate: Decimal,
) -> int:
    """Conservatively budget the integral digits of annual spending divided by rate."""

    # Multiplication by twelve can add at most two integer digits.  Keep this
    # estimate independent from the caller's ambient Decimal context.
    annual_adjusted = monthly_retirement_spending.adjusted() + 2
    return max(1, annual_adjusted - assumed_annual_withdrawal_rate.adjusted() + 1)


def _working_precision(
    monthly_retirement_spending: Decimal,
    eligible_investment_wealth: Decimal,
    assumed_annual_withdrawal_rate: Decimal,
) -> int:
    """Derive a local Decimal precision budget without imposing a money cap.

    The target division can add many integral digits when a valid positive rate
    is very small. Preserve cent-level rounding authority with a 34-digit guard
    beyond the largest expected monetary magnitude.
    """

    largest_integer_magnitude = max(
        _integer_digits(monthly_retirement_spending) + 2,
        _integer_digits(eligible_investment_wealth),
        _target_integer_digits(
            monthly_retirement_spending,
            assumed_annual_withdrawal_rate,
        ),
    )
    return max(
        DECIMAL_CALCULATION_PRECISION,
        largest_integer_magnitude + 2 + DECIMAL_CALCULATION_PRECISION,
    )


def _configure_decimal_context(context, precision: int) -> None:
    context.prec = precision
    context.rounding = ROUND_HALF_EVEN
    context.Emax = MAX_EMAX
    context.Emin = MIN_EMIN
    context.clamp = 0


def _quantize_money(value: Decimal, rounding: str = ROUND_HALF_EVEN) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=rounding)


@dataclass(frozen=True)
class FireSummaryInput:
    """Validated explicit inputs to the pure FIRE summary calculation."""

    eligible_investment_wealth: Decimal
    monthly_retirement_spending: Decimal
    assumed_annual_withdrawal_rate: Decimal

    def __post_init__(self) -> None:
        wealth = _require_decimal(
            self.eligible_investment_wealth,
            "eligible_investment_wealth",
        )
        _require_cent_scale(wealth, "eligible_investment_wealth")
        if wealth < _ZERO:
            raise ValueError("eligible_investment_wealth cannot be negative")

        spending = _require_decimal(
            self.monthly_retirement_spending,
            "monthly_retirement_spending",
        )
        _require_cent_scale(spending, "monthly_retirement_spending")
        if spending <= _ZERO:
            raise ValueError("monthly_retirement_spending must be greater than zero")

        rate = _require_decimal(
            self.assumed_annual_withdrawal_rate,
            "assumed_annual_withdrawal_rate",
        )
        if rate <= _ZERO or rate >= Decimal("1"):
            raise ValueError(
                "assumed_annual_withdrawal_rate must be greater than zero and less than one"
            )


@dataclass(frozen=True)
class FireSummary:
    """Canonical deterministic FIRE summary facts without provenance or timing."""

    monthly_retirement_spending: Decimal
    annual_required_spending: Decimal
    assumed_annual_withdrawal_rate: Decimal
    fire_target: Decimal
    eligible_investment_wealth: Decimal
    gap_to_fire: Decimal
    progress_ratio: Decimal
    supported_annual_withdrawal: Decimal
    supported_monthly_withdrawal: Decimal
    status: FireSummaryStatus


class FireSummaryCalculator:
    """Calculate only the FIRE-specific facts locked by ADR-025."""

    def calculate(self, input: FireSummaryInput) -> FireSummary:
        if not isinstance(input, FireSummaryInput):
            raise TypeError("input must be FireSummaryInput")

        with localcontext() as context:
            _configure_decimal_context(
                context,
                _working_precision(
                    input.monthly_retirement_spending,
                    input.eligible_investment_wealth,
                    input.assumed_annual_withdrawal_rate,
                ),
            )

            monthly_spending = _quantize_money(input.monthly_retirement_spending)
            eligible_wealth = _quantize_money(input.eligible_investment_wealth)
            annual_required_spending = _quantize_money(monthly_spending * _TWELVE)
            raw_fire_target = (
                annual_required_spending / input.assumed_annual_withdrawal_rate
            )
            fire_target = _quantize_money(raw_fire_target, ROUND_CEILING)
            gap_to_fire = max(fire_target - eligible_wealth, _MONEY_ZERO)
            progress_ratio = (eligible_wealth / fire_target).quantize(
                PROGRESS_QUANTUM,
                rounding=ROUND_HALF_EVEN,
            )

            raw_supported_annual_withdrawal = (
                eligible_wealth * input.assumed_annual_withdrawal_rate
            )
            supported_annual_withdrawal = _quantize_money(
                raw_supported_annual_withdrawal
            )
            supported_monthly_withdrawal = _quantize_money(
                raw_supported_annual_withdrawal / _TWELVE
            )
            status = (
                FireSummaryStatus.ALREADY_FINANCIALLY_INDEPENDENT
                if eligible_wealth >= fire_target
                else FireSummaryStatus.BELOW_FIRE_TARGET
            )

            return FireSummary(
                monthly_retirement_spending=monthly_spending,
                annual_required_spending=annual_required_spending,
                assumed_annual_withdrawal_rate=input.assumed_annual_withdrawal_rate,
                fire_target=fire_target,
                eligible_investment_wealth=eligible_wealth,
                gap_to_fire=gap_to_fire,
                progress_ratio=progress_ratio,
                supported_annual_withdrawal=supported_annual_withdrawal,
                supported_monthly_withdrawal=supported_monthly_withdrawal,
                status=status,
            )
