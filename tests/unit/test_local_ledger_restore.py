"""Mounted HTTP + real JWT/financial guards, synthetic SQLite and fake Pierre only."""
import json
import socket
import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.api.dependencies import auth, legacy_financial, ledger_import_history
from backend.api.dependencies.database import get_db_session
from backend.application.services.local_ledger_scope import CAPABILITIES, inventory
from backend.core.config import settings
from backend.domain.enums.user_role import UserRole
from backend.domains.pierre import pipeline
from backend.domains.pierre.models import Account, Category, GovernanceAuditLog, LegacyBase, Transaction
from backend.domains.pierre.repository import TransactionRepository
from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus
from backend.infrastructure.persistence.models.user import UserModel
from backend.infrastructure.security.jwt_service import JWTService
from backend.main import app
from scripts.certify_local_ledger import envelope, issue_certificate, reviewed_inventory, main as certify_main

OWNER = UUID("00000000-0000-0000-0000-000000009101")
OTHER = UUID("00000000-0000-0000-0000-000000009102")
SECRET = "synthetic-local-ledger-test-secret-not-real"


def user(uid):
    return UserModel(id=uid, email=f"synthetic-{uid.int}@example.test", name="Synthetic",
                     hashed_password="unusable", is_active=True, is_verified=True,
                     role=UserRole.VIEWER, created_at=datetime(2026, 1, 1))


def raw(txid, amount="0.10"):
    return {"id": txid, "account_id": "account-a", "account_name": "Reviewed A", "account_type": "BANK",
            "description": "Synthetic RAW", "amount": Decimal(amount), "currency_code": "BRL",
            "date": "2026-01-12T00:00:00", "status": "POSTED", "type": "DEBIT", "category": "New category"}


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    path = tmp_path / "synthetic.db"
    engine = create_engine(f"sqlite:///{path.as_posix()}", connect_args={"check_same_thread": False})
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    LegacyBase.metadata.create_all(engine)
    UserModel.__table__.create(engine)
    SyncLogModel.__table__.create(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add(user(OWNER))
        db.add_all([Account(provider="pierre", external_id="account-a", name="Reviewed A", type="BANK"),
                    Account(provider="pierre", external_id="account-b", name="Reviewed B", type="BANK"),
                    Category(provider="pierre", name="Existing category")])
        db.flush()
        db.add(Transaction(provider="pierre", external_id="existing", account_provider="pierre",
                           account_external_id="account-a", description="Previous RAW", amount=Decimal("17.10"),
                           currency="BRL", date=datetime(2026, 1, 12), status="POSTED", type="DEBIT",
                           manual_transaction=False, governance_status="CLASSIFIED", economic_classification="IGNORAR",
                           notes="Keep governance", investment_name="Synthetic", original_description="Keep original"))
        db.flush()
        db.add(GovernanceAuditLog(provider="pierre", external_id="existing", action="CREATE_CLASSIFICATION",
                                 after_json='{"governance_status":"CLASSIFIED","economic_classification":"IGNORAR"}',
                                 changed_at=datetime(2026, 1, 12), changed_by=None))
        db.commit()
    marker = tmp_path / "installation.json"
    marker.write_text(json.dumps({"installation_id": str(uuid4()), "generation": str(uuid4())}), encoding="utf-8")
    cert_path = tmp_path / "certificate.json"
    for key, value in {
        "JWT_SECRET": SECRET, "PIERRE_API_KEY": "synthetic-provider-credential",
        "ENVIRONMENT": "development", "LOCAL_LEDGER_ENABLED": True,
        "LOCAL_LEDGER_CERTIFICATE_FILE": str(cert_path), "LOCAL_LEDGER_INSTALLATION_FILE": str(marker),
    }.items():
        monkeypatch.setattr(settings, key, value)
    with sessions() as db:
        review = reviewed_inventory(db)
        review["connection_evidence"] = "Owner explicitly reviewed synthetic connection"
        review["account_confirmations"] = [{**a, "evidence": "Owner explicitly reviewed synthetic account"}
                                            for a in review["inventory"]["accounts"]]
        cert = issue_certificate(db, review, days=30, capabilities=set(CAPABILITIES))

    def save_cert(value=cert):
        cert_path.write_text(json.dumps(envelope(value)), encoding="utf-8")
    save_cert()
    monkeypatch.setattr(legacy_financial, "SessionLocal", sessions)
    monkeypatch.setattr(ledger_import_history, "SessionLocal", sessions)
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{path.as_posix()}")
    async_sessions = async_sessionmaker(async_engine, expire_on_commit=False)

    async def auth_db():
        async with async_sessions() as db:
            yield db
    monkeypatch.setattr(app, "dependency_overrides", {get_db_session: auth_db})
    assert auth.get_current_user not in app.dependency_overrides
    assert legacy_financial.require_certified_legacy_financial_scope not in app.dependency_overrides
    state = SimpleNamespace(payload={"success": True, "data": [raw("existing", "12.34"), raw("new")]},
                            calls=[], failure=None, hook=None)

    class FakePierre:
        def __init__(self):
            state.calls.append("constructed")
        async def get_transactions(self, *_args, **_kwargs):
            state.calls.append("fetched")
            if state.hook:
                state.hook()
            if state.failure:
                raise state.failure
            return state.payload
    monkeypatch.setattr(pipeline, "PierreConnector", FakePierre)
    monkeypatch.setattr(socket, "create_connection", lambda *_a, **_k: pytest.fail("Network forbidden"))

    def snapshot():
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
            return tuple(db.iterdump())
    token = JWTService(SECRET, 60, 7).create_access_token(OWNER)
    # Use the real issuer's public contract (same as existing credential suites).
    if not isinstance(token, str):
        raise AssertionError("Unexpected JWT issuer output")
    with TestClient(app, raise_server_exceptions=False) as client:
        yield SimpleNamespace(client=client, sessions=sessions, path=path, marker=marker,
                              cert_path=cert_path, cert=cert, save_cert=save_cert, state=state,
                              snapshot=snapshot, review=review, headers={"Authorization": f"Bearer {token}"})
        client.portal.call(async_engine.dispose)
    engine.dispose()


IMPORTS = ("/api/v1/pierre/import", "/api/v1/dashboard/import-pierre")


def import_request(ledger, endpoint):
    dates = {"start_date": "2026-01-01", "end_date": "2026-01-31"}
    return ledger.client.post(endpoint, headers=ledger.headers,
                              **({"json": dates} if endpoint.endswith("/import") else {"params": dates}))


@pytest.mark.parametrize("endpoint", IMPORTS)
def test_both_importers_atomic_idempotent_preserve_raw_governance_and_decimal(ledger, endpoint):
    response = import_request(ledger, endpoint)
    assert response.status_code == 200, response.text
    assert response.json().get("success", response.json().get("status") == "success")
    with ledger.sessions() as db:
        old = db.get(Transaction, ("pierre", "existing"))
        assert old.amount == Decimal("12.34")
        assert old.original_description == "Keep original"
        assert (old.governance_status, old.economic_classification, old.notes) == ("CLASSIFIED", "IGNORAR", "Keep governance")
        assert db.get(Transaction, ("pierre", "new")).amount == Decimal("0.10")
        assert db.query(GovernanceAuditLog).count() == 1
        assert db.query(GovernanceAuditLog).one().changed_by is None
    repeated = import_request(ledger, endpoint)
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["skipped"] == 2
    with ledger.sessions() as db:
        assert db.query(Transaction).count() == 2
        runs = db.query(SyncLogModel).all()
        assert len(runs) == 2 and all(r.status == SyncStatus.SUCCESS for r in runs)
        assert all(r.provider_metadata["certificate_id"] == str(ledger.cert.certificate_id) for r in runs)


@pytest.mark.parametrize("case", ["missing", "revoked", "expired", "signature", "database", "installation", "connection", "capability", "second-user", "unknown-account", "disabled", "production"])
@pytest.mark.parametrize("endpoint", IMPORTS)
def test_denials_have_no_writes_or_provider_construction(ledger, monkeypatch, case, endpoint):
    if case == "missing":
        ledger.cert_path.unlink()
    elif case == "signature":
        value = json.loads(ledger.cert_path.read_text())
        value["payload"]["accounts"][0]["external_id"] = "forged"
        ledger.cert_path.write_text(json.dumps(value))
    elif case == "second-user":
        with ledger.sessions() as db:
            db.add(user(OTHER)); db.commit()
    elif case == "unknown-account":
        with ledger.sessions() as db:
            db.add(Account(provider="pierre", external_id="unreviewed", name="Unreviewed", type="BANK")); db.commit()
    elif case in {"disabled", "production", "connection"}:
        monkeypatch.setattr(settings, {"disabled": "LOCAL_LEDGER_ENABLED", "production": "ENVIRONMENT", "connection": "PIERRE_API_KEY"}[case],
                            {"disabled": False, "production": "production", "connection": "another-synthetic-connection"}[case])
    else:
        changes = {"revoked": {"revoked": True}, "expired": {"expires_at": datetime.now(timezone.utc) - timedelta(days=1)},
                   "database": {"database_identity": "different"}, "installation": {"installation_id": uuid4()},
                   "capability": {"capabilities": frozenset({"read"})}}[case]
        ledger.save_cert(ledger.cert.model_copy(update=changes))
    before = ledger.snapshot()
    assert import_request(ledger, endpoint).status_code == 403
    assert ledger.snapshot() == before
    assert ledger.state.calls == []


@pytest.mark.parametrize("endpoint", IMPORTS)
@pytest.mark.parametrize("failure", ["unknown-source-account", "partial", "provider-exception", "persist", "revoked-during-fetch", "duplicate-conflict", "float"])
def test_import_failures_roll_back_every_financial_effect(ledger, monkeypatch, endpoint, failure):
    if failure == "unknown-source-account":
        ledger.state.payload["data"][1]["account_id"] = "outside"
    elif failure == "partial":
        ledger.state.payload["partial"] = True
    elif failure == "provider-exception":
        ledger.state.failure = RuntimeError("Synthetic partial fetch")
    elif failure == "persist":
        original = TransactionRepository.upsert
        def broken(self, db, data):
            if data["external_id"] == "new":
                raise RuntimeError("Synthetic persistence failure after first row")
            return original(self, db, data)
        monkeypatch.setattr(TransactionRepository, "upsert", broken)
    elif failure == "revoked-during-fetch":
        ledger.state.hook = lambda: ledger.save_cert(ledger.cert.model_copy(update={"revoked": True}))
    elif failure == "duplicate-conflict":
        ledger.state.payload["data"].append(raw("new", "0.20"))
    elif failure == "float":
        ledger.state.payload["data"][1]["amount"] = 0.1
    before = ledger.snapshot()
    response = import_request(ledger, endpoint)
    assert response.status_code in {403, 422, 502}, response.text
    assert ledger.snapshot() == before


READS = (
    "/api/v1/accounts", "/api/v1/transactions", "/api/v1/categories", "/api/v1/dashboard",
    "/api/v1/dashboard/summary-v2?month=2026-01", "/api/v1/dashboard/pacing-v2?month=2026-01",
    "/api/v1/dashboard/heatmap?month=2026-01", "/api/v1/dashboard/categories?month=2026-01",
    "/api/v1/governance/transactions", "/api/v1/governance/transactions/pierre/existing",
    "/api/v1/governance/transactions/pierre/existing/history", "/api/v1/governance/summary",
    "/api/v1/governance/audit-log", "/api/v1/dashboard/import-status",
)


@pytest.mark.parametrize("path", READS)
def test_adjacent_reads_require_real_certificate(ledger, path):
    before = ledger.snapshot()
    assert ledger.client.get(path, headers=ledger.headers).status_code == 200
    ledger.cert_path.unlink()
    assert ledger.client.get(path, headers=ledger.headers).status_code == 403
    assert ledger.snapshot() == before


def test_governance_and_history_are_scoped_and_actor_is_recorded(ledger):
    path = "/api/v1/governance/transactions/pierre/existing"
    before = ledger.snapshot()
    ledger.save_cert(ledger.cert.model_copy(update={"capabilities": frozenset({"read"})}))
    assert ledger.client.patch(path + "/classify", json={"economic_classification": "SAIDA"}, headers=ledger.headers).status_code == 403
    assert ledger.snapshot() == before
    ledger.save_cert()
    response = ledger.client.patch(path + "/classify", json={"economic_classification": "SAIDA"}, headers=ledger.headers)
    assert response.status_code == 200, response.text
    with ledger.sessions() as db:
        last = db.query(GovernanceAuditLog).order_by(GovernanceAuditLog.id.desc()).first()
        audit_id = last.id
        assert last.changed_by == str(OWNER)
    response = ledger.client.post(path + f"/rollback/{audit_id}", headers=ledger.headers)
    assert response.status_code == 200, response.text
    assert ledger.client.get("/api/v1/governance/transactions/other/outside", headers=ledger.headers).status_code == 404
    with ledger.sessions() as db:
        assert db.get(Transaction, ("pierre", "existing")).economic_classification == "IGNORAR"
        assert db.query(GovernanceAuditLog).count() == 3


def test_pierre_run_history_has_no_bypass_and_no_fake_rollback(ledger):
    assert import_request(ledger, IMPORTS[0]).status_code == 200
    with ledger.sessions() as db:
        run_id = db.query(SyncLogModel).one().id
    paths = ["/api/v1/governance/dashboard", "/api/v1/governance/imports",
             f"/api/v1/governance/imports/{run_id}", f"/api/v1/governance/imports/{run_id}/staging-items"]
    for path in paths:
        assert ledger.client.get(path, headers=ledger.headers).status_code == 200
    assert ledger.client.post(f"/api/v1/governance/imports/{run_id}/rollback", headers=ledger.headers).status_code == 409
    ledger.cert_path.unlink()
    before = ledger.snapshot()
    for path in paths:
        assert ledger.client.get(path, headers=ledger.headers).status_code == 403
    assert ledger.snapshot() == before


def test_offline_review_requires_evidence_and_does_not_change_database(ledger, tmp_path, monkeypatch):
    before = ledger.snapshot()
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{ledger.path.as_posix()}")
    review_path = tmp_path / "review.json"
    assert certify_main(["prepare", "--review", str(review_path)]) == 0
    ledger.cert_path.unlink()
    assert certify_main(["certify", "--review", str(review_path), "--capability", "read", "--confirm-reviewed-accounts", "--confirm-reviewed-connection"]) == 1
    review_path.write_text(json.dumps(ledger.review), encoding="utf-8")
    assert certify_main(["certify", "--review", str(review_path), "--capability", "read", "--confirm-reviewed-accounts", "--confirm-reviewed-connection"]) == 0
    assert ledger.client.get("/api/v1/accounts", headers=ledger.headers).status_code == 200
    assert certify_main(["revoke"]) == 0
    assert ledger.client.get("/api/v1/accounts", headers=ledger.headers).status_code == 403
    assert ledger.snapshot() == before


def test_proxy_stays_closed_without_provider_scope_contract(ledger):
    assert ledger.client.get("/api/v1/pierre/installments", headers=ledger.headers).status_code == 403
    assert ledger.state.calls == []


def test_second_authenticated_user_cannot_use_certificate_or_import_history(ledger):
    with ledger.sessions() as db:
        db.add(user(OTHER)); db.commit()
    other_token = JWTService(SECRET, 60, 7).create_access_token(str(OTHER))
    before = ledger.snapshot()
    assert ledger.client.get("/api/v1/accounts", headers={"Authorization": f"Bearer {other_token}"}).status_code == 403
    assert ledger.snapshot() == before and ledger.state.calls == []


def test_run_identifier_is_not_authorization_and_other_domains_are_not_certified_by_pierre(ledger):
    from backend.domain.enums.provider_type import ProviderType
    with ledger.sessions() as db:
        db.add(SyncLogModel(id="other-run", user_id=str(OTHER), provider=ProviderType.PIERRE,
                            status=SyncStatus.SUCCESS, provider_metadata={"staging_rows": [{"private": "synthetic"}]}))
        db.add(SyncLogModel(id="own-myprofit-run", user_id=str(OWNER), provider=ProviderType.MYPROFIT,
                            status=SyncStatus.RUNNING))
        db.commit()
    ledger.cert_path.unlink()
    for suffix in ("", "/staging-items"):
        assert ledger.client.get("/api/v1/governance/imports/other-run" + suffix, headers=ledger.headers).status_code == 404
    assert ledger.client.post("/api/v1/governance/imports/other-run/rollback", headers=ledger.headers).status_code == 404
    # This is run authorship access, not ownership approval for MyProfit finances.
    assert ledger.client.get("/api/v1/governance/imports/own-myprofit-run", headers=ledger.headers).status_code == 200


def test_partial_payload_and_orphaned_ledger_never_get_silently_certified(ledger):
    before = ledger.snapshot()
    ledger.state.payload["total"] = 99
    assert import_request(ledger, IMPORTS[0]).status_code == 422
    assert ledger.snapshot() == before
    with ledger.sessions() as db:
        db.add(GovernanceAuditLog(provider="pierre", external_id="orphan", action="ROLLBACK"))
        db.commit()
    assert ledger.client.get("/api/v1/accounts", headers=ledger.headers).status_code == 403


def test_scope_reassignment_is_allowed_only_between_reviewed_accounts(ledger):
    ledger.state.payload["data"][0]["account_id"] = "account-b"
    assert import_request(ledger, IMPORTS[0]).status_code == 200
    with ledger.sessions() as db:
        old = db.get(Transaction, ("pierre", "existing"))
        assert old.account_external_id == "account-b" and old.economic_classification == "IGNORAR"
    before = ledger.snapshot()
    ledger.state.payload["data"][0]["account_id"] = "not-reviewed"
    assert import_request(ledger, IMPORTS[0]).status_code == 403
    assert ledger.snapshot() == before


def test_missing_auth_and_inactive_policy_are_preserved(ledger):
    assert ledger.client.get("/api/v1/accounts").status_code == 401
    with ledger.sessions() as db:
        db.get(UserModel, OWNER).is_active = False
        db.commit()
    assert ledger.client.get("/api/v1/accounts", headers=ledger.headers).status_code == 400


def test_uppercase_legacy_adapter_namespace_is_preserved_without_duplicate_transactions(ledger):
    with ledger.sessions() as db:
        old_accounts = db.query(Account).all()
        for account in old_accounts:
            db.add(Account(provider="PIERRE", external_id=account.external_id, name=account.name, type=account.type))
        db.flush()
        old = db.get(Transaction, ("pierre", "existing"))
        old.provider = "PIERRE"
        old.account_provider = "PIERRE"
        db.query(GovernanceAuditLog).update({"provider": "PIERRE"})
        db.flush()
        for account in old_accounts:
            db.delete(account)
        db.commit()
        review = reviewed_inventory(db)
        review["connection_evidence"] = "Explicit synthetic connection review"
        review["account_confirmations"] = [{**a, "evidence": "Explicit synthetic account review"} for a in review["inventory"]["accounts"]]
        cert = issue_certificate(db, review, days=30, capabilities=set(CAPABILITIES))
    ledger.save_cert(cert)
    assert import_request(ledger, IMPORTS[0]).status_code == 200
    assert import_request(ledger, IMPORTS[1]).json()["skipped"] == 2
    with ledger.sessions() as db:
        assert db.query(Transaction).count() == 2
        assert db.get(Transaction, ("pierre", "existing")) is None
        assert db.get(Transaction, ("PIERRE", "existing")).economic_classification == "IGNORAR"
        assert db.query(GovernanceAuditLog).one().provider == "PIERRE"


def test_ambiguous_dual_namespace_is_denied_instead_of_merging_history(ledger):
    with ledger.sessions() as db:
        db.add(Account(provider="PIERRE", external_id="account-a", name="Ambiguous", type="BANK"))
        db.commit()
    before = ledger.snapshot()
    assert import_request(ledger, IMPORTS[0]).status_code == 403
    assert ledger.snapshot() == before and ledger.state.calls == []


@pytest.mark.asyncio
async def test_raw_http_boundary_parses_money_as_decimal_without_network(monkeypatch):
    import httpx
    from backend.domains.pierre.client import PierreHTTPClient
    monkeypatch.setattr(settings, "PIERRE_API_KEY", "synthetic-provider-only")
    factory = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, content=b'{"success":true,"data":[{"amount":0.10}]}', request=request
    ))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: factory(transport=transport, **kwargs))
    payload = await PierreHTTPClient(base_url="https://example.test").get("synthetic")
    assert payload["data"][0]["amount"] == Decimal("0.10")
    assert isinstance(payload["data"][0]["amount"], Decimal)


def test_encoded_url_cannot_downgrade_a_history_capability_to_read(ledger):
    ledger.save_cert(ledger.cert.model_copy(update={"capabilities": frozenset({"read"})}))
    before = ledger.snapshot()
    assert ledger.client.get("/api/v1/governance/transactions/pierre/existing/h%69story", headers=ledger.headers).status_code == 403
    assert ledger.client.get("/api/v1/governance/audit-l%6fg", headers=ledger.headers).status_code == 403
    assert ledger.snapshot() == before


_MINOR01_FIELDS = ("account_name", "account_type", "category", "original_description")


@pytest.mark.parametrize("endpoint", IMPORTS)
@pytest.mark.parametrize("missing", [*( (field,) for field in _MINOR01_FIELDS ), _MINOR01_FIELDS, "omitted"])
def test_minor01_reimport_preserves_null_or_omitted_optional_values(ledger, endpoint, missing):
    with ledger.sessions() as db:
        db.get(Transaction, ("pierre", "existing")).category = "Existing category"
        db.commit()
    incoming = {**raw("existing", "12.34"), "category": "Existing category", "original_description": "Keep original"}
    for field in _MINOR01_FIELDS if missing == "omitted" else missing:
        if missing == "omitted":
            incoming.pop(field)
        else:
            incoming[field] = None
    ledger.state.payload["data"] = [incoming]
    response = import_request(ledger, endpoint)
    assert response.status_code == 200, response.text
    with ledger.sessions() as db:
        account = db.get(Account, ("pierre", "account-a"))
        existing = db.get(Transaction, ("pierre", "existing"))
        assert (account.name, account.type) == ("Reviewed A", "BANK")
        assert (existing.category, existing.original_description) == ("Existing category", "Keep original")
        assert existing.amount == Decimal("12.34") and existing.description == "Synthetic RAW"
        assert (existing.governance_status, existing.economic_classification, existing.notes) == ("CLASSIFIED", "IGNORAR", "Keep governance")
        assert db.query(GovernanceAuditLog).count() == 1
        assert db.query(GovernanceAuditLog).one().changed_by is None
        assert db.get(Category, ("pierre", "Uncategorized")) is None
    repeated = import_request(ledger, endpoint)
    assert repeated.status_code == 200 and repeated.json()["skipped"] == 1
    with ledger.sessions() as db:
        assert db.query(Transaction).count() == 1
        assert db.query(GovernanceAuditLog).count() == 1


@pytest.mark.parametrize("endpoint", IMPORTS)
def test_minor01_non_null_corrections_keep_existing_sync_contract(ledger, endpoint):
    ledger.state.payload["data"] = [{
        **raw("existing", "12.34"), "account_name": "Updated reviewed account", "account_type": "CREDIT",
        "category": "Updated private category", "original_description": "Supplied original description",
    }]
    assert import_request(ledger, endpoint).status_code == 200
    with ledger.sessions() as db:
        account = db.get(Account, ("pierre", "account-a"))
        existing = db.get(Transaction, ("pierre", "existing"))
        assert (account.name, account.type) == ("Updated reviewed account", "CREDIT")
        assert (existing.category, existing.original_description) == ("Updated private category", "Supplied original description")
        assert existing.economic_classification == "IGNORAR" and existing.notes == "Keep governance"
        assert db.query(GovernanceAuditLog).count() == 1


@pytest.mark.parametrize("endpoint", IMPORTS)
def test_minor01_new_transaction_with_null_optionals_uses_only_reviewed_account(ledger, endpoint):
    ledger.state.payload["data"] = [{**raw("new"), **{field: None for field in _MINOR01_FIELDS}}]
    assert import_request(ledger, endpoint).status_code == 200
    with ledger.sessions() as db:
        account = db.get(Account, ("pierre", "account-a"))
        new = db.get(Transaction, ("pierre", "new"))
        assert (account.name, account.type) == ("Reviewed A", "BANK")
        assert new.account_external_id == "account-a" and new.account_provider == "pierre"
        assert new.category is None and new.original_description is None
        assert new.description == "Synthetic RAW" and new.amount == Decimal("0.10")
        assert new.governance_status == "PENDING" and new.economic_classification is None
        assert db.get(Category, ("pierre", "Uncategorized")) is None
        assert db.query(Account).count() == 2 and db.query(GovernanceAuditLog).count() == 1


@pytest.mark.parametrize("field", ["description", "account_id", "amount"])
def test_minor01_required_null_without_legitimate_fallback_is_rejected(ledger, field):
    incoming = {**raw("new"), **{key: None for key in _MINOR01_FIELDS}, field: None}
    ledger.state.payload["data"] = [incoming]
    before = ledger.snapshot()
    assert import_request(ledger, IMPORTS[0]).status_code == 422
    assert ledger.snapshot() == before


def test_minor01_nulls_do_not_admit_an_uncertified_account(ledger):
    ledger.state.payload["data"] = [{**raw("new"), **{field: None for field in _MINOR01_FIELDS}, "account_id": "unknown"}]
    before = ledger.snapshot()
    assert import_request(ledger, IMPORTS[0]).status_code == 403
    assert ledger.snapshot() == before


@pytest.mark.parametrize("endpoint", IMPORTS)
def test_minor01_persistence_failure_rolls_back_null_reimport_and_new_transaction(ledger, monkeypatch, endpoint):
    ledger.state.payload["data"] = [
        {**raw("existing", "12.34"), **{field: None for field in _MINOR01_FIELDS}}, raw("new"),
    ]
    original = TransactionRepository.upsert
    def broken(self, db, data):
        if data["external_id"] == "new":
            raise RuntimeError("Synthetic failure after the existing row update")
        return original(self, db, data)
    monkeypatch.setattr(TransactionRepository, "upsert", broken)
    before = ledger.snapshot()
    assert import_request(ledger, endpoint).status_code == 502
    assert ledger.snapshot() == before
