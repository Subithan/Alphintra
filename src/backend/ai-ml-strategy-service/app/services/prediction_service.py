"""
Real-time Prediction Pipeline - High-performance prediction service for deployed models
"""

import asyncio
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
import redis.asyncio as redis
import aiohttp
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from app.models.model_registry import ModelDeployment, DeploymentStatus
from app.database.connection import get_db_session
from app.core.config import get_settings
from sqlalchemy.orm import Session
# from app.services.model_monitor import model_monitor, PredictionLog  # Temporarily disabled due to circular import

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class PredictionRequest:
    """Prediction request structure"""
    model_deployment_id: int
    features: Dict[str, Any]
    request_id: Optional[str] = None
    timestamp: Optional[float] = None
    priority: int = 1  # 1=high, 2=normal, 3=low
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.request_id is None:
            # Generate unique request ID
            content = f"{self.model_deployment_id}_{self.timestamp}_{json.dumps(self.features, sort_keys=True)}"
            self.request_id = hashlib.md5(content.encode()).hexdigest()[:16]


@dataclass
class PredictionResponse:
    """Prediction response structure"""
    request_id: str
    prediction: Union[float, int, List[float], Dict[str, Any]]
    confidence: Optional[float] = None
    probability: Optional[float] = None
    prediction_time: Optional[float] = None
    processing_time_ms: Optional[float] = None
    model_version: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class FeatureCacheEntry:
    """Feature cache entry structure"""
    features: Dict[str, Any]
    timestamp: float
    expiry: float
    version: str = "v1"


