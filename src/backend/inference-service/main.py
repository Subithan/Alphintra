"""
Strategy Inference and Signal Distribution Service

Main FastAPI application for executing trading strategies and distributing signals.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api import strategies, signals, health
from app.services.strategy_loader import StrategyLoader
from app.services.inference_engine import InferenceEngine
from app.services.signal_distributor import SignalDistributor
from app.services.market_data_client import MarketDataClient
from app.utils.monitoring import setup_prometheus_metrics

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Configuration
SERVICE_NAME = "inference-service"
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Database connections
AI_ML_DATABASE_URL = os.getenv(
    "AI_ML_DATABASE_URL", 
    "postgresql://alphintra:alphintra@localhost:5432/alphintra_ai_ml"
)
NO_CODE_DATABASE_URL = os.getenv(
    "NO_CODE_DATABASE_URL",
    "postgresql://alphintra:alphintra@localhost:5432/alphintra_nocode"
)

# Service dependencies
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Global service instances
strategy_loader: StrategyLoader = None
inference_engine: InferenceEngine = None
signal_distributor: SignalDistributor = None
market_data_client: MarketDataClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global strategy_loader, inference_engine, signal_distributor, market_data_client
    
    logger.info("Starting Strategy Inference Service", version=VERSION)
    
    try:
        # Initialize services
        strategy_loader = StrategyLoader(AI_ML_DATABASE_URL, NO_CODE_DATABASE_URL)
        await strategy_loader.initialize()
        
        market_data_client = MarketDataClient()
        await market_data_client.initialize()
        
        signal_distributor = SignalDistributor(
            kafka_servers=KAFKA_BOOTSTRAP_SERVERS,
            redis_url=REDIS_URL
        )
        await signal_distributor.initialize()
        
        inference_engine = InferenceEngine(
            strategy_loader=strategy_loader,
            market_data_client=market_data_client,
            signal_distributor=signal_distributor
        )
        await inference_engine.initialize()
        
        # Setup monitoring
        setup_prometheus_metrics()
        
        logger.info("Strategy Inference Service started successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start service", error=str(e))
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down Strategy Inference Service")
        
        if inference_engine:
            await inference_engine.shutdown()
        if signal_distributor:
            await signal_distributor.shutdown()
        if market_data_client:
            await market_data_client.shutdown()
        if strategy_loader:
            await strategy_loader.shutdown()

# Create FastAPI application
app = FastAPI(
    title="Strategy Inference Service",
    description="Execute trading strategies and distribute signals in real-time",
    version=VERSION,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if DEBUG else ["https://trading.alphintra.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(signals.router, prefix="/api/signals", tags=["Signals"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": SERVICE_NAME,
        "version": VERSION,
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "strategies": "/api/strategies",
            "signals": "/api/signals",
            "docs": "/docs" if DEBUG else "disabled"
        }
    }

if __name__ == "__main__":
    # Get port from environment, default to 8003
    port = int(os.getenv("SERVICE_PORT", 8003))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=DEBUG,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )