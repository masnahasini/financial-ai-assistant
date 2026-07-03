import logging
from typing import Any

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


logger = logging.getLogger(__name__)


class SentimentService:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()

    def analyze_text(self, text: str) -> dict[str, Any]:
        text = text or ""
        textblob_score = TextBlob(text).sentiment.polarity
        vader_score = self.vader.polarity_scores(text)["compound"]
        combined = (textblob_score + vader_score) / 2
        if combined > 0.05:
            label = "Positive"
        elif combined < -0.05:
            label = "Negative"
        else:
            label = "Neutral"
        return {
            "textblob": round(float(textblob_score), 4),
            "vader": round(float(vader_score), 4),
            "combined": round(float(combined), 4),
            "label": label,
        }

    def analyze_articles(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        if not articles:
            return {
                "overall_sentiment": "Neutral",
                "average_textblob": 0,
                "average_vader": 0,
                "sentiment_counts": {"Positive": 0, "Neutral": 0, "Negative": 0},
                "articles": [],
            }

        analyzed = []
        counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        for article in articles:
            text = f"{article.get('title', '')}. {article.get('description', '')}"
            scores = self.analyze_text(text)
            counts[scores["label"]] += 1
            analyzed.append({**article, **scores})

        avg_textblob = sum(item["textblob"] for item in analyzed) / len(analyzed)
        avg_vader = sum(item["vader"] for item in analyzed) / len(analyzed)
        overall = max(counts, key=counts.get)
        return {
            "overall_sentiment": overall,
            "average_textblob": round(avg_textblob, 4),
            "average_vader": round(avg_vader, 4),
            "sentiment_counts": counts,
            "articles": analyzed,
        }
