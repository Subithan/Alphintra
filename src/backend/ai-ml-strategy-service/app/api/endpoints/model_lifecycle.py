"""
Model Lifecycle Management API Endpoints - Automated model lifecycle operations
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field, validator
import pandas as pd

from app.services.model_lifecycle import (
    model_lifecycle,
    LifecycleConfig,
    LifecycleStatus,
    LifecycleEvent,
    LifecycleStage,
    LifecycleAction
)
from app.services.k8s_deployment import DeploymentConfig
from app.core.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lifecycle", tags=["Model Lifecycle"])

# Request/Response Models

class LifecycleConfigRequest(BaseModel):
    model_id: int = Field(..., description="Model ID")
    retrain_schedule: Optional[str] = Field("0 2 * * *", description="Cron schedule for retraining")
    enable_auto_retrain: bool = Field(True, description="Enable automatic retraining")
    min_retrain_interval_hours: int = Field(24, ge=1, description="Minimum hours between retrains")
    validation_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Validation threshold")
    performance_improvement_threshold: float = Field(0.05, ge=0.0, description="Required improvement")
    max_performance_degradation: float = Field(0.10, ge=0.0, description="Max allowed degradation")
    ab_test_duration_hours: int = Field(168, ge=24, description="A/B test duration in hours")
    ab_test_traffic_split: float = Field(0.1, ge=0.01, le=0.5, description="Traffic split for A/B test")
    ab_test_min_samples: int = Field(1000, ge=100, description="Minimum samples for A/B test")
    canary_percentage: int = Field(10, ge=1, le=50, description="Canary deployment percentage")
    canary_duration_hours: int = Field(24, ge=1, description="Canary duration in hours")
    full_rollout_threshold: float = Field(0.02, ge=0.0, description="Full rollout threshold")
    enable_auto_rollback: bool = Field(True, description="Enable automatic rollback")
    rollback_error_rate_threshold: float = Field(0.15, ge=0.0, le=1.0, description="Error rate rollback threshold")
    rollback_latency_threshold_ms: float = Field(2000, ge=100, description="Latency rollback threshold")
    min_training_samples: int = Field(10000, ge=1000, description="Minimum training samples")
    max_data_age_days: int = Field(30, ge=1, description="Maximum data age in days")
    enable_notifications: bool = Field(True, description="Enable notifications")
    notification_channels: List[str] = Field(default=["email"], description="Notification channels")

class RetrainTriggerRequest(BaseModel):
    model_id: int = Field(..., description="Model ID")
    force: bool = Field(False, description="Force retrain ignoring intervals")

class ValidationRequest(BaseModel):
    model_version_id: int = Field(..., description="Model version ID to validate")

class StagingDeploymentRequest(BaseModel):
    model_version_id: int = Field(..., description="Model version ID to deploy")
    cpu_request: str = Field("250m", description="CPU request")
    cpu_limit: str = Field("1000m", description="CPU limit")
    memory_request: str = Field("512Mi", description="Memory request")
    memory_limit: str = Field("2Gi", description="Memory limit")
    min_replicas: int = Field(1, ge=1, description="Minimum replicas")
    max_replicas: int = Field(3, ge=1, description="Maximum replicas")

class ABTestRequest(BaseModel):
    control_version_id: int = Field(..., description="Control model version ID")
    treatment_version_id: int = Field(..., description="Treatment model version ID")
    traffic_split: Optional[float] = Field(None, ge=0.01, le=0.5, description="Traffic split")

class RollbackRequest(BaseModel):
    deployment_id: int = Field(..., description="Deployment ID to rollback")
    reason: str = Field("Manual rollback", description="Rollback reason")

# Response Models

class LifecycleConfigResponse(BaseModel):
    model_id: int
    retrain_schedule: str
    enable_auto_retrain: bool
    min_retrain_interval_hours: int
    validation_threshold: float
    performance_improvement_threshold: float
    max_performance_degradation: float
    ab_test_duration_hours: int
    ab_test_traffic_split: float
    ab_test_min_samples: int
    canary_percentage: int
    canary_duration_hours: int
    full_rollout_threshold: float
    enable_auto_rollback: bool
    rollback_error_rate_threshold: float
    rollback_latency_threshold_ms: float
    min_training_samples: int
    max_data_age_days: int
    enable_notifications: bool
    notification_channels: List[str]

class LifecycleStatusResponse(BaseModel):
    model_id: int
    current_stage: str
    current_version_id: Optional[int]
    production_version_id: Optional[int]
    staging_version_id: Optional[int]
    training_in_progress: bool
    ab_test_active: bool
    canary_deployment_active: bool
    last_retrain: Optional[float]
    next_scheduled_retrain: Optional[float]
    last_deployment: Optional[float]
    health_score: float
    performance_trend: str
    recommendations: List[str]

class LifecycleEventResponse(BaseModel):
    model_id: int
    event_type: str
    timestamp: float
    stage_from: Optional[str]
    stage_to: Optional[str]
    model_version_id: Optional[int]
    deployment_id: Optional[int]
    success: bool
    error_message: Optional[str]
    metadata: Dict[str, Any]

class ValidationResultResponse(BaseModel):
    model_version_id: int
    validation_passed: bool
    validation_results: Dict[str, float]
    deployment_ready: bool

# Initialize lifecycle service on startup
@router.on_event("startup")
async def startup_event():
    try:
        await model_lifecycle.initialize()
        logger.info("Model lifecycle service started successfully")
    except Exception as e:
        logger.error(f"Failed to start model lifecycle service: {e}")

@router.on_event("shutdown")
async def shutdown_event():
    try:
        await model_lifecycle.cleanup()
        logger.info("Model lifecycle service stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping model lifecycle service: {e}")

# API Endpoints

@router.post("/setup")
async def setup_lifecycle(
    request: LifecycleConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Setup lifecycle management for a model"""
    try:
        logger.info(f"Setting up lifecycle for model {request.model_id} by user {current_user.id}")
        
        # Convert request to config object
        config = LifecycleConfig(
            model_id=request.model_id,
            retrain_schedule=request.retrain_schedule,
            enable_auto_retrain=request.enable_auto_retrain,
            min_retrain_interval_hours=request.min_retrain_interval_hours,
            validation_threshold=request.validation_threshold,
            performance_improvement_threshold=request.performance_improvement_threshold,
            max_performance_degradation=request.max_performance_degradation,
            ab_test_duration_hours=request.ab_test_duration_hours,
            ab_test_traffic_split=request.ab_test_traffic_split,
            ab_test_min_samples=request.ab_test_min_samples,
            canary_percentage=request.canary_percentage,
            canary_duration_hours=request.canary_duration_hours,
            full_rollout_threshold=request.full_rollout_threshold,
            enable_auto_rollback=request.enable_auto_rollback,
            rollback_error_rate_threshold=request.rollback_error_rate_threshold,
            rollback_latency_threshold_ms=request.rollback_latency_threshold_ms,
            min_training_samples=request.min_training_samples,
            max_data_age_days=request.max_data_age_days,
            enable_notifications=request.enable_notifications,
            notification_channels=request.notification_channels
        )
        
        # Setup lifecycle
        success = await model_lifecycle.setup_lifecycle(request.model_id, config)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to setup lifecycle management"
            )
        
        return {
            "message": f"Lifecycle management setup completed for model {request.model_id}",
            "config": LifecycleConfigResponse(**config.__dict__)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up lifecycle: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up lifecycle: {str(e)}"
        )

