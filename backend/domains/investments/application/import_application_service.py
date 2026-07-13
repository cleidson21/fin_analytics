from sqlalchemy.orm import Session
from backend.domains.investments.services.import_service import ImportService
from backend.domains.investments.services.reconciliation_service import ReconciliationService
from backend.domains.investments.repositories.import_log_repository import ImportLogRepository
from backend.domains.investments.import_report import ImportReport
import hashlib
from datetime import datetime, timezone

class ImportApplicationService:
    def __init__(
        self,
        import_service: ImportService,
        reconciliation_service: ReconciliationService,
        import_log_repo: ImportLogRepository
    ):
        self.import_service = import_service
        self.reconciliation_service = reconciliation_service
        self.import_log_repo = import_log_repo

    def execute_import(self, db: Session, content: bytes, filename: str, import_type: str) -> ImportReport:
        # Run ImportService
        report = self.import_service.process_import(db, content, filename, import_type)
        
        # Log to db
        checksum = hashlib.sha256(content).hexdigest()
        file_size = len(content)
        file_type = filename.split('.')[-1].upper() if '.' in filename else 'UNKNOWN'
        
        log_entry = {
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "checksum": checksum,
            "parser": "ImportApplicationService",
            "status": "SUCCESS" if report.success else "FAILED",
            "rows_read": 0,
            "rows_imported": report.rows_persisted,
            "rows_duplicated": report.duplicates_detected,
            "rows_failed": len(report.errors),
            "processing_time_ms": report.processing_time_ms,
            "created_at": datetime.now(timezone.utc),
            "error_message": "; ".join([e.message for e in report.errors]) if report.errors else None,
            "metadata_json": {}
        }
        self.import_log_repo.create(db, log_entry)
        
        return report

    def execute_reconciliation(self, db: Session, target_date=None):
        # Delegate to reconciliation service
        return self.reconciliation_service.reconcile(db, target_date)
