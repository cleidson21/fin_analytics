"""
Testes unitários do PierreImportService.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.application.dtos.provider_dtos import ProviderTransactionDTO, ProviderAccountDTO
from backend.application.services.pierre_import_service import PierreImportService


# ================================================================= #
#  Helper
# ================================================================= #

def make_service(mock_provider=None, mock_tx_repo=None, mock_acc_repo=None) -> PierreImportService:
    provider = mock_provider or MagicMock()
    tx_repo = mock_tx_repo or AsyncMock()
    acc_repo = mock_acc_repo or AsyncMock()
    tx_repo.bulk_upsert = AsyncMock(return_value={"inserted": 0, "skipped": 0})
    return PierreImportService(pierre_provider=provider, transaction_repo=tx_repo, account_repo=acc_repo)


def make_dto(**kwargs) -> ProviderTransactionDTO:
    defaults = {
        "id": "pierre_001",
        "account_id": "acc_aaa",
        "amount": 200.0,
        "direction": "DEBIT",
        "description": "Supermercado Extra",
        "transaction_date": date(2024, 3, 5),
        "is_recurring": False,
    }
    
    inst_count = kwargs.pop("installment_count", None)
    inst_current = kwargs.pop("installment_current", None)
    purch_id = kwargs.pop("purchase_id", None)
    
    defaults.update(kwargs)
    
    dto = ProviderTransactionDTO(**defaults)
    dto.effective_installment_count = lambda: inst_count
    dto.effective_installment_current = lambda: inst_current
    dto.effective_purchase_id = lambda: purch_id
    
    return dto


# ================================================================= #
#  _to_entity tests
# ================================================================= #

class TestToEntity:
    def _get_service(self):
        return make_service()

    def test_basic_conversion(self):
        service = self._get_service()
        dto = make_dto()
        entity = service._to_entity(dto, uuid4())
        assert entity.provider.value == "PIERRE"
        assert entity.external_id == "pierre_001"
        assert entity.amount == Decimal("200")
        assert entity.direction.value == "DEBIT"
        assert entity.transaction_date == date(2024, 3, 5)

    def test_description_normalization(self):
        service = self._get_service()
        dto = make_dto(description="  mercado  extra  ")
        entity = service._to_entity(dto, uuid4())
        assert entity.description == "mercado extra"

    def test_description_control_chars_removed(self):
        service = self._get_service()
        dto = make_dto(description="Loja\x00Extra\x1f")
        entity = service._to_entity(dto, uuid4())
        assert "\x00" not in entity.description
        assert "\x1f" not in entity.description

    def test_description_empty_uses_fallback(self):
        service = self._get_service()
        dto = make_dto(description="   ")
        entity = service._to_entity(dto, uuid4())
        assert entity.description == "Sem descrição"

    def test_type_mapping_purchase(self):
        service = self._get_service()
        dto = make_dto(type="purchase")
        assert service._to_entity(dto, uuid4()).type.value == "PURCHASE"

    def test_type_mapping_transfer(self):
        service = self._get_service()
        dto = make_dto(type="transferência")
        assert service._to_entity(dto, uuid4()).type.value == "TRANSFER"

    def test_type_fallback_debit(self):
        service = self._get_service()
        dto = make_dto(type=None, direction="DEBIT")
        assert service._to_entity(dto, uuid4()).type.value == "PURCHASE"

    def test_type_fallback_credit(self):
        service = self._get_service()
        dto = make_dto(type=None, direction="CREDIT")
        assert service._to_entity(dto, uuid4()).type.value == "OTHER"

    def test_installment_count_from_dto(self):
        service = self._get_service()
        dto = make_dto(installment_count=12, installment_current=3)
        entity = service._to_entity(dto, uuid4())
        assert entity.installment_count == 12
        assert entity.installment_current == 3

    def test_installment_clamping(self):
        """Se current > count, deve ser clamped ao count."""
        service = self._get_service()
        dto = make_dto(installment_count=3, installment_current=5)
        entity = service._to_entity(dto, uuid4())
        assert entity.installment_current == 3

    def test_hash_differs_on_different_ids(self):
        service = self._get_service()
        dto1 = make_dto(id="tx_aaa")
        dto2 = make_dto(id="tx_bbb")
        assert service._compute_hash("tx_aaa", "PIERRE", date(2024, 1, 1), Decimal("100")) != service._compute_hash("tx_bbb", "PIERRE", date(2024, 1, 1), Decimal("100"))

    def test_purchase_id_generated_for_installments(self):
        """Transações parceladas sem purchaseId devem ter um UUID gerado."""
        service = self._get_service()
        dto = make_dto(installment_count=3, installment_current=1)
        entity = service._to_entity(dto, uuid4())
        assert entity.purchase_id is not None

    def test_no_purchase_id_for_single_purchase(self):
        """Transações simples sem parcelamento não devem ter purchase_id."""
        service = self._get_service()
        dto = make_dto(installment_count=None, installment_current=None)
        entity = service._to_entity(dto, uuid4())
        assert entity.purchase_id is None


# ================================================================= #
#  import_transactions integration tests (mocked)
# ================================================================= #

@pytest.mark.asyncio
async def test_import_transactions_success():
    """Importação bem-sucedida deve retornar status 'success'."""
    mock_provider = MagicMock()
    mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
    mock_provider.__aexit__ = AsyncMock(return_value=False)
    mock_provider.get_transactions = AsyncMock(return_value=[make_dto()])
    mock_provider.get_accounts = AsyncMock(return_value=[])

    mock_tx_repo = AsyncMock()
    mock_tx_repo.bulk_upsert = AsyncMock(return_value={"inserted": 1, "skipped": 0})
    
    mock_acc_repo = AsyncMock()

    service = PierreImportService(pierre_provider=mock_provider, transaction_repo=mock_tx_repo, account_repo=mock_acc_repo)
    result = await service.import_transactions(
        user_id=uuid4(),
        start_date=date(2024, 3, 1),
        end_date=date(2024, 3, 5),
    )
    assert result.status == "success"
    assert result.imported == 1
    assert result.skipped == 0


@pytest.mark.asyncio
async def test_import_transactions_handles_client_error():
    """Erro no PierreClient deve retornar status 'failed'."""
    mock_provider = MagicMock()
    mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
    mock_provider.__aexit__ = AsyncMock(return_value=False)
    mock_provider.get_accounts = AsyncMock(side_effect=Exception("Connection failed"))

    mock_tx_repo = AsyncMock()
    mock_acc_repo = AsyncMock()
    service = PierreImportService(pierre_provider=mock_provider, transaction_repo=mock_tx_repo, account_repo=mock_acc_repo)

    result = await service.import_transactions(
        user_id=uuid4(),
        start_date=date(2024, 3, 1),
        end_date=date(2024, 3, 5),
    )
    assert result.status == "failed"
    assert "Connection failed" in (result.error_message or "")


@pytest.mark.asyncio
async def test_import_transactions_skips_on_duplicate():
    """Transações duplicadas (repo retorna skipped) devem ser contabilizadas."""
    mock_provider = MagicMock()
    mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
    mock_provider.__aexit__ = AsyncMock(return_value=False)
    mock_provider.get_transactions = AsyncMock(return_value=[make_dto(), make_dto(id="tx_002")])
    mock_provider.get_accounts = AsyncMock(return_value=[])

    mock_tx_repo = AsyncMock()
    mock_tx_repo.bulk_upsert = AsyncMock(return_value={"inserted": 0, "skipped": 2})
    mock_acc_repo = AsyncMock()

    service = PierreImportService(pierre_provider=mock_provider, transaction_repo=mock_tx_repo, account_repo=mock_acc_repo)
    result = await service.import_transactions(user_id=uuid4())
    assert result.skipped == 2
    assert result.imported == 0

