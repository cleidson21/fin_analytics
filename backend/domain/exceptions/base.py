class FINAnalyticsError(Exception):
    """
    Exceção base para todo o projeto FIN Analytics.
    Todas as exceções customizadas devem herdar desta.
    """
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
