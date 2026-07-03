import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yfinance as yf

from utils.indicators import add_indicators, calculate_indicator_snapshot


logger = logging.getLogger(__name__)

YFINANCE_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "yfinance-cache"
YFINANCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR))


class StockService:
    def get_quote(self, symbol: str, history: pd.DataFrame | None = None) -> dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            info = {}
            try:
                info = ticker.info or {}
            except Exception:
                logger.warning("ticker.info unavailable for %s", symbol)

            history_data = history.copy() if history is not None else self._download_history(symbol, period="5d")
            latest = history_data.iloc[-1] if not history_data.empty else {}
            previous_close = self._derive_previous_close(history_data, info.get("previousClose"))
            current_price = self._safe_scalar(latest, "Close", info.get("currentPrice"))
            change_percent = None
            if previous_close and current_price:
                change_percent = ((current_price - previous_close) / previous_close) * 100

            return {
                "symbol": symbol,
                "current_price": current_price,
                "open": self._safe_scalar(latest, "Open", info.get("open")),
                "day_high": self._safe_scalar(latest, "High", info.get("dayHigh")),
                "day_low": self._safe_scalar(latest, "Low", info.get("dayLow")),
                "volume": self._safe_scalar(latest, "Volume", info.get("volume")),
                "market_cap": info.get("marketCap"),
                "previous_close": previous_close,
                "change_percent": change_percent,
                "currency": info.get("currency", "INR"),
                "company_name": info.get("longName", symbol),
                "sector": info.get("sector", "Unknown"),
            }
        except Exception as exc:
            logger.exception("Failed to fetch quote for %s", symbol)
            return self._empty_quote(symbol)

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        try:
            data = self._download_history(symbol, period=period, interval=interval)
            if data.empty:
                logger.warning("No historical data returned for %s", symbol)
                return pd.DataFrame()
            return add_indicators(data)
        except Exception as exc:
            logger.exception("Failed to fetch history for %s", symbol)
            raise RuntimeError(f"Could not fetch history for {symbol}") from exc

    def get_technical_indicators(self, history: pd.DataFrame) -> dict[str, Any]:
        if history.empty:
            raise ValueError("Historical data is empty.")
        return calculate_indicator_snapshot(history)

    @staticmethod
    def _safe_scalar(mapping: Any, key: str, fallback: Any = None):
        try:
            value = mapping[key]
        except Exception:
            return fallback
        return fallback if value is None else value

    @staticmethod
    def _derive_previous_close(history: pd.DataFrame, fallback: Any = None):
        if history is not None and not history.empty:
            closes = history["Close"].dropna()
            if len(closes) >= 2:
                return float(closes.iloc[-2])
            if len(closes) == 1:
                return float(closes.iloc[-1])
        return fallback

    @staticmethod
    def _empty_quote(symbol: str) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "current_price": None,
            "open": None,
            "day_high": None,
            "day_low": None,
            "volume": None,
            "market_cap": None,
            "previous_close": None,
            "change_percent": None,
            "currency": "INR",
            "company_name": symbol,
            "sector": "Unknown",
        }

    @staticmethod
    def _download_history(symbol: str, period: str = "5d", interval: str = "1d") -> pd.DataFrame:
        last_error = None
        for attempt in range(3):
            try:
                data = yf.download(
                    symbol,
                    period=period,
                    interval=interval,
                    progress=False,
                    auto_adjust=False,
                    threads=False,
                )
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                data = data.dropna(how="all")
                if not data.empty:
                    return data
            except Exception as exc:
                last_error = exc
            try:
                data = StockService._download_history_via_chart_api(symbol, period=period, interval=interval)
                if not data.empty:
                    return data
            except Exception as exc:
                last_error = exc
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, interval=interval, auto_adjust=False)
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                data = data.dropna(how="all")
                if not data.empty:
                    return data
            except Exception as exc:
                last_error = exc
            if attempt < 2:
                time.sleep(1.5)
        if last_error is not None:
            logger.warning("History download failed for %s after retries: %s", symbol, last_error)
        return pd.DataFrame()

    @staticmethod
    def _download_history_via_chart_api(symbol: str, period: str = "5d", interval: str = "1d") -> pd.DataFrame:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "range": period,
            "interval": interval,
            "includePrePost": "false",
            "events": "div,splits",
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        payload = response.json()
        result = ((payload.get("chart") or {}).get("result") or [None])[0]
        if not result:
            return pd.DataFrame()

        timestamps = result.get("timestamp") or []
        quote = (((result.get("indicators") or {}).get("quote")) or [None])[0] or {}
        if not timestamps or not quote:
            return pd.DataFrame()

        frame = pd.DataFrame(
            {
                "Open": quote.get("open", []),
                "High": quote.get("high", []),
                "Low": quote.get("low", []),
                "Close": quote.get("close", []),
                "Volume": quote.get("volume", []),
            },
            index=pd.to_datetime([datetime.fromtimestamp(ts) for ts in timestamps]),
        )

        adjclose = (((result.get("indicators") or {}).get("adjclose")) or [None])[0] or {}
        if adjclose.get("adjclose"):
            frame["Adj Close"] = adjclose["adjclose"]

        return frame.dropna(how="all")
