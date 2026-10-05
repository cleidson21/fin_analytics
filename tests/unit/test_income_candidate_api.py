from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.dependencies.auth import get_current_user
from backend.api.routers import financial_context as financial_context_router
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.services.income_candidate_service import (
    IncomeCandidateService,
)
from backend.application.services.single_tenant_user_scope import (
    SingleTenantUserScopeGuard,
)
from backend.database.base import Base
from backend.domain.enums.user_role import UserRole
from backend.domains.pierre.models import Account, LegacyBase, Transaction
from backend.domains.smart_context import (
    RecurringIncomeDecisionState,
    RecurringIncomeEvidenceEngine,
)
from backend.infrastructure.persistence.models.smart_context import (
    DeclaredFinancialContextModel,
    RecurringIncomeDecisionModel,
)
from backend.infrastructure.persistence.models.user import UserModel
from backend.infrastructure.persistence.repositories.recurring_income_evidence import (
    RecurringIncomeLedgerReader,
)
from backend.infrastructure.persistence.repositories.smart_context import (
    RecurringIncomeDecisionRepository,
)
from backend.main import app


OWNER_ID = UUID("00000000-0000-0000-0000-000000000701")
OTHER_ID = UUID("00000000-0000-0000-0000-000000000702")
AS_OF_DATE = date(2026, 10, 5)
FIXED_NOW = datetime(2026, 10, 5, 12, 30, 0)
VALID_FINGERPRINT = f"sha256:{'0' * 64}"
EXPECTED_CANDIDATE_FIELDS = {
    "candidate_id",
    "evidence_state",
    "decision_state",
    "signature_version",
    "source",
    "evidence_fingerprint",
    "currency",
    "direction",
    "window_start",
    "window_end",
    "current_month_is_partial",
    "includes_current_month",
    "observed_months",
    "monthly_occurrences",
    "occurrence_count",
    "distinct_month_count",
    "first_occurrence_date",
    "latest_occurrence_date",
    "latest_amount",
    "typical_received_amount",
    "minimum_received_amount",
    "maximum_received_amount",
    "median_absolute_deviation",
    "risk_flags",
    "decided_at",
    "decision_updated_at",
}


