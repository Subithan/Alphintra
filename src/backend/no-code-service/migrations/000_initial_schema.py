"""
Migration: Initial schema creation
Date: 2025-09-22
Description: Create all SQLAlchemy models' tables and required extensions in the connected PostgreSQL (Cloud SQL).
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra_user:alphintra_password@localhost:5432/alphintra_db")


def upgrade():
    """Apply initial schema migration"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("Starting migration: Initial schema creation...")

        # Ensure required extensions for UUID generation exist
        try:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            print("   ✅ Ensured extensions pgcrypto and uuid-ossp")
        except Exception as e:
            print(f"   ⚠️ Warning ensuring extensions: {e}")

    # Create all tables defined in SQLAlchemy models
    print("Creating database tables from SQLAlchemy models...")
    Base.metadata.create_all(bind=engine)
    print("✅ Initial schema created successfully!")


def downgrade():
    """Rollback initial schema migration (not implemented to avoid data loss)."""
    print("⚠️ Downgrade for initial schema is not supported.")


if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()