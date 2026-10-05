from backend.application.exceptions.application_error import ApplicationError


class SmartContextOwnershipUnavailableError(ApplicationError):
    """The authenticated user cannot be mapped to the local single-user scope."""


class SmartContextOwnershipInconsistentError(ApplicationError):
    """Persisted user identity violates the Smart Context ownership invariant."""
