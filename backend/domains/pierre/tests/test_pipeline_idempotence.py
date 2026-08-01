"""
test_pipeline_idempotence.py — Domínio Pierre

Testes de integração para a Sprint 4.4.2.

Cenários obrigatórios (Definition of Done 4.4.2):
  ✓ Primeira sincronização → N registros inseridos
  ✓ Segunda sincronização (mesmos dados) → 0 novas inserções, zero duplicações
  ✓ Replay via arquivo JSON → resultado idêntico, sem chamada à API
  ✓ Banco vazio → sem erros, operação completa
  ✓ Banco já populado → upsert atualiza, não duplica
  ✓ Interrupção durante sincronização → sync_history registra FAILED

Estratégia: banco SQLite em memória (:memory:), sem dependência de API real.
O pipeline é testado com payload JSON fixo que simula a resposta da Pierre.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.domains.pierre.models import (
    Account,
    Category,
    SyncHistory,
    SyncState,
    Transaction,
)
from backend.domains.pierre.service import PierreSyncService, SyncMode
from backend.domains.shared.db import Base

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

PIERRE_SAMPLE_PAYLOAD = {
    "success": True,
    "data": [
        {
            "id": "txn-001",
            "account_id": "acc-001",
            "description": "Mercado Extra",
            "original_description": "MERCADO EXTRA",
            "category": "Alimentação",
            "original_category": "FOOD",
            "currency_code": "BRL",
            "amount": 150.50,
            "date": "2025-01-15T10:00:00",
            "type": "DEBIT",
            "status": "POSTED",
            "manual_transaction": False,
            "account_name": "Nubank",
            "account_type": "BANK",
            "account_subtype": "CHECKING_ACCOUNT",
            "connector_name": "Nubank",
            "item_bank_name": "Nu Pagamentos S.A.",
            "account_credit_data": None,
            "credit_card_data": None,
            "payment_data": None,
            "merchant": {"name": "Mercado Extra"},
            "bill_id": None,
        },
        {
            "id": "txn-002",
            "account_id": "acc-002",
            "description": "Amazon Prime",
            "original_description": "AMAZON PRIME",
            "category": "Assinaturas",
            "original_category": "SUBSCRIPTION",
            "currency_code": "BRL",
            "amount": 19.90,
            "date": "2025-01-16T14:30:00",
            "type": "DEBIT",
            "status": "POSTED",
            "manual_transaction": False,
            "account_name": "Nubank Cartão",
            "account_type": "CREDIT",
            "account_subtype": "CREDIT_CARD",
            "connector_name": "Nubank",
            "item_bank_name": "Nu Pagamentos S.A.",
            "account_credit_data": {"limit": 5000.0, "availableLimit": 4980.1},
            "credit_card_data": {
                "purchaseDate": "2025-01-16T14:30:00",
                "installmentNumber": 1,
                "totalInstallments": 1,
                "totalAmount": 19.90,
                "billId": "bill-jan-2025",
                "isFullInstallmentTransaction": True,
                "isIndividualInstallment": False,
            },
            "payment_data": None,
            "merchant": {"name": "Amazon"},
            "bill_id": "bill-jan-2025",
        },
    ],
}


@pytest_asyncio.fixture
async def db_session():
    """Cria banco SQLite em memória para cada teste."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionFactory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    async with SessionFactory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
def service(db_session):
    """Cria PierreSyncService com session em memória e api_key fake."""
    return PierreSyncService(
        session=db_session,
        api_key="sk-fake-test-key",
        environment="test",
    )


@pytest_asyncio.fixture
def sample_payload_file(tmp_path):
    """Cria arquivo JSON temporário para testes de REPLAY."""
    file_path = tmp_path / "pierre_test.json"
    with open(file_path, "w") as f:
        json.dump(PIERRE_SAMPLE_PAYLOAD, f)
    return str(file_path)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: executa sync via REPLAY com payload fixo
# ─────────────────────────────────────────────────────────────────────────────

async def run_replay(service: PierreSyncService, file_path: str):
    return await service.sync(mode=SyncMode.REPLAY, replay_file=file_path)


# ─────────────────────────────────────────────────────────────────────────────
# Testes
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_banco_vazio_sem_erro(service, sample_payload_file):
    """✓ Banco vazio: operação completa sem erros."""
    result = await run_replay(service, sample_payload_file)

    assert result.status == "SUCCESS"
    assert result.received == 2
    assert result.inserted == 2
    assert result.updated == 0
    assert result.error is None


@pytest.mark.asyncio
async def test_primeira_sync_insere_registros(service, sample_payload_file, db_session):
    """✓ Primeira sincronização → N registros inseridos nas tabelas corretas."""
    result = await run_replay(service, sample_payload_file)

    # Verifica accounts
    acc_count = await db_session.scalar(select(func.count(Account.external_id)))
    assert acc_count == 2  # acc-001 e acc-002

    # Verifica transactions
    txn_count = await db_session.scalar(select(func.count(Transaction.external_id)))
    assert txn_count == 2  # txn-001 e txn-002

    # Verifica categories
    cat_count = await db_session.scalar(select(func.count(Category.name)))
    assert cat_count == 2  # Alimentação e Assinaturas

    assert result.inserted == 2
    assert result.status == "SUCCESS"


@pytest.mark.asyncio
async def test_segunda_sync_zero_duplicacoes(service, sample_payload_file, db_session):
    """✓ Segunda sincronização com mesmo JSON → zero duplicações."""
    # Primeira execução
    result1 = await run_replay(service, sample_payload_file)
    assert result1.inserted == 2

    # Segunda execução (mesmo arquivo)
    result2 = await run_replay(service, sample_payload_file)
    assert result2.status == "SUCCESS"
    assert result2.inserted == 0    # Nenhum novo inserido
    assert result2.updated == 2     # Os existentes foram atualizados

    # Contagem total deve ser idêntica
    txn_count = await db_session.scalar(select(func.count(Transaction.external_id)))
    assert txn_count == 2  # Não duplicou!

    acc_count = await db_session.scalar(select(func.count(Account.external_id)))
    assert acc_count == 2  # Não duplicou!


@pytest.mark.asyncio
async def test_replay_resultado_identico(service, sample_payload_file, db_session):
    """✓ Replay: resultado idêntico à execução original (idempotência)."""
    # Execução 1
    r1 = await run_replay(service, sample_payload_file)
    count1_txn = await db_session.scalar(select(func.count(Transaction.external_id)))
    count1_acc = await db_session.scalar(select(func.count(Account.external_id)))

    # Execução 2 (replay)
    r2 = await run_replay(service, sample_payload_file)
    count2_txn = await db_session.scalar(select(func.count(Transaction.external_id)))
    count2_acc = await db_session.scalar(select(func.count(Account.external_id)))

    # Contagens devem ser idênticas
    assert count1_txn == count2_txn
    assert count1_acc == count2_acc

    # Status SUCCESS em ambas
    assert r1.status == "SUCCESS"
    assert r2.status == "SUCCESS"

    # received igual em ambas (mesmo payload)
    assert r1.received == r2.received


@pytest.mark.asyncio
async def test_banco_populado_upsert_atualiza(service, sample_payload_file, db_session):
    """✓ Banco já populado: UPSERT atualiza sem duplicar."""
    # Popula
    await run_replay(service, sample_payload_file)

    # Modifica o payload (simula atualização de status na Pierre)
    modified_payload = json.loads(json.dumps(PIERRE_SAMPLE_PAYLOAD))
    modified_payload["data"][0]["status"] = "PENDING"  # txn-001 muda de POSTED para PENDING

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(modified_payload, f)
        modified_file = f.name

    try:
        result = await run_replay(service, modified_file)

        # Verifica que não duplicou
        txn_count = await db_session.scalar(select(func.count(Transaction.external_id)))
        assert txn_count == 2

        # Verifica que o status foi atualizado
        txn = await db_session.scalar(
            select(Transaction).where(
                Transaction.provider == "pierre",
                Transaction.external_id == "txn-001",
            )
        )
        assert txn is not None
        assert txn.status == "PENDING"

        assert result.updated == 2  # Ambas foram atualizadas (mesmo que só uma mudou)
    finally:
        os.unlink(modified_file)


