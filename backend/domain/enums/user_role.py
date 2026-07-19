from enum import Enum


class UserRole(str, Enum):
    """
    Papel do usuário no sistema.
    ADMIN: Acesso total
    VIEWER: Somente leitura
    """
    ADMIN = "ADMIN"
    VIEWER = "VIEWER"
