"""Centralized configuration for the CareerFarm AI package.

This is the single source of truth for anything environment-specific
or tunable (credentials, model selection, generation parameters).
No other module should read from `os.environ` or hardcode these values.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str

    gemini_model: str = "gemini-flash-lite-latest"
    temperature: float = 0.2
    max_output_tokens: int = 2048

    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached, process-wide Settings instance.

    Cached so the .env file is parsed once and every module shares the
    same configuration object instead of re-instantiating Settings.
    """
    return Settings()