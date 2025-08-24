"""
Model Monitoring API Endpoints - Monitor model performance, drift, and health
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from pydantic import BaseModel, Field, validator
import pandas as pd
import io

from app.services.model_monitor import (
    model_monitor,
    ModelHealthStatus,
    DataDriftAlert,
    PerformanceDegradationAlert,
    MonitoringConfig
)
from app.core.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/monitoring", tags=["Model Monitoring"])

# Request/Response Models

class MonitoringConfigRequest(BaseModel):
    performance_thresholds: Optional[Dict[str, float]] = Field(None, description="Performance degradation thresholds")
    drift_thresholds: Optional[Dict[str, float]] = Field(None, description="Data drift detection thresholds")
    alert_settings: Optional[Dict[str, Any]] = Field(None, description="Alert configuration settings")
    business_thresholds: Optional[Dict[str, float]] = Field(None, description="Business metrics thresholds")

class MonitoringSetupRequest(BaseModel):
    deployment_id: int = Field(..., description="Model deployment ID")
    performance_baseline: Dict[str, float] = Field(..., description="Baseline performance metrics")
    config: Optional[MonitoringConfigRequest] = Field(None, description="Monitoring configuration")

class DataDriftCheckRequest(BaseModel):
    deployment_id: int = Field(..., description="Model deployment ID")
    feature_columns: List[str] = Field(..., description="Feature columns to check for drift")

class PerformanceCheckRequest(BaseModel):
    deployment_id: int = Field(..., description="Model deployment ID")
    current_metrics: Dict[str, float] = Field(..., description="Current performance metrics")

# Response Models

class DataDriftAlertResponse(BaseModel):
    deployment_id: int
    feature_name: str
    drift_score: float
    threshold: float
    detection_method: str
    timestamp: float
    severity: str
    description: str

class PerformanceDegradationAlertResponse(BaseModel):
    deployment_id: int
    metric_name: str
    current_value: float
    expected_value: float
    degradation_percentage: float
    threshold: float
    timestamp: float
    severity: str
    description: str

class ModelHealthStatusResponse(BaseModel):
    deployment_id: int
    health_score: float
    status: str
    performance_metrics: Dict[str, float]
    drift_metrics: Dict[str, float]
    business_metrics: Dict[str, float]
    alerts_count: int
    last_updated: float
    recommendations: List[str]

class AlertHistoryResponse(BaseModel):
    alerts: List[Dict[str, Any]]  # Mixed alert types
    total_count: int
    drift_alerts: int
    performance_alerts: int

class MonitoringStatusResponse(BaseModel):
    monitoring_active: bool
    monitored_deployments: int
    total_alerts_24h: int
    healthy_deployments: int
    warning_deployments: int
    critical_deployments: int

# Initialize monitoring service on startup
@router.on_event("startup")
async def startup_event():
    try:
        await model_monitor.initialize()
        logger.info("Model monitoring service started successfully")
    except Exception as e:
        logger.error(f"Failed to start model monitoring service: {e}")

@router.on_event("shutdown")
async def shutdown_event():
    try:
        await model_monitor.cleanup()
        logger.info("Model monitoring service stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping model monitoring service: {e}")

# API Endpoints

@router.post("/setup")
async def setup_monitoring(
    request: MonitoringSetupRequest,
    reference_data_file: UploadFile = File(..., description="Reference dataset CSV file"),
    current_user: User = Depends(get_current_user)
):
    """Setup monitoring for a model deployment"""
    try:
        logger.info(f"Setting up monitoring for deployment {request.deployment_id} by user {current_user.id}")
        
        # Read reference data from uploaded file
        content = await reference_data_file.read()
        reference_data = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        if reference_data.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reference data file is empty"
            )
        
        # Convert request config if provided
        config = None
        if request.config:
            config = MonitoringConfig(
                deployment_id=request.deployment_id,
                performance_thresholds=request.config.performance_thresholds or {},
                drift_thresholds=request.config.drift_thresholds or {},
                alert_settings=request.config.alert_settings or {},
                business_thresholds=request.config.business_thresholds or {}
            )
        
        # Setup monitoring
        success = await model_monitor.setup_monitoring(
            deployment_id=request.deployment_id,
            reference_data=reference_data,
            performance_baseline=request.performance_baseline,
            config=config
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to setup monitoring"
            )
        
        return {
            "message": f"Monitoring setup completed for deployment {request.deployment_id}",
            "reference_data_rows": len(reference_data),
            "reference_data_columns": list(reference_data.columns),
            "baseline_metrics": request.performance_baseline
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up monitoring: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up monitoring: {str(e)}"
        )

@router.post("/drift/check")
async def check_data_drift(
    request: DataDriftCheckRequest,
    current_data_file: UploadFile = File(..., description="Current dataset CSV file"),
    current_user: User = Depends(get_current_user)
):
    """Check for data drift in current data"""
    try:
        logger.info(f"Checking data drift for deployment {request.deployment_id} by user {current_user.id}")
        
        # Read current data from uploaded file
        content = await current_data_file.read()
        current_data = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        if current_data.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current data file is empty"
            )
        
        # Check data drift
        alerts = await model_monitor.check_data_drift(
            deployment_id=request.deployment_id,
            current_data=current_data,
            feature_columns=request.feature_columns
        )
        
        # Convert alerts to response format
        alert_responses = []
        for alert in alerts:
            alert_responses.append(DataDriftAlertResponse(
                deployment_id=alert.deployment_id,
                feature_name=alert.feature_name,
                drift_score=alert.drift_score,
                threshold=alert.threshold,
                detection_method=alert.detection_method,
                timestamp=alert.timestamp,
                severity=alert.severity,
                description=alert.description
            ))
            
            # Add alert to monitoring system
            await model_monitor.add_alert(alert)
        
        return {
            "deployment_id": request.deployment_id,
            "features_checked": len(request.feature_columns),
            "drift_alerts": alert_responses,
            "total_alerts": len(alert_responses),
            "has_drift": len(alert_responses) > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking data drift: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking data drift: {str(e)}"
        )

@router.post("/performance/check")
async def check_performance_degradation(
    request: PerformanceCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """Check for performance degradation"""
    try:
        logger.info(f"Checking performance degradation for deployment {request.deployment_id} by user {current_user.id}")
        
        # Check performance degradation
        alerts = await model_monitor.check_performance_degradation(
            deployment_id=request.deployment_id,
            current_metrics=request.current_metrics
        )
        
        # Convert alerts to response format
        alert_responses = []
        for alert in alerts:
            alert_responses.append(PerformanceDegradationAlertResponse(
                deployment_id=alert.deployment_id,
                metric_name=alert.metric_name,
                current_value=alert.current_value,
                expected_value=alert.expected_value,
                degradation_percentage=alert.degradation_percentage,
                threshold=alert.threshold,
                timestamp=alert.timestamp,
                severity=alert.severity,
                description=alert.description
            ))
            
            # Add alert to monitoring system
            await model_monitor.add_alert(alert)
        
        return {
            "deployment_id": request.deployment_id,
            "metrics_checked": len(request.current_metrics),
            "performance_alerts": alert_responses,
            "total_alerts": len(alert_responses),
            "has_degradation": len(alert_responses) > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking performance degradation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking performance degradation: {str(e)}"
        )

@router.get("/health/{deployment_id}", response_model=ModelHealthStatusResponse)
async def get_model_health(
    deployment_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get model health status"""
    try:
        health_status = await model_monitor.get_health_status(deployment_id)
        
        if not health_status:
            # Try to update health status if not found
            health_status = await model_monitor.update_health_status(deployment_id)
        
        if not health_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No health status found for deployment {deployment_id}"
            )
        
        return ModelHealthStatusResponse(
            deployment_id=health_status.deployment_id,
            health_score=health_status.health_score,
            status=health_status.status,
            performance_metrics=health_status.performance_metrics,
            drift_metrics=health_status.drift_metrics,
            business_metrics=health_status.business_metrics,
            alerts_count=len(health_status.alerts),
            last_updated=health_status.last_updated,
            recommendations=health_status.recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting model health: {str(e)}"
        )

@router.get("/health-statuses", response_model=List[ModelHealthStatus])
async def get_all_health_statuses(current_user: User = Depends(get_current_user)):
    """
    Get the health status of all monitored models.
    """
    try:
        return await model_monitor.get_all_health_statuses()
    except Exception as e:
        logger.error(f"Error getting all health statuses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting all health statuses: {str(e)}"
        )

@router.post("/health/{deployment_id}/update", response_model=ModelHealthStatusResponse)
async def update_model_health(
    deployment_id: int,
    current_user: User = Depends(get_current_user)
):
    """Force update model health status"""
    try:
        logger.info(f"Updating health status for deployment {deployment_id} by user {current_user.id}")
        
        health_status = await model_monitor.update_health_status(deployment_id)
        
        return ModelHealthStatusResponse(
            deployment_id=health_status.deployment_id,
            health_score=health_status.health_score,
            status=health_status.status,
            performance_metrics=health_status.performance_metrics,
            drift_metrics=health_status.drift_metrics,
            business_metrics=health_status.business_metrics,
            alerts_count=len(health_status.alerts),
            last_updated=health_status.last_updated,
            recommendations=health_status.recommendations
        )
        
    except Exception as e:
        logger.error(f"Error updating model health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating model health: {str(e)}"
        )

