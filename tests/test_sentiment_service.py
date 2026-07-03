from services.sentiment_service import SentimentService


def test_positive_sentiment_text():
    service = SentimentService()
    result = service.analyze_text("Strong earnings growth and excellent business momentum.")
    assert result["label"] == "Positive"


def test_article_sentiment_counts():
    service = SentimentService()
    result = service.analyze_articles(
        [
            {"title": "Company reports strong profit", "description": "Investors are optimistic."},
            {"title": "Stock remains unchanged", "description": "Market waits for earnings."},
        ]
    )
    assert sum(result["sentiment_counts"].values()) == 2
