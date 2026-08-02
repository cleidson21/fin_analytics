import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal

from backend.domains.market_data.interfaces import AssetQuote
from backend.domains.market_data.service import MarketDataService

class TestMarketDataService(unittest.TestCase):
    def setUp(self):
        self.provider = MagicMock()
        self.provider.get_name.return_value = "YFINANCE"
        
        self.repo = MagicMock()
        self.portfolio_service = MagicMock()
        
        self.service = MarketDataService(self.provider, self.repo, self.portfolio_service)
        
    def test_update_market_data(self):
        # Mock active tickers
        session = MagicMock(spec=Session)
        
        # We patch the internal methods that query DB to avoid needing a real DB
        self.service._get_active_tickers = MagicMock(return_value=["PETR4", "VALE3"])
        
        # Mock provider fetch
        quotes = [
            AssetQuote(ticker="PETR4", date=date.today(), close_price=Decimal("35.00"), source="YFINANCE"),
            AssetQuote(ticker="VALE3", date=date.today(), close_price=Decimal("65.00"), source="YFINANCE")
        ]
        self.provider.fetch_current_prices.return_value = quotes
        
        self.repo.save_prices.return_value = 2
        
        # Patch the actual repo instantiations inside the service to avoid errors
        with patch('backend.domains.investments.repositories.trade_repository.TradeRepository'), \
             patch('backend.domains.investments.repositories.snapshot_repository.SnapshotRepository'):
             
            result = self.service.update_market_data(session)
            
        # Asserts
        self.provider.fetch_current_prices.assert_called_once_with(["PETR4", "VALE3"])
        self.repo.save_prices.assert_called_once_with(session, quotes)
        self.portfolio_service.get_current_portfolio.assert_called_once()
        
        # Verify kwargs sent to get_current_portfolio contains the correct market_prices map
        args, kwargs = self.portfolio_service.get_current_portfolio.call_args
        self.assertIn("market_prices", kwargs)
        self.assertEqual(kwargs["market_prices"], {"PETR4": Decimal("35.00"), "VALE3": Decimal("65.00")})
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tickers_fetched"], 2)
        self.assertEqual(result["prices_saved"], 2)

if __name__ == '__main__':
    unittest.main()
