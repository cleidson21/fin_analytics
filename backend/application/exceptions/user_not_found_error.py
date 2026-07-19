from backend.application.exceptions.application_error import ApplicationError


class UserNotFoundError(ApplicationError):
    """
    Exceção lançada quando o usuário solicitado não existe no sistema.
    Corresponde ao código USER_NOT_FOUND.
    """
    def __init__(self, message: str = "Usuário não encontrado.") -> None:
        super().__init__(message)
