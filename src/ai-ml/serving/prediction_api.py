"""
ML Model Prediction API Service
Alphintra Trading Platform - Phase 4
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
import asyncio
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
import pickle
import joblib
from pathlib import Path
from datetime import datetime, timedelta
import warnings
import hashlib
import uuid

# FastAPI for REST API
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Async Redis for caching
import aioredis

# Model loading and inference
import torch
import torch.nn as nn
from sklearn.base import BaseEstimator

# Monitoring and metrics
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST

# Import custom components
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from feature_engineering.technical_indicators import TechnicalIndicators
from training.model_training import ModelType, TaskType, ModelConfig, TrainingResults

logger = logging.getLogger(__name__)


class PredictionStatus(Enum):
    """Prediction status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    CACHED = "cached"
    MODEL_NOT_FOUND = "model_not_found"
    INVALID_INPUT = "invalid_input"


# Pydantic models for API
class PredictionRequest(BaseModel):
    """Request model for predictions"""
    model_id: str = Field(..., description="Model identifier")
    features: Dict[str, float] = Field(..., description="Feature values for prediction")
    symbol: Optional[str] = Field(None, description="Trading symbol")
    timestamp: Optional[datetime] = Field(None, description="Timestamp for prediction")
    cache_ttl: Optional[int] = Field(300, description="Cache TTL in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions"""
    model_id: str = Field(..., description="Model identifier")
    features_batch: List[Dict[str, float]] = Field(..., description="Batch of feature values")
    symbols: Optional[List[str]] = Field(None, description="Trading symbols")
    timestamps: Optional[List[datetime]] = Field(None, description="Timestamps for predictions")
    cache_ttl: Optional[int] = Field(300, description="Cache TTL in seconds")


class PredictionResponse(BaseModel):
    """Response model for predictions"""
    prediction_id: str = Field(..., description="Unique prediction identifier")
    model_id: str = Field(..., description="Model identifier used")
    prediction: float = Field(..., description="Prediction value")
    confidence: Optional[float] = Field(None, description="Prediction confidence")
    probabilities: Optional[Dict[str, float]] = Field(None, description="Class probabilities")
    features_used: List[str] = Field(..., description="Features used in prediction")
    status: PredictionStatus = Field(..., description="Prediction status")
    latency_ms: float = Field(..., description="Prediction latency in milliseconds")
    timestamp: datetime = Field(..., description="Prediction timestamp")
    cached: bool = Field(False, description="Whether result was cached")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions"""
    batch_id: str = Field(..., description="Unique batch identifier")
    model_id: str = Field(..., description="Model identifier used")
    predictions: List[PredictionResponse] = Field(..., description="Individual predictions")
    total_count: int = Field(..., description="Total number of predictions")
    success_count: int = Field(..., description="Number of successful predictions")
    error_count: int = Field(..., description="Number of failed predictions")
    avg_latency_ms: float = Field(..., description="Average prediction latency")
    total_latency_ms: float = Field(..., description="Total batch processing time")
    status: PredictionStatus = Field(..., description="Overall batch status")


class ModelInfo(BaseModel):
    """Model information response"""
    model_id: str = Field(..., description="Model identifier")
    model_type: str = Field(..., description="Model type")
    task_type: str = Field(..., description="Task type")
    features: List[str] = Field(..., description="Required features")
    training_score: float = Field(..., description="Training score")
    validation_score: float = Field(..., description="Validation score")
    test_score: float = Field(..., description="Test score")
    training_time: float = Field(..., description="Training time in seconds")
    created_at: datetime = Field(..., description="Model creation timestamp")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    prediction_count: int = Field(0, description="Total predictions made")


@dataclass
class ModelArtifacts:
    """Container for loaded model artifacts"""
    model: Any
    scaler: Any
    feature_names: List[str]
    model_type: ModelType
    task_type: TaskType
    metadata: Dict[str, Any]
    loaded_at: datetime
    usage_count: int = 0


class ModelRegistry:
    """
    Model registry for loading and managing ML models
    """
    
    def __init__(self, models_dir: str = "models", cache_size: int = 10):
        self.models_dir = Path(models_dir)
        self.cache_size = cache_size
        self.loaded_models: Dict[str, ModelArtifacts] = {}
        self.model_metadata: Dict[str, Dict] = {}
        
        # Load model metadata
        self._load_model_metadata()
    
    def _load_model_metadata(self):
        """Load metadata for all available models"""
        try:
            experiments_dir = self.models_dir.parent / "experiments"
            
            if experiments_dir.exists():
                for metadata_file in experiments_dir.glob("*_results.json"):
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        model_id = metadata.get('model_id')
                        if model_id:
                            self.model_metadata[model_id] = metadata
                            logger.info(f"Loaded metadata for model {model_id}")
                    
                    except Exception as e:
                        logger.warning(f"Error loading metadata from {metadata_file}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error loading model metadata: {str(e)}")
    
    async def load_model(self, model_id: str) -> ModelArtifacts:
        """Load model and its artifacts"""
        try:
            # Check if already loaded
            if model_id in self.loaded_models:
                artifacts = self.loaded_models[model_id]
                artifacts.usage_count += 1
                return artifacts
            
            # Check if model exists
            if model_id not in self.model_metadata:
                raise ValueError(f"Model {model_id} not found in registry")
            
            metadata = self.model_metadata[model_id]
            
            # Load model file
            model_path = Path(metadata.get('model_path'))
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Load scaler if exists
            scaler_path = Path(metadata.get('scaler_path', ''))
            scaler = None
            if scaler_path.exists():
                scaler = joblib.load(scaler_path)
            
            # Load model based on type
            model_type_str = metadata.get('model_type', 'unknown')
            model_type = ModelType(model_type_str) if model_type_str in [mt.value for mt in ModelType] else None
            
            if model_path.suffix == '.pth':  # PyTorch model
                # For PyTorch models, we'd need the model architecture
                # This is simplified - in practice you'd need to reconstruct the model
                model = torch.load(model_path, map_location='cpu')
            else:  # Scikit-learn model
                model = joblib.load(model_path)
            
            # Create artifacts
            artifacts = ModelArtifacts(
                model=model,
                scaler=scaler,
                feature_names=metadata.get('feature_columns', []),
                model_type=model_type or ModelType.LINEAR_REGRESSION,
                task_type=TaskType(metadata.get('task_type', 'regression')),
                metadata=metadata,
                loaded_at=datetime.now(),
                usage_count=1
            )
            
            # Cache model (with LRU eviction)
            if len(self.loaded_models) >= self.cache_size:
                # Remove least recently used model
                lru_model_id = min(
                    self.loaded_models.keys(),
                    key=lambda k: self.loaded_models[k].loaded_at
                )
                del self.loaded_models[lru_model_id]
                logger.info(f"Evicted model {lru_model_id} from cache")
            
            self.loaded_models[model_id] = artifacts
            logger.info(f"Loaded model {model_id} into cache")
            
            return artifacts
        
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {str(e)}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available model IDs"""
        return list(self.model_metadata.keys())
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """Get model metadata"""
        return self.model_metadata.get(model_id)
    
    def update_model_usage(self, model_id: str):
        """Update model usage statistics"""
        if model_id in self.loaded_models:
            self.loaded_models[model_id].usage_count += 1
        
        # Update metadata
        if model_id in self.model_metadata:
            self.model_metadata[model_id]['last_used'] = datetime.now().isoformat()
            self.model_metadata[model_id]['prediction_count'] = (
                self.model_metadata[model_id].get('prediction_count', 0) + 1
            )


class PredictionEngine:
    """
    High-performance prediction engine with caching and monitoring
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.model_registry = ModelRegistry()
        self.technical_indicators = TechnicalIndicators()
        
        # Metrics
        self.prediction_counter = Counter('predictions_total', 'Total predictions', ['model_id', 'status'])
        self.prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency', ['model_id'])
        self.active_models = Gauge('active_models_count', 'Number of loaded models')
        self.cache_hits = Counter('cache_hits_total', 'Cache hits', ['model_id'])
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis for prediction caching")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None
    
    async def predict(self, request: PredictionRequest) -> PredictionResponse:
        """Make a single prediction"""
        start_time = time.time()
        prediction_id = str(uuid.uuid4())
        
        try:
            # Check cache first
            cached_result = await self._get_cached_prediction(request)
            if cached_result:
                self.cache_hits.labels(model_id=request.model_id).inc()
                return cached_result
            
            # Load model
            artifacts = await self.model_registry.load_model(request.model_id)
            
            # Prepare features
            features_array = self._prepare_features(request.features, artifacts.feature_names)
            
            # Scale features if scaler is available
            if artifacts.scaler:
                features_array = artifacts.scaler.transform(features_array)
            
            # Make prediction
            prediction, confidence, probabilities = await self._make_prediction(
                artifacts, features_array
            )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Create response
            response = PredictionResponse(
                prediction_id=prediction_id,
                model_id=request.model_id,
                prediction=prediction,
                confidence=confidence,
                probabilities=probabilities,
                features_used=artifacts.feature_names,
                status=PredictionStatus.SUCCESS,
                latency_ms=latency_ms,
                timestamp=request.timestamp or datetime.now(),
                cached=False
            )
            
            # Cache result
            await self._cache_prediction(request, response)
            
            # Update metrics
            self.prediction_counter.labels(
                model_id=request.model_id, 
                status=PredictionStatus.SUCCESS.value
            ).inc()
            self.prediction_latency.labels(model_id=request.model_id).observe(latency_ms / 1000)
            self.model_registry.update_model_usage(request.model_id)
            
            return response
        
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Update error metrics
            self.prediction_counter.labels(
                model_id=request.model_id, 
                status=PredictionStatus.ERROR.value
            ).inc()
            
            return PredictionResponse(
                prediction_id=prediction_id,
                model_id=request.model_id,
                prediction=0.0,
                confidence=None,
                probabilities=None,
                features_used=[],
                status=PredictionStatus.ERROR,
                latency_ms=latency_ms,
                timestamp=datetime.now(),
                cached=False
            )
    
    async def predict_batch(self, request: BatchPredictionRequest) -> BatchPredictionResponse:
        """Make batch predictions"""
        start_time = time.time()
        batch_id = str(uuid.uuid4())
        predictions = []
        
        try:
            # Load model once for the entire batch
            artifacts = await self.model_registry.load_model(request.model_id)
            
            # Process each prediction in the batch
            for i, features in enumerate(request.features_batch):
                symbol = request.symbols[i] if request.symbols and i < len(request.symbols) else None
                timestamp = request.timestamps[i] if request.timestamps and i < len(request.timestamps) else None
                
                # Create individual prediction request
                pred_request = PredictionRequest(
                    model_id=request.model_id,
                    features=features,
                    symbol=symbol,
                    timestamp=timestamp,
                    cache_ttl=request.cache_ttl
                )
                
                # Make prediction
                prediction = await self.predict(pred_request)
                predictions.append(prediction)
            
            # Calculate batch metrics
            total_latency_ms = (time.time() - start_time) * 1000
            success_count = sum(1 for p in predictions if p.status == PredictionStatus.SUCCESS)
            error_count = len(predictions) - success_count
            avg_latency_ms = sum(p.latency_ms for p in predictions) / len(predictions) if predictions else 0
            
            status = PredictionStatus.SUCCESS if error_count == 0 else PredictionStatus.ERROR
            
            return BatchPredictionResponse(
                batch_id=batch_id,
                model_id=request.model_id,
                predictions=predictions,
                total_count=len(predictions),
                success_count=success_count,
                error_count=error_count,
                avg_latency_ms=avg_latency_ms,
                total_latency_ms=total_latency_ms,
                status=status
            )
        
        except Exception as e:
            logger.error(f"Error making batch predictions: {str(e)}")
            
            return BatchPredictionResponse(
                batch_id=batch_id,
                model_id=request.model_id,
                predictions=predictions,
                total_count=len(request.features_batch),
                success_count=0,
                error_count=len(request.features_batch),
                avg_latency_ms=0.0,
                total_latency_ms=(time.time() - start_time) * 1000,
                status=PredictionStatus.ERROR
            )
    
    def _prepare_features(self, features: Dict[str, float], feature_names: List[str]) -> np.ndarray:
        """Prepare features for prediction"""
        try:
            # Ensure all required features are present
            feature_values = []
            for name in feature_names:
                if name in features:
                    feature_values.append(features[name])
                else:
                    logger.warning(f"Missing feature {name}, using 0.0")
                    feature_values.append(0.0)
            
            return np.array(feature_values).reshape(1, -1)
        
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            raise ValueError(f"Invalid features: {str(e)}")
    
    async def _make_prediction(self, artifacts: ModelArtifacts, 
                             features: np.ndarray) -> Tuple[float, Optional[float], Optional[Dict[str, float]]]:
        """Make prediction using loaded model"""
        try:
            model = artifacts.model
            
            # Handle different model types
            if isinstance(model, torch.nn.Module):
                # PyTorch model
                model.eval()
                with torch.no_grad():
                    features_tensor = torch.FloatTensor(features)
                    output = model(features_tensor)
                    prediction = output.item()
                    confidence = None
                    probabilities = None
            
            elif hasattr(model, 'predict_proba'):
                # Classification model with probabilities
                prediction = model.predict(features)[0]
                proba = model.predict_proba(features)[0]
                confidence = np.max(proba)
                
                # Get class names if available
                if hasattr(model, 'classes_'):
                    probabilities = {str(cls): float(prob) for cls, prob in zip(model.classes_, proba)}
                else:
                    probabilities = {str(i): float(prob) for i, prob in enumerate(proba)}
            
            elif hasattr(model, 'predict'):
                # Standard prediction
                prediction = model.predict(features)[0]
                confidence = None
                probabilities = None
            
            else:
                raise ValueError(f"Unsupported model type: {type(model)}")
            
            return float(prediction), confidence, probabilities
        
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            raise
    
    async def _get_cached_prediction(self, request: PredictionRequest) -> Optional[PredictionResponse]:
        """Get cached prediction if available"""
        if not self.redis_client:
            return None
        
        try:
            # Create cache key
            cache_key = self._create_cache_key(request)
            
            # Get from cache
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                cached_dict = json.loads(cached_data)
                response = PredictionResponse(**cached_dict)
                response.cached = True
                return response
        
        except Exception as e:
            logger.warning(f"Error getting cached prediction: {str(e)}")
        
        return None
    
    async def _cache_prediction(self, request: PredictionRequest, response: PredictionResponse):
        """Cache prediction result"""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._create_cache_key(request)
            cache_data = response.dict()
            cache_data['timestamp'] = response.timestamp.isoformat()
            
            await self.redis_client.setex(
                cache_key,
                request.cache_ttl,
                json.dumps(cache_data, default=str)
            )
        
        except Exception as e:
            logger.warning(f"Error caching prediction: {str(e)}")
    
    def _create_cache_key(self, request: PredictionRequest) -> str:
        """Create cache key for prediction request"""
        # Create deterministic hash of request
        key_data = {
            'model_id': request.model_id,
            'features': sorted(request.features.items()),
            'symbol': request.symbol
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"prediction:{key_hash}"
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get model information"""
        try:
            metadata = self.model_registry.get_model_info(model_id)
            if not metadata:
                return None
            
            return ModelInfo(
                model_id=model_id,
                model_type=metadata.get('model_type', 'unknown'),
                task_type=metadata.get('task_type', 'unknown'),
                features=metadata.get('feature_columns', []),
                training_score=metadata.get('training_score', 0.0),
                validation_score=metadata.get('validation_score', 0.0),
                test_score=metadata.get('test_score', 0.0),
                training_time=metadata.get('training_time', 0.0),
                created_at=datetime.fromisoformat(metadata.get('timestamp', datetime.now().isoformat())),
                last_used=datetime.fromisoformat(metadata['last_used']) if metadata.get('last_used') else None,
                prediction_count=metadata.get('prediction_count', 0)
            )
        
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return None
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get all available models"""
        models = []
        for model_id in self.model_registry.get_available_models():
            model_info = await self.get_model_info(model_id)
            if model_info:
                models.append(model_info)
        return models
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        # Update active models gauge
        self.active_models.set(len(self.model_registry.loaded_models))
        
        return generate_latest()
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()


# FastAPI application
app = FastAPI(
    title="Alphintra ML Prediction API",
    description="High-performance machine learning prediction service for trading strategies",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global prediction engine
prediction_engine = None


@app.on_event("startup")
async def startup_event():
    """Initialize prediction engine on startup"""
    global prediction_engine
    prediction_engine = PredictionEngine()
    await prediction_engine.initialize()
    logger.info("Prediction API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if prediction_engine:
        await prediction_engine.cleanup()
    logger.info("Prediction API stopped")


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """Make a single prediction"""
    if not prediction_engine:
        raise HTTPException(status_code=500, detail="Prediction engine not initialized")
    
    try:
        return await prediction_engine.predict(request)
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResponse:
    """Make batch predictions"""
    if not prediction_engine:
        raise HTTPException(status_code=500, detail="Prediction engine not initialized")
    
    try:
        return await prediction_engine.predict_batch(request)
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models", response_model=List[ModelInfo])
async def get_models() -> List[ModelInfo]:
    """Get all available models"""
    if not prediction_engine:
        raise HTTPException(status_code=500, detail="Prediction engine not initialized")
    
    try:
        return await prediction_engine.get_available_models()
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str) -> ModelInfo:
    """Get specific model information"""
    if not prediction_engine:
        raise HTTPException(status_code=500, detail="Prediction engine not initialized")
    
    try:
        model_info = await prediction_engine.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        return model_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    if not prediction_engine:
        raise HTTPException(status_code=500, detail="Prediction engine not initialized")
    
    metrics = prediction_engine.get_metrics()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)


# Example usage and testing
if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "prediction_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )