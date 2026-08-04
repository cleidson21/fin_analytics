import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from backend.domain.enums.user_role import UserRole


@dataclass(frozen=True)
class UserResponseDTO:
    """
    DTO para retorno de dados do usuário (nunca expõe hash de senha).
    """
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
