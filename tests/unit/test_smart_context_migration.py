from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import CheckConstraint, create_engine, inspect, text

from backend.core.config import settings
from backend.infrastructure.persistence.models.smart_context import (
    DeclaredFinancialContextModel,
    RecurringIncomeDecisionModel,
)


PRE_B1_REVISION = "f2915371d283"
B1_REVISION = "2d6b4f8a9c1e"


def _config_for(database_path: Path, monkeypatch) -> Config:
    monkeypatch.setattr(
        settings,
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{database_path.as_posix()}",
    )
    return Config("alembic.ini")


def _prepare_pre_b1_database(database_path: Path) -> None:
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE users ("
                "id CHAR(32) NOT NULL PRIMARY KEY, "
                "email VARCHAR(255) NOT NULL UNIQUE, "
                "name VARCHAR(255) NOT NULL, "
                "hashed_password VARCHAR(255) NOT NULL, "
                "is_active BOOLEAN NOT NULL, "
                "is_verified BOOLEAN NOT NULL, "
                "role VARCHAR(50) NOT NULL, "
                "created_at DATETIME NOT NULL, "
                "last_login_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE alembic_version ("
                "version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
            )
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": PRE_B1_REVISION},
        )
    engine.dispose()


def test_b1_migration_upgrade_downgrade_and_metadata_sync(tmp_path, monkeypatch):
    database_path = tmp_path / "smart_context_migration.db"
    _prepare_pre_b1_database(database_path)
    config = _config_for(database_path, monkeypatch)

    command.upgrade(config, B1_REVISION)

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    inspector = inspect(engine)
    assert {
        "user_declared_financial_context",
        "recurring_income_decisions",
    }.issubset(inspector.get_table_names())
    assert "recurring_income_candidates" not in inspector.get_table_names()
    for model in (DeclaredFinancialContextModel, RecurringIncomeDecisionModel):
        database_columns = {
            column["name"]: (str(column["type"]), column["nullable"])
            for column in inspector.get_columns(model.__tablename__)
        }
        metadata_columns = {
            column.name: (str(column.type), column.nullable)
            for column in model.__table__.columns
        }
        assert database_columns == metadata_columns
        database_checks = {
            constraint["name"]
            for constraint in inspector.get_check_constraints(model.__tablename__)
        }
        metadata_checks = {
            constraint.name
            for constraint in model.__table__.constraints
            if isinstance(constraint, CheckConstraint)
        }
        assert database_checks == metadata_checks
        assert inspector.get_pk_constraint(model.__tablename__)["constrained_columns"] == [
            column.name for column in model.__table__.primary_key.columns
        ]
    assert {
        tuple(unique["column_names"])
        for unique in inspector.get_unique_constraints("recurring_income_decisions")
    } == {("user_id", "source_signature", "signature_version")}
    assert {
        tuple(index["column_names"])
        for index in inspector.get_indexes("recurring_income_decisions")
    } == {("user_id",)}
    assert len(inspector.get_foreign_keys("user_declared_financial_context")) == 1
    assert len(inspector.get_foreign_keys("recurring_income_decisions")) == 1
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == B1_REVISION
    engine.dispose()

    command.downgrade(config, PRE_B1_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert "user_declared_financial_context" not in inspect(engine).get_table_names()
    assert "recurring_income_decisions" not in inspect(engine).get_table_names()
    engine.dispose()

    command.upgrade(config, B1_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert {
        "user_declared_financial_context",
        "recurring_income_decisions",
    }.issubset(inspect(engine).get_table_names())
    engine.dispose()
