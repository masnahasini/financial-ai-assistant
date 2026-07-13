"""Volatility indicator - Assess price volatility and risk level."""
import logging
from typing import Optional
from utils.helpers import safe_float

logger = logging.getLogger(__name__)


def compute_volatility_level(
    volatility: Optional[float]
) -> tuple[str, str]:
    """Compute volatility risk level.
    
    Levels:
    "Low" = volatility < 15% (very stable)
    "Moderate" = volatility 15-25% (normal for stocks)
    "High" = volatility 25-35% (elevated risk)
    "Very High" = volatility > 35% (extreme risk)
    
    Args:
        volatility: Annualized volatility as percentage
        
    Returns:
        Tuple of (level: str, icon: str)
    """
    volatility = safe_float(volatility)
    
    if volatility == 0:
        return "Unknown", "❓"
    elif volatility < 15:
        return "Low", "🟢"
    elif volatility < 25:
        return "Moderate", "🟡"
    elif volatility < 35:
        return "High", "🟠"
    else:
        return "Very High", "🔴"


def get_volatility_interpretation(volatility: Optional[float], sector_avg: float = 20) -> str:
    """Get interpretation of volatility relative to sector average.
    
    Args:
        volatility: Stock volatility
        sector_avg: Average volatility for sector (default 20%)
        
    Returns:
        Interpretation string
    """
    volatility = safe_float(volatility)
    
    if volatility == 0:
        return "Insufficient data"
    
    diff = volatility - sector_avg
    if abs(diff) < 2:
        return f"Normal for sector ({volatility:.1f}%)"
    elif diff > 0:
        return f"Higher than sector average (+{diff:.1f}%)"
    else:
        return f"Lower than sector average ({diff:.1f}%)"
