"""Workflow domain services."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Union
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import NoCodeWorkflow, User
from schemas_updated import WorkflowCreate, WorkflowUpdate


def _resolve_user_id(current_user: User, dev_mode: bool) -> int:
    """Return the authenticated user's identifier regardless of mode."""

    return current_user.id


def ensure_workflow_access(
    db: Session,
    workflow_uuid: Union[str, UUID],
    current_user: User,
    *,
    dev_mode: bool,
) -> NoCodeWorkflow:
    """Fetch workflow ensuring the caller has access rights."""

    if isinstance(workflow_uuid, str):
        try:
            workflow_uuid_value: Union[str, UUID] = UUID(workflow_uuid)
        except ValueError:
            workflow_uuid_value = workflow_uuid
    else:
        workflow_uuid_value = workflow_uuid

    workflow = (
        db.query(NoCodeWorkflow)
        .filter(
            NoCodeWorkflow.uuid == workflow_uuid_value,
            (NoCodeWorkflow.user_id == current_user.id) | (NoCodeWorkflow.is_public == True),  # noqa: E712
        )
        .first()
    )

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow




def accessible_workflows_query(
    db: Session,
    current_user: User,
    *,
    dev_mode: bool,
):
    """Return SQLAlchemy query for workflows accessible by the current user."""

    user_id = _resolve_user_id(current_user, dev_mode)

    return db.query(NoCodeWorkflow).filter(
        (NoCodeWorkflow.user_id == user_id) | (NoCodeWorkflow.is_public == True)  # noqa: E712
    )

def list_user_workflows(
    db: Session,
    current_user: User,
    *,
    skip: int,
    limit: int,
    category: Optional[str],
    is_public: Optional[bool],
    dev_mode: bool,
) -> List[NoCodeWorkflow]:
    """Return workflows accessible to the user with optional filters."""

    query = accessible_workflows_query(db, current_user, dev_mode=dev_mode)

    if category:
        query = query.filter(NoCodeWorkflow.category == category)
    if is_public is not None:
        query = query.filter(NoCodeWorkflow.is_public == is_public)

    return query.order_by(NoCodeWorkflow.updated_at.desc()).offset(skip).limit(limit).all()


def create_workflow(
    db: Session,
    current_user: User,
    payload: WorkflowCreate,
) -> NoCodeWorkflow:
    """Create a workflow using the provided payload."""

    workflow = NoCodeWorkflow(
        name=payload.name,
        description=payload.description,
        category=payload.category or "custom",
        tags=payload.tags or [],
        user_id=current_user.id,
        workflow_data=payload.workflow_data or {"nodes": [], "edges": []},
        execution_mode=payload.execution_mode or "backtest",
    )

    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


def update_workflow(
    db: Session,
    workflow: NoCodeWorkflow,
    payload: WorkflowUpdate,
) -> NoCodeWorkflow:
    """Update workflow attributes."""

    if payload.name is not None:
        workflow.name = payload.name
    if payload.description is not None:
        workflow.description = payload.description
    if payload.category is not None:
        workflow.category = payload.category
    if payload.tags is not None:
        workflow.tags = payload.tags
    if payload.workflow_data is not None:
        workflow.workflow_data = payload.workflow_data
    if payload.execution_mode is not None:
        workflow.execution_mode = payload.execution_mode
    if payload.is_public is not None:
        workflow.is_public = payload.is_public

    db.commit()
    db.refresh(workflow)
    return workflow


def delete_workflow(db: Session, workflow: NoCodeWorkflow) -> None:
    """Remove workflow from the database."""

    db.delete(workflow)
    db.commit()


def record_tags(workflow: NoCodeWorkflow) -> Iterable[str]:
    """Convenience helper to return workflow tags safely."""

    return workflow.tags or []


def ensure_owner(workflow: NoCodeWorkflow, current_user: User) -> None:
    """Ensure the provided user owns the workflow."""

    if workflow.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation allowed only for workflow owners")
