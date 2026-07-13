"""Momentum indicator - Assess RSI, MACD, and daily returns."""
import logging
from typing import Optional
from utils.helpers import safe_float

logger = logging.getLogger(__name__)


def compute_momentum_score(
    rsi: Optional[float],
    daily_return: Optional[float] = None
) -> tuple[int, str]:
    """Compute momentum score (1-10).
    
    Score interpretation:
    10 = Strong bullish momentum (RSI < 30, oversold)
    8 = Bullish momentum (RSI 40-60)
    5 = Neutral momentum (RSI 50-60)
    2 = Bearish momentum (RSI 60-80)
    1 = Strong bearish momentum (RSI > 70, overbought)
    
    Args:
        rsi: Relative Strength Index (0-100)
        daily_return: Daily return % (optional, for confirmation)
        
    Returns:
        Tuple of (score: 1-10, description: str)
    """
    rsi = safe_float(rsi)
    daily_return = safe_float(daily_return)
    
    if rsi == 0:
        return 5, "Insufficient data"
    
    score = 5  # Start neutral
    
    # RSI-based scoring
    if rsi < 30:
        score = 9  # Oversold, strong bullish bounce potential
        reason = "Oversold (RSI < 30)"
    elif rsi < 40:
        score = 7  # Bullish
        reason = "Bullish (RSI 30-40)"
    elif rsi < 50:
        score = 6  # Mild bullish
        reason = "Mild bullish (RSI 40-50)"
    elif rsi < 60:
        score = 4  # Mild bearish
        reason = "Neutral (RSI 50-60)"
    elif rsi < 70:
        score = 3  # Bearish
        reason = "Bearish (RSI 60-70)"
    else:
        score = 1  # Overbought
        reason = "Overbought (RSI > 70)"
    
    # Adjust for daily return
    if daily_return > 2:
        reason += "; strong move today"
        score = min(10, score + 1)
    elif daily_return < -2:
        reason += "; weak move today"
        score = max(1, score - 1)
    
    return score, reason


def get_momentum_label(rsi: Optional[float]) -> str:
    """Get momentum label for display.
    
    Args:
        rsi: Relative Strength Index (0-100)
        
    Returns:
        Label: "Overbought", "Bullish", "Neutral", "Bearish", or "Oversold"
    """
    rsi = safe_float(rsi)
    
    if rsi == 0:
        return "Unknown"
    elif rsi > 70:
        return "Overbought"
    elif rsi > 60:
        return "Bullish"
    elif rsi > 50:
        return "Neutral-Bullish"
    elif rsi > 40:
        return "Neutral"
    elif rsi > 30:
        return "Bearish"
    else:
        return "Oversold"
