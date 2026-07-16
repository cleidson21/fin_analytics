import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.ai.classification.classification_models import AIClassificationRecord

logger = logging.getLogger(__name__)

class ClassificationRepository:
    def ensure_table_exists(self, session: Session):
        query = text("""
            CREATE TABLE IF NOT EXISTS ai_classifications (
                id TEXT PRIMARY KEY,
                transaction_hash TEXT,
                prompt_hash TEXT,
                suggested_category TEXT,
                confidence REAL,
                accepted_by_user BOOLEAN,
                final_category TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        session.execute(query)
        session.commit()

    def get_cached_classification(self, session: Session, prompt_hash: str) -> Optional[AIClassificationRecord]:
        query = text("""
            SELECT id, transaction_hash, prompt_hash, suggested_category, confidence, 
                   accepted_by_user, final_category, created_at 
            FROM ai_classifications 
            WHERE prompt_hash = :prompt_hash 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        result = session.execute(query, {"prompt_hash": prompt_hash}).fetchone()
        
        if result:
            return AIClassificationRecord(
                id=result[0],
                transaction_hash=result[1],
                prompt_hash=result[2],
                suggested_category=result[3],
                confidence=result[4],
                accepted_by_user=result[5],
                final_category=result[6],
                created_at=result[7]
            )
        return None

    def save_classification(self, session: Session, record: AIClassificationRecord):
        query = text("""
            INSERT INTO ai_classifications (
                id, transaction_hash, prompt_hash, suggested_category, confidence, 
                accepted_by_user, final_category, created_at
            ) VALUES (
                :id, :transaction_hash, :prompt_hash, :suggested_category, :confidence,
                :accepted_by_user, :final_category, strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            )
        """)
        import uuid
        record_id = record.id or str(uuid.uuid4())
        session.execute(query, {
            "id": record_id,
            "transaction_hash": record.transaction_hash,
            "prompt_hash": record.prompt_hash,
            "suggested_category": record.suggested_category,
            "confidence": record.confidence,
            "accepted_by_user": record.accepted_by_user,
            "final_category": record.final_category
        })
        session.commit()
