from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from backend.application.dtos.cashflow_summary_dto import MonthlyFinancialMetricsDTO
from backend.application.exceptions.smart_context_composition_error import (
    UnsupportedSmartContextFeatureError,
)
from backend.application.exceptions.planning_portfolio_source_error import (
    PlanningPortfolioSourceUnavailableError,
)
from backend.application.services.income_candidate_service import (
    IncomeCandidateCollection,
    IncomeCandidateView,
)
from backend.application.services.single_tenant_user_scope import OwnedUserScope
from backend.application.services.smart_financial_context_service import (
    FEATURE_ALLOWLISTS,
    SmartFinancialContextService,
)
from backend.application.services.smart_context_sources import (
    HealthSmartContextSource,
    PortfolioSmartContextSource,
)
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domains.planning.facts import (
    GoalPlanningFact,
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    PlanningFactAsOf,
    PlanningFactProvenance,
)
from backend.domains.smart_context import (
    DeclaredFinancialContext,
    IncomeBasis,
    IncomeCurrency,
    IncomePeriod,
    RecurringIncomeDecisionState,
    RecurringIncomeDirection,
    RecurringIncomeEvidenceState,
    RecurringIncomeRiskFlag,
    SmartContextFeature,
    SmartDefaultState,
    SmartFreshness,
    SmartSemanticType,
    SmartUnavailableReason,
    SmartValueKey,
    SmartValueOwner,
    SmartValue,
    SmartValueSource,
    SmartValueType,
    SmartOverridePolicy,
)


AS_OF = date(2026, 10, 5)
USER_ID = uuid4()


class Guard:
    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def resolve(self, db, current_user_id):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return OwnedUserScope(user_id=current_user_id)


class ProfileSource:
    def __init__(self, value=None):
        self.value = value
        self.calls = 0

    def read(self, db, current_user_id):
        self.calls += 1
        return self.value


class RecurringSource:
    def __init__(self, candidates=()):
        self.collection = IncomeCandidateCollection(AS_OF, tuple(candidates))
        self.calls = 0

    def read(self, db, current_user_id, *, as_of_date):
        self.calls += 1
        assert as_of_date == AS_OF
        return self.collection


class HealthSource:
    def __init__(self, value=None):
        self.value = value
        self.calls = 0

    def read_month(self, db, *, as_of_date):
        self.calls += 1
        assert as_of_date == AS_OF
        return self.value


class GoalSource:
    def __init__(self, values=()):
        self.values = tuple(values)
        self.calls = 0

    def read_owned(self, db, current_user_id):
        self.calls += 1
        return self.values


class PortfolioSource:
    def __init__(self, value=None, error=None):
        self.value = value
        self.error = error
        self.calls = 0

    def read(self, db, current_user_id, *, as_of_date):
        self.calls += 1
        if self.error is not None:
            raise self.error
        assert as_of_date == AS_OF
        return self.value


def _declared(amount=Decimal("5500.00")):
    return DeclaredFinancialContext(
        user_id=USER_ID,
        declared_monthly_gross_income=amount,
        currency=IncomeCurrency.BRL,
        income_period=IncomePeriod.MONTHLY,
        income_basis=IncomeBasis.GROSS,
        income_as_of_date=date(2026, 10, 1),
        declared_at=datetime(2026, 10, 2, 10, 0, 0),
        updated_at=datetime(2026, 10, 2, 10, 0, 0),
    )


def _candidate(
    candidate_id,
    *,
    decision=RecurringIncomeDecisionState.CONFIRMED_AS_INCOME,
    evidence_state=RecurringIncomeEvidenceState.DETECTED_CANDIDATE,
    amount=Decimal("4200.10"),
):
    current = evidence_state is RecurringIncomeEvidenceState.DETECTED_CANDIDATE
    return IncomeCandidateView(
        candidate_id=candidate_id,
        evidence_state=evidence_state,
        decision_state=decision,
        signature_version=1,
        source="GOVERNED_TRANSACTIONS",
        evidence_fingerprint="sha256:fingerprint" if current else None,
        currency="BRL" if current else None,
        direction=RecurringIncomeDirection.CREDIT if current else None,
        window_start=date(2026, 5, 1) if current else None,
        window_end=AS_OF if current else None,
        current_month_is_partial=True if current else None,
        includes_current_month=True if current else None,
        observed_months=("2026-08", "2026-09", "2026-10") if current else (),
        monthly_occurrences=(),
        occurrence_count=3 if current else None,
        distinct_month_count=3 if current else None,
        first_occurrence_date=date(2026, 8, 5) if current else None,
        latest_occurrence_date=date(2026, 10, 5) if current else None,
        latest_amount=amount if current else None,
        typical_received_amount=amount if current else None,
        minimum_received_amount=amount if current else None,
        maximum_received_amount=amount if current else None,
        median_absolute_deviation=Decimal("0.00") if current else None,
        risk_flags=(RecurringIncomeRiskFlag.TRANSFER_AMBIGUITY,) if current else (),
        decided_at=datetime(2026, 9, 1, 12, 0, 0) if decision else None,
        decision_updated_at=datetime(2026, 9, 1, 12, 0, 0) if decision else None,
    )


