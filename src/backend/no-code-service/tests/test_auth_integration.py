import importlib.util
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, String
from sqlalchemy.dialects import postgresql as pg_dialects
from sqlalchemy.types import TypeDecorator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = PROJECT_ROOT / "main.py"


class _DummyAuthResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture
def app_client(monkeypatch, tmp_path):
    module_name = f"nocode_main_test_{uuid.uuid4().hex}"

    database_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}?check_same_thread=false")
    monkeypatch.setenv("DEV_MODE", "false")
    monkeypatch.setenv("AUTH_SERVICE_URL", "http://auth-service")

    class SQLiteUUID(TypeDecorator):
        impl = String
        cache_ok = True

        def __init__(self, *args, **kwargs):
            kwargs.pop("as_uuid", None)
            super().__init__()

        def load_dialect_impl(self, dialect):
            return dialect.type_descriptor(String(36))

        def process_bind_param(self, value, dialect):
            if value is None:
                return None
            return str(value)

        def process_result_value(self, value, dialect):
            return value

    class SQLiteARRAY(TypeDecorator):
        impl = JSON
        cache_ok = True

        def __init__(self, item_type=None, *args, **kwargs):
            self.item_type = item_type
            # Remove PostgreSQL-specific arguments
            kwargs.pop("dimension", None)
            super().__init__()

        def process_bind_param(self, value, dialect):
            return value

        def process_result_value(self, value, dialect):
            return value

    import sqlalchemy as sa
    from sqlalchemy.sql import sqltypes

    monkeypatch.setattr(pg_dialects, "UUID", SQLiteUUID)
    monkeypatch.setattr(pg_dialects, "ARRAY", SQLiteARRAY)
    if hasattr(pg_dialects, "base"):
        monkeypatch.setattr(pg_dialects.base, "UUID", SQLiteUUID, raising=False)
        monkeypatch.setattr(pg_dialects.base, "ARRAY", SQLiteARRAY, raising=False)
    if hasattr(pg_dialects, "array"):
        monkeypatch.setattr(pg_dialects.array, "ARRAY", SQLiteARRAY, raising=False)

    monkeypatch.setattr(sa, "ARRAY", SQLiteARRAY)
    monkeypatch.setattr(sqltypes, "ARRAY", SQLiteARRAY, raising=False)

    spec = importlib.util.spec_from_file_location(module_name, MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None

    path_added = str(PROJECT_ROOT)
    sys.path.insert(0, path_added)
    try:
        spec.loader.exec_module(module)
    finally:
        if sys.path and sys.path[0] == path_added:
            sys.path.pop(0)
        else:
            try:
                sys.path.remove(path_added)
            except ValueError:
                pass

    # Avoid heavy migration logic during tests
    monkeypatch.setattr(module, "apply_all_migrations", lambda: None)

    module.Base.metadata.create_all(bind=module.engine)

    payload = {
        "email": "token.user@example.com",
        "first_name": "Token",
        "last_name": "User",
        "is_verified": True,
    }

    async def fake_get(url, headers):
        fake_get.called_with = {"url": url, "headers": headers}
        return _DummyAuthResponse(payload)

    fake_get.called_with = None
    monkeypatch.setattr(module.http_client, "get", fake_get)

    with TestClient(module.app) as client:
        yield client, module, fake_get

    module.Base.metadata.drop_all(bind=module.engine)
    del sys.modules[module_name]


def test_rest_endpoint_uses_authenticated_user(app_client):
    client, module, fake_get = app_client

    response = client.post(
        "/api/workflows/create-sample",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert fake_get.called_with is not None

    session = module.SessionLocal()
    try:
        user = session.query(module.User).filter_by(email="token.user@example.com").one()
        assert user.id is not None
        workflow = session.query(module.NoCodeWorkflow).filter_by(user_id=user.id).one()
        assert workflow is not None
    finally:
        session.close()


def test_graphql_context_reuses_authenticated_user(app_client):
    client, module, fake_get = app_client

    # Seed a workflow via REST to reuse in GraphQL query
    rest_response = client.post(
        "/api/workflows/create-sample",
        headers={"Authorization": "Bearer another-token"},
    )
    assert rest_response.status_code == 200
    workflow_id = rest_response.json()["workflow_id"]

    query = {
        "query": "query ($id: String!) { workflow(workflowId: $id) { name } }",
        "variables": {"id": workflow_id},
    }
    response = client.post(
        "/graphql",
        json=query,
        headers={"Authorization": "Bearer another-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body
    assert body["data"]["workflow"] is not None
    assert fake_get.called_with is not None
