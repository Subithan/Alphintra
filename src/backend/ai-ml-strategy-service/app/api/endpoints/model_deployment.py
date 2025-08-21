"""
Model Deployment API Endpoints - Deploy and manage ML models on Kubernetes
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status, Query
from pydantic import BaseModel, Field, validator
from datetime import datetime

from app.services.k8s_deployment import (
    k8s_deployment_service, 
    DeploymentConfig, 
    DeploymentResult
)
from app.models.model_registry import (
    Model, ModelVersion, ModelDeployment, DeploymentStatus
)
from app.core.auth import get_current_user
from app.models.user import User
from app.core.database import get_db_session
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/deployments", tags=["Model Deployment"])

# Request/Response Models

class ModelDeploymentRequest(BaseModel):
    model_version_id: int = Field(..., description="Model version ID to deploy")
    deployment_name: str = Field(..., min_length=3, max_length=50, description="Deployment name")
    environment: str = Field(..., description="Environment (dev, staging, prod)")
    
    # Resource configuration
    cpu_request: str = Field("500m", description="CPU request (e.g., 500m)")
    cpu_limit: str = Field("2000m", description="CPU limit (e.g., 2000m)")
    memory_request: str = Field("1Gi", description="Memory request (e.g., 1Gi)")
    memory_limit: str = Field("4Gi", description="Memory limit (e.g., 4Gi)")
    gpu_request: int = Field(0, ge=0, le=8, description="GPU request (0-8)")
    
    # Scaling configuration
    min_replicas: int = Field(1, ge=1, le=20, description="Minimum replicas")
    max_replicas: int = Field(10, ge=1, le=100, description="Maximum replicas")
    target_cpu_utilization: int = Field(70, ge=10, le=95, description="Target CPU utilization %")
    target_rps: Optional[int] = Field(None, ge=1, description="Target requests per second")
    
    # Serving configuration
    serving_framework: str = Field("fastapi", description="Serving framework")
    api_version: str = Field("v1", description="API version")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Custom configuration")
    
    @validator('deployment_name')
    def validate_deployment_name(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError("Deployment name must contain only lowercase letters, numbers, and hyphens")
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['dev', 'staging', 'prod']
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v

class DeploymentScaleRequest(BaseModel):
    min_replicas: int = Field(..., ge=1, le=20, description="Minimum replicas")
    max_replicas: int = Field(..., ge=1, le=100, description="Maximum replicas")
    
    @validator('max_replicas')
    def validate_scale(cls, v, values):
        if 'min_replicas' in values and v < values['min_replicas']:
            raise ValueError("max_replicas must be >= min_replicas")
        return v

class DeploymentUpdateRequest(BaseModel):
    new_model_version_id: int = Field(..., description="New model version ID")
    strategy: str = Field("rolling", description="Update strategy")
    
    @validator('strategy')
    def validate_strategy(cls, v):
        valid_strategies = ['rolling', 'recreate', 'blue_green']
        if v not in valid_strategies:
            raise ValueError(f"Strategy must be one of: {valid_strategies}")
        return v

# Response Models

class DeploymentResponse(BaseModel):
    id: int
    uuid: str
    model_id: int
    model_version_id: int
    deployment_name: str
    environment: str
    endpoint_url: Optional[str]
    api_version: str
    serving_framework: str
    status: str
    deployment_status_message: Optional[str]
    
    # Resource configuration
    cpu_request: str
    cpu_limit: str
    memory_request: str
    memory_limit: str
    gpu_request: int
    min_replicas: int
    max_replicas: int
    target_cpu_utilization: int
    
    # Status and timing
    is_active: bool
    deployed_at: Optional[str]
    last_updated: Optional[str]
    created_at: str
    
    # Health metrics
    health_metrics: Optional[Dict[str, Any]]
    traffic_percentage: int

class DeploymentListResponse(BaseModel):
    deployments: List[DeploymentResponse]
    total: int
    limit: int
    offset: int

class DeploymentStatusResponse(BaseModel):
    deployment_id: int
    status: str
    endpoint_url: Optional[str]
    replicas: Dict[str, int]
    pods: List[Dict[str, Any]]
    service: Dict[str, Any]
    last_updated: Optional[str]
    error: Optional[str] = None

# API Endpoints

@router.post("/", response_model=DeploymentResponse)
async def create_deployment(
    request: ModelDeploymentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Deploy a model version to Kubernetes"""
    try:
        logger.info(f"Creating deployment {request.deployment_name} for user {current_user.id}")
        
        # Verify model version exists and is deployment ready
        model_version = db.query(ModelVersion).get(request.model_version_id)
        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version {request.model_version_id} not found"
            )
        
        if not model_version.deployment_ready:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model version {request.model_version_id} is not ready for deployment"
            )
        
        # Check if deployment name already exists
        existing = db.query(ModelDeployment).filter(
            ModelDeployment.deployment_name == request.deployment_name,
            ModelDeployment.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Deployment '{request.deployment_name}' already exists"
            )
        
        # Create deployment configuration
        config = DeploymentConfig(
            model_version_id=request.model_version_id,
            deployment_name=request.deployment_name,
            environment=request.environment,
            cpu_request=request.cpu_request,
            cpu_limit=request.cpu_limit,
            memory_request=request.memory_request,
            memory_limit=request.memory_limit,
            gpu_request=request.gpu_request,
            min_replicas=request.min_replicas,
            max_replicas=request.max_replicas,
            target_cpu_utilization=request.target_cpu_utilization,
            target_rps=request.target_rps,
            serving_framework=request.serving_framework,
            api_version=request.api_version,
            custom_config=request.custom_config
        )
        
        # Start deployment in background
        result = await k8s_deployment_service.deploy_model(config, current_user.id, db)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deployment failed: {result.error_message}"
            )
        
        # Get the created deployment
        deployment = db.query(ModelDeployment).get(result.deployment_id)
        return DeploymentResponse(**deployment.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deployment: {str(e)}"
        )

