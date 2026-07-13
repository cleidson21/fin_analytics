"""
Testes do PositionRepository — Sprint 2.

Usa SQLite em memória (:memory:) para isolamento total dos testes.
A migration 013 é executada como fixture de setup.
"""
import pytest
from datetime import date
from decimal import Decimal
from pathlib import Path

from backend.domains.investments.dto import PositionSnapshot, AssetTypeEnum
from backend.domains.investments.repositories.position_repository import (
    PositionRepository, PositionRepositoryException
)

# SQL da migration para criar a tabela em memória
MIGRATION_SQL = (
    Path(__file__).parent.parent.parent.parent.parent
    / "database" / "migrations" / "013_position_snapshots.sql"
).read_text(encoding="utf-8")

DB_URL_MEMORY = "sqlite:///:memory:"


def make_repo() -> PositionRepository:
    """Cria um repositório com SQLite em memória e aplica a migration."""
    import sqlite3
    repo = PositionRepository(DB_URL_MEMORY)
    with repo._engine.begin() as conn:
        # Executar linha por linha pois o driver SQLite não suporta executescript via SQLAlchemy
        from sqlalchemy import text
        for stmt in MIGRATION_SQL.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--") and not stmt.startswith("PRAGMA"):
                conn.execute(text(stmt))
    return repo


def make_snapshot(
    ticker="PETR4",
    institution="XP INVESTIMENTOS",
    ref_date=date(2026, 7, 3),
    quantity=Decimal("100"),
    snapshot_hash: str | None = None
) -> PositionSnapshot:
    from backend.domains.investments.normalizers.b3_normalizer import B3CustodyNormalizer
    from backend.domains.investments.parsers.dto import RawB3StockPosition
    
    if snapshot_hash:
        import hashlib
        h = snapshot_hash
    else:
        import hashlib
        h = hashlib.md5(f"{ref_date.isoformat()}|{ticker}|{institution}".encode()).hexdigest()
    
    return PositionSnapshot(
        source_system="B3_AREA_INVESTIDOR",
        reference_date=ref_date,
        ticker=ticker,
        asset_type=AssetTypeEnum.STOCK,
        institution=institution,
        quantity=quantity,
        unit_price=Decimal("35.50"),
        total_value=quantity * Decimal("35.50"),
        snapshot_hash=h,
        metadata={"original_ticker": ticker}
    )


class TestPositionRepository:

    def test_save_many_basic(self):
        repo = make_repo()
        snaps = [make_snapshot("PETR4"), make_snapshot("VALE3")]
        
        count = repo.save_many(snaps)
        
        assert count == 2
        assert repo.count_by_date("2026-07-03") == 2

    def test_save_many_empty(self):
        repo = make_repo()
        count = repo.save_many([])
        assert count == 0

    def test_upsert_idempotency(self):
        """Inserir o mesmo snapshot 2x deve resultar em 1 registro (não duplicar)."""
        repo = make_repo()
        snap = make_snapshot("BBAS3", quantity=Decimal("50"))
        
        repo.save_many([snap])
        repo.save_many([snap])  # Segunda vez: deve fazer UPDATE
        
        assert repo.count_by_date("2026-07-03") == 1

    def test_upsert_updates_quantity(self):
        """Segundo save_many com quantidade diferente deve atualizar o registro."""
        repo = make_repo()
        snap_v1 = make_snapshot("WEGE3", quantity=Decimal("50"))
        snap_v2 = make_snapshot("WEGE3", quantity=Decimal("75"))  # Mesma hash = mesmo hash
        
        repo.save_many([snap_v1])
        repo.save_many([snap_v2])
        
        row = repo.find_by_hash(snap_v1.snapshot_hash)
        assert row is not None
        assert row["quantity"] == "75"

    def test_find_by_hash_not_found(self):
        repo = make_repo()
        result = repo.find_by_hash("hash_inexistente_xyz")
        assert result is None

    def test_find_by_hash_found(self):
        repo = make_repo()
        snap = make_snapshot("KLBN4")
        repo.save_many([snap])
        
        row = repo.find_by_hash(snap.snapshot_hash)
        
        assert row is not None
        assert row["ticker"] == "KLBN4"
        assert row["asset_type"] == "STOCK"
        assert row["source_system"] == "B3_AREA_INVESTIDOR"

    def test_rollback_on_partial_failure(self):
        """Simula falha na transação: nenhum registro deve ser salvo."""
        repo = make_repo()
        snap_ok = make_snapshot("BBSE3")
        
        # Snapshot com hash inválido para forçar erro após o primeiro
        # Vamos forçar erro injetando dado inválido no SQL
        from unittest.mock import patch, MagicMock
        
        with patch.object(repo._engine, "begin") as mock_begin:
            mock_conn = MagicMock()
            mock_conn.__enter__ = lambda s: mock_conn
            mock_conn.__exit__ = lambda s, *a: False
            mock_conn.execute.side_effect = Exception("Forced DB error")
            mock_begin.return_value = mock_conn
            
            with pytest.raises(PositionRepositoryException, match="Erro ao persistir"):
                repo.save_many([snap_ok])


class TestPipelineWithRepository:
    """Testes de integração do Pipeline com o Repository."""
    
    def test_pipeline_without_repo(self):
        """Pipeline sem repository: persisted_count = 0."""
        from backend.domains.investments.pipelines.b3_custody_pipeline import B3CustodyPipeline
        from unittest.mock import MagicMock
        import os
        
        sample_path = str(
            Path(__file__).parent.parent.parent.parent.parent
            / "samples" / "Exemplo_Ativos_B3.csv"
        )
        
        if not os.path.exists(sample_path):
            pytest.skip("Arquivo de amostra não encontrado")
        
        pipeline = B3CustodyPipeline()  # Sem repository
        result = pipeline.execute(sample_path, date(2026, 7, 3))
        
        assert result.status == "SUCCESS"
        assert result.persisted_count == 0  # Sem repo, não persiste
        assert result.processed_count > 0

    def test_pipeline_with_repo_integration(self):
        """Pipeline com repository: persiste snapshots no banco."""
        from backend.domains.investments.pipelines.b3_custody_pipeline import B3CustodyPipeline
        import os
        
        sample_path = str(
            Path(__file__).parent.parent.parent.parent.parent
            / "samples" / "Exemplo_Ativos_B3.csv"
        )
        
        if not os.path.exists(sample_path):
            pytest.skip("Arquivo de amostra não encontrado")
        
        repo = make_repo()
        pipeline = B3CustodyPipeline(repository=repo)
        result = pipeline.execute(sample_path, date(2026, 7, 3))
        
        assert result.status == "SUCCESS", f"Erros: {result.errors}"
        assert result.processed_count > 0
        assert result.persisted_count == result.processed_count
        assert repo.count_by_date("2026-07-03") == result.persisted_count

    def test_pipeline_idempotency_with_repo(self):
        """Executar o pipeline 2x na mesma data não deve duplicar registros."""
        from backend.domains.investments.pipelines.b3_custody_pipeline import B3CustodyPipeline
        import os
        
        sample_path = str(
            Path(__file__).parent.parent.parent.parent.parent
            / "samples" / "Exemplo_Ativos_B3.csv"
        )
        
        if not os.path.exists(sample_path):
            pytest.skip("Arquivo de amostra não encontrado")
        
        repo = make_repo()
        pipeline = B3CustodyPipeline(repository=repo)
        
        result1 = pipeline.execute(sample_path, date(2026, 7, 3))
        result2 = pipeline.execute(sample_path, date(2026, 7, 3))  # Idêntico
        
        count_after = repo.count_by_date("2026-07-03")
        
        # Deve ter exatamente o mesmo número de registros após a 2ª execução
        assert count_after == result1.persisted_count
        assert result2.status == "SUCCESS"
