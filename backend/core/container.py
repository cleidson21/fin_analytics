from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies.database import get_db_session
from backend.application.use_cases.authenticate_user import AuthenticateUserUseCase
from backend.core.config import settings
from backend.infrastructure.bootstrap.bootstrap_admin import BootstrapAdmin

from backend.application.ports.i_user_repository import IUserRepository
from backend.application.ports.account_repository import IAccountRepository
from backend.application.ports.institution_repository import IInstitutionRepository
from backend.application.ports.transaction_repository import ITransactionRepository
from backend.application.ports.category_repository import ICategoryRepository
from backend.application.ports.pierre_provider import IPierreProvider
from backend.application.ports.i_password_hasher import IPasswordHasher
from backend.application.ports.i_jwt_service import IJWTService

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
from backend.infrastructure.http.pierre_client import PierreClient
from backend.application.services.pierre_import_service import PierreImportService

def get_password_hasher() -> IPasswordHasher:
    """Retorna uma instância concreta de IPasswordHasher."""
    return PasswordHasher()


def get_jwt_service() -> IJWTService:
    """Retorna uma instância concreta de IJWTService configurada."""
    refresh_expire = getattr(settings, "JWT_REFRESH_EXPIRE_DAYS", 7)
    return JWTService(
        secret=settings.JWT_SECRET,
        expire_minutes=settings.JWT_EXPIRE_MINUTES,
        refresh_expire_days=refresh_expire
    )


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> IUserRepository:
    """Retorna a implementação concreta de IUserRepository."""
    return SQLAlchemyUserRepository(session=session)


def get_account_repository(session: AsyncSession = Depends(get_db_session)) -> IAccountRepository:
    """Retorna a implementação concreta de IAccountRepository."""
    return SQLAlchemyAccountRepository(session=session)


def get_institution_repository(session: AsyncSession = Depends(get_db_session)) -> IInstitutionRepository:
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
    account_repo: IAccountRepository = Depends(get_account_repository),
    institution_repo: IInstitutionRepository = Depends(get_institution_repository)
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

def get_transaction_repository(session: AsyncSession = Depends(get_db_session)) -> ITransactionRepository:
    return SQLAlchemyTransactionRepository(session=session)

def get_category_repository(session: AsyncSession = Depends(get_db_session)) -> ICategoryRepository:
    return SQLAlchemyCategoryRepository(session=session)

def get_transactions_use_case(
    tx_repo: ITransactionRepository = Depends(get_transaction_repository),
    cat_repo: ICategoryRepository = Depends(get_category_repository),
    account_repo: IAccountRepository = Depends(get_account_repository)
) -> GetTransactionsUseCase:
    return GetTransactionsUseCase(transaction_repo=tx_repo, category_repo=cat_repo, account_repo=account_repo)

def get_transaction_details_use_case(
    tx_repo: ITransactionRepository = Depends(get_transaction_repository),
    cat_repo: ICategoryRepository = Depends(get_category_repository),
    account_repo: IAccountRepository = Depends(get_account_repository)
) -> GetTransactionDetailsUseCase:
    return GetTransactionDetailsUseCase(transaction_repo=tx_repo, category_repo=cat_repo, account_repo=account_repo)

def get_categories_summary_use_case(
    tx_repo: ITransactionRepository = Depends(get_transaction_repository)
) -> GetCategoriesSummaryUseCase:
    return GetCategoriesSummaryUseCase(transaction_repo=tx_repo)

def get_update_transaction_category_use_case(
    tx_repo: ITransactionRepository = Depends(get_transaction_repository),
    cat_repo: ICategoryRepository = Depends(get_category_repository)
) -> UpdateTransactionCategoryUseCase:
    return UpdateTransactionCategoryUseCase(transaction_repo=tx_repo, category_repo=cat_repo)

def get_dashboard_summary_v2_use_case(
    tx_repo: ITransactionRepository = Depends(get_transaction_repository)
) -> GetDashboardSummaryV2UseCase:
    return GetDashboardSummaryV2UseCase(transaction_repo=tx_repo)

def get_get_categories_use_case(
    category_repo: ICategoryRepository = Depends(get_category_repository)
) -> GetCategoriesUseCase:
    return GetCategoriesUseCase(category_repository=category_repo)


from backend.application.ports.sync_log_repository import ISyncLogRepository
from backend.infrastructure.persistence.repositories.sync_log_repository import SQLAlchemySyncLogRepository

def get_sync_log_repository(session: AsyncSession = Depends(get_db_session)) -> ISyncLogRepository:
    return SQLAlchemySyncLogRepository(session=session)

from backend.application.use_cases.get_sync_logs import GetSyncLogsUseCase
from backend.application.use_cases.get_installments import GetInstallmentsUseCase
from backend.application.use_cases.get_subscriptions import GetSubscriptionsUseCase

def get_sync_logs_use_case(
    sync_log_repo: ISyncLogRepository = Depends(get_sync_log_repository)
) -> GetSyncLogsUseCase:
    return GetSyncLogsUseCase(sync_log_repo=sync_log_repo)

def get_installments_use_case(
    session: AsyncSession = Depends(get_db_session)
) -> GetInstallmentsUseCase:
    return GetInstallmentsUseCase(session=session)

def get_subscriptions_use_case(
    session: AsyncSession = Depends(get_db_session)
) -> GetSubscriptionsUseCase:
    return GetSubscriptionsUseCase(session=session)

# ------------------------------------------------------------------ #
#  Pierre Integration
# ------------------------------------------------------------------ #

def get_pierre_client() -> IPierreProvider:
    """Retorna uma instância não-inicializada do PierreClient."""
    return PierreClient()

from backend.application.services.pierre_legacy_tx_adapter import PierreLegacyTransactionAdapter
from backend.application.services.pierre_legacy_acc_adapter import PierreLegacyAccountAdapter
from backend.application.services.pierre_legacy_cat_adapter import PierreLegacyCategoryAdapter

def get_pierre_legacy_transaction_adapter() -> ITransactionRepository:
    return PierreLegacyTransactionAdapter()

def get_pierre_legacy_account_adapter() -> IAccountRepository:
    return PierreLegacyAccountAdapter()

def get_pierre_legacy_category_adapter():
    return PierreLegacyCategoryAdapter()

def get_pierre_import_service(
    transaction_repo: ITransactionRepository = Depends(get_pierre_legacy_transaction_adapter),
    account_repo: IAccountRepository = Depends(get_pierre_legacy_account_adapter),
    category_repo = Depends(get_pierre_legacy_category_adapter),
    sync_log_repo: ISyncLogRepository = Depends(get_sync_log_repository),
) -> PierreImportService:
    """Constrói o PierreImportService com suas dependências injetadas."""
    client = get_pierre_client()
    return PierreImportService(
        pierre_provider=client,
        transaction_repo=transaction_repo,
        account_repo=account_repo,
        category_repo=category_repo,
        sync_log_repo=sync_log_repo,
    )