@router.post("/retrain")
async def trigger_retrain(
    request: RetrainTriggerRequest,
    current_user: User = Depends(get_current_user)
):
    """Trigger model retraining"""
    try:
        logger.info(f"Triggering retrain for model {request.model_id} by user {current_user.id}")
        
        success = await model_lifecycle.trigger_retrain(
            model_id=request.model_id,
            force=request.force
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to trigger retraining. Check if training is already in progress or minimum interval not met."
            )
        
        return {
            "message": f"Retraining triggered for model {request.model_id}",
            "force": request.force
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering retrain: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering retrain: {str(e)}"
        )

@router.post("/validate", response_model=ValidationResultResponse)
async def validate_model_version(
    request: ValidationRequest,
    current_user: User = Depends(get_current_user)
):
    """Validate a model version"""
    try:
        logger.info(f"Validating model version {request.model_version_id} by user {current_user.id}")
        
        validation_passed, validation_results = await model_lifecycle.validate_model_version(
            request.model_version_id
        )
        
        return ValidationResultResponse(
            model_version_id=request.model_version_id,
            validation_passed=validation_passed,
            validation_results=validation_results,
            deployment_ready=validation_passed
        )
        
    except Exception as e:
        logger.error(f"Error validating model version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating model version: {str(e)}"
        )

