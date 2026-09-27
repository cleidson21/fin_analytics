from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, MAX_EMAX, MIN_EMIN, ROUND_HALF_EVEN, localcontext

from backend.domains.planning.assumptions import (
    OutputMode,
    ProjectionAssumptions,
    ReturnType,
)
from backend.domains.planning.facts import InitialWealthFact


DECIMAL_CALCULATION_PRECISION = 80
CENT_TRUTH_GUARD_DIGITS = 34
MONEY_DECIMAL_PLACES = 2
MAGNITUDE_SAFETY_DIGITS = 2
MONEY_QUANTUM = Decimal("0.01")

_ONE = Decimal("1")
_TWELVE = Decimal("12")
_ZERO = Decimal("0")
_MONEY_ZERO = Decimal("0.00")


@dataclass(frozen=True)
class ProjectionPeriod:
    """One complete projected calendar month."""

    period: int
    period_end: date
    opening_wealth: Decimal
    contribution: Decimal
    projected_return: Decimal
    ending_wealth: Decimal
    cumulative_contributions: Decimal
    cumulative_projected_growth: Decimal


@dataclass(frozen=True)
class ForwardProjectionResult:
    """Immutable conditional projection with its complete input audit trail."""

    initial_wealth_fact: InitialWealthFact
    assumptions: ProjectionAssumptions
    effective_projection_annual_rate: Decimal
    monthly_equivalent_rate: Decimal
    periods: tuple[ProjectionPeriod, ...]
    initial_wealth: Decimal
    final_wealth: Decimal
    total_contributions: Decimal
    total_projected_growth: Decimal
    as_of_date: date
    horizon_months: int


def _require_valid_initial_wealth(initial_wealth_fact: InitialWealthFact) -> None:
    if not isinstance(initial_wealth_fact, InitialWealthFact):
        raise TypeError("initial_wealth_fact must be InitialWealthFact")

    amount = initial_wealth_fact.amount
    if not isinstance(amount, Decimal):
        raise TypeError("initial wealth amount must be Decimal")
    if not amount.is_finite():
        raise ValueError("initial wealth amount must be finite")
    if amount < _ZERO:
        raise ValueError("initial wealth amount cannot be negative")
    if amount.as_tuple().exponent < -2:
        raise ValueError("initial wealth amount must have at most two decimal places")


def _resolve_effective_annual_rate(
    assumptions: ProjectionAssumptions,
) -> Decimal:
    if assumptions.return_type is ReturnType.NOMINAL:
        if assumptions.output_mode is OutputMode.NOMINAL:
            return assumptions.expected_return_rate

        if assumptions.output_mode is OutputMode.REAL:
            inflation_rate = assumptions.inflation_rate
            if inflation_rate is None:  # Defensive; assumptions reject this state.
                raise ValueError("inflation_rate is required for NOMINAL to REAL")
            return (
                (_ONE + assumptions.expected_return_rate)
                / (_ONE + inflation_rate)
                - _ONE
            )

    if (
        assumptions.return_type is ReturnType.REAL
        and assumptions.output_mode is OutputMode.REAL
    ):
        return assumptions.expected_return_rate

    raise ValueError("unsupported return/output mode")


def _resolve_annual_growth_factor(
    assumptions: ProjectionAssumptions,
) -> Decimal:
    """Return 1 + effective annual rate without avoidable cancellation."""

    if assumptions.return_type is ReturnType.NOMINAL:
        nominal_growth_factor = _ONE + assumptions.expected_return_rate
        if assumptions.output_mode is OutputMode.NOMINAL:
            return nominal_growth_factor

        if assumptions.output_mode is OutputMode.REAL:
            inflation_rate = assumptions.inflation_rate
            if inflation_rate is None:  # Defensive; assumptions reject this state.
                raise ValueError("inflation_rate is required for NOMINAL to REAL")
            return nominal_growth_factor / (_ONE + inflation_rate)

    if (
        assumptions.return_type is ReturnType.REAL
        and assumptions.output_mode is OutputMode.REAL
    ):
        return _ONE + assumptions.expected_return_rate

    raise ValueError("unsupported return/output mode")


def _configure_decimal_context(context, precision: int) -> None:
    """Isolate calculation settings and use Decimal's native exponent range."""

    context.prec = precision
    context.rounding = ROUND_HALF_EVEN
    context.Emax = MAX_EMAX
    context.Emin = MIN_EMIN
    context.clamp = 0


def _integer_digits(value: Decimal) -> int:
    """Return the integer digits needed for a non-negative monetary value."""

    if value.is_zero() or value < _ONE:
        return 1
    return value.adjusted() + 1


