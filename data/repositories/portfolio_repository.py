"""Portfolio repository - Persistence layer for holdings."""
import logging
from typing import Optional

from database.models import PortfolioHolding
from data.repositories.db_session import SessionLocal
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class PortfolioRepository:
    """Manages portfolio holdings persistence.
    
    This wraps the PortfolioHolding ORM model and provides
    a clean repository interface.
    """
    
    def add_holding(
        self,
        symbol: str,
        quantity: float,
        purchase_price: float
    ) -> Optional[PortfolioHolding]:
        """Add or update a holding.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            purchase_price: Purchase price per share
            
        Returns:
            PortfolioHolding if successful
        """
        with SessionLocal() as session:
            existing = session.query(PortfolioHolding).filter_by(symbol=symbol).first()
            
            try:
                if existing:
                    # Update with weighted average cost basis
                    old_qty = existing.quantity
                    new_total_qty = old_qty + quantity
                    weighted_price = (
                        (existing.purchase_price * old_qty) + 
                        (purchase_price * quantity)
                    ) / new_total_qty
                    existing.quantity = new_total_qty
                    existing.purchase_price = weighted_price
                    session.commit()
                    session.refresh(existing)
                    logger.info(f"Updated {symbol}: {new_total_qty} shares at ₹{weighted_price:.2f}")
                    return existing
                else:
                    # Add new holding
                    holding = PortfolioHolding(
                        symbol=symbol,
                        quantity=quantity,
                        purchase_price=purchase_price
                    )
                    session.add(holding)
                    session.commit()
                    session.refresh(holding)
                    logger.info(f"Added {symbol}: {quantity} shares at ₹{purchase_price:.2f}")
                    return holding
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to add holding for {symbol}: {e}")
                raise RuntimeError(f"Could not add holding for {symbol}") from e
    
    def remove_holding(self, symbol: str) -> bool:
        """Remove a holding.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if removed, False if not found
        """
        with SessionLocal() as session:
            holding = session.query(PortfolioHolding).filter_by(symbol=symbol).first()
            if not holding:
                logger.debug(f"Holding {symbol} not found")
                return False
            
            try:
                session.delete(holding)
                session.commit()
                logger.info(f"Removed holding for {symbol}")
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to remove holding for {symbol}: {e}")
                raise RuntimeError(f"Could not remove holding for {symbol}") from e
    
    def list_holdings(self) -> list[PortfolioHolding]:
        """Get all holdings.
        
        Returns:
            List of PortfolioHolding objects, ordered by creation date
        """
        with SessionLocal() as session:
            holdings = session.query(PortfolioHolding).order_by(
                PortfolioHolding.created_at.desc()
            ).all()
            return [h for h in holdings]
    
    def get_holding(self, symbol: str) -> Optional[PortfolioHolding]:
        """Get a specific holding.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            PortfolioHolding if found, None otherwise
        """
        with SessionLocal() as session:
            return session.query(PortfolioHolding).filter_by(symbol=symbol).first()
    
    def exists(self, symbol: str) -> bool:
        """Check if a holding exists.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if holding exists, False otherwise
        """
        return self.get_holding(symbol) is not None
