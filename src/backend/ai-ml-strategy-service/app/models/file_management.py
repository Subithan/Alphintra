"""
File management models for storing IDE files and projects in database.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel, UserMixin, MetadataMixin


class Project(BaseModel, UserMixin, MetadataMixin):
    """Project model for storing IDE projects."""
    
    __tablename__ = "projects"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    template_type = Column(String(100), default="custom")
    
    # Project settings stored as JSON
    settings = Column(JSON, default=dict)
    
    # Relationships
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("FileSession", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_projects_user_id", "user_id"),
        Index("idx_projects_name", "name"),
        Index("idx_projects_template_type", "template_type"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "file_count": len(self.files) if self.files else 0
        })
        return base_dict


class ProjectFile(BaseModel, MetadataMixin):
    """Project file model for storing individual files within projects."""
    
    __tablename__ = "project_files"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative path within project
    file_name = Column(String(255), nullable=False)
    content = Column(Text, default="")
    file_type = Column(String(100), default="text")  # text, binary, image, etc.
    size_bytes = Column(Integer, default=0)
    is_directory = Column(Boolean, default=False)
    
    # File-specific settings
    language = Column(String(50), default="python")  # For syntax highlighting
    encoding = Column(String(20), default="utf-8")
    
    # Version tracking
    version = Column(Integer, default=1)
    checksum = Column(String(64), nullable=True)  # SHA-256 hash
    
    # Relationships
    project = relationship("Project", back_populates="files")
    
    # Indexes
    __table_args__ = (
        Index("idx_project_files_project_id", "project_id"),
        Index("idx_project_files_path", "project_id", "file_path"),
        Index("idx_project_files_name", "file_name"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert file to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "project_name": self.project.name if self.project else None
        })
        return base_dict


class ProjectTemplate(BaseModel, MetadataMixin):
    """Project template model for predefined project structures."""
    
    __tablename__ = "project_templates"
    
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), default="general")
    
    # Template configuration
    template_config = Column(JSON, default=dict)  # File structure, dependencies, etc.
    default_files = Column(JSON, default=list)    # List of default files to create
    
    # Template metadata
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        Index("idx_project_templates_name", "name"),
        Index("idx_project_templates_category", "category"),
        Index("idx_project_templates_active", "is_active"),
    )


class FileSession(BaseModel):
    """File session model for tracking file editing sessions."""
    
    __tablename__ = "file_sessions"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("project_files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Session data
    session_token = Column(String(64), nullable=False, unique=True)
    cursor_position = Column(JSON, default=dict)  # Line, column
    selected_text = Column(JSON, default=dict)    # Start, end positions
    
    # Session metadata
    is_active = Column(Boolean, default=True)
    last_activity = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    project = relationship("Project", back_populates="sessions")
    file = relationship("ProjectFile")
    
    # Indexes
    __table_args__ = (
        Index("idx_file_sessions_project_id", "project_id"),
        Index("idx_file_sessions_file_id", "file_id"),
        Index("idx_file_sessions_user_id", "user_id"),
        Index("idx_file_sessions_token", "session_token"),
        Index("idx_file_sessions_active", "is_active"),
    )


class FileVersion(BaseModel):
    """File version model for tracking file history."""
    
    __tablename__ = "file_versions"
    
    file_id = Column(UUID(as_uuid=True), ForeignKey("project_files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Version data
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)  # SHA-256
    
    # Change metadata
    change_summary = Column(String(500), default="")
    lines_added = Column(Integer, default=0)
    lines_removed = Column(Integer, default=0)
    
    # Relationships
    file = relationship("ProjectFile")
    
    # Indexes
    __table_args__ = (
        Index("idx_file_versions_file_id", "file_id"),
        Index("idx_file_versions_user_id", "user_id"),
        Index("idx_file_versions_number", "file_id", "version_number"),
    )