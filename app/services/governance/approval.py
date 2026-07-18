from sqlalchemy.orm import Session
from app.models.governance import ImportRun, StagingImport, StagingPosition, StagingDividend
from app.models.core_finance import Transaction
from app.models.wealth import Position, Dividend
import uuid

class ApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def confirm_import(self, run_id: str, user: str = 'system') -> ImportRun:
        """DEPRECATED: O fluxo agora deve ser processado em GovernanceImportService.confirm_and_process()"""
        raise NotImplementedError("This method is deprecated. Use GovernanceImportService.confirm_and_process() instead.")

    def reject_import(self, run_id: str, reason: str, user: str = 'system') -> ImportRun:
        """DEPRECATED: O fluxo de rollback será integrado na GovernanceImportService"""
        run = self.db.query(ImportRun).filter(ImportRun.id == run_id).first()
        if not run:
            raise ValueError("ImportRun not found")
            
        run.status = 'FAILED'
        run.error_log = reason
        run.rollback_reason = reason
        run.rollback_user = user
        
        # Marcar artifacts como FAILED
        # (Em teoria também faria rollback nas tabelas finais se tivessem transações já persistidas)
        self.db.commit()
        self.db.refresh(run)
        return run
