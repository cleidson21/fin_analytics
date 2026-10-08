from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from backend.application.services.smart_financial_context_service import (
    SmartFinancialContextService,
)
from backend.domains.smart_context import SmartContextFeature, SmartFeatureContext


class SmartContextProvider(Protocol):
    """Internal B5 boundary consumed without exposing source-domain readers."""

    def get_context_for(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        feature: SmartContextFeature,
        as_of_date: date,
    ) -> SmartFeatureContext: ...


class SmartContextConsumerFoundation:
    """Read-only, opt-in access to purpose-specific B5 context.

    These methods expose eligible facts, references, and explicit unavailable or
    assumption-required states. They never construct effective engine inputs.
    """

    def __init__(self, context_service: SmartContextProvider | None = None) -> None:
        self._context_service = (
            context_service
            if context_service is not None
            else SmartFinancialContextService()
        )

    def get_home_context(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        as_of_date: date,
    ) -> SmartFeatureContext:
        return self._get_context(
            db,
            current_user_id,
            feature=SmartContextFeature.HOME,
            as_of_date=as_of_date,
        )

    def get_planning_context(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        as_of_date: date,
    ) -> SmartFeatureContext:
        return self._get_context(
            db,
            current_user_id,
            feature=SmartContextFeature.PLANNING,
            as_of_date=as_of_date,
        )

    def get_goal_context(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        as_of_date: date,
    ) -> SmartFeatureContext:
        return self._get_context(
            db,
            current_user_id,
            feature=SmartContextFeature.GOAL,
            as_of_date=as_of_date,
        )

    def get_fire_context(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        as_of_date: date,
    ) -> SmartFeatureContext:
        return self._get_context(
            db,
            current_user_id,
            feature=SmartContextFeature.FIRE,
            as_of_date=as_of_date,
        )

    def _get_context(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        feature: SmartContextFeature,
        as_of_date: date,
    ) -> SmartFeatureContext:
        return self._context_service.get_context_for(
            db,
            current_user_id,
            feature=feature,
            as_of_date=as_of_date,
        )
