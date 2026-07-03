import logging

from sqlalchemy.exc import SQLAlchemyError

from database.db import SessionLocal
from database.models import WatchlistItem


logger = logging.getLogger(__name__)


class WatchlistService:
    def add_stock(self, symbol: str) -> WatchlistItem:
        with SessionLocal() as session:
            existing = session.query(WatchlistItem).filter_by(symbol=symbol).first()
            if existing:
                return existing
            item = WatchlistItem(symbol=symbol)
            try:
                session.add(item)
                session.commit()
                session.refresh(item)
                return item
            except SQLAlchemyError as exc:
                session.rollback()
                logger.exception("Failed to add watchlist item")
                raise RuntimeError("Could not add stock to watchlist") from exc

    def remove_stock(self, symbol: str) -> bool:
        with SessionLocal() as session:
            item = session.query(WatchlistItem).filter_by(symbol=symbol).first()
            if not item:
                return False
            try:
                session.delete(item)
                session.commit()
                return True
            except SQLAlchemyError as exc:
                session.rollback()
                logger.exception("Failed to remove watchlist item")
                raise RuntimeError("Could not remove stock from watchlist") from exc

    def list_stocks(self) -> list[WatchlistItem]:
        with SessionLocal() as session:
            return session.query(WatchlistItem).order_by(WatchlistItem.created_at.desc()).all()
