from backend.application.exceptions.application_error import ApplicationError


class UnsupportedSmartContextFeatureError(ApplicationError):
    """The caller requested a feature outside the locked Smart Context enum."""
