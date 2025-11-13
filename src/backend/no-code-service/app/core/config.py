"""Runtime configuration for the no-code service."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional


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
            "postgresql+pg8000://nocode_service_user:alphintra@123@localhost:5432/alphintra_nocode_service",
        )
    )
    cloud_sql_connection_name: str = field(
        default_factory=lambda: os.getenv(
            "CLOUD_SQL_CONNECTION_NAME",
            ""
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
            "http://auth-service.alphintra.svc.cluster.local:8009",
        )
    )
    aiml_service_url: str = field(
        default_factory=lambda: os.getenv(
            "AIML_SERVICE_URL",
            "http://ai-ml-strategy-service.alphintra.svc.cluster.local:8002",
        )
    )

    dev_mode: bool = field(default_factory=lambda: _bool(os.getenv("DEV_MODE", "true"), True))
    cors_allow_origins: List[str] = field(
        default_factory=lambda: _list(os.getenv("CORS_ALLOW_ORIGINS"))
    )

    prometheus_enabled: bool = field(
        default_factory=lambda: _bool(os.getenv("PROMETHEUS_ENABLED", "true"), True)
    )
    use_new_compiler: bool = field(
        default_factory=lambda: _bool(os.getenv("USE_NEW_COMPILER", "true"), True)
    )
    shadow_compile_enabled: bool = field(
        default_factory=lambda: _bool(os.getenv("SHADOW_COMPILE_ENABLED", "false"), False)
    )
    telemetry_file: Optional[str] = field(
        default_factory=lambda: os.getenv("TELEMETRY_FILE")
    )
    regression_output_modes: List[str] = field(
        default_factory=lambda: _list(os.getenv("REGRESSION_OUTPUT_MODES", "BACKTESTING,LIVE_TRADING,TRAINING"))
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