@dataclass
class ModelMetrics:
    """Model performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p90_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    last_prediction_time: Optional[float] = None
    error_rate: float = 0.0


class PredictionService:
    """
    High-performance real-time prediction service with caching, queuing, and monitoring
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.prediction_queue = asyncio.Queue(maxsize=10000)
        self.thread_pool = ThreadPoolExecutor(max_workers=50)
        
        # Performance tracking
        self.metrics: Dict[int, ModelMetrics] = {}  # deployment_id -> metrics
        self.latency_buffer: Dict[int, List[float]] = {}  # For calculating percentiles
        self.buffer_size = 1000
        
        # Feature cache settings
        self.feature_cache_ttl = 300  # 5 minutes default
        self.cache_prefix = "features:"
        
        # Rate limiting
        self.rate_limits: Dict[int, Dict[str, Any]] = {}  # deployment_id -> rate limit info
        
        # Circuit breaker settings
        self.circuit_breakers: Dict[int, Dict[str, Any]] = {}
        
        # Background tasks
        self._background_tasks = []
        
    async def initialize(self):
        """Initialize the prediction service"""
        try:
            # Initialize Redis connection
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    retry_on_timeout=True
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Connected to Redis for feature caching")
            
            # Initialize HTTP session
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.http_session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": "Alphintra-Prediction-Service"}
            )
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info("Prediction service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize prediction service: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Cancel background tasks
            for task in self._background_tasks:
                task.cancel()
            
            # Close HTTP session
            if self.http_session:
                await self.http_session.close()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)
            
            logger.info("Prediction service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def predict(
        self,
        request: PredictionRequest,
        use_cache: bool = True,
        timeout: float = 30.0
    ) -> PredictionResponse:
        """
        Make a prediction with caching, rate limiting, and error handling
        """
        start_time = time.time()
        
        try:
            # Check rate limits
            if not await self._check_rate_limit(request.model_deployment_id):
                return PredictionResponse(
                    request_id=request.request_id,
                    prediction=None,
                    error="Rate limit exceeded",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check circuit breaker
            if not await self._check_circuit_breaker(request.model_deployment_id):
                return PredictionResponse(
                    request_id=request.request_id,
                    prediction=None,
                    error="Circuit breaker open - service unavailable",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check cache first
            if use_cache:
                cached_result = await self._get_cached_prediction(request)
                if cached_result:
                    logger.debug(f"Cache hit for request {request.request_id}")
                    cached_result.processing_time_ms = (time.time() - start_time) * 1000
                    return cached_result
            
            # Get model deployment info
            deployment = await self._get_deployment(request.model_deployment_id)
            if not deployment:
                return PredictionResponse(
                    request_id=request.request_id,
                    prediction=None,
                    error=f"Deployment {request.model_deployment_id} not found",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Make prediction request
            response = await self._make_prediction_request(deployment, request, timeout)
            
            # Cache successful results
            if use_cache and response.error is None:
                await self._cache_prediction(request, response)
            
            # Update metrics
            await self._update_metrics(request.model_deployment_id, response, start_time)

            # Log prediction for monitoring
            if response.error is None:
                log = PredictionLog(
                    deployment_id=request.model_deployment_id,
                    request_id=request.request_id,
                    features=request.features,
                    prediction=response.prediction,
                    # ground_truth is not available here, will be None
                )
                await model_monitor.log_prediction(log)
            
            response.processing_time_ms = (time.time() - start_time) * 1000
            return response
            
        except asyncio.TimeoutError:
            error_response = PredictionResponse(
                request_id=request.request_id,
                prediction=None,
                error="Prediction timeout",
                processing_time_ms=(time.time() - start_time) * 1000
            )
            await self._update_metrics(request.model_deployment_id, error_response, start_time)
            await self._update_circuit_breaker(request.model_deployment_id, False)
            return error_response
            
        except Exception as e:
            logger.error(f"Prediction error for request {request.request_id}: {e}")
            error_response = PredictionResponse(
                request_id=request.request_id,
                prediction=None,
                error=f"Prediction error: {str(e)}",
                processing_time_ms=(time.time() - start_time) * 1000
            )
            await self._update_metrics(request.model_deployment_id, error_response, start_time)
            await self._update_circuit_breaker(request.model_deployment_id, False)
            return error_response

    async def predict_batch(
        self,
        requests: List[PredictionRequest],
        max_concurrent: int = 10
    ) -> List[PredictionResponse]:
        """Make batch predictions with concurrency control"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def predict_with_semaphore(req):
            async with semaphore:
                return await self.predict(req)
        
        tasks = [predict_with_semaphore(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                results.append(PredictionResponse(
                    request_id=requests[i].request_id,
                    prediction=None,
                    error=f"Batch prediction error: {str(response)}"
                ))
            else:
                results.append(response)
        
        return results

    async def enqueue_prediction(self, request: PredictionRequest) -> bool:
        """Add prediction to async queue for background processing"""
        try:
            await self.prediction_queue.put(request)
            return True
        except asyncio.QueueFull:
            logger.warning("Prediction queue is full")
            return False

    async def get_model_metrics(self, deployment_id: int) -> Optional[ModelMetrics]:
        """Get performance metrics for a model deployment"""
        return self.metrics.get(deployment_id)

    async def get_all_metrics(self) -> Dict[int, ModelMetrics]:
        """Get metrics for all deployments"""
        return self.metrics.copy()

    async def clear_cache(self, deployment_id: Optional[int] = None):
        """Clear prediction cache"""
        if not self.redis_client:
            return
        
        try:
            if deployment_id:
                # Clear cache for specific deployment
                pattern = f"{self.cache_prefix}{deployment_id}:*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                logger.info(f"Cleared cache for deployment {deployment_id}")
            else:
                # Clear all prediction cache
                pattern = f"{self.cache_prefix}*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                logger.info("Cleared all prediction cache")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    # Private helper methods
    
    async def _start_background_tasks(self):
        """Start background processing tasks"""
        # Queue processor
        queue_task = asyncio.create_task(self._process_prediction_queue())
        self._background_tasks.append(queue_task)
        
        # Metrics calculator
        metrics_task = asyncio.create_task(self._calculate_metrics_periodically())
        self._background_tasks.append(metrics_task)
        
        # Cache cleanup
        cache_task = asyncio.create_task(self._cleanup_cache_periodically())
        self._background_tasks.append(cache_task)
        
        # Circuit breaker reset
        cb_task = asyncio.create_task(self._reset_circuit_breakers_periodically())
        self._background_tasks.append(cb_task)

    async def _process_prediction_queue(self):
        """Background task to process queued predictions"""
        while True:
            try:
                request = await self.prediction_queue.get()
                # Process in background without waiting for result
                asyncio.create_task(self.predict(request))
                self.prediction_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing prediction queue: {e}")
                await asyncio.sleep(1)

    async def _get_deployment(self, deployment_id: int) -> Optional[ModelDeployment]:
        """Get model deployment info"""
        try:
            db = next(get_db_session())
            deployment = db.query(ModelDeployment).filter(
                ModelDeployment.id == deployment_id,
                ModelDeployment.is_active == True,
                ModelDeployment.status == DeploymentStatus.DEPLOYED
            ).first()
            db.close()
            return deployment
        except Exception as e:
            logger.error(f"Error getting deployment {deployment_id}: {e}")
            return None

    async def _make_prediction_request(
        self,
        deployment: ModelDeployment,
        request: PredictionRequest,
        timeout: float
    ) -> PredictionResponse:
        """Make HTTP request to model endpoint"""
        if not self.http_session or not deployment.endpoint_url:
            raise ValueError("HTTP session not initialized or no endpoint URL")
        
        try:
            # Prepare request payload
            payload = {
                "features": request.features,
                "metadata": request.metadata or {}
            }
            
            # Make HTTP request
            async with self.http_session.post(
                f"{deployment.endpoint_url}/predict",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Update circuit breaker on success
                    await self._update_circuit_breaker(deployment.id, True)
                    
                    return PredictionResponse(
                        request_id=request.request_id,
                        prediction=result.get("prediction"),
                        confidence=result.get("confidence"),
                        probability=result.get("probability"),
                        prediction_time=time.time(),
                        model_version=deployment.model_version.version if deployment.model_version else None,
                        metadata=result.get("metadata")
                    )
                else:
                    error_text = await response.text()
                    await self._update_circuit_breaker(deployment.id, False)
                    
                    return PredictionResponse(
                        request_id=request.request_id,
                        prediction=None,
                        error=f"HTTP {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            await self._update_circuit_breaker(deployment.id, False)
            raise

    async def _get_cached_prediction(self, request: PredictionRequest) -> Optional[PredictionResponse]:
        """Get cached prediction result"""
        if not self.redis_client:
            return None
        
        try:
            # Create cache key based on deployment and features
            features_hash = hashlib.md5(
                json.dumps(request.features, sort_keys=True).encode()
            ).hexdigest()
            cache_key = f"{self.cache_prefix}{request.model_deployment_id}:{features_hash}"
            
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                return PredictionResponse(**data)
            
        except Exception as e:
            logger.error(f"Error getting cached prediction: {e}")
        
        return None

    async def _cache_prediction(self, request: PredictionRequest, response: PredictionResponse):
        """Cache prediction result"""
        if not self.redis_client or response.error:
            return
        
        try:
            features_hash = hashlib.md5(
                json.dumps(request.features, sort_keys=True).encode()
            ).hexdigest()
            cache_key = f"{self.cache_prefix}{request.model_deployment_id}:{features_hash}"
            
            # Store response data
            cache_data = asdict(response)
            await self.redis_client.setex(
                cache_key,
                self.feature_cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error caching prediction: {e}")

    async def _check_rate_limit(self, deployment_id: int) -> bool:
        """Check if request is within rate limits"""
        if not self.redis_client:
            return True  # No rate limiting if Redis unavailable
        
        try:
            # Simple sliding window rate limiting
            window_size = 60  # 1 minute
            max_requests = 1000  # requests per minute
            
            current_time = int(time.time())
            window_start = current_time - window_size
            
            key = f"rate_limit:{deployment_id}"
            
            # Remove old entries
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            count = await self.redis_client.zcard(key)
            
            if count >= max_requests:
                return False
            
            # Add current request
            await self.redis_client.zadd(key, {str(current_time): current_time})
            await self.redis_client.expire(key, window_size + 10)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow request if rate limit check fails

    async def _check_circuit_breaker(self, deployment_id: int) -> bool:
        """Check circuit breaker status"""
        cb = self.circuit_breakers.get(deployment_id, {
            "state": "closed",  # closed, open, half_open
            "failure_count": 0,
            "last_failure_time": 0,
            "recovery_timeout": 60  # seconds
        })
        
        if cb["state"] == "open":
            # Check if recovery timeout has passed
            if time.time() - cb["last_failure_time"] > cb["recovery_timeout"]:
                cb["state"] = "half_open"
                self.circuit_breakers[deployment_id] = cb
                return True
            return False
        
        return True

    async def _update_circuit_breaker(self, deployment_id: int, success: bool):
        """Update circuit breaker state based on request outcome"""
        cb = self.circuit_breakers.get(deployment_id, {
            "state": "closed",
            "failure_count": 0,
            "last_failure_time": 0,
            "recovery_timeout": 60,
            "failure_threshold": 10
        })
        
        if success:
            if cb["state"] == "half_open":
                cb["state"] = "closed"
                cb["failure_count"] = 0
        else:
            cb["failure_count"] += 1
            cb["last_failure_time"] = time.time()
            
            if cb["failure_count"] >= cb["failure_threshold"]:
                cb["state"] = "open"
        
        self.circuit_breakers[deployment_id] = cb

    async def _update_metrics(
        self,
        deployment_id: int,
        response: PredictionResponse,
        start_time: float
    ):
        """Update performance metrics"""
        metrics = self.metrics.get(deployment_id, ModelMetrics())
        
        metrics.total_requests += 1
        
        if response.error:
            metrics.failed_requests += 1
        else:
            metrics.successful_requests += 1
            metrics.last_prediction_time = time.time()
        
        # Calculate error rate
        metrics.error_rate = metrics.failed_requests / metrics.total_requests
        
        # Update latency metrics
        latency_ms = (time.time() - start_time) * 1000
        
        # Add to latency buffer
        if deployment_id not in self.latency_buffer:
            self.latency_buffer[deployment_id] = []
        
        buffer = self.latency_buffer[deployment_id]
        buffer.append(latency_ms)
        
        # Keep buffer size manageable
        if len(buffer) > self.buffer_size:
            buffer.pop(0)
        
        self.metrics[deployment_id] = metrics

    async def _calculate_metrics_periodically(self):
        """Background task to calculate percentile metrics"""
        while True:
            try:
                await asyncio.sleep(30)  # Calculate every 30 seconds
                
                for deployment_id, buffer in self.latency_buffer.items():
                    if not buffer:
                        continue
                    
                    metrics = self.metrics.get(deployment_id, ModelMetrics())
                    
                    # Calculate percentiles
                    sorted_latencies = sorted(buffer)
                    count = len(sorted_latencies)
                    
                    metrics.avg_latency_ms = sum(sorted_latencies) / count
                    metrics.p50_latency_ms = sorted_latencies[int(count * 0.50)] if count > 0 else 0
                    metrics.p90_latency_ms = sorted_latencies[int(count * 0.90)] if count > 0 else 0
                    metrics.p95_latency_ms = sorted_latencies[int(count * 0.95)] if count > 0 else 0
                    metrics.p99_latency_ms = sorted_latencies[int(count * 0.99)] if count > 0 else 0
                    
                    self.metrics[deployment_id] = metrics
                    
            except Exception as e:
                logger.error(f"Error calculating metrics: {e}")

    async def _cleanup_cache_periodically(self):
        """Background task to cleanup expired cache entries"""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
                if self.redis_client:
                    # Redis handles TTL automatically, but we can do additional cleanup here
                    logger.debug("Cache cleanup cycle completed")
                    
            except Exception as e:
                logger.error(f"Error during cache cleanup: {e}")

    async def _reset_circuit_breakers_periodically(self):
        """Background task to reset circuit breakers"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = time.time()
                for deployment_id, cb in self.circuit_breakers.items():
                    if cb["state"] == "open":
                        if current_time - cb["last_failure_time"] > cb["recovery_timeout"]:
                            cb["state"] = "half_open"
                            logger.info(f"Circuit breaker for deployment {deployment_id} moved to half-open")
                            
            except Exception as e:
                logger.error(f"Error resetting circuit breakers: {e}")


# Global instance
prediction_service = PredictionService()