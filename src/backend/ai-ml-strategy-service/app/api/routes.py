"""
Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

# Import all routers (will be created in subsequent phases)
# from app.api.endpoints import (
#     strategies,
#     datasets,
#     training,
#     backtesting,
#     paper_trading,
#     experiments
# )

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
# api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
# api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
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
        "version": "1.0.0"
    }