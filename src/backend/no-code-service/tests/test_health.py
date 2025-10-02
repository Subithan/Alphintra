"""Regression coverage for HTTP client lifecycle and health checks."""
from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import List

import pytest
from fastapi.testclient import TestClient


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "main.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("no_code_service_main", MODULE_PATH)
main = importlib.util.module_from_spec(SPEC)
sys.modules["no_code_service_main"] = main
assert SPEC.loader is not None
SPEC.loader.exec_module(main)


@pytest.fixture(autouse=True)
def _disable_migrations(monkeypatch):
    """Avoid running real migrations during tests."""
    monkeypatch.setattr(main, "apply_all_migrations", lambda: None)


def test_http_client_closed_on_shutdown():
    """The shared AsyncClient should close cleanly on shutdown."""
    with TestClient(main.app) as client:
        http_client = client.app.state.http_client
        assert http_client is not None, "HTTP client should be created during startup"
        assert not http_client.is_closed

    assert http_client.is_closed, "HTTP client should be closed during shutdown"


def test_health_endpoint_closes_sessions(monkeypatch):
    """Repeated /health checks should not leak SQLAlchemy sessions."""

    closed_sessions: List[object] = []

    class DummySession:
        def __init__(self) -> None:
            self.closed = False

        def execute(self, stmt):  # pragma: no cover - behaviour validated via flag
            return stmt

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.closed = True
            closed_sessions.append(self)

    def session_factory():
        return DummySession()

    monkeypatch.setattr(main, "SessionLocal", session_factory)
    monkeypatch.setattr(main, "redis_client", None)

    with TestClient(main.app) as client:
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200

    assert len(closed_sessions) == 3
    assert all(session.closed for session in closed_sessions)
