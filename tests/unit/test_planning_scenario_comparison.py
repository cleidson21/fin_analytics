from dataclasses import FrozenInstanceError, fields
from datetime import date, datetime
from decimal import Decimal

import pytest

from backend.domains.planning import (
    ForwardProjectionEngine,
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    OutputMode,
    PlanningFactAsOf,
    PlanningFactProvenance,
    ProjectionAssumptions,
    ReturnType,
    ScenarioArchetype,
    ScenarioComparisonEngine,
    ScenarioComparisonEntry,
    ScenarioComparisonResult,
    ScenarioDefinition,
    TargetAchievementSolver,
    TargetAchievementStatus,
    TargetValueBasis,
)
from backend.domains.planning.goal_planning import (
    TargetValueBasis as GoalPlanningTargetValueBasis,
)


def _fact(
    amount: str = "1000.00",
    source: InitialWealthSource = InitialWealthSource.USER_PROVIDED_SCENARIO,
) -> InitialWealthFact:
    scope = {
        InitialWealthSource.GOAL_CURRENT_AMOUNT: InitialWealthScope.GOAL,
        InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT: (
            InitialWealthScope.INVESTMENT_PORTFOLIO
        ),
        InitialWealthSource.USER_PROVIDED_SCENARIO: (
            InitialWealthScope.USER_PROVIDED_SCENARIO
        ),
    }[source]
    return InitialWealthFact(
        source=source,
        amount=Decimal(amount),
        scope=scope,
        as_of=PlanningFactAsOf(observed_at=datetime(2026, 9, 16, 12, 0, 0)),
        provenance=PlanningFactProvenance(
            source_table="planning_test",
            source_type=source.value,
            account_id="account-a" if scope is InitialWealthScope.INVESTMENT_PORTFOLIO else None,
        ),
    )


def _assumptions(**overrides) -> ProjectionAssumptions:
    values = {
        "as_of_date": date(2026, 9, 16),
        "scenario_monthly_contribution": Decimal("100.00"),
        "expected_return_rate": Decimal("0"),
        "return_type": ReturnType.NOMINAL,
        "output_mode": OutputMode.NOMINAL,
        "horizon_months": 3,
    }
    values.update(overrides)
    return ProjectionAssumptions(**values)


def _scenario(
    scenario_id: str,
    amount: str = "1000.00",
    *,
    assumptions: ProjectionAssumptions | None = None,
    source: InitialWealthSource = InitialWealthSource.USER_PROVIDED_SCENARIO,
    label: str | None = None,
    archetype: ScenarioArchetype | None = None,
) -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id=scenario_id,
        initial_wealth_fact=_fact(amount, source),
        assumptions=assumptions or _assumptions(),
        label=label,
        archetype=archetype,
    )


class _CountingProjectionEngine(ForwardProjectionEngine):
    def __init__(self) -> None:
        self.calls = 0

    def project(self, initial_wealth_fact, assumptions):
        self.calls += 1
        return super().project(initial_wealth_fact, assumptions)


class _CountingTargetSolver(TargetAchievementSolver):
    def __init__(self, projection_engine: ForwardProjectionEngine) -> None:
        super().__init__(projection_engine)
        self.calls = 0

    def solve(self, initial_wealth_fact, assumptions, target_amount):
        self.calls += 1
        return super().solve(initial_wealth_fact, assumptions, target_amount)


def _engine_with_spies():
    projection = _CountingProjectionEngine()
    target = _CountingTargetSolver(projection)
    return ScenarioComparisonEngine(projection, target), projection, target


def test_target_value_basis_has_neutral_canonical_identity():
    assert TargetValueBasis is GoalPlanningTargetValueBasis
    assert TargetValueBasis.NOMINAL.value == "NOMINAL"
    assert TargetValueBasis.REAL.value == "REAL"


@pytest.mark.parametrize("scenario_count", [0, 1])
def test_comparison_requires_at_least_two_scenarios_before_any_engine_call(scenario_count):
    engine, projection, target = _engine_with_spies()
    scenarios = tuple(_scenario(f"scenario-{index}") for index in range(scenario_count))

    with pytest.raises(ValueError, match="at least two"):
        engine.compare(scenarios, "scenario-0")

    assert projection.calls == 0
    assert target.calls == 0


