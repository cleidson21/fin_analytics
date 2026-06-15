from sqlalchemy.orm import Session
from app.models.governance import AuditLog
from datetime import datetime
import json
import uuid
from typing import Optional, List

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_event(self, entity_type: str, entity_id: str, action: str, field_changes: Optional[dict] = None, user: str = 'system') -> AuditLog:
        """Registra um evento de auditoria no sistema."""
        log = AuditLog(
            id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field_changes=json.dumps(field_changes) if field_changes else None,
            changed_by=user,
            created_at=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_history(self, entity_type: str, entity_id: str) -> List[AuditLog]:
        """Recupera o histórico de operações para uma entidade."""
        return self.db.query(AuditLog).filter(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        ).order_by(AuditLog.created_at.asc()).all()

    def trace_import_run(self, import_run_id: str) -> List[AuditLog]:
        """Rastreabilidade completa de todas as ações de um ImportRun."""
        return self.get_history(entity_type="ImportRun", entity_id=import_run_id)
