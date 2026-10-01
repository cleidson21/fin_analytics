"""Shared construction of explicit user-provided Planning wealth facts."""

from datetime import datetime
from decimal import Decimal

from backend.domains.planning.facts import (
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    PlanningFactAsOf,
    PlanningFactProvenance,
)


def build_user_initial_wealth_fact(
    *,
    amount: Decimal,
    observed_at: datetime,
) -> InitialWealthFact:
    """Build the existing explicit manual fact without manufacturing provenance."""

    return InitialWealthFact(
        source=InitialWealthSource.USER_PROVIDED_SCENARIO,
        amount=amount,
        as_of=PlanningFactAsOf(observed_at=observed_at),
        scope=InitialWealthScope.USER_PROVIDED_SCENARIO,
        provenance=PlanningFactProvenance(
            source_table="planning_request",
            source_type=InitialWealthSource.USER_PROVIDED_SCENARIO.value,
        ),
    )
