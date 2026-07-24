from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from backend.domain.entities.account import Account
from backend.domain.enums.provider_type import ProviderType
from backend.application.queries.get_accounts import GetAccountsQuery

class IAccountRepository(ABC):
    @abstractmethod
    async def create(self, account: Account) -> Account:
        pass

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[Account]:
        pass

    @abstractmethod
    async def get_by_external_id(self, external_id: str, provider: ProviderType) -> Optional[Account]:
        pass

    @abstractmethod
    async def list(self, user_id: UUID, filters: GetAccountsQuery) -> List[Account]:
        pass

    @abstractmethod
    async def update_balance(self, id: UUID, balance: Decimal, updated_at: datetime) -> Account:
        pass

    @abstractmethod
    async def upsert(self, account: Account) -> Account:
        pass
