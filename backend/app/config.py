from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Single env file at the repo root, shared with the frontend.
# app/ -> backend/ -> repo root
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_ENV, extra="ignore")

    database_url: str = ""
    # Direct (non-pooled) connection, used by Alembic only. Falls back to
    # database_url when unset.
    direct_database_url: str = ""
    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    google_api_key: str = ""
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"
    debug: bool = False
    sentry_dsn: str = ""
    # Number of trusted reverse proxies sitting in front of this app (e.g.
    # Railway's edge). Only this many hops of X-Forwarded-For are trusted;
    # 0 (the default, correct for local dev) means the header is ignored
    # entirely and the socket peer address is used instead.
    trusted_proxy_count: int = 0

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins as a clean list, ignoring blanks and trailing slashes."""
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def migration_database_url(self) -> str:
        """Connection string Alembic should use for DDL."""
        return self.direct_database_url or self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
