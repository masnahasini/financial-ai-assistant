"""Analysis models - Data classes for analysis results."""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class ResearchReport:
    """Complete research report for a stock."""
    symbol: str
    quote: Dict[str, Any]
    history: Any  # pd.DataFrame
    indicators: Dict[str, Any]
    health_scores: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    sentiment: Dict[str, Any]
    trade_signal: Dict[str, Any]
    ai_summary: str
    validation_errors: List[str]
    timestamp: Optional[str] = None


@dataclass
class Recommendation:
    """Trade recommendation."""
    action: str  # BUY, HOLD, SELL
    confidence: float  # 0-1
    reasons: List[str]
    buy_view: str
    sell_view: str
    ai_explanation: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result from analyzing a stock."""
    technical: Dict[str, Any]
    sentiment: Dict[str, Any]
    recommendation: Recommendation
