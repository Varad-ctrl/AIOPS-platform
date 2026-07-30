"""
Centralized application configuration.

All settings are loaded from environment variables (or a .env file) using
pydantic-settings. Nothing sensitive is hardcoded here - see .env.example
for the full list of variables this application expects.
"""
from functools import lru_cache
from typing import ClassVar

from pydantic import field_validator
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
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        return v

    # --- AI / LLM provider (Module 5.1) ---
    # LLM_PROVIDER selects a preset base URL + default model; any of the
    # three can still be overridden individually via LLM_BASE_URL/LLM_MODEL.
    # groq   -> fast + generous free tier, recommended for local development
    # openai -> production-grade, official OpenAI API
    # ollama -> fully local, no API key required, needs `ollama serve` running
    LLM_PROVIDER: str = "groq"  # groq | openai | ollama
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""  # overrides the provider preset when set
    LLM_MODEL: str = ""  # overrides the provider preset when set
    # Back-compat: earlier phases used OPENAI_API_KEY directly. Still read
    # as a fallback so existing .env files don't silently stop working.
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "aiops-assistant@example.com"

    # --- Kubernetes ---
    KUBE_CONTEXT: str | None = None
    PROMETHEUS_URL: str = "http://prometheus:9090"
    GRAFANA_URL: str = "http://grafana:3000"
    LOKI_URL: str = "http://loki:3100"
    JENKINS_URL: str = ""
    JENKINS_USER: str = ""
    JENKINS_API_TOKEN: str = ""

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Provider presets: (base_url, default_model). Ollama needs no API key -
    # it's a local server, so LLM_API_KEY can stay empty for that provider.
    LLM_PRESETS: ClassVar[dict] = {
        "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
        "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
        "ollama": ("http://host.docker.internal:11434/v1", "llama3"),
    }

    def resolve_llm_config(self) -> dict:
        """Resolves the effective (api_key, base_url, model) for AIService,
        applying provider presets first and letting explicit overrides and
        legacy OPENAI_* settings win."""
        preset_base_url, preset_model = self.LLM_PRESETS.get(
            self.LLM_PROVIDER, self.LLM_PRESETS["openai"]
        )
        api_key = self.LLM_API_KEY or self.OPENAI_API_KEY
        base_url = self.LLM_BASE_URL or self.OPENAI_BASE_URL or preset_base_url
        model = self.LLM_MODEL or preset_model
        # Ollama doesn't check the key, but the OpenAI-compatible client
        # still expects an Authorization header - any non-empty string works.
        if self.LLM_PROVIDER == "ollama" and not api_key:
            api_key = "ollama-local"
        return {"api_key": api_key, "base_url": base_url, "model": model}


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance - avoids re-parsing env vars on every call."""
    return Settings()


settings = get_settings()
