"""Technical analyzer - Analyzes price trends, support/resistance, etc."""
import logging
from typing import Dict, Any, Optional
import pandas as pd

from analysis.indicators.health_scores import compute_all_health_scores
from utils.helpers import safe_float

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Analyzes technical indicators and price action."""
    
    def analyze(
        self,
        history: pd.DataFrame,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Perform technical analysis on historical data.
        
        Args:
            history: DataFrame with OHLCV data + indicators (SMA, RSI, Volatility, etc.)
            current_price: Current price (optional, defaults to latest close)
            
        Returns:
            Dictionary with:
                - health_scores: {trend, momentum, risk}
                - support: float
                - resistance: float
                - trend: str ("Up", "Down", "Sideways")
                - summary: str
        """
        if history.empty:
            logger.warning("Cannot analyze empty history")
            return self._empty_analysis()
        
        latest = history.iloc[-1]
        current_price = current_price or safe_float(latest.get("Close"))
        
        # Extract indicators from history
        indicators = {
            "current_price": current_price,
            "sma_20": safe_float(latest.get("SMA_20")),
            "sma_50": safe_float(latest.get("SMA_50")),
            "rsi": safe_float(latest.get("RSI")),
            "volatility": safe_float(latest.get("Volatility")),
            "daily_return": safe_float(latest.get("Daily_Return")) * 100,
        }
        
        # Compute health scores
        health_scores = compute_all_health_scores(indicators)
        
        # Calculate support and resistance
        support, resistance = self._calculate_support_resistance(history, current_price)
        
        # Determine overall trend
        trend = self._determine_trend(health_scores)
        
        # Generate summary
        summary = self._generate_summary(health_scores, support, resistance)
        
        return {
            "indicators": indicators,
            "health_scores": health_scores,
            "support": support,
            "resistance": resistance,
            "trend": trend,
            "summary": summary,
        }
    
    def _calculate_support_resistance(
        self,
        history: pd.DataFrame,
        current_price: float
    ) -> tuple[float, float]:
        """Calculate support and resistance levels.
        
        Using simple method: recent low = support, recent high = resistance
        
        Args:
            history: Historical data
            current_price: Current price
            
        Returns:
            Tuple of (support, resistance)
        """
        # Use 50-day lows/highs
        recent = history.tail(50)
        support = safe_float(recent["Low"].min())
        resistance = safe_float(recent["High"].max())
        
        # Ensure they make sense
        if support >= current_price:
            support = safe_float(history["Low"].min())
        if resistance <= current_price:
            resistance = safe_float(history["High"].max())
        
        return support, resistance
    
    def _determine_trend(self, health_scores: Dict[str, Any]) -> str:
        """Determine overall trend from health scores.
        
        Args:
            health_scores: Dictionary with trend, momentum, risk scores
            
        Returns:
            Trend: "Uptrend", "Downtrend", or "Sideways"
        """
        trend_score = health_scores["trend"]["score"]
        
        if trend_score >= 8:
            return "Uptrend"
        elif trend_score <= 2:
            return "Downtrend"
        else:
            return "Sideways"
    
    def _generate_summary(self, health_scores, support, resistance) -> str:
        """Generate a natural language summary of the technical analysis.
        
        Args:
            health_scores: Health scores dictionary
            support: Support level
            resistance: Resistance level
            
        Returns:
            Summary string
        """
        trend = health_scores["trend"]["description"]
        momentum = health_scores["momentum"]["description"]
        risk = health_scores["risk"]["level"]
        
        return f"Trend: {trend}. Momentum: {momentum}. Risk: {risk}."
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            "indicators": {},
            "health_scores": {},
            "support": None,
            "resistance": None,
            "trend": "Unknown",
            "summary": "Insufficient data",
        }
