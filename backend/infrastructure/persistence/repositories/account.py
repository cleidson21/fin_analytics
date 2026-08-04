from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.domain.entities.account import Account
from backend.domain.enums.account_type import AccountType
from backend.domain.enums.currency_code import CurrencyCode
from backend.domain.enums.provider_type import ProviderType
from backend.application.queries.get_accounts import GetAccountsQuery
from backend.application.ports.account_repository import IAccountRepository
from backend.infrastructure.persistence.models.account import AccountModel

class SQLAlchemyAccountRepository(IAccountRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: AccountModel) -> Account:
        return Account(
            id=UUID(model.id),
            user_id=UUID(model.user_id),
            external_id=model.external_id,
            provider=ProviderType(model.provider),
            institution_id=UUID(model.institution_id) if model.institution_id else None,
            name=model.name,
            type=AccountType(model.type),
            subtype=model.subtype,
            currency_code=CurrencyCode(model.currency_code),
            balance=Decimal(model.balance) if model.balance is not None else None,
            balance_updated_at=model.balance_updated_at,
            is_active=model.is_active,
            provider_code=model.provider_code,
            provider_metadata=model.provider_metadata,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: Account) -> AccountModel:
        return AccountModel(
            id=str(entity.id),
            user_id=str(entity.user_id),
            external_id=entity.external_id,
            provider=entity.provider.value,
            institution_id=str(entity.institution_id) if entity.institution_id else None,
            name=entity.name,
            type=entity.type.value,
            subtype=entity.subtype,
            currency_code=entity.currency_code.value,
            balance=entity.balance,
            balance_updated_at=entity.balance_updated_at,
            is_active=entity.is_active,
            provider_code=entity.provider_code,
            provider_metadata=entity.provider_metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    async def create(self, account: Account) -> Account:
        model = self._to_model(account)
        self.session.add(model)
        await self.session.flush()
        return account

    async def get_by_id(self, id: UUID) -> Optional[Account]:
        stmt = select(AccountModel).where(AccountModel.id == str(id))
        result = await self.session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_external_id(self, external_id: str, provider: ProviderType) -> Optional[Account]:
        stmt = select(AccountModel).where(AccountModel.external_id == external_id, AccountModel.provider == provider.value)
        result = await self.session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        return self._to_entity(model)

    async def list(self, user_id: UUID, filters: GetAccountsQuery) -> List[Account]:
        stmt = select(AccountModel).where(AccountModel.user_id == str(user_id))
        
        if filters.type is not None:
            stmt = stmt.where(AccountModel.type == filters.type.value)
        if filters.is_active is not None:
            stmt = stmt.where(AccountModel.is_active == filters.is_active)
        if filters.provider is not None:
            stmt = stmt.where(AccountModel.provider == filters.provider.value)
            
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def update_balance(self, id: UUID, balance: Decimal, updated_at: datetime) -> Account:
        stmt = select(AccountModel).where(AccountModel.id == str(id))
        result = await self.session.execute(stmt)
        model = result.scalars().first()
        if model:
            model.balance = balance
            model.balance_updated_at = updated_at
            await self.session.flush()
            return self._to_entity(model)
        raise Exception("Account not found")

    async def upsert(self, account: Account) -> Account:
        existing = None
        if account.external_id:
            existing = await self.get_by_external_id(account.external_id, account.provider)
        else:
            existing = await self.get_by_id(account.id)
            
        if existing:
            # Simple update approach for now (assumes Unit of Work commits)
            stmt = select(AccountModel).where(AccountModel.id == str(existing.id))
            result = await self.session.execute(stmt)
            model = result.scalars().first()
            if model:
                model.name = account.name
                model.balance = account.balance
                model.balance_updated_at = account.balance_updated_at
                model.is_active = account.is_active
                await self.session.flush()
                return self._to_entity(model)
        
        return await self.create(account)
