"""Redis utilities."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import redis

from .config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_redis_client() -> Optional[redis.Redis]:
    """Return shared Redis client instance or None when connection fails."""

    settings = get_settings()
    try:
        return redis.from_url(settings.redis_url)
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.warning("Redis connection failed, disabling cache: %s", exc)
        return None