@router.get("/alerts/{deployment_id}", response_model=AlertHistoryResponse)
async def get_alert_history(
    deployment_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type (drift, performance)"),
    current_user: User = Depends(get_current_user)
):
    """Get alert history for a deployment"""
    try:
        alerts = await model_monitor.get_alert_history(deployment_id, hours, alert_type)
        
        # Convert alerts to dict format
        alert_dicts = []
        drift_count = 0
        performance_count = 0
        
        for alert in alerts:
            alert_dict = alert.__dict__.copy()
            alert_dict["alert_type"] = "drift" if isinstance(alert, DataDriftAlert) else "performance"
            alert_dicts.append(alert_dict)
            
            if isinstance(alert, DataDriftAlert):
                drift_count += 1
            else:
                performance_count += 1
        
        return AlertHistoryResponse(
            alerts=alert_dicts,
            total_count=len(alerts),
            drift_alerts=drift_count,
            performance_alerts=performance_count
        )
        
    except Exception as e:
        logger.error(f"Error getting alert history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting alert history: {str(e)}"
        )

@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status(
    current_user: User = Depends(get_current_user)
):
    """Get overall monitoring service status"""
    try:
        # Get health statuses for all deployments
        healthy_count = 0
        warning_count = 0
        critical_count = 0
        total_alerts_24h = 0
        
        for deployment_id in model_monitor.monitoring_configs.keys():
            health_status = await model_monitor.get_health_status(deployment_id)
            if health_status:
                if health_status.status == "healthy":
                    healthy_count += 1
                elif health_status.status == "warning":
                    warning_count += 1
                elif health_status.status == "critical":
                    critical_count += 1
                
                # Count recent alerts
                alerts = await model_monitor.get_alert_history(deployment_id, hours=24)
                total_alerts_24h += len(alerts)
        
        return MonitoringStatusResponse(
            monitoring_active=model_monitor._monitoring_active,
            monitored_deployments=len(model_monitor.monitoring_configs),
            total_alerts_24h=total_alerts_24h,
            healthy_deployments=healthy_count,
            warning_deployments=warning_count,
            critical_deployments=critical_count
        )
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting monitoring status: {str(e)}"
        )

@router.get("/deployments")
async def list_monitored_deployments(
    status_filter: Optional[str] = Query(None, description="Filter by health status"),
    current_user: User = Depends(get_current_user)
):
    """List all monitored deployments"""
    try:
        deployments = []
        
        for deployment_id in model_monitor.monitoring_configs.keys():
            health_status = await model_monitor.get_health_status(deployment_id)
            if health_status and (not status_filter or health_status.status == status_filter):
                deployments.append({
                    "deployment_id": deployment_id,
                    "health_score": health_status.health_score,
                    "status": health_status.status,
                    "alerts_count": len(health_status.alerts),
                    "last_updated": health_status.last_updated
                })
        
        return {
            "deployments": sorted(deployments, key=lambda x: x["health_score"], reverse=True),
            "total_count": len(deployments),
            "filtered_by": status_filter
        }
        
    except Exception as e:
        logger.error(f"Error listing monitored deployments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing monitored deployments: {str(e)}"
        )

