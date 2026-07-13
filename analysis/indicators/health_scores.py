"""Health scores - Derived insights from multiple indicators."""
import logging
from typing import Optional, Dict, Any

from analysis.indicators.trend import compute_trend_health, get_trend_direction
from analysis.indicators.momentum import compute_momentum_score, get_momentum_label
from analysis.indicators.volatility import compute_volatility_level
from utils.helpers import safe_float

logger = logging.getLogger(__name__)


def compute_all_health_scores(indicators: Dict[str, Any]) -> Dict[str, Any]:
    """Compute all health scores from technical indicators.
    
    Args:
        indicators: Dictionary with keys:
            - current_price: float
            - sma_20: float
            - sma_50: float
            - rsi: float
            - volatility: float
            - daily_return: float
            
    Returns:
        Dictionary with health scores:
            - trend: {score: 1-10, label: str, direction: str}
            - momentum: {score: 1-10, label: str}
            - risk: {level: str, icon: str}
            - volume: {label: str}  (if available)
    """
    
    health_scores = {}
    
    # Trend health
    trend_score, trend_desc = compute_trend_health(
        indicators.get("current_price"),
        indicators.get("sma_20"),
        indicators.get("sma_50")
    )
    trend_direction = get_trend_direction(
        indicators.get("sma_20"),
        indicators.get("sma_50")
    )
    health_scores["trend"] = {
        "score": trend_score,
        "description": trend_desc,
        "direction": trend_direction,
        "sma_20": safe_float(indicators.get("sma_20")),
        "sma_50": safe_float(indicators.get("sma_50")),
    }
    
    # Momentum health
    momentum_score, momentum_desc = compute_momentum_score(
        indicators.get("rsi"),
        indicators.get("daily_return")
    )
    momentum_label = get_momentum_label(indicators.get("rsi"))
    health_scores["momentum"] = {
        "score": momentum_score,
        "description": momentum_desc,
        "label": momentum_label,
        "rsi": safe_float(indicators.get("rsi")),
    }
    
    # Risk health
    volatility_level, volatility_icon = compute_volatility_level(
        indicators.get("volatility")
    )
    health_scores["risk"] = {
        "level": volatility_level,
        "icon": volatility_icon,
        "volatility": safe_float(indicators.get("volatility")),
    }
    
    logger.debug(f"Computed health scores: {health_scores}")
    return health_scores
