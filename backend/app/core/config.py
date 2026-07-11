"""
Centralized application configuration.

All settings are loaded from environment variables (or a .env file) using
pydantic-settings. Nothing sensitive is hardcoded here - see .env.example
for the full list of variables this application expects.
"""
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    PROJECT_NAME: str = "AIOps Assistant"
    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Security / JWT ---
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:password@postgres:5432/aiops_db"
    )
    DB_ECHO: bool = False

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        return v

    # --- Third-party integrations (used in later phases, wired now) ---
    OPENAI_API_KEY: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "aiops-assistant@example.com"

    PROMETHEUS_URL: str = "http://prometheus:9090"
    GRAFANA_URL: str = "http://grafana:3000"
    LOKI_URL: str = "http://loki:3100"
    JENKINS_URL: str = ""

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance - avoids re-parsing env vars on every call."""
    return Settings()


settings = get_settings()
