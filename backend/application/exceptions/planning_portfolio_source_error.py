"""Application errors for ADR-023 portfolio-source resolution.

HTTP translation is intentionally deferred to TSK-10.3.10B2.
"""

from backend.application.exceptions.application_error import ApplicationError


class PlanningPortfolioSourceUnavailableError(ApplicationError):
    """The selected certified portfolio source cannot be resolved."""


class PlanningPortfolioSourceAmbiguousError(ApplicationError):
    """More than one canonical portfolio scope is eligible."""


class PlanningPortfolioSourceInconsistentError(ApplicationError):
    """Persisted provenance or temporal data violates ADR-023 invariants."""
