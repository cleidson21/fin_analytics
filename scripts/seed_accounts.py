import asyncio
import os
import sys

# Add backend to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.future import select
from decimal import Decimal
import uuid
from datetime import datetime

from backend.database.session import AsyncSessionLocal
from backend.infrastructure.persistence.models.user import UserModel
from backend.domain.entities.institution import Institution
from backend.domain.entities.account import Account
from backend.domain.enums.account_type import AccountType
from backend.domain.enums.currency_code import CurrencyCode
from backend.domain.enums.provider_type import ProviderType
from backend.infrastructure.persistence.repositories.institution import SQLAlchemyInstitutionRepository
from backend.infrastructure.persistence.repositories.account import SQLAlchemyAccountRepository
from backend.application.queries.get_accounts import GetAccountsQuery

async def seed_accounts():
    # Schema creation is an explicit Alembic operation. This utility only seeds
    # a database that has already been migrated.
    async with AsyncSessionLocal() as session:
        # Bootstrap admin if needed
        from backend.core.container import get_bootstrap_admin
        await get_bootstrap_admin(session).execute()
        await session.commit()
        
        # Get admin user
        stmt = select(UserModel).where(UserModel.email == "admin")
        result = await session.execute(stmt)
        admin = result.scalars().first()
        
        if not admin:
            print("Admin user not found! Please run backend to bootstrap first.")
            return

        inst_repo = SQLAlchemyInstitutionRepository(session)
        acc_repo = SQLAlchemyAccountRepository(session)

        # Create Institution
        nubank = await inst_repo.get_or_create(code="NUBANK", name="Nubank")
        itau = await inst_repo.get_or_create(code="ITAU", name="Banco Itaú")
        
        # Create Accounts
        # Check if already exists
        admin_id_uuid = admin.id if isinstance(admin.id, uuid.UUID) else uuid.UUID(str(admin.id))
        
        query = GetAccountsQuery(user_id=admin_id_uuid)
        accounts = await acc_repo.list(query.user_id, query)
        
        if accounts:
            print(f"User already has {len(accounts)} accounts.")
            return

        acc1 = Account(
            id=uuid.uuid4(),
            user_id=admin_id_uuid,
            external_id="acc_nubank_123",
            provider=ProviderType.PIERRE,
            institution_id=nubank.id,
            name="Conta Corrente Nubank",
            type=AccountType.BANK,
            subtype="CHECKING_ACCOUNT",
            currency_code=CurrencyCode.BRL,
            balance=Decimal("1542.50"),
            balance_updated_at=datetime.utcnow(),
            is_active=True,
            provider_code="NUBANK",
            provider_metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        acc2 = Account(
            id=uuid.uuid4(),
            user_id=admin_id_uuid,
            external_id="acc_itau_456",
            provider=ProviderType.PIERRE,
            institution_id=itau.id,
            name="Cartão de Crédito Itaú",
            type=AccountType.CREDIT_CARD,
            subtype="CREDIT_CARD",
            currency_code=CurrencyCode.BRL,
            balance=Decimal("-840.20"),
            balance_updated_at=datetime.utcnow(),
            is_active=True,
            provider_code="ITAU",
            provider_metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await acc_repo.create(acc1)
        await acc_repo.create(acc2)
        
        await session.commit()
        print("Successfully seeded 2 accounts for admin user.")

if __name__ == "__main__":
    asyncio.run(seed_accounts())
