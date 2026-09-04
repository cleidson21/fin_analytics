import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import date
from decimal import Decimal

from backend.application.use_cases.transactions import GetTransactionsUseCase, GetTransactionDetailsUseCase, GetDashboardSummaryV2UseCase
from backend.application.use_cases.get_categories import GetCategoriesUseCase
from backend.domain.entities.transaction import Transaction
from backend.domain.entities.category import Category

@pytest.mark.asyncio
async def test_get_transactions_use_case():
    tx_repo = AsyncMock()
    cat_repo = AsyncMock()
    acc_repo = AsyncMock()
    uc = GetTransactionsUseCase(tx_repo, cat_repo, acc_repo)
    
    # Mock data
    tx_id = uuid4()
    cat_id = uuid4()
    mock_tx = Transaction(
        id=tx_id,
        user_id=uuid4(),
        provider="manual",
        account_id=uuid4(),
        amount=Decimal("100.0"),
        direction="DEBIT",
        currency_code="BRL",
        description="Test",
        type="PURCHASE",
        status="CONFIRMED",
        transaction_date=date.today(),
        is_recurring=False,
        category_id=cat_id,
        hash="test_hash"
    )
    
    mock_cat = Category(
        id=cat_id,
        name="Food",
        slug="food",
        is_system=True
    )
    
    mock_acc = AsyncMock()
    mock_acc.name = "Test Account"
    
    tx_repo.find.return_value = ([mock_tx], 1)
    cat_repo.get_by_id.return_value = mock_cat
    acc_repo.get_by_id.return_value = mock_acc
    
    user_id = uuid4()
    result, total = await uc.execute(user_id=user_id)
    
    assert total == 1
    assert len(result) == 1
    assert result[0].id == tx_id
    assert result[0].category is not None
    assert result[0].category.name == "Food"

@pytest.mark.asyncio
async def test_get_transaction_details_use_case():
    tx_repo = AsyncMock()
    cat_repo = AsyncMock()
    acc_repo = AsyncMock()
    uc = GetTransactionDetailsUseCase(tx_repo, cat_repo, acc_repo)
    
    tx_id = uuid4()
    mock_tx = Transaction(
        id=tx_id,
        user_id=uuid4(),
        provider="manual",
        account_id=uuid4(),
        amount=Decimal("50.0"),
        direction="DEBIT",
        currency_code="BRL",
        description="Test Details",
        type="PURCHASE",
        status="CONFIRMED",
        transaction_date=date.today(),
        is_recurring=False,
        hash="test_hash_2"
    )
    
    mock_acc = AsyncMock()
    mock_acc.name = "Test Account Details"
    
    tx_repo.get_by_id.return_value = mock_tx
    acc_repo.get_by_id.return_value = mock_acc
    
    result = await uc.execute(transaction_id=tx_id)
    assert result is not None
    assert result.id == tx_id
    assert result.description == "Test Details"

@pytest.mark.asyncio
async def test_get_dashboard_summary_v2_use_case():
    tx_repo = AsyncMock()
    uc = GetDashboardSummaryV2UseCase(tx_repo)
    
    tx_repo.get_monthly_totals.side_effect = [
        {"income": 5000.0, "expense": 2000.0}, # current month
        {"income": 4000.0, "expense": 1000.0}  # previous month
    ]
    
    result = await uc.execute("2026-07")
    
    assert result.month == "2026-07"
    assert result.receitas.current == 5000.0
    assert result.receitas.previous == 4000.0
    assert result.despesas.current == 2000.0
    assert result.despesas.previous == 1000.0
    
@pytest.mark.asyncio
async def test_get_categories_use_case():
    cat_repo = AsyncMock()
    uc = GetCategoriesUseCase(cat_repo)
    
    mock_cat = Category(
        id=uuid4(),
        name="Lazer",
        slug="lazer",
        is_system=True
    )
    cat_repo.get_all.return_value = [mock_cat]
    
    result = await uc.execute(include_system=True)
    assert len(result) == 1
    assert result[0].name == "Lazer"
