import pytest
from backend.core.config import settings
from backend.database.engine import engine

def test_settings_loaded():
    assert settings.ENVIRONMENT == "development"
    assert "sqlite" in settings.DATABASE_URL

def test_engine_created():
    assert engine is not None
    assert engine.url.database is not None
