"""
Base model classes and mixins.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

from app.core.database import Base


class UUIDMixin:
    """Mixin for UUID primary key."""
    
    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid4)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class UserMixin:
    """Mixin for user_id foreign key."""
    
    @declared_attr
    def user_id(cls):
        return Column(UUID(as_uuid=True), nullable=False, index=True)


class MetadataMixin:
    """Mixin for JSON metadata storage."""
    
    metadata_ = Column("metadata", JSON, default=dict)


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Base model class with UUID primary key and timestamps.
    """
    __abstract__ = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)