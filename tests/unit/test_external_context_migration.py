from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import CheckConstraint, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from backend.core.config import settings
from backend.infrastructure.persistence.models.external_context import (
    ExternalObservationVersionModel,
    ExternalSeriesSyncStateModel,
)


PRE_R3D_REVISION = "2d6b4f8a9c1e"
R3D_REVISION = "4f9c2d7e1a6b"


def _config_for(database_path: Path, monkeypatch) -> Config:
    assert "fin_analytics.db" not in database_path.name
    monkeypatch.setattr(
        settings,
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{database_path.as_posix()}",
    )
    return Config("alembic.ini")


def _prepare_previous_head(database_path: Path) -> None:
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": PRE_R3D_REVISION},
        )
    engine.dispose()


def _sample_event_values() -> dict[str, object]:
    return {
        "observation_event_id": "00000000-0000-0000-0000-000000000001",
        "registry_key": "BCB_SGS_SELIC_TARGET",
        "provider": "BCB_SGS",
        "series_id": "432",
        "series_concept": "Interest rate - Selic target",
        "semantic_class": "EXTERNAL_OBSERVATION",
        "reference_period_start": "2026-10-09",
        "reference_period_end": "2026-10-09",
        "value_text": "10.50",
        "value_scale": 2,
        "unit": "PERCENT_PER_YEAR",
        "currency": None,
        "frequency": "DAILY",
        "scope": "BR",
        "registry_contract_version": 1,
        "content_fingerprint_version": 1,
        "content_fingerprint": "sha256:" + "a" * 64,
        "provider_value_text": "10.5",
        "provider_decimal_places": 2,
        "source_url": "https://example.invalid/432",
        "license_id": "ODbL",
        "attribution": "Banco Central do Brasil / SGS",
        "retrieved_at": "2026-10-10T12:00:00.000000Z",
        "observed_at": None,
        "published_at": None,
        "provider_revision_id": None,
        "revised_at": None,
        "ingested_at": "2026-10-10T12:00:01.000000Z",
        "known_from": "2026-10-10T12:00:01.000000Z",
        "knowledge_sequence": 1,
        "supersedes_event_id": None,
    }


def test_r3d_migration_upgrade_downgrade_reupgrade_and_metadata(tmp_path, monkeypatch):
    database_path = tmp_path / "r3d_migration.db"
    _prepare_previous_head(database_path)
    config = _config_for(database_path, monkeypatch)

    command.upgrade(config, R3D_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    inspector = inspect(engine)
    assert {"external_observation_versions", "external_series_sync_state"}.issubset(
        inspector.get_table_names()
    )
    assert {
        table_name
        for table_name in inspector.get_table_names()
        if table_name.startswith("external_")
    } == {"external_observation_versions", "external_series_sync_state"}
    for model in (ExternalObservationVersionModel, ExternalSeriesSyncStateModel):
        database_columns = {
            column["name"]: (str(column["type"]), column["nullable"])
            for column in inspector.get_columns(model.__tablename__)
        }
        metadata_columns = {
            column.name: (str(column.type), column.nullable)
            for column in model.__table__.columns
        }
        assert database_columns == metadata_columns
        assert {
            constraint["name"]
            for constraint in inspector.get_check_constraints(model.__tablename__)
        } == {
            constraint.name
            for constraint in model.__table__.constraints
            if isinstance(constraint, CheckConstraint)
        }
    assert {index["name"] for index in inspector.get_indexes("external_observation_versions")} == {
        "ix_external_observation_identity_head",
        "ix_external_observation_series_as_of",
    }
    assert len(inspector.get_foreign_keys("external_observation_versions")) == 1
    assert len(inspector.get_foreign_keys("external_series_sync_state")) == 1
    with engine.begin() as connection:
        connection.execute(ExternalObservationVersionModel.__table__.insert(), _sample_event_values())
        assert connection.execute(
            text("SELECT typeof(value_text) FROM external_observation_versions")
        ).scalar_one() == "text"
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE external_observation_versions SET value_text = '11.00'")
            )
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM external_observation_versions"))
    engine.dispose()

    command.downgrade(config, PRE_R3D_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert "external_observation_versions" not in inspect(engine).get_table_names()
    assert "external_series_sync_state" not in inspect(engine).get_table_names()
    engine.dispose()

    command.upgrade(config, R3D_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert {"external_observation_versions", "external_series_sync_state"}.issubset(
        inspect(engine).get_table_names()
    )
    assert engine.connect().execute(text("SELECT version_num FROM alembic_version")).scalar_one() == R3D_REVISION
    engine.dispose()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("registry_contract_version", 0),
        ("content_fingerprint_version", 0),
        ("knowledge_sequence", 0),
        ("known_from", "2026-10-10T12:00:02.000000Z"),
    ],
)
def test_r3d_schema_rejects_invalid_storage(tmp_path, monkeypatch, field, value):
    database_path = tmp_path / f"invalid_{field}.db"
    _prepare_previous_head(database_path)
    command.upgrade(_config_for(database_path, monkeypatch), R3D_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    values = _sample_event_values()
    values[field] = value
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(ExternalObservationVersionModel.__table__.insert(), values)
    engine.dispose()
