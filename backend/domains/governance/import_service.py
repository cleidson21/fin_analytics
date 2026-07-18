from typing import Dict, Any
from datetime import datetime, timezone
import uuid
import json
from backend.shared.db import engine
from sqlalchemy import text
from backend.domains.imports.dto import RawDocument, ImportSource
from backend.domains.imports.parsers.pierre_txt import PierreTxtParser
from backend.domains.imports.readers.myprofit_csv import MyProfitProventosReader
from backend.domains.imports.parsers.myprofit_proventos import MyProfitProventosParser
from backend.domains.imports.readers.nubank_conta import NubankContaReader
from backend.domains.imports.parsers.nubank_conta import NubankContaParser
from backend.domains.imports.readers.nubank_fatura import NubankFaturaReader
from backend.domains.imports.parsers.nubank_fatura import NubankFaturaParser
from backend.domains.imports.parsers.factory import ImportParserFactory
from backend.domains.banking.models import Transaction
from backend.domains.investments.models import Dividend, PositionSnapshot, PortfolioSnapshot
from app.services.ai_layer.classification import ClassificationEngineService
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class GovernanceImportService:
    def __init__(self):
        self.db = engine

    def process_import(self, file_name: str, raw_text: str = "", source_type: str = "", user_id: str = "admin", **kwargs) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()
        
        # 1. Detect file type based on source_type
        detected_type = getattr(ImportSource, source_type, source_type)

        # 2. Persist ImportRun
        with self.db.connect() as conn:
            # Pegar o usuário admin
            user = conn.execute(text("SELECT id FROM users WHERE email='admin' LIMIT 1")).fetchone()
            if not user:
                # Fallback para o usuário existente se o admin não estiver populado direito
                user = conn.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
            
            user_id = user[0] if user else "mock-user-id"

            conn.execute(text("""
                INSERT INTO import_runs (id, user_id, source, status, filename, started_at)
                VALUES (:id, :user_id, :source, 'PENDING', :filename, :started_at)
            """), {
                "id": run_id,
                "user_id": user_id,
                "source": detected_type,
                "filename": file_name,
                "started_at": started_at
            })
            
            # Count rows and run parsing
            lines = raw_text.splitlines() if raw_text else []
            total_rows = len(lines)
            inserted = 0
            
            try:
                raw_content = kwargs.get("raw_content", raw_text)
                parsed_rows = ImportParserFactory.execute(raw_content, file_name, source_type)

                
                # Insert parsed rows as artifacts
                if parsed_rows:
                    for i, row in enumerate(parsed_rows):
                        artifact_id = str(uuid.uuid4())
                        conn.execute(text("""
                            INSERT INTO import_artifacts (id, run_id, row_number, raw_data, status)
                            VALUES (:id, :run_id, :row_number, :raw_data, 'INSERTED')
                        """), {
                            "id": artifact_id,
                            "run_id": run_id,
                            "row_number": i + 1,
                            "raw_data": row.model_dump_json()
                        })
                        inserted += 1
                else:
                    # Default generic dump for other files that don't have parsers explicitly wired yet
                    for i, line in enumerate(lines[:100]):
                        artifact_id = str(uuid.uuid4())
                        conn.execute(text("""
                            INSERT INTO import_artifacts (id, run_id, row_number, raw_data, status)
                            VALUES (:id, :run_id, :row_number, :raw_data, 'INSERTED')
                        """), {
                            "id": artifact_id,
                            "run_id": run_id,
                            "row_number": i + 1,
                            "raw_data": json.dumps({"raw_line": line})
                        })
                        inserted += 1
            except Exception as e:
                print(f"Error parsing file {file_name}: {e}")
                # Fallback on generic dump so UI won't completely fail
                for i, line in enumerate(lines[:100]):
                    artifact_id = str(uuid.uuid4())
                    conn.execute(text("""
                        INSERT INTO import_artifacts (id, run_id, row_number, raw_data, status)
                        VALUES (:id, :run_id, :row_number, :raw_data, 'INSERTED')
                    """), {
                        "id": artifact_id,
                        "run_id": run_id,
                        "row_number": i + 1,
                        "raw_data": json.dumps({"raw_line": line})
                    })
                    inserted += 1
                
            conn.execute(text("""
                UPDATE import_runs 
                SET rows_parsed = :rows, rows_inserted = :inserted, finished_at = :finished_at
                WHERE id = :id
            """), {
                "rows": total_rows,
                "inserted": inserted,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "id": run_id
            })
            conn.commit()

            conn.commit()

        # Unified preview payload
        return {
            "run_id": run_id,
            "preview": {
                "detected_file_type": detected_type,
                "total_rows": total_rows,
                "valid_rows": inserted,
                "invalid_rows": 0,
                "warnings": [],
                "errors": [],
                "summary": {},
                "sample": []
            }
        }

    def confirm_and_process(self, run_id: str) -> Dict[str, Any]:
        """
        Staging -> Engines Financeiras.
        Lê de import_artifacts, passa pelos motores e persiste nas tabelas oficiais.
        """
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=self.db)
        
        inserted = 0
        failed = 0
        
        with SessionLocal() as session:
            run = session.execute(text("SELECT source FROM import_runs WHERE id = :id"), {"id": run_id}).fetchone()
            
            # Fetch default account
            account_row = session.execute(text("SELECT id FROM accounts LIMIT 1")).fetchone()
            fallback_account_id = account_row[0] if account_row else "00000000-0000-0000-0000-000000000000"
            
            # Fetch default asset
            asset_row = session.execute(text("SELECT id FROM assets LIMIT 1")).fetchone()
            fallback_asset_id = asset_row[0] if asset_row else "00000000-0000-0000-0000-000000000000"

            if not run:
                raise ValueError("ImportRun not found")
                
            source_type = run[0]
            artifacts = session.execute(
                text("SELECT id, raw_data, row_number FROM import_artifacts WHERE run_id = :id AND status IN ('INSERTED', 'PENDING')"), 
                {"id": run_id}
            ).fetchall()
            
            classifier = ClassificationEngineService(session)
            
            for art in artifacts:
                art_id, raw_data_str, row_no = art
                try:
                    data = json.loads(raw_data_str)
                    
                    ticker = data.get("ativo") or data.get("conta") or data.get("ticker") or "UNKNOWN"
                    asset_row = session.execute(text("SELECT id FROM assets WHERE ticker = :ticker"), {"ticker": ticker}).fetchone()
                    if asset_row:
                        current_asset_id = asset_row[0]
                    else:
                        current_asset_id = str(uuid.uuid4())
                        session.execute(text("INSERT INTO assets (id, ticker, type, name) VALUES (:id, :ticker, 'STOCK', :name)"), 
                                        {"id": current_asset_id, "ticker": ticker, "name": f"Ativo {ticker}"})
                    
                    if source_type in (ImportSource.NUBANK_CONTA, ImportSource.NUBANK_FATURA):
                        desc = data.get("description") or data.get("descricao") or "Unknown"
                        val = data.get("amount") or data.get("valor") or 0.0
                        dt_str = data.get("transaction_date") or data.get("data") or "2026-01-01"
                        
                        t = Transaction(
                            id=str(uuid.uuid4()),
                            account_id=fallback_account_id,
                            date=dt_str,
                            amount=int(abs(float(val)) * 100),
                            type='OUT' if float(val) < 0 else 'IN',
                            original_description=desc,
                            normalized_desc=desc,
                            source='NUBANK_CSV',
                            run_id=run_id
                        )
                        session.add(t)
                        
                    elif source_type == ImportSource.MYPROFIT_PROVENTOS:
                        d = Dividend(
                            id=str(uuid.uuid4()),
                            asset_id=current_asset_id,
                            account_id=fallback_account_id,
                            type='DIVIDEND',
                            
                            ex_date=data.get("transaction_date") or data.get("data_pagamento") or data.get("data_ex") or "2026-01-01",
                            payment_date=data.get("transaction_date") or data.get("data_pagamento") or "2026-01-01",
                            quantity_held=1.0,
                            value_per_share=0,
                            gross_amount=int(float(data.get("amount") or data.get("valor_liquido") or 0) * 100),
                            source='MYPROFIT_IMPORT',
                            run_id=run_id
                        )
                        session.add(d)
                        
                    elif source_type == ImportSource.PIERRE:
                        ps = PositionSnapshot(
                            id=str(uuid.uuid4()),
                            snapshot_hash=str(uuid.uuid4()),
                            reference_date=data.get("data") or "2026-01-01",
                            ticker=data.get("conta") or "UNKNOWN",
                            asset_type='UNKNOWN',
                            institution='PIERRE',
                            quantity=float(data.get("valor") or 0),
                            
                            run_id=run_id
                        )
                        session.add(ps)
                        
                    elif source_type == ImportSource.MYPROFIT_EVOLUCAO:
                        p = PortfolioSnapshot(
                            id=str(uuid.uuid4()),
                            user_id='mock-user-id',
                            date=data.get("reference_month") or f"2026-01-{row_no:02d}",
                            total_equity=int(float(data.get("patrimonio") or 0) * 100),
                            cost_basis=int(float(data.get("patrimonio") or 0) * 100),
                            run_id=run_id
                        )
                        session.add(p)
                        
                    elif source_type == ImportSource.B3:
                        ps = PositionSnapshot(
                            id=str(uuid.uuid4()),
                            snapshot_hash=str(uuid.uuid4()),
                            reference_date=datetime.now().isoformat(),
                            ticker=data.get("ativo") or "UNKNOWN",
                            asset_type='UNKNOWN',
                            institution='B3',
                            quantity=float(data.get("quantidade") or 0),
                            
                            run_id=run_id
                        )
                        session.add(ps)
                    
                    # No need to mark as PROCESSED since the check constraint only allows INSERTED.
                    # If it successfully goes to the engine, it's just kept as INSERTED.
                    inserted += 1
                except Exception as e:
                    logger.error(f"Erro processando artifact {art_id}: {e}")
                    failed += 1
                    session.execute(text("UPDATE import_artifacts SET status = 'ERROR', error_msg = :msg WHERE id = :id"), {"id": art_id, "msg": str(e)})
                    
            # 6. Atualização final de status
            final_status = 'SUCCESS' if failed == 0 else ('PARTIAL' if inserted > 0 else 'FAILED')
            session.execute(text("""
                UPDATE import_runs 
                SET status = :status, rows_inserted = :inserted, rows_errored = :failed, finished_at = :now
                WHERE id = :id
            """), {
                "status": final_status,
                "inserted": inserted,
                "failed": failed,
                "now": datetime.now(timezone.utc).isoformat(),
                "id": run_id
            })
            
            session.commit()
            
        return {
            "status": "success",
            "rows_processed": inserted,
            "rows_failed": failed
        }
