"""
Model training API endpoints for Phase 4: Model Training Orchestrator.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user_id, require_permission, create_rate_limit_dependency
from app.services.training_job_manager import TrainingJobManager
from app.services.resource_allocator import ResourceAllocator
from app.services.vertex_ai_integration import VertexAIIntegrationService
from app.services.hyperparameter_tuning import HyperparameterTuningService
from app.models.training import (
    JobType, JobStatus, InstanceType, ModelFramework, TrainingPriority,
    OptimizationObjective, OptimizationAlgorithm
)

router = APIRouter(prefix="/training")

# Service instances
training_manager = TrainingJobManager()
resource_allocator = ResourceAllocator()
vertex_ai_service = VertexAIIntegrationService()
hyperparameter_service = HyperparameterTuningService()

# Rate limiting
rate_limit = create_rate_limit_dependency(requests_per_minute=30)


# Request/Response Models
class TrainingJobRequest(BaseModel):
    strategy_id: str = Field(..., description="Strategy ID to train")
    dataset_id: str = Field(..., description="Dataset ID for training")
    job_name: str = Field(..., min_length=1, max_length=255)
    job_type: JobType = Field(default=JobType.TRAINING)
    instance_type: InstanceType = Field(..., description="Compute instance type")
    machine_type: Optional[str] = Field(None, max_length=100)
    disk_size: int = Field(default=100, ge=10, le=1000, description="Disk size in GB")
    timeout_hours: int = Field(default=24, ge=1, le=72, description="Timeout in hours")
    priority: TrainingPriority = Field(default=TrainingPriority.NORMAL)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    training_config: Dict[str, Any] = Field(default_factory=dict)
    model_config: Dict[str, Any] = Field(default_factory=dict)


class HyperparameterTuningRequest(BaseModel):
    strategy_id: str = Field(..., description="Strategy ID to tune")
    dataset_id: str = Field(..., description="Dataset ID for tuning")
    job_name: str = Field(..., min_length=1, max_length=255)
    parameter_space: Dict[str, Any] = Field(..., description="Hyperparameter search space")
    optimization_algorithm: OptimizationAlgorithm = Field(default=OptimizationAlgorithm.RANDOM_SEARCH)
    optimization_objective: OptimizationObjective = Field(..., description="Maximize or minimize")
    objective_metric: str = Field(..., description="Metric to optimize")
    max_trials: int = Field(default=100, ge=1, le=1000)
    max_parallel_trials: int = Field(default=4, ge=1, le=20)
    max_trial_duration_hours: int = Field(default=4, ge=1, le=24)
    instance_type: InstanceType = Field(default=InstanceType.GPU_T4)
    priority: TrainingPriority = Field(default=TrainingPriority.NORMAL)
    early_stopping_config: Dict[str, Any] = Field(default_factory=dict)


class JobProgressUpdate(BaseModel):
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    logs: Optional[List[str]] = None
    metrics: Optional[Dict[str, float]] = None


class JobCompletionData(BaseModel):
    final_metrics: Optional[Dict[str, float]] = None
    resource_usage: Optional[Dict[str, Any]] = None


class TrialResultData(BaseModel):
    status: JobStatus = Field(default=JobStatus.COMPLETED)
    objective_value: Optional[float] = None
    final_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    early_stopped: bool = Field(default=False)
    compute_cost: float = Field(default=0.0)


class ResourceRecommendationRequest(BaseModel):
    job_type: str = Field(default="training")
    dataset_size_mb: float = Field(default=100, ge=1)
    model_complexity: str = Field(default="medium", regex="^(low|medium|high)$")
    estimated_duration_hours: float = Field(default=4, ge=0.1, le=72)
    priority: TrainingPriority = Field(default=TrainingPriority.NORMAL)
    max_budget: Optional[float] = Field(None, ge=0)


# Training Job Endpoints
@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_training_job(
    request: TrainingJobRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Create a new training job."""
    try:
        job_data = request.dict()
        job_data["user_id"] = str(user_id)
        
        result = await training_manager.create_training_job(job_data, str(user_id), db)
        
        if result["success"]:
            return result
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


