#!/usr/bin/env python3
"""
Simple migration runner for no-code-service.
- Discovers migration files in this directory (NNN_name.py)
- Applies them in lexical order if not yet applied
- Records applied migrations in a migration_versions table
- Designed to run safely against Cloud SQL (PostgreSQL) with idempotent migrations
"""

import os
import re
import sys
import importlib.util
from typing import List
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Ensure project root is in path for model imports from migrations
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://alphintra_user:alphintra_password@localhost:5432/alphintra_db",
)

MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATION_PATTERN = re.compile(r"^(\d{3}_.+?)\.py$")


def _load_module_from_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return module


def _ensure_versions_table(engine: Engine):
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS migration_versions (
                    filename TEXT PRIMARY KEY,
                    applied_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
        )


def _get_applied(engine: Engine) -> set:
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT filename FROM migration_versions")).fetchall()
        return {r[0] for r in rows}


def _record_applied(engine: Engine, filename: str):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO migration_versions(filename, applied_at) VALUES (:f, :t) ON CONFLICT (filename) DO NOTHING"),
            {"f": filename, "t": datetime.utcnow()},
        )


def _is_alembic_based(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(4096)
            return ("from alembic import op" in head) or ("alembic" in head and "op." in head)
    except Exception:
        return False


def discover_migrations() -> List[str]:
    files = []
    for fname in os.listdir(MIGRATIONS_DIR):
        if fname in {"__init__.py", os.path.basename(__file__)}:
            continue
        if MIGRATION_PATTERN.match(fname):
            path = os.path.join(MIGRATIONS_DIR, fname)
            if _is_alembic_based(path):
                # Skip Alembic-style migrations; runner applies only safe, idempotent scripts
                continue
            files.append(fname)
    return sorted(files)


def apply_all_migrations():
    print("[migrate] Connecting to database...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    # Acquire advisory lock to avoid concurrent runners
    with engine.begin() as conn:
        print("[migrate] Acquiring advisory lock...")
        conn.execute(text("SELECT pg_advisory_lock(84239912)"))

    try:
        _ensure_versions_table(engine)
        applied = _get_applied(engine)
        to_apply = [f for f in discover_migrations() if f not in applied]

        if not to_apply:
            print("[migrate] No pending migrations.")
            return

        print(f"[migrate] Pending migrations: {to_apply}")
        for fname in to_apply:
            path = os.path.join(MIGRATIONS_DIR, fname)
            mod_name = f"migrations.{fname[:-3]}"
            print(f"[migrate] Applying {fname}...")
            module = _load_module_from_path(mod_name, path)
            if not hasattr(module, "upgrade"):
                raise RuntimeError(f"Migration {fname} has no upgrade() function")
            module.upgrade()
            _record_applied(engine, fname)
            print(f"[migrate] ✅ Applied {fname}")
        print("[migrate] ✅ All migrations applied")
    finally:
        with engine.begin() as conn:
            print("[migrate] Releasing advisory lock...")
            conn.execute(text("SELECT pg_advisory_unlock(84239912)"))


if __name__ == "__main__":
    apply_all_migrations()