def _health():
    return MonthlyFinancialMetricsDTO(
        reference_month="2026-10",
        total_income=Decimal("9000.00"),
        total_expense=Decimal("6000.00"),
        net_cashflow=Decimal("3000.00"),
        savings_amount=Decimal("3000.00"),
        savings_rate=Decimal("0.3333333333"),
    )


def _wealth():
    return InitialWealthFact(
        source=InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT,
        amount=Decimal("123456.78"),
        as_of=PlanningFactAsOf(reference_month="2026-09"),
        scope=InitialWealthScope.INVESTMENT_PORTFOLIO,
        provenance=PlanningFactProvenance(
            source_table="portfolio_snapshots",
            source_type="MYPROFIT_EVOLUCAO",
            account_id="private-account",
            reference_month="2026-09",
            run_id="private-run",
        ),
    )


def _goal():
    now = datetime(2026, 10, 1, 9, 0, 0)
    return GoalPlanningFact(
        goal_id=uuid4(),
        user_id=USER_ID,
        name="Reserva",
        description=None,
        goal_type=GoalType.EMERGENCY_RESERVE,
        status=GoalStatus.ACTIVE,
        target_amount=Decimal("50000.00"),
        target_date=date(2027, 12, 31),
        current_amount=Decimal("10000.00"),
        goal_planned_monthly_contribution=Decimal("750.00"),
        priority=1,
        linked_account_id=None,
        created_at=now,
        updated_at=now,
    )


def _service(*, profile=None, candidates=(), health=None, goals=(), wealth=None, guard=None):
    sources = {
        "profile_source": ProfileSource(profile),
        "recurring_income_source": RecurringSource(candidates),
        "health_source": HealthSource(health),
        "goal_source": GoalSource(goals),
        "portfolio_source": PortfolioSource(wealth),
    }
    service = SmartFinancialContextService(
        ownership_guard=guard or Guard(),
        **sources,
    )
    return service, sources


def _context(service, feature):
    return service.get_context_for(
        object(), USER_ID, feature=feature, as_of_date=AS_OF
    )


def test_supported_features_and_allowlists_are_locked():
    assert set(SmartContextFeature) == {
        SmartContextFeature.PROFILE,
        SmartContextFeature.HOME,
        SmartContextFeature.PLANNING,
        SmartContextFeature.GOAL,
        SmartContextFeature.FIRE,
    }
    assert set(FEATURE_ALLOWLISTS) == set(SmartContextFeature)


def test_unknown_free_form_feature_fails_instead_of_falling_back():
    service, _ = _service()
    with pytest.raises(UnsupportedSmartContextFeatureError):
        service.get_context_for(
            object(), USER_ID, feature="PLANNING", as_of_date=AS_OF
        )


def test_profile_declared_income_preserves_decimal_and_provenance():
    service, _ = _service(profile=_declared())
    context = _context(service, SmartContextFeature.PROFILE)
    value = next(
        item
        for item in context.values
        if item.key is SmartValueKey.DECLARED_MONTHLY_GROSS_INCOME
    )
    assert value.value == Decimal("5500.00")
    assert type(value.value) is Decimal
    assert value.semantic_type is SmartSemanticType.DECLARED
    assert value.owner is SmartValueOwner.PROFILE
    assert value.declared_at == datetime(2026, 10, 2, 10, 0, 0)
    assert value.reference_period == "2026-10-01"


def test_missing_profile_declaration_is_not_zero():
    service, _ = _service()
    context = _context(service, SmartContextFeature.PROFILE)
    value = context.values[0]
    assert value.value is None
    assert value.unavailable_reason is SmartUnavailableReason.NOT_DECLARED


def test_confirmed_sources_remain_separate_and_are_not_aggregated():
    candidates = (
        _candidate("ric_v1_a", amount=Decimal("4000.00")),
        _candidate("ric_v1_b", amount=Decimal("2500.00")),
    )
    service, _ = _service(candidates=candidates)
    context = _context(service, SmartContextFeature.PROFILE)
    values = [
        item
        for item in context.values
        if item.key is SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE
    ]
    assert [item.value for item in values] == [Decimal("4000.00"), Decimal("2500.00")]
    assert all(item.semantic_type is SmartSemanticType.DERIVED for item in values)


