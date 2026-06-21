"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings with .env support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="AI Study Buddy API", alias="APP_NAME")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        alias="APP_ENV",
    )
    debug: bool = Field(default=False, alias="DEBUG")

    database_url: str = Field(
        default="sqlite:///./study_buddy.db",
        alias="DATABASE_URL",
    )

    cors_origins_raw: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    gemini_text_model: str = Field(
        default="gemini-2.5-flash",
        alias="GEMINI_TEXT_MODEL",
    )
    gemini_media_model: str = Field(
        default="gemini-3.1-pro-preview",
        alias="GEMINI_MEDIA_MODEL",
    )
    gemini_request_timeout_ms: int = Field(
        default=120_000,
        alias="GEMINI_REQUEST_TIMEOUT_MS",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins_raw.split(",")
            if origin.strip()
        ]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
