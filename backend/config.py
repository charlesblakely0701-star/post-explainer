"""Configuration module for the Post Explainer backend."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


# Find the .env file - check both backend dir and parent dir
def find_env_file() -> str:
    """Find .env file in current or parent directory."""
    current = Path(__file__).parent / ".env"
    parent = Path(__file__).parent.parent / ".env"
    
    if current.exists():
        return str(current)
    elif parent.exists():
        return str(parent)
    return ".env"  # fallback


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Required API Keys
    openai_api_key: str
    tavily_api_key: str
    
    # Optional API Keys
    anthropic_api_key: str | None = None
    brave_api_key: str | None = None
    
    # Optional Configuration
    redis_url: str | None = None
    debug: bool = False
    
    # LLM Settings
    openai_model: str = "gpt-4o"
    max_tokens: int = 1024
    temperature: float = 0.3
    
    # Search Settings
    max_search_results: int = 8
    search_timeout: int = 10
    
    # Cache Settings
    cache_ttl: int = 86400  # 24 hours
    
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

