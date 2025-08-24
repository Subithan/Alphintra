"""
Research Mode API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pydantic import BaseModel, Field

from app.core.auth import get_current_user_id

router = APIRouter(prefix="/research")

class ResearchSessionRequest(BaseModel):
    workflow_definition: Dict[str, Any] = Field(..., description="The workflow definition from the no-code UI")
    config: Dict[str, Any] = Field(..., description="Research session configuration")

@router.post("/from-workflow")
async def start_research_session(
    request: ResearchSessionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Starts a new research session.
    """
    # Placeholder implementation
    return {"message": "Research session started", "notebook_template": request.config.get("notebook_template")}
