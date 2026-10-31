import asyncio
import uuid
from decimal import Decimal
from datetime import date, datetime

from backend.core.config import settings
from backend.database.disposable import disposable_script_async_session
from backend.domain.entities.category import Category
from backend.domain.entities.transaction import Transaction
from backend.infrastructure.persistence.repositories.category_repository import SQLAlchemyCategoryRepository
from backend.infrastructure.persistence.repositories.transaction_repository import SQLAlchemyTransactionRepository
from backend.infrastructure.persistence.repositories.account import SQLAlchemyAccountRepository
from backend.domain.entities.account import Account
from backend.domain.enums.account_type import AccountType
from backend.domain.enums.provider_type import ProviderType
from backend.domain.enums.currency_code import CurrencyCode
from backend.infrastructure.persistence.repositories.user_repository import SQLAlchemyUserRepository

# UUIDs for the current month
current_year = date.today().year
current_month = date.today().month

async def seed():
    async with disposable_script_async_session(settings.DATABASE_URL) as session:
        cat_repo = SQLAlchemyCategoryRepository(session)
        tx_repo = SQLAlchemyTransactionRepository(session)
        
        # 1. Create categories
        categories = [
            Category(name="Alimentação", slug="alimentacao", is_system=True),
            Category(name="Transporte", slug="transporte", is_system=True),
            Category(name="Saúde", slug="saude", is_system=True),
            Category(name="Lazer", slug="lazer", is_system=True),
            Category(name="Moradia", slug="moradia", is_system=True),
            Category(name="Salário", slug="salario", is_system=True),
            Category(name="Transferências", slug="transferencias", is_system=True),
        ]
        
        cat_ids = {}
        for c in categories:
            saved = await cat_repo.save(c)
            cat_ids[c.name] = saved.id
            
        user_repo = SQLAlchemyUserRepository(session)
        admin_user = await user_repo.get_by_email("admin")
        
        if not admin_user:
            print("Admin user not found. Please run the backend to bootstrap it first.")
            return
            
        user_id = admin_user.id
        
        # 2. Create Account
        acc_repo = SQLAlchemyAccountRepository(session)
        account = Account(
            id=uuid.uuid4(),
            user_id=user_id,
            external_id="acc_seed",
            provider=ProviderType.MANUAL,
            institution_id=None,
            name="Conta Principal",
            type=AccountType.BANK,
            subtype=None,
            currency_code=CurrencyCode.BRL,
            balance=Decimal("15000.00"),
            balance_updated_at=None,
            is_active=True,
            provider_code=None,
            provider_metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        saved_account = await acc_repo.create(account)
        account_id = saved_account.id
        
        # 3. Create transactions
        transactions = [
            Transaction(
                user_id=user_id,
                provider="seed",
                account_id=account_id,
                amount=Decimal("5000.00"),
                direction="CREDIT",
                currency_code="BRL",
                description="Salário",
                type="DEPOSIT",
                status="CONFIRMED",
                transaction_date=date(current_year, current_month, 5),
                is_recurring=True,
                hash=str(uuid.uuid4()),
                category_id=cat_ids["Salário"]
            ),
            Transaction(
                user_id=user_id,
                provider="seed",
                account_id=account_id,
                amount=Decimal("150.00"),
                direction="DEBIT",
                currency_code="BRL",
                description="Mercado",
                type="PURCHASE",
                status="CONFIRMED",
                transaction_date=date(current_year, current_month, 10),
                is_recurring=False,
                hash=str(uuid.uuid4()),
                category_id=cat_ids["Alimentação"]
            ),
            Transaction(
                user_id=user_id,
                provider="seed",
                account_id=account_id,
                amount=Decimal("80.00"),
                direction="DEBIT",
                currency_code="BRL",
                description="Uber",
                type="PURCHASE",
                status="CONFIRMED",
                transaction_date=date(current_year, current_month, 12),
                is_recurring=False,
                hash=str(uuid.uuid4()),
                category_id=cat_ids["Transporte"]
            ),
            Transaction(
                user_id=user_id,
                provider="seed",
                account_id=account_id,
                amount=Decimal("200.00"),
                direction="DEBIT",
                currency_code="BRL",
                description="Farmácia",
                type="PURCHASE",
                status="CONFIRMED",
                transaction_date=date(current_year, current_month, 15),
                is_recurring=False,
                hash=str(uuid.uuid4()),
                category_id=cat_ids["Saúde"]
            ),
            Transaction(
                user_id=user_id,
                provider="seed",
                account_id=account_id,
                amount=Decimal("45.90"),
                direction="DEBIT",
                currency_code="BRL",
                description="Netflix",
                type="PURCHASE",
                status="CONFIRMED",
                transaction_date=date(current_year, current_month, 20),
                is_recurring=True,
                hash=str(uuid.uuid4()),
                category_id=cat_ids["Lazer"]
            ),
            Transaction(
                user_id=user_id,
                provider="seed",
                account_id=account_id,
                amount=Decimal("1000.00"),
                direction="DEBIT",
                currency_code="BRL",
                description="Aluguel",
                type="PURCHASE",
                status="CONFIRMED",
                transaction_date=date(current_year, current_month, 5),
                is_recurring=True,
                hash=str(uuid.uuid4()),
                category_id=cat_ids["Moradia"]
            ),
            Transaction(
                user_id=user_id,
                provider="seed",
                account_id=account_id,
                amount=Decimal("500.00"),
                direction="DEBIT",
                currency_code="BRL",
                description="PIX Transferência",
                type="TRANSFER",
                status="CONFIRMED",
                transaction_date=date(current_year, current_month, 22),
                is_recurring=False,
                hash=str(uuid.uuid4()),
                category_id=cat_ids["Transferências"]
            ),
            # Parcelada
            Transaction(
                user_id=user_id,
                provider="seed",
                account_id=account_id,
                amount=Decimal("100.00"),
                direction="DEBIT",
                currency_code="BRL",
                description="Geladeira (1/10)",
                type="PURCHASE",
                status="CONFIRMED",
                transaction_date=date(current_year, current_month, 1),
                is_recurring=False,
                hash=str(uuid.uuid4()),
                category_id=cat_ids["Moradia"],
                installment_count=10,
                installment_current=1
            ),
        ]
        
        for tx in transactions:
            await tx_repo.save(tx)
            
        await session.commit()
        print("Seed finalizado com sucesso!")

if __name__ == "__main__":
    asyncio.run(seed())