@router.get("/jobs")
async def list_training_jobs(
    status_filter: Optional[str] = None,
    job_type: Optional[str] = None,
    strategy_id: Optional[str] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List training jobs for the user."""
    try:
        filters = {
            "status": status_filter,
            "job_type": job_type,
            "strategy_id": strategy_id,
            "start_date_from": start_date_from,
            "start_date_to": start_date_to,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        result = await training_manager.list_user_jobs(str(user_id), filters, db)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs/{job_id}")
async def get_training_job(
    job_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a training job."""
    try:
        result = await training_manager.get_job_details(job_id, str(user_id), db)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/jobs/{job_id}/start")
async def start_training_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("start_training"))
):
    """Start a training job."""
    try:
        # Start job in background
        background_tasks.add_task(
            training_manager.start_next_job,
            db
        )
        
        return {"message": "Training job start requested", "job_id": job_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/jobs/{job_id}/progress")
async def update_job_progress(
    job_id: str,
    request: JobProgressUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Update training job progress."""
    try:
        progress_data = request.dict(exclude_unset=True)
        
        result = await training_manager.update_job_progress(job_id, progress_data, db)
        
        if result["success"]:
            return result
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


@router.post("/jobs/{job_id}/complete")
async def complete_training_job(
    job_id: str,
    request: JobCompletionData,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("complete_training"))
):
    """Mark a training job as completed."""
    try:
        completion_data = request.dict(exclude_unset=True)
        
        result = await training_manager.complete_job(job_id, completion_data, db)
        
        if result["success"]:
            return result
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


@router.post("/jobs/{job_id}/cancel")
async def cancel_training_job(
    job_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Cancel a training job."""
    try:
        result = await training_manager.cancel_job(job_id, str(user_id), db)
        
        if result["success"]:
            return result
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


@router.get("/jobs/{job_id}/logs")
async def get_training_logs(
    job_id: str,
    max_lines: int = Query(default=1000, le=10000),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get training job logs."""
    try:
        # First verify user has access to this job
        job_details = await training_manager.get_job_details(job_id, str(user_id), db)
        
        if "error" in job_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or access denied"
            )
        
        # Get logs from training logs or Vertex AI
        logs = job_details.get("training_logs", [])
        
        # Limit logs if needed
        if len(logs) > max_lines:
            logs = logs[-max_lines:]
        
        return {
            "job_id": job_id,
            "logs": logs,
            "log_count": len(logs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Hyperparameter Tuning Endpoints
@router.post("/hyperparameter-tuning", status_code=status.HTTP_201_CREATED)
async def create_hyperparameter_tuning_job(
    request: HyperparameterTuningRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Create a new hyperparameter tuning job."""
    try:
        job_data = request.dict()
        job_data["user_id"] = str(user_id)
        
        result = await hyperparameter_service.create_tuning_job(job_data, str(user_id), db)
        
        if result["success"]:
            return result
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


@router.post("/hyperparameter-tuning/{tuning_job_id}/start")
async def start_hyperparameter_tuning(
    tuning_job_id: str,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("start_hyperparameter_tuning"))
):
    """Start a hyperparameter tuning job."""
    try:
        # Start tuning job in background
        background_tasks.add_task(
            hyperparameter_service.start_tuning_job,
            tuning_job_id,
            db
        )
        
        return {"message": "Hyperparameter tuning job started", "tuning_job_id": tuning_job_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/hyperparameter-tuning/{tuning_job_id}/status")
async def get_tuning_status(
    tuning_job_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get status of hyperparameter tuning job."""
    try:
        result = await hyperparameter_service.get_tuning_status(tuning_job_id, db)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/hyperparameter-tuning/{tuning_job_id}/suggest-trial")
async def suggest_next_trial(
    tuning_job_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Suggest parameters for the next hyperparameter trial."""
    try:
        result = await hyperparameter_service.suggest_next_trial(tuning_job_id, db)
        
        if result["success"]:
            return result
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


@router.put("/hyperparameter-tuning/trials/{trial_id}/result")
async def update_trial_result(
    trial_id: str,
    request: TrialResultData,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Update hyperparameter trial result."""
    try:
        result_data = request.dict()
        
        result = await hyperparameter_service.update_trial_result(trial_id, result_data, db)
        
        if result["success"]:
            return result
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


@router.post("/hyperparameter-tuning/{tuning_job_id}/stop")
async def stop_hyperparameter_tuning(
    tuning_job_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Stop a hyperparameter tuning job."""
    try:
        result = await hyperparameter_service.stop_tuning_job(tuning_job_id, str(user_id), db)
        
        if result["success"]:
            return result
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


# Resource Management Endpoints
@router.get("/resources")
async def get_available_resources(
    instance_type: Optional[str] = None,
    provider: Optional[str] = None,
    region: Optional[str] = None,
    max_cost_per_hour: Optional[float] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get available compute resources."""
    try:
        filters = {
            "instance_type": instance_type,
            "provider": provider,
            "region": region,
            "max_cost_per_hour": max_cost_per_hour
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        result = await resource_allocator.get_available_resources(filters, db)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/resources/recommend")
async def recommend_optimal_resource(
    request: ResourceRecommendationRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Get optimal resource recommendations for a job."""
    try:
        job_requirements = request.dict()
        job_requirements["user_id"] = str(user_id)
        
        user_preferences = {
            "max_budget": request.max_budget
        } if request.max_budget else {}
        
        result = await resource_allocator.recommend_optimal_resource(
            job_requirements, user_preferences, db
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/quota")
async def get_user_quota(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's resource quota status."""
    try:
        result = await resource_allocator.quota_manager.get_quota_status(str(user_id), db)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/queue/status")
async def get_queue_status(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current training queue status."""
    try:
        result = await training_manager.get_queue_status(db)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Utility Endpoints
@router.get("/job-types")
async def get_job_types():
    """Get available job types."""
    return {
        "job_types": [
            {"value": job_type.value, "name": job_type.value.replace("_", " ").title()}
            for job_type in JobType
        ]
    }


@router.get("/instance-types")
async def get_instance_types():
    """Get available instance types."""
    return {
        "instance_types": [
            {"value": instance.value, "name": instance.value.replace("_", " ").upper()}
            for instance in InstanceType
        ]
    }


@router.get("/optimization-algorithms")
async def get_optimization_algorithms():
    """Get available optimization algorithms."""
    return {
        "algorithms": [
            {"value": algo.value, "name": algo.value.replace("_", " ").title()}
            for algo in OptimizationAlgorithm
        ]
    }


@router.get("/model-frameworks")
async def get_model_frameworks():
    """Get available model frameworks."""
    return {
        "frameworks": [
            {"value": framework.value, "name": framework.value.title()}
            for framework in ModelFramework
        ]
    }


@router.get("/health")
async def training_service_health():
    """Training service health check."""
    return {
        "status": "healthy",
        "service": "training-orchestrator",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "training_manager": "operational",
            "resource_allocator": "operational",
            "hyperparameter_tuning": "operational",
            "vertex_ai_integration": "operational"
        }
    }