from typing import List
from uuid import UUID

from backend.application.ports.sync_log_repository import ISyncLogRepository
from backend.infrastructure.persistence.models.sync_log import SyncLogModel

class GetSyncLogsUseCase:
    def __init__(self, sync_log_repo: ISyncLogRepository):
        self._repo = sync_log_repo

    async def execute(self, limit: int = 10) -> List[dict]:
        logs = await self._repo.get_history(limit=limit)
        return [
            {
                "id": log.id,
                "provider": log.provider.value,
                "status": log.status.value,
                "start_time": log.start_time.isoformat() if log.start_time else None,
                "end_time": log.end_time.isoformat() if log.end_time else None,
                "duration_seconds": log.duration_seconds,
                "accounts_synced": log.accounts_synced,
                "transactions_synced": log.transactions_synced,
                "categories_synced": log.categories_synced,
                "inserted": log.inserted,
                "updated": log.updated,
                "ignored": log.ignored,
                "error_message": log.error_message,
            }
            for log in logs
        ]
