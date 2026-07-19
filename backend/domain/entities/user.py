from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from backend.domain.enums.user_role import UserRole


@dataclass
class User:
    """
    Representa o usuário autenticado no sistema.
    """
    id: uuid.UUID
    email: str
    name: str
    hashed_password: str
    is_active: bool
    is_verified: bool
    role: UserRole
    created_at: datetime
    last_login_at: datetime | None = None
