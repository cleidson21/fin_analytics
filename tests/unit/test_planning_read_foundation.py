from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.database.base import Base
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domains.pierre.models import Account, LegacyBase, Transaction
from backend.domains.planning import (
    InitialWealthScope,
    InitialWealthSource,
    PlanningGoalReadQuery,
    PlanningHealthReadAdapter,
    PlanningPortfolioReadQuery,
)
from backend.infrastructure.persistence.models.goal import GoalModel
from backend.infrastructure.persistence.models.user import UserModel
from backend.infrastructure.persistence.models.wealth.portfolio_snapshot import (
    PortfolioSnapshotModel,
)


@pytest.fixture
def planning_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            UserModel.__table__,
            GoalModel.__table__,
            PortfolioSnapshotModel.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def health_db():
    engine = create_engine("sqlite:///:memory:")
    LegacyBase.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(
        Account(
            provider="test",
            external_id="planning-health",
            name="Planning Health",
            type="CHECKING",
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _goal(user_id, **overrides):
    now = datetime(2026, 9, 16, 12, 0, 0)
    values = {
        "id": uuid4(),
        "user_id": user_id,
        "name": "Reserva Planejada",
        "description": "Goal read boundary",
        "goal_type": GoalType.EMERGENCY_RESERVE,
        "target_amount": Decimal("1000.10"),
        "target_date": date(2027, 12, 31),
        "status": GoalStatus.ACTIVE,
        "created_at": now,
        "updated_at": now,
        "current_amount": Decimal("0.10"),
        "priority": 1,
        "monthly_contribution": Decimal("0.20"),
        "linked_account_id": "manual-reference",
        "assumptions_json": '{"ignored": true}',
    }
    values.update(overrides)
    return GoalModel(**values)


def _snapshot(account_id, reference_month, amount, **overrides):
    values = {
        "account_id": account_id,
        "reference_month": reference_month,
        "patrimonio": Decimal(amount),
        "source_type": "MYPROFIT_EVOLUCAO",
        "run_id": f"run-{account_id}-{reference_month}",
        "created_at": datetime(2026, 9, 1, 10, 0, 0),
        "updated_at": datetime(2026, 9, 10, 11, 0, 0),
    }
    values.update(overrides)
    return PortfolioSnapshotModel(**values)


def _health_transaction(external_id, when, amount, classification):
    return Transaction(
        provider="test",
        external_id=external_id,
        account_provider="test",
        account_external_id="planning-health",
        description="Planning read test",
        amount=Decimal(amount),
        currency="BRL",
        date=when,
        status="POSTED",
        type="TRANSFER",
        governance_status="CLASSIFIED",
        economic_classification=classification,
    )


def test_goal_read_preserves_decimal_fields_and_ignores_assumptions(planning_db):
    user_id = uuid4()
    model = _goal(user_id)
    planning_db.add(model)
    planning_db.commit()

    fact = PlanningGoalReadQuery().get_goal(planning_db, model.id, user_id)

    assert fact is not None
    assert fact.goal_id == model.id
    assert fact.user_id == user_id
    assert fact.target_amount == Decimal("1000.10")
    assert fact.current_amount == Decimal("0.10")
    assert fact.goal_planned_monthly_contribution == Decimal("0.20")
    assert isinstance(fact.target_amount, Decimal)
    assert isinstance(fact.current_amount, Decimal)
    assert isinstance(fact.goal_planned_monthly_contribution, Decimal)
    assert not hasattr(fact, "assumptions_json")


def test_goal_read_preserves_null_and_explicit_zero(planning_db):
    user_id = uuid4()
    missing = _goal(user_id, current_amount=None, monthly_contribution=None)
    zero = _goal(
        user_id,
        current_amount=Decimal("0.00"),
        monthly_contribution=Decimal("0.00"),
    )
    planning_db.add_all([missing, zero])
    planning_db.commit()

    missing_fact = PlanningGoalReadQuery().get_goal(planning_db, missing.id, user_id)
    zero_fact = PlanningGoalReadQuery().get_goal(planning_db, zero.id, user_id)

    assert missing_fact is not None
    assert missing_fact.current_amount is None
    assert missing_fact.goal_planned_monthly_contribution is None
    assert zero_fact is not None
    assert zero_fact.current_amount == Decimal("0.00")
    assert zero_fact.goal_planned_monthly_contribution == Decimal("0.00")


def test_goal_read_enforces_ownership(planning_db):
    owner_id = uuid4()
    other_user_id = uuid4()
    model = _goal(owner_id)
    planning_db.add(model)
    planning_db.commit()

    reader = PlanningGoalReadQuery()
    assert reader.get_goal(planning_db, model.id, owner_id) is not None
    assert reader.get_goal(planning_db, model.id, other_user_id) is None
    assert reader.get_goal(planning_db, uuid4(), owner_id) is None


def test_goal_list_is_owned_ordered_and_decimal_safe(planning_db):
    owner_id = uuid4()
    other_user_id = uuid4()
    later = datetime(2026, 9, 17, 12, 0, 0)
    priority_two = _goal(owner_id, priority=2, name="Priority two")
    priority_one = _goal(
        owner_id,
        priority=1,
        name="Priority one",
        created_at=later,
        updated_at=later,
    )
    foreign = _goal(other_user_id, priority=1, name="Foreign")
    planning_db.add_all([priority_two, priority_one, foreign])
    planning_db.commit()

    facts = PlanningGoalReadQuery().list_goals(planning_db, owner_id)

    assert [fact.name for fact in facts] == ["Priority one", "Priority two"]
    assert all(fact.user_id == owner_id for fact in facts)
    assert all(type(fact.target_amount) is Decimal for fact in facts)


def test_goal_list_uses_one_owned_select_and_stable_tie_breakers(planning_db):
    owner_id = uuid4()
    other_user_id = uuid4()
    created_at = datetime(2026, 9, 17, 12, 0, 0)
    first_id = UUID("00000000-0000-0000-0000-000000000001")
    second_id = UUID("00000000-0000-0000-0000-000000000002")
    planning_db.add_all(
        [
            _goal(owner_id, id=second_id, priority=1, created_at=created_at),
            _goal(owner_id, id=first_id, priority=1, created_at=created_at),
            _goal(other_user_id, priority=1, created_at=created_at),
        ]
    )
    planning_db.commit()
    statements = []
    event.listen(
        planning_db.bind,
        "before_cursor_execute",
        lambda _conn, _cursor, statement, _parameters, _context, _many:
            statements.append(statement),
    )

    facts = PlanningGoalReadQuery().list_goals(planning_db, owner_id)

    assert [fact.goal_id for fact in facts] == [first_id, second_id]
    assert len(statements) == 1
    assert statements[0].lstrip().upper().startswith("SELECT")
    assert "goals.user_id" in statements[0]
    assert "portfolio" not in statements[0].lower()
    assert "position_snapshots" not in statements[0].lower()
    assert not planning_db.new
    assert not planning_db.dirty
    assert not planning_db.deleted


def test_selected_goal_batch_uses_one_owned_query_and_preserves_request_order(
    planning_db,
):
    owner_id = uuid4()
    other_user_id = uuid4()
    first = _goal(owner_id, name="First")
    second = _goal(owner_id, name="Second")
    foreign = _goal(other_user_id, name="Foreign")
    planning_db.add_all([first, second, foreign])
    planning_db.commit()
    first_id = first.id
    second_id = second.id
    foreign_id = foreign.id
    statements = []
    event.listen(
        planning_db.bind,
        "before_cursor_execute",
        lambda _conn, _cursor, statement, _parameters, _context, _many:
            statements.append(statement),
    )

    facts = PlanningGoalReadQuery().get_goals_by_ids(
        planning_db,
        (second_id, foreign_id, first_id),
        owner_id,
    )

    assert [fact.goal_id for fact in facts] == [second_id, first_id]
    assert all(fact.user_id == owner_id for fact in facts)
    assert len(statements) == 1
    assert statements[0].lstrip().upper().startswith("SELECT")
    assert "goals.user_id" in statements[0]
    assert "portfolio" not in statements[0].lower()
    assert not planning_db.new
    assert not planning_db.dirty
    assert not planning_db.deleted


def test_goal_initial_wealth_requires_present_current_amount(planning_db):
    user_id = uuid4()
    missing = _goal(user_id, current_amount=None)
    zero = _goal(user_id, current_amount=Decimal("0.00"))
    planning_db.add_all([missing, zero])
    planning_db.commit()
    reader = PlanningGoalReadQuery()

    missing_goal = reader.get_goal(planning_db, missing.id, user_id)
    zero_goal = reader.get_goal(planning_db, zero.id, user_id)

    assert missing_goal is not None
    assert zero_goal is not None
    assert reader.current_amount_as_initial_wealth(missing_goal) is None
    zero_wealth = reader.current_amount_as_initial_wealth(zero_goal)
    assert zero_wealth is not None
    assert zero_wealth.amount == Decimal("0.00")
    assert zero_wealth.source is InitialWealthSource.GOAL_CURRENT_AMOUNT
    assert zero_wealth.scope is InitialWealthScope.GOAL
    assert zero_wealth.provenance.goal_id == zero.id


def test_goal_money_never_crosses_float_boundary(planning_db):
    user_id = uuid4()
    model = _goal(user_id)
    planning_db.add(model)
    planning_db.commit()

    fact = PlanningGoalReadQuery().get_goal(planning_db, model.id, user_id)

    assert fact is not None
    assert fact.current_amount + fact.goal_planned_monthly_contribution == Decimal("0.30")
    assert type(fact.current_amount) is Decimal
    assert type(fact.goal_planned_monthly_contribution) is Decimal


def test_portfolio_read_is_account_scoped_and_uses_latest_reference_month(planning_db):
    planning_db.add_all(
        [
            _snapshot("account-a", "2026-07", "100.10"),
            _snapshot("account-a", "2026-08", "200.20"),
            _snapshot("account-b", "2026-09", "999.99"),
        ]
    )
    planning_db.commit()

    fact = PlanningPortfolioReadQuery().get_latest_investment_wealth(
        planning_db,
        "account-a",
    )

    assert fact is not None
    assert fact.amount == Decimal("200.20")
    assert isinstance(fact.amount, Decimal)
    assert fact.source is InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT
    assert fact.scope is InitialWealthScope.INVESTMENT_PORTFOLIO
    assert fact.as_of.reference_month == "2026-08"
    assert fact.provenance.account_id == "account-a"
    assert fact.provenance.reference_month == "2026-08"
    assert fact.provenance.source_type == "MYPROFIT_EVOLUCAO"
    assert fact.provenance.run_id == "run-account-a-2026-08"
    assert fact.provenance.updated_at == datetime(2026, 9, 10, 11, 0, 0)


def test_portfolio_read_returns_none_for_account_without_snapshot(planning_db):
    reader = PlanningPortfolioReadQuery()

    assert reader.get_latest_investment_wealth(planning_db, "missing-account") is None
    with pytest.raises(ValueError, match="account_id is required"):
        reader.get_latest_investment_wealth(planning_db, "  ")


def test_portfolio_read_only_selects_portfolio_snapshots(planning_db):
    planning_db.add(_snapshot("account-a", "2026-08", "200.20"))
    planning_db.commit()
    statements = []
    event.listen(
        planning_db.bind,
        "before_cursor_execute",
        lambda _conn, _cursor, statement, _parameters, _context, _many:
            statements.append(statement),
    )

    PlanningPortfolioReadQuery().get_latest_investment_wealth(
        planning_db,
        "account-a",
    )

    assert statements
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    assert all("portfolio_snapshots" in statement for statement in statements)
    assert all("position_snapshots" not in statement for statement in statements)
    assert not planning_db.new
    assert not planning_db.dirty
    assert not planning_db.deleted


def test_goal_and_portfolio_origins_remain_separate_facts(planning_db):
    user_id = uuid4()
    goal = _goal(user_id, current_amount=Decimal("113000.00"))
    planning_db.add(goal)
    planning_db.add(_snapshot("Myprofit", "2026-09", "112888.91"))
    planning_db.commit()

    goal_reader = PlanningGoalReadQuery()
    goal_fact = goal_reader.get_goal(planning_db, goal.id, user_id)
    assert goal_fact is not None
    goal_wealth = goal_reader.current_amount_as_initial_wealth(goal_fact)
    portfolio_wealth = PlanningPortfolioReadQuery().get_latest_investment_wealth(
        planning_db,
        "Myprofit",
    )

    assert goal_wealth is not None
    assert portfolio_wealth is not None
    assert goal_wealth.source is InitialWealthSource.GOAL_CURRENT_AMOUNT
    assert portfolio_wealth.source is InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT
    assert goal_wealth.amount == Decimal("113000.00")
    assert portfolio_wealth.amount == Decimal("112888.91")
    assert not hasattr(goal_reader, "get_initial_wealth")
    assert not hasattr(PlanningPortfolioReadQuery(), "get_initial_wealth")


def test_health_adapter_reuses_certified_facts_and_preserves_gaps(health_db):
    health_db.add_all(
        [
            _health_transaction(
                "june-income",
                datetime(2026, 6, 5),
                "1000.10",
                "ENTRADA",
            ),
            _health_transaction(
                "june-expense",
                datetime(2026, 6, 6),
                "-800.20",
                "SAIDA",
            ),
            _health_transaction(
                "august-income",
                datetime(2026, 8, 5),
                "500.00",
                "ENTRADA",
            ),
            _health_transaction(
                "august-expense",
                datetime(2026, 8, 6),
                "-700.00",
                "SAIDA",
            ),
        ]
    )
    health_db.commit()

    facts = PlanningHealthReadAdapter().get_monthly_facts(
        health_db,
        datetime(2026, 6, 1),
        datetime(2026, 9, 1),
    )

    assert [fact.reference_month for fact in facts] == ["2026-06", "2026-08"]
    assert facts[0].total_income == Decimal("1000.10")
    assert facts[0].total_expense == Decimal("800.20")
    assert facts[0].net_cashflow == Decimal("199.90")
    assert facts[0].savings_amount == facts[0].net_cashflow
    assert facts[1].savings_amount == Decimal("-200.00")
    assert all(isinstance(fact.total_income, Decimal) for fact in facts)
    assert all(isinstance(fact.total_expense, Decimal) for fact in facts)


def test_health_adapter_returns_empty_without_certified_months(health_db):
    facts = PlanningHealthReadAdapter().get_monthly_facts(
        health_db,
        datetime(2026, 1, 1),
        datetime(2026, 2, 1),
    )

    assert facts == ()


def test_planning_queries_are_read_only(planning_db):
    user_id = uuid4()
    goal = _goal(user_id)
    planning_db.add(goal)
    planning_db.add(_snapshot("account-a", "2026-08", "200.20"))
    planning_db.commit()
    statements = []
    event.listen(
        planning_db.bind,
        "before_cursor_execute",
        lambda _conn, _cursor, statement, _parameters, _context, _many:
            statements.append(statement),
    )

    PlanningGoalReadQuery().get_goal(planning_db, goal.id, user_id)
    PlanningPortfolioReadQuery().get_latest_investment_wealth(
        planning_db,
        "account-a",
    )

    assert statements
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    assert not planning_db.new
    assert not planning_db.dirty
    assert not planning_db.deleted
