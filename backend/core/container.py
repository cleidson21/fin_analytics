from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies.database import get_db_session
from backend.application.use_cases.authenticate_user import AuthenticateUserUseCase
from backend.core.config import settings
from backend.infrastructure.bootstrap.bootstrap_admin import BootstrapAdmin
from backend.infrastructure.persistence.repositories.user_repository import SQLAlchemyUserRepository
from backend.infrastructure.persistence.repositories.account import SQLAlchemyAccountRepository
from backend.infrastructure.persistence.repositories.institution import SQLAlchemyInstitutionRepository
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.password_hasher import PasswordHasher
from backend.application.use_cases.get_accounts import GetAccountsUseCase
from backend.infrastructure.persistence.repositories.transaction_repository import SQLAlchemyTransactionRepository
from backend.infrastructure.persistence.repositories.category_repository import SQLAlchemyCategoryRepository
from backend.application.use_cases.transactions import (
    GetTransactionsUseCase,
    GetCategoriesSummaryUseCase,
    UpdateTransactionCategoryUseCase,
    GetDashboardSummaryV2UseCase,
    GetTransactionDetailsUseCase,
)
from backend.application.use_cases.get_categories import GetCategoriesUseCase

def get_password_hasher() -> PasswordHasher:
    """Retorna uma instância concreta de IPasswordHasher."""
    return PasswordHasher()


def get_jwt_service() -> JWTService:
    """Retorna uma instância concreta de IJWTService configurada."""
    refresh_expire = getattr(settings, "JWT_REFRESH_EXPIRE_DAYS", 7)
    return JWTService(
        secret=settings.JWT_SECRET,
        expire_minutes=settings.JWT_EXPIRE_MINUTES,
        refresh_expire_days=refresh_expire
    )


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyUserRepository:
    """Retorna a implementação concreta de IUserRepository."""
    return SQLAlchemyUserRepository(session=session)


def get_account_repository(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyAccountRepository:
    """Retorna a implementação concreta de IAccountRepository."""
    return SQLAlchemyAccountRepository(session=session)


def get_institution_repository(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyInstitutionRepository:
    """Retorna a implementação concreta de IInstitutionRepository."""
    return SQLAlchemyInstitutionRepository(session=session)


def get_authenticate_user_use_case(session: AsyncSession = Depends(get_db_session)) -> AuthenticateUserUseCase:
    """Constrói e retorna o AuthenticateUserUseCase (Composition Root)."""
    return AuthenticateUserUseCase(
        user_repository=get_user_repository(session),
        password_hasher=get_password_hasher(),
        jwt_service=get_jwt_service(),
    )


def get_get_accounts_use_case(
    account_repo: SQLAlchemyAccountRepository = Depends(get_account_repository),
    institution_repo: SQLAlchemyInstitutionRepository = Depends(get_institution_repository)
) -> GetAccountsUseCase:
    """Constrói e retorna o GetAccountsUseCase."""
    return GetAccountsUseCase(
        account_repository=account_repo,
        institution_repository=institution_repo
    )


def get_bootstrap_admin(session: AsyncSession) -> BootstrapAdmin:
    """Constrói o serviço de inicialização do sistema."""
    return BootstrapAdmin(
        user_repository=SQLAlchemyUserRepository(session=session)
    )

def get_transaction_repository(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyTransactionRepository:
    return SQLAlchemyTransactionRepository(session=session)

def get_category_repository(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyCategoryRepository:
    return SQLAlchemyCategoryRepository(session=session)

def get_transactions_use_case(
    tx_repo: SQLAlchemyTransactionRepository = Depends(get_transaction_repository),
    cat_repo: SQLAlchemyCategoryRepository = Depends(get_category_repository),
    account_repo: SQLAlchemyAccountRepository = Depends(get_account_repository)
) -> GetTransactionsUseCase:
    return GetTransactionsUseCase(transaction_repo=tx_repo, category_repo=cat_repo, account_repo=account_repo)

def get_transaction_details_use_case(
    tx_repo: SQLAlchemyTransactionRepository = Depends(get_transaction_repository),
    cat_repo: SQLAlchemyCategoryRepository = Depends(get_category_repository),
    account_repo: SQLAlchemyAccountRepository = Depends(get_account_repository)
) -> GetTransactionDetailsUseCase:
    return GetTransactionDetailsUseCase(transaction_repo=tx_repo, category_repo=cat_repo, account_repo=account_repo)

def get_categories_summary_use_case(
    tx_repo: SQLAlchemyTransactionRepository = Depends(get_transaction_repository)
) -> GetCategoriesSummaryUseCase:
    return GetCategoriesSummaryUseCase(transaction_repo=tx_repo)

def get_update_transaction_category_use_case(
    tx_repo: SQLAlchemyTransactionRepository = Depends(get_transaction_repository),
    cat_repo: SQLAlchemyCategoryRepository = Depends(get_category_repository)
) -> UpdateTransactionCategoryUseCase:
    return UpdateTransactionCategoryUseCase(transaction_repo=tx_repo, category_repo=cat_repo)

def get_dashboard_summary_v2_use_case(
    tx_repo: SQLAlchemyTransactionRepository = Depends(get_transaction_repository)
) -> GetDashboardSummaryV2UseCase:
    return GetDashboardSummaryV2UseCase(transaction_repo=tx_repo)

def get_get_categories_use_case(
    category_repo: SQLAlchemyCategoryRepository = Depends(get_category_repository)
) -> GetCategoriesUseCase:
    return GetCategoriesUseCase(category_repository=category_repo)
