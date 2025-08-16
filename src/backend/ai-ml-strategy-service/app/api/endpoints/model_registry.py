"""
Model Registry API Endpoints - RESTful API for model management, versioning, and deployment
"""

from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, status, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime
import tempfile
import os

from app.services.model_registry import (
    model_registry, 
    RegistrationRequest, 
    ModelArtifacts
)
from app.models.model_registry import (
    Model, ModelVersion, ModelDeployment, ModelABTest,
    ModelStatus, DeploymentStatus
)
from app.core.auth import get_current_user
from app.models.user import User
from app.core.database import get_db_session
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/models", tags=["Model Registry"])

# Request/Response Models

class ModelCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Model name")
    description: str = Field("", max_length=2000, description="Model description")
    category: str = Field(..., description="Model category (prediction, signal, risk)")
    strategy_type: str = Field(..., description="Strategy type (momentum, mean_reversion, etc.)")
    framework: str = Field(..., description="ML framework (scikit-learn, tensorflow, pytorch)")
    model_type: str = Field(..., description="Model type (random_forest, neural_network, etc.)")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")

class ModelVersionCreateRequest(BaseModel):
    version: str = Field(..., description="Semantic version (e.g., 1.0.0)")
    description: str = Field("", description="Version description")
    training_config: Dict[str, Any] = Field(..., description="Training configuration")
    performance_metrics: Dict[str, float] = Field(..., description="Performance metrics")
    business_metrics: Optional[Dict[str, float]] = Field(None, description="Business metrics")
    dataset_version: Optional[str] = Field(None, description="Dataset version used")
    training_job_id: Optional[str] = Field(None, description="Training job reference")
    changelog: Optional[str] = Field(None, description="Changes from previous version")
    
    @validator('performance_metrics')
    def validate_metrics(cls, v):
        required_metrics = ['accuracy', 'precision', 'recall']
        for metric in required_metrics:
            if metric not in v:
                raise ValueError(f"Missing required metric: {metric}")
        return v

class ModelVersionPromoteRequest(BaseModel):
    target_status: str = Field(..., description="Target status (validated, deployed)")
    
    @validator('target_status')
    def validate_status(cls, v):
        valid_statuses = ['validated', 'deployed', 'deprecated']
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v

class ABTestCreateRequest(BaseModel):
    name: str = Field(..., description="A/B test name")
    description: str = Field("", description="Test description")
    control_version_id: int = Field(..., description="Control model version ID")
    treatment_version_id: int = Field(..., description="Treatment model version ID")
    traffic_split: float = Field(0.5, ge=0.1, le=0.9, description="Traffic split for treatment")
    duration_days: int = Field(7, ge=1, le=30, description="Test duration in days")
    success_criteria: Optional[Dict] = Field(None, description="Success criteria")

class ModelComparisonRequest(BaseModel):
    version_1_id: int = Field(..., description="First version ID")
    version_2_id: int = Field(..., description="Second version ID") 
    metrics: List[str] = Field(
        default_factory=lambda: ['accuracy', 'precision', 'recall', 'sharpe_ratio'],
        description="Metrics to compare"
    )

# Response Models

class ModelResponse(BaseModel):
    id: int
    uuid: str
    name: str
    description: str
    category: str
    strategy_type: str
    framework: str
    model_type: str
    status: str
    is_active: bool
    created_at: str
    updated_at: str
    tags: List[str]
    version_count: int
    latest_version: Optional[str]

class ModelVersionResponse(BaseModel):
    id: int
    uuid: str
    model_id: int
    version: str
    artifacts_path: str
    model_file_size: Optional[int]
    training_config: Dict[str, Any]
    performance_metrics: Dict[str, float]
    business_metrics: Optional[Dict[str, float]]
    validation_status: str
    deployment_ready: bool
    status: str
    created_at: str
    description: str
    changelog: Optional[str]

class ModelListResponse(BaseModel):
    models: List[ModelResponse]
    total: int
    limit: int
    offset: int

class ModelVersionListResponse(BaseModel):
    versions: List[ModelVersionResponse]
    total: int
    limit: int

# API Endpoints

@router.post("/", response_model=ModelResponse)
async def create_model(
    request: ModelCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create a new model entry in the registry"""
    try:
        logger.info(f"Creating model {request.name} by user {current_user.id}")
        
        # Check if model name already exists
        existing = db.query(Model).filter(Model.name == request.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model with name '{request.name}' already exists"
            )
        
        # Create model
        model = Model(
            name=request.name,
            description=request.description,
            category=request.category,
            strategy_type=request.strategy_type,
            framework=request.framework,
            model_type=request.model_type,
            created_by=current_user.id,
            tags=request.tags,
            status=ModelStatus.TRAINING
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        return ModelResponse(**model.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to create model: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create model: {str(e)}"
        )

@router.get("/", response_model=ModelListResponse)
async def list_models(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """List models with filtering options"""
    try:
        tag_list = tags.split(',') if tags else None
        
        models = await model_registry.list_models(
            category=category,
            status=status,
            tags=tag_list,
            limit=limit,
            offset=offset,
            db_session=db
        )
        
        # Get total count
        total_query = db.query(Model).filter(Model.is_active == True)
        if category:
            total_query = total_query.filter(Model.category == category)
        if status:
            total_query = total_query.filter(Model.status == status)
        total = total_query.count()
        
        model_responses = [ModelResponse(**model.to_dict()) for model in models]
        
        return ModelListResponse(
            models=model_responses,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )

@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get model by ID"""
    model = db.query(Model).filter(Model.id == model_id, Model.is_active == True).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )
    
    return ModelResponse(**model.to_dict())

