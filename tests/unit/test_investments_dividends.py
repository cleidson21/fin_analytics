import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.database import get_db_session
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.domain.enums.user_role import UserRole
from backend.infrastructure.persistence.models.wealth.income_event import IncomeEventModel
from datetime import datetime, date
import uuid
from unittest.mock import AsyncMock

test_user_id = str(uuid.uuid4())
mock_user = UserResponseDTO(
    id=uuid.UUID(test_user_id),
    email="test@test.com",
    name="Test User",
    role=UserRole.ADMIN,
    is_active=True,
    is_verified=True,
    created_at=datetime.utcnow(),
    last_login_at=None
)

async def mock_get_current_user():
    return mock_user

class MockResult:
    def __init__(self, items, is_scalar=False):
        self.items = items
        self.is_scalar = is_scalar
        
    def scalar_one_or_none(self):
        return self.items[0] if self.items else None
        
    def fetchone(self):
        if not self.items:
            return None
        return self.items[0]
        
    def all(self):
        return self.items

    def scalars(self):
        class MockScalars:
            def __init__(self, data):
                self.data = data
            def all(self):
                return self.data
        return MockScalars(self.items)

@pytest.fixture
def test_user():
    return {"id": test_user_id}

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def client(mock_session):
    async def get_mock_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db_session] = get_mock_db
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()

def test_investments_dividends_history(client, mock_session):
    mock_session.execute.side_effect = [
        MockResult([
            IncomeEventModel(payment_date=date(2026, 8, 15), gross_amount=50.0, event_type="DIVIDENDO"),
            IncomeEventModel(payment_date=date(2026, 8, 20), gross_amount=25.0, event_type="JCP")
        ])
    ]

    response = client.get("/api/v1/investments/dividends/history")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert data[0]["valor"] == 50.0
    assert data[0]["tipo_evento"] == "DIVIDENDO"
    assert data[1]["valor"] == 25.0
    assert data[1]["tipo_evento"] == "JCP"

def test_investments_dividends_breakdown(client, mock_session):
    mock_session.execute.side_effect = [
        MockResult([
            ("PETR4", 500.0),
            ("VALE3", 200.0)
        ])
    ]

    response = client.get("/api/v1/investments/dividends/breakdown")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert data[0]["ticker"] == "PETR4"
    assert data[0]["total_received"] == 500.0
    assert data[1]["ticker"] == "VALE3"
    assert data[1]["total_received"] == 200.0
