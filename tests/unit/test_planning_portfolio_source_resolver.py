from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.application.exceptions.planning_portfolio_source_error import (
    PlanningPortfolioSourceAmbiguousError,
    PlanningPortfolioSourceInconsistentError,
    PlanningPortfolioSourceUnavailableError,
)
from backend.application.services.planning_portfolio_source_resolver import (
    PlanningPortfolioSourceResolver,
)
from backend.database.base import Base
from backend.domain.enums.provider_type import ProviderType
from backend.domain.enums.user_role import UserRole
from backend.domains.planning import InitialWealthScope, InitialWealthSource
from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus
from backend.infrastructure.persistence.models.user import UserModel
from backend.infrastructure.persistence.models.wealth.portfolio_snapshot import (
    PortfolioSnapshotModel,
)


@pytest.fixture
def portfolio_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            UserModel.__table__,
            SyncLogModel.__table__,
            PortfolioSnapshotModel.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _user(user_id):
    return UserModel(
        id=user_id,
        email=f"{user_id.hex}@example.test",
        name="Portfolio Owner",
        hashed_password="not-used",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 9, 1, 9, 0, 0),
        last_login_at=None,
    )


def _run(run_id, user_id, **overrides):
    values = {
        "id": run_id,
        "user_id": str(user_id),
        "provider": ProviderType.MYPROFIT_EVOLUCAO,
        "status": SyncStatus.SUCCESS,
        "start_time": datetime(2026, 9, 3, 10, 0, 0),
        "end_time": datetime(2026, 9, 3, 10, 1, 0),
    }
    values.update(overrides)
    return SyncLogModel(**values)


def _snapshot(scope, reference_month, amount, run_id, updated_at, **overrides):
    values = {
        "account_id": scope,
        "reference_month": reference_month,
        "patrimonio": Decimal(amount),
        "source_type": ProviderType.MYPROFIT_EVOLUCAO.value,
        "run_id": run_id,
        "created_at": datetime(2026, 9, 3, 10, 0, 0),
        "updated_at": updated_at,
    }
    values.update(overrides)
    return PortfolioSnapshotModel(**values)


def _persist(portfolio_db, user_id, runs=(), snapshots=(), extra_users=()):
    portfolio_db.add(_user(user_id))
    portfolio_db.add_all(_user(extra_user_id) for extra_user_id in extra_users)
    portfolio_db.add_all(runs)
    portfolio_db.add_all(snapshots)
    portfolio_db.commit()


def test_resolves_one_authorized_scope_with_exact_decimal_and_no_observed_at(portfolio_db):
    owner = uuid4()
    run_id = "run-2026-09"
    _persist(
        portfolio_db,
        owner,
        runs=[_run(run_id, owner.hex)],
        snapshots=[
            _snapshot(
                "myprofit-main",
                "2026-09",
                "123456.78",
                run_id,
                datetime(2026, 9, 3, 10, 0, 0),
            )
        ],
    )

    fact = PlanningPortfolioSourceResolver().resolve(
        portfolio_db,
        owner,
        date(2026, 9, 5),
    )

    assert fact.amount == Decimal("123456.78")
    assert type(fact.amount) is Decimal
    assert fact.source is InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT
    assert fact.scope is InitialWealthScope.INVESTMENT_PORTFOLIO
    assert fact.as_of.reference_month == "2026-09"
    assert fact.as_of.observed_at is None
    assert fact.provenance.account_id == "myprofit-main"
    assert fact.provenance.reference_month == "2026-09"
    assert fact.provenance.run_id == run_id
    assert fact.provenance.updated_at == datetime(2026, 9, 3, 10, 0, 0)


def test_rejects_zero_and_multiple_authorized_scopes(portfolio_db):
    owner = uuid4()
    _persist(portfolio_db, owner)

    resolver = PlanningPortfolioSourceResolver()
    with pytest.raises(PlanningPortfolioSourceUnavailableError):
        resolver.resolve(portfolio_db, owner, date(2026, 9, 5))

    portfolio_db.add_all(
        [
            _run("run-a", owner),
            _run("run-b", owner),
            _snapshot("scope-a", "2026-09", "1.00", "run-a", datetime(2026, 9, 3)),
            _snapshot("scope-b", "2026-09", "2.00", "run-b", datetime(2026, 9, 3)),
        ]
    )
    portfolio_db.commit()

    with pytest.raises(PlanningPortfolioSourceAmbiguousError):
        resolver.resolve(portfolio_db, owner, date(2026, 9, 5))


def test_rejects_authenticated_user_outside_the_single_tenant(portfolio_db):
    owner = uuid4()
    caller = uuid4()
    _persist(
        portfolio_db,
        owner,
        runs=[_run("run", owner)],
        snapshots=[_snapshot("scope", "2026-09", "1.00", "run", datetime(2026, 9, 3))],
    )

    with pytest.raises(PlanningPortfolioSourceUnavailableError):
        PlanningPortfolioSourceResolver().resolve(portfolio_db, caller, date(2026, 9, 5))


@pytest.mark.parametrize(
    "run_overrides",
    [
        {"status": SyncStatus.RUNNING},
        {"provider": ProviderType.MYPROFIT_ATIVOS},
    ],
)
def test_rejects_non_successful_or_incompatible_run(portfolio_db, run_overrides):
    owner = uuid4()
    _persist(
        portfolio_db,
        owner,
        runs=[_run("run-invalid", owner, **run_overrides)],
        snapshots=[
            _snapshot("scope", "2026-09", "1.00", "run-invalid", datetime(2026, 9, 3))
        ],
    )

    with pytest.raises(PlanningPortfolioSourceInconsistentError):
        PlanningPortfolioSourceResolver().resolve(portfolio_db, owner, date(2026, 9, 5))


