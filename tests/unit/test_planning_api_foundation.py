"""Contract tests for the 10.3.8-B Planning API foundation only."""

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import get_args

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from backend.api.dependencies.planning import CurrentPlanningUser, PlanningReadSession
from backend.api.planning_errors import raise_planning_error
from backend.api.planning_mapping import (
    build_projection_assumptions,
    build_user_initial_wealth_fact,
    map_initial_wealth_fact,
    map_projection_assumptions,
    serialize_decimal,
)
from backend.api.routers.planning import router
from backend.application.dtos.planning_dto import (
    GoalCurrentAmountInitialWealthRequestDTO,
    InitialWealthSelectorRequestDTO,
    ProjectionAssumptionsRequestDTO,
    StrictDecimalString,
    UserProvidedInitialWealthRequestDTO,
)
from backend.domains.planning.assumptions import (
    ContributionTiming,
    OutputMode,
    ProjectionAssumptions,
    RateBasis,
    ReturnType,
)
from backend.domains.planning.facts import (
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    PlanningFactAsOf,
    PlanningFactProvenance,
)
from backend.main import app


def _assumptions_payload(**overrides):
    payload = {
        "as_of_date": "2026-09-16",
        "scenario_monthly_contribution": "1000.00",
        "expected_return_rate": "0.08",
        "return_type": "NOMINAL",
        "output_mode": "NOMINAL",
        "inflation_rate": None,
        "horizon_months": 12,
        "target_date": None,
        "rate_basis": "EFFECTIVE_ANNUAL",
        "contribution_timing": "END_OF_MONTH",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    "value, expected",
    [
        ("0", Decimal("0")),
        ("0.08", Decimal("0.08")),
        ("1000.00", Decimal("1000.00")),
        ("-0.50", Decimal("-0.50")),
        ("0.12345678901234567890123456789", Decimal("0.12345678901234567890123456789")),
    ],
)
def test_strict_decimal_string_accepts_plain_finite_strings(value, expected):
    assert TypeAdapter(StrictDecimalString).validate_python(value) == expected


@pytest.mark.parametrize(
    "value",
    [0, 0.08, 1000, True, False, None, "NaN", "Infinity", "-Infinity", "1e3", " 1.00", "1.00 "],
)
def test_strict_decimal_string_rejects_numbers_nonfinite_scientific_and_whitespace(value):
    with pytest.raises(ValidationError):
        TypeAdapter(StrictDecimalString).validate_python(value)


def test_strict_decimal_and_source_selector_contracts_hold_after_real_json_parsing():
    payload = _assumptions_payload(expected_return_rate="0.080000")

    request = ProjectionAssumptionsRequestDTO.model_validate_json(json.dumps(payload))
    assert request.expected_return_rate == Decimal("0.080000")
    assert request.expected_return_rate.as_tuple().exponent == -6

    for invalid_value in (0, 0.08, True, None, "NaN", "1e3", " 0.08 "):
        with pytest.raises(ValidationError):
            ProjectionAssumptionsRequestDTO.model_validate_json(
                json.dumps(_assumptions_payload(expected_return_rate=invalid_value))
            )

    selector = TypeAdapter(InitialWealthSelectorRequestDTO)
    for forged_payload in (
        {
            "source": "INVESTMENT_PORTFOLIO_SNAPSHOT",
            "account_id": "external-account",
        },
        {
            "source": "GOAL_CURRENT_AMOUNT",
            "goal_id": "00000000-0000-0000-0000-000000000001",
            "amount": "999999999.00",
        },
    ):
        with pytest.raises(ValidationError):
            selector.validate_json(json.dumps(forged_payload))


def test_declared_decimal_scale_is_preserved_until_domain_validation():
    request = ProjectionAssumptionsRequestDTO.model_validate(
        _assumptions_payload(scenario_monthly_contribution="1.000")
    )

    assert request.scenario_monthly_contribution == Decimal("1.000")
    assert request.scenario_monthly_contribution.as_tuple().exponent == -3
    with pytest.raises(ValueError, match="at most two decimal places"):
        build_projection_assumptions(request)


def test_projection_assumptions_builder_preserves_exact_decimal_date_enum_and_horizon_values():
    request = ProjectionAssumptionsRequestDTO.model_validate(
        _assumptions_payload(
            scenario_monthly_contribution="1000.10",
            expected_return_rate="0.080000",
            target_date=None,
        )
    )

    assumptions = build_projection_assumptions(request)

    assert assumptions == ProjectionAssumptions(
        as_of_date=date(2026, 9, 16),
        scenario_monthly_contribution=Decimal("1000.10"),
        expected_return_rate=Decimal("0.080000"),
        return_type=ReturnType.NOMINAL,
        output_mode=OutputMode.NOMINAL,
        inflation_rate=None,
        horizon_months=12,
        rate_basis=RateBasis.EFFECTIVE_ANNUAL,
        contribution_timing=ContributionTiming.END_OF_MONTH,
    )


