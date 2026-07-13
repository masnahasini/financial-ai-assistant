"""Watchlist repository - Persistence layer for watchlist items."""
import logging
from typing import Optional

from database.models import WatchlistItem
from data.repositories.db_session import SessionLocal
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class WatchlistRepository:
    """Manages watchlist persistence.
    
    This wraps the WatchlistItem ORM model and provides
    a clean repository interface.
    """
    
    def add_stock(self, symbol: str) -> Optional[WatchlistItem]:
        """Add a stock to the watchlist.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE.NS")
            
        Returns:
            WatchlistItem if successful, None if already exists
        """
        with SessionLocal() as session:
            # Check if already exists
            existing = session.query(WatchlistItem).filter_by(symbol=symbol).first()
            if existing:
                logger.debug(f"Stock {symbol} already in watchlist")
                return existing
            
            # Add new item
            try:
                item = WatchlistItem(symbol=symbol)
                session.add(item)
                session.commit()
                session.refresh(item)
                logger.info(f"Added {symbol} to watchlist")
                return item
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to add {symbol} to watchlist: {e}")
                raise RuntimeError(f"Could not add {symbol} to watchlist") from e
    
    def remove_stock(self, symbol: str) -> bool:
        """Remove a stock from the watchlist.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if removed, False if not found
        """
        with SessionLocal() as session:
            item = session.query(WatchlistItem).filter_by(symbol=symbol).first()
            if not item:
                logger.debug(f"Stock {symbol} not found in watchlist")
                return False
            
            try:
                session.delete(item)
                session.commit()
                logger.info(f"Removed {symbol} from watchlist")
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to remove {symbol} from watchlist: {e}")
                raise RuntimeError(f"Could not remove {symbol} from watchlist") from e
    
    def list_stocks(self) -> list[WatchlistItem]:
        """Get all watchlist items.
        
        Returns:
            List of WatchlistItem objects, ordered by creation date (newest first)
        """
        with SessionLocal() as session:
            items = session.query(WatchlistItem).order_by(
                WatchlistItem.created_at.desc()
            ).all()
            # Detach from session to return independent objects
            return [item for item in items]
    
    def get_stock(self, symbol: str) -> Optional[WatchlistItem]:
        """Get a specific watchlist item.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            WatchlistItem if found, None otherwise
        """
        with SessionLocal() as session:
            return session.query(WatchlistItem).filter_by(symbol=symbol).first()
    
    def exists(self, symbol: str) -> bool:
        """Check if a stock is in the watchlist.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if in watchlist, False otherwise
        """
        return self.get_stock(symbol) is not None
