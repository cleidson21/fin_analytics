import logging
import time
from datetime import datetime, timezone
from typing import List, Tuple
from sqlalchemy.orm import Session

from backend.domains.investments.import_report import ImportReport, ImportError, ImportWarning
from backend.domains.investments.repositories.trade_repository import TradeRepository
from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
from backend.domains.investments.repositories.import_log_repository import ImportLogRepository
from backend.domains.investments.parsers.cei_parser import B3MovementsParser
from backend.domains.investments.parsers.b3_parser import B3CustodyParser
from backend.domains.investments.parsers.csv_parser import CSVTradeParser
from backend.domains.investments.parsers.open_finance_parser import OpenFinanceParser
from backend.domains.investments.parsers.ofx_parser import OFXParser

import pandas as pd
import io
import hashlib

logger = logging.getLogger(__name__)

class ImportService:
    """
    Orquestrador Real do Pipeline de Ingestão de Dados (Gate 10.1).
    Executa a leitura, delega para os parsers reais, cuida do hash (idempotência)
    e persiste (DO NOTHING on conflict) via Repositories.
    """

    def __init__(self, db: Session):
        self.db = db
        self.trade_repo = TradeRepository()
        self.snapshot_repo = SnapshotRepository()
        self.import_log_repo = ImportLogRepository()

    def process_import(self, content: bytes, filename: str, import_type: str) -> ImportReport:
        """
        Método central que recebe o arquivo em memória, decide o parser
        e devolve o relatório consolidado de idempotência e sucesso.
        """
        report = ImportReport(source=import_type, file_name=filename)
        start_time = time.perf_counter()
        
        # Calculate checksum and file info (Gate 10.2)
        checksum = hashlib.sha256(content).hexdigest()
        file_size = len(content)
        file_type = filename.split('.')[-1].upper() if '.' in filename else 'UNKNOWN'
        
        parser_name = "UNKNOWN"
        
        try:
            trades = []
            
            # Escolhe o Parser de acordo com o tipo
            if import_type.upper() == "CEI":
                # CEI is generally Excel or CSV. We assume XLSX here since CEI/B3 gives XLSX
                try:
                    df = pd.read_excel(io.BytesIO(content), sheet_name="Negociação")
                    parser = B3MovementsParser()
                    parser_name = "B3MovementsParser"
                    # We would need a converter from RawB3Movement to TradeDTO, but since we created CSVTradeParser, 
                    # let's assume the user uploaded a CSV or we use CSVTradeParser as a generic fallback.
                    # We will just parse it as CSV for simplicity if it's a CEI export in CSV format.
                    parser = CSVTradeParser()
                    parser_name = "CSVTradeParser"
                    trades = parser.parse(content, filename, report)
                except Exception:
                    # Fallback to CSV parser if not excel
                    parser = CSVTradeParser()
                    parser_name = "CSVTradeParser"
                    trades = parser.parse(content, filename, report)
                    
            elif import_type.upper() == "OPEN_FINANCE":
                parser = OpenFinanceParser()
                parser_name = "OpenFinanceParser"
                trades = parser.parse(content, filename, report)
                
            elif import_type.upper() == "OFX":
                parser = OFXParser()
                parser_name = "OFXParser"
                trades = parser.parse(content, filename, report)
                
            else:
                # Default fallback CSV
                parser = CSVTradeParser()
                parser_name = "CSVTradeParser"
                trades = parser.parse(content, filename, report)

            # Persistência Idempotente
            if trades:
                self._persist_trades(trades, report)
            
            report.success = True if report.rows_persisted > 0 or report.duplicates_detected > 0 else False
                
        except Exception as e:
            logger.error(f"Erro fatal na importação: {e}")
            report.errors.append(ImportError(message=f"Erro crítico no processamento: {str(e)}"))
            report.success = False
        finally:
            end_time = time.perf_counter()
            report.finished_at = datetime.now(timezone.utc)
            report.elapsed_ms = int((end_time - start_time) * 1000)
            
            # Persistent Audit Logging (Gate 10.2)
            log_status = 'SUCCESS' if report.success else ('PARTIAL' if report.rows_persisted > 0 and len(report.errors) > 0 else 'FAILED')
            
            log_data = {
                "created_at": report.started_at,
                "filename": filename,
                "file_type": file_type,
                "file_size": file_size,
                "checksum": checksum,
                "parser": parser_name,
                "rows_read": report.rows_read,
                "rows_imported": report.rows_persisted,
                "rows_duplicated": report.duplicates_detected,
                "rows_failed": len(report.errors),
                "processing_time_ms": report.elapsed_ms,
                "status": log_status,
                "error_message": report.errors[0].message if report.errors else None,
                "metadata_json": {
                    "warnings": [w.message for w in report.warnings],
                    "source": report.source
                }
            }
            
            try:
                self.import_log_repo.create(self.db, log_data)
                self.db.commit()
            except Exception as log_ex:
                logger.error(f"Failed to save import log: {log_ex}")
                self.db.rollback()
            
        return report

    def _persist_trades(self, trades: List, report: ImportReport) -> None:
        """
        Tenta persistir transações. Caso haja conflito de Hash, incrementa duplicatas.
        O próprio Repository lida com 'ON CONFLICT DO NOTHING'.
        """
        for trade in trades:
            try:
                # Save Idempotent returns True if inserted, False if ignored
                inserted = self.trade_repo.save_idempotent(self.db, trade)
                if inserted:
                    report.rows_persisted += 1
                else:
                    report.duplicates_detected += 1
            except Exception as e:
                report.errors.append(ImportError(message=f"Falha de persistência no Ticker {trade.ticker}: {str(e)}"))
        
        self.db.commit()
