import yfinance as yf
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from decimal import Decimal
import logging
import pandas as pd

from backend.domains.market_data.interfaces import MarketDataProvider, AssetQuote
from backend.domains.market_data.config import MarketDataConfig
from backend.domains.market_data.cache import market_data_cache

logger = logging.getLogger(__name__)

class YahooFinanceProvider(MarketDataProvider):
    def __init__(self):
        self.settings = MarketDataConfig.get_provider_settings("yahoo_finance")
        # Ensure correct B3 suffix for Brazilian assets if needed, but the caller should pass correct tickers
        
    def get_name(self) -> str:
        return "YFINANCE"
        
    def _format_ticker(self, ticker: str) -> str:
        """Adiciona .SA para ativos brasileiros se não possuir, exceto índices conhecidos."""
        # Simple heuristic, assumes caller passes B3 tickers without .SA mostly, 
        # but yfinance requires .SA for B3. We check if it's already an index like ^BVSP
        if ticker.startswith('^') or ticker.endswith('.SA') or ticker.endswith('.US'):
            return ticker
        # Assuming default B3 for standard 4-6 chars alphanumeric without suffix
        if len(ticker) <= 6 and ticker.isalnum():
            return f"{ticker}.SA"
        return ticker
        
    def fetch_current_prices(self, tickers: List[str]) -> List[AssetQuote]:
        quotes = []
        tickers_to_fetch = []
        formatted_map = {}
        
        # Check cache first
        for t in tickers:
            formatted_t = self._format_ticker(t)
            formatted_map[formatted_t] = t
            
            cache_key = f"yfinance_current_price_{formatted_t}"
            cached_quote = market_data_cache.get(cache_key)
            if cached_quote:
                quotes.append(cached_quote)
            else:
                tickers_to_fetch.append(formatted_t)
                
        if not tickers_to_fetch:
            return quotes
            
        try:
            # Batch download
            data = yf.download(
                tickers_to_fetch, 
                period="1d", 
                group_by="ticker", 
                threads=True,
                progress=False
            )
            
            # yfinance returns different shapes if 1 ticker vs multiple
            if len(tickers_to_fetch) == 1:
                t = tickers_to_fetch[0]
                self._process_single_ticker_data(t, formatted_map[t], data, quotes)
            else:
                for t in tickers_to_fetch:
                    if t in data:
                        ticker_data = data[t]
                        self._process_single_ticker_data(t, formatted_map[t], ticker_data, quotes)
        except Exception as e:
            logger.error(f"Error fetching prices from YFinance: {e}")
            
        return quotes

    def _process_single_ticker_data(self, formatted_t: str, original_t: str, data: pd.DataFrame, quotes: List[AssetQuote]):
        if data.empty:
            return
            
        latest = data.iloc[-1]
        if pd.isna(latest.get('Close')):
            return
            
        quote = AssetQuote(
            ticker=original_t,
            date=latest.name.date() if isinstance(latest.name, pd.Timestamp) else date.today(),
            open_price=Decimal(str(latest['Open'])) if 'Open' in latest and not pd.isna(latest['Open']) else None,
            high_price=Decimal(str(latest['High'])) if 'High' in latest and not pd.isna(latest['High']) else None,
            low_price=Decimal(str(latest['Low'])) if 'Low' in latest and not pd.isna(latest['Low']) else None,
            close_price=Decimal(str(latest['Close'])),
            adjusted_close_price=Decimal(str(latest['Adj Close'])) if 'Adj Close' in latest and not pd.isna(latest['Adj Close']) else None,
            volume=Decimal(str(latest['Volume'])) if 'Volume' in latest and not pd.isna(latest['Volume']) else None,
            source=self.get_name()
        )
        quotes.append(quote)
        
        # Cache the result
        cache_key = f"yfinance_current_price_{formatted_t}"
        market_data_cache.set(cache_key, quote)

    def fetch_historical_prices(self, ticker: str, start_date: date, end_date: date) -> List[AssetQuote]:
        formatted_t = self._format_ticker(ticker)
        cache_key = f"yfinance_hist_{formatted_t}_{start_date}_{end_date}"
        cached = market_data_cache.get(cache_key)
        if cached:
            return cached
            
        quotes = []
        try:
            stock = yf.Ticker(formatted_t)
            hist = stock.history(start=start_date.isoformat(), end=(end_date + timedelta(days=1)).isoformat())
            
            for index, row in hist.iterrows():
                quote = AssetQuote(
                    ticker=ticker,
                    date=index.date(),
                    open_price=Decimal(str(row['Open'])),
                    high_price=Decimal(str(row['High'])),
                    low_price=Decimal(str(row['Low'])),
                    close_price=Decimal(str(row['Close'])),
                    volume=Decimal(str(row['Volume'])),
                    source=self.get_name()
                )
                quotes.append(quote)
                
            market_data_cache.set(cache_key, quotes, ttl=86400) # cache for 1 day
        except Exception as e:
            logger.error(f"Error fetching historical prices for {ticker}: {e}")
            
        return quotes

    def fetch_dividends(self, ticker: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        formatted_t = self._format_ticker(ticker)
        try:
            stock = yf.Ticker(formatted_t)
            divs = stock.dividends
            if divs.empty:
                return []
                
            divs = divs.loc[str(start_date):str(end_date)]
            results = []
            for index, value in divs.items():
                results.append({
                    "date": index.date(),
                    "value": Decimal(str(value))
                })
            return results
        except Exception as e:
            logger.error(f"Error fetching dividends for {ticker}: {e}")
            return []

    def fetch_metadata(self, ticker: str) -> Dict[str, Any]:
        formatted_t = self._format_ticker(ticker)
        try:
            stock = yf.Ticker(formatted_t)
            info = stock.info
            return {
                "name": info.get("shortName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "currency": info.get("currency", "BRL"),
                "type": info.get("quoteType", "")
            }
        except Exception as e:
            logger.error(f"Error fetching metadata for {ticker}: {e}")
            return {}
