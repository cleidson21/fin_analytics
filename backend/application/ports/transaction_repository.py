from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from backend.domain.entities.transaction import Transaction

class ITransactionRepository(ABC):
    @abstractmethod
    async def create(self, transaction: Transaction) -> Transaction:
        pass

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[Transaction]:
        pass

    @abstractmethod
    async def get_by_hash(self, hash: str) -> Optional[Transaction]:
        pass

    @abstractmethod
    async def bulk_upsert(self, transactions: List[Transaction]) -> Dict[str, int]:
        """Upserts a list of transactions.
        Returns a dict with metrics like 'inserted', 'skipped', 'errors'.
        """
        pass

    @abstractmethod
    async def update(self, transaction: Transaction) -> Transaction:
        pass
