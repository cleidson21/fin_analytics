from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticateUserCommand:
    """
    Command com a intenção de autenticar um usuário no sistema.
    Imutável, contendo apenas dados.
    """
    email: str
    password: str
