import time
from typing import Any, Dict, Optional
from backend.domains.market_data.config import MarketDataConfig

class LocalCache:
    """
    Simple in-memory local cache to avoid repeated identical calls.
    Future: Extend to Redis or SQLite-based cache if multi-process is required.
    """
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def get(self, key: str) -> Optional[Any]:
        if not MarketDataConfig.CACHE_ENABLED:
            return None
            
        entry = self._cache.get(key)
        if not entry:
            return None
            
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
            
        return entry["value"]
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not MarketDataConfig.CACHE_ENABLED:
            return
            
        _ttl = ttl if ttl is not None else MarketDataConfig.CACHE_TTL_SECONDS
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + _ttl
        }
        
    def clear(self):
        self._cache.clear()

# Singleton cache instance for the application lifecycle
market_data_cache = LocalCache()
