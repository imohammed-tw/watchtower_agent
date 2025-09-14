"""
Configuration settings for AI Watchtower
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import pytz
from datetime import datetime


class Settings(BaseSettings):
    """Application settings"""

    # API Keys
    openai_api_key: str = ""
    perplexity_api_key: str = ""

    # App Settings
    secret_key: str = "your-secret-key-change-this"
    debug: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./ai_watchtower_new.db"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Agent Settings
    max_articles_per_source: int = 50
    analysis_batch_size: int = 10
    content_cache_ttl: int = 3600

    # NEW: Timezone and Date Settings
    timezone: str = "Asia/Kolkata"  # India Standard Time
    search_hours_daily: int = 24      # Hours to look back for daily newsletters
    search_days_weekly: int = 7       # Days to look back for weekly newsletters  
    search_days_monthly: int = 30     # Days to look back for monthly newsletters
    
    # Date format for searches
    date_format: str = "%Y-%m-%d"
    datetime_format: str = "%Y-%m-%d %H:%M:%S"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_user_timezone(self) -> pytz.BaseTzInfo:
        """Get configured timezone object"""
        try:
            return pytz.timezone(self.timezone)
        except pytz.UnknownTimeZoneError:
            print(f"⚠️ Unknown timezone: {self.timezone}, falling back to UTC")
            return pytz.UTC
    
    def get_current_time(self) -> datetime:
        """Get current time in configured timezone"""
        tz = self.get_user_timezone()
        return datetime.now(tz)
    
    def get_utc_time(self) -> datetime:
        """Get current UTC time"""
        return datetime.utcnow()


settings = Settings()
