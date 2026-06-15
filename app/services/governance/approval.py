from sqlalchemy.orm import Session
from app.models.governance import ImportRun, StagingImport, StagingPosition, StagingDividend
from app.models.core_finance import Transaction
from app.models.wealth import Position, Dividend
import uuid

class ApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def confirm_import(self, run_id: str, user: str = 'system') -> ImportRun:
        """Confirma a importação e promove staging -> ledger."""
        run = self.db.query(ImportRun).filter(ImportRun.id == run_id).first()
        if not run:
            raise ValueError("ImportRun not found")
        
        if run.status != 'PENDING':
            raise ValueError(f"ImportRun cannot be confirmed from status {run.status}")

        self._promote_transactions(run_id)
        self._promote_positions(run_id)
        self._promote_dividends(run_id)
        
        run.status = 'COMPLETED'
        
        self.db.commit()
        self.db.refresh(run)
        return run

    def reject_import(self, run_id: str, reason: str, user: str = 'system') -> ImportRun:
        """Rejeita a importação. Entidades na ledger vinculadas seriam apagadas por ON DELETE CASCADE caso tivessem sido promovidas. Staging é mantido como FAILED."""
        run = self.db.query(ImportRun).filter(ImportRun.id == run_id).first()
        if not run:
            raise ValueError("ImportRun not found")
            
        run.status = 'FAILED'
        run.error_log = reason
        run.rollback_reason = reason
        run.rollback_user = user
        
        # Marcar staging como FAILED
        self.db.query(StagingImport).filter(StagingImport.import_run_id == run_id).update({"status": "FAILED"})
        self.db.query(StagingPosition).filter(StagingPosition.import_run_id == run_id).update({"validation_status": "FAILED"})
        self.db.query(StagingDividend).filter(StagingDividend.import_run_id == run_id).update({"validation_status": "FAILED"})
        
        self.db.commit()
        self.db.refresh(run)
        return run

    def _promote_transactions(self, run_id: str):
        stg_items = self.db.query(StagingImport).filter(
            StagingImport.import_run_id == run_id, 
            StagingImport.status == 'PENDING'
        ).all()
        
        for stg in stg_items:
            # Fake parsing date for promotion
            from datetime import date
            dt = date.today()
            if stg.date:
                try:
                    dt = date.fromisoformat(stg.date)
                except ValueError:
                    pass

            t = Transaction(
                id_economico=str(uuid.uuid4()),
                source="IMPORT",
                import_run_id=run_id,
                source_line_no=stg.source_line_no,
                data=dt,
                descricao_original=stg.description or "Unknown",
                descricao_normalizada=stg.description or "Unknown",
                valor=stg.amount or 0.0,
                valor_cents=stg.amount_cents or int((stg.amount or 0) * 100),
                natureza='EXPENSE' if (stg.amount or 0) < 0 else 'INCOME',
                perfil='CASA',
                classificacao_fonte='ETL'
            )
            self.db.add(t)
            stg.status = 'PROMOTED'

    def _promote_positions(self, run_id: str):
        stg_items = self.db.query(StagingPosition).filter(
            StagingPosition.import_run_id == run_id, 
            StagingPosition.validation_status == 'PENDING'
        ).all()
        
        for stg in stg_items:
            p = Position(
                ticker=stg.ticker,
                data_snapshot=stg.data_snapshot,
                source=stg.source or "IMPORT",
                quantidade=stg.quantidade or 0.0,
                preco_medio=stg.preco_medio or 0.0,
                total_investido=stg.total_investido or 0.0,
                preco_atual=stg.preco_atual or 0.0,
                total_atual=stg.total_atual or 0.0,
                ganho=stg.ganho or 0.0,
                import_run_id=run_id,
                source_line_no=stg.source_line_no
            )
            self.db.add(p)
            stg.validation_status = 'PROMOTED'

    def _promote_dividends(self, run_id: str):
        stg_items = self.db.query(StagingDividend).filter(
            StagingDividend.import_run_id == run_id, 
            StagingDividend.validation_status == 'PENDING'
        ).all()
        
        for stg in stg_items:
            d = Dividend(
                id_economico=stg.id_economico or str(uuid.uuid4()),
                source=stg.source or "IMPORT",
                ticker=stg.ticker,
                tipo_evento=stg.tipo_evento or "DIVIDENDO",
                data_pagamento=stg.data_pagamento,
                valor_liquido=stg.valor_liquido or 0.0,
                valor_liquido_cents=stg.valor_liquido_cents,
                import_run_id=run_id,
                source_line_no=stg.source_line_no
            )
            self.db.add(d)
            stg.validation_status = 'PROMOTED'
