"""
Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

# Import endpoint routers
from app.api.endpoints import strategies, templates, datasets, training, backtesting, paper_trading, live_execution

# Create main API router
api_router = APIRouter()

# Include Phase 2 endpoint routers
api_router.include_router(strategies.router, tags=["Strategy Development"])
api_router.include_router(templates.router, tags=["Strategy Templates"])

# Include Phase 3 endpoint routers
api_router.include_router(datasets.router, tags=["Dataset Management"])

# Include Phase 4 endpoint routers
api_router.include_router(training.router, tags=["Model Training"])

# Include Phase 5 endpoint routers
api_router.include_router(backtesting.router, tags=["Backtesting"])

# Include Phase 6 endpoint routers
api_router.include_router(paper_trading.router, tags=["Paper Trading"])

# Include Phase 7 endpoint routers
api_router.include_router(live_execution.router, tags=["Live Execution"])
# api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])

# Basic health check endpoint
@api_router.get("/status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "operational",
        "service": "ai-ml-strategy-service",
        "version": "1.0.0",
        "phase": "7 - Live Strategy Execution Engine"
    }