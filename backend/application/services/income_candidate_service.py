from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.application.exceptions.income_candidate_error import (
    IncomeCandidateEvidenceConflictError,
    IncomeCandidateNotFoundError,
)
from backend.application.services.single_tenant_user_scope import (
    OwnedUserScope,
    SingleTenantUserScopeGuard,
)
from backend.domains.smart_context import (
    MonthlyOccurrenceCount,
    RecurringIncomeCandidate,
    RecurringIncomeDecision,
    RecurringIncomeDecisionState,
    RecurringIncomeDirection,
    RecurringIncomeEvidenceState,
    RecurringIncomeEvidenceEngine,
    RecurringIncomeRiskFlag,
    build_candidate_id,
)
from backend.infrastructure.persistence.repositories.recurring_income_evidence import (
    RecurringIncomeLedgerReader,
)
from backend.infrastructure.persistence.repositories.smart_context import (
    RecurringIncomeDecisionRepository,
)


@dataclass(frozen=True)
class IncomeCandidateView:
    candidate_id: str
    evidence_state: RecurringIncomeEvidenceState
    decision_state: RecurringIncomeDecisionState | None
    signature_version: int
    source: str
    evidence_fingerprint: str | None
    currency: str | None
    direction: RecurringIncomeDirection | None
    window_start: date | None
    window_end: date | None
    current_month_is_partial: bool | None
    includes_current_month: bool | None
    observed_months: tuple[str, ...]
    monthly_occurrences: tuple[MonthlyOccurrenceCount, ...]
    occurrence_count: int | None
    distinct_month_count: int | None
    first_occurrence_date: date | None
    latest_occurrence_date: date | None
    latest_amount: Decimal | None
    typical_received_amount: Decimal | None
    minimum_received_amount: Decimal | None
    maximum_received_amount: Decimal | None
    median_absolute_deviation: Decimal | None
    risk_flags: tuple[RecurringIncomeRiskFlag, ...]
    decided_at: datetime | None
    decision_updated_at: datetime | None


@dataclass(frozen=True)
class IncomeCandidateCollection:
    as_of_date: date
    candidates: tuple[IncomeCandidateView, ...]


