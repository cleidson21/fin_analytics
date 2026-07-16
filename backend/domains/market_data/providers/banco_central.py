import logging
import requests
from typing import List, Dict, Any
from datetime import date, datetime
from decimal import Decimal

from backend.domains.market_data.interfaces import MarketDataProvider, AssetQuote

logger = logging.getLogger(__name__)

# SGS Codes
SGS_CODES = {
    "CDI": 12,
    "SELIC": 11,
    "IPCA": 433
}

class BCProvider(MarketDataProvider):
    def get_name(self) -> str:
        return "Banco Central (SGS)"

    def _fetch_sgs_latest(self, indicator: str, code: int) -> AssetQuote:
        try:
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/1?formato=json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                raise ValueError(f"No data returned for {indicator}")
                
            item = data[0]
            val = Decimal(str(item["valor"]))
            dt = datetime.strptime(item["data"], "%d/%m/%Y").date()
            
            return AssetQuote(
                ticker=indicator,
                date=dt,
                close_price=val,
                currency="BRL",
                source=self.get_name()
            )
        except Exception as e:
            logger.error(f"Error fetching {indicator} from SGS: {str(e)}")
            raise e

    def fetch_current_prices(self, tickers: List[str]) -> List[AssetQuote]:
        """Fetch the latest indicators from BCB."""
        quotes = []
        for ticker in tickers:
            ticker_upper = ticker.upper()
            if ticker_upper in SGS_CODES:
                try:
                    quote = self._fetch_sgs_latest(ticker_upper, SGS_CODES[ticker_upper])
                    quotes.append(quote)
                except Exception:
                    # Will be handled gracefully by service
                    pass
        return quotes
        
    def fetch_historical_prices(self, ticker: str, start_date: date, end_date: date) -> List[AssetQuote]:
        """Fetch historical indicators (Not implemented for this MVP)"""
        return []

    def fetch_dividends(self, ticker: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        return []
        
    def fetch_metadata(self, ticker: str) -> Dict[str, Any]:
        return {}
