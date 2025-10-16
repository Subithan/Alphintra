"""Runtime configuration for the no-code service."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _list(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    """Application wide settings sourced from environment variables."""

    service_name: str = field(default="Alphintra No-Code Service")
    description: str = field(
        default="Microservice for visual workflow builder and trading strategy management"
    )
    version: str = field(default="2.0.0")

    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://nocode_service_user:nocode_service_pass@postgresql-primary.alphintra.svc.cluster.local:5432/alphintra_nocode",
        )
    )
    redis_url: str = field(
        default_factory=lambda: os.getenv(
            "REDIS_URL",
            "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/2",
        )
    )
    auth_service_url: str = field(
        default_factory=lambda: os.getenv(
            "AUTH_SERVICE_URL",
            "http://auth-service.alphintra.svc.cluster.local:8080",
        )
    )
    aiml_service_url: str = field(
        default_factory=lambda: os.getenv(
            "AIML_SERVICE_URL",
            "http://ai-ml-strategy-service.alphintra.svc.cluster.local:8000",
        )
    )

    dev_mode: bool = field(default_factory=lambda: _bool(os.getenv("DEV_MODE", "true"), True))
    cors_allow_origins: List[str] = field(
        default_factory=lambda: _list(os.getenv("CORS_ALLOW_ORIGINS"))
    )

    prometheus_enabled: bool = field(
        default_factory=lambda: _bool(os.getenv("PROMETHEUS_ENABLED", "true"), True)
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
