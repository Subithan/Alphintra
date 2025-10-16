"""FastAPI application factory."""

from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from migrations.run_migrations import apply_all_migrations

from .core.config import get_settings
from .core.http import close_http_client
from .core.metrics import setup_metrics

logger = logging.getLogger(__name__)


def _cors_origins(settings) -> List[str]:
    return settings.cors_allow_origins or ["*"]


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    settings = get_settings()
    app = FastAPI(
        title=settings.service_name,
        description=settings.description,
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(settings),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_metrics(app)

    @app.on_event("startup")
    async def _run_startup_tasks():
        try:
            logger.info("Running database migrations on startup...")
            apply_all_migrations()
            logger.info("Database migrations completed.")
        except Exception:  # pragma: no cover - logging path
            logger.exception("Database migration failed")
            if not settings.dev_mode:
                raise

    @app.on_event("shutdown")
    async def _run_shutdown_tasks():
        await close_http_client()

    return app
