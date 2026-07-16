import os
from typing import Dict, Any

class MarketDataConfig:
    # Providers config
    YAHOO_FINANCE_TIMEOUT = int(os.getenv("YFINANCE_TIMEOUT", "10"))
    USER_AGENT = os.getenv("MARKET_DATA_USER_AGENT", "FinAnalytics V3/1.0")
    
    # Cache config
    CACHE_ENABLED = os.getenv("MARKET_DATA_CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_SECONDS = int(os.getenv("MARKET_DATA_CACHE_TTL", "3600")) # 1 hour default
    
    # Retry config
    MAX_RETRIES = int(os.getenv("MARKET_DATA_MAX_RETRIES", "3"))
    RETRY_BACKOFF_FACTOR = float(os.getenv("MARKET_DATA_RETRY_BACKOFF", "0.5"))

    @classmethod
    def get_provider_settings(cls, provider_name: str) -> Dict[str, Any]:
        return {
            "timeout": cls.YAHOO_FINANCE_TIMEOUT if provider_name == "yahoo_finance" else 10,
            "user_agent": cls.USER_AGENT,
            "max_retries": cls.MAX_RETRIES,
            "retry_backoff": cls.RETRY_BACKOFF_FACTOR
        }
