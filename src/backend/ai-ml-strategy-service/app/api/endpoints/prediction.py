"""
Prediction API Endpoints - Real-time model prediction service
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator
import asyncio

from app.services.prediction_service import (
    prediction_service,
    PredictionRequest,
    PredictionResponse,
    ModelMetrics
)
from app.core.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predictions", tags=["Real-time Predictions"])

# Request/Response Models

class PredictionRequestModel(BaseModel):
    model_deployment_id: int = Field(..., description="Model deployment ID")
    features: Dict[str, Any] = Field(..., description="Feature values for prediction")
    priority: int = Field(1, ge=1, le=3, description="Request priority (1=high, 2=normal, 3=low)")
    use_cache: bool = Field(True, description="Use cached results if available")
    timeout: float = Field(30.0, ge=1.0, le=300.0, description="Request timeout in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class BatchPredictionRequestModel(BaseModel):
    requests: List[PredictionRequestModel] = Field(..., min_items=1, max_items=100, description="Batch of prediction requests")
    max_concurrent: int = Field(10, ge=1, le=50, description="Maximum concurrent predictions")

class PredictionResponseModel(BaseModel):
    request_id: str
    prediction: Optional[Any] = None
    confidence: Optional[float] = None
    probability: Optional[float] = None
    prediction_time: Optional[float] = None
    processing_time_ms: Optional[float] = None
    model_version: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BatchPredictionResponseModel(BaseModel):
    responses: List[PredictionResponseModel]
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_processing_time_ms: float

class ModelMetricsResponse(BaseModel):
    deployment_id: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    last_prediction_time: Optional[float] = None

class AllMetricsResponse(BaseModel):
    metrics: Dict[int, ModelMetricsResponse]
    timestamp: float

# Initialize prediction service on startup
@router.on_event("startup")
async def startup_event():
    try:
        await prediction_service.initialize()
        logger.info("Prediction service started successfully")
    except Exception as e:
        logger.error(f"Failed to start prediction service: {e}")

@router.on_event("shutdown") 
async def shutdown_event():
    try:
        await prediction_service.cleanup()
        logger.info("Prediction service stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping prediction service: {e}")

# API Endpoints

@router.post("/predict", response_model=PredictionResponseModel)
async def make_prediction(
    request: PredictionRequestModel,
    current_user: User = Depends(get_current_user)
):
    """Make a single prediction"""
    try:
        logger.info(f"Prediction request for deployment {request.model_deployment_id} by user {current_user.id}")
        
        # Convert to internal request format
        pred_request = PredictionRequest(
            model_deployment_id=request.model_deployment_id,
            features=request.features,
            priority=request.priority,
            metadata=request.metadata
        )
        
        # Make prediction
        response = await prediction_service.predict(
            pred_request,
            use_cache=request.use_cache,
            timeout=request.timeout
        )
        
        return PredictionResponseModel(
            request_id=response.request_id,
            prediction=response.prediction,
            confidence=response.confidence,
            probability=response.probability,
            prediction_time=response.prediction_time,
            processing_time_ms=response.processing_time_ms,
            model_version=response.model_version,
            error=response.error,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )

@router.post("/predict/batch", response_model=BatchPredictionResponseModel)
async def make_batch_prediction(
    request: BatchPredictionRequestModel,
    current_user: User = Depends(get_current_user)
):
    """Make batch predictions with concurrency control"""
    try:
        logger.info(f"Batch prediction request for {len(request.requests)} items by user {current_user.id}")
        
        # Convert to internal request format
        pred_requests = []
        for req in request.requests:
            pred_req = PredictionRequest(
                model_deployment_id=req.model_deployment_id,
                features=req.features,
                priority=req.priority,
                metadata=req.metadata
            )
            pred_requests.append(pred_req)
        
        # Make batch predictions
        start_time = asyncio.get_event_loop().time()
        responses = await prediction_service.predict_batch(
            pred_requests,
            max_concurrent=request.max_concurrent
        )
        total_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Convert responses
        response_models = []
        successful_count = 0
        failed_count = 0
        
        for response in responses:
            response_model = PredictionResponseModel(
                request_id=response.request_id,
                prediction=response.prediction,
                confidence=response.confidence,
                probability=response.probability,
                prediction_time=response.prediction_time,
                processing_time_ms=response.processing_time_ms,
                model_version=response.model_version,
                error=response.error,
                metadata=response.metadata
            )
            response_models.append(response_model)
            
            if response.error:
                failed_count += 1
            else:
                successful_count += 1
        
        return BatchPredictionResponseModel(
            responses=response_models,
            total_requests=len(request.requests),
            successful_requests=successful_count,
            failed_requests=failed_count,
            total_processing_time_ms=total_time_ms
        )
        
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction error: {str(e)}"
        )

@router.post("/predict/async")
async def enqueue_prediction(
    request: PredictionRequestModel,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Enqueue prediction for background processing"""
    try:
        logger.info(f"Async prediction request for deployment {request.model_deployment_id} by user {current_user.id}")
        
        # Convert to internal request format
        pred_request = PredictionRequest(
            model_deployment_id=request.model_deployment_id,
            features=request.features,
            priority=request.priority,
            metadata=request.metadata
        )
        
        # Enqueue prediction
        success = await prediction_service.enqueue_prediction(pred_request)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Prediction queue is full. Please try again later."
            )
        
        return {
            "request_id": pred_request.request_id,
            "status": "queued",
            "message": "Prediction request queued for background processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Async prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Async prediction error: {str(e)}"
        )

