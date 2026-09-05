import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from backend.integrations.market_data.models import MarketQuote
from backend.integrations.yfinance.yfinance_provider import YFinanceProvider
from backend.application.services.market_data_service import MarketDataService

class TestYFinanceProvider:
    def test_normalize_ticker(self):
        provider = YFinanceProvider()
        
        # Brasil
        assert provider._normalize_ticker("PETR4", "STOCK") == "PETR4.SA"
        assert provider._normalize_ticker("KNCR11", "FII") == "KNCR11.SA"
        
        # Crypto
        assert provider._normalize_ticker("BTC", "CRYPTO") == "BTC-USD"
        
        # ETF Global
        assert provider._normalize_ticker("IVV", "ETF_GLOBAL") == "IVV"
        
        # BDR
        assert provider._normalize_ticker("BABA34", "BDR") == "BABA34.SA"
        assert provider._normalize_ticker("BABA", "BDR") == "BABA"
        
        # Renda Fixa & Outros
        assert provider._normalize_ticker("RDB", "FIXED_INCOME") is None
        assert provider._normalize_ticker("FIDC", "OTHER") is None

    @patch("backend.integrations.yfinance.yfinance_provider.yf.Ticker")
    def test_get_quote_valid(self, mock_ticker):
        # Mock yf response
        import pandas as pd
        
        mock_hist = pd.DataFrame({"Close": [10.5]})
        # Add timezone to match yfinance output
        mock_hist.index = [pd.Timestamp(datetime.utcnow(), tz='UTC')]
        
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_instance
        
        provider = YFinanceProvider()
        quote = provider.get_quote("PETR4", "STOCK")
        
        assert quote is not None
        assert quote.provider == "YFINANCE"
        assert quote.source_ticker == "PETR4.SA"
        assert quote.price == Decimal("10.5")
        
    @patch("backend.integrations.yfinance.yfinance_provider.yf.Ticker")
    def test_get_quote_empty(self, mock_ticker):
        import pandas as pd
        mock_hist = pd.DataFrame()
        
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_instance
        
        provider = YFinanceProvider()
        quote = provider.get_quote("INVALID", "STOCK")
        assert quote is None

class TestMarketDataService:
    def test_cache_hits_and_misses(self):
        mock_provider = MagicMock()
        mock_provider.get_quote.return_value = MarketQuote(
            provider="MOCK",
            source_ticker="PETR4.SA",
            price=Decimal("20.0"),
            price_date=None,
            timestamp=datetime.utcnow()
        )
        
        service = MarketDataService(provider=mock_provider, ttl_minutes=15)
        
        # 1. Primeira chamada vai pro provider
        quote1 = service.get_quote("PETR4", "STOCK")
        assert quote1 is not None
        assert mock_provider.get_quote.call_count == 1
        
        # 2. Segunda chamada usa cache
        quote2 = service.get_quote("PETR4", "STOCK")
        assert quote2 is not None
        assert mock_provider.get_quote.call_count == 1
        
        # 3. Força expiração do cache
        cache_key = "PETR4_STOCK"
        service._cache[cache_key]["expires_at"] = datetime.utcnow() - timedelta(minutes=1)
        
        # 4. Terceira chamada vai pro provider
        quote3 = service.get_quote("PETR4", "STOCK")
        assert quote3 is not None
        assert mock_provider.get_quote.call_count == 2
