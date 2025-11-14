from __future__ import annotations

import importlib.util
import os
import sys

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from tests.backend.no_code_service import SERVICE_ROOT

MODULE_DIR = SERVICE_ROOT
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
sys.path.insert(0, str(MODULE_DIR))
spec = importlib.util.spec_from_file_location(
    "app.core.dependencies", MODULE_DIR / "app" / "core" / "dependencies.py"
)
assert spec and spec.loader
deps = importlib.util.module_from_spec(spec)
sys.modules.setdefault(spec.name, deps)
spec.loader.exec_module(deps)


class DummySettings:
    dev_mode = False


def _make_request(token: str | None) -> Request:
    scope = {
        "type": "http",
        "headers": [],
    }
    if token:
        scope["headers"] = [(b"authorization", f"Bearer {token}".encode())]
    return Request(scope)


@pytest.mark.asyncio
async def test_get_current_user_returns_token_user(monkeypatch):
    monkeypatch.setattr(deps, "extract_user_id_from_token", lambda token: "token-user")
    monkeypatch.setattr(
        deps,
        "extract_user_claims",
        lambda token: {"email": "user@example.com"},
    )
    request = _make_request("token")
    user = await deps.get_current_user(request=request, settings=DummySettings())
    assert user.id == "token-user"
    assert user.email == "user@example.com"
    assert user.claims == {"email": "user@example.com"}


@pytest.mark.asyncio
async def test_get_current_user_requires_token(monkeypatch):
    request = _make_request(None)

    class NoDevSettings(DummySettings):
        dev_mode = False

    with pytest.raises(HTTPException):
        await deps.get_current_user(request=request, settings=NoDevSettings())
