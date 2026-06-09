import logging

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from database.db import SessionLocal
from database.models import PortfolioHolding
from services.stock_service import StockService


logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, stock_service: StockService | None = None):
        self.stock_service = stock_service or StockService()

    def add_holding(self, symbol: str, quantity: float, purchase_price: float) -> PortfolioHolding:
        with SessionLocal() as session:
            existing = session.query(PortfolioHolding).filter_by(symbol=symbol).first()
            try:
                if existing:
                    existing.quantity += quantity
                    existing.purchase_price = (
                        (existing.purchase_price * (existing.quantity - quantity)) + (purchase_price * quantity)
                    ) / existing.quantity
                    session.commit()
                    session.refresh(existing)
                    return existing
                holding = PortfolioHolding(symbol=symbol, quantity=quantity, purchase_price=purchase_price)
                session.add(holding)
                session.commit()
                session.refresh(holding)
                return holding
            except SQLAlchemyError as exc:
                session.rollback()
                logger.exception("Failed to add portfolio holding")
                raise RuntimeError("Could not add holding") from exc

    def remove_holding(self, symbol: str) -> bool:
        with SessionLocal() as session:
            holding = session.query(PortfolioHolding).filter_by(symbol=symbol).first()
            if not holding:
                return False
            try:
                session.delete(holding)
                session.commit()
                return True
            except SQLAlchemyError as exc:
                session.rollback()
                logger.exception("Failed to remove holding")
                raise RuntimeError("Could not remove holding") from exc

    def list_holdings(self) -> list[PortfolioHolding]:
        with SessionLocal() as session:
            return session.query(PortfolioHolding).order_by(PortfolioHolding.created_at.desc()).all()

    def get_portfolio_summary(self) -> pd.DataFrame:
        rows = []
        for holding in self.list_holdings():
            quote = self.stock_service.get_quote(holding.symbol)
            current_price = quote.get("current_price") or 0
            investment_value = holding.quantity * holding.purchase_price
            current_value = holding.quantity * current_price
            profit_loss = current_value - investment_value
            profit_loss_percent = (profit_loss / investment_value * 100) if investment_value else 0
            rows.append(
                {
                    "Symbol": holding.symbol,
                    "Quantity": holding.quantity,
                    "Purchase Price": holding.purchase_price,
                    "Current Price": current_price,
                    "Investment Value": investment_value,
                    "Current Value": current_value,
                    "Profit/Loss": profit_loss,
                    "Profit/Loss %": profit_loss_percent,
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def calculate_totals(summary: pd.DataFrame) -> dict[str, float]:
        investment_value = float(summary["Investment Value"].sum()) if not summary.empty else 0
        current_value = float(summary["Current Value"].sum()) if not summary.empty else 0
        profit_loss = current_value - investment_value
        profit_loss_percent = (profit_loss / investment_value * 100) if investment_value else 0
        return {
            "investment_value": investment_value,
            "current_value": current_value,
            "profit_loss": profit_loss,
            "profit_loss_percent": profit_loss_percent,
        }
