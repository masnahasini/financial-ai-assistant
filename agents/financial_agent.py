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


DISCLAIMER = "Educational purposes only. This is not financial advice."
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
            ai_summary = self.generate_research_summary(symbol, quote, technical, sentiment, articles)

            return {
                "symbol": symbol,
                "quote": quote,
                "history": history,
                "indicators": technical,
                "news": articles,
                "sentiment": sentiment,
                "ai_summary": ai_summary,
                "disclaimer": DISCLAIMER,
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
                    "Use only the supplied data. Avoid guaranteed predictions. Always include the exact disclaimer.",
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
5. Final recommendation

Quote data:
{quote}

Technical indicators:
{indicators}

Sentiment:
{sentiment}

Recent news:
{news}

Mandatory disclaimer:
{disclaimer}
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
                    "news": dataframe_to_records(pd.DataFrame(articles)),
                    "disclaimer": DISCLAIMER,
                }
            )
            content = response.content if hasattr(response, "content") else str(response)
            if DISCLAIMER not in content:
                content = f"{content}\n\n{DISCLAIMER}"
            return content
        except Exception:
            logger.exception("Gemini summary failed; returning local fallback summary.")
            return self._fallback_summary(symbol, quote, indicators, sentiment)

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
        recommendation = "Hold / Watch"
        if rsi < 35 and sentiment_label == "Positive":
            recommendation = "Watch for accumulation opportunities"
        elif rsi > 70 or sentiment_label == "Negative":
            recommendation = "Exercise caution"

        return f"""
### Company overview
{symbol} is an Indian listed equity. The latest available market price is {quote.get("current_price")}.

### Market sentiment
Recent news sentiment is {sentiment_label}. Positive, neutral, and negative counts are {sentiment.get("sentiment_counts")}.

### Technical analysis summary
The stock is trading {trend} its 50-day simple moving average. RSI is {rsi:.2f}, and annualized volatility is approximately {volatility:.2f}%.

### Risk assessment
Key risks include market volatility, sector-specific developments, earnings surprises, liquidity conditions, and news-driven price gaps.

### Final recommendation
{recommendation}. Confirm with additional fundamental research and personal risk tolerance before acting.

{DISCLAIMER}
"""
