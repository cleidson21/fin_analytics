from backend.application.exceptions.unauthorized_error import UnauthorizedError


class InvalidCredentialsError(UnauthorizedError):
    """
    Exceção lançada quando as credenciais fornecidas no login são inválidas
    (senha incorreta ou email não correspondente ao admin único).
    Corresponde ao código AUTH_INVALID_CREDENTIALS.
    """
    def __init__(self, message: str = "Email ou senha inválidos.") -> None:
        super().__init__(message)