def test_detected_candidate_is_review_state_not_confirmed_income():
    service, _ = _service(candidates=(_candidate("ric_v1_detected", decision=None),))
    context = _context(service, SmartContextFeature.PROFILE)
    confirmed = [
        item
        for item in context.values
        if item.key is SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE
    ]
    review = next(
        item
        for item in context.values
        if item.key is SmartValueKey.RECURRING_INCOME_REVIEW_AVAILABLE
    )
    assert confirmed[0].value is None
    assert confirmed[0].unavailable_reason is SmartUnavailableReason.NO_CONFIRMED_SOURCE
    assert review.value == 1


def test_rejected_candidate_is_not_exposed_as_positive_context():
    service, _ = _service(
        candidates=(
            _candidate("ric_v1_rejected", decision=RecurringIncomeDecisionState.REJECTED),
        )
    )
    context = _context(service, SmartContextFeature.PROFILE)
    assert all(item.value is None for item in context.values)
    assert not any(
        item.key is SmartValueKey.RECURRING_INCOME_REVIEW_AVAILABLE
        for item in context.values
    )


def test_stale_confirmed_source_preserves_state_without_current_amount():
    service, _ = _service(
        candidates=(
            _candidate(
                "ric_v1_stale",
                evidence_state=RecurringIncomeEvidenceState.STALE,
            ),
        )
    )
    context = _context(service, SmartContextFeature.PROFILE)
    value = next(
        item
        for item in context.values
        if item.key is SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE
    )
    assert value.value is None
    assert value.freshness is SmartFreshness.STALE_EVIDENCE
    assert value.unavailable_reason is SmartUnavailableReason.STALE_EVIDENCE


def test_home_delegates_to_all_approved_sources_without_double_counting_income():
    service, sources = _service(
        profile=_declared(),
        candidates=(_candidate("ric_v1_confirmed"),),
        health=_health(),
        goals=(_goal(),),
        wealth=_wealth(),
    )
    context = _context(service, SmartContextFeature.HOME)
    assert all(source.calls == 1 for source in sources.values())
    keys = [item.key for item in context.values]
    assert keys.count(SmartValueKey.HEALTH_MONTHLY_INCOME) == 1
    assert keys.count(SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE) == 1
    assert SmartValueKey.PLANNING_CONTRIBUTION not in keys
    assert all(item.key in FEATURE_ALLOWLISTS[SmartContextFeature.HOME] for item in context.values)


def test_planning_uses_only_portfolio_and_explicit_assumption_states():
    service, sources = _service(
        profile=_declared(),
        candidates=(_candidate("ric_v1_confirmed"),),
        health=_health(),
        goals=(_goal(),),
        wealth=_wealth(),
    )
    context = _context(service, SmartContextFeature.PLANNING)
    assert sources["portfolio_source"].calls == 1
    assert all(
        sources[name].calls == 0
        for name in (
            "profile_source",
            "recurring_income_source",
            "health_source",
            "goal_source",
        )
    )
    wealth = context.values[0]
    assert wealth.value == Decimal("123456.78")
    assert wealth.reference_period == "2026-09"
    assert "private-account" not in repr(context)
    assert all(
        item.state is SmartDefaultState.ASSUMPTION_REQUIRED
        for item in context.values[1:]
    )


def test_fire_preserves_required_spending_withdrawal_and_market_assumptions():
    service, _ = _service(wealth=_wealth())
    context = _context(service, SmartContextFeature.FIRE)
    assert {item.key for item in context.values} == FEATURE_ALLOWLISTS[SmartContextFeature.FIRE]
    assert context.values[0].value == Decimal("123456.78")
    assert all(
        item.state is SmartDefaultState.ASSUMPTION_REQUIRED
        for item in context.values[1:]
    )


def test_goal_context_uses_owned_goal_facts_and_labels_savings_as_reference():
    service, sources = _service(health=_health(), goals=(_goal(),))
    context = _context(service, SmartContextFeature.GOAL)
    keys = {item.key for item in context.values}
    assert SmartValueKey.GOAL_TARGET_AMOUNT in keys
    assert SmartValueKey.GOAL_PLANNED_CONTRIBUTION in keys
    savings = next(
        item for item in context.values if item.key is SmartValueKey.HEALTH_SAVINGS_AMOUNT
    )
    assert savings.value == Decimal("3000.00")
    assert savings.state is SmartDefaultState.SUGGESTED_REFERENCE
    assert "not sustainable contribution capacity" in savings.reason
    assert sources["profile_source"].calls == 0
    assert sources["recurring_income_source"].calls == 0


