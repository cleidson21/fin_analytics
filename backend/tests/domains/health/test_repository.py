import pytest
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.domains.pierre.models import LegacyBase, Transaction, Account
from backend.domains.health.repository import HealthFinancialQuery

@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    LegacyBase.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()

    # Create an account
    acc = Account(
        provider='test_prov',
        external_id='test_acc',
        name='Test Account',
        type='CHECKING'
    )
    db.add(acc)
    db.commit()

    yield db
    db.close()

def _add_tx(
    db,
    ext_id,
    dt,
    amt,
    gov_status,
    econ_class,
    cat=None,
    account_provider='test_prov',
    account_external_id='test_acc',
):
    tx = Transaction(
        provider='test_prov',
        external_id=ext_id,
        account_provider=account_provider,
        account_external_id=account_external_id,
        description='Test TX',
        amount=Decimal(str(amt)),
        currency='BRL',
        date=datetime.strptime(dt, '%Y-%m-%d %H:%M:%S'),
        status='POSTED',
        type='CARD',
        governance_status=gov_status,
        economic_classification=econ_class,
        category=cat
    )
    db.add(tx)
    db.commit()

def test_health_query_classified_only(db_session):
    query = HealthFinancialQuery()

    _add_tx(db_session, '1', '2026-09-05 10:00:00', -100, 'CLASSIFIED', 'SAIDA')
    _add_tx(db_session, '2', '2026-09-06 10:00:00', -200, 'PENDING', None)
    _add_tx(db_session, '3', '2026-09-07 10:00:00', -50, 'CLASSIFIED', 'IGNORAR')

    start_date = datetime(2026, 9, 1)
    end_date = datetime(2026, 10, 1)

    # Test 1, 2, 3: Only CLASSIFIED and SAIDA should be counted
    cashflow = query.get_cashflow(db_session, start_date, end_date)
    assert cashflow['expense_total'] == Decimal('100.00')
    assert cashflow['income_total'] == Decimal('0.00')

def test_health_query_entrada_and_saida(db_session):
    query = HealthFinancialQuery()

    # Test 4: ENTRADA with positive value
    _add_tx(db_session, '1', '2026-09-05 10:00:00', 500, 'CLASSIFIED', 'ENTRADA')
    # Test 5: SAIDA with negative value
    _add_tx(db_session, '2', '2026-09-06 10:00:00', -150.50, 'CLASSIFIED', 'SAIDA')
    # Test 6: SAIDA with positive value (sometimes happens in API)
    _add_tx(db_session, '3', '2026-09-07 10:00:00', 50.25, 'CLASSIFIED', 'SAIDA')

    start_date = datetime(2026, 9, 1)
    end_date = datetime(2026, 10, 1)

    cashflow = query.get_cashflow(db_session, start_date, end_date)
    assert cashflow['income_total'] == Decimal('500.00')
    # abs(-150.50) + abs(50.25) = 200.75
    assert cashflow['expense_total'] == Decimal('200.75')

def test_health_query_date_limits(db_session):
    query = HealthFinancialQuery()

    # Test 7: Boundaries start <= date < end
    _add_tx(db_session, '1', '2026-08-31 23:59:59', -10, 'CLASSIFIED', 'SAIDA') # Before
    _add_tx(db_session, '2', '2026-09-01 00:00:00', -20, 'CLASSIFIED', 'SAIDA') # Exact start
    _add_tx(db_session, '3', '2026-09-15 12:00:00', -30, 'CLASSIFIED', 'SAIDA') # Inside
    _add_tx(db_session, '4', '2026-10-01 00:00:00', -40, 'CLASSIFIED', 'SAIDA') # Exact end (should be excluded)

    start_date = datetime(2026, 9, 1)
    end_date = datetime(2026, 10, 1)

    cashflow = query.get_cashflow(db_session, start_date, end_date)
    assert cashflow['expense_total'] == Decimal('50.00')  # 20 + 30

def test_health_query_monthly_aggregation(db_session):
    query = HealthFinancialQuery()

    # Test 8: Monthly aggregation
    _add_tx(db_session, '1', '2026-07-15 10:00:00', -100, 'CLASSIFIED', 'SAIDA')
    _add_tx(db_session, '2', '2026-08-15 10:00:00', -200, 'CLASSIFIED', 'SAIDA')
    _add_tx(db_session, '3', '2026-08-16 10:00:00', 500, 'CLASSIFIED', 'ENTRADA')
    _add_tx(db_session, '4', '2026-09-01 10:00:00', -300, 'CLASSIFIED', 'SAIDA')

    start_date = datetime(2026, 7, 1)
    end_date = datetime(2026, 10, 1)

    totals = query.get_monthly_totals(db_session, start_date, end_date)

    assert len(totals) == 3
    assert totals[0]['month'] == '2026-07'
    assert totals[0]['expense'] == Decimal('100.00')
    assert totals[0]['income'] == Decimal('0.00')

    assert totals[1]['month'] == '2026-08'
    assert totals[1]['expense'] == Decimal('200.00')
    assert totals[1]['income'] == Decimal('500.00')

    assert totals[2]['month'] == '2026-09'
    assert totals[2]['expense'] == Decimal('300.00')
    assert totals[2]['income'] == Decimal('0.00')

