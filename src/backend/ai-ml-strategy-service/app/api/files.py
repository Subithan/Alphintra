from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.db import get_db
from ..core.security import get_current_user_id
from ..services import files_service as svc
from ..schemas.files import (
    ProjectInfo, CreateProjectRequest, UpdateProjectRequest,
    FileInfo, CreateFileRequest, UpdateFileRequest,
)

router = APIRouter(prefix="/api/files", tags=["Files"])


def _to_file_info(model) -> FileInfo:
    return FileInfo(
        id=model.id,
        name=model.name,
        path=model.path,
        content=getattr(model, "content", None),
        language=model.language,
        size=model.size or 0,
        modified=False,
        created_at=model.created_at,
        updated_at=model.updated_at,
        is_directory=model.is_directory or False,
    )


def _to_project_info(model, files=None) -> ProjectInfo:
    return ProjectInfo(
        id=model.id,
        name=model.name,
        description=model.description,
        path=model.path,
        files=[_to_file_info(f) for f in (files or getattr(model, "files", []))],
        created_at=model.created_at,
        updated_at=model.updated_at,
        settings=model.settings or {},
    )


@router.get("/projects", response_model=List[ProjectInfo])
def list_projects(db: Session = Depends(get_db), user_id: Optional[str] = Depends(get_current_user_id)):
    projects = svc.list_projects(db, user_id)
    # For list view, avoid content payloads
    return [_to_project_info(p, files=[]) for p in projects]


@router.post("/projects", response_model=ProjectInfo)
def create_project(req: CreateProjectRequest, db: Session = Depends(get_db), user_id: Optional[str] = Depends(get_current_user_id)):
    project = svc.create_project(db, req.name, req.description, req.template, user_id)
    # Return with files (without content)
    files = svc.list_files(db, project.id)
    # Strip content for list view
    for f in files:
        f.content = None
    return _to_project_info(project, files=files)


@router.get("/projects/{project_id}", response_model=ProjectInfo)
def get_project(project_id: str, db: Session = Depends(get_db), user_id: Optional[str] = Depends(get_current_user_id)):
    project = svc.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    files = svc.list_files(db, project_id)
    # For this endpoint we return files without content by default
    for f in files:
        f.content = None
    return _to_project_info(project, files=files)


@router.patch("/projects/{project_id}", response_model=ProjectInfo)
def update_project(project_id: str, req: UpdateProjectRequest, db: Session = Depends(get_db), user_id: Optional[str] = Depends(get_current_user_id)):
    project = svc.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    updated = svc.update_project(db, project, req.model_dump(exclude_unset=True))
    files = svc.list_files(db, project_id)
    for f in files:
        f.content = None
    return _to_project_info(updated, files=files)


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db), user_id: Optional[str] = Depends(get_current_user_id)):
    project = svc.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    svc.delete_project(db, project)
    return {"message": "Project deleted"}


@router.get("/projects/{project_id}/files", response_model=List[FileInfo])
def list_project_files(
    project_id: str,
    include_content: Optional[bool] = Query(default=False),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    project = svc.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    files = svc.list_files(db, project_id)
    if not include_content:
        for f in files:
            f.content = None
    return [_to_file_info(f) for f in files]


@router.post("/projects/{project_id}/files", response_model=FileInfo)
def create_file(project_id: str, req: CreateFileRequest, db: Session = Depends(get_db), user_id: Optional[str] = Depends(get_current_user_id)):
    project = svc.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    file = svc.create_file(db, project_id, req.name, req.content or "", req.language, user_id)
    return _to_file_info(file)


@router.get("/projects/{project_id}/files/{name}", response_model=FileInfo)
def get_file(project_id: str, name: str, db: Session = Depends(get_db), user_id: Optional[str] = Depends(get_current_user_id)):
    project = svc.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    file = svc.find_file(db, project_id, name)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return _to_file_info(file)


@router.put("/projects/{project_id}/files/{name}", response_model=FileInfo)
def update_file(project_id: str, name: str, req: UpdateFileRequest, db: Session = Depends(get_db), user_id: Optional[str] = Depends(get_current_user_id)):
    project = svc.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    file = svc.find_file(db, project_id, name)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    updated = svc.update_file(db, file, req.content, req.language)
    return _to_file_info(updated)


@router.delete("/projects/{project_id}/files/{name}")
def delete_file(project_id: str, name: str, db: Session = Depends(get_db), user_id: Optional[str] = Depends(get_current_user_id)):
    project = svc.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    file = svc.find_file(db, project_id, name)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    svc.delete_file(db, file)
    return {"message": "File deleted"}
