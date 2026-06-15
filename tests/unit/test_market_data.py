import pytest
from unittest.mock import patch, MagicMock
from app.api.services.market_data import format_ticker_for_yf, get_asset_history, get_asset_indicators

def test_format_ticker():
    assert format_ticker_for_yf("PETR4") == "PETR4.SA"
    assert format_ticker_for_yf("BTC") == "BTC-USD"
    assert format_ticker_for_yf("TESOURO SELIC") == ""

@patch("app.api.services.market_data._get_cache")
@patch("app.api.services.market_data._set_cache")
@patch("app.api.services.market_data.yf")
def test_get_asset_history(mock_yf, mock_set_cache, mock_get_cache):
    mock_get_cache.return_value = None
    
    mock_ticker = MagicMock()
    # Mocking pandas DataFrame returned by yf history
    import pandas as pd
    mock_hist = pd.DataFrame({"Close": [10.0, 11.0]}, index=pd.to_datetime(["2026-06-01", "2026-06-02"]))
    mock_ticker.history.return_value = mock_hist
    mock_yf.Ticker.return_value = mock_ticker

    history = get_asset_history("PETR4")
    assert history["available"] is True
    assert len(history["history"]) == 2

@patch("app.api.services.market_data._get_cache")
@patch("app.api.services.market_data._set_cache")
@patch("app.api.services.market_data.yf")
def test_get_asset_indicators(mock_yf, mock_set_cache, mock_get_cache):
    mock_get_cache.return_value = None
    
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "dividendYield": 0.05,
        "trailingPE": 10.5,
        "priceToBook": 1.2,
        "returnOnEquity": 0.15,
        "sector": "Energy",
        "someOtherField": 123
    }
    mock_yf.Ticker.return_value = mock_ticker

    indicators = get_asset_indicators("PETR4")
    assert indicators["available"] is True
    assert "Dividend Yield" in indicators["indicators"]
    assert "P/L" in indicators["indicators"]
