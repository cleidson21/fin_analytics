import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import time

# Mock yfinance to prevent import errors in the provider package
sys.modules['yfinance'] = MagicMock()

from datetime import date
from backend.domains.market_data.providers.banco_central import BCProvider
from backend.domains.market_data.macro_service import MacroIndicatorsService, MacroIndicatorsCache
from backend.domains.market_data.interfaces import AssetQuote

class TestMacroIndicators(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock(spec=BCProvider)
        self.mock_repo = MagicMock()
        self.service = MacroIndicatorsService(self.mock_provider, self.mock_repo, cache_ttl=10)
        self.mock_session = MagicMock()

    def test_cache_hit_and_miss(self):
        # Setup
        mock_data = [{"indicator_type": "SELIC", "value": 10.5, "date": "2026-07-15"}]
        self.mock_repo.get_latest_indicators.return_value = mock_data
        
        # Act 1: Cache Miss
        result_miss = self.service.get_latest_indicators(self.mock_session)
        self.assertEqual(result_miss, mock_data)
        self.mock_repo.get_latest_indicators.assert_called_once()
        
        # Act 2: Cache Hit
        self.mock_repo.get_latest_indicators.reset_mock()
        result_hit = self.service.get_latest_indicators(self.mock_session)
        self.assertEqual(result_hit, mock_data)
        self.mock_repo.get_latest_indicators.assert_not_called()
        
    def test_provider_unavailable_fallback(self):
        # Setup
        self.mock_provider.fetch_current_prices.side_effect = Exception("BCB API Timeout")
        
        # Act
        result = self.service.update_indicators(self.mock_session)
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "BCB unavailable")
        self.mock_repo.save_indicators.assert_not_called()

    def test_update_daily_persistence(self):
        # Setup
        self.mock_provider.fetch_current_prices.return_value = [
            AssetQuote(ticker="SELIC", date=date.today(), close_price=10.5, source="SGS"),
            AssetQuote(ticker="CDI", date=date.today(), close_price=10.4, source="SGS")
        ]
        self.mock_repo.save_indicators.return_value = 2
        
        # Act
        result = self.service.update_indicators(self.mock_session)
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["indicators_saved"], 2)
        self.mock_repo.save_indicators.assert_called_once()
        
        # Check cache is populated after sync
        cached = self.service.cache.get("latest_indicators")
        self.assertEqual(len(cached), 2)
        self.assertEqual(cached[0]["indicator_type"], "SELIC")

if __name__ == '__main__':
    unittest.main()
