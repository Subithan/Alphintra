"""
Risk Management Service - Critical Security Microservice
Handles risk assessment, limit monitoring, and compliance checks for trading operations
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime, timedelta
import os
import logging
from prometheus_fastapi_instrumentator import Instrumentator
import redis
import httpx
from decimal import Decimal
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration with K3D internal networking
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://risk_service_user:risk_service_pass@postgresql-primary.alphintra.svc.cluster.local:5432/alphintra_risk"
)

# Redis configuration
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/2"
)

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service.alphintra.svc.cluster.local:8080")

# Initialize Redis
try:
    redis_client = redis.from_url(REDIS_URL)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

# Initialize FastAPI app
app = FastAPI(
    title="Alphintra Risk Management Service",
    description="Critical risk assessment and compliance microservice for financial trading",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Security
security = HTTPBearer()

# HTTP client for service communication
http_client = httpx.AsyncClient(timeout=30.0)

# Risk limits configuration
DEFAULT_RISK_LIMITS = {
    "max_daily_loss": 5000.0,
    "max_daily_loss_percent": 5.0,
    "max_position_size": 10000.0,
    "max_position_size_percent": 10.0,
    "max_leverage": 3.0,
    "max_concentration": {
        "CRYPTO": 0.70,
        "STOCKS": 0.80,
        "FOREX": 0.60
    },
    "max_correlation": 0.75,
    "stop_loss_required": True,
    "max_orders_per_minute": 100,
    "max_drawdown": 0.10
}

# Health checks
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Check Redis connection if available
        if redis_client:
            redis_client.ping()
        
        return {
            "status": "healthy",
            "service": "risk-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    return {
        "status": "ready",
        "service": "risk-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "risk-service",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "assess": "/api/v1/risk/assess",
            "limits": "/api/v1/risk/limits",
            "metrics": "/api/v1/risk/metrics"
        }
    }

# Risk Assessment API Routes
@app.post("/api/v1/risk/assess")
async def assess_order_risk(risk_request: dict):
    """Assess risk for a trading order"""
    try:
        user_id = risk_request.get("user_id")
        order = risk_request.get("order", {})
        
        # Mock risk assessment
        risk_assessment = {
            "approved": True,
            "risk_score": 25.0,
            "risk_level": "LOW",
            "reason": None,
            "adjustments": []
        }
        
        # Cache assessment result
        assessment_id = str(uuid.uuid4())
        if redis_client:
            redis_client.setex(
                f"risk_assessment:{assessment_id}",
                3600,
                json.dumps(risk_assessment)
            )
        
        logger.info(f"Risk assessment for user {user_id}: {risk_assessment}")
        
        return {
            "assessment_id": assessment_id,
            "approved": risk_assessment["approved"],
            "risk_score": risk_assessment["risk_score"],
            "risk_level": risk_assessment["risk_level"],
            "reason": risk_assessment.get("reason"),
            "adjustments": risk_assessment.get("adjustments", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in risk assessment: {e}")
        raise HTTPException(status_code=500, detail="Risk assessment failed")

@app.post("/api/v1/risk/assess-signal")
async def assess_signal_risk(signal: dict):
    """Assess risk for a trading signal"""
    try:
        # Mock signal risk assessment
        signal_risk = {
            "approved": True,
            "risk_score": 30.0,
            "risk_level": "LOW",
            "quality_factors": [],
            "reason": None
        }
        
        logger.info(f"Signal risk assessment: {signal_risk}")
        
        return signal_risk
        
    except Exception as e:
        logger.error(f"Error in signal risk assessment: {e}")
        raise HTTPException(status_code=500, detail="Signal risk assessment failed")

@app.get("/api/v1/risk/metrics")
async def get_risk_metrics():
    """Get current risk metrics"""
    try:
        # Mock risk metrics
        risk_metrics = {
            "portfolio_id": "portfolio-123",
            "risk_metrics": {
                "var_1day": {
                    "amount": 2500,
                    "percent": 0.025,
                    "confidence": 95
                },
                "var_5day": {
                    "amount": 5590,
                    "percent": 0.056,
                    "confidence": 95
                },
                "expected_shortfall": 3200,
                "beta": 1.15,
                "sharpe_ratio": 1.25,
                "max_drawdown": 0.08,
                "current_drawdown": 0.02
            },
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        return risk_metrics
        
    except Exception as e:
        logger.error(f"Error fetching risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch risk metrics")

@app.get("/api/v1/risk/limits")
async def get_risk_limits():
    """Get risk limits"""
    try:
        return DEFAULT_RISK_LIMITS
        
    except Exception as e:
        logger.error(f"Error fetching risk limits: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch risk limits")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )