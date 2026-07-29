from typing import List
from backend.application.dtos.category_response_dto import CategoryResponseDTO
from backend.application.ports.category_repository import ICategoryRepository

class GetCategoriesUseCase:
    def __init__(self, category_repository: ICategoryRepository):
        self.category_repository = category_repository

    async def execute(self, include_system: bool = True) -> List[CategoryResponseDTO]:
        categories = await self.category_repository.get_all(include_system=include_system)
        return [
            CategoryResponseDTO(
                id=c.id,
                name=c.name,
                slug=c.slug,
                is_system=c.is_system,
                icon=c.icon,
                color=c.color
            )
            for c in categories
        ]