@pytest.mark.parametrize(
    "overrides, expected_message",
    [
        (
            {"return_type": "REAL", "output_mode": "NOMINAL"},
            "REAL return to NOMINAL",
        ),
        (
            {"horizon_months": 12, "target_date": "2027-09-01"},
            "exactly one horizon source",
        ),
    ],
)
def test_projection_assumptions_builder_leaves_semantic_validation_to_domain(
    overrides,
    expected_message,
):
    request = ProjectionAssumptionsRequestDTO.model_validate(
        _assumptions_payload(**overrides)
    )

    with pytest.raises(ValueError, match=expected_message):
        build_projection_assumptions(request)


@pytest.mark.parametrize("value", [True, False, "12", 12.0])
def test_horizon_request_does_not_coerce_bool_string_or_float(value):
    with pytest.raises(ValidationError):
        ProjectionAssumptionsRequestDTO.model_validate(
            _assumptions_payload(horizon_months=value)
        )


def test_user_provided_selector_constructs_only_user_provided_fact_without_clock_invention():
    observed_at = "2026-09-16T12:30:45+03:00"
    request = UserProvidedInitialWealthRequestDTO.model_validate(
        {
            "source": "USER_PROVIDED_SCENARIO",
            "amount": "130000.00",
            "observed_at": observed_at,
        }
    )

    fact = build_user_initial_wealth_fact(request)

    assert fact.source is InitialWealthSource.USER_PROVIDED_SCENARIO
    assert fact.scope is InitialWealthScope.USER_PROVIDED_SCENARIO
    assert fact.amount == Decimal("130000.00")
    assert fact.as_of.observed_at == datetime.fromisoformat(observed_at)
    assert fact.provenance.source_table == "planning_request"
    assert fact.provenance.source_type == "USER_PROVIDED_SCENARIO"
    assert fact.provenance.goal_id is None
    assert fact.provenance.created_at is None
    assert fact.provenance.updated_at is None


@pytest.mark.parametrize(
    "payload",
    [
        {"source": "INVESTMENT_PORTFOLIO_SNAPSHOT", "account_id": "Myprofit"},
        {
            "source": "GOAL_CURRENT_AMOUNT",
            "goal_id": "00000000-0000-0000-0000-000000000001",
            "amount": "999999999.00",
        },
        {
            "source": "GOAL_CURRENT_AMOUNT",
            "goal_id": "00000000-0000-0000-0000-000000000001",
            "provenance": {"goal_id": "00000000-0000-0000-0000-000000000001"},
        },
        {
            "source": "USER_PROVIDED_SCENARIO",
            "amount": "10.00",
            "observed_at": "2026-09-16T12:00:00",
            "provenance": {"source_table": "goals"},
        },
    ],
)
def test_selector_rejects_forged_certified_fact_fields(payload):
    with pytest.raises(ValidationError):
        TypeAdapter(InitialWealthSelectorRequestDTO).validate_python(payload)


def test_goal_selector_is_only_goal_identity_and_no_certified_amount_or_provenance():
    request = GoalCurrentAmountInitialWealthRequestDTO.model_validate(
        {
            "source": "GOAL_CURRENT_AMOUNT",
            "goal_id": "00000000-0000-0000-0000-000000000001",
        }
    )

    assert str(request.goal_id) == "00000000-0000-0000-0000-000000000001"
    assert not hasattr(request, "amount")
    assert not hasattr(request, "provenance")


def test_initial_wealth_response_mapper_serializes_decimal_and_omits_internal_table_name():
    fact = InitialWealthFact(
        source=InitialWealthSource.GOAL_CURRENT_AMOUNT,
        amount=Decimal("130000.00"),
        as_of=PlanningFactAsOf(observed_at=datetime(2026, 9, 16, 12, tzinfo=timezone.utc)),
        scope=InitialWealthScope.GOAL,
        provenance=PlanningFactProvenance(
            source_table="goals",
            source_type="USER_GOVERNED_GOAL",
            goal_id=None,
            created_at=datetime(2026, 1, 1, 9, 0, 0),
            updated_at=datetime(2026, 9, 16, 12, 0, 0),
        ),
    )

    encoded = json.loads(map_initial_wealth_fact(fact).model_dump_json())

    assert encoded["amount"] == "130000.00"
    assert isinstance(encoded["amount"], str)
    assert encoded["as_of"]["observed_at"] == "2026-09-16T12:00:00Z"
    assert encoded["provenance"]["source_type"] == "USER_GOVERNED_GOAL"
    assert "source_table" not in encoded["provenance"]


