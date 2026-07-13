"""Realistic mock data for testing."""
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def get_sample_history(days: int = 100, symbol: str = "RELIANCE.NS") -> pd.DataFrame:
    """Generate realistic sample historical data.
    
    Args:
        days: Number of days of history
        symbol: Stock symbol
        
    Returns:
        DataFrame with OHLCV + indicators (SMA, RSI, Volatility)
    """
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate realistic price movement (random walk)
    np.random.seed(42)  # For reproducibility
    returns = np.random.normal(0.0005, 0.02, len(dates))  # 0.05% mean, 2% std
    price = 2750 * np.exp(np.cumsum(returns))  # Start at ~2750
    
    # Create OHLCV data
    data = pd.DataFrame({
        'Open': price * (1 + np.random.normal(0, 0.005, len(dates))),
        'High': price * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
        'Low': price * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
        'Close': price,
        'Volume': np.random.randint(1000000, 5000000, len(dates)),
        'Adj Close': price,
    }, index=dates)
    
    # Ensure High >= Close >= Low >= Open
    data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
    
    # Compute indicators
    close = data['Close'].astype(float)
    
    # SMA
    data['SMA_20'] = close.rolling(window=20).mean()
    data['SMA_50'] = close.rolling(window=50).mean()
    
    # RSI (simplified)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Daily return
    data['Daily_Return'] = close.pct_change()
    
    # Volatility (annualized)
    data['Volatility'] = data['Daily_Return'].rolling(window=20).std() * np.sqrt(252) * 100
    
    return data


def get_sample_quote(symbol: str = "RELIANCE.NS") -> dict:
    """Generate realistic sample quote data.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Quote dictionary
    """
    price = 2750.50
    previous_close = 2745.00
    change_percent = ((price - previous_close) / previous_close) * 100
    
    return {
        "symbol": symbol,
        "current_price": price,
        "open": 2745.00,
        "day_high": 2760.00,
        "day_low": 2740.00,
        "volume": 4500000,
        "market_cap": 3500000000000,
        "previous_close": previous_close,
        "change_percent": change_percent,
        "currency": "INR",
        "company_name": "Reliance Industries Limited",
        "sector": "Oil & Gas",
    }


def get_sample_articles(sentiment: str = "mixed") -> list:
    """Generate realistic sample news articles.
    
    Args:
        sentiment: "positive", "negative", or "mixed"
        
    Returns:
        List of article dictionaries
    """
    if sentiment == "positive":
        titles = [
            "Reliance profits surge on strong oil prices",
            "Reliance Q2 earnings beat analyst expectations",
            "Reliance expands renewable energy portfolio",
            "Foreign investors boost Reliance stake",
        ]
        descriptions = [
            "Strong quarterly results drive market sentiment",
            "Company guidance remains positive for FY2024",
            "Green energy initiatives attract institutional buyers",
            "Record profit margins on improved refining spreads",
        ]
    elif sentiment == "negative":
        titles = [
            "Reliance faces regulatory headwinds",
            "Oil prices fall, impacting Reliance margins",
            "Reliance stock drops on profit warning",
            "Supply chain disruptions hit production",
        ]
        descriptions = [
            "Refining margins compress amid oversupply",
            "Regulatory challenges in key markets",
            "Competition from renewables increases",
            "Earnings guidance cut for FY2024",
        ]
    else:  # mixed
        titles = [
            "Reliance profits surge on strong oil prices",
            "Oil prices fall, impacting Reliance margins",
            "Reliance expands renewable energy portfolio",
            "Reliance Q2 earnings beat analyst expectations",
            "Regulatory challenges in key markets",
            "Strong quarterly results drive market sentiment",
        ]
        descriptions = [
            "Mixed signals as oil prices fluctuate",
            "Q2 earnings beat but outlook uncertain",
            "Renewable energy growth offsets oil decline",
            "Global supply chain normalization underway",
            "Analyst ratings split on near-term outlook",
            "Long-term fundamentals remain solid",
        ]
    
    articles = []
    for i, (title, desc) in enumerate(zip(titles, descriptions)):
        articles.append({
            "title": title,
            "description": desc,
            "url": f"https://example.com/article-{i}",
            "source": "Financial News",
            "published_at": (datetime.now() - timedelta(days=i)).isoformat(),
        })
    
    return articles


def get_uptrend_indicators() -> dict:
    """Indicators showing a strong uptrend."""
    return {
        "current_price": 2800.00,
        "sma_20": 2780.00,
        "sma_50": 2750.00,
        "rsi": 65.0,
        "volatility": 18.5,
        "daily_return": 1.5,
    }


def get_downtrend_indicators() -> dict:
    """Indicators showing a strong downtrend."""
    return {
        "current_price": 2700.00,
        "sma_20": 2720.00,
        "sma_50": 2750.00,
        "rsi": 35.0,
        "volatility": 22.0,
        "daily_return": -1.8,
    }


def get_sideways_indicators() -> dict:
    """Indicators showing a sideways market."""
    return {
        "current_price": 2750.00,
        "sma_20": 2752.00,
        "sma_50": 2748.00,
        "rsi": 50.0,
        "volatility": 15.0,
        "daily_return": 0.1,
    }


def get_overbought_indicators() -> dict:
    """Indicators showing overbought conditions."""
    return {
        "current_price": 2850.00,
        "sma_20": 2810.00,
        "sma_50": 2750.00,
        "rsi": 75.0,
        "volatility": 20.0,
        "daily_return": 3.5,
    }


def get_oversold_indicators() -> dict:
    """Indicators showing oversold conditions."""
    return {
        "current_price": 2650.00,
        "sma_20": 2720.00,
        "sma_50": 2750.00,
        "rsi": 28.0,
        "volatility": 25.0,
        "daily_return": -3.8,
    }