@router.post("/deploy/staging")
async def deploy_to_staging(
    request: StagingDeploymentRequest,
    current_user: User = Depends(get_current_user)
):
    """Deploy model version to staging"""
    try:
        logger.info(f"Deploying model version {request.model_version_id} to staging by user {current_user.id}")
        
        # Create deployment config
        deployment_config = DeploymentConfig(
            model_version_id=request.model_version_id,
            deployment_name=f"model-v{request.model_version_id}-staging",
            environment="staging",
            cpu_request=request.cpu_request,
            cpu_limit=request.cpu_limit,
            memory_request=request.memory_request,
            memory_limit=request.memory_limit,
            min_replicas=request.min_replicas,
            max_replicas=request.max_replicas
        )
        
        deployment_id = await model_lifecycle.deploy_to_staging(
            request.model_version_id,
            deployment_config
        )
        
        if not deployment_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deploy to staging"
            )
        
        return {
            "message": f"Model version {request.model_version_id} deployed to staging",
            "deployment_id": deployment_id,
            "environment": "staging"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying to staging: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deploying to staging: {str(e)}"
        )

@router.post("/ab-test")
async def start_ab_test(
    request: ABTestRequest,
    current_user: User = Depends(get_current_user)
):
    """Start A/B test between two model versions"""
    try:
        logger.info(f"Starting A/B test: control={request.control_version_id}, treatment={request.treatment_version_id} by user {current_user.id}")
        
        ab_test_id = await model_lifecycle.start_ab_test(
            control_version_id=request.control_version_id,
            treatment_version_id=request.treatment_version_id,
            traffic_split=request.traffic_split
        )
        
        if not ab_test_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start A/B test"
            )
        
        return {
            "message": "A/B test started successfully",
            "ab_test_id": ab_test_id,
            "control_version_id": request.control_version_id,
            "treatment_version_id": request.treatment_version_id,
            "traffic_split": request.traffic_split
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting A/B test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting A/B test: {str(e)}"
        )

@router.post("/rollback")
async def rollback_deployment(
    request: RollbackRequest,
    current_user: User = Depends(get_current_user)
):
    """Rollback a deployment"""
    try:
        logger.info(f"Rolling back deployment {request.deployment_id} by user {current_user.id}")
        
        success = await model_lifecycle.rollback_deployment(
            deployment_id=request.deployment_id,
            reason=request.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rollback deployment"
            )
        
        return {
            "message": f"Deployment {request.deployment_id} rolled back successfully",
            "reason": request.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rolling back deployment: {str(e)}"
        )

