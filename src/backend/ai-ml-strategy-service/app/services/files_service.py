from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.project import Project
from ..models.file import ProjectFile
from ..utils.paths import sanitize_relative_path, detect_language
from datetime import datetime


def list_projects(db: Session, user_id: str | None) -> List[Project]:
    q = db.query(Project)
    if user_id:
        q = q.filter(Project.user_id == user_id)
    else:
        q = q.filter(Project.user_id.is_(None))
    return q.order_by(Project.created_at.desc()).all()


def create_project(db: Session, name: str, description: str | None, template: str | None, user_id: str | None) -> Project:
    # Create unique path slug based on name
    import re, uuid
    slug = re.sub(r"[^a-z0-9-]", "-", name.lower().replace(" ", "-")).strip("-")
    if not slug:
        slug = str(uuid.uuid4())[:8]
    base_slug = slug
    idx = 1
    while db.query(Project).filter(Project.path == slug).first() is not None:
        idx += 1
        slug = f"{base_slug}-{idx}"

    project = Project(
        name=name,
        description=description,
        path=slug,
        user_id=user_id,
        settings={
            "aiEnabled": True,
            "suggestions": True,
            "autoComplete": True,
            "errorDetection": True,
            "testGeneration": True,
        },
    )
    db.add(project)
    db.flush()

    # Seed template files
    from .templates import project_template
    for filename, content in project_template(template or "trading").items():
        lang = detect_language(filename)
        f = ProjectFile(
            project_id=project.id,
            owner_user_id=user_id,
            name=filename,
            path=sanitize_relative_path(filename),
            language=lang,
            size=len(content or ""),
            is_directory=False,
            content=content or "",
        )
        db.add(f)

    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: str, user_id: str | None = None) -> Optional[Project]:
    q = db.query(Project).filter(Project.id == project_id)
    if user_id:
        q = q.filter(Project.user_id == user_id)
    else:
        q = q.filter(Project.user_id.is_(None))
    return q.first()


def update_project(db: Session, project: Project, updates: dict) -> Project:
    if "name" in updates and updates["name"]:
        project.name = updates["name"]
    if "description" in updates:
        project.description = updates["description"]
    if "settings" in updates and updates["settings"] is not None:
        project.settings = updates["settings"].model_dump() if hasattr(updates["settings"], "model_dump") else updates["settings"]
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    # Delete files first due to FK
    db.query(ProjectFile).filter(ProjectFile.project_id == project.id).delete()
    db.delete(project)
    db.commit()


def list_files(db: Session, project_id: str) -> List[ProjectFile]:
    return (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.created_at.asc())
        .all()
    )


def find_file(db: Session, project_id: str, name_or_path: str) -> Optional[ProjectFile]:
    key = name_or_path
    try:
        sanitized = sanitize_relative_path(name_or_path)
    except Exception:
        sanitized = name_or_path
    return (
        db.query(ProjectFile)
        .filter(
            ProjectFile.project_id == project_id,
            ((ProjectFile.name == key) | (ProjectFile.path == sanitized)),
        )
        .first()
    )


def create_file(db: Session, project_id: str, name: str, content: str | None, language: str | None, user_id: str | None) -> ProjectFile:
    path = sanitize_relative_path(name)
    lang = language or detect_language(name)
    file = ProjectFile(
        project_id=project_id,
        owner_user_id=user_id,
        name=name,
        path=path,
        language=lang,
        size=len(content or ""),
        is_directory=False,
        content=content or "",
    )
    db.add(file)
    db.commit()
    db.refresh(file)
    return file


def update_file(db: Session, file: ProjectFile, content: str, language: str | None) -> ProjectFile:
    file.content = content
    if language:
        file.language = language
    file.size = len(content or "")
    file.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(file)
    return file


def delete_file(db: Session, file: ProjectFile) -> None:
    db.delete(file)
    db.commit()
