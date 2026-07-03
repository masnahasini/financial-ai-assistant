import logging
import os
from datetime import datetime, timedelta
from typing import Any

import requests


logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        self.endpoint = "https://newsapi.org/v2/everything"

    def fetch_company_news(self, symbol: str, limit: int = 10) -> list[dict[str, Any]]:
        company_query = symbol.replace(".NS", "").replace(".BO", "")
        if not self.api_key:
            logger.warning("NEWS_API_KEY is not configured; returning empty news list.")
            return []

        params = {
            "q": f"{company_query} stock OR shares OR NSE OR BSE",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": limit,
            "from": (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d"),
            "apiKey": self.api_key,
        }
        try:
            response = requests.get(self.endpoint, params=params, timeout=15)
            response.raise_for_status()
            payload = response.json()
            articles = payload.get("articles", [])
            return [
                {
                    "title": item.get("title") or "",
                    "description": item.get("description") or "",
                    "url": item.get("url") or "",
                    "source": (item.get("source") or {}).get("name", ""),
                    "published_at": item.get("publishedAt") or "",
                }
                for item in articles[:limit]
            ]
        except Exception as exc:
            logger.exception("Failed to fetch news for %s", symbol)
            return [
                {
                    "title": f"News fetch unavailable for {symbol}",
                    "description": str(exc),
                    "url": "",
                    "source": "Local error handler",
                    "published_at": datetime.utcnow().isoformat(),
                }
            ]
