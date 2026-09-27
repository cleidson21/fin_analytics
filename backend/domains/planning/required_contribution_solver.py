from dataclasses import dataclass, replace
from decimal import Decimal
from enum import Enum
from typing import Optional

from backend.domains.planning.assumptions import ProjectionAssumptions
from backend.domains.planning.facts import InitialWealthFact
from backend.domains.planning.target_solver import (
    TargetAchievementResult,
    TargetAchievementSolver,
    TargetAchievementStatus,
)


_MONEY_ZERO = Decimal("0.00")


class RequiredContributionStatus(str, Enum):
    """Approved mathematical states for the required-contribution solver."""

    ALREADY_ACHIEVED = "ALREADY_ACHIEVED"
    ZERO_CONTRIBUTION_REQUIRED = "ZERO_CONTRIBUTION_REQUIRED"
    SOLVED = "SOLVED"
    IMPOSSIBLE_HORIZON = "IMPOSSIBLE_HORIZON"
    OUT_OF_SUPPORTED_RANGE = "OUT_OF_SUPPORTED_RANGE"


@dataclass(frozen=True)
class RequiredContributionResult:
    """Immutable cent-minimal contribution result with its audit trail."""

    status: RequiredContributionStatus
    target_amount: Decimal
    initial_wealth_fact: InitialWealthFact
    assumptions_template: ProjectionAssumptions
    required_monthly_contribution: Decimal
    solved_assumptions: ProjectionAssumptions
    target_achievement_result: TargetAchievementResult


def _money_to_cents(value: Decimal) -> int:
    """Convert a validated cent-scale Decimal to exact integer cents."""

    sign, digits, exponent = value.as_tuple()
    coefficient = 0
    for digit in digits:
        coefficient = coefficient * 10 + digit
    if sign:
        coefficient = -coefficient
    return coefficient * (10 ** (exponent + 2))


def _cents_to_money(cents: int) -> Decimal:
    """Construct a cent-scale Decimal without using the active context."""

    cents_tuple = Decimal(cents).as_tuple()
    return Decimal((cents_tuple.sign, cents_tuple.digits, -2))


def _reaches_target(result: TargetAchievementResult) -> bool:
    return result.status in {
        TargetAchievementStatus.ALREADY_ACHIEVED,
        TargetAchievementStatus.ACHIEVED,
    }


class RequiredContributionSolver:
    """Find the smallest monthly contribution using target solves as oracle."""

    def __init__(
        self,
        target_solver: Optional[TargetAchievementSolver] = None,
    ) -> None:
        self._target_solver = target_solver or TargetAchievementSolver()

    def solve(
        self,
        initial_wealth_fact: InitialWealthFact,
        assumptions_template: ProjectionAssumptions,
        target_amount: Decimal,
    ) -> RequiredContributionResult:
        if not isinstance(initial_wealth_fact, InitialWealthFact):
            raise TypeError("initial_wealth_fact must be InitialWealthFact")
        if not isinstance(assumptions_template, ProjectionAssumptions):
            raise TypeError("assumptions_template must be ProjectionAssumptions")

        zero_assumptions = replace(
            assumptions_template,
            scenario_monthly_contribution=_MONEY_ZERO,
        )
        zero_result = self._target_solver.solve(
            initial_wealth_fact,
            zero_assumptions,
            target_amount,
        )

        if zero_result.status is TargetAchievementStatus.ALREADY_ACHIEVED:
            return RequiredContributionResult(
                status=RequiredContributionStatus.ALREADY_ACHIEVED,
                target_amount=target_amount,
                initial_wealth_fact=initial_wealth_fact,
                assumptions_template=assumptions_template,
                required_monthly_contribution=_MONEY_ZERO,
                solved_assumptions=zero_assumptions,
                target_achievement_result=zero_result,
            )

        if zero_result.status is TargetAchievementStatus.ACHIEVED:
            return RequiredContributionResult(
                status=RequiredContributionStatus.ZERO_CONTRIBUTION_REQUIRED,
                target_amount=target_amount,
                initial_wealth_fact=initial_wealth_fact,
                assumptions_template=assumptions_template,
                required_monthly_contribution=_MONEY_ZERO,
                solved_assumptions=zero_assumptions,
                target_achievement_result=zero_result,
            )

        # For a fixed contribution, the validated cent recurrence is monotone:
        # positive returns preserve order, while for -1 < rate < 0 the rounded
        # loss can grow by at most one cent when opening wealth grows one cent.
        # Thus the post-return balance never decreases as a candidate increases,
        # and induction preserves order across every projected month.
        #
        # A contribution equal to target_amount is also a safe upper bound. The
        # pre-contribution balance cannot be negative under the same recurrence,
        # so END_OF_MONTH addition reaches the target in period one.
        low_failing_cents = 0
        high_succeeding_cents = _money_to_cents(target_amount)
        high_result = self._solve_candidate(
            initial_wealth_fact,
            assumptions_template,
            target_amount,
            high_succeeding_cents,
        )
        if not _reaches_target(high_result):
            raise ArithmeticError(
                "target_amount contribution upper bound failed to reach target"
            )

        while high_succeeding_cents - low_failing_cents > 1:
            candidate_cents = (
                low_failing_cents + high_succeeding_cents
            ) // 2
            candidate_result = self._solve_candidate(
                initial_wealth_fact,
                assumptions_template,
                target_amount,
                candidate_cents,
            )
            if _reaches_target(candidate_result):
                high_succeeding_cents = candidate_cents
            else:
                low_failing_cents = candidate_cents

        solved_result = self._solve_candidate(
            initial_wealth_fact,
            assumptions_template,
            target_amount,
            high_succeeding_cents,
        )
        previous_result = self._solve_candidate(
            initial_wealth_fact,
            assumptions_template,
            target_amount,
            high_succeeding_cents - 1,
        )
        if not _reaches_target(solved_result) or _reaches_target(previous_result):
            raise ArithmeticError("cent-minimal contribution invariant failed")

        solved_assumptions = solved_result.assumptions
        return RequiredContributionResult(
            status=RequiredContributionStatus.SOLVED,
            target_amount=target_amount,
            initial_wealth_fact=initial_wealth_fact,
            assumptions_template=assumptions_template,
            required_monthly_contribution=(
                solved_assumptions.scenario_monthly_contribution
            ),
            solved_assumptions=solved_assumptions,
            target_achievement_result=solved_result,
        )

    def _solve_candidate(
        self,
        initial_wealth_fact: InitialWealthFact,
        assumptions_template: ProjectionAssumptions,
        target_amount: Decimal,
        candidate_cents: int,
    ) -> TargetAchievementResult:
        candidate_assumptions = replace(
            assumptions_template,
            scenario_monthly_contribution=_cents_to_money(candidate_cents),
        )
        return self._target_solver.solve(
            initial_wealth_fact,
            candidate_assumptions,
            target_amount,
        )
