from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from backend.application.ports.sync_log_repository import ISyncLogRepository
from backend.infrastructure.persistence.models.sync_log import SyncLogModel

class SQLAlchemySyncLogRepository(ISyncLogRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, log: SyncLogModel) -> SyncLogModel:
        self._session.add(log)
        await self._session.commit()
        await self._session.refresh(log)
        return log

    async def get_last_sync(self) -> SyncLogModel | None:
        result = await self._session.execute(
            select(SyncLogModel).order_by(desc(SyncLogModel.start_time)).limit(1)
        )
        return result.scalars().first()

    async def get_history(self, limit: int = 10) -> list[SyncLogModel]:
        result = await self._session.execute(
            select(SyncLogModel).order_by(desc(SyncLogModel.start_time)).limit(limit)
        )
        return list(result.scalars().all())