def test_health_query_category_grouping(db_session):
    query = HealthFinancialQuery()

    # Test 9: Category grouping
    _add_tx(db_session, '1', '2026-09-05 10:00:00', -100, 'CLASSIFIED', 'SAIDA', 'Food')
    _add_tx(db_session, '2', '2026-09-06 10:00:00', -50, 'CLASSIFIED', 'SAIDA', 'Food')
    _add_tx(db_session, '3', '2026-09-07 10:00:00', -200, 'CLASSIFIED', 'SAIDA', 'Transport')
    _add_tx(db_session, '4', '2026-09-08 10:00:00', 500, 'CLASSIFIED', 'ENTRADA', 'Salary') # Should be ignored (SAIDA only)
    _add_tx(db_session, '5', '2026-09-09 10:00:00', -30, 'CLASSIFIED', 'SAIDA', None) # Uncategorized

    start_date = datetime(2026, 9, 1)
    end_date = datetime(2026, 10, 1)

    categories = query.get_category_expenses(db_session, start_date, end_date)

    assert len(categories) == 3

    # Ordered by total descending
    assert categories[0]['category'] == 'Transport'
    assert categories[0]['expense_total'] == Decimal('200.00')

    assert categories[1]['category'] == 'Food'
    assert categories[1]['expense_total'] == Decimal('150.00')

    assert categories[2]['category'] == 'Uncategorized'
    assert categories[2]['expense_total'] == Decimal('30.00')

def test_health_query_consolidates_classified_transactions_across_accounts(db_session):
    """Financial Health aggregates all eligible accounts in the local tenant."""
    second_account = Account(
        provider='test_prov',
        external_id='test_acc_2',
        name='Second Test Account',
        type='CREDIT',
    )
    db_session.add(second_account)
    db_session.commit()

    query = HealthFinancialQuery()
    _add_tx(db_session, '1', '2026-09-05 10:00:00', 1000, 'CLASSIFIED', 'ENTRADA')
    _add_tx(db_session, '2', '2026-09-06 10:00:00', -200, 'CLASSIFIED', 'SAIDA')
    _add_tx(
        db_session, '3', '2026-09-07 10:00:00', 500, 'CLASSIFIED', 'ENTRADA',
        account_external_id='test_acc_2'
    )
    _add_tx(
        db_session, '4', '2026-09-08 10:00:00', -100, 'CLASSIFIED', 'SAIDA',
        account_external_id='test_acc_2'
    )

    start_date = datetime(2026, 9, 1)
    end_date = datetime(2026, 10, 1)

    cashflow = query.get_cashflow(db_session, start_date, end_date)
    assert cashflow['income_total'] == Decimal('1500.00')
    assert cashflow['expense_total'] == Decimal('300.00')


def test_health_query_normalizes_sqlite_aggregate_precision_to_decimal(db_session):
    """SQLite SUM(ABS(Numeric)) may return a binary-float artifact."""
    query = HealthFinancialQuery()
    _add_tx(db_session, 'precision-income-1', '2026-08-05 10:00:00', '0.10', 'CLASSIFIED', 'ENTRADA')
    _add_tx(db_session, 'precision-income-2', '2026-08-06 10:00:00', '0.20', 'CLASSIFIED', 'ENTRADA')
    _add_tx(db_session, 'precision-expense-1', '2026-08-07 10:00:00', '-0.10', 'CLASSIFIED', 'SAIDA', 'Precision')
    _add_tx(db_session, 'precision-expense-2', '2026-08-08 10:00:00', '-0.20', 'CLASSIFIED', 'SAIDA', 'Precision')

    start_date = datetime(2026, 8, 1)
    end_date = datetime(2026, 9, 1)

    cashflow = query.get_cashflow(db_session, start_date, end_date)
    monthly = query.get_monthly_totals(db_session, start_date, end_date)
    categories = query.get_category_expenses(db_session, start_date, end_date)

    assert isinstance(cashflow['income_total'], Decimal)
    assert isinstance(cashflow['expense_total'], Decimal)
    assert cashflow == {'income_total': Decimal('0.30'), 'expense_total': Decimal('0.30')}
    assert monthly == [{'month': '2026-08', 'income': Decimal('0.30'), 'expense': Decimal('0.30')}]
    assert isinstance(categories[0]['expense_total'], Decimal)
    assert categories == [{'category': 'Precision', 'expense_total': Decimal('0.30')}]
