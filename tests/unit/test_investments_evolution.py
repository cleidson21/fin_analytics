import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.database import get_db_session
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.domain.enums.user_role import UserRole
from backend.infrastructure.persistence.models.wealth.portfolio_snapshot import PortfolioSnapshotModel
from datetime import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

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

def test_investments_evolution_summary(client, mock_session):
    # Mock para o latest snapshot (stmt_latest)
    snap = PortfolioSnapshotModel(
        account_id=test_user_id,
        reference_month="2026-01",
        patrimonio=50000.0,
        pct_mensal=0.02,
        pct_acumulada=0.02,
        compras=1000.0,
        vendas=0.0,
        proventos=100.0,
        ibov_mensal=0.01,
        ibov_acumulado=0.01
    )
    
    class MockSums:
        total_dividends = 100.0
        total_compras = 1000.0
        total_vendas = 0.0

    # O endpoint faz 2 executes para o summary
    mock_session.execute.side_effect = [
        MockResult([snap]),        # 1. latest_snapshot
        MockResult([MockSums()])   # 2. sums
    ]

    response = client.get("/api/v1/investments/evolution/summary")
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_wealth"] == 50000.0
    assert data["accumulated_return_pct"] == 2.0  # 0.02 * 100
    assert data["total_dividends"] == 100.0
    assert data["total_invested"] == 1000.0  # compras - vendas
    assert data["ibov_acumulado"] == 1.0     # 0.01 * 100
    assert data["alpha_vs_ibov"] == 1.0      # 2.0 - 1.0
    assert data["alpha_vs_cdi"] == 2.0       # 2.0 - 0.0

def test_investments_evolution_history(client, mock_session):
    snap1 = PortfolioSnapshotModel(
        account_id=test_user_id,
        reference_month="2026-01",
        patrimonio=50000.0,
    )
    snap2 = PortfolioSnapshotModel(
        account_id=test_user_id,
        reference_month="2026-02",
        patrimonio=52000.0,
    )
    
    mock_session.execute.side_effect = [
        MockResult([snap1, snap2])
    ]

    response = client.get("/api/v1/investments/evolution/history")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert data[0]["month"] == "2026-01"
    assert data[1]["month"] == "2026-02"
    assert data[0]["patrimonio_value"] == 50000.0
    assert data[1]["patrimonio_value"] == 52000.0
