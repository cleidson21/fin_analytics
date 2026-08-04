from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.domain.entities.institution import Institution
from backend.application.ports.institution_repository import IInstitutionRepository
from backend.infrastructure.persistence.models.institution import InstitutionModel

class SQLAlchemyInstitutionRepository(IInstitutionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: InstitutionModel) -> Institution:
        return Institution(
            id=UUID(model.id),
            name=model.name,
            code=model.code,
            type=model.type,
            country=model.country,
            logo_url=model.logo_url,
            created_at=model.created_at
        )

    async def get_by_code(self, code: str) -> Optional[Institution]:
        stmt = select(InstitutionModel).where(InstitutionModel.code == code)
        result = await self.session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        return self._to_entity(model)

    async def get_or_create(self, code: str, name: str) -> Institution:
        existing = await self.get_by_code(code)
        if existing:
            return existing
            
        import uuid
        model = InstitutionModel(
            id=str(uuid.uuid4()),
            code=code,
            name=name,
            country="BR"
        )
        self.session.add(model)
        # Flush is needed so that the model gets created and can be returned
        await self.session.flush()
        return self._to_entity(model)

    async def list(self) -> List[Institution]:
        stmt = select(InstitutionModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
