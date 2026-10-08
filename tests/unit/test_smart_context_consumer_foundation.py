from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from backend.application.services.smart_context_consumer_foundation import (
    SmartContextConsumerFoundation,
)
from backend.domains.smart_context import (
    SmartContextFeature,
    SmartDefaultState,
    SmartFeatureContext,
    SmartOverridePolicy,
    SmartSemanticType,
    SmartUnavailableReason,
    SmartValue,
    SmartValueKey,
    SmartValueOwner,
    SmartValueScope,
    SmartValueSource,
    SmartValueType,
)


AS_OF = date(2026, 10, 6)
USER_ID = uuid4()
DB = object()


def _money_value(
    key: SmartValueKey,
    amount: str,
    *,
    semantic_type: SmartSemanticType,
    owner: SmartValueOwner,
    source: SmartValueSource,
    state: SmartDefaultState,
    override_policy: SmartOverridePolicy,
    scope: str,
    reason: str | None = None,
) -> SmartValue:
    return SmartValue(
        key=key,
        value=Decimal(amount),
        value_type=SmartValueType.MONEY,
        semantic_type=semantic_type,
        owner=owner,
        source=source,
        source_label=f"{owner.value} - certified test source",
        state=state,
        override_policy=override_policy,
        scope=SmartValueScope(scope),
        reference_period="2026-09",
        reason=reason,
    )


def _assumption(key: SmartValueKey, owner: SmartValueOwner) -> SmartValue:
    value_type = (
        SmartValueType.RATIO
        if key
        in {
            SmartValueKey.PLANNING_EXPECTED_RETURN,
            SmartValueKey.PLANNING_INFLATION,
            SmartValueKey.FIRE_WITHDRAWAL_RATE,
            SmartValueKey.FIRE_EXPECTED_RETURN,
            SmartValueKey.FIRE_INFLATION,
        }
        else SmartValueType.MONEY
    )
    return SmartValue(
        key=key,
        value=None,
        value_type=value_type,
        semantic_type=SmartSemanticType.ASSUMPTION,
        owner=owner,
        source=SmartValueSource.USER_INPUT_REQUIRED,
        source_label=f"{owner.value} - explicit assumption",
        state=SmartDefaultState.ASSUMPTION_REQUIRED,
        override_policy=SmartOverridePolicy.SCENARIO_OVERRIDE,
        unavailable_reason=SmartUnavailableReason.ASSUMPTION_REQUIRED,
        reason="The consumer must supply this assumption explicitly.",
    )


