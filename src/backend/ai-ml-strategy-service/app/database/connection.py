"""Database connection utilities."""

from app.core.database import get_db

# Alias for backward compatibility
get_db_session = get_db