@router.get("/metrics/{deployment_id}", response_model=ModelMetricsResponse)
async def get_model_metrics(
    deployment_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for a specific model deployment"""
    try:
        metrics = await prediction_service.get_model_metrics(deployment_id)
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No metrics found for deployment {deployment_id}"
            )
        
        return ModelMetricsResponse(
            deployment_id=deployment_id,
            total_requests=metrics.total_requests,
            successful_requests=metrics.successful_requests,
            failed_requests=metrics.failed_requests,
            avg_latency_ms=metrics.avg_latency_ms,
            p95_latency_ms=metrics.p95_latency_ms,
            p99_latency_ms=metrics.p99_latency_ms,
            error_rate=metrics.error_rate,
            last_prediction_time=metrics.last_prediction_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting model metrics: {str(e)}"
        )

@router.get("/metrics", response_model=AllMetricsResponse)
async def get_all_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for all model deployments"""
    try:
        all_metrics = await prediction_service.get_all_metrics()
        
        metrics_responses = {}
        for deployment_id, metrics in all_metrics.items():
            metrics_responses[deployment_id] = ModelMetricsResponse(
                deployment_id=deployment_id,
                total_requests=metrics.total_requests,
                successful_requests=metrics.successful_requests,
                failed_requests=metrics.failed_requests,
                avg_latency_ms=metrics.avg_latency_ms,
                p95_latency_ms=metrics.p95_latency_ms,
                p99_latency_ms=metrics.p99_latency_ms,
                error_rate=metrics.error_rate,
                last_prediction_time=metrics.last_prediction_time
            )
        
        return AllMetricsResponse(
            metrics=metrics_responses,
            timestamp=asyncio.get_event_loop().time()
        )
        
    except Exception as e:
        logger.error(f"Error getting all metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting all metrics: {str(e)}"
        )

@router.delete("/cache/{deployment_id}")
async def clear_model_cache(
    deployment_id: int,
    current_user: User = Depends(get_current_user)
):
    """Clear cache for specific model deployment"""
    try:
        await prediction_service.clear_cache(deployment_id)
        
        logger.info(f"Cleared cache for deployment {deployment_id} by user {current_user.id}")
        return {"message": f"Cache cleared for deployment {deployment_id}"}
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache: {str(e)}"
        )

@router.delete("/cache")
async def clear_all_cache(
    current_user: User = Depends(get_current_user)
):
    """Clear all prediction cache"""
    try:
        await prediction_service.clear_cache()
        
        logger.info(f"Cleared all prediction cache by user {current_user.id}")
        return {"message": "All prediction cache cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing all cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing all cache: {str(e)}"
        )

@router.get("/health")
async def prediction_service_health():
    """Check prediction service health"""
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "service": "prediction-service",
            "redis_connected": prediction_service.redis_client is not None,
            "http_session_active": prediction_service.http_session is not None,
            "background_tasks_active": len(prediction_service._background_tasks),
            "queue_size": prediction_service.prediction_queue.qsize(),
            "active_deployments": len(prediction_service.metrics)
        }
        
        # Test Redis connection if available
        if prediction_service.redis_client:
            try:
                await prediction_service.redis_client.ping()
                health_status["redis_ping"] = "ok"
            except Exception as e:
                health_status["redis_ping"] = f"error: {str(e)}"
                health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/status/{deployment_id}")
async def get_deployment_prediction_status(
    deployment_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get prediction service status for specific deployment"""
    try:
        metrics = await prediction_service.get_model_metrics(deployment_id)
        
        circuit_breaker = prediction_service.circuit_breakers.get(deployment_id, {
            "state": "closed",
            "failure_count": 0
        })
        
        return {
            "deployment_id": deployment_id,
            "prediction_service_available": True,
            "circuit_breaker_state": circuit_breaker["state"],
            "recent_failure_count": circuit_breaker["failure_count"],
            "total_requests": metrics.total_requests if metrics else 0,
            "error_rate": metrics.error_rate if metrics else 0.0,
            "avg_latency_ms": metrics.avg_latency_ms if metrics else 0.0,
            "last_prediction_time": metrics.last_prediction_time if metrics else None
        }
        
    except Exception as e:
        logger.error(f"Error getting deployment status: {str(e)}")
        return {
            "deployment_id": deployment_id,
            "prediction_service_available": False,
            "error": str(e)
        }

# Stream prediction results (WebSocket would be better, but using SSE for now)
@router.get("/stream/{deployment_id}")
async def stream_predictions(
    deployment_id: int,
    current_user: User = Depends(get_current_user)
):
    """Stream prediction results (placeholder for WebSocket implementation)"""
    try:
        # This would be implemented with WebSockets for real-time streaming
        # For now, just return current metrics
        metrics = await prediction_service.get_model_metrics(deployment_id)
        
        return {
            "deployment_id": deployment_id,
            "streaming": False,
            "message": "WebSocket streaming not implemented yet",
            "current_metrics": {
                "total_requests": metrics.total_requests if metrics else 0,
                "avg_latency_ms": metrics.avg_latency_ms if metrics else 0.0,
                "error_rate": metrics.error_rate if metrics else 0.0
            }
        }
        
    except Exception as e:
        logger.error(f"Error in stream endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming error: {str(e)}"
        )