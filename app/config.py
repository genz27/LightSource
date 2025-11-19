"""Central configuration for LightSource backend.

Values default to the provided PostgreSQL instance; override via environment variables
in non-development environments to avoid hard-coding secrets.
"""
from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, env_file=".env", env_file_encoding="utf-8")

    postgres_host: str = Field("localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_user: str = Field("postgres", env="POSTGRES_USER")
    postgres_password: str = Field("postgres", env="POSTGRES_PASSWORD")
    postgres_db: str = Field("lightsource", env="POSTGRES_DB")

    # Optional full DSN override
    database_url: str | None = Field(None, env="DATABASE_URL")

    storage_base: str = Field(..., env="STORAGE_BASE")
    cors_origins: list[str] = Field(..., env="CORS_ORIGINS")
    public_api_key: str | None = Field(None, env="PUBLIC_API_KEY")
    rate_limit_per_minute: int = Field(..., env="RATE_LIMIT_PER_MINUTE")
    burst_limit: int = Field(..., env="BURST_LIMIT")

    # Debug flag for provider call tracing
    debug: bool = Field(False, env="DEBUG")

    # External image upload for qwen-image-edit (Cloudflare Worker)
    ext_image_upload_base: str | None = Field("https://img.scdn.io/api/v1.php", env="EXT_IMAGE_UPLOAD_BASE")
    ext_image_upload_auth_key: str | None = Field(None, env="EXT_IMAGE_UPLOAD_AUTH_KEY")

    # Features (WebSocket removed; system uses HTTPS polling only)

    # Auth
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_access_minutes: int = Field(..., env="JWT_ACCESS_MINUTES")
    jwt_refresh_minutes: int = Field(..., env="JWT_REFRESH_MINUTES")

    frontend_dist: str | None = Field(None, env="FRONTEND_DIST")
    

    @property
    def db_dsn(self) -> str:
        """Return SQLAlchemy/PostgreSQL DSN.

        DATABASE_URL takes precedence if provided. Otherwise, build from individual
        fields using psycopg2 driver.
        """

        if self.database_url:
            return self.database_url

        return (
            "postgresql+psycopg2://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache()
def get_settings() -> Settings:
    """Load and cache settings instance."""

    return Settings()
