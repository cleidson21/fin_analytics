from abc import ABC, abstractmethod
from backend.infrastructure.persistence.models.sync_log import SyncLogModel

class ISyncLogRepository(ABC):
    @abstractmethod
    async def create(self, log: SyncLogModel) -> SyncLogModel:
        pass
    
    @abstractmethod
    async def get_last_sync(self) -> SyncLogModel:
        pass
    
    @abstractmethod
    async def get_history(self, limit: int = 10) -> list[SyncLogModel]:
        pass
