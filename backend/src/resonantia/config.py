"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ProductionConfigError(RuntimeError):
    """Raised when production starts without required configuration."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "Resonantia"
    app_environment: str = "development"
    debug: bool = False
    demo_mode: bool = False

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/resonantia"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- LLM ---
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4o"
    default_provider: str = "anthropic"

    # Per-role model assignment (multi-agent topology)
    planner_model: str = "claude-sonnet-4-20250514"
    specialist_model: str = "claude-sonnet-4-20250514"
    critic_model: str = "claude-haiku-4-5-20251001"

    # --- Multi-agent topology ---
    # When true, chat goes through the orchestrator + specialists + critic
    # path in services/multi_agent/. When false, the legacy single-agent
    # loop in services/agent.py serves chat. Default off so existing
    # demos and tests keep their previous behavior.
    multi_agent_enabled: bool = False

    # --- Clerk ---
    clerk_secret_key: str = ""
    clerk_jwt_key: str = ""
    clerk_authorized_parties: list[str] = []

    # --- Storage ---
    storage_backend: str = "local"
    upload_dir: str = "./uploads"
    microscopy_dir: str = "./uploads/microscopy"
    thumbnail_size: tuple[int, int] = (256, 256)
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_prefix: str = "resonantia"
    s3_signed_url_expires_seconds: int = 3600

    # --- Temporal ---
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "resonantia-tasks"

    # --- Langfuse ---
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # --- OpenTelemetry ---
    otel_service_name: str = "resonantia-backend"
    otel_environment: str = "development"
    otel_exporter_otlp_endpoint: str = ""

    # --- eLabFTW ---
    elabftw_url: str = ""
    elabftw_api_key: str = ""

    # --- Voice ---
    tts_voice: str = "nova"
    tts_model: str = "gpt-4o-mini-tts"
    stt_model: str = "gpt-4o-transcribe"
    voice_input_retention_days: int = 30
    voice_output_retention_days: int = 7

    # --- CORS ---
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    def is_production(self) -> bool:
        return self.app_environment.lower() == "production" or self.otel_environment.lower() == "production"

    def validate_production(self) -> None:
        """Fail fast when production is missing critical configuration."""
        if not self.is_production():
            return

        missing: list[str] = []
        if self.demo_mode:
            missing.append("DEMO_MODE must be false in production")
        if not self.database_url or self.database_url.startswith("sqlite"):
            missing.append("DATABASE_URL")
        if not self.redis_url:
            missing.append("REDIS_URL")
        if not self.temporal_host:
            missing.append("TEMPORAL_HOST")
        if not self.clerk_secret_key:
            missing.append("CLERK_SECRET_KEY")

        provider = self.default_provider.lower()
        if provider == "openai" and not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        elif provider == "anthropic" and not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        elif provider not in {"openai", "anthropic"}:
            missing.append("DEFAULT_PROVIDER must be 'openai' or 'anthropic'")

        if self.storage_backend.lower() == "s3" and not self.s3_bucket:
            missing.append("S3_BUCKET")

        if missing:
            raise ProductionConfigError("Invalid production configuration: " + ", ".join(missing))


@lru_cache
def get_settings() -> Settings:
    return Settings()
