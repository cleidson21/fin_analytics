"""Caller-transactional SQLAlchemy Core repositories for R3-D."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from backend.domains.external_context import (
    CONTENT_FINGERPRINT_VERSION,
    EXTERNAL_SERIES_REGISTRY_VERSION,
    EconomicIdentity,
    ExternalContextPersistenceError,
    ExternalContextPersistenceErrorCode,
    ExternalObservation,
    ExternalObservationProvenance,
    ExternalSeriesSyncState,
    PersistedObservationEvent,
    Provider,
    RegistryKey,
    SemanticClass,
    SyncAttemptResult,
    build_content_fingerprint_v1,
    decode_utc_timestamp,
    encode_utc_timestamp,
    normalize_external_observation,
    parse_civil_date,
    resolve_series,
    resolve_series_by_key,
    validate_and_normalize_content,
)
from backend.infrastructure.persistence.models.external_context import (
    ExternalObservationVersionModel,
    ExternalSeriesSyncStateModel,
)


def _integrity(message: str, *, field: str | None = None) -> ExternalContextPersistenceError:
    return ExternalContextPersistenceError(
        ExternalContextPersistenceErrorCode.INTEGRITY_VIOLATION,
        message,
        field=field,
    )


def _require_exact_type(row: object, field: str, expected: type, *, nullable: bool = False):
    value = row[field]
    if nullable and value is None:
        return None
    if type(value) is not expected:
        raise _integrity(f"Stored {field} has an invalid SQLite/Python type.", field=field)
    return value


def _validate_event_id(value: object, *, field: str, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if type(value) is not str:
        raise _integrity(f"Stored {field} must be UUID text.", field=field)
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError) as exc:
        raise _integrity(f"Stored {field} is not UUID text.", field=field) from exc
    if str(parsed) != value:
        raise _integrity(f"Stored {field} is not canonical UUID text.", field=field)
    return value


class ExternalObservationRepository:
    """Append-only event storage; the application service owns its transaction."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_head(self, identity: EconomicIdentity) -> PersistedObservationEvent | None:
        table = ExternalObservationVersionModel.__table__
        row = self._db.execute(
            select(table)
            .where(
                table.c.provider == identity.provider.value,
                table.c.series_id == identity.series_id,
                table.c.reference_period_start == identity.reference_period_start.isoformat(),
                table.c.reference_period_end == identity.reference_period_end.isoformat(),
                table.c.semantic_class == identity.semantic_class.value,
            )
            .order_by(table.c.knowledge_sequence.desc())
            .limit(1)
        ).mappings().one_or_none()
        return self._to_certified_event(row) if row is not None else None

    def get_by_id(self, event_id: str) -> PersistedObservationEvent | None:
        table = ExternalObservationVersionModel.__table__
        row = self._db.execute(
            select(table).where(table.c.observation_event_id == event_id)
        ).mappings().one_or_none()
        return self._to_certified_event(row) if row is not None else None

    def list_identity(self, identity: EconomicIdentity) -> tuple[PersistedObservationEvent, ...]:
        table = ExternalObservationVersionModel.__table__
        rows = self._db.execute(
            select(table)
            .where(
                table.c.provider == identity.provider.value,
                table.c.series_id == identity.series_id,
                table.c.reference_period_start == identity.reference_period_start.isoformat(),
                table.c.reference_period_end == identity.reference_period_end.isoformat(),
                table.c.semantic_class == identity.semantic_class.value,
            )
            .order_by(table.c.knowledge_sequence.asc())
        ).mappings()
        return tuple(self._to_certified_event(row) for row in rows)

    def get_identity_as_of(
        self,
        identity: EconomicIdentity,
        *,
        consumer_as_of_date: date,
        consumer_as_of_timestamp,
    ) -> PersistedObservationEvent | None:
        known_cut = encode_utc_timestamp(
            consumer_as_of_timestamp,
            field="consumer_as_of_timestamp",
        )
        if identity.reference_period_end > consumer_as_of_date:
            return None
        table = ExternalObservationVersionModel.__table__
        row = self._db.execute(
            select(table)
            .where(
                table.c.provider == identity.provider.value,
                table.c.series_id == identity.series_id,
                table.c.reference_period_start == identity.reference_period_start.isoformat(),
                table.c.reference_period_end == identity.reference_period_end.isoformat(),
                table.c.semantic_class == identity.semantic_class.value,
                table.c.known_from <= known_cut,
            )
            .order_by(table.c.known_from.desc(), table.c.knowledge_sequence.desc())
            .limit(1)
        ).mappings().one_or_none()
        return self._to_certified_event(row) if row is not None else None

    def get_latest_series_as_of(
        self,
        *,
        provider: Provider,
        series_id: str,
        consumer_as_of_date: date,
        consumer_as_of_timestamp,
    ) -> PersistedObservationEvent | None:
        known_cut = encode_utc_timestamp(
            consumer_as_of_timestamp,
            field="consumer_as_of_timestamp",
        )
        table = ExternalObservationVersionModel.__table__
        row = self._db.execute(
            select(table)
            .where(
                table.c.provider == provider.value,
                table.c.series_id == series_id,
                table.c.reference_period_end <= consumer_as_of_date.isoformat(),
                table.c.known_from <= known_cut,
            )
            .order_by(
                table.c.reference_period_end.desc(),
                table.c.known_from.desc(),
                table.c.knowledge_sequence.desc(),
            )
            .limit(1)
        ).mappings().one_or_none()
        return self._to_certified_event(row) if row is not None else None

    def insert(self, event: PersistedObservationEvent) -> None:
        observation = event.observation
        content = observation.content
        provenance = observation.provenance
        definition = resolve_series_by_key(observation.registry_key)
        self._db.execute(
            insert(ExternalObservationVersionModel.__table__).values(
                observation_event_id=event.observation_event_id,
                registry_key=observation.registry_key.value,
                provider=content.provider.value,
                series_id=content.series_id,
                series_concept=observation.series_concept,
                semantic_class=content.semantic_class.value,
                reference_period_start=content.reference_period.start_text,
                reference_period_end=content.reference_period.end_text,
                value_text=content.value_text,
                value_scale=content.value_scale,
                unit=content.unit.value,
                currency=content.currency,
                frequency=content.frequency.value,
                scope=content.scope.value,
                registry_contract_version=event.registry_contract_version,
                content_fingerprint_version=event.content_fingerprint_version,
                content_fingerprint=event.content_fingerprint,
                provider_value_text=provenance.provider_value_text,
                provider_decimal_places=provenance.provider_decimal_places,
                source_url=provenance.source_url,
                license_id=provenance.license_id,
                attribution=definition.provenance.attribution,
                retrieved_at=encode_utc_timestamp(provenance.retrieved_at, field="retrieved_at"),
                observed_at=(
                    encode_utc_timestamp(provenance.observed_at, field="observed_at")
                    if provenance.observed_at is not None else None
                ),
                published_at=(
                    encode_utc_timestamp(provenance.published_at, field="published_at")
                    if provenance.published_at is not None else None
                ),
                provider_revision_id=provenance.provider_revision_id,
                revised_at=(
                    encode_utc_timestamp(provenance.revised_at, field="revised_at")
                    if provenance.revised_at is not None else None
                ),
                ingested_at=encode_utc_timestamp(event.ingested_at, field="ingested_at"),
                known_from=encode_utc_timestamp(event.known_from, field="known_from"),
                knowledge_sequence=event.knowledge_sequence,
                supersedes_event_id=event.supersedes_event_id,
            )
        )

    @staticmethod
    def _to_certified_event(row: object) -> PersistedObservationEvent:
        event_id = _validate_event_id(row["observation_event_id"], field="observation_event_id")
        registry_version = _require_exact_type(row, "registry_contract_version", int)
        if registry_version != EXTERNAL_SERIES_REGISTRY_VERSION:
            raise ExternalContextPersistenceError(
                ExternalContextPersistenceErrorCode.UNSUPPORTED_REGISTRY_VERSION,
                "The stored observation uses an unsupported registry contract version.",
                field="registry_contract_version",
            )
        fingerprint_version = _require_exact_type(row, "content_fingerprint_version", int)
        if fingerprint_version != CONTENT_FINGERPRINT_VERSION:
            raise _integrity("Unsupported stored fingerprint version.", field="content_fingerprint_version")
        sequence = _require_exact_type(row, "knowledge_sequence", int)
        if sequence < 1:
            raise _integrity("Stored knowledge_sequence must be positive.", field="knowledge_sequence")

        payload = {
            "provider": _require_exact_type(row, "provider", str),
            "series_id": _require_exact_type(row, "series_id", str),
            "reference_period_start": _require_exact_type(row, "reference_period_start", str),
            "reference_period_end": _require_exact_type(row, "reference_period_end", str),
            "semantic_class": _require_exact_type(row, "semantic_class", str),
            "frequency": _require_exact_type(row, "frequency", str),
            "value_text": _require_exact_type(row, "value_text", str),
            "value_scale": _require_exact_type(row, "value_scale", int),
            "unit": _require_exact_type(row, "unit", str),
            "currency": _require_exact_type(row, "currency", str, nullable=True),
            "scope": _require_exact_type(row, "scope", str),
        }
        content = validate_and_normalize_content(payload)
        definition = resolve_series(content.provider, content.series_id)
        registry_key = _require_exact_type(row, "registry_key", str)
        if registry_key != definition.registry_key.value:
            raise _integrity("Stored registry_key does not match the certified series.", field="registry_key")
        series_concept = _require_exact_type(row, "series_concept", str)
        if series_concept != definition.official_concept:
            raise _integrity("Stored series_concept does not match the registry.", field="series_concept")
        source_url = _require_exact_type(row, "source_url", str)
        license_id = _require_exact_type(row, "license_id", str)
        attribution = _require_exact_type(row, "attribution", str)
        if (
            source_url != definition.provenance.source_url
            or license_id != definition.provenance.license_id
            or attribution != definition.provenance.attribution
        ):
            raise _integrity("Stored provenance does not match the registry.", field="source_url")

        raw_payload = dict(payload)
        raw_payload["value_text"] = _require_exact_type(row, "provider_value_text", str)
        observation = normalize_external_observation(
            raw_payload,
            retrieved_at=decode_utc_timestamp(_require_exact_type(row, "retrieved_at", str), field="retrieved_at"),
            observed_at=(
                decode_utc_timestamp(row["observed_at"], field="observed_at")
                if row["observed_at"] is not None else None
            ),
            published_at=(
                decode_utc_timestamp(row["published_at"], field="published_at")
                if row["published_at"] is not None else None
            ),
            provider_revision_id=_require_exact_type(row, "provider_revision_id", str, nullable=True),
            revised_at=(
                decode_utc_timestamp(row["revised_at"], field="revised_at")
                if row["revised_at"] is not None else None
            ),
        )
        if observation.content != content or observation.registry_key.value != registry_key:
            raise _integrity("Stored provider value does not recertify to stored content.")
        recalculated = build_content_fingerprint_v1(content.as_payload_v1())
        stored_fingerprint = _require_exact_type(row, "content_fingerprint", str)
        if recalculated.as_pair() != (fingerprint_version, stored_fingerprint):
            raise ExternalContextPersistenceError(
                ExternalContextPersistenceErrorCode.FINGERPRINT_MISMATCH,
                "Stored content fingerprint does not match certified content.",
                field="content_fingerprint",
            )
        supersedes = _validate_event_id(
            row["supersedes_event_id"],
            field="supersedes_event_id",
            nullable=True,
        )
        ingested = decode_utc_timestamp(_require_exact_type(row, "ingested_at", str), field="ingested_at")
        known = decode_utc_timestamp(_require_exact_type(row, "known_from", str), field="known_from")
        return PersistedObservationEvent(
            observation_event_id=event_id,
            observation=observation,
            registry_contract_version=registry_version,
            content_fingerprint_version=fingerprint_version,
            content_fingerprint=stored_fingerprint,
            ingested_at=ingested,
            known_from=known,
            knowledge_sequence=sequence,
            supersedes_event_id=supersedes,
        )


