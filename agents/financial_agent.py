import logging
import os
from typing import Any

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from services.news_service import NewsService
from services.sentiment_service import SentimentService
from services.stock_service import StockService
from utils.helpers import dataframe_to_records, safe_float


logger = logging.getLogger(__name__)


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


class FinancialResearchAgent:
    """Coordinates market data, indicators, sentiment, and Gemini summaries."""

    def __init__(
        self,
        stock_service: StockService | None = None,
        news_service: NewsService | None = None,
        sentiment_service: SentimentService | None = None,
    ):
        self.stock_service = stock_service or StockService()
        self.news_service = news_service or NewsService()
        self.sentiment_service = sentiment_service or SentimentService()
        self.llm = self._build_llm()

    def _build_llm(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY is not configured; using deterministic local summaries.")
            return None
        model_name = os.getenv("GOOGLE_MODEL", DEFAULT_GEMINI_MODEL)
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.2)

    def research_stock(self, symbol: str, period: str = "1y") -> dict[str, Any]:
        try:
            history = self.stock_service.get_history(symbol, period=period)
            if history.empty:
                return {
                    "error": (
                        f"No historical data found for {symbol}. Yahoo Finance may be rate-limiting requests. "
                        "Wait 1-2 minutes and try again."
                    )
                }
            quote = self.stock_service.get_quote(symbol, history=history.tail(5))

            technical = self.stock_service.get_technical_indicators(history)
            series = technical.pop("series")
            for name, values in series.items():
                history[name] = values

            articles = self.news_service.fetch_company_news(symbol, limit=10)
            sentiment = self.sentiment_service.analyze_articles(articles)
            trade_signal = self.generate_trade_signal(quote, technical, sentiment)
            ai_summary = self.generate_research_summary(symbol, quote, technical, sentiment, articles)

            return {
                "symbol": symbol,
                "quote": quote,
                "history": history,
                "indicators": technical,
                "news": articles,
                "sentiment": sentiment,
                "trade_signal": trade_signal,
                "ai_summary": ai_summary,
            }
        except Exception as exc:
            logger.exception("Research failed for %s", symbol)
            return {"error": f"Unable to complete research for {symbol}: {exc}"}

    def compare_stocks(self, symbol_a: str, symbol_b: str) -> dict[str, Any]:
        try:
            rows = []
            histories = {}
            for symbol in [symbol_a, symbol_b]:
                history = self.stock_service.get_history(symbol, period="1y")
                if history.empty:
                    return {"error": f"No data found for {symbol}."}
                histories[symbol] = history
                indicators = self.stock_service.get_technical_indicators(history)
                articles = self.news_service.fetch_company_news(symbol, limit=5)
                sentiment = self.sentiment_service.analyze_articles(articles)
                returns = (history["Close"].iloc[-1] / history["Close"].iloc[0] - 1) * 100
                rows.append(
                    {
                        "Symbol": symbol,
                        "Returns %": round(float(returns), 2),
                        "Volatility %": round(safe_float(indicators.get("volatility")), 2),
                        "Average Volume": round(float(history["Volume"].mean()), 0),
                        "RSI": round(safe_float(indicators.get("rsi")), 2),
                        "Sentiment": sentiment.get("overall_sentiment", "Neutral"),
                        "Trade Signal": self.generate_trade_signal({}, indicators, sentiment)["action"],
                    }
                )
            return {"table": pd.DataFrame(rows), "histories": histories}
        except Exception as exc:
            logger.exception("Stock comparison failed")
            return {"error": f"Unable to compare stocks: {exc}"}

    def generate_research_summary(
        self,
        symbol: str,
        quote: dict[str, Any],
        indicators: dict[str, Any],
        sentiment: dict[str, Any],
        articles: list[dict[str, Any]],
    ) -> str:
        if self.llm is None:
            return self._fallback_summary(symbol, quote, indicators, sentiment)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a cautious senior financial research assistant for Indian equities. "
                    "Use only the supplied data. Avoid guaranteed predictions. Include a practical trading view.",
                ),
                (
                    "human",
                    """
Create a concise stock research report for {symbol}.

Required sections:
1. Company overview
2. Market sentiment
3. Technical analysis summary
4. Risk assessment
5. Trade setup
6. Final recommendation

Quote data:
{quote}

Technical indicators:
{indicators}

Sentiment:
{sentiment}

Trade signal:
{trade_signal}

Recent news:
{news}
""",
                ),
            ]
        )
        try:
            chain = prompt | self.llm
            response = chain.invoke(
                {
                    "symbol": symbol,
                    "quote": quote,
                    "indicators": indicators,
                    "sentiment": sentiment,
                    "trade_signal": self.generate_trade_signal(quote, indicators, sentiment),
                    "news": dataframe_to_records(pd.DataFrame(articles)),
                }
            )
            return response.content if hasattr(response, "content") else str(response)
        except Exception:
            logger.exception("Gemini summary failed; returning local fallback summary.")
            return self._fallback_summary(symbol, quote, indicators, sentiment)

    def generate_trade_signal(
        self,
        quote: dict[str, Any],
        indicators: dict[str, Any],
        sentiment: dict[str, Any],
    ) -> dict[str, Any]:
        current_price = safe_float(quote.get("current_price"))
        sma_20 = safe_float(indicators.get("sma_20"))
        sma_50 = safe_float(indicators.get("sma_50"))
        rsi = safe_float(indicators.get("rsi"))
        daily_return = safe_float(indicators.get("daily_return"))
        sentiment_label = sentiment.get("overall_sentiment", "Neutral")

        score = 0
        reasons = []

        if current_price and sma_20 and current_price > sma_20:
            score += 1
            reasons.append("price is above the 20-day moving average")
        elif current_price and sma_20:
            score -= 1
            reasons.append("price is below the 20-day moving average")

        if current_price and sma_50 and current_price > sma_50:
            score += 1
            reasons.append("price is above the 50-day moving average")
        elif current_price and sma_50:
            score -= 1
            reasons.append("price is below the 50-day moving average")

        if rsi < 35:
            score += 1
            reasons.append("RSI suggests the stock is near oversold territory")
        elif rsi > 70:
            score -= 1
            reasons.append("RSI suggests the stock is near overbought territory")

        if sentiment_label == "Positive":
            score += 1
            reasons.append("recent news sentiment is positive")
        elif sentiment_label == "Negative":
            score -= 1
            reasons.append("recent news sentiment is negative")

        if daily_return > 2:
            reasons.append("the latest daily move is strong, so entries may need patience")
        elif daily_return < -2:
            reasons.append("the latest daily move is weak, so risk control matters")

        if score >= 2:
            action = "Buy"
            buy_view = "Look for entries on small pullbacks while price holds above SMA 20 and SMA 50."
            sell_view = "Consider taking profit near resistance or if RSI moves above 70 and momentum fades."
        elif score <= -2:
            action = "Sell"
            buy_view = "Avoid fresh long entries until price reclaims key moving averages."
            sell_view = "Existing holders may consider trimming on weak rebounds or if sentiment stays negative."
        else:
            action = "Hold"
            buy_view = "Wait for a clearer confirmation from price trend, RSI, and sentiment alignment."
            sell_view = "Review again if price breaks below SMA 50 or momentum improves above both moving averages."

        return {
            "action": action,
            "score": score,
            "buy_view": buy_view,
            "sell_view": sell_view,
            "rationale": "; ".join(reasons) if reasons else "Signal is based on available technical and sentiment inputs.",
        }

    def _fallback_summary(
        self,
        symbol: str,
        quote: dict[str, Any],
        indicators: dict[str, Any],
        sentiment: dict[str, Any],
    ) -> str:
        rsi = safe_float(indicators.get("rsi"))
        volatility = safe_float(indicators.get("volatility"))
        trend = "above" if safe_float(quote.get("current_price")) >= safe_float(indicators.get("sma_50")) else "below"
        sentiment_label = sentiment.get("overall_sentiment", "Neutral")
        trade_signal = self.generate_trade_signal(quote, indicators, sentiment)

        return f"""
### Company overview
{symbol} is an Indian listed equity. The latest available market price is {quote.get("current_price")}.

### Market sentiment
Recent news sentiment is {sentiment_label}. Positive, neutral, and negative counts are {sentiment.get("sentiment_counts")}.

### Technical analysis summary
The stock is trading {trend} its 50-day simple moving average. RSI is {rsi:.2f}, and annualized volatility is approximately {volatility:.2f}%.

### Risk assessment
Key risks include market volatility, sector-specific developments, earnings surprises, liquidity conditions, and news-driven price gaps.

### Trade setup
Current signal: {trade_signal['action']}

Buy view: {trade_signal['buy_view']}

Sell view: {trade_signal['sell_view']}

Signal rationale: {trade_signal['rationale']}

### Final recommendation
{trade_signal['action']}. Confirm with your risk tolerance, capital allocation rules, and stop-loss discipline before acting.
"""
