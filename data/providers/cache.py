"""Generic caching layer with TTL-based expiration."""
import time
from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)


class DataCache:
    """Intelligent caching with category-based TTLs.
    
    Categories:
    - live: 60 seconds (quote prices, real-time data)
    - frequent: 900 seconds (15 minutes, news articles)
    - periodic: 3600 seconds (1 hour, historical data)
    - static: session duration (company info, validation rules)
    """
    
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        self.ttl_map = {
            "live": 60,           # 1 minute
            "frequent": 900,      # 15 minutes
            "periodic": 3600,     # 1 hour
            "static": float('inf'),  # Session
        }
        self.hits = 0
        self.misses = 0
    
    def get_or_fetch(
        self,
        key: str,
        category: str,
        fetch_fn: Callable,
    ) -> Any:
        """Get from cache if valid, else fetch from source.
        
        Args:
            key: Cache key (e.g., "quote:RELIANCE.NS")
            category: TTL category (live, frequent, periodic, static)
            fetch_fn: Callable that fetches fresh data
            
        Returns:
            Cached or fresh data
        """
        if category not in self.ttl_map:
            raise ValueError(f"Unknown cache category: {category}")
        
        # Check if cached and not expired
        if key in self.cache:
            age = time.time() - self.timestamps[key]
            ttl = self.ttl_map[category]
            if age < ttl:
                self.hits += 1
                logger.debug(f"Cache hit: {key} (age: {age:.1f}s, ttl: {ttl}s)")
                return self.cache[key]
        
        # Fetch new data
        logger.debug(f"Cache miss: {key}, fetching from source...")
        try:
            data = fetch_fn()
            self.cache[key] = data
            self.timestamps[key] = time.time()
            self.misses += 1
            return data
        except Exception as e:
            logger.error(f"Error fetching {key}: {e}")
            # Return cached data if available, even if expired
            if key in self.cache:
                logger.warning(f"Returning expired cache for {key}: {e}")
                return self.cache[key]
            raise
    
    def invalidate(self, key: str) -> None:
        """Force refresh on next access."""
        if key in self.cache:
            logger.debug(f"Invalidating cache: {key}")
            del self.cache[key]
            del self.timestamps[key]
    
    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching a pattern.
        
        Args:
            pattern: Pattern like "quote:*" to invalidate all quotes
        """
        import fnmatch
        keys_to_remove = [k for k in self.cache if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_remove:
            self.invalidate(key)
        logger.debug(f"Invalidated {len(keys_to_remove)} cache entries matching {pattern}")
    
    def clear(self) -> None:
        """Clear entire cache."""
        logger.debug(f"Clearing entire cache ({len(self.cache)} entries)")
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "entries": len(self.cache),
        }
