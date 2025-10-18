"""Routes for component and template libraries."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.db import get_db
from app.services import workflows as workflow_service
from models import NoCodeComponent, NoCodeTemplate, User
from schemas_updated import ComponentResponse, TemplateResponse, WorkflowCreate, WorkflowResponse

router = APIRouter(prefix="/api", tags=["library"])


@router.get("/components", response_model=List[ComponentResponse])
async def get_components(
    category: Optional[str] = None,
    is_builtin: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the available workflow components."""

    try:
        query = db.query(NoCodeComponent)

        if category:
            query = query.filter(NoCodeComponent.category == category)
        if is_builtin is not None:
            query = query.filter(NoCodeComponent.is_builtin == is_builtin)

        # Show public components and user's own components
        query = query.filter(
            (NoCodeComponent.is_public == True) | (NoCodeComponent.author_id == current_user.id)
        )

        components = query.order_by(NoCodeComponent.category, NoCodeComponent.name).all()
        return [ComponentResponse.from_orm(component) for component in components]
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Failed to fetch components: {exc}") from exc


@router.get("/templates", response_model=List[TemplateResponse])
async def get_templates(
    category: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    is_featured: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Return workflow templates filtered by category/flags."""

    try:
        query = db.query(NoCodeTemplate).filter(NoCodeTemplate.is_public == True)  # noqa: E712

        if category:
            query = query.filter(NoCodeTemplate.category == category)
        if difficulty_level:
            query = query.filter(NoCodeTemplate.difficulty_level == difficulty_level)
        if is_featured is not None:
            query = query.filter(NoCodeTemplate.is_featured == is_featured)

        templates = query.order_by(NoCodeTemplate.rating.desc()).all()
        return [TemplateResponse.from_orm(template) for template in templates]
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {exc}") from exc


@router.post("/templates/{template_id}/use", response_model=WorkflowResponse)
async def create_workflow_from_template(
    template_id: str,
    workflow_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Instantiate a workflow from a stored template."""

    try:
        template = (
            db.query(NoCodeTemplate)
            .filter(NoCodeTemplate.uuid == template_id, NoCodeTemplate.is_public == True)  # noqa: E712
            .first()
        )

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        payload = WorkflowCreate(
            name=workflow_name,
            description=f"Created from template: {template.name}",
            category=template.category,
            tags=template.keywords,
            workflow_data=template.template_data,
            execution_mode="backtest",
        )

        workflow = workflow_service.create_workflow(db, current_user, payload)
        workflow.parent_workflow_id = None
        workflow.is_template = False

        template.usage_count = (template.usage_count or 0) + 1
        db.commit()
        db.refresh(workflow)

        return WorkflowResponse.from_orm(workflow)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow from template: {exc}") from exc
