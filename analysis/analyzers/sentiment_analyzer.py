"""Sentiment analyzer - Analyzes news sentiment."""
import logging
from typing import Dict, Any, List

from services.sentiment_service import SentimentService

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment from news articles."""
    
    def __init__(self):
        self.sentiment_service = SentimentService()
    
    def analyze(
        self,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze sentiment from articles.
        
        Args:
            articles: List of article dictionaries with title, description
            
        Returns:
            Dictionary with:
                - overall_sentiment: str (Positive, Neutral, Negative)
                - confidence: float (0-1)
                - average_textblob: float
                - average_vader: float
                - sentiment_counts: {Positive, Neutral, Negative}
                - articles: List of articles with sentiment scores
        """
        if not articles:
            logger.debug("No articles to analyze")
            return self._empty_sentiment()
        
        # Use existing sentiment service
        result = self.sentiment_service.analyze_articles(articles)
        
        # Add confidence score
        confidence = self._compute_confidence(result["sentiment_counts"])
        result["confidence"] = confidence
        
        logger.debug(f"Sentiment analysis: {result['overall_sentiment']} (conf: {confidence:.2f})")
        return result
    
    def _compute_confidence(self, sentiment_counts: Dict[str, int]) -> float:
        """Compute confidence in sentiment assessment.
        
        Args:
            sentiment_counts: {Positive, Neutral, Negative} counts
            
        Returns:
            Confidence score (0-1)
        """
        total = sum(sentiment_counts.values())
        if total == 0:
            return 0.0
        
        # Confidence is how dominant the majority sentiment is
        max_count = max(sentiment_counts.values())
        confidence = max_count / total
        
        return confidence
    
    def _empty_sentiment(self) -> Dict[str, Any]:
        """Return empty sentiment structure."""
        return {
            "overall_sentiment": "Neutral",
            "confidence": 0.0,
            "average_textblob": 0.0,
            "average_vader": 0.0,
            "sentiment_counts": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "articles": [],
        }
