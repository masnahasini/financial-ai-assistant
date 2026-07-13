"""News data provider with caching.

Wraps NewsAPI calls and applies intelligent caching.
"""
import logging
from typing import Any, Optional

from data.providers.cache import DataCache
from services.news_service import NewsService

logger = logging.getLogger(__name__)


class NewsProvider:
    """Provides news articles with intelligent caching.
    
    This is a wrapper around NewsService that adds caching:
    - News articles: cached for 15 minutes
    """
    
    def __init__(self, cache: Optional[DataCache] = None):
        self.news_service = NewsService()
        self.cache = cache or DataCache()
    
    def fetch_articles(
        self,
        symbol: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """Fetch news articles with 15-minute cache.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE.NS")
            limit: Maximum number of articles
            
        Returns:
            List of article dictionaries with title, description, url, etc.
        """
        key = f"news:{symbol}:{limit}"
        return self.cache.get_or_fetch(
            key,
            category="frequent",
            fetch_fn=lambda: self.news_service.fetch_company_news(symbol, limit)
        )
    
    def invalidate_articles(self, symbol: str) -> None:
        """Force refresh of articles for a symbol."""
        self.cache.invalidate_pattern(f"news:{symbol}:*")
    
    def invalidate_all_articles(self) -> None:
        """Force refresh of all cached articles."""
        self.cache.invalidate_pattern("news:*")