@pytest.mark.asyncio
async def test_sync_state_atualizado(service, sample_payload_file, db_session):
    """✓ sync_state é atualizado corretamente após sincronização."""
    await run_replay(service, sample_payload_file)

    state = await db_session.scalar(
        select(SyncState).where(SyncState.provider == "pierre")
    )
    assert state is not None
    assert state.last_success_sync is not None
    assert state.last_attempt is not None
    assert state.provider == "pierre"


@pytest.mark.asyncio
async def test_sync_history_registrado(service, sample_payload_file, db_session):
    """✓ sync_history registra cada execução."""
    # Executa duas vezes
    await run_replay(service, sample_payload_file)
    await run_replay(service, sample_payload_file)

    # Deve haver 2 entradas em sync_history
    count = await db_session.scalar(select(func.count(SyncHistory.id)))
    assert count == 2  # Uma por execução

    # Verifica campos do último registro
    last = await db_session.scalar(
        select(SyncHistory).order_by(SyncHistory.id.desc()).limit(1)
    )
    assert last is not None
    assert last.provider == "pierre"
    assert last.status == "SUCCESS"
    assert last.started_at is not None
    assert last.finished_at is not None
    assert last.received == 2


@pytest.mark.asyncio
async def test_interrupção_registra_failed(service, db_session, monkeypatch):
    """✓ Interrupção durante sync → sync_history registra FAILED."""
    async def _raise_error(*args, **kwargs):
        raise RuntimeError("Simulação de falha de rede")

    monkeypatch.setattr(service, "_load_data", _raise_error)

    result = await service.sync(mode=SyncMode.REPLAY, replay_file="fake.json")

    assert result.status == "FAILED"
    assert result.error is not None
    assert "Simulação de falha" in result.error

    # sync_history deve registrar o FAILED
    history = await db_session.scalar(
        select(SyncHistory).where(SyncHistory.status == "FAILED")
    )
    assert history is not None
    assert history.provider == "pierre"


@pytest.mark.asyncio
async def test_replay_file_inexistente(service):
    """✓ Arquivo de replay inexistente lança erro claro."""
    result = await service.sync(
        mode=SyncMode.REPLAY,
        replay_file="/caminho/inexistente/arquivo.json",
    )
    assert result.status == "FAILED"
    assert result.error is not None


@pytest.mark.asyncio
async def test_mapeamento_campos_cartao(service, sample_payload_file, db_session):
    """✓ Campos de cartão de crédito mapeados corretamente."""
    await run_replay(service, sample_payload_file)

    txn = await db_session.scalar(
        select(Transaction).where(
            Transaction.provider == "pierre",
            Transaction.external_id == "txn-002",
        )
    )
    assert txn is not None
    assert txn.bill_id == "bill-jan-2025"
    assert txn.installment_number == 1
    assert txn.total_installments == 1
    assert txn.merchant_name == "Amazon"
    assert txn.category == "Assinaturas"
    assert txn.type == "DEBIT"
    assert txn.status == "POSTED"


@pytest.mark.asyncio
async def test_credit_metadata_json_salvo(service, sample_payload_file, db_session):
    """✓ account_credit_data serializado em credit_metadata_json na conta."""
    await run_replay(service, sample_payload_file)

    acc = await db_session.scalar(
        select(Account).where(
            Account.provider == "pierre",
            Account.external_id == "acc-002",
        )
    )
    assert acc is not None
    assert acc.credit_metadata_json is not None
    data = json.loads(acc.credit_metadata_json)
    assert data["limit"] == 5000.0