def test_rejects_other_owned_run_despite_semantic_uuid_support(portfolio_db):
    owner = uuid4()
    other_owner = uuid4()
    _persist(
        portfolio_db,
        owner,
        runs=[_run("run-other", other_owner.hex)],
        snapshots=[
            _snapshot("scope", "2026-09", "1.00", "run-other", datetime(2026, 9, 3))
        ],
    )

    with pytest.raises(PlanningPortfolioSourceInconsistentError):
        PlanningPortfolioSourceResolver().resolve(portfolio_db, owner, date(2026, 9, 5))


def test_rejects_unknown_run(portfolio_db):
    owner = uuid4()
    _persist(
        portfolio_db,
        owner,
        snapshots=[
            _snapshot("scope", "2026-09", "1.00", "missing-run", datetime(2026, 9, 3))
        ],
    )

    with pytest.raises(PlanningPortfolioSourceInconsistentError):
        PlanningPortfolioSourceResolver().resolve(portfolio_db, owner, date(2026, 9, 5))


@pytest.mark.parametrize(
    ("reference_month", "updated_at", "as_of_date", "expected"),
    [
        ("2026-08", datetime(2026, 8, 31), date(2026, 9, 10), "eligible"),
        ("2026-09", datetime(2026, 9, 3), date(2026, 9, 5), "eligible"),
        ("2026-09", datetime(2026, 10, 2), date(2026, 9, 30), "unavailable"),
        ("2026-10", datetime(2026, 9, 20), date(2026, 9, 30), "unavailable"),
    ],
)
def test_latest_eligible_as_of_temporal_matrix(
    portfolio_db,
    reference_month,
    updated_at,
    as_of_date,
    expected,
):
    owner = uuid4()
    _persist(
        portfolio_db,
        owner,
        runs=[_run("run", owner)],
        snapshots=[_snapshot("scope", reference_month, "10.00", "run", updated_at)],
    )

    resolver = PlanningPortfolioSourceResolver()
    if expected == "eligible":
        assert resolver.resolve(portfolio_db, owner, as_of_date).as_of.reference_month == reference_month
    else:
        with pytest.raises(PlanningPortfolioSourceUnavailableError):
            resolver.resolve(portfolio_db, owner, as_of_date)


def test_selects_latest_eligible_month_and_falls_back_from_later_upsert(portfolio_db):
    owner = uuid4()
    _persist(
        portfolio_db,
        owner,
        runs=[_run("run-aug", owner), _run("run-sep", owner)],
        snapshots=[
            _snapshot("scope", "2026-08", "100.00", "run-aug", datetime(2026, 8, 31)),
            _snapshot("scope", "2026-09", "200.00", "run-sep", datetime(2026, 10, 2)),
        ],
    )

    fact = PlanningPortfolioSourceResolver().resolve(portfolio_db, owner, date(2026, 9, 30))

    assert fact.amount == Decimal("100.00")
    assert fact.as_of.reference_month == "2026-08"


def test_rejects_inconsistent_scope_with_invalid_reference_month(portfolio_db):
    owner = uuid4()
    _persist(
        portfolio_db,
        owner,
        runs=[_run("run", owner)],
        snapshots=[_snapshot("scope", "invalid", "1.00", "run", datetime(2026, 9, 3))],
    )

    with pytest.raises(PlanningPortfolioSourceInconsistentError):
        PlanningPortfolioSourceResolver().resolve(portfolio_db, owner, date(2026, 9, 5))


def test_rejects_scope_with_incompatible_snapshot_source(portfolio_db):
    owner = uuid4()
    _persist(
        portfolio_db,
        owner,
        runs=[_run("run", owner)],
        snapshots=[
            _snapshot("scope", "2026-08", "1.00", "run", datetime(2026, 8, 31)),
            _snapshot(
                "scope",
                "2026-09",
                "2.00",
                "run",
                datetime(2026, 9, 3),
                source_type="MANUAL",
            ),
        ],
    )

    with pytest.raises(PlanningPortfolioSourceInconsistentError):
        PlanningPortfolioSourceResolver().resolve(portfolio_db, owner, date(2026, 9, 5))


def test_rejects_single_tenant_break(portfolio_db):
    owner = uuid4()
    second_user = uuid4()
    _persist(
        portfolio_db,
        owner,
        runs=[_run("run", owner)],
        snapshots=[_snapshot("scope", "2026-09", "1.00", "run", datetime(2026, 9, 3))],
        extra_users=[second_user],
    )

    with pytest.raises(PlanningPortfolioSourceUnavailableError):
        PlanningPortfolioSourceResolver().resolve(portfolio_db, owner, date(2026, 9, 5))


def test_resolver_is_read_only_and_does_not_query_core_accounts_or_positions(portfolio_db):
    owner = uuid4()
    _persist(
        portfolio_db,
        owner,
        runs=[_run("run", owner)],
        snapshots=[_snapshot("scope", "2026-09", "1.00", "run", datetime(2026, 9, 3))],
    )
    statements = []
    event.listen(
        portfolio_db.bind,
        "before_cursor_execute",
        lambda _conn, _cursor, statement, _parameters, _context, _many: statements.append(statement),
    )

    PlanningPortfolioSourceResolver().resolve(portfolio_db, owner, date(2026, 9, 5))

    assert statements
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    normalized = [statement.lower() for statement in statements]
    assert all(" from accounts" not in statement for statement in normalized)
    assert all(" from position_snapshots" not in statement for statement in normalized)
    assert not portfolio_db.new
    assert not portfolio_db.dirty
    assert not portfolio_db.deleted
