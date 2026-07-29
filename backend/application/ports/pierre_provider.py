from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

from backend.application.dtos.provider_dtos import ProviderTransactionDTO, ProviderAccountDTO

class IPierreProvider(ABC):
    @abstractmethod
    async def get_transactions(self, start_date: date, end_date: date, account_type: Optional[str] = None) -> List[ProviderTransactionDTO]:
        pass

    @abstractmethod
    async def get_accounts(self) -> List[ProviderAccountDTO]:
        pass

    @abstractmethod
    async def __aenter__(self) -> "IPierreProvider":
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
