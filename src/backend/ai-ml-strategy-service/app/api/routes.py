"""
Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

# Import endpoint routers
from app.api.endpoints import strategies, templates, datasets

# Create main API router
api_router = APIRouter()

# Include Phase 2 endpoint routers
api_router.include_router(strategies.router, tags=["Strategy Development"])
api_router.include_router(templates.router, tags=["Strategy Templates"])

# Include Phase 3 endpoint routers
api_router.include_router(datasets.router, tags=["Dataset Management"])

# Future Phase routers (will be added in subsequent phases)
# api_router.include_router(training.router, prefix="/training", tags=["training"])
# api_router.include_router(backtesting.router, prefix="/backtests", tags=["backtesting"])
# api_router.include_router(paper_trading.router, prefix="/paper-trading", tags=["paper-trading"])
# api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])

# Basic health check endpoint
@api_router.get("/status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "operational",
        "service": "ai-ml-strategy-service",
        "version": "1.0.0",
        "phase": "3 - Dataset Management"
    }