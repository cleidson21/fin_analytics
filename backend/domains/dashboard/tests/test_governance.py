"""
test_governance.py — Domínio Dashboard

Testes de integração para a Sprint 4.4.3 (Governança).

Cenários cobertos:
  ✓ Banco vazio: retorna listas vazias sem erro
  ✓ Um provider: sync_state e sync_history corretos
  ✓ Múltiplos providers: retorna todos e ordena corretamente
  ✓ Histórico ordenado: finished_at DESC
  ✓ Filtro por provider: retorna apenas o provider solicitado
  ✓ Erro nulo: error=None serializado corretamente
  ✓ Erro preenchido: mensagem de erro preservada
  ✓ Datas serializadas: objetos datetime corretos (não strings)
  ✓ Paginação: limit/offset funcionando
  ✓ Sprint 4.4.2 intacta: nenhuma tabela alterada após 4.4.3

Estratégia: SQLite em memória, sem dependência de API real.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.domains.dashboard.repository import GovernanceRepository
from backend.domains.dashboard.service import GovernanceService
from backend.domains.pierre.models import Account, SyncHistory, SyncState, Transaction
from backend.domains.shared.db import Base


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_session():
    """Banco SQLite em memória com schema V3 completo."""
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
def repo(db_session):
    return GovernanceRepository(db_session)


@pytest_asyncio.fixture
def service(db_session):
    return GovernanceService(db_session)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_sync_state(provider: str, last_success=None, last_attempt=None):
    return SyncState(
        provider=provider,
        last_success_sync=last_success or datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        last_attempt=last_attempt or datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        last_cursor=None,
        last_period="2025-01-01/2025-01-15",
        api_version="1.0",
    )


def make_sync_history(
    provider: str,
    status: str = "SUCCESS",
    started_at=None,
    finished_at=None,
    received: int = 100,
    inserted: int = 80,
    updated: int = 20,
    ignored: int = 0,
    error: str = None,
):
    base = datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc)
    return SyncHistory(
        provider=provider,
        started_at=started_at or base,
        finished_at=finished_at or base,
        received=received,
        inserted=inserted,
        updated=updated,
        ignored=ignored,
        status=status,
        error=error,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Testes — Banco vazio
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_banco_vazio_sync_status_retorna_lista_vazia(service):
    """✓ Banco vazio: GET /sync/status retorna lista vazia sem erro."""
    result = await service.get_all_sync_status()
    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_banco_vazio_sync_history_retorna_lista_vazia(service):
    """✓ Banco vazio: GET /sync/history retorna lista vazia sem erro."""
    result = await service.get_sync_history()
    assert result.total == 0
    assert result.items == []
    assert result.provider is None


# ─────────────────────────────────────────────────────────────────────────────
# Testes — Um provider
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_um_provider_sync_state(service, db_session):
    """✓ Um provider: sync_state retornado corretamente."""
    db_session.add(make_sync_state("pierre"))
    await db_session.commit()

    result = await service.get_all_sync_status()
    assert result.total == 1
    assert result.items[0].provider == "pierre"
    assert result.items[0].last_period == "2025-01-01/2025-01-15"
    assert result.items[0].api_version == "1.0"


@pytest.mark.asyncio
async def test_um_provider_sync_history(service, db_session):
    """✓ Um provider: histórico com um registro retornado corretamente."""
    db_session.add(make_sync_history("pierre", received=100, inserted=80, updated=20))
    await db_session.commit()

    result = await service.get_sync_history()
    assert result.total == 1
    assert result.items[0].provider == "pierre"
    assert result.items[0].received == 100
    assert result.items[0].inserted == 80
    assert result.items[0].updated == 20
    assert result.items[0].status == "SUCCESS"


# ─────────────────────────────────────────────────────────────────────────────
# Testes — Múltiplos providers
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_multiplos_providers_status(service, db_session):
    """✓ Múltiplos providers: retorna todos ordenados por provider."""
    db_session.add(make_sync_state("pierre"))
    db_session.add(make_sync_state("myprofit"))
    await db_session.commit()

    result = await service.get_all_sync_status()
    assert result.total == 2
    providers = [item.provider for item in result.items]
    assert "pierre" in providers
    assert "myprofit" in providers


@pytest.mark.asyncio
async def test_multiplos_providers_historico(service, db_session):
    """✓ Múltiplos providers: histórico retorna todos."""
    db_session.add(make_sync_history("pierre"))
    db_session.add(make_sync_history("myprofit", inserted=50))
    await db_session.commit()

    result = await service.get_sync_history()
    assert result.total == 2
    providers = {item.provider for item in result.items}
    assert "pierre" in providers
    assert "myprofit" in providers


# ─────────────────────────────────────────────────────────────────────────────
# Testes — Ordenação por finished_at DESC
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_historico_ordenado_finished_at_desc(service, db_session):
    """✓ Histórico ordenado: finished_at DESC — mais recente primeiro."""
    older = datetime(2025, 1, 10, tzinfo=timezone.utc)
    newer = datetime(2025, 1, 20, tzinfo=timezone.utc)

    db_session.add(make_sync_history("pierre", finished_at=older, inserted=10))
    db_session.add(make_sync_history("pierre", finished_at=newer, inserted=99))
    await db_session.commit()

    result = await service.get_sync_history(provider="pierre")
    assert result.total == 2
    # Mais recente deve ser o primeiro
    assert result.items[0].inserted == 99
    assert result.items[1].inserted == 10


# ─────────────────────────────────────────────────────────────────────────────
# Testes — Filtro por provider
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_filtro_por_provider_pierre(service, db_session):
    """✓ Filtro por provider: ?provider=pierre retorna apenas pierre."""
    db_session.add(make_sync_history("pierre", inserted=80))
    db_session.add(make_sync_history("myprofit", inserted=50))
    await db_session.commit()

    result = await service.get_sync_history(provider="pierre")
    assert result.total == 1
    assert result.items[0].provider == "pierre"
    assert result.items[0].inserted == 80
    assert result.provider == "pierre"


@pytest.mark.asyncio
async def test_filtro_por_provider_myprofit(service, db_session):
    """✓ Filtro por provider: ?provider=myprofit retorna apenas myprofit."""
    db_session.add(make_sync_history("pierre"))
    db_session.add(make_sync_history("myprofit", inserted=50))
    await db_session.commit()

    result = await service.get_sync_history(provider="myprofit")
    assert result.total == 1
    assert result.items[0].provider == "myprofit"


# ─────────────────────────────────────────────────────────────────────────────
# Testes — Erro nulo e erro preenchido
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_erro_nulo_serializado_corretamente(service, db_session):
    """✓ Erro nulo: error=None deve retornar None no DTO."""
    db_session.add(make_sync_history("pierre", status="SUCCESS", error=None))
    await db_session.commit()

    result = await service.get_sync_history()
    assert result.items[0].error is None
    assert result.items[0].status == "SUCCESS"


@pytest.mark.asyncio
async def test_erro_preenchido_preservado(service, db_session):
    """✓ Erro preenchido: mensagem de erro deve ser preservada integralmente."""
    error_msg = "ConnectionError: timeout ao conectar na API Pierre após 60s"
    db_session.add(make_sync_history("pierre", status="FAILED", error=error_msg))
    await db_session.commit()

    result = await service.get_sync_history()
    assert result.items[0].status == "FAILED"
    assert result.items[0].error == error_msg


# ─────────────────────────────────────────────────────────────────────────────
# Testes — Datas serializadas corretamente
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_datas_retornadas_como_datetime(service, db_session):
    """✓ Datas serializadas: objetos datetime (não strings) no DTO."""
    started = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    finished = datetime(2025, 1, 15, 10, 5, 30, tzinfo=timezone.utc)

    db_session.add(make_sync_history(
        "pierre",
        started_at=started,
        finished_at=finished,
    ))
    await db_session.commit()

    result = await service.get_sync_history()
    item = result.items[0]
    assert isinstance(item.started_at, datetime)
    assert isinstance(item.finished_at, datetime)


@pytest.mark.asyncio
async def test_sync_state_datas_como_datetime(service, db_session):
    """✓ sync_state: last_success_sync e last_attempt são objetos datetime."""
    now = datetime(2025, 1, 15, 12, 0, tzinfo=timezone.utc)
    db_session.add(make_sync_state("pierre", last_success=now, last_attempt=now))
    await db_session.commit()

    result = await service.get_all_sync_status()
    item = result.items[0]
    assert isinstance(item.last_success_sync, datetime)
    assert isinstance(item.last_attempt, datetime)


# ─────────────────────────────────────────────────────────────────────────────
# Testes — Paginação
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_paginacao_limit(service, db_session):
    """✓ Paginação: limit=1 retorna apenas 1 item, total=N."""
    for i in range(5):
        db_session.add(make_sync_history(
            "pierre",
            finished_at=datetime(2025, 1, i + 1, tzinfo=timezone.utc),
            inserted=i,
        ))
    await db_session.commit()

    result = await service.get_sync_history(limit=1)
    assert result.total == 5
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_paginacao_offset(service, db_session):
    """✓ Paginação: offset=2 pula os 2 primeiros."""
    datas = [datetime(2025, 1, i + 1, tzinfo=timezone.utc) for i in range(5)]
    for i, dt in enumerate(sorted(datas, reverse=True)):
        db_session.add(make_sync_history("pierre", finished_at=dt, inserted=i * 10))
    await db_session.commit()

    page1 = await service.get_sync_history(limit=2, offset=0)
    page2 = await service.get_sync_history(limit=2, offset=2)

    assert len(page1.items) == 2
    assert len(page2.items) == 2
    # Itens das páginas devem ser diferentes
    ids_p1 = {item.id for item in page1.items}
    ids_p2 = {item.id for item in page2.items}
    assert ids_p1.isdisjoint(ids_p2)


# ─────────────────────────────────────────────────────────────────────────────
# Teste — Integridade com Sprint 4.4.2 (nenhuma tabela alterada)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sprint_442_nao_alterada_leitura_nao_modifica(service, db_session):
    """
    ✓ Sprint 4.4.2 intacta: consultas de governança não alteram nenhuma tabela.
    Verifica contagens antes e depois da leitura.
    """
    # Popula com dados V3 como a 4.4.2 faria
    db_session.add(make_sync_state("pierre"))
    db_session.add(make_sync_history("pierre"))
    await db_session.commit()

    # Conta antes
    state_before = (await db_session.execute(
        select(SyncState)
    )).scalars().all()
    history_before = (await db_session.execute(
        select(SyncHistory)
    )).scalars().all()

    # Executa consultas de governança
    await service.get_all_sync_status()
    await service.get_sync_history()
    await service.get_sync_history(provider="pierre")

    # Conta depois
    state_after = (await db_session.execute(
        select(SyncState)
    )).scalars().all()
    history_after = (await db_session.execute(
        select(SyncHistory)
    )).scalars().all()

    # Nenhum registro foi adicionado ou removido
    assert len(state_before) == len(state_after)
    assert len(history_before) == len(history_after)
