#!/usr/bin/env python3
"""
Script to backfill user association for existing records in the no-code service.

This script assigns user_id to existing CompilationResult and ExecutionHistory records
by linking them to the respective workflow owners.
"""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from models import Base, CompilationResult, ExecutionHistory, NoCodeWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


def create_database_session():
    """Create database session."""
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def get_workflow_owner_user_id(db_session, workflow_id: int) -> int:
    """Get the user_id of a workflow owner."""
    workflow = db_session.query(NoCodeWorkflow).filter(
        NoCodeWorkflow.id == workflow_id
    ).first()

    if workflow:
        return workflow.user_id
    return None


def migrate_compilation_results(db_session):
    """Migrate CompilationResult records to add user_id."""
    logger.info("Starting migration for CompilationResult records...")

    # Find compilation results without user_id
    results_to_migrate = db_session.query(CompilationResult).filter(
        CompilationResult.user_id.is_(None)
    ).all()

    logger.info(f"Found {len(results_to_migrate)} CompilationResult records to migrate")

    migrated_count = 0
    failed_count = 0

    for result in results_to_migrate:
        try:
            # Get user_id from workflow
            user_id = get_workflow_owner_user_id(db_session, result.workflow_id)

            if user_id:
                result.user_id = user_id
                migrated_count += 1
            else:
                logger.warning(f"Could not find user for CompilationResult {result.id} - workflow {result.workflow_id}")
                failed_count += 1

        except Exception as e:
            logger.error(f"Error migrating CompilationResult {result.id}: {e}")
            failed_count += 1

    try:
        db_session.commit()
        logger.info(f"Successfully migrated {migrated_count} CompilationResult records")
        if failed_count > 0:
            logger.warning(f"Failed to migrate {failed_count} CompilationResult records")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to commit CompilationResult migration: {e}")
        raise


def migrate_execution_history(db_session):
    """Migrate ExecutionHistory records to add user_id."""
    logger.info("Starting migration for ExecutionHistory records...")

    # Find execution history records without user_id
    history_to_migrate = db_session.query(ExecutionHistory).filter(
        ExecutionHistory.user_id.is_(None)
    ).all()

    logger.info(f"Found {len(history_to_migrate)} ExecutionHistory records to migrate")

    migrated_count = 0
    failed_count = 0

    for history in history_to_migrate:
        try:
            # Get user_id from workflow
            user_id = get_workflow_owner_user_id(db_session, history.workflow_id)

            if user_id:
                history.user_id = user_id
                migrated_count += 1
            else:
                logger.warning(f"Could not find user for ExecutionHistory {history.id} - workflow {history.workflow_id}")
                failed_count += 1

        except Exception as e:
            logger.error(f"Error migrating ExecutionHistory {history.id}: {e}")
            failed_count += 1

    try:
        db_session.commit()
        logger.info(f"Successfully migrated {migrated_count} ExecutionHistory records")
        if failed_count > 0:
            logger.warning(f"Failed to migrate {failed_count} ExecutionHistory records")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to commit ExecutionHistory migration: {e}")
        raise


def verify_migration(db_session):
    """Verify that all records have user_id assigned."""
    logger.info("Verifying migration...")

    # Check CompilationResult
    compilation_results_without_user = db_session.query(CompilationResult).filter(
        CompilationResult.user_id.is_(None)
    ).count()

    # Check ExecutionHistory
    execution_history_without_user = db_session.query(ExecutionHistory).filter(
        ExecutionHistory.user_id.is_(None)
    ).count()

    logger.info(f"CompilationResult records without user_id: {compilation_results_without_user}")
    logger.info(f"ExecutionHistory records without user_id: {execution_history_without_user}")

    if compilation_results_without_user == 0 and execution_history_without_user == 0:
        logger.info("✅ Migration verification successful - all records have user association")
        return True
    else:
        logger.error("❌ Migration verification failed - some records still lack user association")
        return False


def create_backup_table(db_session, engine):
    """Create backup tables before migration."""
    logger.info("Creating backup tables...")

    try:
        # Backup CompilationResult
        engine.execute(text("""
            CREATE TABLE compilation_results_backup AS
            SELECT * FROM compilation_results
        """))

        # Backup ExecutionHistory
        engine.execute(text("""
            CREATE TABLE execution_history_backup AS
            SELECT * FROM execution_history
        """))

        logger.info("✅ Backup tables created successfully")

    except Exception as e:
        logger.warning(f"Could not create backup tables: {e}")


def main():
    """Main migration function."""
    logger.info("Starting user association migration for no-code service")

    try:
        # Create database session
        db_session, engine = create_database_session()

        # Create backup tables
        create_backup_table(db_session, engine)

        # Run migrations
        migrate_compilation_results(db_session)
        migrate_execution_history(db_session)

        # Verify migration
        success = verify_migration(db_session)

        if success:
            logger.info("🎉 Migration completed successfully!")
            return 0
        else:
            logger.error("❌ Migration completed with issues")
            return 1

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1
    finally:
        if 'db_session' in locals():
            db_session.close()


def dry_run(db_session):
    """Perform a dry run to see what would be migrated."""
    logger.info("Performing dry run...")

    # Count records that would be migrated
    compilation_count = db_session.query(CompilationResult).filter(
        CompilationResult.user_id.is_(None)
    ).count()

    execution_count = db_session.query(ExecutionHistory).filter(
        ExecutionHistory.user_id.is_(None)
    ).count()

    logger.info(f"Dry run: Would migrate {compilation_count} CompilationResult records")
    logger.info(f"Dry run: Would migrate {execution_count} ExecutionHistory records")
    logger.info("Use --execute to perform the actual migration")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate user association for existing records")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    parser.add_argument("--execute", action="store_true", help="Execute the migration")

    args = parser.parse_args()

    if not args.execute and not args.dry_run:
        print("Please specify either --dry-run or --execute")
        sys.exit(1)

    if args.dry_run:
        db_session, _ = create_database_session()
        try:
            dry_run(db_session)
            sys.exit(0)
        finally:
            db_session.close()

    if args.execute:
        sys.exit(main())