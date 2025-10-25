"""Authentication and authorisation tests for workflow routes."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.sqltypes import ARRAY
from sqlalchemy.types import TEXT, TypeDecorator
from pytest import FixtureRequest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = PROJECT_ROOT / "src" / "backend" / "no-code-service"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


class SqliteArray(TypeDecorator):
    """SQLite compatible replacement for SQLAlchemy ARRAY type."""

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):  # type: ignore[override]
        if value is None:
            return []
        return json.loads(value)


def _prepare_sqlite_models():
    import models

    replacements = {}
    for table in models.Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, ARRAY):
                replacements[column] = column.type
                column.type = SqliteArray()
    return models, replacements


@pytest.fixture()
def test_app(monkeypatch, request: FixtureRequest) -> Dict[str, Any]:
    """Return FastAPI test client with SQLite-backed dependencies."""

    dev_mode = bool(getattr(request, "param", False))

    monkeypatch.setenv("DEV_MODE", "true" if dev_mode else "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

    for module_name in [
        "app",
        "app.api",
        "app.api.routes",
        "app.api.routes.workflows",
        "app.api.routes.library",
        "app.core.config",
        "app.core.db",
        "app.core.dependencies",
    ]:
        sys.modules.pop(module_name, None)

    from app.core.config import get_settings

    get_settings.cache_clear()

    models, replacements = _prepare_sqlite_models()

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    models.Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import sessionmaker

    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    workflows_module = importlib.import_module("app.api.routes.workflows")
    importlib.reload(workflows_module)

    app = FastAPI()
    app.include_router(workflows_module.router)

    from app.core.db import get_db
    from app.core.dependencies import get_settings_dependency

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings_dependency] = lambda: get_settings()

    client = TestClient(app)

    context = {
        "client": client,
        "session_factory": TestingSessionLocal,
        "models": models,
    }

    yield context

    client.close()
    app.dependency_overrides.clear()
    models.Base.metadata.drop_all(bind=engine)
    get_settings.cache_clear()
    for column, original in replacements.items():
        column.type = original


@pytest.mark.parametrize("test_app", [True], indirect=True)
def test_create_and_list_workflows_use_authenticated_user(test_app):
    """Ensure workflow creation and listing honour the caller even in dev mode."""

    client: TestClient = test_app["client"]
    session_factory = test_app["session_factory"]
    models = test_app["models"]

    with session_factory() as db:
        user = models.User(
            id=777,
            email="owner@example.com",
            password_hash="hash-owner",
            first_name="Workflow",
            last_name="Owner",
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
        user_email = user.email

    token = jwt.encode(
        {"sub": str(user_id), "email": user_email},
        "unit-test-secret",
        algorithm="HS256",
    )

    create_payload = {
        "name": "Dev Mode Workflow",
        "description": "Created while DEV_MODE is true",
        "category": "test",
        "tags": ["dev", "mode"],
        "workflow_data": {"nodes": [], "edges": []},
        "execution_mode": "backtest",
    }

    create_response = client.post(
        "/api/workflows",
        headers={"Authorization": f"Bearer {token}"},
        json=create_payload,
    )
    assert create_response.status_code == 200
    created_workflow = create_response.json()
    assert created_workflow["name"] == create_payload["name"]

    with session_factory() as db:
        other_user = models.User(
            id=888,
            email="other@example.com",
            password_hash="hash-other",
            first_name="Other",
            last_name="User",
            is_verified=True,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        alien_workflow = models.NoCodeWorkflow(
            name="Alien Workflow",
            description="Should never be visible",
            category="test",
            tags=["alien"],
            user_id=other_user.id,
            workflow_data={"nodes": [], "edges": []},
        )
        db.add(alien_workflow)
        db.commit()

    list_response = client.get(
        "/api/workflows",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    workflows = list_response.json()
    assert len(workflows) == 1
    assert workflows[0]["id"] == created_workflow["id"]

    detail_response = client.get(
        f"/api/workflows/{created_workflow['uuid']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_response.status_code == 200, detail_response.text
    detail_payload = detail_response.json()
    assert detail_payload["id"] == created_workflow["id"]


@pytest.fixture()
def seeded_app(test_app):
    """Seed database with users and workflows and return helper context."""

    client: TestClient = test_app["client"]
    session_factory = test_app["session_factory"]
    models = test_app["models"]

    with session_factory() as db:
        user_one = models.User(
            email="one@example.com",
            password_hash="hash1",
            first_name="User",
            last_name="One",
            is_verified=True,
        )
        user_two = models.User(
            email="two@example.com",
            password_hash="hash2",
            first_name="User",
            last_name="Two",
            is_verified=True,
        )
        db.add_all([user_one, user_two])
        db.commit()
        db.refresh(user_one)
        db.refresh(user_two)

        workflow_one = models.NoCodeWorkflow(
            name="First Workflow",
            description="User one workflow",
            category="alpha",
            tags=["personal"],
            user_id=user_one.id,
            workflow_data={"nodes": [], "edges": []},
        )
        workflow_two = models.NoCodeWorkflow(
            name="Second Workflow",
            description="Another for user one",
            category="beta",
            tags=["personal"],
            user_id=user_one.id,
            workflow_data={"nodes": [], "edges": []},
        )
        other_workflow = models.NoCodeWorkflow(
            name="Other Workflow",
            description="Belongs to user two",
            category="alpha",
            tags=["shared"],
            user_id=user_two.id,
            workflow_data={"nodes": [], "edges": []},
        )
        db.add_all([workflow_one, workflow_two, other_workflow])
        db.commit()

        user_one_id = user_one.id
        user_one_email = user_one.email

    token_user_one = jwt.encode(
        {"sub": str(user_one_id), "email": user_one_email},
        "unit-test-secret",
        algorithm="HS256",
    )
    token_unknown = jwt.encode(
        {"sub": "9999", "email": "ghost@example.com"},
        "unit-test-secret",
        algorithm="HS256",
    )

    return {
        "client": client,
        "token_user_one": token_user_one,
        "token_unknown": token_unknown,
        "user_workflow_names": {"First Workflow", "Second Workflow"},
    }


def test_missing_token_is_rejected(test_app):
    response = test_app["client"].get("/api/workflows")
    assert response.status_code == 401


def test_mismatched_token_is_rejected(seeded_app):
    response = seeded_app["client"].get(
        "/api/workflows",
        headers={"Authorization": f"Bearer {seeded_app['token_unknown']}"},
    )
    assert response.status_code == 401


def test_valid_token_returns_only_user_workflows(seeded_app):
    response = seeded_app["client"].get(
        "/api/workflows",
        headers={"Authorization": f"Bearer {seeded_app['token_user_one']}"},
    )
    assert response.status_code == 200
    payload = response.json()
    names = {workflow["name"] for workflow in payload}
    assert names == seeded_app["user_workflow_names"]
