from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.category import Category
from backend.infrastructure.persistence.models.category import CategoryModel

class SQLAlchemyCategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        stmt = select(CategoryModel).where(CategoryModel.id == category_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_all(self, include_system: bool = True) -> List[Category]:
        stmt = select(CategoryModel)
        if not include_system:
            stmt = stmt.where(CategoryModel.is_system == False)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, category: Category) -> Category:
        model = CategoryModel(
            id=category.id,
            name=category.name,
            slug=category.slug,
            is_system=category.is_system,
            parent_id=category.parent_id,
            icon=category.icon,
            color=category.color,
            created_at=category.created_at,
        )
        self.session.add(model)
        await self.session.flush()
        return category

    def _to_entity(self, model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            name=model.name,
            slug=model.slug,
            is_system=model.is_system,
            parent_id=model.parent_id,
            icon=model.icon,
            color=model.color,
            created_at=model.created_at,
        )