@router.delete("/setup/{deployment_id}")
async def remove_monitoring(
    deployment_id: int,
    current_user: User = Depends(get_current_user)
):
    """Remove monitoring for a deployment"""
    try:
        logger.info(f"Removing monitoring for deployment {deployment_id} by user {current_user.id}")
        
        # Remove from monitoring configs
        if deployment_id in model_monitor.monitoring_configs:
            del model_monitor.monitoring_configs[deployment_id]
        
        # Remove health status
        if deployment_id in model_monitor.health_statuses:
            del model_monitor.health_statuses[deployment_id]
        
        # Remove alert history
        if deployment_id in model_monitor.alert_history:
            del model_monitor.alert_history[deployment_id]
        
        # Remove reference data
        if deployment_id in model_monitor.reference_data:
            del model_monitor.reference_data[deployment_id]
        
        # Remove performance baselines
        if deployment_id in model_monitor.performance_baselines:
            del model_monitor.performance_baselines[deployment_id]
        
        return {
            "message": f"Monitoring removed for deployment {deployment_id}"
        }
        
    except Exception as e:
        logger.error(f"Error removing monitoring: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing monitoring: {str(e)}"
        )

@router.get("/health")
async def monitoring_service_health():
    """Check monitoring service health"""
    try:
        health_info = {
            "status": "healthy" if model_monitor._monitoring_active else "inactive",
            "service": "model-monitoring-service",
            "redis_connected": model_monitor.redis_client is not None,
            "background_tasks_active": len(model_monitor._background_tasks),
            "monitored_deployments": len(model_monitor.monitoring_configs),
            "total_health_statuses": len(model_monitor.health_statuses),
            "total_alert_history_entries": sum(len(alerts) for alerts in model_monitor.alert_history.values())
        }
        
        # Test Redis connection if available
        if model_monitor.redis_client:
            try:
                await model_monitor.redis_client.ping()
                health_info["redis_ping"] = "ok"
            except Exception as e:
                health_info["redis_ping"] = f"error: {str(e)}"
                health_info["status"] = "degraded"
        
        return health_info
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/config/{deployment_id}")
async def update_monitoring_config(
    deployment_id: int,
    config: MonitoringConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Update monitoring configuration for a deployment"""
    try:
        logger.info(f"Updating monitoring config for deployment {deployment_id} by user {current_user.id}")
        
        # Get existing config or create new one
        existing_config = model_monitor.monitoring_configs.get(
            deployment_id,
            MonitoringConfig(deployment_id=deployment_id)
        )
        
        # Update config fields if provided
        if config.performance_thresholds:
            existing_config.performance_thresholds.update(config.performance_thresholds)
        
        if config.drift_thresholds:
            existing_config.drift_thresholds.update(config.drift_thresholds)
        
        if config.alert_settings:
            existing_config.alert_settings.update(config.alert_settings)
        
        if config.business_thresholds:
            existing_config.business_thresholds.update(config.business_thresholds)
        
        # Save updated config
        model_monitor.monitoring_configs[deployment_id] = existing_config
        
        # Save to cache if available
        if model_monitor.redis_client:
            await model_monitor._save_config_to_cache(deployment_id, existing_config)
        
        return {
            "message": f"Monitoring configuration updated for deployment {deployment_id}",
            "config": {
                "performance_thresholds": existing_config.performance_thresholds,
                "drift_thresholds": existing_config.drift_thresholds,
                "alert_settings": existing_config.alert_settings,
                "business_thresholds": existing_config.business_thresholds
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating monitoring config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating monitoring config: {str(e)}"
        )

@router.get("/config/{deployment_id}")
async def get_monitoring_config(
    deployment_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get monitoring configuration for a deployment"""
    try:
        config = model_monitor.monitoring_configs.get(deployment_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No monitoring configuration found for deployment {deployment_id}"
            )
        
        return {
            "deployment_id": config.deployment_id,
            "performance_thresholds": config.performance_thresholds,
            "drift_thresholds": config.drift_thresholds,
            "alert_settings": config.alert_settings,
            "business_thresholds": config.business_thresholds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monitoring config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting monitoring config: {str(e)}"
        )