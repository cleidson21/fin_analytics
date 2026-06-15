from sqlalchemy.orm import Session
from app.models.governance import ImportRun, ImportArtifact
from datetime import datetime
from typing import Optional, List
import uuid

class ImportService:
    def __init__(self, db: Session):
        self.db = db

    def start_import_run(self, source_type: str, file_name: str, checksum: str, user: str = 'system') -> ImportRun:
        """Cria e inicia um novo ciclo de importação."""
        run = ImportRun(
            id=str(uuid.uuid4()),
            source_type=source_type,
            file_name=file_name,
            checksum=checksum,
            started_at=datetime.utcnow(),
            status='PENDING',
            created_by=user
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def add_artifact(self, run_id: str, artifact_type: str, storage_path: str, sha256: str, size: int) -> ImportArtifact:
        """Adiciona um artefato ao import run."""
        artifact = ImportArtifact(
            id=str(uuid.uuid4()),
            import_run_id=run_id,
            artifact_type=artifact_type,
            storage_path=storage_path,
            sha256=sha256,
            size_bytes=size,
            created_at=datetime.utcnow()
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def complete_import_run(self, run_id: str, rows_read: int, rows_inserted: int, rows_updated: int, rows_failed: int) -> ImportRun:
        """Conclui a importação com métricas."""
        run = self.db.query(ImportRun).filter(ImportRun.id == run_id).first()
        if not run:
            raise ValueError(f"ImportRun {run_id} not found")
        
        run.status = 'COMPLETED'
        run.finished_at = datetime.utcnow()
        run.rows_read = rows_read
        run.rows_inserted = rows_inserted
        run.rows_updated = rows_updated
        run.rows_failed = rows_failed
        
        self.db.commit()
        self.db.refresh(run)
        return run

    def fail_import_run(self, run_id: str, error_log: str) -> ImportRun:
        """Falha a importação logando o erro."""
        run = self.db.query(ImportRun).filter(ImportRun.id == run_id).first()
        if not run:
            raise ValueError(f"ImportRun {run_id} not found")
            
        run.status = 'FAILED'
        run.finished_at = datetime.utcnow()
        run.error_log = error_log
        
        self.db.commit()
        self.db.refresh(run)
        return run