@router.get("/", response_model=DeploymentListResponse)
async def list_deployments(
    environment: Optional[str] = Query(None, description="Filter by environment"),
    status: Optional[str] = Query(None, description="Filter by status"),
    model_id: Optional[int] = Query(None, description="Filter by model ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """List deployments with filtering options"""
    try:
        query = db.query(ModelDeployment).filter(ModelDeployment.is_active == True)
        
        if environment:
            query = query.filter(ModelDeployment.environment == environment)
        if status:
            query = query.filter(ModelDeployment.status == status)
        if model_id:
            query = query.filter(ModelDeployment.model_id == model_id)
        
        # Get total count
        total = query.count()
        
        # Get deployments
        deployments = query.order_by(ModelDeployment.created_at.desc()).offset(offset).limit(limit).all()
        
        deployment_responses = [DeploymentResponse(**d.to_dict()) for d in deployments]
        
        return DeploymentListResponse(
            deployments=deployment_responses,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to list deployments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list deployments: {str(e)}"
        )

@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get deployment by ID"""
    deployment = db.query(ModelDeployment).filter(
        ModelDeployment.id == deployment_id,
        ModelDeployment.is_active == True
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found"
        )
    
    return DeploymentResponse(**deployment.to_dict())

@router.get("/{deployment_id}/status", response_model=DeploymentStatusResponse)
async def get_deployment_status(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get detailed deployment status from Kubernetes"""
    try:
        deployment = db.query(ModelDeployment).filter(
            ModelDeployment.id == deployment_id,
            ModelDeployment.is_active == True
        ).first()
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment {deployment_id} not found"
            )
        
        # Get live status from Kubernetes
        status_info = await k8s_deployment_service.get_deployment_status(deployment_id, db)
        
        return DeploymentStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"Failed to get deployment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deployment status: {str(e)}"
        )

@router.post("/{deployment_id}/scale", response_model=DeploymentResponse)
async def scale_deployment(
    deployment_id: int,
    request: DeploymentScaleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Scale deployment replicas"""
    try:
        deployment = db.query(ModelDeployment).filter(
            ModelDeployment.id == deployment_id,
            ModelDeployment.is_active == True
        ).first()
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment {deployment_id} not found"
            )
        
        if deployment.status != DeploymentStatus.DEPLOYED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only scale deployed models"
            )
        
        # Scale deployment
        success = await k8s_deployment_service.scale_deployment(
            deployment_id, request.min_replicas, request.max_replicas, db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to scale deployment"
            )
        
        # Return updated deployment
        db.refresh(deployment)
        return DeploymentResponse(**deployment.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to scale deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scale deployment: {str(e)}"
        )

@router.post("/{deployment_id}/update", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: int,
    request: DeploymentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update deployment with new model version"""
    try:
        deployment = db.query(ModelDeployment).filter(
            ModelDeployment.id == deployment_id,
            ModelDeployment.is_active == True
        ).first()
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment {deployment_id} not found"
            )
        
        if deployment.status != DeploymentStatus.DEPLOYED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update deployed models"
            )
        
        # Verify new model version
        new_model_version = db.query(ModelVersion).get(request.new_model_version_id)
        if not new_model_version or not new_model_version.deployment_ready:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New model version not found or not deployment ready"
            )
        
        # Update deployment
        success = await k8s_deployment_service.update_deployment(
            deployment_id, request.new_model_version_id, request.strategy, db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update deployment"
            )
        
        # Return updated deployment
        db.refresh(deployment)
        return DeploymentResponse(**deployment.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update deployment: {str(e)}"
        )

@router.delete("/{deployment_id}")
async def delete_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Delete deployment and cleanup Kubernetes resources"""
    try:
        deployment = db.query(ModelDeployment).filter(
            ModelDeployment.id == deployment_id,
            ModelDeployment.is_active == True
        ).first()
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment {deployment_id} not found"
            )
        
        # Delete deployment
        success = await k8s_deployment_service.delete_deployment(deployment_id, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete deployment"
            )
        
        logger.info(f"Deleted deployment {deployment_id}")
        return {"message": f"Deployment {deployment_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete deployment: {str(e)}"
        )

@router.post("/{deployment_id}/restart")
async def restart_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Restart deployment pods"""
    try:
        deployment = db.query(ModelDeployment).filter(
            ModelDeployment.id == deployment_id,
            ModelDeployment.is_active == True
        ).first()
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment {deployment_id} not found"
            )
        
        if deployment.status != DeploymentStatus.DEPLOYED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only restart deployed models"
            )
        
        # Restart by updating deployment with current timestamp annotation
        from kubernetes import client
        k8s_apps = client.AppsV1Api()
        
        try:
            # Get current deployment
            k8s_deployment = k8s_apps.read_namespaced_deployment(
                name=deployment.k8s_deployment_name,
                namespace=k8s_deployment_service.namespace
            )
            
            # Add restart annotation
            if k8s_deployment.spec.template.metadata.annotations is None:
                k8s_deployment.spec.template.metadata.annotations = {}
            
            k8s_deployment.spec.template.metadata.annotations["kubectl.kubernetes.io/restartedAt"] = \
                datetime.utcnow().isoformat()
            
            # Update deployment
            k8s_apps.patch_namespaced_deployment(
                name=deployment.k8s_deployment_name,
                namespace=k8s_deployment_service.namespace,
                body=k8s_deployment
            )
            
            logger.info(f"Restarted deployment {deployment_id}")
            return {"message": f"Deployment {deployment_id} restart initiated"}
            
        except Exception as e:
            logger.error(f"Failed to restart deployment: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restart deployment: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restarting deployment: {str(e)}"
        )

@router.get("/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: int,
    lines: int = Query(100, ge=1, le=1000, description="Number of log lines"),
    follow: bool = Query(False, description="Follow logs (streaming)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get deployment pod logs"""
    try:
        deployment = db.query(ModelDeployment).filter(
            ModelDeployment.id == deployment_id,
            ModelDeployment.is_active == True
        ).first()
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment {deployment_id} not found"
            )
        
        from kubernetes import client
        k8s_core = client.CoreV1Api()
        
        try:
            # Get pods for deployment
            pods = k8s_core.list_namespaced_pod(
                namespace=k8s_deployment_service.namespace,
                label_selector=f"app={deployment.deployment_name}"
            )
            
            if not pods.items:
                return {"logs": "No pods found for deployment"}
            
            # Get logs from first pod (or combine from all pods)
            pod_name = pods.items[0].metadata.name
            
            logs = k8s_core.read_namespaced_pod_log(
                name=pod_name,
                namespace=k8s_deployment_service.namespace,
                tail_lines=lines,
                follow=follow
            )
            
            return {"logs": logs, "pod_name": pod_name}
            
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get logs: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deployment logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting deployment logs: {str(e)}"
        )

@router.get("/environments/list")
async def list_environments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """List available deployment environments"""
    try:
        # Get distinct environments from deployments
        environments = db.query(ModelDeployment.environment).distinct().all()
        env_list = [env[0] for env in environments if env[0]]
        
        # Add default environments if not present
        default_envs = ['dev', 'staging', 'prod']
        for env in default_envs:
            if env not in env_list:
                env_list.append(env)
        
        return {"environments": sorted(env_list)}
        
    except Exception as e:
        logger.error(f"Error listing environments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing environments: {str(e)}"
        )