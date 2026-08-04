from datetime import datetime

from backend.application.commands.authenticate_user_command import AuthenticateUserCommand
from backend.application.dtos.auth_token_dto import AuthTokenDTO
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.exceptions.invalid_credentials_error import InvalidCredentialsError
from backend.application.exceptions.unauthorized_error import UnauthorizedError
from backend.application.exceptions.user_not_found_error import UserNotFoundError
from backend.application.ports.i_jwt_service import IJWTService
from backend.application.ports.i_password_hasher import IPasswordHasher
from backend.application.ports.i_user_repository import IUserRepository


class AuthenticateUserUseCase:
    """
    Caso de Uso: Autenticar Usuário (UC-01).
    Responsável por validar as credenciais e gerar os tokens de acesso.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
        jwt_service: IJWTService,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._jwt_service = jwt_service

    async def execute(self, command: AuthenticateUserCommand) -> AuthTokenDTO:
        # Buscar usuário pelo email
        user = await self._user_repository.get_by_email(command.email)
        if not user:
            raise UserNotFoundError()

        # Verificar se o usuário está ativo
        if not user.is_active or not user.is_verified:
            raise UnauthorizedError("Usuário inativo ou não verificado.")

        # Validar senha utilizando IPasswordHasher
        is_password_valid = self._password_hasher.verify_password(
            plain_password=command.password,
            hashed_password=user.hashed_password
        )
        if not is_password_valid:
            raise InvalidCredentialsError()

        # Atualizar last_login através do IUserRepository
        now = datetime.utcnow()
        await self._user_repository.update_last_login(id=user.id, at=now)

        # Gerar Access Token utilizando IJWTService
        access_token = self._jwt_service.create_access_token(user_id=str(user.id))

        # Gerar Refresh Token
        refresh_token = self._jwt_service.create_refresh_token(user_id=str(user.id))

        # Decodificar token apenas para extrair a validade exata (exp - iat)
        decoded = self._jwt_service.decode_token(access_token)
        expires_in = int(decoded["exp"]) - int(decoded["iat"])

        # Montar UserResponseDTO
        user_response = UserResponseDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login_at=now
        )

        # Montar AuthTokenDTO
        return AuthTokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_response
        )