def build_evidence_fingerprint(candidate: RecurringIncomeCandidate) -> str:
    """Hash exact reviewed evidence without exposing its private source identity."""

    payload = json.dumps(
        {
            "candidate_id": candidate.candidate_id,
            "signature_version": candidate.signature_version,
            "source_signature": candidate.source_signature,
            "source_provider": candidate.source_provider,
            "source_account_scope": candidate.source_account_scope,
            "currency": candidate.currency,
            "direction": candidate.direction.value,
            "window_start": candidate.window_start.isoformat(),
            "window_end": candidate.window_end.isoformat(),
            "current_month_is_partial": candidate.current_month_is_partial,
            "includes_current_month": candidate.includes_current_month,
            "observed_months": candidate.observed_months,
            "monthly_occurrences": tuple(
                (item.reference_month, item.occurrence_count)
                for item in candidate.monthly_occurrences
            ),
            "occurrence_count": candidate.occurrence_count,
            "distinct_month_count": candidate.distinct_month_count,
            "first_occurrence_date": candidate.first_occurrence_date.isoformat(),
            "latest_occurrence_date": candidate.latest_occurrence_date.isoformat(),
            "latest_amount": str(candidate.latest_amount),
            "typical_received_amount": str(candidate.typical_received_amount),
            "minimum_received_amount": str(candidate.minimum_received_amount),
            "maximum_received_amount": str(candidate.maximum_received_amount),
            "median_absolute_deviation": (
                None
                if candidate.median_absolute_deviation is None
                else str(candidate.median_absolute_deviation)
            ),
            "risk_flags": tuple(flag.value for flag in candidate.risk_flags),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


class IncomeCandidateService:
    """Owns B4 candidate/decision composition and decision orchestration."""

    def __init__(
        self,
        ownership_guard: SingleTenantUserScopeGuard | None = None,
        ledger_reader: RecurringIncomeLedgerReader | None = None,
        evidence_engine: RecurringIncomeEvidenceEngine | None = None,
        today: Callable[[], date] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._ownership_guard = ownership_guard or SingleTenantUserScopeGuard()
        self._ledger_reader = ledger_reader or RecurringIncomeLedgerReader(
            self._ownership_guard
        )
        self._evidence_engine = evidence_engine or RecurringIncomeEvidenceEngine()
        self._today = today or date.today
        self._clock = clock or datetime.utcnow

    def list_candidates(
        self,
        db: Session,
        current_user_id: UUID,
    ) -> IncomeCandidateCollection:
        owner = self._ownership_guard.resolve(db, current_user_id)
        as_of_date = self._today()
        current = self._current_candidates(db, owner, as_of_date=as_of_date)
        decisions = RecurringIncomeDecisionRepository(db, owner).list_all()
        return self._compose(as_of_date, current, decisions)

    def confirm(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        candidate_id: str,
        evidence_fingerprint: str,
    ) -> IncomeCandidateView:
        return self._set_decision(
            db,
            current_user_id,
            candidate_id=candidate_id,
            evidence_fingerprint=evidence_fingerprint,
            decision_state=RecurringIncomeDecisionState.CONFIRMED_AS_INCOME,
        )

    def reject(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        candidate_id: str,
        evidence_fingerprint: str,
    ) -> IncomeCandidateView:
        return self._set_decision(
            db,
            current_user_id,
            candidate_id=candidate_id,
            evidence_fingerprint=evidence_fingerprint,
            decision_state=RecurringIncomeDecisionState.REJECTED,
        )

    def reset(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        candidate_id: str,
    ) -> None:
        owner = self._ownership_guard.resolve(db, current_user_id)
        repository = RecurringIncomeDecisionRepository(db, owner)
        decision = next(
            (
                item
                for item in repository.list_all()
                if self._decision_candidate_id(item) == candidate_id
            ),
            None,
        )
        if decision is None:
            raise IncomeCandidateNotFoundError("Income candidate is unavailable.")
        removed = repository.reset(
            source_signature=decision.source_signature,
            signature_version=decision.signature_version,
        )
        if not removed:
            raise IncomeCandidateNotFoundError("Income candidate is unavailable.")

    def _set_decision(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        candidate_id: str,
        evidence_fingerprint: str,
        decision_state: RecurringIncomeDecisionState,
    ) -> IncomeCandidateView:
        owner = self._ownership_guard.resolve(db, current_user_id)
        as_of_date = self._today()
        candidate = next(
            (
                item
                for item in self._current_candidates(
                    db,
                    owner,
                    as_of_date=as_of_date,
                )
                if item.candidate_id == candidate_id
            ),
            None,
        )
        if candidate is None:
            raise IncomeCandidateNotFoundError("Income candidate is unavailable.")

        current_fingerprint = build_evidence_fingerprint(candidate)
        if not hmac.compare_digest(current_fingerprint, evidence_fingerprint):
            raise IncomeCandidateEvidenceConflictError(
                "Income candidate evidence changed."
            )

        decision = RecurringIncomeDecisionRepository(db, owner).save(
            source_provider=candidate.source_provider,
            source_account_scope=candidate.source_account_scope,
            source_signature=candidate.source_signature,
            signature_version=candidate.signature_version,
            decision=decision_state,
            label=None,
            at=self._clock(),
        )
        return self._current_view(candidate, decision)

    def _current_candidates(
        self,
        db: Session,
        owner: OwnedUserScope,
        *,
        as_of_date: date,
    ) -> tuple[RecurringIncomeCandidate, ...]:
        observations = self._ledger_reader.read_eligible_observations_for_scope(
            db,
            owner,
            as_of_date=as_of_date,
        )
        return self._evidence_engine.detect(observations, as_of_date=as_of_date)

    def _compose(
        self,
        as_of_date: date,
        candidates: tuple[RecurringIncomeCandidate, ...],
        decisions: tuple[RecurringIncomeDecision, ...],
    ) -> IncomeCandidateCollection:
        remaining = {
            (decision.source_signature, decision.signature_version): decision
            for decision in decisions
        }
        views = []
        for candidate in candidates:
            decision = remaining.pop(
                (candidate.source_signature, candidate.signature_version),
                None,
            )
            views.append(self._current_view(candidate, decision))

        # Repository order is deterministic: updated_at descending, then
        # signature/version. Dict insertion order preserves that stale suffix.
        stale = tuple(remaining.values())
        views.extend(self._stale_view(decision) for decision in stale)
        return IncomeCandidateCollection(as_of_date=as_of_date, candidates=tuple(views))

    @staticmethod
    def _current_view(
        candidate: RecurringIncomeCandidate,
        decision: RecurringIncomeDecision | None,
    ) -> IncomeCandidateView:
        return IncomeCandidateView(
            candidate_id=candidate.candidate_id,
            evidence_state=RecurringIncomeEvidenceState(
                candidate.classification_state.value
            ),
            decision_state=None if decision is None else decision.decision,
            signature_version=candidate.signature_version,
            source="GOVERNED_TRANSACTIONS",
            evidence_fingerprint=build_evidence_fingerprint(candidate),
            currency=candidate.currency,
            direction=candidate.direction,
            window_start=candidate.window_start,
            window_end=candidate.window_end,
            current_month_is_partial=candidate.current_month_is_partial,
            includes_current_month=candidate.includes_current_month,
            observed_months=candidate.observed_months,
            monthly_occurrences=candidate.monthly_occurrences,
            occurrence_count=candidate.occurrence_count,
            distinct_month_count=candidate.distinct_month_count,
            first_occurrence_date=candidate.first_occurrence_date,
            latest_occurrence_date=candidate.latest_occurrence_date,
            latest_amount=candidate.latest_amount,
            typical_received_amount=candidate.typical_received_amount,
            minimum_received_amount=candidate.minimum_received_amount,
            maximum_received_amount=candidate.maximum_received_amount,
            median_absolute_deviation=candidate.median_absolute_deviation,
            risk_flags=candidate.risk_flags,
            decided_at=None if decision is None else decision.decided_at,
            decision_updated_at=None if decision is None else decision.updated_at,
        )

    @staticmethod
    def _stale_view(decision: RecurringIncomeDecision) -> IncomeCandidateView:
        return IncomeCandidateView(
            candidate_id=IncomeCandidateService._decision_candidate_id(decision),
            evidence_state=RecurringIncomeEvidenceState.STALE,
            decision_state=decision.decision,
            signature_version=decision.signature_version,
            source="GOVERNED_TRANSACTIONS",
            evidence_fingerprint=None,
            currency=None,
            direction=None,
            window_start=None,
            window_end=None,
            current_month_is_partial=None,
            includes_current_month=None,
            observed_months=(),
            monthly_occurrences=(),
            occurrence_count=None,
            distinct_month_count=None,
            first_occurrence_date=None,
            latest_occurrence_date=None,
            latest_amount=None,
            typical_received_amount=None,
            minimum_received_amount=None,
            maximum_received_amount=None,
            median_absolute_deviation=None,
            risk_flags=(),
            decided_at=decision.decided_at,
            decision_updated_at=decision.updated_at,
        )

    @staticmethod
    def _decision_candidate_id(decision: RecurringIncomeDecision) -> str:
        return build_candidate_id(
            decision.source_signature,
            signature_version=decision.signature_version,
        )
