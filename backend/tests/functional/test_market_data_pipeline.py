import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import date
import pandas as pd
import sys
import unittest.mock as mock

# Fake yfinance module to bypass import error
fake_yf = mock.MagicMock()
sys.modules['yfinance'] = fake_yf

from backend.domains.market_data.providers.yahoo_finance import YahooFinanceProvider
from backend.domains.market_data.cache import market_data_cache
from backend.domains.market_data.interfaces import AssetQuote
from backend.domains.market_data.config import MarketDataConfig

class TestYahooFinanceProvider(unittest.TestCase):
    def setUp(self):
        market_data_cache.clear()
        self.provider = YahooFinanceProvider()

    @patch('backend.domains.market_data.providers.yahoo_finance.yf.download')
    def test_fetch_valid_asset(self, mock_download):
        # Mock yfinance return
        df = pd.DataFrame({
            'Open': [10.0],
            'High': [11.0],
            'Low': [9.0],
            'Close': [10.5],
            'Adj Close': [10.5],
            'Volume': [1000]
        }, index=pd.to_datetime(['2026-07-15']))
        df.index.name = 'Date'
        # For a single ticker, yf.download returns a flat DataFrame
        mock_download.return_value = df

        quotes = self.provider.fetch_current_prices(["PETR4"])
        
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0].ticker, "PETR4")
        self.assertEqual(quotes[0].close_price, Decimal("10.5"))
        self.assertTrue(mock_download.called)

    @patch('backend.domains.market_data.providers.yahoo_finance.yf.download')
    def test_cache_hit(self, mock_download):
        # First call hits network
        df = pd.DataFrame({
            'Open': [10.0],
            'High': [11.0],
            'Low': [9.0],
            'Close': [10.5],
            'Adj Close': [10.5],
            'Volume': [1000]
        }, index=pd.to_datetime(['2026-07-15']))
        df.index.name = 'Date'
        mock_download.return_value = df

        self.provider.fetch_current_prices(["PETR4"])
        self.assertEqual(mock_download.call_count, 1)

        # Second call should hit cache
        quotes = self.provider.fetch_current_prices(["PETR4"])
        self.assertEqual(len(quotes), 1)
        self.assertEqual(mock_download.call_count, 1) # Network NOT called again

    @patch('backend.domains.market_data.providers.yahoo_finance.yf.download')
    def test_invalid_asset(self, mock_download):
        # Return empty DataFrame for invalid ticker
        mock_download.return_value = pd.DataFrame()

        quotes = self.provider.fetch_current_prices(["INVALID"])
        self.assertEqual(len(quotes), 0)

    @patch('backend.domains.market_data.providers.yahoo_finance.yf.download')
    def test_no_internet_timeout(self, mock_download):
        mock_download.side_effect = Exception("Connection Error")
        
        quotes = self.provider.fetch_current_prices(["PETR4"])
        self.assertEqual(len(quotes), 0) # Should fail gracefully

    def test_cache_ttl_and_stats(self):
        market_data_cache.set("test_key", "value", ttl=-1) # Already expired
        val = market_data_cache.get("test_key")
        self.assertIsNone(val)
        
        market_data_cache.set("test_key2", "value", ttl=10) # Valid
        val2 = market_data_cache.get("test_key2")
        self.assertEqual(val2, "value")

if __name__ == '__main__':
    unittest.main()