@router.post("/{model_id}/versions", response_model=ModelVersionResponse)
async def register_model_version(
    model_id: int,
    request: ModelVersionCreateRequest,
    artifacts_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Register a new model version with artifacts"""
    try:
        # Verify model exists
        model = db.query(Model).filter(Model.id == model_id, Model.is_active == True).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        # Save uploaded artifacts to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
            content = await artifacts_file.read()
            temp_file.write(content)
            temp_artifacts_path = temp_file.name
        
        try:
            # Create artifacts object
            artifacts = ModelArtifacts(
                model_file=temp_artifacts_path,
                code_files=[],  # Will be extracted from tar
                metadata={'original_filename': artifacts_file.filename}
            )
            
            # Create registration request
            reg_request = RegistrationRequest(
                name=model.name,
                description=request.description,
                category=model.category,
                strategy_type=model.strategy_type,
                framework=model.framework,
                model_type=model.model_type,
                version=request.version,
                artifacts=artifacts,
                training_config=request.training_config,
                performance_metrics=request.performance_metrics,
                business_metrics=request.business_metrics,
                dataset_version=request.dataset_version,
                training_job_id=request.training_job_id,
                tags=model.tags
            )
            
            # Register version
            model_version = await model_registry.register_model(
                reg_request, 
                current_user.id, 
                db
            )
            
            # Update changelog if provided
            if request.changelog:
                model_version.changelog = request.changelog
                db.commit()
            
            return ModelVersionResponse(**model_version.to_dict())
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_artifacts_path):
                os.unlink(temp_artifacts_path)
        
    except Exception as e:
        logger.error(f"Failed to register model version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register model version: {str(e)}"
        )

@router.get("/{model_id}/versions", response_model=ModelVersionListResponse)
async def list_model_versions(
    model_id: int,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """List all versions for a model"""
    try:
        # Verify model exists
        model = db.query(Model).filter(Model.id == model_id, Model.is_active == True).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        versions = await model_registry.get_model_versions(model_id, limit, db)
        version_responses = [ModelVersionResponse(**v.to_dict()) for v in versions]
        
        return ModelVersionListResponse(
            versions=version_responses,
            total=len(model.versions),
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list model versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list model versions: {str(e)}"
        )

@router.get("/{model_id}/versions/{version}", response_model=ModelVersionResponse)
async def get_model_version(
    model_id: int,
    version: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get specific model version"""
    model_version = await model_registry.get_model_version(model_id, version, db)
    
    if not model_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version {version} not found for model {model_id}"
        )
    
    return ModelVersionResponse(**model_version.to_dict())

@router.post("/versions/{version_id}/promote", response_model=ModelVersionResponse)
async def promote_model_version(
    version_id: int,
    request: ModelVersionPromoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Promote model version to new status"""
    try:
        target_status = ModelStatus(request.target_status)
        model_version = await model_registry.promote_version(version_id, target_status, db)
        
        return ModelVersionResponse(**model_version.to_dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to promote model version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to promote model version: {str(e)}"
        )

@router.get("/versions/{version_id}/artifacts")
async def download_model_artifacts(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Download model artifacts"""
    try:
        model_version = db.query(ModelVersion).get(version_id)
        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version {version_id} not found"
            )
        
        # Download artifacts to temporary location
        local_path = await model_registry.download_model_artifacts(model_version)
        
        # Return file
        return FileResponse(
            path=local_path,
            filename=f"model_artifacts_{model_version.model.name}_{model_version.version}.tar.gz",
            media_type='application/gzip'
        )
        
    except Exception as e:
        logger.error(f"Failed to download artifacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download artifacts: {str(e)}"
        )

@router.post("/versions/compare")
async def compare_model_versions(
    request: ModelComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Compare performance metrics between two model versions"""
    try:
        comparison = await model_registry.compare_versions(
            request.version_1_id,
            request.version_2_id,
            request.metrics,
            db
        )
        
        return comparison
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to compare model versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare model versions: {str(e)}"
        )

@router.post("/ab-tests", response_model=dict)
async def create_ab_test(
    request: ABTestCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create A/B test for model comparison"""
    try:
        ab_test = await model_registry.create_ab_test(
            name=request.name,
            description=request.description,
            control_version_id=request.control_version_id,
            treatment_version_id=request.treatment_version_id,
            traffic_split=request.traffic_split,
            duration_days=request.duration_days,
            success_criteria=request.success_criteria,
            db_session=db
        )
        
        return ab_test.to_dict()
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create A/B test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create A/B test: {str(e)}"
        )

@router.get("/versions/{version_id}/lineage")
async def get_model_lineage(
    version_id: int,
    depth: int = Query(5, ge=1, le=10, description="Lineage depth"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get model version lineage (ancestry and descendants)"""
    try:
        lineage = await model_registry.get_model_lineage(version_id, depth, db)
        return lineage
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get model lineage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model lineage: {str(e)}"
        )

@router.delete("/{model_id}")
async def archive_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Archive a model (soft delete)"""
    try:
        model = db.query(Model).filter(Model.id == model_id, Model.is_active == True).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        # Check if model has active deployments
        active_deployments = db.query(ModelDeployment).filter(
            ModelDeployment.model_id == model_id,
            ModelDeployment.is_active == True,
            ModelDeployment.status == DeploymentStatus.DEPLOYED
        ).count()
        
        if active_deployments > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot archive model with {active_deployments} active deployments"
            )
        
        # Archive model and all versions
        model.is_active = False
        model.status = ModelStatus.ARCHIVED
        model.updated_at = datetime.utcnow()
        
        for version in model.versions:
            version.is_active = False
            version.status = ModelStatus.ARCHIVED
        
        db.commit()
        
        logger.info(f"Archived model {model_id}")
        return {"message": f"Model {model_id} archived successfully"}
        
    except Exception as e:
        logger.error(f"Failed to archive model: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive model: {str(e)}"
        )