def _contexts() -> dict[SmartContextFeature, SmartFeatureContext]:
    wealth = _money_value(
        SmartValueKey.INVESTMENT_WEALTH,
        "123456.78",
        semantic_type=SmartSemanticType.OBSERVED,
        owner=SmartValueOwner.PLANNING_PORTFOLIO_RESOLVER,
        source=SmartValueSource.INVESTMENT_PORTFOLIO,
        state=SmartDefaultState.SUGGESTED_REFERENCE,
        override_policy=SmartOverridePolicy.SELECT_SOURCE,
        scope="INVESTMENT_PORTFOLIO",
    )
    declared_income = _money_value(
        SmartValueKey.DECLARED_MONTHLY_GROSS_INCOME,
        "5500.00",
        semantic_type=SmartSemanticType.DECLARED,
        owner=SmartValueOwner.PROFILE,
        source=SmartValueSource.USER_PROFILE,
        state=SmartDefaultState.SUGGESTED_REFERENCE,
        override_policy=SmartOverridePolicy.USE_AS_REFERENCE,
        scope="DECLARED_GROSS_MONTHLY_BRL",
    )
    recurring_income = _money_value(
        SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE,
        "4200.10",
        semantic_type=SmartSemanticType.DERIVED,
        owner=SmartValueOwner.GOVERNED_LEDGER,
        source=SmartValueSource.GOVERNED_TRANSACTIONS,
        state=SmartDefaultState.SUGGESTED_REFERENCE,
        override_policy=SmartOverridePolicy.USE_AS_REFERENCE,
        scope="RECURRING_INCOME_SOURCE",
    )
    health_savings = _money_value(
        SmartValueKey.HEALTH_SAVINGS_AMOUNT,
        "3000.00",
        semantic_type=SmartSemanticType.DERIVED,
        owner=SmartValueOwner.FINANCIAL_HEALTH,
        source=SmartValueSource.FINANCIAL_HEALTH,
        state=SmartDefaultState.SUGGESTED_REFERENCE,
        override_policy=SmartOverridePolicy.USE_AS_REFERENCE,
        scope="CONSOLIDATED_HEALTH",
        reason="Realized savings; not contribution capacity.",
    )
    goal_target = _money_value(
        SmartValueKey.GOAL_TARGET_AMOUNT,
        "50000.00",
        semantic_type=SmartSemanticType.DECLARED,
        owner=SmartValueOwner.GOALS,
        source=SmartValueSource.GOAL,
        state=SmartDefaultState.KNOWN_FACT,
        override_policy=SmartOverridePolicy.NOT_ALLOWED,
        scope="GOAL",
    )
    planning_assumptions = (
        _assumption(SmartValueKey.PLANNING_CONTRIBUTION, SmartValueOwner.PLANNING),
        _assumption(SmartValueKey.PLANNING_EXPECTED_RETURN, SmartValueOwner.PLANNING),
        _assumption(SmartValueKey.PLANNING_INFLATION, SmartValueOwner.PLANNING),
    )
    fire_assumptions = tuple(
        _assumption(key, SmartValueOwner.FIRE)
        for key in (
            SmartValueKey.FIRE_RETIREMENT_SPENDING,
            SmartValueKey.FIRE_WITHDRAWAL_RATE,
            SmartValueKey.FIRE_EXPECTED_RETURN,
            SmartValueKey.FIRE_INFLATION,
            SmartValueKey.FIRE_CONTRIBUTION,
        )
    )
    return {
        SmartContextFeature.HOME: SmartFeatureContext(
            SmartContextFeature.HOME,
            AS_OF,
            (declared_income, recurring_income, health_savings, wealth, goal_target),
        ),
        SmartContextFeature.PLANNING: SmartFeatureContext(
            SmartContextFeature.PLANNING,
            AS_OF,
            (wealth, *planning_assumptions),
        ),
        SmartContextFeature.GOAL: SmartFeatureContext(
            SmartContextFeature.GOAL,
            AS_OF,
            (goal_target, health_savings),
        ),
        SmartContextFeature.FIRE: SmartFeatureContext(
            SmartContextFeature.FIRE,
            AS_OF,
            (wealth, *fire_assumptions),
        ),
    }


class RecordingContextService:
    def __init__(self, contexts=None, error: Exception | None = None) -> None:
        self.contexts = contexts if contexts is not None else _contexts()
        self.error = error
        self.calls: list[tuple[object, UUID, SmartContextFeature, date]] = []

    def get_context_for(self, db, current_user_id, *, feature, as_of_date):
        self.calls.append((db, current_user_id, feature, as_of_date))
        if self.error is not None:
            raise self.error
        return self.contexts[feature]


@pytest.mark.parametrize(
    ("method_name", "feature"),
    [
        ("get_home_context", SmartContextFeature.HOME),
        ("get_planning_context", SmartContextFeature.PLANNING),
        ("get_goal_context", SmartContextFeature.GOAL),
        ("get_fire_context", SmartContextFeature.FIRE),
    ],
)
def test_each_consumer_delegates_once_with_fixed_feature_user_and_as_of(
    method_name,
    feature,
):
    provider = RecordingContextService()
    foundation = SmartContextConsumerFoundation(provider)

    result = getattr(foundation, method_name)(DB, USER_ID, as_of_date=AS_OF)

    assert result is provider.contexts[feature]
    assert provider.calls == [(DB, USER_ID, feature, AS_OF)]


def test_planning_exposes_only_wealth_and_explicit_assumption_states():
    context = SmartContextConsumerFoundation(
        RecordingContextService()
    ).get_planning_context(DB, USER_ID, as_of_date=AS_OF)

    assert context.values[0].key is SmartValueKey.INVESTMENT_WEALTH
    assert context.values[0].value == Decimal("123456.78")
    assert all(
        value.state is SmartDefaultState.ASSUMPTION_REQUIRED
        and value.value is None
        for value in context.values[1:]
    )
    assert {value.key for value in context.values}.isdisjoint(
        {
            SmartValueKey.DECLARED_MONTHLY_GROSS_INCOME,
            SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE,
            SmartValueKey.HEALTH_SAVINGS_AMOUNT,
        }
    )


