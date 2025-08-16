"""
Strategy template API endpoints.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user_id, create_rate_limit_dependency
from app.services.template_service import TemplateService
from app.services.execution_engine import ExecutionEngine

router = APIRouter()

# Dependency instances
execution_engine = ExecutionEngine()
template_service = TemplateService(execution_engine)

# Rate limiting
rate_limit = create_rate_limit_dependency(requests_per_minute=30)


# Request/Response Models
class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=1000)
    category: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    documentation: Optional[str] = Field(default="", max_length=5000)
    difficulty_level: str = Field(default="intermediate")
    is_public: bool = Field(default=False)
    tags: Optional[List[str]] = Field(default_factory=list)


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1)
    parameters: Optional[Dict[str, Any]] = None
    documentation: Optional[str] = Field(None, max_length=5000)
    difficulty_level: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class TemplateCloneRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class TemplateRatingRequest(BaseModel):
    rating: float = Field(..., ge=1.0, le=5.0)


class TemplateFilters(BaseModel):
    category: Optional[str] = None
    difficulty_level: Optional[str] = None
    is_public: Optional[bool] = None
    author_id: Optional[str] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    sort_by: Optional[str] = Field(default="created_at")
    sort_order: Optional[str] = Field(default="desc")
    limit: Optional[int] = Field(default=50, le=100)
    offset: Optional[int] = Field(default=0, ge=0)


# Template CRUD Endpoints
@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    request: TemplateCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Create a new strategy template."""
    try:
        result = await template_service.create_template(
            template_data=request.dict(),
            author_id=str(user_id),
            db=db
        )
        
        if result["success"]:
            return {
                "template_id": result["template_id"],
                "validation_warnings": result.get("validation_warnings", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates")
async def list_templates(
    category: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    is_public: Optional[bool] = None,
    author_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List strategy templates with optional filtering."""
    try:
        filters = {
            "category": category,
            "difficulty_level": difficulty_level,
            "is_public": is_public,
            "author_id": author_id,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": min(limit, 100),
            "offset": offset
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        templates = await template_service.list_templates(filters, db)
        
        return {
            "templates": templates,
            "total": len(templates),
            "limit": limit,
            "offset": offset,
            "filters": filters
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific template by ID."""
    try:
        template = await template_service.get_template(template_id, db)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    request: TemplateUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Update an existing template."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        result = await template_service.update_template(
            template_id=template_id,
            update_data=update_data,
            user_id=str(user_id),
            db=db
        )
        
        if result["success"]:
            return {
                "message": "Template updated successfully",
                "validation_warnings": result.get("validation_warnings", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a template."""
    try:
        result = await template_service.delete_template(
            template_id=template_id,
            user_id=str(user_id),
            db=db
        )
        
        if result["success"]:
            return {"message": "Template deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Template Operations
@router.post("/templates/{template_id}/clone")
async def clone_template(
    template_id: str,
    request: TemplateCloneRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Clone a template to create a new strategy."""
    try:
        clone_data = request.dict()
        
        result = await template_service.clone_template(
            template_id=template_id,
            user_id=str(user_id),
            clone_data=clone_data,
            db=db
        )
        
        if result["success"]:
            return {
                "strategy_id": result["strategy_id"],
                "message": "Template cloned successfully",
                "template_usage_count": result["template_usage_count"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/templates/{template_id}/rate")
async def rate_template(
    template_id: str,
    request: TemplateRatingRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Rate a template."""
    try:
        result = await template_service.rate_template(
            template_id=template_id,
            rating=request.rating,
            user_id=str(user_id),
            db=db
        )
        
        if result["success"]:
            return {
                "message": "Template rated successfully",
                "new_rating": result["new_rating"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Template Discovery
@router.get("/templates/categories")
async def get_template_categories():
    """Get available template categories."""
    try:
        categories = await template_service.get_template_categories()
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates/stats")
async def get_template_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get template statistics and analytics."""
    try:
        stats = await template_service.get_template_stats(db)
        return {"stats": stats}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates/trending")
async def get_trending_templates(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get trending/popular templates."""
    try:
        filters = {
            "is_public": True,
            "sort_by": "usage_count",
            "sort_order": "desc",
            "limit": min(limit, 50),
            "offset": 0
        }
        
        templates = await template_service.list_templates(filters, db)
        
        return {
            "trending_templates": templates,
            "total": len(templates)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates/recommended")
async def get_recommended_templates(
    limit: int = 10,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized template recommendations."""
    try:
        # Simple recommendation: highest rated public templates
        # In production, this would use ML-based recommendations
        filters = {
            "is_public": True,
            "sort_by": "rating",
            "sort_order": "desc",
            "limit": min(limit, 20),
            "offset": 0
        }
        
        templates = await template_service.list_templates(filters, db)
        
        # Filter out templates by same user
        recommended = [
            template for template in templates 
            if template["author_id"] != str(user_id)
        ][:limit]
        
        return {
            "recommended_templates": recommended,
            "total": len(recommended)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates/by-author/{author_id}")
async def get_templates_by_author(
    author_id: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get public templates by a specific author."""
    try:
        filters = {
            "author_id": author_id,
            "is_public": True,
            "sort_by": "created_at",
            "sort_order": "desc",
            "limit": min(limit, 50),
            "offset": offset
        }
        
        templates = await template_service.list_templates(filters, db)
        
        return {
            "templates": templates,
            "author_id": author_id,
            "total": len(templates),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates/search")
async def search_templates(
    q: str = "",
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Advanced template search."""
    try:
        filters = {
            "is_public": True,
            "search": q if q else None,
            "category": category,
            "difficulty_level": difficulty,
            "sort_by": "usage_count",
            "sort_order": "desc",
            "limit": min(limit, 50),
            "offset": offset
        }
        
        if tags:
            filters["tags"] = [tag.strip() for tag in tags.split(",")]
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        templates = await template_service.list_templates(filters, db)
        
        return {
            "templates": templates,
            "query": q,
            "filters": {
                "category": category,
                "difficulty": difficulty,
                "tags": filters.get("tags")
            },
            "total": len(templates),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )