import json
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
import uuid

class ImportLogRepository:
    """
    Repositório focado exclusivamente na persistência e leitura
    do histórico de importações (import_logs). (Gate 10.2)
    """

    def create(self, db: Session, log_data: dict) -> str:
        """
        Cria um registro imutável da importação.
        """
        log_id = str(uuid.uuid4())
        
        # Format dates properly
        created_at = log_data.get('created_at')
        if not created_at:
            created_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%fZ')
        elif isinstance(created_at, datetime):
            created_at = created_at.strftime('%Y-%m-%dT%H:%M:%fZ')
            
        metadata_json = log_data.get('metadata_json', {})
        if isinstance(metadata_json, dict):
            metadata_json = json.dumps(metadata_json)

        query = text("""
            INSERT INTO import_logs (
                id, user_id, created_at, filename, file_type, file_size,
                checksum, parser, rows_read, rows_imported, rows_duplicated,
                rows_failed, processing_time_ms, status, error_message, metadata_json
            ) VALUES (
                :id, :user_id, :created_at, :filename, :file_type, :file_size,
                :checksum, :parser, :rows_read, :rows_imported, :rows_duplicated,
                :rows_failed, :processing_time_ms, :status, :error_message, :metadata_json
            )
        """)
        
        db.execute(query, {
            "id": log_id,
            "user_id": log_data.get("user_id", "SINGLE_USER"),
            "created_at": created_at,
            "filename": log_data.get("filename", ""),
            "file_type": log_data.get("file_type", "UNKNOWN"),
            "file_size": log_data.get("file_size", 0),
            "checksum": log_data.get("checksum", ""),
            "parser": log_data.get("parser", ""),
            "rows_read": log_data.get("rows_read", 0),
            "rows_imported": log_data.get("rows_imported", 0),
            "rows_duplicated": log_data.get("rows_duplicated", 0),
            "rows_failed": log_data.get("rows_failed", 0),
            "processing_time_ms": log_data.get("processing_time_ms", 0),
            "status": log_data.get("status", "FAILED"),
            "error_message": log_data.get("error_message"),
            "metadata_json": metadata_json
        })
        # Note: the caller (ImportService) should handle the commit.
        return log_id

    def list_history(self, db: Session, filters: dict = None) -> List[dict]:
        """
        Retorna o histórico com suporte a filtros.
        """
        filters = filters or {}
        
        base_query = "SELECT * FROM import_logs WHERE 1=1"
        params = {}
        
        if filters.get("status"):
            base_query += " AND status = :status"
            params["status"] = filters["status"]
            
        if filters.get("parser"):
            base_query += " AND parser = :parser"
            params["parser"] = filters["parser"]
            
        if filters.get("checksum"):
            base_query += " AND checksum = :checksum"
            params["checksum"] = filters["checksum"]
            
        if filters.get("filename"):
            base_query += " AND filename LIKE :filename"
            params["filename"] = f"%{filters['filename']}%"
            
        base_query += " ORDER BY created_at DESC"
        
        result = db.execute(text(base_query), params).mappings().all()
        return [dict(r) for r in result]
        
    def get_by_id(self, db: Session, log_id: str) -> Optional[dict]:
        query = text("SELECT * FROM import_logs WHERE id = :id")
        result = db.execute(query, {"id": log_id}).mappings().first()
        return dict(result) if result else None
        
    def delete(self, db: Session, log_id: str) -> bool:
        """Deletes an import log."""
        query = text("DELETE FROM import_logs WHERE id = :id")
        result = db.execute(query, {"id": log_id})
        return result.rowcount > 0
