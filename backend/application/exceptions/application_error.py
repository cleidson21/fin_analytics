from backend.domain.exceptions.base import FINAnalyticsError


class ApplicationError(FINAnalyticsError):
    """
    Exceção base para erros na camada Application.
    """
    pass
