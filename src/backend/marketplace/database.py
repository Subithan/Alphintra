from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.exc import OperationalError # Added for race condition handling
from config import settings
import logging # Added for better logging in multi-worker

# Define a logger for better debugging in a multi-worker environment
logger = logging.getLogger(__name__)

# Create the engine object for the database
# NOTE: This relies on 'settings.DATABASE_URL' being defined in marketplace/config.py
engine = create_engine(settings.DATABASE_URL, echo=False) # Changed echo to False for cleaner logs

# Function to initialize the database tables, now with race condition handling
def create_db_and_tables():
    """
    Creates database tables, handling race conditions typical of multi-worker SQLite startup.
    This function uses the global 'engine' defined above.
    """
    try:
        # Use checkfirst=True to only issue CREATE TABLE for tables that do not exist.
        SQLModel.metadata.create_all(engine, checkfirst=True)
        logger.info("Database tables checked/created successfully.")
    except OperationalError as e:
        # This occurs due to the multi-worker race condition in SQLite.
        error_message = str(e)
        # Check for common SQLite "table already exists" error message
        if "table already exists" in error_message or "already exists" in error_message:
            logger.warning(
                "Race condition detected during table creation (likely SQLite multi-worker startup). "
                "Table already exists. Proceeding without error."
            )
        else:
            # Re-raise unexpected operational errors
            logger.error(f"Unexpected OperationalError during table creation: {error_message}")
            raise e
    except Exception as e:
        # Catch any other unexpected exceptions
        logger.critical(f"Fatal error during database creation: {e}")
        raise e

# Dependency to get a DB session
def get_session():
    """FastAPI dependency to provide a database session."""
    with Session(engine) as session:
        yield session
