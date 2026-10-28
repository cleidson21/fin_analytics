"""Pure Decimal tests for the R6.2 Goal progress read model."""

from decimal import Decimal, getcontext

import pytest

from backend.domains.planning.goal_progress import calculate_goal_progress


@pytest.mark.parametrize(
    ("target", "current", "expected_gap", "expected_percent"),
    [
        ("50000.00", "18500.00", "31500.00", "37.00"),
        ("50000.00", "50000.00", "0.00", "100.00"),
        ("50000.00", "60000.00", "-10000.00", "120.00"),
        ("50000.00", "0.00", "50000.00", "0.00"),
        ("10.01", "3.34", "6.67", "33.37"),
        ("32.00", "1.00", "31.00", "3.12"),
    ],
)
def test_goal_progress_preserves_signed_gap_and_uncapped_half_even_percent(
    target,
    current,
    expected_gap,
    expected_percent,
):
    result = calculate_goal_progress(Decimal(target), Decimal(current))

    assert result.gap_amount == Decimal(expected_gap)
    assert result.completion_percent == Decimal(expected_percent)


@pytest.mark.parametrize(
    ("target", "current", "expected_target", "expected_current", "expected_gap"),
    [
        (Decimal("50000.00"), None, Decimal("50000.00"), None, None),
        (None, Decimal("10.00"), None, Decimal("10.00"), None),
        (None, None, None, None, None),
        (Decimal("0.00"), Decimal("10.00"), Decimal("0.00"), Decimal("10.00"), Decimal("-10.00")),
        (Decimal("-5.00"), Decimal("10.00"), Decimal("-5.00"), Decimal("10.00"), Decimal("-15.00")),
    ],
)
def test_goal_progress_preserves_null_zero_and_nonpositive_target_semantics(
    target,
    current,
    expected_target,
    expected_current,
    expected_gap,
):
    result = calculate_goal_progress(target, current)

    assert result.target_amount == expected_target
    assert result.current_amount == expected_current
    assert result.gap_amount == expected_gap
    assert result.completion_percent is None


def test_goal_progress_supports_large_decimal_magnitude_without_losing_gap_units():
    current = Decimal("1E+100")

    result = calculate_goal_progress(Decimal("1"), current)

    assert format(result.gap_amount, "f") == f"-{'9' * 100}"
    assert format(result.completion_percent, "f") == f"1{'0' * 102}.00"


def test_goal_progress_does_not_mutate_global_decimal_context():
    before = getcontext().copy()

    calculate_goal_progress(Decimal("3.00"), Decimal("1.00"))

    after = getcontext()
    assert after.prec == before.prec
    assert after.rounding == before.rounding
    assert after.Emax == before.Emax
    assert after.Emin == before.Emin
    assert after.clamp == before.clamp


@pytest.mark.parametrize(
    ("target", "current", "expected_error"),
    [
        (1.0, Decimal("1.00"), TypeError),
        (Decimal("1.00"), 1.0, TypeError),
        (Decimal("NaN"), Decimal("1.00"), ValueError),
        (Decimal("1.00"), Decimal("Infinity"), ValueError),
    ],
)
def test_goal_progress_rejects_non_decimal_or_non_finite_values(
    target,
    current,
    expected_error,
):
    with pytest.raises(expected_error):
        calculate_goal_progress(target, current)
