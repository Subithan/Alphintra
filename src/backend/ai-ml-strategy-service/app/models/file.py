from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..core.db import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ProjectFile(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    owner_user_id = Column(String, nullable=True, index=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)  # relative path within project
    language = Column(String, nullable=False, default="plaintext")
    size = Column(Integer, default=0)
    is_directory = Column(Boolean, default=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", backref="files")