def test_definition_requires_explicit_typed_identity_fact_assumptions_and_metadata():
    with pytest.raises(ValueError, match="non-empty"):
        _scenario("")
    with pytest.raises(TypeError, match="label"):
        ScenarioDefinition("scenario", _fact(), _assumptions(), label=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="archetype"):
        _scenario("scenario", archetype="BASE")  # type: ignore[arg-type]

    definition = _scenario(
        "scenario",
        label="Any user label",
        archetype=ScenarioArchetype.BASE,
    )
    assert definition.label == "Any user label"
    assert definition.archetype is ScenarioArchetype.BASE


def test_reference_is_explicit_unique_and_need_not_be_base_or_first():
    scenarios = (
        _scenario("first", archetype=ScenarioArchetype.BASE),
        _scenario("reference", archetype=ScenarioArchetype.CONSERVATIVE),
        _scenario("last", archetype=ScenarioArchetype.OPTIMISTIC),
    )
    result = ScenarioComparisonEngine().compare(scenarios, "reference")

    assert result.reference_scenario_id == "reference"
    assert [entry.scenario_id for entry in result.entries] == [
        "first",
        "reference",
        "last",
    ]
    assert result.entries[1].final_wealth_delta == Decimal("0.00")


@pytest.mark.parametrize("reference_id", ["first", "middle", "last"])
def test_any_explicit_input_position_can_be_the_reference(reference_id):
    scenarios = (_scenario("first"), _scenario("middle"), _scenario("last"))

    result = ScenarioComparisonEngine().compare(scenarios, reference_id)

    reference_entry = next(
        entry for entry in result.entries if entry.scenario_id == reference_id
    )
    assert reference_entry.final_wealth_delta == Decimal("0.00")


@pytest.mark.parametrize(
    ("scenarios", "reference_id", "message"),
    [
        ((_scenario("same"), _scenario("same")), "same", "unique"),
        ((_scenario("a"), _scenario("b")), "missing", "supplied"),
    ],
)
def test_duplicate_or_missing_reference_is_rejected_atomically(
    scenarios,
    reference_id,
    message,
):
    engine, projection, target = _engine_with_spies()

    with pytest.raises(ValueError, match=message):
        engine.compare(scenarios, reference_id)

    assert projection.calls == 0
    assert target.calls == 0


def test_archetypes_are_metadata_without_economic_ordering_or_ranking():
    conservative = _scenario(
        "conservative",
        assumptions=_assumptions(expected_return_rate=Decimal("0.30")),
        archetype=ScenarioArchetype.CONSERVATIVE,
    )
    optimistic = _scenario(
        "optimistic",
        assumptions=_assumptions(expected_return_rate=Decimal("0.01")),
        archetype=ScenarioArchetype.OPTIMISTIC,
    )

    result = ScenarioComparisonEngine().compare(
        (conservative, optimistic),
        "optimistic",
    )

    assert result.entries[0].archetype is ScenarioArchetype.CONSERVATIVE
    assert result.entries[1].archetype is ScenarioArchetype.OPTIMISTIC
    assert not any("rank" in field.name or "winner" in field.name for field in fields(result))


def test_prevalidation_uses_shared_as_of_resolved_horizon_output_and_timing():
    engine, projection, target = _engine_with_spies()
    valid = _scenario("valid")
    different_as_of = _scenario(
        "as-of",
        assumptions=_assumptions(as_of_date=date(2026, 10, 1)),
    )
    with pytest.raises(ValueError, match="as_of_date"):
        engine.compare((valid, different_as_of), "valid")

    different_horizon = _scenario("horizon", assumptions=_assumptions(horizon_months=2))
    with pytest.raises(ValueError, match="resolved_horizon_months"):
        engine.compare((valid, different_horizon), "valid")

    different_output = _scenario(
        "real",
        assumptions=_assumptions(
            return_type=ReturnType.REAL,
            output_mode=OutputMode.REAL,
        ),
    )
    with pytest.raises(ValueError, match="output_mode"):
        engine.compare((valid, different_output), "valid")

    assert projection.calls == 0
    assert target.calls == 0


