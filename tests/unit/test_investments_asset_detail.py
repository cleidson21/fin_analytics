import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from backend.main import app
from fastapi.testclient import TestClient
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.infrastructure.persistence.models.wealth.asset import AssetModel
from backend.infrastructure.persistence.models.wealth.position_snapshot import PositionSnapshotModel
from backend.integrations.market_data.models import MarketQuote

client = TestClient(app)

from backend.domain.enums.user_role import UserRole

def mock_user():
    return UserResponseDTO(
        id="user-123", 
        email="test@test.com", 
        name="Test", 
        role=UserRole.VIEWER, 
        is_active=True, 
        is_verified=True,
        created_at=datetime.utcnow(),
        last_login_at=None
    )

def test_get_asset_detail_unauthorized():
    response = client.get("/api/v1/investments/asset/PETR4")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_asset_detail_not_found():
    from backend.api.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_user
    
    class MockSession:
        async def execute(self, stmt):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            return mock_result
            
    from backend.api.dependencies.database import get_db_session
    app.dependency_overrides[get_db_session] = lambda: MockSession()
    
    response = client.get("/api/v1/investments/asset/UNKNOWN")
    assert response.status_code == 404
    assert "Ativo não encontrado" in response.json()["detail"]
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_asset_detail_success_with_governance_value():
    from backend.api.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_user
    
    mock_asset = MagicMock(id=1, ticker="ITUB4", asset_class="STOCK", user_id="user-123")
    mock_pos = MagicMock(asset_id=1, quantity=100, avg_price=20.0, current_value=2500.0)
    
    class MockSession:
        def __init__(self):
            self.call_count = 0
            
        async def execute(self, stmt):
            self.call_count += 1
            mock_result = MagicMock()
            
            if self.call_count == 1:
                # Asset
                mock_result.scalar_one_or_none.return_value = mock_asset
            elif self.call_count == 2:
                # Position
                mock_result.scalar_one_or_none.return_value = mock_pos
            elif self.call_count == 3:
                # Portfolio (total wealth)
                mock_result.scalar_one_or_none.return_value = 10000.0
            elif self.call_count == 4:
                # Income Events
                mock_result.scalars.return_value.all.return_value = []
                
            return mock_result

    from backend.api.dependencies.database import get_db_session
    app.dependency_overrides[get_db_session] = lambda: MockSession()
    
    response = client.get("/api/v1/investments/asset/ITUB4")
    assert response.status_code == 200
    data = response.json()
    
    assert data["position"]["ticker"] == "ITUB4"
    assert data["position"]["quantidade"] == 100
    assert data["position"]["valor_investido"] == 2000.0
    assert data["position"]["valor_atual"] == 2500.0
    assert data["position"]["ganho"] == 500.0
    assert data["position"]["peso"] == 25.0 # 2500 / 10000 * 100
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_asset_detail_success_with_market_data():
    from backend.api.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_user
    
    mock_asset = MagicMock(id=1, ticker="PETR4", asset_class="STOCK", user_id="user-123")
    # current_value is None, should trigger Market Data
    mock_pos = MagicMock(asset_id=1, quantity=100, avg_price=10.0, current_value=None)
    
    class MockSession:
        def __init__(self):
            self.call_count = 0
            
        async def execute(self, stmt):
            self.call_count += 1
            mock_result = MagicMock()
            
            if self.call_count == 1:
                mock_result.scalar_one_or_none.return_value = mock_asset
            elif self.call_count == 2:
                mock_result.scalar_one_or_none.return_value = mock_pos
            elif self.call_count == 3:
                mock_result.scalar_one_or_none.return_value = 10000.0
            elif self.call_count == 4:
                mock_result.scalars.return_value.all.return_value = []
                
            return mock_result

    from backend.api.dependencies.database import get_db_session
    app.dependency_overrides[get_db_session] = lambda: MockSession()
    
    with patch("backend.api.routers.investments.market_data_service") as mock_market_data:
        mock_market_data.get_quote.return_value = MarketQuote(
            provider="YFINANCE", source_ticker="PETR4.SA", price=Decimal("15.0"), timestamp=datetime.utcnow(), price_date=None
        )
        mock_market_data.get_history.return_value = [{"date": "2023-01-01", "close": 14.5}]
        
        response = client.get("/api/v1/investments/asset/PETR4")
        assert response.status_code == 200
        data = response.json()
        
        assert data["position"]["valor_atual"] == 1500.0
        assert data["position"]["ganho"] == 500.0
        assert data["market_data"]["available"] == True
        assert len(data["market_data"]["history"]) == 1
        
    app.dependency_overrides.clear()
