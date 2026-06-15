import json
from database.financial_repository import FinancialRepository
import re
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional

try:
    import yfinance as yf
except ImportError:
    yf = None

logger = logging.getLogger(__name__)

from database.config import DATABASE_PATH
DB_PATH = str(DATABASE_PATH)

def get_db_connection():
    return FinancialRepository()._get_connection()

def format_ticker_for_yf(ticker: str) -> str:
    """Format the ticker symbol for yfinance."""
    if not ticker:
        return ""
    
    ticker_upper = ticker.upper().strip()
    
    # Renda fixa ou Tesouro (has spaces, skip yf completely to save time)
    if " " in ticker_upper or "TESOURO" in ticker_upper or "RDB" in ticker_upper or "CDB" in ticker_upper:
        return ""
        
    # Crypto
    if ticker_upper == "BTC":
        return "BTC-USD"
    if ticker_upper == "ETH":
        return "ETH-USD"
        
    # Brazilian Stocks/FIIs (e.g. PETR4, TAEE11)
    if re.match(r"^[A-Z]{4}[0-9]{1,2}$", ticker_upper):
        return f"{ticker_upper}.SA"
        
    return ticker_upper

def _get_cache(ticker: str, cache_type: str, max_age_hours: int) -> Optional[Dict[str, Any]]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT payload_json, updated_at FROM market_cache WHERE ticker = ? AND cache_type = ?",
                (ticker, cache_type)
            )
            row = cursor.fetchone()
            if row:
                payload, updated_at_str = row
                updated_at = datetime.fromisoformat(updated_at_str)
                if datetime.now() - updated_at < timedelta(hours=max_age_hours):
                    return json.loads(payload)
    except Exception as e:
        logger.error(f"Error reading cache for {ticker} {cache_type}: {e}")
    return None

def _set_cache(ticker: str, cache_type: str, payload: Dict[str, Any]):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO market_cache (ticker, cache_type, payload_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(ticker, cache_type) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    updated_at=excluded.updated_at
                """,
                (ticker, cache_type, json.dumps(payload), datetime.now().isoformat())
            )
    except Exception as e:
        logger.error(f"Error writing cache for {ticker} {cache_type}: {e}")

def get_asset_history(ticker: str) -> Dict[str, Any]:
    """
    Returns 1mo, 6mo, 1y, 5y history points for the asset.
    Cache expires in 24 hours.
    """
    cache_data = _get_cache(ticker, "PRICE_HISTORY", max_age_hours=24)
    if cache_data is not None:
        return cache_data
        
    yf_ticker = format_ticker_for_yf(ticker)
    result = {"available": False, "history": {}}
    
    if not yf_ticker or not yf:
        _set_cache(ticker, "PRICE_HISTORY", result)
        return result
        
    try:
        asset = yf.Ticker(yf_ticker)
        # Fetching multiple periods efficiently
        hist = asset.history(period="5y")
        if not hist.empty:
            result["available"] = True
            history_data = []
            for date, row in hist.iterrows():
                history_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "close": float(row["Close"])
                })
            result["history"] = history_data
    except Exception as e:
        logger.warning(f"Failed to fetch history from yf for {yf_ticker}: {e}")
        
    _set_cache(ticker, "PRICE_HISTORY", result)
    return result

def get_asset_indicators(ticker: str) -> Dict[str, Any]:
    """
    Returns P/L, P/VP, ROE, DY etc.
    Cache expires in 7 days (168 hours).
    """
    cache_data = _get_cache(ticker, "INDICATORS", max_age_hours=168)
    if cache_data is not None:
        return cache_data
        
    yf_ticker = format_ticker_for_yf(ticker)
    result = {"available": False, "indicators": {}}
    
    if not yf_ticker or not yf:
        _set_cache(ticker, "INDICATORS", result)
        return result
        
    try:
        asset = yf.Ticker(yf_ticker)
        info = asset.info
        
        if info and len(info.keys()) > 5:
            result["available"] = True
            indicators = {}
            
            # DY
            dy = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
            if dy is not None:
                indicators["Dividend Yield"] = f"{dy * 100:.2f}%"
                
            # P/L (PE Ratio)
            pe = info.get("trailingPE")
            if pe is not None:
                indicators["P/L"] = f"{pe:.2f}"
                
            # P/VP (Price to Book)
            pb = info.get("priceToBook")
            if pb is not None:
                indicators["P/VP"] = f"{pb:.2f}"
                
            # ROE
            roe = info.get("returnOnEquity")
            if roe is not None:
                indicators["ROE"] = f"{roe * 100:.2f}%"
                
            # Sector/Industry
            sector = info.get("sector")
            if sector:
                indicators["Setor"] = sector
                
            result["indicators"] = indicators
            
    except Exception as e:
        logger.warning(f"Failed to fetch indicators from yf for {yf_ticker}: {e}")
        
    _set_cache(ticker, "INDICATORS", result)
    return result
