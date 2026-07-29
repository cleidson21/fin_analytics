from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func

from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus

class GetGovernanceDashboardUseCase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self) -> Dict[str, Any]:
        result = await self.session.execute(select(SyncLogModel))
        logs = list(result.scalars().all())
        
        total_runs = len(logs)
        confirmed_runs = sum(1 for log in logs if log.status == SyncStatus.SUCCESS)
        pending_runs = sum(1 for log in logs if log.status == SyncStatus.RUNNING)
        lines_inserted = sum(log.inserted for log in logs if log.inserted)
        lines_updated = sum(log.updated for log in logs if log.updated)
        lines_failed = sum(1 for log in logs if log.status == SyncStatus.FAILED)
        
        last_import = None
        if logs:
            sorted_logs = sorted(logs, key=lambda x: x.start_time, reverse=True)
            last_import = sorted_logs[0].start_time.isoformat() if sorted_logs[0].start_time else None
            
        return {
            "total_runs": total_runs,
            "confirmed_runs": confirmed_runs,
            "pending_runs": pending_runs,
            "lines_inserted": lines_inserted,
            "lines_updated": lines_updated,
            "lines_failed": lines_failed,
            "last_import": last_import
        }

class GetGovernanceImportsUseCase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, limit: int = 10) -> Dict[str, Any]:
        result = await self.session.execute(
            select(SyncLogModel).order_by(desc(SyncLogModel.start_time)).limit(limit)
        )
        logs = list(result.scalars().all())
        
        count_result = await self.session.execute(select(func.count(SyncLogModel.id)))
        total = count_result.scalar() or 0
        
        items = []
        for log in logs:
            items.append({
                "id": log.id,
                "source_type": log.provider.value,
                "file_name": "API Pierre" if log.provider.value == "PIERRE" else "Upload",
                "started_at": log.start_time.isoformat() if log.start_time else "",
                "status": log.status.value,
                "rows_read": log.transactions_synced or 0,
                "rows_inserted": log.inserted or 0,
                "rows_failed": 1 if log.status == SyncStatus.FAILED else 0
            })
            
        return {
            "items": items,
            "total": total
        }
