"""Trusted authenticated-principal boundary for R4-B read-only tools."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from backend.application.ai_runtime.contracts import ServerUserScope
from backend.application.ai_runtime.errors import (
    AIContractError,
    AIErrorCode,
    AIErrorMetadata,
)
from backend.application.dtos.user_response_dto import UserResponseDTO


class TrustedServerUserScopeResolver:
    """Derive an opaque runtime scope only from the authenticated server DTO."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def resolve(self, principal: UserResponseDTO) -> ServerUserScope:
        user_id = self._require_active_principal(principal)
        resolved_at = self._utc_now()
        return ServerUserScope(
            subject_id=str(user_id),
            authorization_context_id=f"authenticated-user:{user_id}",
            resolved_at=resolved_at,
        )

    def require_matches(
        self,
        scope: ServerUserScope,
        principal: UserResponseDTO,
        *,
        request_id: str,
    ) -> UUID:
        user_id = self._require_active_principal(principal, request_id=request_id)
        expected_context = f"authenticated-user:{user_id}"
        if scope.subject_id != str(user_id) or scope.authorization_context_id != expected_context:
            raise AIContractError(
                AIErrorCode.AUTHORIZATION_DENIED,
                metadata=AIErrorMetadata(request_id=request_id),
            )
        return user_id

    @staticmethod
    def _require_active_principal(
        principal: UserResponseDTO,
        *,
        request_id: str | None = None,
    ) -> UUID:
        if not isinstance(principal, UserResponseDTO) or type(principal.id) is not UUID:
            raise AIContractError(
                AIErrorCode.AUTHORIZATION_DENIED,
                metadata=AIErrorMetadata(request_id=request_id),
            )
        if principal.is_active is not True:
            raise AIContractError(
                AIErrorCode.AUTHORIZATION_DENIED,
                metadata=AIErrorMetadata(request_id=request_id),
            )
        return principal.id

    def _utc_now(self) -> datetime:
        value = self._clock()
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise TypeError("clock must return a timezone-aware datetime.")
        return value.astimezone(timezone.utc)