def test_equivalent_horizon_representations_and_different_return_types_are_comparable():
    nominal_real = _scenario(
        "nominal-real",
        assumptions=_assumptions(
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=Decimal("0.03"),
            horizon_months=12,
        ),
    )
    real = _scenario(
        "real",
        assumptions=_assumptions(
            return_type=ReturnType.REAL,
            output_mode=OutputMode.REAL,
            horizon_months=None,
            target_date=date(2027, 9, 1),
        ),
    )

    result = ScenarioComparisonEngine().compare((nominal_real, real), "nominal-real")

    assert result.horizon_months == 12
    assert result.output_mode is OutputMode.REAL


def test_no_target_uses_exactly_one_forward_projection_per_scenario_and_preserves_provenance():
    engine, projection, target = _engine_with_spies()
    reference = _scenario("reference", "1000.00")
    candidate = _scenario(
        "candidate",
        "1000.00",
        assumptions=_assumptions(scenario_monthly_contribution=Decimal("150.00")),
        source=InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT,
    )

    result = engine.compare((reference, candidate), "reference")

    assert projection.calls == 2
    assert target.calls == 0
    assert result.target_amount is None
    assert result.target_value_basis is None
    assert result.entries[0].target_achievement_result is None
    assert result.entries[0].months_saved_or_lost is None
    assert result.entries[1].initial_wealth_fact is candidate.initial_wealth_fact
    assert result.entries[1].initial_wealth_fact.source is InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT
    assert result.entries[0].final_wealth_delta == Decimal("0.00")
    assert result.entries[1].final_wealth_delta == Decimal("150.00")
    assert result.entries[1].total_contributions_delta == Decimal("150.00")
    assert result.entries[1].total_projected_growth_delta == Decimal("0.00")


def test_identical_scenarios_are_valid_and_produce_exact_zero_deltas():
    result = ScenarioComparisonEngine().compare(
        (_scenario("left"), _scenario("right")),
        "left",
    )

    assert result.entries[1].final_wealth_delta == Decimal("0.00")
    assert result.entries[1].total_contributions_delta == Decimal("0.00")
    assert result.entries[1].total_projected_growth_delta == Decimal("0.00")


def test_no_target_return_and_initial_wealth_differences_are_explicit_facts_not_attribution():
    reference = _scenario("reference", "1000.00")
    candidate = _scenario(
        "candidate",
        "1200.00",
        assumptions=_assumptions(expected_return_rate=Decimal("0.12")),
    )

    result = ScenarioComparisonEngine().compare((reference, candidate), "reference")

    assert result.entries[1].final_wealth_delta > Decimal("0.00")
    assert result.entries[1].total_contributions_delta == Decimal("0.00")
    assert not any("attribution" in field.name for field in fields(result))


@pytest.mark.parametrize(
    ("target_amount", "basis", "message"),
    [
        (None, TargetValueBasis.NOMINAL, "provided together"),
        (Decimal("1000.00"), None, "provided together"),
        (Decimal("1000.001"), TargetValueBasis.NOMINAL, "at most two"),
        (Decimal("0.00"), TargetValueBasis.NOMINAL, "greater than zero"),
    ],
)
def test_target_pair_and_target_money_contract_are_prevalidated_atomically(
    target_amount,
    basis,
    message,
):
    engine, projection, target = _engine_with_spies()

    with pytest.raises(ValueError, match=message):
        engine.compare((_scenario("a"), _scenario("b")), "a", target_amount, basis)

    assert projection.calls == 0
    assert target.calls == 0


def test_target_basis_must_match_common_output_mode_before_engine_calls():
    engine, projection, target = _engine_with_spies()
    with pytest.raises(ValueError, match="basis must match"):
        engine.compare(
            (_scenario("a"), _scenario("b")),
            "a",
            Decimal("1000.00"),
            TargetValueBasis.REAL,
        )

    assert projection.calls == 0
    assert target.calls == 0


