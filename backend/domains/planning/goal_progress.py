"""Pure Decimal Goal progress calculation for the R6.2 read model."""

from dataclasses import dataclass
from decimal import (
    Decimal,
    MAX_EMAX,
    MIN_EMIN,
    ROUND_HALF_EVEN,
    localcontext,
)


PERCENT_QUANTUM = Decimal("0.01")
DECIMAL_GUARD_DIGITS = 34

_HUNDRED = Decimal("100")
_ZERO = Decimal("0")


def _optional_finite_decimal(
    value: object | None,
    field_name: str,
) -> Decimal | None:
    if value is None:
        return None
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _integer_digits(value: Decimal) -> int:
    if value.is_zero() or value.adjusted() < 0:
        return 1
    return value.adjusted() + 1


def _fractional_places(value: Decimal) -> int:
    return max(0, -value.as_tuple().exponent)


def _working_precision(target_amount: Decimal, current_amount: Decimal) -> int:
    """Budget enough local precision for exact gap cents and an unbounded ratio."""

    gap_digits = max(
        _integer_digits(target_amount),
        _integer_digits(current_amount),
    ) + max(
        _fractional_places(target_amount),
        _fractional_places(current_amount),
    )
    percent_integer_digits = max(
        1,
        current_amount.adjusted() - target_amount.adjusted() + 3,
    )
    return max(
        DECIMAL_GUARD_DIGITS,
        gap_digits + DECIMAL_GUARD_DIGITS,
        percent_integer_digits + 2 + DECIMAL_GUARD_DIGITS,
    )


@dataclass(frozen=True)
class GoalProgressResult:
    """Immutable R6.2 operands and their deterministic derived values."""

    target_amount: Decimal | None
    current_amount: Decimal | None
    gap_amount: Decimal | None
    completion_percent: Decimal | None


def calculate_goal_progress(
    target_amount: Decimal | None,
    current_amount: Decimal | None,
) -> GoalProgressResult:
    """Calculate signed gap and uncapped percentage without global context drift."""

    target = _optional_finite_decimal(target_amount, "target_amount")
    current = _optional_finite_decimal(current_amount, "current_amount")

    if target is None or current is None:
        return GoalProgressResult(
            target_amount=target,
            current_amount=current,
            gap_amount=None,
            completion_percent=None,
        )

    with localcontext() as context:
        context.prec = _working_precision(target, current)
        context.rounding = ROUND_HALF_EVEN
        context.Emax = MAX_EMAX
        context.Emin = MIN_EMIN
        context.clamp = 0

        gap_amount = target - current
        completion_percent = None
        if target > _ZERO:
            completion_percent = ((current / target) * _HUNDRED).quantize(
                PERCENT_QUANTUM,
                rounding=ROUND_HALF_EVEN,
            )

    return GoalProgressResult(
        target_amount=target,
        current_amount=current,
        gap_amount=gap_amount,
        completion_percent=completion_percent,
    )
