from abc import ABC, abstractmethod
from typing import Any, Dict


class IJWTService(ABC):
    """
    Port (interface) para o serviço de criação e validação de tokens JWT.
    Definido pela camada Application. Implementado pela Infrastructure.
    """

    @abstractmethod
    def create_access_token(self, user_id: str) -> str:
        """
        Gera um JWT access_token de curta duração.

        Args:
            user_id: ID do usuário (geralmente convertido em string).

        Returns:
            String contendo o token JWT codificado e assinado.
        """
        ...

    @abstractmethod
    def create_refresh_token(self, user_id: str) -> str:
        """
        Gera um JWT refresh_token de longa duração.

        Args:
            user_id: ID do usuário (geralmente convertido em string).

        Returns:
            String contendo o token JWT codificado e assinado.
        """
        ...

    @abstractmethod
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decodifica o token sem validar a assinatura.
        Útil para ler o JTI ou claims antes da validação estrita.

        Args:
            token: String do token JWT.

        Returns:
            Dicionário com as claims contidas no token.
        """
        ...

    @abstractmethod
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica a assinatura e expiração do token e retorna as claims.

        Args:
            token: String do token JWT.

        Returns:
            Dicionário com as claims validadas.

        Raises:
            ValueError: Caso o token seja inválido ou expirado.
        """
        ...
