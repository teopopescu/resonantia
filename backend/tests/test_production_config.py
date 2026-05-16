"""Production configuration validation tests."""

from __future__ import annotations

import pytest

from resonantia.config import ProductionConfigError, Settings


def test_development_configuration_does_not_require_provider_keys():
    settings = Settings(app_environment="development", openai_api_key="", anthropic_api_key="")

    settings.validate_production()


def test_production_requires_configured_default_provider_key():
    settings = Settings(
        app_environment="production",
        database_url="postgresql+asyncpg://user:pass@db:5432/resonantia",
        redis_url="redis://redis:6379/0",
        temporal_host="temporal:7233",
        clerk_secret_key="clerk-secret",
        default_provider="openai",
        openai_api_key="",
        anthropic_api_key="",
    )

    with pytest.raises(ProductionConfigError, match="OPENAI_API_KEY"):
        settings.validate_production()


def test_production_accepts_anthropic_provider_key():
    settings = Settings(
        app_environment="production",
        database_url="postgresql+asyncpg://user:pass@db:5432/resonantia",
        redis_url="redis://redis:6379/0",
        temporal_host="temporal:7233",
        clerk_secret_key="clerk-secret",
        default_provider="anthropic",
        anthropic_api_key="anthropic-key",
    )

    settings.validate_production()


def test_production_disallows_demo_mode():
    settings = Settings(
        app_environment="production",
        demo_mode=True,
        database_url="postgresql+asyncpg://user:pass@db:5432/resonantia",
        redis_url="redis://redis:6379/0",
        temporal_host="temporal:7233",
        clerk_secret_key="clerk-secret",
        default_provider="openai",
        openai_api_key="openai-key",
    )

    with pytest.raises(ProductionConfigError, match="DEMO_MODE"):
        settings.validate_production()
