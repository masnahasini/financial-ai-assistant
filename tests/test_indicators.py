import pandas as pd

from utils.indicators import add_indicators, calculate_indicator_snapshot


def sample_prices():
    return pd.DataFrame(
        {
            "Open": range(1, 61),
            "High": range(2, 62),
            "Low": range(0, 60),
            "Close": range(1, 61),
            "Volume": [1000] * 60,
        },
        index=pd.date_range("2024-01-01", periods=60),
    )


def test_add_indicators_creates_expected_columns():
    result = add_indicators(sample_prices())
    assert "SMA_20" in result.columns
    assert "SMA_50" in result.columns
    assert "RSI" in result.columns
    assert "Daily_Return" in result.columns
    assert "Volatility" in result.columns


def test_calculate_indicator_snapshot_returns_values():
    snapshot = calculate_indicator_snapshot(sample_prices())
    assert snapshot["sma_20"] > 0
    assert snapshot["sma_50"] > 0
    assert "series" in snapshot
