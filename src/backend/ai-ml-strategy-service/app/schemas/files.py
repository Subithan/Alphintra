from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class FileInfo(BaseModel):
    id: str
    name: str
    path: str
    content: Optional[str] = None
    language: str
    size: int
    modified: bool = False
    created_at: datetime
    updated_at: datetime
    is_directory: bool = False


class CreateFileRequest(BaseModel):
    name: str
    content: Optional[str] = ""
    language: Optional[str] = "plaintext"


class UpdateFileRequest(BaseModel):
    content: str
    language: Optional[str] = None


class ProjectSettings(BaseModel):
    aiEnabled: Optional[bool] = True
    suggestions: Optional[bool] = True
    autoComplete: Optional[bool] = True
    errorDetection: Optional[bool] = True
    testGeneration: Optional[bool] = True
    extra: Dict[str, Any] = {}


class ProjectInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    path: str
    files: List[FileInfo] = []
    created_at: datetime
    updated_at: datetime
    settings: ProjectSettings = Field(default_factory=ProjectSettings)


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    template: Optional[str] = "trading"


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[ProjectSettings] = None
