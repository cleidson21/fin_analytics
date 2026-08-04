from dataclasses import dataclass

from backend.application.dtos.user_response_dto import UserResponseDTO


@dataclass(frozen=True)
class AuthTokenDTO:
    """
    DTO para retorno de tokens de autenticação.
    """
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponseDTO
