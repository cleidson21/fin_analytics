from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.application.exceptions.smart_context_composition_error import (
    UnsupportedSmartContextFeatureError,
)
from backend.application.services.single_tenant_user_scope import (
    SingleTenantUserScopeGuard,
)
from backend.application.services.smart_context_sources import (
    GoalSmartContextSource,
    HealthSmartContextSource,
    PortfolioSmartContextSource,
    ProfileSmartContextSource,
    RecurringIncomeSmartContextSource,
)
from backend.domain.enums.goal_status import GoalStatus
from backend.domains.planning.facts import GoalPlanningFact, InitialWealthFact
from backend.domains.smart_context import (
    DeclaredFinancialContext,
    RecurringIncomeDecisionState,
    RecurringIncomeEvidenceState,
    SmartContextFeature,
    SmartDefaultState,
    SmartFeatureContext,
    SmartFreshness,
    SmartOverridePolicy,
    SmartSemanticType,
    SmartUnavailableReason,
    SmartValue,
    SmartValueEvidence,
    SmartValueKey,
    SmartValueOwner,
    SmartValueScope,
    SmartValueSource,
    SmartValueType,
)


FEATURE_ALLOWLISTS: dict[SmartContextFeature, frozenset[SmartValueKey]] = {
    SmartContextFeature.PROFILE: frozenset(
        {
            SmartValueKey.DECLARED_MONTHLY_GROSS_INCOME,
            SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE,
            SmartValueKey.RECURRING_INCOME_REVIEW_AVAILABLE,
        }
    ),
    SmartContextFeature.HOME: frozenset(
        {
            SmartValueKey.DECLARED_MONTHLY_GROSS_INCOME,
            SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE,
            SmartValueKey.HEALTH_MONTHLY_INCOME,
            SmartValueKey.HEALTH_MONTHLY_EXPENSES,
            SmartValueKey.HEALTH_NET_CASHFLOW,
            SmartValueKey.HEALTH_SAVINGS_AMOUNT,
            SmartValueKey.HEALTH_SAVINGS_RATE,
            SmartValueKey.INVESTMENT_WEALTH,
            SmartValueKey.GOAL_NAME,
            SmartValueKey.GOAL_TARGET_AMOUNT,
            SmartValueKey.GOAL_TARGET_DATE,
            SmartValueKey.GOAL_CURRENT_AMOUNT,
            SmartValueKey.GOAL_STATUS,
            SmartValueKey.GOAL_SUMMARY,
        }
    ),
    SmartContextFeature.PLANNING: frozenset(
        {
            SmartValueKey.INVESTMENT_WEALTH,
            SmartValueKey.PLANNING_CONTRIBUTION,
            SmartValueKey.PLANNING_EXPECTED_RETURN,
            SmartValueKey.PLANNING_INFLATION,
        }
    ),
    SmartContextFeature.GOAL: frozenset(
        {
            SmartValueKey.GOAL_SUMMARY,
            SmartValueKey.GOAL_NAME,
            SmartValueKey.GOAL_TARGET_AMOUNT,
            SmartValueKey.GOAL_TARGET_DATE,
            SmartValueKey.GOAL_CURRENT_AMOUNT,
            SmartValueKey.GOAL_PLANNED_CONTRIBUTION,
            SmartValueKey.GOAL_PRIORITY,
            SmartValueKey.GOAL_STATUS,
            SmartValueKey.HEALTH_SAVINGS_AMOUNT,
        }
    ),
    SmartContextFeature.FIRE: frozenset(
        {
            SmartValueKey.INVESTMENT_WEALTH,
            SmartValueKey.FIRE_RETIREMENT_SPENDING,
            SmartValueKey.FIRE_WITHDRAWAL_RATE,
            SmartValueKey.FIRE_EXPECTED_RETURN,
            SmartValueKey.FIRE_INFLATION,
            SmartValueKey.FIRE_CONTRIBUTION,
        }
    ),
}


class SmartFinancialContextService:
    """Read-only, purpose-limited composition over existing authorities."""

    def __init__(
        self,
        *,
        ownership_guard: SingleTenantUserScopeGuard | None = None,
        profile_source: ProfileSmartContextSource | None = None,
        recurring_income_source: RecurringIncomeSmartContextSource | None = None,
        health_source: HealthSmartContextSource | None = None,
        goal_source: GoalSmartContextSource | None = None,
        portfolio_source: PortfolioSmartContextSource | None = None,
    ) -> None:
        self._ownership_guard = ownership_guard or SingleTenantUserScopeGuard()
        self._profile_source = profile_source or ProfileSmartContextSource()
        self._recurring_income_source = (
            recurring_income_source or RecurringIncomeSmartContextSource()
        )
        self._health_source = health_source or HealthSmartContextSource()
        self._goal_source = goal_source or GoalSmartContextSource()
        self._portfolio_source = portfolio_source or PortfolioSmartContextSource()

    def get_context_for(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        feature: SmartContextFeature,
        as_of_date: date,
    ) -> SmartFeatureContext:
        if not isinstance(feature, SmartContextFeature):
            raise UnsupportedSmartContextFeatureError(
                "Smart Context requires a supported feature identifier."
            )
        if type(as_of_date) is not date:
            raise TypeError("as_of_date must be a civil date.")

        # This guard is the one security gate shared by all otherwise disparate
        # single-tenant sources. Security failures are never converted to nulls.
        self._ownership_guard.resolve(db, current_user_id)

        if feature is SmartContextFeature.PROFILE:
            values = self._profile_context(db, current_user_id, as_of_date)
        elif feature is SmartContextFeature.HOME:
            values = self._home_context(db, current_user_id, as_of_date)
        elif feature is SmartContextFeature.PLANNING:
            values = self._planning_context(db, current_user_id, as_of_date)
        elif feature is SmartContextFeature.GOAL:
            values = self._goal_context(db, current_user_id, as_of_date)
        elif feature is SmartContextFeature.FIRE:
            values = self._fire_context(db, current_user_id, as_of_date)
        else:  # pragma: no cover - Enum exhaustiveness defense
            raise UnsupportedSmartContextFeatureError("Unsupported Smart Context feature.")

        allowed = FEATURE_ALLOWLISTS[feature]
        if any(value.key not in allowed for value in values):
            raise RuntimeError("Smart Context feature allowlist was violated.")
        return SmartFeatureContext(feature=feature, as_of_date=as_of_date, values=values)

    def _profile_context(
        self,
        db: Session,
        current_user_id: UUID,
        as_of_date: date,
    ) -> tuple[SmartValue, ...]:
        declared = self._profile_source.read(db, current_user_id)
        recurring = self._recurring_income_source.read(
            db, current_user_id, as_of_date=as_of_date
        )
        return (
            self._declared_income_value(declared, reference_only=False),
            *self._recurring_values(recurring, include_review=True),
        )

    def _home_context(
        self,
        db: Session,
        current_user_id: UUID,
        as_of_date: date,
    ) -> tuple[SmartValue, ...]:
        declared = self._profile_source.read(db, current_user_id)
        recurring = self._recurring_income_source.read(
            db, current_user_id, as_of_date=as_of_date
        )
        health = self._health_source.read_month(db, as_of_date=as_of_date)
        goals = self._goal_source.read_owned(db, current_user_id)
        wealth = self._portfolio_source.read(
            db, current_user_id, as_of_date=as_of_date
        )
        return (
            self._declared_income_value(declared, reference_only=True),
            *self._recurring_values(recurring, include_review=False),
            *self._health_values(health, as_of_date=as_of_date),
            self._wealth_value(wealth),
            *self._goal_values(goals, summary=True),
        )

    def _planning_context(
        self,
        db: Session,
        current_user_id: UUID,
        as_of_date: date,
    ) -> tuple[SmartValue, ...]:
        wealth = self._portfolio_source.read(
            db, current_user_id, as_of_date=as_of_date
        )
        return (
            self._wealth_value(wealth),
            self._assumption(SmartValueKey.PLANNING_CONTRIBUTION, SmartValueOwner.PLANNING),
            self._assumption(SmartValueKey.PLANNING_EXPECTED_RETURN, SmartValueOwner.PLANNING),
            self._assumption(SmartValueKey.PLANNING_INFLATION, SmartValueOwner.PLANNING),
        )

    def _goal_context(
        self,
        db: Session,
        current_user_id: UUID,
        as_of_date: date,
    ) -> tuple[SmartValue, ...]:
        goals = self._goal_source.read_owned(db, current_user_id)
        health = self._health_source.read_month(db, as_of_date=as_of_date)
        savings = self._health_savings_reference(health, as_of_date=as_of_date)
        return (*self._goal_values(goals, summary=False), savings)

    def _fire_context(
        self,
        db: Session,
        current_user_id: UUID,
        as_of_date: date,
    ) -> tuple[SmartValue, ...]:
        wealth = self._portfolio_source.read(
            db, current_user_id, as_of_date=as_of_date
        )
        return (
            self._wealth_value(wealth),
            self._assumption(SmartValueKey.FIRE_RETIREMENT_SPENDING, SmartValueOwner.FIRE),
            self._assumption(
                SmartValueKey.FIRE_WITHDRAWAL_RATE,
                SmartValueOwner.FIRE,
                value_type=SmartValueType.RATIO,
            ),
            self._assumption(
                SmartValueKey.FIRE_EXPECTED_RETURN,
                SmartValueOwner.FIRE,
                value_type=SmartValueType.RATIO,
            ),
            self._assumption(
                SmartValueKey.FIRE_INFLATION,
                SmartValueOwner.FIRE,
                value_type=SmartValueType.RATIO,
            ),
            self._assumption(SmartValueKey.FIRE_CONTRIBUTION, SmartValueOwner.FIRE),
        )

    @staticmethod
    def _declared_income_value(
        declared: DeclaredFinancialContext | None,
        *,
        reference_only: bool,
    ) -> SmartValue:
        amount = None if declared is None else declared.declared_monthly_gross_income
        if amount is None:
            return SmartValue(
                key=SmartValueKey.DECLARED_MONTHLY_GROSS_INCOME,
                value=None,
                value_type=SmartValueType.MONEY,
                semantic_type=SmartSemanticType.DECLARED,
                owner=SmartValueOwner.PROFILE,
                source=SmartValueSource.USER_PROFILE,
                source_label="Profile · declared by you",
                state=SmartDefaultState.INCOMPLETE_OR_UNAVAILABLE,
                override_policy=SmartOverridePolicy.NOT_ALLOWED,
                scope=SmartValueScope("DECLARED_GROSS_MONTHLY_BRL"),
                unavailable_reason=SmartUnavailableReason.NOT_DECLARED,
                reason="No declared monthly gross income is stored.",
            )
        return SmartValue(
            key=SmartValueKey.DECLARED_MONTHLY_GROSS_INCOME,
            value=amount,
            value_type=SmartValueType.MONEY,
            semantic_type=SmartSemanticType.DECLARED,
            owner=SmartValueOwner.PROFILE,
            source=SmartValueSource.USER_PROFILE,
            source_label="Profile · declared by you",
            state=(
                SmartDefaultState.SUGGESTED_REFERENCE
                if reference_only
                else SmartDefaultState.KNOWN_FACT
            ),
            override_policy=(
                SmartOverridePolicy.USE_AS_REFERENCE
                if reference_only
                else SmartOverridePolicy.NOT_ALLOWED
            ),
            scope=SmartValueScope("DECLARED_GROSS_MONTHLY_BRL"),
            declared_at=declared.declared_at,
            reference_period=(
                None
                if declared.income_as_of_date is None
                else declared.income_as_of_date.isoformat()
            ),
        )

    @staticmethod
    def _recurring_values(collection, *, include_review: bool) -> tuple[SmartValue, ...]:
        values: list[SmartValue] = []
        review_count = 0
        for candidate in collection.candidates:
            if (
                candidate.evidence_state is RecurringIncomeEvidenceState.DETECTED_CANDIDATE
                and candidate.decision_state is RecurringIncomeDecisionState.CONFIRMED_AS_INCOME
            ):
                values.append(
                    SmartValue(
                        key=SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE,
                        value=candidate.typical_received_amount,
                        value_type=SmartValueType.MONEY,
                        semantic_type=SmartSemanticType.DERIVED,
                        owner=SmartValueOwner.GOVERNED_LEDGER,
                        source=SmartValueSource.GOVERNED_TRANSACTIONS,
                        source_label="Governed transactions · confirmed recurring income source",
                        state=SmartDefaultState.SUGGESTED_REFERENCE,
                        override_policy=SmartOverridePolicy.USE_AS_REFERENCE,
                        scope=SmartValueScope("RECURRING_INCOME_SOURCE", candidate.candidate_id),
                        observed_at=candidate.latest_occurrence_date,
                        reference_period=(
                            f"{candidate.window_start.isoformat()}/"
                            f"{candidate.window_end.isoformat()}"
                        ),
                        freshness=SmartFreshness.CURRENT_EVIDENCE,
                        confirmation_status=candidate.decision_state,
                        evidence=SmartValueEvidence(
                            window_start=candidate.window_start,
                            window_end=candidate.window_end,
                            first_occurrence_date=candidate.first_occurrence_date,
                            latest_occurrence_date=candidate.latest_occurrence_date,
                            occurrence_count=candidate.occurrence_count,
                            distinct_month_count=candidate.distinct_month_count,
                            typical_received_amount=candidate.typical_received_amount,
                            risk_flags=tuple(flag.value for flag in candidate.risk_flags),
                        ),
                    )
                )
            elif (
                candidate.evidence_state is RecurringIncomeEvidenceState.STALE
                and candidate.decision_state is RecurringIncomeDecisionState.CONFIRMED_AS_INCOME
            ):
                values.append(
                    SmartValue(
                        key=SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE,
                        value=None,
                        value_type=SmartValueType.MONEY,
                        semantic_type=SmartSemanticType.OBSERVED,
                        owner=SmartValueOwner.GOVERNED_LEDGER,
                        source=SmartValueSource.GOVERNED_TRANSACTIONS,
                        source_label="Governed transactions · confirmed recurring income source",
                        state=SmartDefaultState.INCOMPLETE_OR_UNAVAILABLE,
                        override_policy=SmartOverridePolicy.USE_AS_REFERENCE,
                        scope=SmartValueScope("RECURRING_INCOME_SOURCE", candidate.candidate_id),
                        freshness=SmartFreshness.STALE_EVIDENCE,
                        confirmation_status=candidate.decision_state,
                        unavailable_reason=SmartUnavailableReason.STALE_EVIDENCE,
                        reason="The confirmed source has no current qualifying evidence.",
                    )
                )
            elif (
                candidate.evidence_state is RecurringIncomeEvidenceState.DETECTED_CANDIDATE
                and candidate.decision_state is None
            ):
                review_count += 1

        if not values:
            values.append(
                SmartValue(
                    key=SmartValueKey.CONFIRMED_RECURRING_INCOME_SOURCE,
                    value=None,
                    value_type=SmartValueType.MONEY,
                    semantic_type=SmartSemanticType.OBSERVED,
                    owner=SmartValueOwner.GOVERNED_LEDGER,
                    source=SmartValueSource.GOVERNED_TRANSACTIONS,
                    source_label="Governed transactions · confirmed recurring income source",
                    state=SmartDefaultState.INCOMPLETE_OR_UNAVAILABLE,
                    override_policy=SmartOverridePolicy.USE_AS_REFERENCE,
                    unavailable_reason=SmartUnavailableReason.NO_CONFIRMED_SOURCE,
                    reason="No current recurring income source is confirmed.",
                )
            )
        if include_review and review_count:
            values.append(
                SmartValue(
                    key=SmartValueKey.RECURRING_INCOME_REVIEW_AVAILABLE,
                    value=review_count,
                    value_type=SmartValueType.INTEGER,
                    semantic_type=SmartSemanticType.OBSERVED,
                    owner=SmartValueOwner.GOVERNED_LEDGER,
                    source=SmartValueSource.GOVERNED_TRANSACTIONS,
                    source_label="Governed transactions · recurring source review",
                    state=SmartDefaultState.SUGGESTED_REFERENCE,
                    override_policy=SmartOverridePolicy.NOT_ALLOWED,
                    reference_period=collection.as_of_date.isoformat(),
                )
            )
        return tuple(values)

    @staticmethod
    def _health_values(health, *, as_of_date: date) -> tuple[SmartValue, ...]:
        keys = (
            (
                SmartValueKey.HEALTH_MONTHLY_INCOME,
                SmartSemanticType.OBSERVED,
                SmartValueType.MONEY,
                "total_income",
            ),
            (
                SmartValueKey.HEALTH_MONTHLY_EXPENSES,
                SmartSemanticType.OBSERVED,
                SmartValueType.MONEY,
                "total_expense",
            ),
            (
                SmartValueKey.HEALTH_NET_CASHFLOW,
                SmartSemanticType.DERIVED,
                SmartValueType.MONEY,
                "net_cashflow",
            ),
            (
                SmartValueKey.HEALTH_SAVINGS_AMOUNT,
                SmartSemanticType.DERIVED,
                SmartValueType.MONEY,
                "savings_amount",
            ),
            (
                SmartValueKey.HEALTH_SAVINGS_RATE,
                SmartSemanticType.DERIVED,
                SmartValueType.RATIO,
                "savings_rate",
            ),
        )
        if health is None:
            return tuple(
                SmartValue(
                    key=key,
                    value=None,
                    value_type=value_type,
                    semantic_type=semantic,
                    owner=SmartValueOwner.FINANCIAL_HEALTH,
                    source=SmartValueSource.FINANCIAL_HEALTH,
                    source_label="Financial Health · monthly certified facts",
                    state=SmartDefaultState.INCOMPLETE_OR_UNAVAILABLE,
                    override_policy=SmartOverridePolicy.NOT_ALLOWED,
                    reference_period=as_of_date.strftime("%Y-%m"),
                    unavailable_reason=SmartUnavailableReason.SOURCE_UNAVAILABLE,
                    reason="Financial Health has no fact for the requested period.",
                )
                for key, semantic, value_type, _ in keys
            )
        freshness = (
            SmartFreshness.CLOSED_PERIOD
            if as_of_date.day == monthrange(as_of_date.year, as_of_date.month)[1]
            else SmartFreshness.PARTIAL_PERIOD
        )
        values = []
        for key, semantic, value_type, attribute in keys:
            value = getattr(health, attribute)
            if value is None:
                values.append(
                    SmartValue(
                        key=key,
                        value=None,
                        value_type=value_type,
                        semantic_type=semantic,
                        owner=SmartValueOwner.FINANCIAL_HEALTH,
                        source=SmartValueSource.FINANCIAL_HEALTH,
                        source_label=(
                            f"Financial Health · reference {health.reference_month}"
                        ),
                        state=SmartDefaultState.INCOMPLETE_OR_UNAVAILABLE,
                        override_policy=SmartOverridePolicy.NOT_ALLOWED,
                        scope=SmartValueScope("CONSOLIDATED_HEALTH"),
                        reference_period=health.reference_month,
                        freshness=freshness,
                        unavailable_reason=SmartUnavailableReason.SOURCE_UNAVAILABLE,
                        reason="The certified Health metric is not available for this period.",
                    )
                )
                continue
            values.append(
                SmartValue(
                    key=key,
                    value=value,
                    value_type=value_type,
                    semantic_type=semantic,
                    owner=SmartValueOwner.FINANCIAL_HEALTH,
                    source=SmartValueSource.FINANCIAL_HEALTH,
                    source_label=f"Financial Health · reference {health.reference_month}",
                    state=SmartDefaultState.KNOWN_FACT,
                    override_policy=SmartOverridePolicy.NOT_ALLOWED,
                    scope=SmartValueScope("CONSOLIDATED_HEALTH"),
                    reference_period=health.reference_month,
                    freshness=freshness,
                )
            )
        return tuple(values)

    @staticmethod
    def _health_savings_reference(health, *, as_of_date: date) -> SmartValue:
        if health is None:
            return SmartValue(
                key=SmartValueKey.HEALTH_SAVINGS_AMOUNT,
                value=None,
                value_type=SmartValueType.MONEY,
                semantic_type=SmartSemanticType.DERIVED,
                owner=SmartValueOwner.FINANCIAL_HEALTH,
                source=SmartValueSource.FINANCIAL_HEALTH,
                source_label="Financial Health · realized savings",
                state=SmartDefaultState.INCOMPLETE_OR_UNAVAILABLE,
                override_policy=SmartOverridePolicy.USE_AS_REFERENCE,
                reference_period=as_of_date.strftime("%Y-%m"),
                unavailable_reason=SmartUnavailableReason.SOURCE_UNAVAILABLE,
                reason="No realized savings fact exists for the requested period.",
            )
        return SmartValue(
            key=SmartValueKey.HEALTH_SAVINGS_AMOUNT,
            value=health.savings_amount,
            value_type=SmartValueType.MONEY,
            semantic_type=SmartSemanticType.DERIVED,
            owner=SmartValueOwner.FINANCIAL_HEALTH,
            source=SmartValueSource.FINANCIAL_HEALTH,
            source_label=f"Financial Health · realized savings · {health.reference_month}",
            state=SmartDefaultState.SUGGESTED_REFERENCE,
            override_policy=SmartOverridePolicy.USE_AS_REFERENCE,
            scope=SmartValueScope("CONSOLIDATED_HEALTH"),
            reference_period=health.reference_month,
            freshness=(
                SmartFreshness.CLOSED_PERIOD
                if as_of_date.day == monthrange(as_of_date.year, as_of_date.month)[1]
                else SmartFreshness.PARTIAL_PERIOD
            ),
            reason="Realized historical savings; not sustainable contribution capacity.",
        )

    @staticmethod
    def _wealth_value(wealth: InitialWealthFact | None) -> SmartValue:
        if wealth is None:
            return SmartValue(
                key=SmartValueKey.INVESTMENT_WEALTH,
                value=None,
                value_type=SmartValueType.MONEY,
                semantic_type=SmartSemanticType.OBSERVED,
                owner=SmartValueOwner.PLANNING_PORTFOLIO_RESOLVER,
                source=SmartValueSource.INVESTMENT_PORTFOLIO,
                source_label="Investment portfolio · certified wealth",
                state=SmartDefaultState.INCOMPLETE_OR_UNAVAILABLE,
                override_policy=SmartOverridePolicy.SELECT_SOURCE,
                unavailable_reason=SmartUnavailableReason.SOURCE_UNAVAILABLE,
                reason="No eligible investment portfolio snapshot is available.",
            )
        reference = wealth.as_of.reference_month
        return SmartValue(
            key=SmartValueKey.INVESTMENT_WEALTH,
            value=wealth.amount,
            value_type=SmartValueType.MONEY,
            semantic_type=SmartSemanticType.OBSERVED,
            owner=SmartValueOwner.PLANNING_PORTFOLIO_RESOLVER,
            source=SmartValueSource.INVESTMENT_PORTFOLIO,
            source_label=(
                "Investment portfolio · certified wealth"
                if reference is None
                else f"Investment portfolio · reference {reference}"
            ),
            state=SmartDefaultState.SUGGESTED_REFERENCE,
            override_policy=SmartOverridePolicy.SELECT_SOURCE,
            scope=SmartValueScope("INVESTMENT_PORTFOLIO"),
            observed_at=wealth.as_of.observed_at,
            reference_period=reference,
        )

    @staticmethod
    def _goal_values(
        goals: tuple[GoalPlanningFact, ...],
        *,
        summary: bool,
    ) -> tuple[SmartValue, ...]:
        if not goals:
            return (
                SmartValue(
                    key=SmartValueKey.GOAL_SUMMARY,
                    value=None,
                    value_type=SmartValueType.TEXT,
                    semantic_type=SmartSemanticType.DECLARED,
                    owner=SmartValueOwner.GOALS,
                    source=SmartValueSource.GOAL,
                    source_label="Goals · owned goals",
                    state=SmartDefaultState.INCOMPLETE_OR_UNAVAILABLE,
                    override_policy=SmartOverridePolicy.NOT_ALLOWED,
                    unavailable_reason=SmartUnavailableReason.NO_GOALS,
                    reason="No owned Goal is available.",
                ),
            )
        values: list[SmartValue] = []
        for goal in goals:
            scope = SmartValueScope("GOAL", str(goal.goal_id))
            label = f"Goals · {goal.name}"
            fields = [
                (SmartValueKey.GOAL_NAME, goal.name, SmartValueType.TEXT),
                (SmartValueKey.GOAL_TARGET_AMOUNT, goal.target_amount, SmartValueType.MONEY),
                (SmartValueKey.GOAL_TARGET_DATE, goal.target_date, SmartValueType.DATE),
                (SmartValueKey.GOAL_CURRENT_AMOUNT, goal.current_amount, SmartValueType.MONEY),
                (
                    SmartValueKey.GOAL_STATUS,
                    (
                        goal.status.value
                        if isinstance(goal.status, GoalStatus)
                        else str(goal.status)
                    ),
                    SmartValueType.ENUM,
                ),
            ]
            if not summary:
                fields.extend(
                    [
                        (
                            SmartValueKey.GOAL_PLANNED_CONTRIBUTION,
                            goal.goal_planned_monthly_contribution,
                            SmartValueType.MONEY,
                        ),
                        (SmartValueKey.GOAL_PRIORITY, goal.priority, SmartValueType.INTEGER),
                    ]
                )
            for key, value, value_type in fields:
                if value is None:
                    continue
                values.append(
                    SmartValue(
                        key=key,
                        value=value,
                        value_type=value_type,
                        semantic_type=SmartSemanticType.DECLARED,
                        owner=SmartValueOwner.GOALS,
                        source=SmartValueSource.GOAL,
                        source_label=label,
                        state=SmartDefaultState.KNOWN_FACT,
                        override_policy=SmartOverridePolicy.NOT_ALLOWED,
                        scope=scope,
                        observed_at=goal.updated_at,
                    )
                )
        return tuple(values)

    @staticmethod
    def _assumption(
        key: SmartValueKey,
        owner: SmartValueOwner,
        *,
        value_type: SmartValueType = SmartValueType.MONEY,
    ) -> SmartValue:
        return SmartValue(
            key=key,
            value=None,
            value_type=value_type,
            semantic_type=SmartSemanticType.ASSUMPTION,
            owner=owner,
            source=SmartValueSource.USER_INPUT_REQUIRED,
            source_label=f"{owner.value.title()} · explicit scenario assumption",
            state=SmartDefaultState.ASSUMPTION_REQUIRED,
            override_policy=SmartOverridePolicy.SCENARIO_OVERRIDE,
            unavailable_reason=SmartUnavailableReason.ASSUMPTION_REQUIRED,
            reason="Define this assumption explicitly for the analysis.",
        )
