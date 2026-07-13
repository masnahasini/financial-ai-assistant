"""Portfolio workflow - Manages portfolio operations."""
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from data.repositories.portfolio_repository import PortfolioRepository
from data.providers.stock_provider import StockProvider
from data.providers.cache import DataCache
from utils.helpers import safe_float

logger = logging.getLogger(__name__)


class PortfolioWorkflow:
    """Manages portfolio operations and P&L tracking."""
    
    def __init__(
        self,
        cache: Optional[DataCache] = None,
        stock_provider: Optional[StockProvider] = None,
    ):
        self.repository = PortfolioRepository()
        self.cache = cache or DataCache()
        self.stock_provider = stock_provider or StockProvider(self.cache)
    
    def add_holding(
        self,
        symbol: str,
        quantity: float,
        purchase_price: float
    ) -> Dict[str, Any]:
        """Add or update a holding.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            purchase_price: Purchase price per share
            
        Returns:
            Holding details
        """
        logger.info(f"Adding holding: {symbol} x{quantity} @ ₹{purchase_price}")
        
        holding = self.repository.add_holding(symbol, quantity, purchase_price)
        
        return {
            "symbol": holding.symbol,
            "quantity": holding.quantity,
            "purchase_price": holding.purchase_price,
            "investment_value": holding.quantity * holding.purchase_price,
        }
    
    def remove_holding(self, symbol: str) -> bool:
        """Remove a holding.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if removed, False if not found
        """
        logger.info(f"Removing holding: {symbol}")
        return self.repository.remove_holding(symbol)
    
    def get_holdings(self) -> List[Dict[str, Any]]:
        """Get all holdings with current prices.
        
        Returns:
            List of holdings with current value and P&L
        """
        holdings = self.repository.list_holdings()
        results = []
        
        for holding in holdings:
            try:
                quote = self.stock_provider.get_quote(holding.symbol)
                current_price = safe_float(quote.get("current_price"))
                investment = holding.quantity * holding.purchase_price
                current_value = holding.quantity * current_price
                profit_loss = current_value - investment
                profit_loss_pct = (profit_loss / investment * 100) if investment > 0 else 0
                
                results.append({
                    "symbol": holding.symbol,
                    "quantity": holding.quantity,
                    "purchase_price": holding.purchase_price,
                    "current_price": current_price,
                    "investment_value": investment,
                    "current_value": current_value,
                    "profit_loss": profit_loss,
                    "profit_loss_pct": profit_loss_pct,
                })
            except Exception as e:
                logger.warning(f"Failed to get quote for {holding.symbol}: {e}")
                results.append({
                    "symbol": holding.symbol,
                    "quantity": holding.quantity,
                    "purchase_price": holding.purchase_price,
                    "current_price": None,
                    "investment_value": holding.quantity * holding.purchase_price,
                    "current_value": None,
                    "profit_loss": None,
                    "profit_loss_pct": None,
                })
        
        return results
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio-level metrics.
        
        Returns:
            Dictionary with total investment, current value, overall P&L
        """
        holdings = self.get_holdings()
        
        total_investment = sum(h["investment_value"] for h in holdings if h["investment_value"])
        total_current = sum(h["current_value"] for h in holdings if h["current_value"])
        total_pl = total_current - total_investment if total_investment > 0 else 0
        total_pl_pct = (total_pl / total_investment * 100) if total_investment > 0 else 0
        
        return {
            "total_investment": total_investment,
            "total_current_value": total_current,
            "total_profit_loss": total_pl,
            "total_profit_loss_pct": total_pl_pct,
            "num_holdings": len(holdings),
            "holdings": holdings,
        }