def _user_model(user_id: UUID) -> UserModel:
    return UserModel(
        id=user_id,
        email=f"{user_id.hex}@example.test",
        name="Context Owner",
        hashed_password="not-used",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _current_user(user_id: UUID = OWNER_ID) -> UserResponseDTO:
    return UserResponseDTO(
        id=user_id,
        email=f"{user_id.hex}@example.test",
        name="Context Owner",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _transaction(
    external_id: str,
    occurred_on: date,
    *,
    amount: str = "4800.00",
    description: str = "Monthly income source",
    category: str | None = None,
) -> Transaction:
    return Transaction(
        provider="pierre",
        external_id=external_id,
        account_provider="pierre",
        account_external_id="account-a",
        description=description,
        original_description=description,
        category=category,
        original_category=category,
        amount=Decimal(amount),
        currency="BRL",
        date=datetime.combine(occurred_on, datetime.min.time()),
        status="POSTED",
        type="CREDIT",
        manual_transaction=False,
        governance_status="CLASSIFIED",
        economic_classification="ENTRADA",
        investment_name=None,
    )


def _seed_candidate(db, *, description: str = "Monthly income source") -> None:
    db.add_all(
        [
            _transaction("income-aug", date(2026, 8, 5), amount="4700.00", description=description),
            _transaction("income-sep", date(2026, 9, 5), amount="4800.00", description=description),
            _transaction(
                "income-oct",
                date(2026, 10, 5),
                amount="4900.00",
                description=description,
                category="Transferências para terceiros",
            ),
        ]
    )


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    app.openapi_schema = None
    yield
    app.dependency_overrides.clear()
    app.openapi_schema = None


@pytest.fixture
def income_candidate_api(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(
        engine,
        "connect",
        lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
    )
    Base.metadata.create_all(
        engine,
        tables=[
            UserModel.__table__,
            DeclaredFinancialContextModel.__table__,
            RecurringIncomeDecisionModel.__table__,
        ],
    )
    LegacyBase.metadata.create_all(
        engine,
        tables=[Account.__table__, Transaction.__table__],
    )
    session_factory = sessionmaker(bind=engine)
    with session_factory.begin() as db:
        db.add(_user_model(OWNER_ID))
        db.add(
            Account(
                provider="pierre",
                external_id="account-a",
                name="Account A",
                type="CHECKING",
            )
        )

    from backend.api.dependencies import financial_context as dependencies

    monkeypatch.setattr(dependencies, "SessionLocal", session_factory)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[
        financial_context_router.get_income_candidate_service
    ] = lambda: IncomeCandidateService(
        today=lambda: AS_OF_DATE,
        clock=lambda: FIXED_NOW,
    )

    with TestClient(app) as client:
        yield client, session_factory

    engine.dispose()


def _candidate(client: TestClient) -> dict:
    response = client.get("/api/v1/financial-context/income-candidates")
    assert response.status_code == 200
    candidates = response.json()["candidates"]
    assert len(candidates) == 1
    return candidates[0]


def _decision_request(candidate: dict) -> dict:
    return {"evidence_fingerprint": candidate["evidence_fingerprint"]}


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/api/v1/financial-context/income-candidates", None),
        (
            "POST",
            "/api/v1/financial-context/income-candidates/candidate/confirm",
            {"evidence_fingerprint": VALID_FINGERPRINT},
        ),
        (
            "POST",
            "/api/v1/financial-context/income-candidates/candidate/reject",
            {"evidence_fingerprint": VALID_FINGERPRINT},
        ),
        (
            "DELETE",
            "/api/v1/financial-context/income-candidates/candidate/decision",
            None,
        ),
    ],
)
def test_income_candidate_api_requires_authentication(method, path, payload):
    with TestClient(app) as client:
        response = client.request(method, path, json=payload)

    assert response.status_code == 401


def test_get_empty_candidate_collection_is_legitimate(income_candidate_api):
    client, _ = income_candidate_api

    response = client.get("/api/v1/financial-context/income-candidates")

    assert response.status_code == 200
    assert response.json() == {"as_of_date": "2026-10-05", "candidates": []}


def test_get_candidate_returns_ordered_privacy_safe_exact_evidence(income_candidate_api):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)

    response = client.get("/api/v1/financial-context/income-candidates")

    assert response.status_code == 200
    candidate = response.json()["candidates"][0]
    assert set(candidate) == EXPECTED_CANDIDATE_FIELDS
    assert candidate["evidence_state"] == "DETECTED_CANDIDATE"
    assert candidate["decision_state"] is None
    assert candidate["source"] == "GOVERNED_TRANSACTIONS"
    assert candidate["signature_version"] == 1
    assert candidate["currency"] == "BRL"
    assert candidate["direction"] == "CREDIT"
    assert candidate["window_start"] == "2026-05-01"
    assert candidate["window_end"] == "2026-10-05"
    assert candidate["current_month_is_partial"] is True
    assert candidate["includes_current_month"] is True
    assert candidate["observed_months"] == ["2026-08", "2026-09", "2026-10"]
    assert candidate["occurrence_count"] == 3
    assert candidate["distinct_month_count"] == 3
    assert candidate["latest_amount"] == "4900.00"
    assert candidate["typical_received_amount"] == "4800.00"
    assert candidate["minimum_received_amount"] == "4700.00"
    assert candidate["maximum_received_amount"] == "4900.00"
    assert candidate["median_absolute_deviation"] == "100.00"
    assert candidate["risk_flags"] == ["TRANSFER_AMBIGUITY"]
    assert candidate["evidence_fingerprint"].startswith("sha256:")
    assert len(candidate["evidence_fingerprint"]) == 71
    serialized = response.text.lower()
    for forbidden in (
        "description",
        "transaction_id",
        "external_id",
        "account_id",
        "account_scope",
        "source_signature",
        "user_id",
        OWNER_ID.hex,
        "cpf",
        "email",
        "counterparty",
        "payer",
        "receiver",
        "secret",
    ):
        assert forbidden not in serialized


def test_confirm_is_durable_idempotent_and_uses_one_decision_row(income_candidate_api):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    candidate = _candidate(client)
    path = f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}/confirm"

    first = client.post(path, json=_decision_request(candidate))
    second = client.post(path, json=_decision_request(candidate))

    assert first.status_code == second.status_code == 200
    assert first.json()["decision_state"] == "CONFIRMED_AS_INCOME"
    assert second.json()["decision_state"] == "CONFIRMED_AS_INCOME"
    with session_factory() as db:
        assert db.execute(
            select(func.count()).select_from(RecurringIncomeDecisionModel)
        ).scalar_one() == 1
        stored = db.execute(select(RecurringIncomeDecisionModel)).scalar_one()
        assert stored.decision == "CONFIRMED_AS_INCOME"
        assert stored.label is None
    assert _candidate(client)["decision_state"] == "CONFIRMED_AS_INCOME"


def test_reject_is_visible_and_can_replace_confirmation_without_duplicate(income_candidate_api):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    candidate = _candidate(client)
    base = f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}"

    assert client.post(f"{base}/confirm", json=_decision_request(candidate)).status_code == 200
    rejected = client.post(f"{base}/reject", json=_decision_request(candidate))

    assert rejected.status_code == 200
    assert rejected.json()["decision_state"] == "REJECTED"
    assert _candidate(client)["decision_state"] == "REJECTED"
    with session_factory() as db:
        rows = db.execute(select(RecurringIncomeDecisionModel)).scalars().all()
        assert len(rows) == 1
        assert rows[0].decision == "REJECTED"


@pytest.mark.parametrize(
    ("first_action", "second_action", "expected"),
    [
        ("reject", "confirm", "CONFIRMED_AS_INCOME"),
        ("confirm", "reject", "REJECTED"),
    ],
)
def test_decision_replacement_is_reversible(
    income_candidate_api,
    first_action,
    second_action,
    expected,
):
    client, _ = income_candidate_api
    with income_candidate_api[1].begin() as db:
        _seed_candidate(db)
    candidate = _candidate(client)
    base = f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}"
    payload = _decision_request(candidate)

    assert client.post(f"{base}/{first_action}", json=payload).status_code == 200
    response = client.post(f"{base}/{second_action}", json=payload)

    assert response.status_code == 200
    assert response.json()["decision_state"] == expected


@pytest.mark.parametrize("action", ["confirm", "reject"])
def test_reset_returns_current_candidate_to_evidence_only(income_candidate_api, action):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    candidate = _candidate(client)
    base = f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}"
    assert client.post(f"{base}/{action}", json=_decision_request(candidate)).status_code == 200

    reset = client.delete(f"{base}/decision")

    assert reset.status_code == 204
    assert _candidate(client)["decision_state"] is None
    with session_factory() as db:
        assert db.execute(
            select(func.count()).select_from(RecurringIncomeDecisionModel)
        ).scalar_one() == 0
    assert client.delete(f"{base}/decision").status_code == 404


def test_stale_confirmed_decision_is_preserved_and_can_be_reset(income_candidate_api):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    candidate = _candidate(client)
    base = f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}"
    assert client.post(f"{base}/confirm", json=_decision_request(candidate)).status_code == 200
    with session_factory.begin() as db:
        db.query(Transaction).delete()

    stale = _candidate(client)

    assert stale["candidate_id"] == candidate["candidate_id"]
    assert stale["evidence_state"] == "STALE"
    assert stale["decision_state"] == "CONFIRMED_AS_INCOME"
    assert stale["evidence_fingerprint"] is None
    assert stale["latest_amount"] is None
    assert client.delete(f"{base}/decision").status_code == 204
    response = client.get("/api/v1/financial-context/income-candidates")
    assert response.json()["candidates"] == []


def test_signature_version_mismatch_does_not_overlay_current_candidate(income_candidate_api):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    with session_factory.begin() as db:
        owner = SingleTenantUserScopeGuard().resolve(db, OWNER_ID)
        observations = RecurringIncomeLedgerReader().read_eligible_observations_for_scope(
            db,
            owner,
            as_of_date=AS_OF_DATE,
        )
        current = RecurringIncomeEvidenceEngine().detect(
            observations,
            as_of_date=AS_OF_DATE,
        )[0]
        RecurringIncomeDecisionRepository(db, owner).save(
            source_provider=current.source_provider,
            source_account_scope=current.source_account_scope,
            source_signature=current.source_signature,
            signature_version=2,
            decision=RecurringIncomeDecisionState.CONFIRMED_AS_INCOME,
            label=None,
            at=FIXED_NOW,
        )

    response = client.get("/api/v1/financial-context/income-candidates")

    assert response.status_code == 200
    candidates = response.json()["candidates"]
    assert len(candidates) == 2
    assert candidates[0]["signature_version"] == 1
    assert candidates[0]["decision_state"] is None
    assert candidates[0]["evidence_state"] == "DETECTED_CANDIDATE"
    assert candidates[1]["signature_version"] == 2
    assert candidates[1]["decision_state"] == "CONFIRMED_AS_INCOME"
    assert candidates[1]["evidence_state"] == "STALE"
    assert candidates[0]["candidate_id"] != candidates[1]["candidate_id"]


@pytest.mark.parametrize("action", ["confirm", "reject"])
def test_changed_evidence_returns_409_without_writing_decision(
    income_candidate_api,
    action,
):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    candidate = _candidate(client)
    with session_factory.begin() as db:
        db.add(_transaction("income-oct-extra", date(2026, 10, 4), amount="4850.00"))

    response = client.post(
        f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}/{action}",
        json=_decision_request(candidate),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Income candidate evidence changed. Refresh and try again."
    }
    with session_factory() as db:
        assert db.execute(
            select(func.count()).select_from(RecurringIncomeDecisionModel)
        ).scalar_one() == 0


def test_disappeared_or_forged_candidate_returns_same_non_enumerating_404(
    income_candidate_api,
):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    candidate = _candidate(client)
    with session_factory.begin() as db:
        db.query(Transaction).delete()

    disappeared = client.post(
        f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}/confirm",
        json=_decision_request(candidate),
    )
    forged = client.post(
        "/api/v1/financial-context/income-candidates/ric_v1_forged/confirm",
        json={"evidence_fingerprint": VALID_FINGERPRINT},
    )

    assert disappeared.status_code == forged.status_code == 404
    assert disappeared.json() == forged.json() == {
        "detail": "Income candidate is unavailable."
    }


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"evidence_fingerprint": 1},
        {"evidence_fingerprint": "bad"},
        {"evidence_fingerprint": VALID_FINGERPRINT, "user_id": str(OWNER_ID)},
        {"evidence_fingerprint": VALID_FINGERPRINT, "account_id": "account-a"},
        {"evidence_fingerprint": VALID_FINGERPRINT, "scope_id": "scope"},
        {"evidence_fingerprint": VALID_FINGERPRINT, "source_signature": "forged"},
        {"evidence_fingerprint": VALID_FINGERPRINT, "provider": "pierre"},
        {"evidence_fingerprint": VALID_FINGERPRINT, "label": "Salary"},
    ],
)
def test_decision_request_is_strict_and_rejects_owner_source_or_label_fields(
    income_candidate_api,
    payload,
):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    candidate = _candidate(client)

    response = client.post(
        f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}/confirm",
        json=payload,
    )

    assert response.status_code == 422


def test_wrong_user_and_multiple_users_fail_closed(income_candidate_api):
    client, session_factory = income_candidate_api
    app.dependency_overrides[get_current_user] = lambda: _current_user(OTHER_ID)
    wrong = client.get("/api/v1/financial-context/income-candidates")
    assert wrong.status_code == 422
    assert wrong.json() == {"detail": "Financial context is unavailable."}
    assert OWNER_ID.hex not in wrong.text

    app.dependency_overrides[get_current_user] = _current_user
    with session_factory.begin() as db:
        db.add(_user_model(OTHER_ID))
    ambiguous = client.get("/api/v1/financial-context/income-candidates")
    assert ambiguous.status_code == 422
    assert ambiguous.json() == {"detail": "Financial context is unavailable."}


