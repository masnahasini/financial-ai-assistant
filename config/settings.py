"""Application settings and configuration."""
import os
from functools import lru_cache


class Settings:
    """Application settings."""
    
    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    
    # Feature Flags (for gradual rollout)
    ENABLE_NEW_RESEARCH_UI: bool = os.getenv("ENABLE_NEW_RESEARCH_UI", "false").lower() == "true"
    ENABLE_NEW_HOME_PAGE: bool = os.getenv("ENABLE_NEW_HOME_PAGE", "false").lower() == "true"
    ENABLE_NEW_WORKFLOWS: bool = os.getenv("ENABLE_NEW_WORKFLOWS", "true").lower() == "true"
    
    # Cache Settings
    CACHE_QUOTE_TTL: int = 60  # 1 minute
    CACHE_NEWS_TTL: int = 900  # 15 minutes
    CACHE_HISTORY_TTL: int = 3600  # 1 hour
    
    # Research Settings
    RESEARCH_DEFAULT_PERIOD: str = "1y"
    RESEARCH_HISTORY_MIN_DAYS: int = 20  # Minimum days for indicators
    
    # Display Settings
    DISPLAY_CURRENCY: str = "INR"
    DISPLAY_DECIMAL_PLACES: int = 2
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get application settings (singleton)."""
    return Settings()


settings = get_settings()
