import logging
import time
import hashlib
from typing import List
from sqlalchemy.orm import Session

from backend.domains.investments.import_report import ImportReport, ImportError
from backend.domains.investments.services.parse_service import ParseService
from backend.domains.investments.services.persistence_service import PersistenceService

logger = logging.getLogger(__name__)

class ImportService:
    """
    Orquestrador Refatorado de Importação (Gate 10.9).
    Delega o parsing e persistência.
    """

    def __init__(self, parse_service: ParseService, persistence_service: PersistenceService):
        self.parse_service = parse_service
        self.persistence_service = persistence_service

    def process_import(self, db: Session, content: bytes, filename: str, import_type: str) -> ImportReport:
        report = ImportReport(source=import_type, file_name=filename)
        start_time = time.perf_counter()
        
        checksum = hashlib.sha256(content).hexdigest()
        file_size = len(content)
        file_type = filename.split('.')[-1].upper() if '.' in filename else 'UNKNOWN'
        
        try:
            trades, parser_name = self.parse_service.parse_content(content, filename, import_type, report)

            if trades:
                self.persistence_service.persist_trades(db, trades, report)
            
            report.success = True if report.rows_persisted > 0 or report.duplicates_detected > 0 else False
                
        except Exception as e:
            logger.error(f"Erro fatal na importação: {e}")
            report.errors.append(ImportError(message=f"Erro crítico no processamento: {str(e)}"))
            report.success = False
        finally:
            end_time = time.perf_counter()
            report.processing_time_ms = int((end_time - start_time) * 1000)
            
        return report
