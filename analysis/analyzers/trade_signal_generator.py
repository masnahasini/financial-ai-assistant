"""Trade signal generator - Generates buy/hold/sell signals."""
import logging
from typing import Dict, Any, Optional

from utils.helpers import safe_float

logger = logging.getLogger(__name__)


class TradeSignalGenerator:
    """Generates trading signals (BUY, HOLD, SELL) with confidence."""
    
    def generate(
        self,
        quote: Dict[str, Any],
        indicators: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a trade signal.
        
        Args:
            quote: Quote data with current_price
            indicators: Technical indicators (sma_20, sma_50, rsi, etc.)
            sentiment: Sentiment analysis (overall_sentiment, confidence)
            
        Returns:
            Dictionary with:
                - action: str (BUY, HOLD, SELL)
                - score: int (-3 to 3)
                - confidence: float (0-1)
                - reasons: List[str]
                - buy_view: str
                - sell_view: str
        """
        score = 0
        reasons = []
        
        # Extract values
        current_price = safe_float(quote.get("current_price"))
        sma_20 = safe_float(indicators.get("sma_20"))
        sma_50 = safe_float(indicators.get("sma_50"))
        rsi = safe_float(indicators.get("rsi"))
        daily_return = safe_float(indicators.get("daily_return"))
        sentiment_label = sentiment.get("overall_sentiment", "Neutral")
        
        # Trend scoring
        if current_price > sma_20 and sma_20 > sma_50:
            score += 1
            reasons.append("Price above both moving averages (strong uptrend)")
        elif current_price > sma_50 and current_price < sma_20:
            score += 0  # Neutral in uptrend
            reasons.append("Price in uptrend but below SMA20")
        elif current_price < sma_50:
            score -= 1
            reasons.append("Price below SMA50 (downtrend)")
        
        # RSI scoring
        if rsi < 30:
            score += 1
            reasons.append("RSI oversold (<30), bounce potential")
        elif rsi > 70:
            score -= 1
            reasons.append("RSI overbought (>70), pullback risk")
        elif 40 < rsi < 60:
            score += 0  # Neutral momentum
        
        # Sentiment scoring
        if sentiment_label == "Positive":
            score += 1
            reasons.append("News sentiment is positive")
        elif sentiment_label == "Negative":
            score -= 1
            reasons.append("News sentiment is negative")
        
        # Daily move note
        if daily_return > 2:
            reasons.append("Strong move today, consider entry on pullback")
        elif daily_return < -2:
            reasons.append("Weak move today, monitor for confirmation")
        
        # Determine action
        if score >= 2:
            action = "BUY"
            buy_view = "Look for pullbacks to SMA20 while above SMA50. Stop loss below SMA50."
            sell_view = "Take profit near resistance or if RSI exceeds 70 and momentum fades."
        elif score <= -2:
            action = "SELL"
            buy_view = "Avoid new longs until price reclaims SMA50 and sentiment improves."
            sell_view = "Consider trimming on weak bounces. Watch for support levels."
        else:
            action = "HOLD"
            buy_view = "Wait for clearer trend confirmation from price and indicators."
            sell_view = "Monitor for break below SMA50 or negative sentiment shift."
        
        # Compute confidence
        confidence = self._compute_confidence(score, sentiment)
        
        result = {
            "action": action,
            "score": score,
            "confidence": confidence,
            "reasons": reasons,
            "buy_view": buy_view,
            "sell_view": sell_view,
        }
        
        logger.debug(f"Trade signal: {action} (score: {score}, confidence: {confidence:.2f})")
        return result
    
    def _compute_confidence(self, score: int, sentiment: Dict[str, Any]) -> float:
        """Compute confidence in the signal.
        
        Args:
            score: Signal score (-3 to 3)
            sentiment: Sentiment analysis with confidence
            
        Returns:
            Confidence (0-1)
        """
        # Base confidence from signal strength
        base = abs(score) / 3.0  # 0-1
        
        # Adjust for sentiment confidence
        sentiment_conf = sentiment.get("confidence", 0.5)
        
        # Average them
        confidence = (base + sentiment_conf) / 2
        
        return min(1.0, confidence)
