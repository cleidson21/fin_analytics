from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from backend.application.exceptions.smart_context_ownership_error import (
    SmartContextOwnershipUnavailableError,
)
from backend.database.base import Base
from backend.domain.enums.user_role import UserRole
from backend.domains.pierre.models import Account, LegacyBase, Transaction
from backend.domains.smart_context import (
    RecurringIncomeEvidenceEngine,
    RecurringIncomeRiskFlag,
)
from backend.infrastructure.persistence.models.user import UserModel
from backend.infrastructure.persistence.repositories.recurring_income_evidence import (
    RecurringIncomeLedgerReader,
)


@pytest.fixture
def ledger_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[UserModel.__table__])
    LegacyBase.metadata.create_all(
        engine,
        tables=[Account.__table__, Transaction.__table__],
    )
    db = sessionmaker(bind=engine)()
    owner = uuid4()
    db.add(_user(owner))
    db.add_all(
        [
            Account(
                provider="pierre",
                external_id="account-a",
                name="Account A",
                type="CHECKING",
            ),
            Account(
                provider="pierre",
                external_id="account-b",
                name="Account B",
                type="CHECKING",
            ),
        ]
    )
    db.commit()
    try:
        yield db, owner, engine
    finally:
        db.close()
        engine.dispose()


def _user(user_id):
    return UserModel(
        id=user_id,
        email=f"{user_id.hex}@example.test",
        name="Context Owner",
        hashed_password="not-used",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 10, 5, 9, 0, 0),
        last_login_at=None,
    )


def _transaction(
    external_id: str,
    occurred_at: datetime,
    *,
    governance_status: str = "CLASSIFIED",
    economic_classification: str | None = "ENTRADA",
    transaction_type: str = "CREDIT",
    amount: str = "1000.00",
    description: str = "Recurring source",
    currency: str = "BRL",
    category: str | None = None,
    investment_name: str | None = None,
    account_external_id: str = "account-a",
) -> Transaction:
    return Transaction(
        provider="pierre",
        external_id=external_id,
        account_provider="pierre",
        account_external_id=account_external_id,
        description=description,
        original_description=description,
        category=category,
        original_category=category,
        amount=Decimal(amount),
        currency=currency,
        date=occurred_at,
        status="POSTED",
        type=transaction_type,
        manual_transaction=False,
        governance_status=governance_status,
        economic_classification=economic_classification,
        investment_name=investment_name,
    )


def test_reader_selects_only_structurally_eligible_governed_credits(ledger_db):
    db, owner, _ = ledger_db
    cases = [
        _transaction("eligible", datetime(2026, 10, 1), category=None),
        _transaction("pending", datetime(2026, 10, 2), governance_status="PENDING"),
        _transaction("outgoing", datetime(2026, 10, 3), economic_classification="SAIDA"),
        _transaction("ignored", datetime(2026, 10, 4), economic_classification="IGNORAR"),
        _transaction("debit", datetime(2026, 10, 5), transaction_type="DEBIT"),
        _transaction("refund", datetime(2026, 10, 6), transaction_type="REFUND"),
        _transaction("zero", datetime(2026, 10, 7), amount="0.00"),
        _transaction("negative", datetime(2026, 10, 8), amount="-10.00"),
        _transaction("blank", datetime(2026, 10, 9), description="   "),
        _transaction(
            "own-transfer",
            datetime(2026, 10, 10),
            category="Transferência mesma titularidade",
        ),
        _transaction(
            "investment",
            datetime(2026, 10, 11),
            investment_name="Governed investment evidence",
        ),
    ]
    db.add_all(cases)
    db.commit()

    observations = RecurringIncomeLedgerReader().read_eligible_observations(
        db,
        owner,
        as_of_date=datetime(2026, 10, 15).date(),
    )

    assert len(observations) == 1
    assert observations[0].amount == Decimal("1000.00")
    assert observations[0].provider == "pierre"
    assert observations[0].currency == "BRL"
    assert observations[0].source_record_key.startswith("sha256:")
    assert observations[0].account_scope.startswith("sha256:")


def test_generic_transfer_category_is_eligible_with_ambiguity_flag(ledger_db):
    db, owner, _ = ledger_db
    db.add(
        _transaction(
            "ambiguous-transfer",
            datetime(2026, 10, 1),
            category="Transferências para terceiros",
        )
    )
    db.commit()

    observation = RecurringIncomeLedgerReader().read_eligible_observations(
        db,
        owner,
        as_of_date=datetime(2026, 10, 15).date(),
    )[0]

    assert observation.risk_flags == (RecurringIncomeRiskFlag.TRANSFER_AMBIGUITY,)


