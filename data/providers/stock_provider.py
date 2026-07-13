"""Stock data provider with caching.

Wraps yfinance API calls and applies intelligent caching.
"""
import logging
from typing import Any, Optional
import pandas as pd
import yfinance as yf

from data.providers.cache import DataCache
from services.stock_service import StockService

logger = logging.getLogger(__name__)


class StockProvider:
    """Provides stock data with intelligent caching.
    
    This is a wrapper around StockService that adds caching:
    - Quote prices: cached for 1 minute
    - Historical data: cached for 1 hour
    - Company info: cached for session
    """
    
    def __init__(self, cache: Optional[DataCache] = None):
        self.stock_service = StockService()
        self.cache = cache or DataCache()
    
    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Get current quote with 1-minute cache.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE.NS")
            
        Returns:
            Quote dictionary with price, open, high, low, volume, etc.
        """
        key = f"quote:{symbol}"
        return self.cache.get_or_fetch(
            key,
            category="live",
            fetch_fn=lambda: self.stock_service.get_quote(symbol)
        )
    
    def get_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical data with 1-hour cache.
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, etc.)
            interval: Candle interval (1m, 5m, 15m, 30m, 60m, 1d)
            
        Returns:
            DataFrame with OHLCV data + indicators
        """
        key = f"history:{symbol}:{period}:{interval}"
        return self.cache.get_or_fetch(
            key,
            category="periodic",
            fetch_fn=lambda: self.stock_service.get_history(symbol, period, interval)
        )
    
    def get_technical_indicators(self, history: pd.DataFrame) -> dict[str, Any]:
        """Compute technical indicators from history.
        
        This is not cached because it's instant (computed locally).
        
        Args:
            history: DataFrame with OHLCV data
            
        Returns:
            Dictionary with indicator values
        """
        return self.stock_service.get_technical_indicators(history)
    
    def get_company_info(self, symbol: str) -> dict[str, Any]:
        """Get company info with session cache.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with company name, sector, industry, etc.
        """
        key = f"company:{symbol}"
        
        def fetch_info():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info or {}
                return {
                    "name": info.get("longName", symbol),
                    "sector": info.get("sector", "Unknown"),
                    "industry": info.get("industry", "Unknown"),
                    "market_cap": info.get("marketCap"),
                    "currency": info.get("currency", "INR"),
                }
            except Exception as e:
                logger.warning(f"Failed to fetch company info for {symbol}: {e}")
                return {
                    "name": symbol,
                    "sector": "Unknown",
                    "industry": "Unknown",
                    "market_cap": None,
                    "currency": "INR",
                }
        
        return self.cache.get_or_fetch(
            key,
            category="static",
            fetch_fn=fetch_info
        )
    
    def invalidate_quote(self, symbol: str) -> None:
        """Force refresh of a stock quote."""
        self.cache.invalidate(f"quote:{symbol}")
    
    def invalidate_all_quotes(self) -> None:
        """Force refresh of all cached quotes."""
        self.cache.invalidate_pattern("quote:*")
    
    def invalidate_history(self, symbol: str) -> None:
        """Force refresh of historical data."""
        self.cache.invalidate_pattern(f"history:{symbol}:*")
