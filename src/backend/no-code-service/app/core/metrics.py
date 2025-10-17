"""Prometheus instrumentation helpers."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .config import get_settings

_instrumentator: Optional[Instrumentator] = None


def setup_metrics(app: FastAPI) -> None:
    """Attach Prometheus instrumentation to the FastAPI application."""

    settings = get_settings()
    if not settings.prometheus_enabled:
        return

    global _instrumentator
    if _instrumentator is None:
        _instrumentator = Instrumentator()
        _instrumentator.instrument(app).expose(app)