@router.get("/status/{model_id}", response_model=LifecycleStatusResponse)
async def get_lifecycle_status(
    model_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get lifecycle status for a model"""
    try:
        status = await model_lifecycle.get_lifecycle_status(model_id)
        
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No lifecycle status found for model {model_id}"
            )
        
        return LifecycleStatusResponse(
            model_id=status.model_id,
            current_stage=status.current_stage.value,
            current_version_id=status.current_version_id,
            production_version_id=status.production_version_id,
            staging_version_id=status.staging_version_id,
            training_in_progress=status.training_in_progress,
            ab_test_active=status.ab_test_active,
            canary_deployment_active=status.canary_deployment_active,
            last_retrain=status.last_retrain,
            next_scheduled_retrain=status.next_scheduled_retrain,
            last_deployment=status.last_deployment,
            health_score=status.health_score,
            performance_trend=status.performance_trend,
            recommendations=status.recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lifecycle status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting lifecycle status: {str(e)}"
        )

@router.get("/events/{model_id}")
async def get_lifecycle_events(
    model_id: int,
    limit: int = Query(50, ge=1, le=200, description="Number of events to retrieve"),
    current_user: User = Depends(get_current_user)
):
    """Get lifecycle event history for a model"""
    try:
        events = await model_lifecycle.get_lifecycle_events(model_id, limit)
        
        event_responses = []
        for event in events:
            event_responses.append(LifecycleEventResponse(
                model_id=event.model_id,
                event_type=event.event_type.value,
                timestamp=event.timestamp,
                stage_from=event.stage_from.value if event.stage_from else None,
                stage_to=event.stage_to.value if event.stage_to else None,
                model_version_id=event.model_version_id,
                deployment_id=event.deployment_id,
                success=event.success,
                error_message=event.error_message,
                metadata=event.metadata
            ))
        
        return {
            "model_id": model_id,
            "events": event_responses,
            "total_events": len(event_responses),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting lifecycle events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting lifecycle events: {str(e)}"
        )

@router.get("/config/{model_id}", response_model=LifecycleConfigResponse)
async def get_lifecycle_config(
    model_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get lifecycle configuration for a model"""
    try:
        config = model_lifecycle.lifecycle_configs.get(model_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No lifecycle configuration found for model {model_id}"
            )
        
        return LifecycleConfigResponse(**config.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lifecycle config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting lifecycle config: {str(e)}"
        )

@router.put("/config/{model_id}", response_model=LifecycleConfigResponse)
async def update_lifecycle_config(
    model_id: int,
    request: LifecycleConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Update lifecycle configuration for a model"""
    try:
        logger.info(f"Updating lifecycle config for model {model_id} by user {current_user.id}")
        
        # Convert request to config object
        config = LifecycleConfig(
            model_id=model_id,
            retrain_schedule=request.retrain_schedule,
            enable_auto_retrain=request.enable_auto_retrain,
            min_retrain_interval_hours=request.min_retrain_interval_hours,
            validation_threshold=request.validation_threshold,
            performance_improvement_threshold=request.performance_improvement_threshold,
            max_performance_degradation=request.max_performance_degradation,
            ab_test_duration_hours=request.ab_test_duration_hours,
            ab_test_traffic_split=request.ab_test_traffic_split,
            ab_test_min_samples=request.ab_test_min_samples,
            canary_percentage=request.canary_percentage,
            canary_duration_hours=request.canary_duration_hours,
            full_rollout_threshold=request.full_rollout_threshold,
            enable_auto_rollback=request.enable_auto_rollback,
            rollback_error_rate_threshold=request.rollback_error_rate_threshold,
            rollback_latency_threshold_ms=request.rollback_latency_threshold_ms,
            min_training_samples=request.min_training_samples,
            max_data_age_days=request.max_data_age_days,
            enable_notifications=request.enable_notifications,
            notification_channels=request.notification_channels
        )
        
        # Update configuration
        model_lifecycle.lifecycle_configs[model_id] = config
        
        return LifecycleConfigResponse(**config.__dict__)
        
    except Exception as e:
        logger.error(f"Error updating lifecycle config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating lifecycle config: {str(e)}"
        )

@router.delete("/config/{model_id}")
async def remove_lifecycle(
    model_id: int,
    current_user: User = Depends(get_current_user)
):
    """Remove lifecycle management for a model"""
    try:
        logger.info(f"Removing lifecycle management for model {model_id} by user {current_user.id}")
        
        # Remove from configurations
        if model_id in model_lifecycle.lifecycle_configs:
            del model_lifecycle.lifecycle_configs[model_id]
        
        # Remove from statuses
        if model_id in model_lifecycle.lifecycle_statuses:
            del model_lifecycle.lifecycle_statuses[model_id]
        
        # Keep event history for audit trail
        
        return {
            "message": f"Lifecycle management removed for model {model_id}"
        }
        
    except Exception as e:
        logger.error(f"Error removing lifecycle: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing lifecycle: {str(e)}"
        )

@router.get("/models")
async def list_managed_models(
    current_user: User = Depends(get_current_user)
):
    """List all models under lifecycle management"""
    try:
        models = []
        
        for model_id, config in model_lifecycle.lifecycle_configs.items():
            status = await model_lifecycle.get_lifecycle_status(model_id)
            models.append({
                "model_id": model_id,
                "current_stage": status.current_stage.value if status else "unknown",
                "health_score": status.health_score if status else 0.0,
                "training_in_progress": status.training_in_progress if status else False,
                "ab_test_active": status.ab_test_active if status else False,
                "auto_retrain_enabled": config.enable_auto_retrain,
                "auto_rollback_enabled": config.enable_auto_rollback
            })
        
        return {
            "models": sorted(models, key=lambda x: x["health_score"], reverse=True),
            "total_models": len(models),
            "models_with_auto_retrain": len([m for m in models if m["auto_retrain_enabled"]]),
            "models_with_auto_rollback": len([m for m in models if m["auto_rollback_enabled"]])
        }
        
    except Exception as e:
        logger.error(f"Error listing managed models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing managed models: {str(e)}"
        )

@router.get("/health")
async def lifecycle_service_health():
    """Check lifecycle service health"""
    try:
        return {
            "status": "healthy" if model_lifecycle._lifecycle_active else "inactive",
            "service": "model-lifecycle-service",
            "managed_models": len(model_lifecycle.lifecycle_configs),
            "background_tasks_active": len(model_lifecycle._background_tasks),
            "scheduled_tasks_active": len(model_lifecycle._scheduled_tasks),
            "models_in_training": len([
                s for s in model_lifecycle.lifecycle_statuses.values()
                if s.training_in_progress
            ]),
            "active_ab_tests": len([
                s for s in model_lifecycle.lifecycle_statuses.values()
                if s.ab_test_active
            ])
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }