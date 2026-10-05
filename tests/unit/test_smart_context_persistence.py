from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, inspect, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.application.services.single_tenant_user_scope import (
    SingleTenantUserScopeGuard,
)
from backend.database.base import Base
from backend.domain.enums.user_role import UserRole
from backend.domains.smart_context import RecurringIncomeDecisionState
from backend.infrastructure.persistence.models.smart_context import (
    DeclaredFinancialContextModel,
    RecurringIncomeDecisionModel,
)
from backend.infrastructure.persistence.models.user import UserModel
from backend.infrastructure.persistence.repositories.smart_context import (
    DeclaredContextRepository,
    RecurringIncomeDecisionRepository,
)


@pytest.fixture
def persistence_db():
    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(
        engine,
        tables=[
            UserModel.__table__,
            DeclaredFinancialContextModel.__table__,
            RecurringIncomeDecisionModel.__table__,
        ],
    )
    db = sessionmaker(bind=engine)()
    owner = uuid4()
    db.add(
        UserModel(
            id=owner,
            email=f"{owner.hex}@example.test",
            name="Context Owner",
            hashed_password="not-used",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            created_at=datetime(2026, 10, 5, 9, 0, 0),
            last_login_at=None,
        )
    )
    db.commit()
    try:
        yield db, owner
    finally:
        db.close()
        engine.dispose()


def _repositories(persistence_db):
    db, owner = persistence_db
    scope = SingleTenantUserScopeGuard().resolve(db, owner)
    return (
        db,
        owner,
        DeclaredContextRepository(db, scope),
        RecurringIncomeDecisionRepository(db, scope),
    )


def test_declared_context_roundtrips_exact_decimal_and_provenance(persistence_db):
    db, owner, repository, _ = _repositories(persistence_db)
    declared_at = datetime(2026, 10, 5, 10, 30, 0)

    persisted = repository.save(
        declared_monthly_gross_income=Decimal("12345.67"),
        income_as_of_date=date(2026, 10, 1),
        at=declared_at,
    )

    assert persisted.user_id == owner
    assert persisted.declared_monthly_gross_income == Decimal("12345.67")
    assert type(persisted.declared_monthly_gross_income) is Decimal
    assert persisted.currency.value == "BRL"
    assert persisted.income_period.value == "MONTHLY"
    assert persisted.income_basis.value == "GROSS"
    assert persisted.income_as_of_date == date(2026, 10, 1)
    assert persisted.declared_at == declared_at
    assert persisted.updated_at == declared_at
    assert db.in_transaction()


def test_declared_context_clear_is_null_not_zero(persistence_db):
    _, _, repository, _ = _repositories(persistence_db)
    assert repository.get() is None
    repository.save(
        declared_monthly_gross_income=Decimal("5000.00"),
        income_as_of_date=None,
        at=datetime(2026, 10, 5, 10, 0, 0),
    )

    cleared = repository.clear(at=datetime(2026, 10, 5, 11, 0, 0))

    assert cleared.declared_monthly_gross_income is None
    assert cleared.currency is None
    assert cleared.income_period is None
    assert cleared.income_basis is None
    assert cleared.income_as_of_date is None
    assert cleared.declared_at is None
    assert cleared.updated_at == datetime(2026, 10, 5, 11, 0, 0)


def test_repository_leaves_commit_control_to_caller(persistence_db):
    db, _, repository, _ = _repositories(persistence_db)
    repository.save(
        declared_monthly_gross_income=Decimal("1000.00"),
        income_as_of_date=None,
        at=datetime(2026, 10, 5, 10, 0, 0),
    )

    db.rollback()

    assert repository.get() is None


@pytest.mark.parametrize("invalid", [Decimal("0.00"), Decimal("-1.00"), Decimal("1.001")])
def test_declared_context_rejects_non_positive_or_subcent_values(persistence_db, invalid):
    _, _, repository, _ = _repositories(persistence_db)

    with pytest.raises(ValueError):
        repository.save(
            declared_monthly_gross_income=invalid,
            income_as_of_date=None,
            at=datetime(2026, 10, 5, 10, 0, 0),
        )


def test_declared_context_database_enforces_one_row_per_user(persistence_db):
    db, owner, _, _ = _repositories(persistence_db)
    values = {
        "user_id": owner,
        "declared_monthly_gross_income": None,
        "currency": None,
        "income_period": None,
        "income_basis": None,
        "income_as_of_date": None,
        "declared_at": None,
        "updated_at": datetime(2026, 10, 5, 10, 0, 0),
    }
    db.execute(insert(DeclaredFinancialContextModel.__table__).values(**values))

    with pytest.raises(IntegrityError):
        db.execute(insert(DeclaredFinancialContextModel.__table__).values(**values))


def test_declared_context_database_enforces_semantic_tuple(persistence_db):
    db, owner, _, _ = _repositories(persistence_db)

    with pytest.raises(IntegrityError):
        db.execute(
            insert(DeclaredFinancialContextModel.__table__).values(
                user_id=owner,
                declared_monthly_gross_income=Decimal("1000.00"),
                currency="USD",
                income_period="MONTHLY",
                income_basis="GROSS",
                income_as_of_date=None,
                declared_at=datetime(2026, 10, 5, 10, 0, 0),
                updated_at=datetime(2026, 10, 5, 10, 0, 0),
            )
        )


def test_declared_context_database_enforces_cent_scale(persistence_db):
    db, owner, _, _ = _repositories(persistence_db)

    with pytest.raises(IntegrityError):
        db.execute(
            insert(DeclaredFinancialContextModel.__table__).values(
                user_id=owner,
                declared_monthly_gross_income=Decimal("1000.001"),
                currency="BRL",
                income_period="MONTHLY",
                income_basis="GROSS",
                income_as_of_date=None,
                declared_at=datetime(2026, 10, 5, 10, 0, 0),
                updated_at=datetime(2026, 10, 5, 10, 0, 0),
            )
        )


def test_recurring_decision_roundtrip_update_and_reset(persistence_db):
    _, owner, _, repository = _repositories(persistence_db)
    first_time = datetime(2026, 10, 5, 10, 0, 0)
    second_time = datetime(2026, 10, 5, 11, 0, 0)

    confirmed = repository.save(
        source_provider="PIERRE",
        source_account_scope="scope-opaque-1",
        source_signature="sha256:opaque-signature",
        signature_version=1,
        decision=RecurringIncomeDecisionState.CONFIRMED_AS_INCOME,
        label="Renda principal",
        at=first_time,
    )
    rejected = repository.save(
        source_provider="PIERRE",
        source_account_scope="scope-opaque-1",
        source_signature="sha256:opaque-signature",
        signature_version=1,
        decision=RecurringIncomeDecisionState.REJECTED,
        label=None,
        at=second_time,
    )

    assert confirmed.user_id == owner
    assert confirmed.decision is RecurringIncomeDecisionState.CONFIRMED_AS_INCOME
    assert rejected.id == confirmed.id
    assert rejected.decision is RecurringIncomeDecisionState.REJECTED
    assert rejected.signature_version == 1
    assert rejected.decided_at == second_time
    assert repository.reset(
        source_signature="sha256:opaque-signature",
        signature_version=1,
    )
    assert repository.get(
        source_signature="sha256:opaque-signature",
        signature_version=1,
    ) is None


def test_decision_identity_cannot_change_resolved_scope(persistence_db):
    _, _, _, repository = _repositories(persistence_db)
    values = {
        "source_provider": "PIERRE",
        "source_account_scope": "scope-a",
        "source_signature": "sha256:opaque-signature",
        "signature_version": 1,
        "decision": RecurringIncomeDecisionState.CONFIRMED_AS_INCOME,
        "label": None,
        "at": datetime(2026, 10, 5, 10, 0, 0),
    }
    repository.save(**values)

    with pytest.raises(ValueError, match="cannot change"):
        repository.save(**{**values, "source_account_scope": "scope-b"})


def test_decision_database_prevents_contradictory_identity_rows(persistence_db):
    db, owner, _, _ = _repositories(persistence_db)
    common = {
        "user_id": owner,
        "source_provider": "PIERRE",
        "source_account_scope": "scope-opaque-1",
        "source_signature": "sha256:opaque-signature",
        "signature_version": 1,
        "label": None,
        "decided_at": datetime(2026, 10, 5, 10, 0, 0),
        "updated_at": datetime(2026, 10, 5, 10, 0, 0),
    }
    db.execute(
        insert(RecurringIncomeDecisionModel.__table__).values(
            id=uuid4(),
            decision="CONFIRMED_AS_INCOME",
            **common,
        )
    )

    with pytest.raises(IntegrityError):
        db.execute(
            insert(RecurringIncomeDecisionModel.__table__).values(
                id=uuid4(),
                decision="REJECTED",
                **common,
            )
        )


@pytest.mark.parametrize(
    ("decision", "signature_version"),
    [("DETECTED_CANDIDATE", 1), ("STALE", 1), ("REJECTED", 0)],
)
def test_decision_database_rejects_computed_states_and_invalid_versions(
    persistence_db,
    decision,
    signature_version,
):
    db, owner, _, _ = _repositories(persistence_db)

    with pytest.raises(IntegrityError):
        db.execute(
            insert(RecurringIncomeDecisionModel.__table__).values(
                id=uuid4(),
                user_id=owner,
                source_provider="PIERRE",
                source_account_scope="scope-opaque-1",
                source_signature="sha256:opaque-signature",
                signature_version=signature_version,
                decision=decision,
                label=None,
                decided_at=datetime(2026, 10, 5, 10, 0, 0),
                updated_at=datetime(2026, 10, 5, 10, 0, 0),
            )
        )


@pytest.mark.parametrize(
    "table",
    [DeclaredFinancialContextModel.__table__, RecurringIncomeDecisionModel.__table__],
)
def test_smart_context_tables_enforce_user_foreign_key(persistence_db, table):
    db, _, _, _ = _repositories(persistence_db)
    missing_owner = uuid4()
    if table is DeclaredFinancialContextModel.__table__:
        values = {
            "user_id": missing_owner,
            "declared_monthly_gross_income": None,
            "currency": None,
            "income_period": None,
            "income_basis": None,
            "income_as_of_date": None,
            "declared_at": None,
            "updated_at": datetime(2026, 10, 5, 10, 0, 0),
        }
    else:
        values = {
            "id": uuid4(),
            "user_id": missing_owner,
            "source_provider": "PIERRE",
            "source_account_scope": "scope-opaque-1",
            "source_signature": "sha256:opaque-signature",
            "signature_version": 1,
            "decision": "REJECTED",
            "label": None,
            "decided_at": datetime(2026, 10, 5, 10, 0, 0),
            "updated_at": datetime(2026, 10, 5, 10, 0, 0),
        }

    with pytest.raises(IntegrityError):
        db.execute(insert(table).values(**values))


def test_schema_contains_no_candidate_table_or_sensitive_payload_columns(persistence_db):
    db, _, _, _ = _repositories(persistence_db)
    inspector = inspect(db.bind)

    assert "recurring_income_candidates" not in inspector.get_table_names()
    declared_columns = {
        column["name"] for column in inspector.get_columns("user_declared_financial_context")
    }
    decision_columns = {
        column["name"] for column in inspector.get_columns("recurring_income_decisions")
    }
    forbidden = {
        "cpf",
        "phone",
        "birth_date",
        "employer",
        "raw_description",
        "counterparty",
        "account_number",
        "api_key",
        "secret",
        "token",
        "amount",
        "transaction_ids",
        "evidence",
    }

    assert declared_columns.isdisjoint(forbidden)
    assert decision_columns.isdisjoint(forbidden)
