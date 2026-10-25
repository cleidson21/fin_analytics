from __future__ import annotations

from decimal import Decimal

from backend.application.dtos.wealth_home_dto import (
    WealthHomeGoalsReadModel,
    WealthHomeGoalStatusCountReadModel,
    WealthHomeHealthReadModel,
    WealthHomeInvestmentsReadModel,
    WealthHomeReadModel,
    WealthHomeSourceReadModel,
)
from backend.application.services.wealth_home_read_service import (
    WealthHomeData,
    WealthHomeSourceMetadata,
)


def _serialize_decimal(value: Decimal) -> str:
    if not isinstance(value, Decimal):
        raise TypeError("Wealth Home financial values must be Decimal.")
    if not value.is_finite():
        raise ValueError("Wealth Home financial values must be finite.")
    return str(value)


def _map_source(source: WealthHomeSourceMetadata) -> WealthHomeSourceReadModel:
    return WealthHomeSourceReadModel(
        authority=source.authority,
        reader=source.reader,
        version=source.version,
        scope=source.scope,
        read_at=source.read_at,
        updated_at=source.updated_at,
        freshness=source.freshness,
        completeness=source.completeness,
    )


def map_wealth_home(data: WealthHomeData) -> WealthHomeReadModel:
    return WealthHomeReadModel(
        contract_version=data.contract_version,
        status=data.status,
        reference_month=data.reference_month,
        scope=data.scope,
        generated_at=data.generated_at,
        health=WealthHomeHealthReadModel(
            status=data.health.status,
            reference_month=data.health.reference_month,
            currency=data.health.currency,
            net_cashflow=(
                None
                if data.health.net_cashflow is None
                else _serialize_decimal(data.health.net_cashflow)
            ),
            reason=data.health.reason,
            source=_map_source(data.health.source),
        ),
        goals=WealthHomeGoalsReadModel(
            status=data.goals.status,
            total_count=data.goals.total_count,
            by_status=tuple(
                WealthHomeGoalStatusCountReadModel(
                    status=item.status,
                    count=item.count,
                )
                for item in data.goals.by_status
            ),
            reason=data.goals.reason,
            source=_map_source(data.goals.source),
        ),
        investments=WealthHomeInvestmentsReadModel(
            status=data.investments.status,
            requested_reference_month=data.investments.requested_reference_month,
            snapshot_reference_month=data.investments.snapshot_reference_month,
            currency=data.investments.currency,
            investment_wealth=(
                None
                if data.investments.investment_wealth is None
                else _serialize_decimal(data.investments.investment_wealth)
            ),
            source_type=data.investments.source_type,
            portfolio_scope=data.investments.portfolio_scope,
            run_id=data.investments.run_id,
            reason=data.investments.reason,
            source=_map_source(data.investments.source),
        ),
    )