def test_projection_assumptions_response_mapper_preserves_decimal_representation_without_rounding():
    assumptions = ProjectionAssumptions(
        as_of_date=date(2026, 9, 16),
        scenario_monthly_contribution=Decimal("1000.10"),
        expected_return_rate=Decimal("0.080000"),
        return_type=ReturnType.NOMINAL,
        output_mode=OutputMode.REAL,
        inflation_rate=Decimal("0.040000"),
        horizon_months=12,
        rate_basis=RateBasis.EFFECTIVE_ANNUAL,
        contribution_timing=ContributionTiming.END_OF_MONTH,
    )

    encoded = json.loads(map_projection_assumptions(assumptions).model_dump_json())

    assert encoded["scenario_monthly_contribution"] == "1000.10"
    assert encoded["expected_return_rate"] == "0.080000"
    assert encoded["inflation_rate"] == "0.040000"
    assert isinstance(encoded["expected_return_rate"], str)


@pytest.mark.parametrize("value", [Decimal("130000.00"), Decimal("0.080000")])
def test_decimal_response_serializer_never_uses_float(value):
    assert serialize_decimal(value) == str(value)


def test_local_error_mapping_preserves_existing_detail_convention_without_global_handler():
    with pytest.raises(HTTPException) as validation:
        raise_planning_error(ValueError("invalid Planning request"))
    assert validation.value.status_code == 422
    assert validation.value.detail == "invalid Planning request"

    with pytest.raises(HTTPException) as arithmetic:
        raise_planning_error(ArithmeticError("internal recurrence detail"))
    assert arithmetic.value.status_code == 500
    assert arithmetic.value.detail == "Planning calculation could not be completed."


def test_router_keeps_the_relative_prefix_and_only_approved_planning_routes():
    assert router.prefix == "/planning"
    assert router.tags == ["Planning"]
    assert {route.path for route in router.routes} == {
        "/planning/goals/overview",
        "/planning/goals/batch-contribution-preview",
        "/planning/goals/budget-preview",
        "/planning/goals/{goal_id}/context",
        "/planning/goals/{goal_id}/progress",
        "/planning/goals/{goal_id}/projection",
        "/planning/projection",
        "/planning/target-achievement",
        "/planning/required-contribution",
        "/planning/scenarios/compare",
    }


def test_planning_dependency_annotations_keep_existing_auth_and_sync_reader_boundaries():
    user_annotation = get_args(CurrentPlanningUser)
    session_annotation = get_args(PlanningReadSession)

    assert user_annotation[0].__name__ == "UserResponseDTO"
    assert session_annotation[0] is Session
    assert user_annotation[1].dependency.__name__ == "get_current_user"
    assert session_annotation[1].dependency.__name__ == "get_db"


def test_app_starts_and_planning_openapi_has_no_fake_or_unapproved_operation():
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    planning_paths = {
        path: sorted(operations)
        for path, operations in response.json()["paths"].items()
        if path.startswith("/api/v1/planning")
    }
    assert planning_paths == {
        "/api/v1/planning/goals/overview": ["get"],
        "/api/v1/planning/goals/batch-contribution-preview": ["post"],
        "/api/v1/planning/goals/budget-preview": ["post"],
        "/api/v1/planning/goals/{goal_id}/context": ["get"],
        "/api/v1/planning/goals/{goal_id}/progress": ["get"],
        "/api/v1/planning/goals/{goal_id}/projection": ["post"],
        "/api/v1/planning/projection": ["post"],
        "/api/v1/planning/required-contribution": ["post"],
        "/api/v1/planning/scenarios/compare": ["post"],
        "/api/v1/planning/target-achievement": ["post"],
    }


def test_openapi_schema_primitives_are_strings_and_selector_includes_only_approved_sources():
    assumptions_schema = ProjectionAssumptionsRequestDTO.model_json_schema()
    selector_schema = TypeAdapter(InitialWealthSelectorRequestDTO).json_schema()

    assert assumptions_schema["properties"]["scenario_monthly_contribution"]["type"] == "string"
    assert assumptions_schema["properties"]["expected_return_rate"]["type"] == "string"
    assert assumptions_schema["properties"]["as_of_date"]["type"] == "string"
    assert assumptions_schema["properties"]["as_of_date"]["format"] == "date"
    assert "pattern" in assumptions_schema["properties"]["expected_return_rate"]
    assert "INVESTMENT_PORTFOLIO_SNAPSHOT" in json.dumps(selector_schema)
    assert "GOAL_CURRENT_AMOUNT" in json.dumps(selector_schema)
    assert "USER_PROVIDED_SCENARIO" in json.dumps(selector_schema)
