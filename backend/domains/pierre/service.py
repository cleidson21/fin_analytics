"""
service.py — Domínio Pierre

PierreSyncService: orquestrador do pipeline de sincronização.

Responsabilidades:
  - Determinar o modo de operação (PROD | DEV | REPLAY)
  - Buscar dados da API Pierre (modos PROD e DEV)
  - Carregar arquivo local (modo REPLAY)
  - Coordenar: download → validação → pipeline.process_payload → repositories
  - Registrar governança: sync_state e sync_history

Modos de Operação:
  PROD   → chama API Pierre, JSON em memória, não salva em disco
  DEV    → chama API Pierre, salva JSON bruto em exports/pierre/raw/<timestamp>.json
  REPLAY → carrega arquivo JSON salvo, não chama a API

Regras:
  - Nenhuma regra financeira
  - Nenhum cálculo ou enriquecimento
  - Persiste exatamente o que recebe da Pierre
  - Interface pública: sync() retorna SyncResultResponse
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.pierre.pipeline import process_payload
from backend.domains.pierre.repository import (
    AccountRepository,
    CategoryRepository,
    SyncRepository,
    TransactionRepository,
)
from backend.domains.pierre.schemas import (
    PierreApiResponse,
    PierreTransactionRaw,
    SyncResultResponse,
    SyncStatusResponse,
)

PROVIDER = "pierre"
PIERRE_API_URL = "https://www.pierre.finance/tools/api/get-transactions"
EXPORTS_DIR = Path("exports/pierre/raw")


class SyncMode(str, Enum):
    PROD = "PROD"
    DEV = "DEV"
    REPLAY = "REPLAY"


class PierreApiError(Exception):
    """Erro retornado pela API Pierre."""


class PierreSyncService:
    """
    Orquestra o pipeline completo de sincronização da Pierre.

    Uso:
        service = PierreSyncService(session=session, api_key="sk-...")
        result = await service.sync(mode=SyncMode.PROD, start_date="2025-01-01", end_date="2025-12-31")
    """

    def __init__(
        self,
        session: AsyncSession,
        api_key: str,
        environment: str = "production",
    ) -> None:
        self._session = session
        self._api_key = api_key
        self._environment = environment

        self._account_repo = AccountRepository(session)
        self._transaction_repo = TransactionRepository(session)
        self._category_repo = CategoryRepository(session)
        self._sync_repo = SyncRepository(session)

    # ─────────────────────────────────────────────────────────────────────────
    # Interface pública
    # ─────────────────────────────────────────────────────────────────────────

    async def sync(
        self,
        mode: SyncMode = SyncMode.PROD,
        start_date: str = "2024-01-01",
        end_date: Optional[str] = None,
        replay_file: Optional[str] = None,
    ) -> SyncResultResponse:
        """
        Executa o pipeline completo de sincronização Pierre.

        Args:
            mode: PROD | DEV | REPLAY
            start_date: data de início (YYYY-MM-DD), usado em PROD/DEV
            end_date: data de fim (YYYY-MM-DD), padrão = hoje
            replay_file: caminho do arquivo JSON para modo REPLAY

        Returns:
            SyncResultResponse com os contadores e status da execução
        """
        started_at = datetime.now(timezone.utc)

        if end_date is None:
            end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Registra tentativa no sync_state
        await self._sync_repo.upsert_state(
            provider=PROVIDER,
            last_attempt=started_at,
        )
        await self._session.commit()

        try:
            # ── 1. Download / Carregamento ────────────────────────────────
            raw_transactions, actual_file = await self._load_data(
                mode=mode,
                start_date=start_date,
                end_date=end_date,
                replay_file=replay_file,
            )

            received = len(raw_transactions)

            if received == 0:
                return await self._finalize(
                    started_at=started_at,
                    received=0, inserted=0, updated=0, ignored=0,
                    status="SUCCESS",
                    mode=mode,
                    replay_file=actual_file,
                    last_period=f"{start_date}/{end_date}",
                )

            # ── 2. Mapeamento (pipeline.py) ───────────────────────────────
            sync_at = started_at
            accounts_data, transactions_data, category_names = process_payload(
                raw_transactions, sync_at
            )

            # ── 3. Accounts UPSERT ────────────────────────────────────────
            acc_counts = await self._account_repo.upsert_many(accounts_data)

            # ── 4. Transactions UPSERT ────────────────────────────────────
            txn_counts = await self._transaction_repo.upsert_many(transactions_data)

            # ── 5. Categories INSERT OR IGNORE ────────────────────────────
            await self._category_repo.insert_ignore_many(PROVIDER, category_names)

            # ── 6. Commit ─────────────────────────────────────────────────
            await self._session.commit()

            # ── 7. Governança ─────────────────────────────────────────────
            return await self._finalize(
                started_at=started_at,
                received=received,
                inserted=txn_counts["inserted"],
                updated=txn_counts["updated"],
                ignored=txn_counts.get("ignored", 0),
                status="SUCCESS",
                mode=mode,
                replay_file=actual_file,
                last_period=f"{start_date}/{end_date}",
            )

        except Exception as exc:
            await self._session.rollback()
            return await self._finalize(
                started_at=started_at,
                received=0, inserted=0, updated=0, ignored=0,
                status="FAILED",
                mode=mode,
                replay_file=replay_file,
                error=str(exc),
            )

    async def get_status(self) -> Optional[SyncStatusResponse]:
        """Retorna o estado atual do sync_state para a Pierre."""
        state = await self._sync_repo.get_state(PROVIDER)
        if state is None:
            return None
        return SyncStatusResponse(
            provider=state.provider,
            last_success_sync=state.last_success_sync,
            last_attempt=state.last_attempt,
            last_cursor=state.last_cursor,
            last_period=state.last_period,
            api_version=state.api_version,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Privado
    # ─────────────────────────────────────────────────────────────────────────

    async def _load_data(
        self,
        mode: SyncMode,
        start_date: str,
        end_date: str,
        replay_file: Optional[str],
    ) -> tuple[list[PierreTransactionRaw], Optional[str]]:
        """
        Carrega os dados brutos da Pierre conforme o modo.
        Retorna (lista de PierreTransactionRaw validados, arquivo salvo ou None).
        """
        if mode == SyncMode.REPLAY:
            if not replay_file:
                raise ValueError("replay_file é obrigatório no modo REPLAY")
            return self._load_from_file(replay_file), replay_file

        # PROD ou DEV: chama a API
        raw_json = await self._fetch_from_api(start_date, end_date)

        saved_file = None
        if mode == SyncMode.DEV:
            saved_file = self._save_raw_json(raw_json)

        return self._parse_json(raw_json), saved_file

    async def _fetch_from_api(self, start_date: str, end_date: str) -> dict:
        """Chama GET /tools/api/get-transactions e retorna o JSON bruto."""
        headers = {"Authorization": f"Bearer {self._api_key}"}
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "format": "raw",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(PIERRE_API_URL, headers=headers, params=params)

        if response.status_code != 200:
            raise PierreApiError(
                f"Pierre API retornou status {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        if not data.get("success"):
            raise PierreApiError(f"Pierre API retornou success=false: {data}")

        return data

    def _parse_json(self, raw_json: dict) -> list[PierreTransactionRaw]:
        """Valida e converte o JSON bruto em lista de PierreTransactionRaw."""
        response = PierreApiResponse.model_validate(raw_json)
        return response.data

    def _load_from_file(self, file_path: str) -> list[PierreTransactionRaw]:
        """Carrega e valida um arquivo JSON salvo anteriormente."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de replay não encontrado: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_json = json.load(f)

        return self._parse_json(raw_json)

    def _save_raw_json(self, raw_json: dict) -> str:
        """
        Salva o JSON bruto em exports/pierre/raw/<timestamp>.json.
        Retorna o caminho do arquivo salvo.
        """
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_path = EXPORTS_DIR / f"{timestamp}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(raw_json, f, ensure_ascii=False, default=str, indent=2)

        return str(file_path)

    async def _finalize(
        self,
        started_at: datetime,
        received: int,
        inserted: int,
        updated: int,
        ignored: int,
        status: str,
        mode: SyncMode,
        replay_file: Optional[str] = None,
        error: Optional[str] = None,
        last_period: Optional[str] = None,
    ) -> SyncResultResponse:
        """
        Registra governança (sync_state + sync_history) e retorna resultado.
        """
        finished_at = datetime.now(timezone.utc)

        # Atualiza sync_state
        state_fields = {
            "last_attempt": started_at,
            "last_period": last_period,
        }
        if status == "SUCCESS":
            state_fields["last_success_sync"] = finished_at

        await self._sync_repo.upsert_state(provider=PROVIDER, **state_fields)

        # Grava sync_history
        await self._sync_repo.insert_history(
            provider=PROVIDER,
            started_at=started_at,
            finished_at=finished_at,
            received=received,
            inserted=inserted,
            updated=updated,
            ignored=ignored,
            status=status,
            error=error,
        )

        await self._session.commit()

        return SyncResultResponse(
            provider=PROVIDER,
            status=status,
            received=received,
            inserted=inserted,
            updated=updated,
            ignored=ignored,
            started_at=started_at,
            finished_at=finished_at,
            error=error,
            mode=mode.value,
            replay_file=replay_file,
        )