def _estimate_working_precision(
    initial_wealth: Decimal,
    assumptions: ProjectionAssumptions,
) -> int:
    """Derive a conservative precision budget from projection magnitude.

    The balance before growth is bounded by initial wealth plus every monthly
    contribution. For positive growth, each complete or partial projection
    year is conservatively bounded by the next power of ten above the annual
    growth factor. The resulting maximum integer-digit budget is extended by
    cent scale and a 34-digit guard so the monthly rate error cannot grow with
    the balance and erase cent-level truth.
    """

    horizon_months = assumptions.resolved_horizon_months
    horizon_digits = len(str(horizon_months))

    initial_digits = _integer_digits(initial_wealth)
    if assumptions.scenario_monthly_contribution.is_zero():
        contribution_total_digits = 1
    else:
        contribution_total_digits = (
            _integer_digits(assumptions.scenario_monthly_contribution)
            + horizon_digits
        )

    balance_before_growth_digits = (
        max(initial_digits, contribution_total_digits) + 1
    )

    rate_input_digits = len(assumptions.expected_return_rate.as_tuple().digits)
    if assumptions.inflation_rate is not None:
        rate_input_digits = max(
            rate_input_digits,
            len(assumptions.inflation_rate.as_tuple().digits),
        )

    estimate_precision = max(
        DECIMAL_CALCULATION_PRECISION,
        rate_input_digits + CENT_TRUTH_GUARD_DIGITS,
    )
    with localcontext() as estimate_context:
        _configure_decimal_context(estimate_context, estimate_precision)
        annual_growth_factor = _resolve_annual_growth_factor(assumptions)

    growth_digits = 0
    if annual_growth_factor > _ONE:
        projected_years_ceiling = (horizon_months + 11) // 12
        annual_factor_digit_bound = annual_growth_factor.adjusted() + 1
        growth_digits = projected_years_ceiling * annual_factor_digit_bound

    maximum_balance_digits = (
        balance_before_growth_digits
        + growth_digits
        + MAGNITUDE_SAFETY_DIGITS
    )
    return max(
        DECIMAL_CALCULATION_PRECISION,
        maximum_balance_digits
        + MONEY_DECIMAL_PLACES
        + CENT_TRUTH_GUARD_DIGITS,
    )


def _annual_to_monthly_rate(effective_annual_rate: Decimal) -> Decimal:
    if effective_annual_rate == _ZERO:
        return _ZERO

    annual_growth_factor = _ONE + effective_annual_rate
    return (annual_growth_factor.ln() / _TWELVE).exp() - _ONE


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)


def _projected_period_end(as_of_date: date, period: int) -> date:
    absolute_month = as_of_date.year * 12 + (as_of_date.month - 1) + period
    year, zero_based_month = divmod(absolute_month, 12)
    month = zero_based_month + 1
    return date(year, month, monthrange(year, month)[1])


class ForwardProjectionEngine:
    """Pure monthly Decimal projection governed by ADR-020."""

    def project(
        self,
        initial_wealth_fact: InitialWealthFact,
        assumptions: ProjectionAssumptions,
    ) -> ForwardProjectionResult:
        _require_valid_initial_wealth(initial_wealth_fact)
        if not isinstance(assumptions, ProjectionAssumptions):
            raise TypeError("assumptions must be ProjectionAssumptions")

        working_precision = _estimate_working_precision(
            initial_wealth_fact.amount,
            assumptions,
        )
        with localcontext() as context:
            _configure_decimal_context(context, working_precision)

            effective_annual_rate = _resolve_effective_annual_rate(assumptions)
            monthly_rate = _annual_to_monthly_rate(effective_annual_rate)

            opening_wealth = initial_wealth_fact.amount
            contribution = assumptions.scenario_monthly_contribution
            cumulative_contributions = _MONEY_ZERO
            cumulative_projected_growth = _MONEY_ZERO
            periods = []

            for period_number in range(1, assumptions.resolved_horizon_months + 1):
                projected_return = _quantize_money(opening_wealth * monthly_rate)
                ending_wealth = opening_wealth + projected_return + contribution
                cumulative_contributions += contribution
                cumulative_projected_growth += projected_return

                periods.append(
                    ProjectionPeriod(
                        period=period_number,
                        period_end=_projected_period_end(
                            assumptions.as_of_date,
                            period_number,
                        ),
                        opening_wealth=opening_wealth,
                        contribution=contribution,
                        projected_return=projected_return,
                        ending_wealth=ending_wealth,
                        cumulative_contributions=cumulative_contributions,
                        cumulative_projected_growth=cumulative_projected_growth,
                    )
                )
                opening_wealth = ending_wealth

            immutable_periods = tuple(periods)
            return ForwardProjectionResult(
                initial_wealth_fact=initial_wealth_fact,
                assumptions=assumptions,
                effective_projection_annual_rate=effective_annual_rate,
                monthly_equivalent_rate=monthly_rate,
                periods=immutable_periods,
                initial_wealth=initial_wealth_fact.amount,
                final_wealth=immutable_periods[-1].ending_wealth,
                total_contributions=cumulative_contributions,
                total_projected_growth=cumulative_projected_growth,
                as_of_date=assumptions.as_of_date,
                horizon_months=assumptions.resolved_horizon_months,
            )
