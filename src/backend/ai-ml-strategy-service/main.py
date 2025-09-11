from dotenv import load_dotenv
load_dotenv()

"""
AI/ML Strategy Service - Main FastAPI Application

This service provides comprehensive machine learning capabilities, code-based strategy
development, model training orchestration, backtesting, and paper trading functionality.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import api_router
from app.core.monitoring import setup_metrics


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
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting AI/ML Strategy Service")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Setup monitoring
    setup_metrics()
    logger.info("Metrics setup completed")

    yield

    # Shutdown
    logger.info("Shutting down AI/ML Strategy Service")


# Create FastAPI application
app = FastAPI(
    title="AI/ML Strategy Service",
    description="Comprehensive machine learning and algorithmic trading strategy development platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": "INTERNAL_ERROR"
        }
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "ai-ml-strategy-service"}


@app.get("/ready")
async def readiness_check():
    """Readiness probe for Kubernetes."""
    try:
        # Add database connectivity check here
        return {"status": "ready", "service": "ai-ml-strategy-service"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "error": str(e)}
        )


# Include API router
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_config=None,  # Use our structured logging
    )
