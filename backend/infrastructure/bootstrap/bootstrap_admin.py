import uuid
from datetime import datetime
from typing import TYPE_CHECKING
import bcrypt

from backend.domain.entities.user import User
from backend.domain.enums.user_role import UserRole

if TYPE_CHECKING:
    from backend.application.ports.i_user_repository import IUserRepository


class BootstrapAdmin:
    """
    Serviço de inicialização para garantir a existência do usuário Admin
    no sistema Single User (conforme ADR-010).
    """

    def __init__(self, user_repository: "IUserRepository") -> None:
        self._user_repository = user_repository

    async def execute(self) -> None:
        """
        Executa o bootstrap. Verifica se o usuário admin existe e cria se necessário.
        É idempotente: executá-lo várias vezes não duplicará o usuário.
        """
        admin_email = "admin"
        
        existing_user = await self._user_repository.get_by_email(admin_email)
        if existing_user is not None:
            return  # Idempotente: usuário já existe

        # Gera hash bcrypt para a senha padrão 'admin'
        hashed_password = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("utf-8")
        
        admin_user = User(
            id=uuid.uuid4(),
            email=admin_email,
            name="Administrator",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            role=UserRole.ADMIN,
            created_at=datetime.utcnow(),
            last_login_at=None,
        )

        await self._user_repository.create(admin_user)
