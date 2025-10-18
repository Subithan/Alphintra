"""API router registration."""

from __future__ import annotations

from fastapi import FastAPI

from .routes import library, workflows


def register_routes(app: FastAPI) -> None:
    """Attach all API routers to the FastAPI application."""

    app.include_router(workflows.router)
    app.include_router(library.router)
