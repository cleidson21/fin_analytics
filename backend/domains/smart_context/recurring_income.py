from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


SIGNATURE_VERSION = 1
MINIMUM_OBSERVED_MONTHS = 3
EVIDENCE_WINDOW_MONTHS = 6


class RecurringIncomeCandidateState(str, Enum):
    DETECTED_CANDIDATE = "DETECTED_CANDIDATE"


class RecurringIncomeEvidenceState(str, Enum):
    DETECTED_CANDIDATE = "DETECTED_CANDIDATE"
    STALE = "STALE"


class RecurringIncomeDirection(str, Enum):
    CREDIT = "CREDIT"


class RecurringIncomeRiskFlag(str, Enum):
    TRANSFER_AMBIGUITY = "TRANSFER_AMBIGUITY"


@dataclass(frozen=True)
class RecurringIncomeObservation:
    """Private immutable input built from one governed ledger row."""

    source_record_key: str
    provider: str
    account_scope: str
    currency: str
    direction: RecurringIncomeDirection
    description: str
    amount: Decimal
    occurred_on: date
    risk_flags: tuple[RecurringIncomeRiskFlag, ...] = ()

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.source_record_key, "source_record_key"),
            (self.provider, "provider"),
            (self.account_scope, "account_scope"),
            (self.currency, "currency"),
            (self.description, "description"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required.")
        if self.direction is not RecurringIncomeDirection.CREDIT:
            raise ValueError("Recurring-income observations must be credits.")
        if type(self.amount) is not Decimal:
            raise TypeError("Recurring-income amounts must be Decimal.")
        if not self.amount.is_finite() or self.amount <= Decimal("0"):
            raise ValueError("Recurring-income amounts must be positive and finite.")
        if type(self.occurred_on) is not date:
            raise TypeError("occurred_on must be a civil date.")
        if len(set(self.risk_flags)) != len(self.risk_flags):
            raise ValueError("Risk flags must be unique.")


@dataclass(frozen=True)
class MonthlyOccurrenceCount:
    reference_month: str
    occurrence_count: int


@dataclass(frozen=True)
class RecurringIncomeCandidate:
    """Internal candidate evidence; account scope is never a public field."""

    candidate_id: str
    source_signature: str
    signature_version: int
    classification_state: RecurringIncomeCandidateState
    source_provider: str
    source_account_scope: str
    currency: str
    direction: RecurringIncomeDirection
    window_start: date
    window_end: date
    current_month_is_partial: bool
    includes_current_month: bool
    observed_months: tuple[str, ...]
    monthly_occurrences: tuple[MonthlyOccurrenceCount, ...]
    occurrence_count: int
    distinct_month_count: int
    first_occurrence_date: date
    latest_occurrence_date: date
    latest_amount: Decimal
    typical_received_amount: Decimal
    minimum_received_amount: Decimal
    maximum_received_amount: Decimal
    median_absolute_deviation: Decimal | None
    risk_flags: tuple[RecurringIncomeRiskFlag, ...]


def normalize_recurring_description(value: str) -> str:
    """Version-1 normalization: NFKC, case-fold, trim, whitespace collapse."""

    if not isinstance(value, str):
        raise TypeError("Description must be a string.")
    normalized = unicodedata.normalize("NFKC", value).casefold()
    collapsed = " ".join(normalized.split())
    if not collapsed:
        raise ValueError("Description must contain structural identity.")
    return collapsed


def canonical_signature_payload(
    *,
    provider: str,
    account_scope: str,
    currency: str,
    direction: RecurringIncomeDirection,
    normalized_description: str,
) -> str:
    """Return the unambiguous ordered version-1 signature material."""

    values = (
        provider,
        account_scope,
        currency,
        direction.value,
        normalized_description,
    )
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError("Signature components must be non-empty strings.")
    return json.dumps(
        [SIGNATURE_VERSION, *values],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def build_source_signature(
    *,
    provider: str,
    account_scope: str,
    currency: str,
    direction: RecurringIncomeDirection,
    normalized_description: str,
) -> str:
    payload = canonical_signature_payload(
        provider=provider,
        account_scope=account_scope,
        currency=currency,
        direction=direction,
        normalized_description=normalized_description,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_candidate_id(
    source_signature: str,
    *,
    signature_version: int = SIGNATURE_VERSION,
) -> str:
    prefix = "sha256:"
    if not source_signature.startswith(prefix):
        raise ValueError("Source signature must use the SHA-256 form.")
    if type(signature_version) is not int or signature_version < 1:
        raise ValueError("Signature version must be a positive integer.")
    return f"ric_v{signature_version}_{source_signature.removeprefix(prefix)}"


def evidence_window_start(as_of_date: date) -> date:
    if type(as_of_date) is not date:
        raise TypeError("as_of_date must be a civil date.")
    absolute_month = as_of_date.year * 12 + (as_of_date.month - 1)
    start_month = absolute_month - (EVIDENCE_WINDOW_MONTHS - 1)
    return date(start_month // 12, (start_month % 12) + 1, 1)


def _next_month_start(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _decimal_median(values: tuple[Decimal, ...]) -> Decimal:
    ordered = tuple(sorted(values))
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / Decimal("2")


class RecurringIncomeEvidenceEngine:
    """Pure, clock-free recurrence detector over eligible observations."""

    def detect(
        self,
        observations: tuple[RecurringIncomeObservation, ...],
        *,
        as_of_date: date,
    ) -> tuple[RecurringIncomeCandidate, ...]:
        window_start = evidence_window_start(as_of_date)
        grouped: dict[str, list[RecurringIncomeObservation]] = defaultdict(list)

        for observation in observations:
            if not isinstance(observation, RecurringIncomeObservation):
                raise TypeError("The evidence engine accepts immutable observations only.")
            if observation.occurred_on < window_start or observation.occurred_on > as_of_date:
                continue
            normalized_description = normalize_recurring_description(
                observation.description
            )
            signature = build_source_signature(
                provider=observation.provider,
                account_scope=observation.account_scope,
                currency=observation.currency,
                direction=observation.direction,
                normalized_description=normalized_description,
            )
            grouped[signature].append(observation)

        candidates = []
        for signature, group in grouped.items():
            months = Counter(
                occurrence.occurred_on.strftime("%Y-%m") for occurrence in group
            )
            if len(months) < MINIMUM_OBSERVED_MONTHS:
                continue

            ordered_group = tuple(
                sorted(group, key=lambda item: (item.occurred_on, item.source_record_key))
            )
            amounts = tuple(item.amount for item in ordered_group)
            median_amount = _decimal_median(amounts)
            deviations = tuple(abs(amount - median_amount) for amount in amounts)
            mad = _decimal_median(deviations) if len(amounts) >= 3 else None
            latest = ordered_group[-1]
            risk_flags = tuple(
                sorted(
                    {flag for item in ordered_group for flag in item.risk_flags},
                    key=lambda flag: flag.value,
                )
            )
            observed_months = tuple(sorted(months))
            current_reference_month = as_of_date.strftime("%Y-%m")
            candidates.append(
                RecurringIncomeCandidate(
                    candidate_id=build_candidate_id(signature),
                    source_signature=signature,
                    signature_version=SIGNATURE_VERSION,
                    classification_state=(
                        RecurringIncomeCandidateState.DETECTED_CANDIDATE
                    ),
                    source_provider=latest.provider,
                    source_account_scope=latest.account_scope,
                    currency=latest.currency,
                    direction=latest.direction,
                    window_start=window_start,
                    window_end=as_of_date,
                    current_month_is_partial=(
                        as_of_date
                        != _next_month_start(as_of_date) - date.resolution
                    ),
                    includes_current_month=current_reference_month in months,
                    observed_months=observed_months,
                    monthly_occurrences=tuple(
                        MonthlyOccurrenceCount(month, months[month])
                        for month in observed_months
                    ),
                    occurrence_count=len(ordered_group),
                    distinct_month_count=len(months),
                    first_occurrence_date=ordered_group[0].occurred_on,
                    latest_occurrence_date=latest.occurred_on,
                    latest_amount=latest.amount,
                    typical_received_amount=median_amount,
                    minimum_received_amount=min(amounts),
                    maximum_received_amount=max(amounts),
                    median_absolute_deviation=mad,
                    risk_flags=risk_flags,
                )
            )

        return tuple(
            sorted(
                candidates,
                key=lambda candidate: (
                    -candidate.latest_occurrence_date.toordinal(),
                    candidate.source_signature,
                ),
            )
        )