def test_zero_users_fails_closed_instead_of_returning_empty_evidence(
    income_candidate_api,
):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        db.query(UserModel).delete()

    response = client.get("/api/v1/financial-context/income-candidates")

    assert response.status_code == 422
    assert response.json() == {"detail": "Financial context is unavailable."}


def test_get_and_decisions_never_mutate_transactions_or_profile(income_candidate_api):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    with session_factory() as db:
        before = tuple(
            db.execute(
                select(
                    Transaction.provider,
                    Transaction.external_id,
                    Transaction.governance_status,
                    Transaction.economic_classification,
                    Transaction.category,
                ).order_by(Transaction.external_id)
            ).all()
        )
    candidate = _candidate(client)
    base = f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}"
    assert client.post(f"{base}/confirm", json=_decision_request(candidate)).status_code == 200
    assert client.post(f"{base}/reject", json=_decision_request(candidate)).status_code == 200
    assert client.delete(f"{base}/decision").status_code == 204

    with session_factory() as db:
        after = tuple(
            db.execute(
                select(
                    Transaction.provider,
                    Transaction.external_id,
                    Transaction.governance_status,
                    Transaction.economic_classification,
                    Transaction.category,
                ).order_by(Transaction.external_id)
            ).all()
        )
        profile_count = db.execute(
            select(func.count()).select_from(DeclaredFinancialContextModel)
        ).scalar_one()
    assert after == before
    assert profile_count == 0


def test_mapping_failure_rolls_back_decision_write(income_candidate_api, monkeypatch):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)
    candidate = _candidate(client)

    def fail_mapping(*_args, **_kwargs):
        raise RuntimeError("mapping failed after write")

    monkeypatch.setattr(financial_context_router, "map_income_candidate", fail_mapping)
    response = client.post(
        f"/api/v1/financial-context/income-candidates/{candidate['candidate_id']}/confirm",
        json=_decision_request(candidate),
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal financial context error."}
    with session_factory() as db:
        assert db.execute(
            select(func.count()).select_from(RecurringIncomeDecisionModel)
        ).scalar_one() == 0


def test_openapi_exposes_exact_authenticated_b4_surface():
    schema = app.openapi()
    financial_context_paths = {
        path: sorted(operations)
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v1/financial-context")
    }

    assert financial_context_paths == {
        "/api/v1/financial-context/income-candidates": ["get"],
        "/api/v1/financial-context/income-candidates/{candidate_id}/confirm": ["post"],
        "/api/v1/financial-context/income-candidates/{candidate_id}/decision": ["delete"],
        "/api/v1/financial-context/income-candidates/{candidate_id}/reject": ["post"],
    }
    for path in financial_context_paths:
        for operation in schema["paths"][path].values():
            assert operation["security"]
    assert "/api/v1/financial-context" not in schema["paths"]
    assert set(schema["paths"]["/api/v1/profile/context"]) == {"get", "patch"}

    confirm = schema["paths"][
        "/api/v1/financial-context/income-candidates/{candidate_id}/confirm"
    ]["post"]
    request_ref = confirm["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    request_schema = schema["components"]["schemas"][request_ref.rsplit("/", 1)[-1]]
    assert request_schema["additionalProperties"] is False
    assert set(request_schema["properties"]) == {"evidence_fingerprint"}


def test_candidate_amounts_are_strings_and_never_json_numbers(income_candidate_api):
    client, session_factory = income_candidate_api
    with session_factory.begin() as db:
        _seed_candidate(db)

    candidate = _candidate(client)

    for field in (
        "latest_amount",
        "typical_received_amount",
        "minimum_received_amount",
        "maximum_received_amount",
        "median_absolute_deviation",
    ):
        assert type(candidate[field]) is str
