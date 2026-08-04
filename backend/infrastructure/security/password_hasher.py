import bcrypt

from backend.application.ports.i_password_hasher import IPasswordHasher


class PasswordHasher(IPasswordHasher):
    """
    Serviço de infraestrutura para criptografia de senhas usando bcrypt.
    Totalmente independente de Frameworks, Domain e Banco de dados.
    """

    def hash_password(self, password: str) -> str:
        """
        Gera o hash de uma senha em texto plano.
        """
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica se a senha plana corresponde ao hash armazenado.
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
