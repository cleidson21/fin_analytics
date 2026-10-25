from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from backend.application.services.wealth_home_read_service import (
    WealthHomeAvailability,
    WealthHomeCompleteness,
    WealthHomeFreshness,
)
from backend.domain.enums.goal_status import GoalStatus


class WealthHomeSourceReadModel(BaseModel):
    authority: str
    reader: str
    version: str
    scope: str
    read_at: datetime
    updated_at: datetime | None
    freshness: WealthHomeFreshness
    completeness: WealthHomeCompleteness


class WealthHomeHealthReadModel(BaseModel):
    status: WealthHomeAvailability
    reference_month: str
    currency: str
    net_cashflow: str | None
    reason: str | None
    source: WealthHomeSourceReadModel


class WealthHomeGoalStatusCountReadModel(BaseModel):
    status: GoalStatus
    count: int


class WealthHomeGoalsReadModel(BaseModel):
    status: WealthHomeAvailability
    total_count: int
    by_status: tuple[WealthHomeGoalStatusCountReadModel, ...]
    reason: str | None
    source: WealthHomeSourceReadModel


class WealthHomeInvestmentsReadModel(BaseModel):
    status: WealthHomeAvailability
    requested_reference_month: str
    snapshot_reference_month: str | None
    currency: str
    investment_wealth: str | None
    source_type: str | None
    portfolio_scope: str | None
    run_id: str | None
    reason: str | None
    source: WealthHomeSourceReadModel


class WealthHomeReadModel(BaseModel):
    """Minimal public W3.1 contract; financial values are JSON strings."""

    contract_version: str
    status: WealthHomeAvailability
    reference_month: str
    scope: str
    generated_at: datetime
    health: WealthHomeHealthReadModel
    goals: WealthHomeGoalsReadModel
    investments: WealthHomeInvestmentsReadModel
