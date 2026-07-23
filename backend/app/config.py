from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Single env file at the repo root, shared with the frontend.
# app/ -> backend/ -> repo root
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_ENV, extra="ignore")

    database_url: str = ""
    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    anthropic_api_key: str = ""
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
