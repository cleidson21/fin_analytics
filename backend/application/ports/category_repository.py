from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from backend.domain.entities.category import Category

class ICategoryRepository(ABC):
    @abstractmethod
    async def create(self, category: Category) -> Category:
        pass

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[Category]:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Category]:
        pass

    @abstractmethod
    async def list_all(self) -> List[Category]:
        pass
