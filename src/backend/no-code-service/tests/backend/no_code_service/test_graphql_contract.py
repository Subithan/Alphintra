from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.sqltypes import ARRAY
from sqlalchemy.types import TEXT, TypeDecorator, String

from tests.backend.no_code_service import SERVICE_ROOT

MODULE_DIR = SERVICE_ROOT


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


class SqliteUUID(TypeDecorator):
    """SQLite-friendly UUID that stores values as CHAR(36)."""

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):  # type: ignore[override]
        return value


def _load_graphql_schema():
    sys.path.insert(0, str(MODULE_DIR))
    module_path = MODULE_DIR / "graphql_schema.py"
    spec = importlib.util.spec_from_file_location("graphql_schema", module_path)
    if not spec or not spec.loader:
        raise RuntimeError("Unable to load graphql_schema module")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def _load_graphql_resolvers():
    sys.path.insert(0, str(MODULE_DIR))
    module_path = MODULE_DIR / "graphql_resolvers.py"
    spec = importlib.util.spec_from_file_location("graphql_resolvers", module_path)
    if not spec or not spec.loader:
        raise RuntimeError("Unable to load graphql_resolvers module")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def _prepare_sqlite_models(models_module):
    replacements = {}
    for table in models_module.Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, ARRAY):
                replacements[column] = column.type
                column.type = SqliteArray()
            elif isinstance(column.type, PGUUID):
                replacements[column] = column.type
                column.type = SqliteUUID()
    return replacements


def test_workflow_conversion_includes_compiler_version():
    graphql_schema = _load_graphql_schema()
    now = datetime.utcnow()
    dummy_workflow = SimpleNamespace(
        id=1,
        uuid="1234",
        name="Snapshot Workflow",
        description=None,
        category="swing",
        tags=[],
        workflow_data={"nodes": [], "edges": []},
        generated_code=None,
        generated_code_language="python",
        generated_requirements=[],
        compilation_status="success",
        compilation_errors=[],
        validation_status="pending",
        validation_errors=[],
        deployment_status="draft",
        execution_mode="backtest",
        version=1,
        parent_workflow_id=None,
        is_template=False,
        is_public=False,
        total_executions=0,
        successful_executions=0,
        avg_performance_score=None,
        last_execution_at=None,
        created_at=now,
        updated_at=now,
        published_at=None,
        compiler_version="Enhanced v2.0",
    )

    gql_workflow = graphql_schema.convert_db_workflow_to_graphql(dummy_workflow)
    assert gql_workflow.compiler_version == "Enhanced v2.0"


def test_workflows_query_orders_before_limiting():
    """Ensure the GraphQL workflows resolver does not raise when limit/offset are used."""
    graphql_schema = _load_graphql_schema()
    graphql_resolvers = _load_graphql_resolvers()

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    sys.path.insert(0, str(MODULE_DIR))
    import models

    replacements = _prepare_sqlite_models(models)
    models.Base.metadata.create_all(bind=engine)

    try:
        with SessionLocal() as session:
            user = models.User(
                email="graphql@example.com",
                password_hash="secret",
                first_name="Graph",
                last_name="Tester",
                is_verified=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            for idx in range(3):
                workflow = models.NoCodeWorkflow(
                    name=f"Workflow {idx}",
                    description="",
                    category="alpha",
                    tags=[],
                    user_id=user.id,
                    workflow_data={"nodes": [], "edges": []},
                )
                session.add(workflow)
            session.commit()

            info = SimpleNamespace(
                context={"db_session": session, "current_user": user},
            )
            filters = graphql_schema.WorkflowFilters(limit=1)

            connection = graphql_resolvers.Query().workflows(info, filters)

            assert connection.total == 3
            assert len(connection.workflows) == 1
            assert connection.workflows[0].compiler_version == "Enhanced v2.0"
    finally:
        models.Base.metadata.drop_all(bind=engine)
        for column, original in replacements.items():
            column.type = original