def test_reader_bounds_the_query_to_the_six_month_window_and_as_of_day(ledger_db):
    db, owner, _ = ledger_db
    db.add_all(
        [
            _transaction("before", datetime(2026, 4, 30, 23, 59, 59)),
            _transaction("start", datetime(2026, 5, 1, 0, 0, 0)),
            _transaction("as-of", datetime(2026, 10, 15, 23, 59, 59)),
            _transaction("future", datetime(2026, 10, 16, 0, 0, 0)),
        ]
    )
    db.commit()

    observations = RecurringIncomeLedgerReader().read_eligible_observations(
        db,
        owner,
        as_of_date=datetime(2026, 10, 15).date(),
    )

    assert [item.occurred_on for item in observations] == [
        datetime(2026, 5, 1).date(),
        datetime(2026, 10, 15).date(),
    ]


def test_reader_keeps_provider_account_and_currency_scopes_separate(ledger_db):
    db, owner, _ = ledger_db
    db.add_all(
        [
            _transaction("a-brl", datetime(2026, 10, 1)),
            _transaction(
                "b-usd",
                datetime(2026, 10, 2),
                account_external_id="account-b",
                currency="USD",
            ),
        ]
    )
    db.commit()

    observations = RecurringIncomeLedgerReader().read_eligible_observations(
        db,
        owner,
        as_of_date=datetime(2026, 10, 15).date(),
    )

    assert len({item.account_scope for item in observations}) == 2
    assert {item.currency for item in observations} == {"BRL", "USD"}


def test_reader_output_composes_with_the_pure_candidate_engine(ledger_db):
    db, owner, _ = ledger_db
    db.add_all(
        [
            _transaction(f"month-{month}", datetime(2026, month, 5))
            for month in (1, 3, 5)
        ]
    )
    db.commit()

    observations = RecurringIncomeLedgerReader().read_eligible_observations(
        db,
        owner,
        as_of_date=datetime(2026, 5, 20).date(),
    )
    candidates = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=datetime(2026, 5, 20).date(),
    )

    assert len(candidates) == 1
    assert candidates[0].distinct_month_count == 3
    assert candidates[0].occurrence_count == 3


def test_reader_fails_closed_for_wrong_authenticated_user(ledger_db):
    db, _, _ = ledger_db

    with pytest.raises(SmartContextOwnershipUnavailableError):
        RecurringIncomeLedgerReader().read_eligible_observations(
            db,
            uuid4(),
            as_of_date=datetime(2026, 10, 15).date(),
        )


@pytest.mark.parametrize("user_count", [0, 2])
def test_reader_fails_closed_for_zero_or_ambiguous_users(ledger_db, user_count):
    db, owner, _ = ledger_db
    db.query(UserModel).delete()
    for _ in range(user_count):
        db.add(_user(uuid4()))
    db.commit()

    with pytest.raises(SmartContextOwnershipUnavailableError):
        RecurringIncomeLedgerReader().read_eligible_observations(
            db,
            owner,
            as_of_date=datetime(2026, 10, 15).date(),
        )


def test_reader_is_read_only_and_uses_two_bounded_selects(ledger_db, monkeypatch):
    db, owner, engine = ledger_db
    db.add(_transaction("eligible", datetime(2026, 10, 1)))
    db.commit()
    statements = []

    def capture_statement(_, __, statement, ___, ____, _____):
        statements.append(statement)

    def fail_commit():
        raise AssertionError("The B3 ledger reader must not commit.")

    event.listen(engine, "before_cursor_execute", capture_statement)
    monkeypatch.setattr(db, "commit", fail_commit)
    try:
        before_count = db.execute(select(func.count()).select_from(Transaction)).scalar_one()
        statements.clear()
        observations = RecurringIncomeLedgerReader().read_eligible_observations(
            db,
            owner,
            as_of_date=datetime(2026, 10, 15).date(),
        )
        reader_statements = tuple(statements)
        statements.clear()
        after_count = db.execute(select(func.count()).select_from(Transaction)).scalar_one()
    finally:
        event.remove(engine, "before_cursor_execute", capture_statement)

    assert len(observations) == 1
    assert before_count == after_count == 1
    assert len(reader_statements) == 2
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in reader_statements)
    assert not db.new
    assert not db.dirty
    assert not db.deleted