class ExternalSeriesSyncStateRepository:
    """Mutable bounded operational state; never observation authority."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, registry_key: RegistryKey | str) -> ExternalSeriesSyncState | None:
        key = registry_key.value if isinstance(registry_key, RegistryKey) else registry_key
        table = ExternalSeriesSyncStateModel.__table__
        row = self._db.execute(
            select(table).where(table.c.registry_key == key)
        ).mappings().one_or_none()
        return self._to_domain(row) if row is not None else None

    def initialize(self, registry_key: RegistryKey | str) -> ExternalSeriesSyncState:
        definition = resolve_series_by_key(registry_key)
        state = ExternalSeriesSyncState(
            registry_key=definition.registry_key.value,
            provider=definition.provider.value,
            series_id=definition.series_id,
            registry_contract_version=EXTERNAL_SERIES_REGISTRY_VERSION,
        )
        statement = sqlite_insert(ExternalSeriesSyncStateModel.__table__).values(
            **self._values(state)
        ).on_conflict_do_nothing(index_elements=[ExternalSeriesSyncStateModel.registry_key])
        self._db.execute(statement)
        return self.get(definition.registry_key) or state

    def save(self, state: ExternalSeriesSyncState) -> None:
        definition = resolve_series_by_key(state.registry_key)
        if state.provider != definition.provider.value or state.series_id != definition.series_id:
            raise ValueError("Sync state identity must match the executable registry.")
        values = self._values(state)
        statement = sqlite_insert(ExternalSeriesSyncStateModel.__table__).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[ExternalSeriesSyncStateModel.registry_key],
            set_={key: value for key, value in values.items() if key != "registry_key"},
        )
        self._db.execute(statement)

    @staticmethod
    def _values(state: ExternalSeriesSyncState) -> dict[str, object]:
        return {
            "registry_key": state.registry_key,
            "provider": state.provider,
            "series_id": state.series_id,
            "registry_contract_version": state.registry_contract_version,
            "last_attempt_at": encode_utc_timestamp(state.last_attempt_at, field="last_attempt_at") if state.last_attempt_at else None,
            "last_success_at": encode_utc_timestamp(state.last_success_at, field="last_success_at") if state.last_success_at else None,
            "next_refresh_eligible_at": encode_utc_timestamp(state.next_refresh_eligible_at, field="next_refresh_eligible_at") if state.next_refresh_eligible_at else None,
            "coverage_start": state.coverage_start.isoformat() if state.coverage_start else None,
            "coverage_end": state.coverage_end.isoformat() if state.coverage_end else None,
            "last_attempt_result": state.last_attempt_result.value if state.last_attempt_result else None,
            "partial_coverage": state.partial_coverage,
            "last_error_code": state.last_error_code,
            "last_http_status": state.last_http_status,
            "last_valid_observation_event_id": state.last_valid_observation_event_id,
            "consecutive_retransmissions": state.consecutive_retransmissions,
            "accepted_transitions": state.accepted_transitions,
            "observations_received": state.observations_received,
        }

    @staticmethod
    def _to_domain(row: object) -> ExternalSeriesSyncState:
        definition = resolve_series_by_key(_require_exact_type(row, "registry_key", str))
        provider = _require_exact_type(row, "provider", str)
        series_id = _require_exact_type(row, "series_id", str)
        if provider != definition.provider.value or series_id != definition.series_id:
            raise _integrity("Stored sync identity does not match the registry.")
        return ExternalSeriesSyncState(
            registry_key=definition.registry_key.value,
            provider=provider,
            series_id=series_id,
            registry_contract_version=_require_exact_type(row, "registry_contract_version", int),
            last_attempt_at=decode_utc_timestamp(row["last_attempt_at"], field="last_attempt_at") if row["last_attempt_at"] is not None else None,
            last_success_at=decode_utc_timestamp(row["last_success_at"], field="last_success_at") if row["last_success_at"] is not None else None,
            next_refresh_eligible_at=decode_utc_timestamp(row["next_refresh_eligible_at"], field="next_refresh_eligible_at") if row["next_refresh_eligible_at"] is not None else None,
            coverage_start=parse_civil_date(row["coverage_start"], field_name="coverage_start") if row["coverage_start"] is not None else None,
            coverage_end=parse_civil_date(row["coverage_end"], field_name="coverage_end") if row["coverage_end"] is not None else None,
            last_attempt_result=SyncAttemptResult(row["last_attempt_result"]) if row["last_attempt_result"] is not None else None,
            partial_coverage=bool(_require_exact_type(row, "partial_coverage", bool)),
            last_error_code=_require_exact_type(row, "last_error_code", str, nullable=True),
            last_http_status=_require_exact_type(row, "last_http_status", int, nullable=True),
            last_valid_observation_event_id=_validate_event_id(row["last_valid_observation_event_id"], field="last_valid_observation_event_id", nullable=True),
            consecutive_retransmissions=_require_exact_type(row, "consecutive_retransmissions", int),
            accepted_transitions=_require_exact_type(row, "accepted_transitions", int),
            observations_received=_require_exact_type(row, "observations_received", int),
        )
