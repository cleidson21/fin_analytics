from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from backend.domain.entities.user import User


class IUserRepository(ABC):
    """
    Port (interface) do repositório de usuários.
    Definido pela camada Application. Implementado pela Infrastructure.
    Nunca depende de SQLAlchemy, FastAPI, Pydantic ou qualquer infraestrutura.
    """

    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Persiste um novo usuário.

        Args:
            user: Entidade User já construída, com id e hashed_password.

        Returns:
            O mesmo User após persistência.
        """
        ...

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> User | None:
        """
        Busca usuário pelo identificador interno.

        Args:
            id: UUID interno do usuário.

        Returns:
            User encontrado ou None.
        """
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """
        Busca usuário pelo e-mail (chave externa única).

        Args:
            email: Endereço de e-mail do usuário.

        Returns:
            User encontrado ou None.
        """
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Atualiza campos mutáveis do usuário (name, hashed_password, role, is_active).

        Args:
            user: Entidade User com os campos atualizados.

        Returns:
            User após persistência.
        """
        ...

    @abstractmethod
    async def update_last_login(self, id: uuid.UUID, at: datetime) -> None:
        """
        Registra o timestamp do último login do usuário.

        Args:
            id: UUID interno do usuário.
            at: Datetime do login (fornecido pelo IClock).
        """
        ...
