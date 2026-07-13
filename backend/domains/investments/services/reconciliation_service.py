from typing import List, Dict, Tuple
from decimal import Decimal
from backend.domains.investments.dto import ReconciliationResult, ReconciliationStatus, ReconciliationRecommendation
from backend.domains.investments.repositories.trade_repository import TradeRepository
from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
from backend.domains.investments.engines.position_engine import PositionEngine
from sqlalchemy.orm import Session

class ReconciliationService:
    def __init__(self, trade_repo, snapshot_repo, position_engine):
        self.trade_repo = trade_repo
        self.snapshot_repo = snapshot_repo
        self.position_engine = position_engine
        
    def reconcile(self, db: Session, target_date=None) -> List[ReconciliationResult]:
        trades = self.trade_repo.list_all(db)
        snapshots = self.snapshot_repo.list_all(db)
        
        # Calculates ledger position
        positions = self.position_engine.calculate_position(trades, snapshots)
        
        # Group snapshot quantities by (ticker, broker) to compare with ledger
        # Typically the latest snapshot gives the declared position.
        # Since snapshot repo returns all, we find the latest for each ticker/broker
        latest_snapshots: Dict[Tuple[str, str], Decimal] = {}
        for snap in snapshots:
            key = (snap.asset, snap.broker)
            # Simplification: in a real world we sort by date, assuming last is the declared one
            # If multiple exist for the same asset/broker, just take the last one or accumulate if they are different accounts?
            # Normally snapshot is the exact amount on that date. We'll assume the snapshot has the latest quantity.
            latest_snapshots[key] = snap.quantity
            
        results = []
        
        # Compare Ledger vs Snapshot
        for pos in positions:
            key = (pos.asset, pos.broker)
            ledger_qty = pos.quantity
            snapshot_qty = latest_snapshots.get(key, Decimal('0'))
            
            difference = ledger_qty - snapshot_qty
            difference_percent = (difference / snapshot_qty) if snapshot_qty > 0 else (Decimal('1') if difference > 0 else Decimal('0'))
            
            abs_diff_pct = abs(difference_percent)
            
            status = ReconciliationStatus.OK
            recommendation = ReconciliationRecommendation.NO_ACTION
            
            if abs_diff_pct == 0:
                status = ReconciliationStatus.OK
                recommendation = ReconciliationRecommendation.NO_ACTION
            elif abs_diff_pct <= Decimal('0.01'):
                status = ReconciliationStatus.WARNING
                recommendation = ReconciliationRecommendation.CHECK_CUSTODY
            else:
                status = ReconciliationStatus.ERROR
                if snapshot_qty == Decimal('0'):
                    recommendation = ReconciliationRecommendation.UPDATE_SNAPSHOT
                else:
                    recommendation = ReconciliationRecommendation.REVIEW_IMPORT
                    
            results.append(
                ReconciliationResult(
                    ticker=pos.asset,
                    broker=pos.broker,
                    ledger_quantity=ledger_qty,
                    snapshot_quantity=snapshot_qty,
                    difference=difference,
                    difference_percent=difference_percent,
                    status=status,
                    recommendation=recommendation
                )
            )
            
        return results
