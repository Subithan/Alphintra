"""
Migration: Add execution mode fields
Date: 2025-08-08
Description: Add execution_metadata, aiml_training_job_id fields to NoCodeWorkflow
             and create ExecutionHistory table for tracking dual-mode execution
"""

import os
import sys
from sqlalchemy import create_engine, text, Column, String, JSON, Integer, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra_user:alphintra_password@localhost:5432/alphintra_db")


def upgrade():
    """Apply migration"""
    # Use autocommit so a handled error doesn't poison the whole transaction
    engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    
    with engine.connect() as conn:
        print("Starting migration: Add execution mode fields...")
        
        # Add new columns to nocode_workflows table
        print("1. Adding execution_metadata column to nocode_workflows...")
        try:
            conn.execute(text("""
                ALTER TABLE nocode_workflows 
                ADD COLUMN IF NOT EXISTS execution_metadata JSON DEFAULT '{}'::json
            """))
            print("   ✅ execution_metadata column ensured")
        except Exception as e:
            if "already exists" in str(e):
                print("   ⚠️ execution_metadata column already exists, skipping")
            else:
                raise
        
        print("2. Adding aiml_training_job_id column to nocode_workflows...")
        try:
            conn.execute(text("""
                ALTER TABLE nocode_workflows 
                ADD COLUMN IF NOT EXISTS aiml_training_job_id VARCHAR
            """))
            print("   ✅ aiml_training_job_id column ensured")
        except Exception as e:
            if "already exists" in str(e):
                print("   ⚠️ aiml_training_job_id column already exists, skipping")
            else:
                raise
        
        # Create ExecutionHistory table
        print("3. Creating execution_history table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    id SERIAL PRIMARY KEY,
                    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
                    workflow_id INTEGER NOT NULL REFERENCES nocode_workflows(id),
                    execution_mode VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    execution_config JSON DEFAULT '{}'::json,
                    results JSON DEFAULT '{}'::json,
                    error_logs JSON DEFAULT '[]'::json,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                )
            """))
            print("   ✅ execution_history table created")
        except Exception as e:
            if "already exists" in str(e):
                print("   ⚠️ execution_history table already exists, skipping")
            else:
                raise
        
        # Create indexes for performance
        print("4. Creating indexes...")
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_execution_history_workflow_id ON execution_history(workflow_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_execution_history_uuid ON execution_history(uuid)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_execution_history_status ON execution_history(status)"))
            print("   ✅ Indexes ensured")
        except Exception as e:
            if "already exists" in str(e):
                print("   ⚠️ Some indexes already exist, continuing")
            else:
                print(f"   ⚠️ Warning creating indexes: {e}")
        
        # Commit transaction
        conn.commit()
        print("✅ Migration completed successfully!")


def downgrade():
    """Rollback migration"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Rolling back migration: Add execution mode fields...")
        
        # Drop ExecutionHistory table
        print("1. Dropping execution_history table...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS execution_history"))
            print("   ✅ execution_history table dropped")
        except Exception as e:
            print(f"   ⚠️ Warning dropping table: {e}")
        
        # Remove columns from nocode_workflows
        print("2. Removing aiml_training_job_id column...")
        try:
            conn.execute(text("ALTER TABLE nocode_workflows DROP COLUMN IF EXISTS aiml_training_job_id"))
            print("   ✅ aiml_training_job_id column removed")
        except Exception as e:
            print(f"   ⚠️ Warning removing column: {e}")
        
        print("3. Removing execution_metadata column...")
        try:
            conn.execute(text("ALTER TABLE nocode_workflows DROP COLUMN IF EXISTS execution_metadata"))
            print("   ✅ execution_metadata column removed")
        except Exception as e:
            print(f"   ⚠️ Warning removing column: {e}")
        
        # Commit transaction
        conn.commit()
        print("✅ Rollback completed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
