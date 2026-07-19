import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.ports.i_user_repository import IUserRepository
from backend.domain.entities.user import User
from backend.infrastructure.persistence.mappers.user_mapper import UserMapper
from backend.infrastructure.persistence.models.user import UserModel


class SQLAlchemyUserRepository(IUserRepository):
    """
    Implementação concreta do IUserRepository usando SQLAlchemy 2.x e AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> User:
        user_model = UserMapper.to_orm(user)
        self._session.add(user_model)
        return user

    async def get_by_id(self, id: uuid.UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def update(self, user: User) -> User:
        user_model = UserMapper.to_orm(user)
        await self._session.merge(user_model)
        return user

    async def update_last_login(self, id: uuid.UUID, at: datetime) -> None:
        stmt = update(UserModel).where(UserModel.id == id).values(last_login_at=at)
        await self._session.execute(stmt)
