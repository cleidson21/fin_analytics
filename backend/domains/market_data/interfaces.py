from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import date
from pydantic import BaseModel
from decimal import Decimal

class AssetQuote(BaseModel):
    ticker: str
    date: date
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Decimal
    adjusted_close_price: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    currency: str = "BRL"
    source: str

class MarketDataProvider(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Returns the identifier of the provider."""
        pass

    @abstractmethod
    def fetch_current_prices(self, tickers: List[str]) -> List[AssetQuote]:
        """Fetch the latest available prices for a list of tickers."""
        pass
        
    @abstractmethod
    def fetch_historical_prices(self, ticker: str, start_date: date, end_date: date) -> List[AssetQuote]:
        """Fetch historical daily prices for a ticker."""
        pass

    @abstractmethod
    def fetch_dividends(self, ticker: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Fetch historical dividends for a ticker."""
        pass
        
    @abstractmethod
    def fetch_metadata(self, ticker: str) -> Dict[str, Any]:
        """Fetch asset metadata (name, sector, currency, etc)."""
        pass