def test_fire_exposes_wealth_without_resolving_any_required_assumption():
    context = SmartContextConsumerFoundation(
        RecordingContextService()
    ).get_fire_context(DB, USER_ID, as_of_date=AS_OF)

    assert context.values[0].key is SmartValueKey.INVESTMENT_WEALTH
    assert context.values[0].value == Decimal("123456.78")
    assert {value.key for value in context.values[1:]} == {
        SmartValueKey.FIRE_RETIREMENT_SPENDING,
        SmartValueKey.FIRE_WITHDRAWAL_RATE,
        SmartValueKey.FIRE_EXPECTED_RETURN,
        SmartValueKey.FIRE_INFLATION,
        SmartValueKey.FIRE_CONTRIBUTION,
    }
    assert all(
        value.state is SmartDefaultState.ASSUMPTION_REQUIRED
        and value.value is None
        for value in context.values[1:]
    )


def test_goal_preserves_owned_fact_and_labels_health_savings_as_reference_only():
    context = SmartContextConsumerFoundation(
        RecordingContextService()
    ).get_goal_context(DB, USER_ID, as_of_date=AS_OF)

    goal = next(value for value in context.values if value.owner is SmartValueOwner.GOALS)
    savings = next(
        value
        for value in context.values
        if value.key is SmartValueKey.HEALTH_SAVINGS_AMOUNT
    )
    assert goal.value == Decimal("50000.00")
    assert goal.state is SmartDefaultState.KNOWN_FACT
    assert savings.value == Decimal("3000.00")
    assert savings.state is SmartDefaultState.SUGGESTED_REFERENCE
    assert "not contribution capacity" in savings.reason
    assert SmartValueKey.PLANNING_CONTRIBUTION not in {
        value.key for value in context.values
    }


def test_home_preserves_b5_values_without_score_performance_or_recommendation():
    provider = RecordingContextService()
    context = SmartContextConsumerFoundation(provider).get_home_context(
        DB,
        USER_ID,
        as_of_date=AS_OF,
    )

    assert context is provider.contexts[SmartContextFeature.HOME]
    assert {value.key for value in context.values} == {
        SmartValueKey.DECLARED_MONTHLY_GROSS_INCOME,
        SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE,
        SmartValueKey.HEALTH_SAVINGS_AMOUNT,
        SmartValueKey.INVESTMENT_WEALTH,
        SmartValueKey.GOAL_TARGET_AMOUNT,
    }


def test_cross_feature_contexts_remain_purpose_limited():
    foundation = SmartContextConsumerFoundation(RecordingContextService())

    planning = foundation.get_planning_context(DB, USER_ID, as_of_date=AS_OF)
    fire = foundation.get_fire_context(DB, USER_ID, as_of_date=AS_OF)
    goal = foundation.get_goal_context(DB, USER_ID, as_of_date=AS_OF)

    assert SmartValueKey.DECLARED_MONTHLY_GROSS_INCOME not in {
        value.key for value in planning.values
    }
    assert SmartValueKey.GOAL_TARGET_AMOUNT not in {
        value.key for value in fire.values
    }
    assert SmartValueKey.INVESTMENT_WEALTH not in {
        value.key for value in goal.values
    }


def test_ownership_failure_propagates_without_null_or_default_context():
    error = RuntimeError("ownership failure")
    provider = RecordingContextService(error=error)
    foundation = SmartContextConsumerFoundation(provider)

    with pytest.raises(RuntimeError, match="ownership failure"):
        foundation.get_planning_context(DB, USER_ID, as_of_date=AS_OF)

    assert provider.calls == [(DB, USER_ID, SmartContextFeature.PLANNING, AS_OF)]


def test_foundation_returns_immutable_context_without_mutation_or_copy():
    provider = RecordingContextService()
    expected = provider.contexts[SmartContextFeature.PLANNING]
    foundation = SmartContextConsumerFoundation(provider)

    result = foundation.get_planning_context(DB, USER_ID, as_of_date=AS_OF)

    assert result is expected
    with pytest.raises(FrozenInstanceError):
        result.values[0].value = Decimal("0.00")
