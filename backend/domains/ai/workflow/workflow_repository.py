import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from backend.domains.ai.workflow.workflow_models import WorkflowRunRecord

logger = logging.getLogger(__name__)

class WorkflowRepository:
    def ensure_table_exists(self, session: Session):
        query = text("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                id TEXT PRIMARY KEY,
                workflow_name TEXT,
                workflow_type TEXT,
                status TEXT,
                started_at TEXT,
                finished_at TEXT,
                duration_ms INTEGER,
                trigger TEXT,
                executed_steps TEXT,
                failed_step TEXT,
                error_message TEXT
            )
        """)
        session.execute(query)
        session.commit()

    def create_run(self, session: Session, record: WorkflowRunRecord):
        self.ensure_table_exists(session)
        query = text("""
            INSERT INTO workflow_runs (
                id, workflow_name, workflow_type, status, started_at, trigger, executed_steps
            ) VALUES (
                :id, :workflow_name, :workflow_type, :status, :started_at, :trigger, :executed_steps
            )
        """)
        session.execute(query, {
            "id": record.id,
            "workflow_name": record.workflow_name,
            "workflow_type": record.workflow_type,
            "status": record.status,
            "started_at": record.started_at,
            "trigger": record.trigger,
            "executed_steps": record.executed_steps
        })
        session.commit()

    def update_run(self, session: Session, record: WorkflowRunRecord):
        query = text("""
            UPDATE workflow_runs
            SET status = :status,
                finished_at = :finished_at,
                duration_ms = :duration_ms,
                executed_steps = :executed_steps,
                failed_step = :failed_step,
                error_message = :error_message
            WHERE id = :id
        """)
        session.execute(query, {
            "id": record.id,
            "status": record.status,
            "finished_at": record.finished_at,
            "duration_ms": record.duration_ms,
            "executed_steps": record.executed_steps,
            "failed_step": record.failed_step,
            "error_message": record.error_message
        })
        session.commit()

    def get_last_run_status(self, session: Session, workflow_name: str) -> str:
        self.ensure_table_exists(session)
        query = text("""
            SELECT status FROM workflow_runs
            WHERE workflow_name = :workflow_name
            ORDER BY started_at DESC LIMIT 1
        """)
        row = session.execute(query, {"workflow_name": workflow_name}).fetchone()
        if row:
            return row[0]
        return "PENDING"
        
    def get_last_execution_time(self, session: Session) -> str:
        self.ensure_table_exists(session)
        query = text("""
            SELECT started_at FROM workflow_runs
            ORDER BY started_at DESC LIMIT 1
        """)
        row = session.execute(query).fetchone()
        if row:
            return row[0]
        return "N/A"
