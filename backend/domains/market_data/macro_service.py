import logging
import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from backend.domains.market_data.interfaces import MarketDataProvider
from backend.domains.market_data.macro_repository import MacroIndicatorsRepository

logger = logging.getLogger(__name__)

class MacroIndicatorsCache:
    def __init__(self, ttl_seconds: int = 86400):
        self.ttl = ttl_seconds
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str) -> Any:
        if key in self._cache:
            if (time.time() - self._timestamps[key]) <= self.ttl:
                return self._cache[key]
            else:
                self.invalidate(key)
        return None

    def set(self, key: str, value: Any):
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def invalidate(self, key: str):
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)


class MacroIndicatorsService:
    def __init__(
        self,
        provider: MarketDataProvider,
        repository: MacroIndicatorsRepository,
        cache_ttl: int = 86400
    ):
        self.provider = provider
        self.repository = repository
        self.cache = MacroIndicatorsCache(ttl_seconds=cache_ttl)

    def _fetch_from_provider_safely(self, tickers: List[str]) -> List[Dict[str, Any]]:
        try:
            quotes = self.provider.fetch_current_prices(tickers)
            return [
                {
                    "indicator_type": q.ticker,
                    "date": q.date.strftime("%Y-%m-%d"),
                    "value": q.close_price
                }
                for q in quotes
            ]
        except Exception as e:
            logger.error(f"Failed to fetch macro indicators from {self.provider.get_name()}: {str(e)}")
            return []

    def update_indicators(self, session: Session) -> dict:
        """
        Rotina principal do Scheduler. Busca SELIC, CDI e IPCA do Banco Central.
        Salva no BD e atualiza o cache.
        """
        logger.info("Starting Macro Indicators update process...")
        tickers = ["SELIC", "CDI", "IPCA"]
        
        indicators = self._fetch_from_provider_safely(tickers)
        if not indicators:
            logger.info("Fallback: Maintaining previous macro indicators as BCB is unavailable.")
            return {"status": "error", "message": "BCB unavailable"}
            
        saved_count = self.repository.save_indicators(session, indicators)
        logger.info(f"Saved {saved_count} macro indicators to database.")
        
        # Atualiza o cache (cachemiss logic update)
        self.cache.set("latest_indicators", indicators)
        
        return {
            "status": "success",
            "provider": self.provider.get_name(),
            "indicators_fetched": len(indicators),
            "indicators_saved": saved_count
        }

    def get_latest_indicators(self, session: Session) -> List[Dict[str, Any]]:
        # Check Cache
        cached_data = self.cache.get("latest_indicators")
        if cached_data:
            logger.info("Macro indicators cache hit.")
            return cached_data
            
        logger.info("Macro indicators cache miss. Fetching from DB.")
        # DB Fallback
        db_data = self.repository.get_latest_indicators(session)
        if db_data:
            self.cache.set("latest_indicators", db_data)
            return db_data
            
        return []

    def get_historical_indicators(self, session: Session, indicator_type: str = None) -> List[Dict[str, Any]]:
        # History we don't cache deeply for MVP, directly to DB
        return self.repository.get_historical_indicators(session, indicator_type)
