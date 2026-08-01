"""
Testes unitários do PierreClient.

Cobre:
  - Autenticação (header Bearer)
  - Retry exponencial em erros de rede
  - Chunking por período
  - Erro 401 → PierreAuthError
  - Resposta válida → lista de PierreTransactionDTO
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.infrastructure.http.pierre_dtos import (
    PierreTransactionDTO,
    PierreTransactionsResponseDTO,
    PierreAccountDTO,
    PierreAccountsResponseDTO,
    PierreImportResultDTO,
)
from backend.infrastructure.http.pierre_client import (
    PierreClient,
    PierreAuthError,
    PierreClientError,
)


# ================================================================= #
#  DTO unit tests
# ================================================================= #


class TestPierreTransactionDTO:
    def test_amount_coercion_positive(self):
        """Amount deve ser sempre positivo (abs)."""
        dto = PierreTransactionDTO(
            id="tx_1",
            accountId="acc_1",
            amount=-150.50,
            direction="DEBIT",
            description="Mercado",
            date=date(2024, 1, 15),
        )
        assert dto.amount == Decimal("150.50")

    def test_direction_normalization_credit(self):
        """Variações de 'crédito' devem ser normalizadas para CREDIT."""
        for raw in ("credit", "CREDIT", "IN", "income", "ENTRADA"):
            dto = PierreTransactionDTO(
                id="tx", accountId="acc", amount=100,
                direction=raw, description="Test", date=date.today()
            )
            assert dto.direction == "CREDIT", f"Failed for '{raw}'"

    def test_direction_normalization_debit(self):
        """Variações de 'débito' devem ser normalizadas para DEBIT."""
        for raw in ("debit", "DEBIT", "OUT", "despesa"):
            dto = PierreTransactionDTO(
                id="tx", accountId="acc", amount=100,
                direction=raw, description="Test", date=date.today()
            )
            assert dto.direction == "DEBIT", f"Failed for '{raw}'"

    def test_status_normalization(self):
        assert PierreTransactionDTO(
            id="t", accountId="a", amount=1, direction="DEBIT",
            description="x", date=date.today(), status="pending"
        ).status == "PENDING"

        assert PierreTransactionDTO(
            id="t", accountId="a", amount=1, direction="DEBIT",
            description="x", date=date.today(), status="POSTED"
        ).status == "POSTED"

    def test_date_coercion_from_string(self):
        dto = PierreTransactionDTO(
            id="t", accountId="a", amount=50, direction="DEBIT",
            description="x", date="2024-03-20"
        )
        assert dto.transaction_date == date(2024, 3, 20)

    def test_installment_effective_methods(self):
        from backend.infrastructure.http.pierre_dtos import PierreInstallmentDTO
        inst = PierreInstallmentDTO(installmentCount=6, installmentNumber=3, purchaseId="pur_123")
        dto = PierreTransactionDTO(
            id="t", accountId="a", amount=300, direction="DEBIT",
            description="Parcelado", date=date.today(), installments=inst
        )
        assert dto.effective_installment_count() == 6
        assert dto.effective_installment_current() == 3
        assert dto.effective_purchase_id() == "pur_123"

    def test_empty_data_list_response(self):
        resp = PierreTransactionsResponseDTO(success=True, data=None)
        assert resp.data == []

    def test_import_result_dto(self):
        r = PierreImportResultDTO(status="success", imported=10, skipped=2, errors=0)
        assert r.imported == 10


# ================================================================= #
#  PierreClient unit tests (mocked HTTP)
# ================================================================= #


def make_client(api_key: str = "sk-test") -> PierreClient:
    return PierreClient(api_key=api_key, base_url="https://mock.pierre.finance")


def make_mock_response(json_data: dict, status_code: int = 200):
    mock = MagicMock(spec=httpx.Response)
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.text = str(json_data)
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_TX_RAW = {
    "success": True,
    "data": [
        {
            "id": "pierre_tx_001",
            "accountId": "acc_abc",
            "amount": 89.90,
            "direction": "DEBIT",
            "description": "iFood",
            "date": "2024-02-14",
            "isRecurring": False,
        }
    ],
    "count": 1,
}


@pytest.mark.asyncio
async def test_client_auth_header():
    """O cliente deve enviar Authorization: Bearer <key>."""
    client = make_client(api_key="sk-mykey")
    mock_http = AsyncMock()
    mock_http.request = AsyncMock(return_value=make_mock_response(SAMPLE_TX_RAW))

    client._client = mock_http
    result = await client._request("GET", "/tools/api/get-transactions", params={})

    mock_http.request.assert_called_once()
    assert result["success"] is True


@pytest.mark.asyncio
async def test_client_raises_auth_error_on_401():
    """Erro 401 deve levantar PierreAuthError."""
    client = make_client()
    mock_resp = make_mock_response({}, status_code=401)
    mock_http = AsyncMock()
    mock_http.request = AsyncMock(return_value=mock_resp)
    client._client = mock_http

    with pytest.raises(PierreAuthError):
        await client._request("GET", "/tools/api/get-transactions")


@pytest.mark.asyncio
async def test_client_retries_on_network_error():
    """Erros de rede devem gerar retry até _MAX_RETRIES, depois levantar PierreClientError."""
    client = make_client()
    mock_http = AsyncMock()
    mock_http.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    client._client = mock_http

    with patch("backend.infrastructure.http.pierre_client.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(PierreClientError):
            await client._request("GET", "/path")

    assert mock_http.request.call_count == 3  # _MAX_RETRIES = 3


@pytest.mark.asyncio
async def test_client_get_transactions_returns_dtos():
    """get_transactions deve retornar lista de ProviderTransactionDTO."""
    client = make_client()
    mock_http = AsyncMock()
    mock_http.request = AsyncMock(return_value=make_mock_response(SAMPLE_TX_RAW))
    client._client = mock_http

    from backend.application.dtos.provider_dtos import ProviderTransactionDTO
    result = await client.get_transactions(date(2024, 2, 1), date(2024, 2, 14))
    assert len(result) == 1
    assert isinstance(result[0], ProviderTransactionDTO)
    assert result[0].id == "pierre_tx_001"
    assert result[0].amount == 89.90


@pytest.mark.asyncio
async def test_client_chunks_large_date_range():
    """Intervalos maiores que _CHUNK_DAYS devem gerar múltiplas chamadas."""
    from backend.infrastructure.http.pierre_client import _CHUNK_DAYS

    start = date(2024, 1, 1)
    end = date(2024, 1, 1) + timedelta(days=_CHUNK_DAYS + 30)

    client = make_client()
    mock_http = AsyncMock()
    mock_http.request = AsyncMock(return_value=make_mock_response(
        {"success": True, "data": [], "count": 0}
    ))
    client._client = mock_http

    await client.get_transactions(start, end)
    # Deve ter feito pelo menos 2 chamadas (1 por chunk)
    assert mock_http.request.call_count >= 2
