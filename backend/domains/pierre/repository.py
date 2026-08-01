"""
repository.py — Domínio Pierre

Camada de acesso exclusivo ao banco para as 5 tabelas do domínio Pierre.
Implementa UPSERT idempotente via SQLite INSERT OR REPLACE / ON CONFLICT.

Responsabilidades:
  AccountRepository    → UPSERT em accounts
  TransactionRepository → UPSERT em transactions
  CategoryRepository   → INSERT OR IGNORE em categories
  SyncRepository       → UPDATE sync_state + INSERT sync_history

Regras:
  - Nenhum domínio importa este módulo diretamente — apenas pierre/service.py
  - Toda operação produtora de efeito é idempotente
  - Sem lógica de negócio — apenas SQL
  - Sem transformação de dados — recebe dados já mapeados
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.pierre.models import (
    Account,
    Category,
    SyncHistory,
    SyncState,
    Transaction,
)


# ─────────────────────────────────────────────────────────────────────────────
# AccountRepository
# ─────────────────────────────────────────────────────────────────────────────

class AccountRepository:
    """
    UPSERT idempotente de contas via PK composta (provider, external_id).

    Se a conta já existir: atualiza name, type, subtype, bank, connector,
    credit_metadata_json e last_sync.
    Se não existir: insere novo registro.

    Estratégia: INSERT OR REPLACE (SQLite) — atomicamente destrói e recria
    o registro. Como a PK é composta e não há FK de accounts → outras tabelas,
    não há risco de cascade delete.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_many(self, records: list[dict]) -> dict[str, int]:
        """
        Faz UPSERT de uma lista de dicts com os campos de accounts.
        Retorna contadores: {'inserted': N, 'updated': M}.
        """
        if not records:
            return {"inserted": 0, "updated": 0}

        inserted = updated = 0

        for rec in records:
            # Verifica se já existe
            existing = await self._session.execute(
                select(Account).where(
                    Account.provider == rec["provider"],
                    Account.external_id == rec["external_id"],
                )
            )
            existing_row = existing.scalar_one_or_none()

            stmt = sqlite_insert(Account).values(**rec)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["provider", "external_id"],
                set_={
                    "name": stmt.excluded.name,
                    "type": stmt.excluded.type,
                    "subtype": stmt.excluded.subtype,
                    "bank": stmt.excluded.bank,
                    "connector": stmt.excluded.connector,
                    "credit_metadata_json": stmt.excluded.credit_metadata_json,
                    "last_sync": stmt.excluded.last_sync,
                },
            )
            await self._session.execute(upsert_stmt)

            if existing_row:
                updated += 1
            else:
                inserted += 1

        return {"inserted": inserted, "updated": updated}


# ─────────────────────────────────────────────────────────────────────────────
# TransactionRepository
# ─────────────────────────────────────────────────────────────────────────────

class TransactionRepository:
    """
    UPSERT idempotente de transações via PK composta (provider, external_id).

    Se a transação já existir: atualiza todos os campos canônicos
    (exceto provider e external_id que são a PK).
    Se não existir: insere novo registro.

    A idempotência é garantida pelo ON CONFLICT na PK composta —
    executar 2x com o mesmo payload = resultado idêntico, zero duplicações.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_many(self, records: list[dict]) -> dict[str, int]:
        """
        Faz UPSERT de uma lista de dicts com os campos de transactions.
        Retorna contadores: {'inserted': N, 'updated': M, 'ignored': K}.
        """
        if not records:
            return {"inserted": 0, "updated": 0, "ignored": 0}

        inserted = updated = ignored = 0

        # Busca PKs já existentes de uma vez (eficiência)
        external_ids = [r["external_id"] for r in records]
        providers = list({r["provider"] for r in records})

        existing_result = await self._session.execute(
            select(Transaction.provider, Transaction.external_id).where(
                Transaction.provider.in_(providers),
                Transaction.external_id.in_(external_ids),
            )
        )
        existing_pks = {(row.provider, row.external_id) for row in existing_result}

        for rec in records:
            pk = (rec["provider"], rec["external_id"])

            stmt = sqlite_insert(Transaction).values(**rec)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["provider", "external_id"],
                set_={
                    "description": stmt.excluded.description,
                    "original_description": stmt.excluded.original_description,
                    "category": stmt.excluded.category,
                    "original_category": stmt.excluded.original_category,
                    "amount": stmt.excluded.amount,
                    "currency": stmt.excluded.currency,
                    "date": stmt.excluded.date,
                    "status": stmt.excluded.status,
                    "type": stmt.excluded.type,
                    "merchant_name": stmt.excluded.merchant_name,
                    "bill_id": stmt.excluded.bill_id,
                    "installment_number": stmt.excluded.installment_number,
                    "total_installments": stmt.excluded.total_installments,
                    "purchase_date": stmt.excluded.purchase_date,
                    "receiver_name": stmt.excluded.receiver_name,
                    "payer_name": stmt.excluded.payer_name,
                    "manual_transaction": stmt.excluded.manual_transaction,
                    "extra_json": stmt.excluded.extra_json,
                },
            )
            await self._session.execute(upsert_stmt)

            if pk in existing_pks:
                updated += 1
            else:
                inserted += 1

        return {"inserted": inserted, "updated": updated, "ignored": ignored}


# ─────────────────────────────────────────────────────────────────────────────
# CategoryRepository
# ─────────────────────────────────────────────────────────────────────────────

class CategoryRepository:
    """
    INSERT OR IGNORE de categorias (catálogo estatístico).

    Nunca sobrescreve registros existentes — se a categoria já existe,
    ignora silenciosamente. Isso preserva normalized_name customizado.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _normalize(name: str) -> str:
        """Normalização básica: lowercase, sem acentos comuns."""
        import unicodedata
        nfd = unicodedata.normalize("NFD", name.lower())
        return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

    async def insert_ignore_many(self, provider: str, names: list[str]) -> int:
        """
        Insere categorias novas, ignorando as já existentes.
        Retorna número de categorias efetivamente inseridas.
        """
        unique_names = list(set(names))
        if not unique_names:
            return 0

        inserted = 0
        for name in unique_names:
            stmt = sqlite_insert(Category).values(
                provider=provider,
                name=name,
                normalized_name=self._normalize(name),
            )
            ignore_stmt = stmt.on_conflict_do_nothing(
                index_elements=["provider", "name"]
            )
            result = await self._session.execute(ignore_stmt)
            if result.rowcount > 0:
                inserted += 1

        return inserted


# ─────────────────────────────────────────────────────────────────────────────
# SyncRepository
# ─────────────────────────────────────────────────────────────────────────────

class SyncRepository:
    """
    Governança de sincronização.

    - upsert_state: atualiza sync_state ao final de cada sync bem-sucedida
    - insert_history: grava sync_history com resultado de toda execução
    - get_state: lê o estado atual do sync_state
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_state(self, provider: str, **fields) -> None:
        """
        Atualiza ou cria o registro de sync_state para o provider.
        """
        stmt = sqlite_insert(SyncState).values(provider=provider, **fields)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["provider"],
            set_=fields,
        )
        await self._session.execute(upsert_stmt)

    async def insert_history(
        self,
        provider: str,
        started_at: datetime,
        finished_at: datetime,
        received: int,
        inserted: int,
        updated: int,
        ignored: int,
        status: str,
        error: Optional[str] = None,
    ) -> SyncHistory:
        """Grava uma entrada de auditoria em sync_history."""
        record = SyncHistory(
            provider=provider,
            started_at=started_at,
            finished_at=finished_at,
            received=received,
            inserted=inserted,
            updated=updated,
            ignored=ignored,
            status=status,
            error=error,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_state(self, provider: str) -> Optional[SyncState]:
        """Retorna o sync_state atual do provider."""
        result = await self._session.execute(
            select(SyncState).where(SyncState.provider == provider)
        )
        return result.scalar_one_or_none()
