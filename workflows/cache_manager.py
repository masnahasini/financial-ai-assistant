"""Cache manager - Centralized cache lifecycle management."""
import logging
from typing import Optional

from data.providers.cache import DataCache

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages cache lifecycle and invalidation."""
    
    _instance: Optional["CacheManager"] = None
    
    def __new__(cls):
        """Singleton pattern - only one cache instance per app."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = DataCache()
        return cls._instance
    
    @property
    def cache(self) -> DataCache:
        """Get the cache instance."""
        return self._cache
    
    @cache.setter
    def cache(self, value: DataCache):
        """Set the cache instance."""
        self._cache = value
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache.get_stats()
    
    def invalidate_stock(self, symbol: str) -> None:
        """Invalidate all caches for a stock."""
        logger.info(f"Invalidating all caches for {symbol}")
        self.cache.invalidate_pattern(f"quote:{symbol}")
        self.cache.invalidate_pattern(f"history:{symbol}:*")
        self.cache.invalidate_pattern(f"news:{symbol}:*")
    
    def invalidate_quotes(self) -> None:
        """Invalidate all quote caches."""
        logger.info("Invalidating all quote caches")
        self.cache.invalidate_pattern("quote:*")
    
    def invalidate_news(self) -> None:
        """Invalidate all news caches."""
        logger.info("Invalidating all news caches")
        self.cache.invalidate_pattern("news:*")
    
    def clear(self) -> None:
        """Clear entire cache."""
        logger.warning("Clearing entire cache")
        self.cache.clear()
