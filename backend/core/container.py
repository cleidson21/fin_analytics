from backend.application.use_cases.authenticate_user import AuthenticateUserUseCase
from backend.core.config import settings
from backend.infrastructure.bootstrap.bootstrap_admin import BootstrapAdmin
from backend.infrastructure.persistence.repositories.user_repository import SQLAlchemyUserRepository
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.password_hasher import PasswordHasher


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


def get_user_repository(session) -> SQLAlchemyUserRepository:
    """Retorna a implementação concreta de IUserRepository."""
    return SQLAlchemyUserRepository(session=session)


def get_authenticate_user_use_case(session) -> AuthenticateUserUseCase:
    """Constrói e retorna o AuthenticateUserUseCase (Composition Root)."""
    return AuthenticateUserUseCase(
        user_repository=get_user_repository(session),
        password_hasher=get_password_hasher(),
        jwt_service=get_jwt_service(),
    )


def get_bootstrap_admin(session) -> BootstrapAdmin:
    """Constrói o serviço de inicialização do sistema."""
    return BootstrapAdmin(
        user_repository=get_user_repository(session)
    )
