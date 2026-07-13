"""
PositionRepository — Repositório de Persistência de Custódia B3.

Responsabilidade:
    - Persistir PositionSnapshots em lote (save_many).
    - Implementar UPSERT idempotente usando snapshot_hash como chave.
    - Garantir transação única com rollback em caso de falha.
    - NÃO conhece Reader, Parser, Normalizer ou Pipeline.

Limitações Intencionais (Sprint 2):
    - Não implementa valuation.
    - Não cruza dados com imports/.
    - Não acessa APIs externas.
"""
import uuid
import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import List, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from backend.domains.investments.dto import PositionSnapshot

logger = logging.getLogger(__name__)


class PositionRepositoryException(Exception):
    pass


class PositionRepository:
    """
    Repositório de PositionSnapshot desacoplado do Pipeline.
    Recebe uma SQLAlchemy connection string ou engine — não importa o Pipeline.
    """

    def __init__(self, db_url: str):
        self._engine = create_engine(db_url, connect_args={"check_same_thread": False})

    @contextmanager
    def _transaction(self) -> Generator[Connection, None, None]:
        """Context manager que garante commit/rollback atômico."""
        with self._engine.begin() as conn:
            try:
                yield conn
            except Exception:
                # SQLAlchemy 2.0: engine.begin() faz rollback automático em exceção
                raise

    def save_many(self, snapshots: List[PositionSnapshot]) -> int:
        """
        Persiste uma lista de PositionSnapshots em transação única.
        Usa INSERT OR REPLACE para idempotência via snapshot_hash.

        Returns:
            Número de registros inseridos/atualizados.
        """
        if not snapshots:
            return 0

        upsert_sql = text("""
            INSERT INTO position_snapshots (
                id, snapshot_hash, reference_date, ticker, asset_type,
                institution, source_system, quantity, unit_price,
                total_value, metadata_json, created_at, updated_at
            ) VALUES (
                :id, :snapshot_hash, :reference_date, :ticker, :asset_type,
                :institution, :source_system, :quantity, :unit_price,
                :total_value, :metadata_json, :created_at, :updated_at
            )
            ON CONFLICT(snapshot_hash) DO UPDATE SET
                quantity       = excluded.quantity,
                unit_price     = excluded.unit_price,
                total_value    = excluded.total_value,
                metadata_json  = excluded.metadata_json,
                updated_at     = excluded.updated_at
        """)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

        rows = []
        for snap in snapshots:
            rows.append({
                "id": str(uuid.uuid4()),
                "snapshot_hash": snap.snapshot_hash,
                "reference_date": snap.reference_date.isoformat(),
                "ticker": snap.ticker,
                "asset_type": snap.asset_type.value,
                "institution": snap.institution,
                "source_system": snap.source_system,
                "quantity": str(snap.quantity),
                "unit_price": str(snap.unit_price) if snap.unit_price is not None else None,
                "total_value": str(snap.total_value) if snap.total_value is not None else None,
                "metadata_json": json.dumps(snap.metadata, ensure_ascii=False, default=str),
                "created_at": now,
                "updated_at": now,
            })

        try:
            with self._transaction() as conn:
                conn.execute(upsert_sql, rows)
            logger.info(f"[PositionRepository] {len(rows)} snapshots persistidos com sucesso.")
            return len(rows)
        except Exception as e:
            logger.error(f"[PositionRepository] Falha na persistência: {e}")
            raise PositionRepositoryException(f"Erro ao persistir snapshots: {e}") from e

    def count_by_date(self, reference_date: str) -> int:
        """Retorna a contagem de snapshots para uma data de referência."""
        with self._engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM position_snapshots WHERE reference_date = :d"),
                {"d": reference_date}
            )
            return result.scalar_one()

    def find_by_hash(self, snapshot_hash: str) -> dict | None:
        """Busca um snapshot pelo seu hash de idempotência."""
        with self._engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM position_snapshots WHERE snapshot_hash = :h"),
                {"h": snapshot_hash}
            )
            row = result.mappings().first()
            return dict(row) if row else None
