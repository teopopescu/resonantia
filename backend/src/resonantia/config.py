"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "Resonantia"
    debug: bool = False

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

    # --- Storage ---
    upload_dir: str = "./uploads"
    microscopy_dir: str = "./uploads/microscopy"
    thumbnail_size: tuple[int, int] = (256, 256)

    # --- Temporal ---
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "resonantia-tasks"

    # --- Langfuse ---
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # --- eLabFTW ---
    elabftw_url: str = ""
    elabftw_api_key: str = ""

    # --- Voice ---
    tts_voice: str = "nova"
    tts_model: str = "tts-1"
    stt_model: str = "whisper-1"

    # --- CORS ---
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
