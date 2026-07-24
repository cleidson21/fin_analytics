from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from backend.domain.entities.institution import Institution

class IInstitutionRepository(ABC):
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Institution]:
        pass

    @abstractmethod
    async def get_or_create(self, code: str, name: str) -> Institution:
        pass

    @abstractmethod
    async def list(self) -> List[Institution]:
        pass