def test_missing_sources_return_unavailable_not_fabricated_zero():
    service, _ = _service()
    home = _context(service, SmartContextFeature.HOME)
    assert all(item.value is None for item in home.values)
    reasons = {item.unavailable_reason for item in home.values}
    assert SmartUnavailableReason.NOT_DECLARED in reasons
    assert SmartUnavailableReason.NO_CONFIRMED_SOURCE in reasons
    assert SmartUnavailableReason.SOURCE_UNAVAILABLE in reasons
    assert SmartUnavailableReason.NO_GOALS in reasons


def test_ownership_failure_is_not_converted_to_unavailable_context():
    error = RuntimeError("ownership unavailable")
    service, sources = _service(guard=Guard(error=error), wealth=_wealth())
    with pytest.raises(RuntimeError, match="ownership unavailable"):
        _context(service, SmartContextFeature.PLANNING)
    assert all(source.calls == 0 for source in sources.values())


def test_context_and_values_are_immutable():
    service, _ = _service(profile=_declared())
    context = _context(service, SmartContextFeature.PROFILE)
    with pytest.raises(FrozenInstanceError):
        context.feature = SmartContextFeature.HOME
    with pytest.raises(FrozenInstanceError):
        context.values[0].value = Decimal("0.00")


def test_override_model_preserves_offered_and_effective_values_without_persistence():
    value = SmartValue(
        key=SmartValueKey.PLANNING_CONTRIBUTION,
        value=Decimal("750.00"),
        value_type=SmartValueType.MONEY,
        semantic_type=SmartSemanticType.USER_OVERRIDE,
        owner=SmartValueOwner.PLANNING,
        source=SmartValueSource.USER_INPUT_REQUIRED,
        source_label="Planning · scenario override",
        state=SmartDefaultState.USER_OVERRIDE_ACTIVE,
        override_policy=SmartOverridePolicy.SCENARIO_OVERRIDE,
        offered_value=Decimal("500.00"),
        effective_value=Decimal("750.00"),
        override_reason="Scenario-specific contribution",
    )
    assert value.offered_value == Decimal("500.00")
    assert value.effective_value == Decimal("750.00")
    assert value.value == Decimal("750.00")


def test_context_contains_no_user_identity_or_raw_source_fields():
    service, _ = _service(
        profile=_declared(),
        candidates=(_candidate("ric_v1_confirmed"),),
        wealth=_wealth(),
    )
    for feature in SmartContextFeature:
        context = _context(service, feature)
        representation = repr(context).lower()
        assert str(USER_ID).lower() not in representation
        assert "private-account" not in representation
        assert "private-run" not in representation
        assert "raw_description" not in representation
        assert "cpf" not in representation


def test_no_smart_value_contains_float():
    service, _ = _service(
        profile=_declared(), health=_health(), goals=(_goal(),), wealth=_wealth()
    )
    for feature in SmartContextFeature:
        context = _context(service, feature)
        assert all(not isinstance(item.value, float) for item in context.values)


def test_health_source_bounds_partial_month_at_explicit_as_of_date():
    class Adapter:
        def __init__(self):
            self.bounds = None

        def get_monthly_facts(self, db, start, end):
            self.bounds = (start, end)
            return (_health(),)

    adapter = Adapter()
    result = HealthSmartContextSource(adapter).read_month(object(), as_of_date=AS_OF)
    assert result == _health()
    assert adapter.bounds == (
        datetime(2026, 10, 1, 0, 0, 0),
        datetime(2026, 10, 6, 0, 0, 0),
    )


def test_portfolio_source_maps_only_no_snapshot_to_unavailable():
    class Resolver:
        def __init__(self, message):
            self.message = message

        def resolve(self, db, current_user_id, as_of_date):
            raise PlanningPortfolioSourceUnavailableError(self.message)

    missing = PortfolioSmartContextSource(
        Resolver("No eligible investment portfolio snapshot is available for as_of_date.")
    )
    assert missing.read(object(), USER_ID, as_of_date=AS_OF) is None

    ownership = PortfolioSmartContextSource(
        Resolver("The authenticated user does not own the canonical portfolio tenant.")
    )
    with pytest.raises(PlanningPortfolioSourceUnavailableError):
        ownership.read(object(), USER_ID, as_of_date=AS_OF)
