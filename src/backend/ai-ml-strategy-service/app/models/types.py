"""Custom SQLAlchemy types for cross-database compatibility."""

import json
from typing import Any, List, Optional

from sqlalchemy import TypeDecorator, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import String, Float, Integer


class JSONArray(TypeDecorator):
    """A type that stores arrays as JSON in SQLite and as ARRAY in PostgreSQL."""
    
    impl = Text
    cache_ok = True
    
    def __init__(self, item_type=String, **kwargs):
        self.item_type = item_type
        super().__init__(**kwargs)
    
    def load_dialect_impl(self, dialect):
        """Load the appropriate type based on the database dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(Text())
    
    def process_bind_param(self, value: Optional[List[Any]], dialect) -> Optional[str]:
        """Process value before storing in database."""
        if value is None:
            return None
        
        if dialect.name == 'postgresql':
            return value
        else:
            # For SQLite and other databases, store as JSON
            return json.dumps(value)
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[List[Any]]:
        """Process value after retrieving from database."""
        if value is None:
            return []
        
        if dialect.name == 'postgresql':
            return value if value is not None else []
        else:
            # For SQLite and other databases, parse JSON
            try:
                return json.loads(value) if value else []
            except (json.JSONDecodeError, TypeError):
                return []


class StringArray(JSONArray):
    """Array of strings that works across databases."""
    
    def __init__(self, **kwargs):
        super().__init__(item_type=String, **kwargs)


class IntegerArray(JSONArray):
    """Array of integers that works across databases."""
    
    def __init__(self, **kwargs):
        super().__init__(item_type=Integer, **kwargs)


class FloatArray(JSONArray):
    """Array of floats that works across databases."""
    
    def __init__(self, **kwargs):
        super().__init__(item_type=Float, **kwargs)