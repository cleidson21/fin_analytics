import logging
from typing import List
from sqlalchemy.orm import Session
from backend.domains.investments.import_report import ImportReport
from backend.domains.investments.repositories.trade_repository import TradeRepository
from backend.domains.investments.dto import TradeDTO

logger = logging.getLogger(__name__)

class PersistenceService:
    def __init__(self, trade_repo: TradeRepository):
        self.trade_repo = trade_repo

    def persist_trades(self, db: Session, trades: List[TradeDTO], report: ImportReport):
        for trade_dto in trades:
            existing = self.trade_repo.exists_hash(db, trade_dto.idempotency_hash)
            if existing:
                report.duplicates_detected += 1
            else:
                success = self.trade_repo.save_idempotent(db, trade_dto)
                if success:
                    report.rows_persisted += 1
                else:
                    report.duplicates_detected += 1
