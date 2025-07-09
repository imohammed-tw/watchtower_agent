"""
Configuration settings for AI Watchtower
"""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings"""

    # API Keys
    openai_api_key: str = ""
    perplexity_api_key: str = ""

    # App Settings
    secret_key: str = "your-secret-key-change-this"
    debug: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./ai_watchtower.db"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Agent Settings
    max_articles_per_source: int = 50
    analysis_batch_size: int = 10
    content_cache_ttl: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
