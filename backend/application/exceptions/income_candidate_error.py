class IncomeCandidateError(Exception):
    """Base error for the purpose-limited income-candidate boundary."""


class IncomeCandidateNotFoundError(IncomeCandidateError):
    """Candidate or decision is not visible in the authenticated scope."""


class IncomeCandidateEvidenceConflictError(IncomeCandidateError):
    """The reviewed evidence no longer matches the current candidate."""
