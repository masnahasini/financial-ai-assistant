"""Trend indicator - Assess price trend and moving average alignment."""
import logging
from typing import Optional
from utils.helpers import safe_float

logger = logging.getLogger(__name__)


def compute_trend_health(
    price: Optional[float],
    sma_20: Optional[float],
    sma_50: Optional[float]
) -> tuple[int, str]:
    """Compute trend health score (1-10).
    
    Score interpretation:
    10 = Strong uptrend (price > SMA20 > SMA50)
    8 = Moderate uptrend (price > SMA50, price < SMA20)
    5 = Sideways/uncertain
    2 = Moderate downtrend (price < SMA20, price > SMA50)
    1 = Strong downtrend (price < SMA20 < SMA50)
    
    Args:
        price: Current stock price
        sma_20: 20-day simple moving average
        sma_50: 50-day simple moving average
        
    Returns:
        Tuple of (score: 1-10, description: str)
    """
    price = safe_float(price)
    sma_20 = safe_float(sma_20)
    sma_50 = safe_float(sma_50)
    
    if price == 0 or sma_20 == 0 or sma_50 == 0:
        return 5, "Insufficient data"
    
    # Strong uptrend: price above both SMAs
    if price > sma_20 and sma_20 > sma_50:
        return 10, "Strong uptrend"
    
    # Moderate uptrend: price above SMA50 but below SMA20 (pullback in uptrend)
    if price > sma_50 and price < sma_20:
        return 8, "Uptrend with pullback"
    
    # Price above SMA50 but below SMA20: Mixed
    if price > sma_50 and sma_50 > sma_20:
        return 7, "Uptrend, SMA alignment improving"
    
    # Sideways: Price between SMAs
    if (sma_20 > price > sma_50) or (sma_50 > price > sma_20):
        return 5, "Sideways"
    
    # Moderate downtrend: price below SMA20 but above SMA50
    if price < sma_20 and price > sma_50:
        return 2, "Downtrend with bounce"
    
    # Strong downtrend: price below both SMAs
    if price < sma_20 and sma_20 < sma_50:
        return 1, "Strong downtrend"
    
    return 5, "Uncertain"


def get_trend_direction(
    sma_20: Optional[float],
    sma_50: Optional[float]
) -> str:
    """Get trend direction based on moving averages.
    
    Args:
        sma_20: 20-day SMA
        sma_50: 50-day SMA
        
    Returns:
        Direction: "↗ Up", "→ Flat", or "↘ Down"
    """
    sma_20 = safe_float(sma_20)
    sma_50 = safe_float(sma_50)
    
    if sma_20 == 0 or sma_50 == 0:
        return "→ Unknown"
    
    diff_pct = ((sma_20 - sma_50) / sma_50) * 100
    
    if diff_pct > 1:  # SMA20 > SMA50 by >1%
        return "↗ Up"
    elif diff_pct < -1:  # SMA20 < SMA50 by >1%
        return "↘ Down"
    else:
        return "→ Flat"
