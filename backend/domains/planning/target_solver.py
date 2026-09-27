from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from backend.domains.planning.assumptions import ProjectionAssumptions
from backend.domains.planning.facts import InitialWealthFact
from backend.domains.planning.projection import (
    ForwardProjectionEngine,
    ForwardProjectionResult,
)


_ZERO = Decimal("0")


class TargetAchievementStatus(str, Enum):
    """Approved mathematical states for the target-achievement solver."""

    ALREADY_ACHIEVED = "ALREADY_ACHIEVED"
    ACHIEVED = "ACHIEVED"
    UNREACHABLE = "UNREACHABLE"
    NOT_REACHED_WITHIN_HORIZON = "NOT_REACHED_WITHIN_HORIZON"


@dataclass(frozen=True)
class TargetAchievementResult:
    """Immutable target crossing result with its complete audit trail."""

    status: TargetAchievementStatus
    target_amount: Decimal
    initial_wealth_fact: InitialWealthFact
    assumptions: ProjectionAssumptions
    achievement_period: Optional[int]
    achievement_date: Optional[date]
    months_required: Optional[int]
    achieved_wealth: Optional[Decimal]
    projection_result: Optional[ForwardProjectionResult]


def _require_valid_solver_inputs(
    initial_wealth_fact: InitialWealthFact,
    assumptions: ProjectionAssumptions,
) -> None:
    if not isinstance(initial_wealth_fact, InitialWealthFact):
        raise TypeError("initial_wealth_fact must be InitialWealthFact")
    if not isinstance(assumptions, ProjectionAssumptions):
        raise TypeError("assumptions must be ProjectionAssumptions")

    amount = initial_wealth_fact.amount
    if not isinstance(amount, Decimal):
        raise TypeError("initial wealth amount must be Decimal")
    if not amount.is_finite():
        raise ValueError("initial wealth amount must be finite")
    if amount < _ZERO:
        raise ValueError("initial wealth amount cannot be negative")
    if amount.as_tuple().exponent < -2:
        raise ValueError("initial wealth amount must have at most two decimal places")


def _require_valid_target_amount(target_amount: Decimal) -> None:
    if not isinstance(target_amount, Decimal):
        raise TypeError("target_amount must be Decimal")
    if not target_amount.is_finite():
        raise ValueError("target_amount must be finite")
    if target_amount <= _ZERO:
        raise ValueError("target_amount must be greater than zero")
    if target_amount.as_tuple().exponent < -2:
        raise ValueError("target_amount must have at most two decimal places")


class TargetAchievementSolver:
    """Find the first target crossing using the forward engine as sole oracle."""

    def __init__(self, projection_engine: Optional[ForwardProjectionEngine] = None):
        self._projection_engine = projection_engine or ForwardProjectionEngine()

    def solve(
        self,
        initial_wealth_fact: InitialWealthFact,
        assumptions: ProjectionAssumptions,
        target_amount: Decimal,
    ) -> TargetAchievementResult:
        _require_valid_solver_inputs(initial_wealth_fact, assumptions)
        _require_valid_target_amount(target_amount)

        if initial_wealth_fact.amount >= target_amount:
            return TargetAchievementResult(
                status=TargetAchievementStatus.ALREADY_ACHIEVED,
                target_amount=target_amount,
                initial_wealth_fact=initial_wealth_fact,
                assumptions=assumptions,
                achievement_period=0,
                achievement_date=assumptions.as_of_date,
                months_required=0,
                achieved_wealth=initial_wealth_fact.amount,
                projection_result=None,
            )

        projection = self._projection_engine.project(
            initial_wealth_fact,
            assumptions,
        )
        for period in projection.periods:
            if period.ending_wealth >= target_amount:
                return TargetAchievementResult(
                    status=TargetAchievementStatus.ACHIEVED,
                    target_amount=target_amount,
                    initial_wealth_fact=initial_wealth_fact,
                    assumptions=assumptions,
                    achievement_period=period.period,
                    achievement_date=period.period_end,
                    months_required=period.period,
                    achieved_wealth=period.ending_wealth,
                    projection_result=projection,
                )

        zero_contribution = assumptions.scenario_monthly_contribution.is_zero()
        impossibility_proven = zero_contribution and (
            initial_wealth_fact.amount.is_zero()
            or projection.monthly_equivalent_rate <= _ZERO
        )
        status = (
            TargetAchievementStatus.UNREACHABLE
            if impossibility_proven
            else TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON
        )
        return TargetAchievementResult(
            status=status,
            target_amount=target_amount,
            initial_wealth_fact=initial_wealth_fact,
            assumptions=assumptions,
            achievement_period=None,
            achievement_date=None,
            months_required=None,
            achieved_wealth=None,
            projection_result=projection,
        )
