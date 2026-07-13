"""Research workflow - Orchestrates the complete research pipeline."""
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import pandas as pd

from data.providers.stock_provider import StockProvider
from data.providers.news_provider import NewsProvider
from data.providers.cache import DataCache
from analysis.analyzers.technical_analyzer import TechnicalAnalyzer
from analysis.analyzers.sentiment_analyzer import SentimentAnalyzer
from analysis.analyzers.trade_signal_generator import TradeSignalGenerator
from analysis.models import ResearchReport, Recommendation

logger = logging.getLogger(__name__)


class ResearchWorkflow:
    """Orchestrates the complete research pipeline for a stock.
    
    Pipeline stages:
    1. Data Collection - Fetch quote, history, news in parallel
    2. Validation - Verify data quality
    3. Enrichment - Compute indicators, sentiment
    4. Analysis - Run all analyzers
    5. Recommendation - Generate signal and confidence
    6. Report - Assemble into ResearchReport
    """
    
    def __init__(
        self,
        cache: Optional[DataCache] = None,
        stock_provider: Optional[StockProvider] = None,
        news_provider: Optional[NewsProvider] = None,
    ):
        self.cache = cache or DataCache()
        self.stock_provider = stock_provider or StockProvider(self.cache)
        self.news_provider = news_provider or NewsProvider(self.cache)
        self.technical_analyzer = TechnicalAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.trade_signal_generator = TradeSignalGenerator()
    
    def research_stock(
        self,
        symbol: str,
        period: str = "1y"
    ) -> ResearchReport:
        """Execute complete research pipeline.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE.NS")
            period: Historical period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)
            
        Returns:
            ResearchReport with all analysis
        """
        logger.info(f"Starting research for {symbol}")
        
        # Stage 1: Data Collection
        try:
            collection = self._collect_data(symbol, period)
        except Exception as e:
            logger.error(f"Data collection failed for {symbol}: {e}")
            raise
        
        # Stage 2: Validation
        validation_errors = self._validate_data(collection)
        if collection.get("history", pd.DataFrame()).empty:
            logger.error(f"No historical data for {symbol}")
            raise RuntimeError(f"No historical data available for {symbol}")
        
        # Stage 3: Enrichment (done by StockService automatically)
        
        # Stage 4: Analysis
        try:
            technical_result = self.technical_analyzer.analyze(
                collection["history"],
                collection["quote"].get("current_price")
            )
            sentiment_result = self.sentiment_analyzer.analyze(
                collection["articles"]
            )
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}")
            raise
        
        # Stage 5: Recommendation
        try:
            signal = self.trade_signal_generator.generate(
                collection["quote"],
                technical_result["indicators"],
                sentiment_result
            )
        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {e}")
            raise
        
        # Stage 6: Report Assembly
        report = ResearchReport(
            symbol=symbol,
            quote=collection["quote"],
            history=collection["history"],
            indicators=technical_result["indicators"],
            health_scores=technical_result["health_scores"],
            technical_analysis=technical_result,
            sentiment=sentiment_result,
            trade_signal=signal,
            ai_summary=self._generate_ai_summary(symbol, technical_result, sentiment_result, signal),
            validation_errors=validation_errors,
            timestamp=datetime.now().isoformat(),
        )
        
        logger.info(f"Research completed for {symbol}: {signal['action']}")
        return report
    
    def _collect_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """Collect all required data.
        
        Args:
            symbol: Stock symbol
            period: Historical period
            
        Returns:
            Dictionary with history, quote, articles
        """
        logger.debug(f"Collecting data for {symbol}...")
        
        history = self.stock_provider.get_history(symbol, period)
        quote = self.stock_provider.get_quote(symbol)
        articles = self.news_provider.fetch_articles(symbol, limit=10)
        
        return {
            "history": history,
            "quote": quote,
            "articles": articles,
        }
    
    def _validate_data(self, collection: Dict[str, Any]) -> list[str]:
        """Validate data quality.
        
        Args:
            collection: Data collection result
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        history = collection.get("history", pd.DataFrame())
        if len(history) < 20:
            errors.append("Not enough historical data (need at least 20 days)")
        
        quote = collection.get("quote", {})
        if not quote.get("current_price"):
            errors.append("Unable to fetch current price")
        
        articles = collection.get("articles", [])
        if not articles:
            errors.append("No news articles found (sentiment analysis unavailable)")
        
        if errors:
            logger.warning(f"Validation errors: {errors}")
        
        return errors
    
    def _generate_ai_summary(
        self,
        symbol: str,
        technical: Dict[str, Any],
        sentiment: Dict[str, Any],
        signal: Dict[str, Any]
    ) -> str:
        """Generate AI-powered summary.
        
        For now, returns a deterministic summary.
        In production, this would call Gemini API.
        
        Args:
            symbol: Stock symbol
            technical: Technical analysis result
            sentiment: Sentiment analysis result
            signal: Trade signal
            
        Returns:
            Markdown-formatted summary
        """
        trend = technical["trend"]
        momentum = technical["health_scores"]["momentum"]["description"]
        sentiment_label = sentiment["overall_sentiment"]
        action = signal["action"]
        
        summary = f"""
### Investment Analysis: {symbol}

#### Current Market Position
{symbol} is currently in a **{trend}** with {momentum.lower()}. 
News sentiment is **{sentiment_label.lower()}**.

#### Recommendation: {action}
**Confidence Level:** {signal['confidence']:.0%}

#### Key Reasons
{"".join(f"- {reason}\n" for reason in signal['reasons'][:3])}

#### Trading View
**Buy Setup:** {signal['buy_view']}

**Sell Setup:** {signal['sell_view']}

#### Risk Considerations
- Market volatility may impact entry/exit timing
- News flow can rapidly change sentiment
- Position size should match your risk tolerance

*This analysis is for informational purposes only. Not investment advice.*
"""
        
        return summary
