"""Watchlist workflow - Manages watchlist operations."""
import logging
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

from data.repositories.watchlist_repository import WatchlistRepository
from data.providers.stock_provider import StockProvider
from data.providers.cache import DataCache
from utils.helpers import safe_float

logger = logging.getLogger(__name__)


class WatchlistWorkflow:
    """Manages watchlist operations with efficient quote fetching."""
    
    def __init__(
        self,
        cache: Optional[DataCache] = None,
        stock_provider: Optional[StockProvider] = None,
    ):
        self.repository = WatchlistRepository()
        self.cache = cache or DataCache()
        self.stock_provider = stock_provider or StockProvider(self.cache)
    
    def add_stock(self, symbol: str) -> Dict[str, Any]:
        """Add a stock to watchlist.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock info
        """
        logger.info(f"Adding {symbol} to watchlist")
        item = self.repository.add_stock(symbol)
        
        if item:
            return {"symbol": item.symbol, "created_at": item.created_at}
        return {}
    
    def remove_stock(self, symbol: str) -> bool:
        """Remove a stock from watchlist.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if removed, False if not found
        """
        logger.info(f"Removing {symbol} from watchlist")
        return self.repository.remove_stock(symbol)
    
    def get_watchlist_with_quotes(
        self,
        max_workers: int = 5
    ) -> List[Dict[str, Any]]:
        """Get all watchlist items with current quotes (parallel fetch).
        
        Args:
            max_workers: Number of parallel workers for quote fetching
            
        Returns:
            List of watchlist items with current quotes
        """
        items = self.repository.list_stocks()
        logger.debug(f"Fetching quotes for {len(items)} stocks in parallel...")
        
        results = []
        
        # Fetch quotes in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            quote_futures = {
                executor.submit(self.stock_provider.get_quote, item.symbol): item
                for item in items
            }
            
            for future in concurrent.futures.as_completed(quote_futures, timeout=30):
                item = quote_futures[future]
                try:
                    quote = future.result(timeout=5)
                    results.append({
                        "symbol": item.symbol,
                        "name": quote.get("company_name", item.symbol),
                        "current_price": safe_float(quote.get("current_price")),
                        "change_percent": safe_float(quote.get("change_percent")),
                        "volume": safe_float(quote.get("volume")),
                        "created_at": item.created_at,
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch quote for {item.symbol}: {e}")
                    results.append({
                        "symbol": item.symbol,
                        "name": item.symbol,
                        "current_price": None,
                        "change_percent": None,
                        "volume": None,
                        "created_at": item.created_at,
                        "error": str(e),
                    })
        
        return results
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Get all watchlist items without quotes.
        
        Returns:
            List of watchlist items
        """
        items = self.repository.list_stocks()
        return [
            {"symbol": item.symbol, "created_at": item.created_at}
            for item in items
        ]
