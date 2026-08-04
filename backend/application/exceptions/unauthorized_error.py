from backend.application.exceptions.application_error import ApplicationError


class UnauthorizedError(ApplicationError):
    """
    Exceção base para erros de autorização e autenticação.
    """
    pass
