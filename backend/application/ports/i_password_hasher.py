from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    """
    Port (interface) para o serviço de criptografia de senhas.
    Definido pela camada Application. Implementado pela Infrastructure.
    """

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """
        Gera o hash de uma senha em texto plano.

        Args:
            password: Senha em texto plano.

        Returns:
            String contendo o hash criptografado.
        """
        ...

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica se a senha plana corresponde ao hash armazenado.

        Args:
            plain_password: Senha em texto plano (digitada no login).
            hashed_password: Hash seguro armazenado no banco.

        Returns:
            True se a senha for válida, False caso contrário.
        """
        ...