@pytest.mark.parametrize(
    ("target_amount", "exception", "message"),
    [
        (1000, TypeError, "must be Decimal"),
        (1000.0, TypeError, "must be Decimal"),
        (True, TypeError, "must be Decimal"),
        ("1000.00", TypeError, "must be Decimal"),
        (Decimal("NaN"), ValueError, "finite"),
        (Decimal("Infinity"), ValueError, "finite"),
    ],
)
def test_target_rejects_non_decimal_and_non_finite_values_before_engine_calls(
    target_amount,
    exception,
    message,
):
    engine, projection, target = _engine_with_spies()
    with pytest.raises(exception, match=message):
        engine.compare(
            (_scenario("a"), _scenario("b")),
            "a",
            target_amount,  # type: ignore[arg-type]
            TargetValueBasis.NOMINAL,
        )

    assert projection.calls == 0
    assert target.calls == 0


def test_target_mode_reuses_nested_projection_and_calculates_temporal_and_money_deltas():
    engine, projection, target = _engine_with_spies()
    reference = _scenario("reference", "800.00", assumptions=_assumptions(horizon_months=4))
    earlier = _scenario(
        "earlier",
        "800.00",
        assumptions=_assumptions(
            scenario_monthly_contribution=Decimal("200.00"),
            horizon_months=4,
        ),
    )
    later = _scenario(
        "later",
        "800.00",
        assumptions=_assumptions(
            scenario_monthly_contribution=Decimal("50.00"),
            horizon_months=4,
        ),
    )

    result = engine.compare(
        (reference, earlier, later),
        "reference",
        Decimal("1000.00"),
        TargetValueBasis.NOMINAL,
    )

    assert target.calls == 3
    assert projection.calls == 3
    assert [entry.months_saved_or_lost for entry in result.entries] == [0, 1, -2]
    assert [entry.target_achievement_result.status for entry in result.entries] == [
        TargetAchievementStatus.ACHIEVED,
        TargetAchievementStatus.ACHIEVED,
        TargetAchievementStatus.ACHIEVED,
    ]
    assert result.entries[1].final_wealth_delta == Decimal("400.00")
    assert result.entries[2].final_wealth_delta == Decimal("-200.00")


def test_same_target_month_has_zero_temporal_delta():
    result = ScenarioComparisonEngine().compare(
        (
            _scenario("reference", "900.00"),
            _scenario("same-month", "800.00", assumptions=_assumptions(
                scenario_monthly_contribution=Decimal("200.00")
            )),
        ),
        "reference",
        Decimal("1000.00"),
        TargetValueBasis.NOMINAL,
    )

    assert [entry.months_saved_or_lost for entry in result.entries] == [0, 0]


def test_already_achieved_gets_only_its_required_direct_forward_projection():
    engine, projection, target = _engine_with_spies()
    normal = _scenario("normal", "900.00")
    already = _scenario("already", "1000.00")

    result = engine.compare(
        (normal, already),
        "normal",
        Decimal("1000.00"),
        TargetValueBasis.NOMINAL,
    )

    assert target.calls == 2
    assert projection.calls == 2
    assert result.entries[1].target_achievement_result.status is TargetAchievementStatus.ALREADY_ACHIEVED
    assert result.entries[1].target_achievement_result.projection_result is None
    assert result.entries[1].months_saved_or_lost == 1


def test_reference_already_achieved_and_non_achieving_states_obey_temporal_null_contract():
    reference_already = _scenario("reference", "1000.00")
    later = _scenario("later", "900.00")
    already_result = ScenarioComparisonEngine().compare(
        (reference_already, later),
        "reference",
        Decimal("1000.00"),
        TargetValueBasis.NOMINAL,
    )
    assert [entry.months_saved_or_lost for entry in already_result.entries] == [0, -1]

    unreachable = _scenario(
        "unreachable",
        "900.00",
        assumptions=_assumptions(scenario_monthly_contribution=Decimal("0.00")),
    )
    no_temporal_result = ScenarioComparisonEngine().compare(
        (later, unreachable),
        "later",
        Decimal("1000.00"),
        TargetValueBasis.NOMINAL,
    )
    assert no_temporal_result.entries[1].target_achievement_result.status is TargetAchievementStatus.UNREACHABLE
    assert [entry.months_saved_or_lost for entry in no_temporal_result.entries] == [0, None]

    reference_not_reached = _scenario(
        "reference-not-reached",
        "900.00",
        assumptions=_assumptions(scenario_monthly_contribution=Decimal("10.00")),
    )
    candidate_achieved = _scenario("candidate-achieved", "900.00")
    not_reached_result = ScenarioComparisonEngine().compare(
        (reference_not_reached, candidate_achieved),
        "reference-not-reached",
        Decimal("1000.00"),
        TargetValueBasis.NOMINAL,
    )
    assert (
        not_reached_result.entries[0].target_achievement_result.status
        is TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON
    )
    assert [entry.months_saved_or_lost for entry in not_reached_result.entries] == [None, None]


@pytest.mark.parametrize(
    ("basis", "assumptions"),
    [
        (TargetValueBasis.NOMINAL, _assumptions()),
        (
            TargetValueBasis.REAL,
            _assumptions(
                return_type=ReturnType.REAL,
                output_mode=OutputMode.REAL,
            ),
        ),
    ],
)
def test_nominal_and_real_target_modes_preserve_target_without_conversion(basis, assumptions):
    result = ScenarioComparisonEngine().compare(
        (
            _scenario("a", "900.00", assumptions=assumptions),
            _scenario("b", "950.00", assumptions=assumptions),
        ),
        "a",
        Decimal("1000.00"),
        basis,
    )

    assert result.target_amount == Decimal("1000.00")
    assert result.target_value_basis is basis
    assert all(
        entry.target_achievement_result.target_amount == Decimal("1000.00")
        for entry in result.entries
    )


def test_large_decimal_facts_and_deltas_remain_exact_without_float():
    amount = Decimal("9" * 120 + ".00")
    result = ScenarioComparisonEngine().compare(
        (
            _scenario("reference", str(amount)),
            _scenario("candidate", str(amount + Decimal("1.00"))),
        ),
        "reference",
    )

    assert result.entries[1].final_wealth_delta == Decimal("1.00")
    assert isinstance(result.entries[1].final_wealth_delta, Decimal)
    assert result.entries[1].final_wealth.adjusted() + 1 == 121


def test_results_are_frozen_deterministic_and_preserve_complete_certified_results():
    scenarios = (_scenario("a", "900.00"), _scenario("b", "1000.00"))
    engine = ScenarioComparisonEngine()
    first = engine.compare(
        scenarios,
        "a",
        Decimal("1000.00"),
        TargetValueBasis.NOMINAL,
    )
    second = engine.compare(
        scenarios,
        "a",
        Decimal("1000.00"),
        TargetValueBasis.NOMINAL,
    )

    assert first == second
    assert isinstance(first.entries, tuple)
    assert first.entries[0].scenario is scenarios[0]
    assert first.entries[0].projection_result.initial_wealth_fact is scenarios[0].initial_wealth_fact
    assert first.entries[0].projection_result.assumptions is scenarios[0].assumptions
    with pytest.raises(FrozenInstanceError):
        first.reference_scenario_id = "b"
    with pytest.raises(FrozenInstanceError):
        first.entries[0].final_wealth_delta = Decimal("1.00")


def test_definition_is_frozen_and_caller_owned_input_list_is_not_mutated():
    first = _scenario("first")
    second = _scenario("second")
    caller_owned_scenarios = [first, second]
    original_order = list(caller_owned_scenarios)

    result = ScenarioComparisonEngine().compare(
        caller_owned_scenarios,
        "second",
    )

    assert caller_owned_scenarios == original_order
    assert [entry.scenario for entry in result.entries] == original_order
    with pytest.raises(FrozenInstanceError):
        first.scenario_id = "changed"


def test_result_types_have_only_transient_comparison_contract_fields():
    assert [field.name for field in fields(ScenarioComparisonEntry)] == [
        "scenario",
        "projection_result",
        "target_achievement_result",
        "final_wealth_delta",
        "total_contributions_delta",
        "total_projected_growth_delta",
        "months_saved_or_lost",
    ]
    assert [field.name for field in fields(ScenarioComparisonResult)] == [
        "reference_scenario_id",
        "entries",
        "as_of_date",
        "horizon_months",
        "output_mode",
        "contribution_timing",
        "target_amount",
        "target_value_basis",
    ]
