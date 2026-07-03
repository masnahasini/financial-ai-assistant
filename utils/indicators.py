import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator


def add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return data
    result = data.copy()
    close = result["Close"].astype(float)
    result["SMA_20"] = SMAIndicator(close=close, window=20).sma_indicator()
    result["SMA_50"] = SMAIndicator(close=close, window=50).sma_indicator()
    result["RSI"] = RSIIndicator(close=close, window=14).rsi()
    result["Daily_Return"] = close.pct_change()
    result["Volatility"] = result["Daily_Return"].rolling(window=20).std() * np.sqrt(252) * 100
    return result


def calculate_indicator_snapshot(data: pd.DataFrame) -> dict:
    enriched = add_indicators(data)
    latest = enriched.iloc[-1]
    daily_returns = enriched["Daily_Return"].dropna()
    volatility = float(daily_returns.std() * np.sqrt(252) * 100) if not daily_returns.empty else 0
    return {
        "sma_20": round(_safe_float(latest.get("SMA_20")), 2),
        "sma_50": round(_safe_float(latest.get("SMA_50")), 2),
        "rsi": round(_safe_float(latest.get("RSI")), 2),
        "volatility": round(volatility, 2),
        "daily_return": round(_safe_float(latest.get("Daily_Return")) * 100, 2),
        "series": {
            "SMA_20": enriched["SMA_20"],
            "SMA_50": enriched["SMA_50"],
            "RSI": enriched["RSI"],
            "Daily_Return": enriched["Daily_Return"],
            "Volatility": enriched["Volatility"],
        },
    }


def _safe_float(value) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(value)
