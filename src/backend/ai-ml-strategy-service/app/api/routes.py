"""
Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

# Import endpoint routers

from app.api.endpoints import strategies, templates, datasets, training, backtesting, paper_trading, live_execution, ai_code, model_registry, prediction, model_monitoring, hybrid_execution, research, files
# feature_engineering temporarily disabled due to talib dependency
# model_deployment and model_lifecycle temporarily disabled due to kubernetes dependency

# Create main API router
api_router = APIRouter()

# Include Phase 2 endpoint routers
api_router.include_router(strategies.router, tags=["Strategy Development"])
api_router.include_router(templates.router, tags=["Strategy Templates"])

# Include Phase 3 endpoint routers
api_router.include_router(datasets.router, tags=["Dataset Management"])
# api_router.include_router(feature_engineering.router, prefix="/feature-engineering", tags=["Feature Engineering"])  # Temporarily disabled due to talib dependency

# Include Phase 4 endpoint routers
api_router.include_router(training.router, tags=["Model Training"])

# Include Phase 5 endpoint routers
api_router.include_router(backtesting.router, tags=["Backtesting"])

# Include Phase 6 endpoint routers
api_router.include_router(paper_trading.router, tags=["Paper Trading"])

# Include Phase 7 endpoint routers
api_router.include_router(live_execution.router, tags=["Live Execution"])
# api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])

# Include AI Code endpoints
api_router.include_router(ai_code.router, tags=["AI Code Assistant"])

# Include Model Registry endpoints  
api_router.include_router(model_registry.router, tags=["Model Registry"])

# Include Model Deployment endpoints
# api_router.include_router(model_deployment.router, tags=["Model Deployment"])  # Temporarily disabled due to kubernetes dependency

# Include Prediction Service endpoints
api_router.include_router(prediction.router, tags=["Real-time Predictions"])

# Include Model Monitoring endpoints
api_router.include_router(model_monitoring.router, tags=["Model Monitoring"])

# Include Model Lifecycle endpoints
# api_router.include_router(model_lifecycle.router, tags=["Model Lifecycle"])  # Temporarily disabled due to kubernetes dependency

# Include new execution modes
api_router.include_router(hybrid_execution.router, tags=["Hybrid Execution"])
api_router.include_router(research.router, tags=["Research Mode"])

# Include File Management endpoints for IDE integration
api_router.include_router(files.router, tags=["File Management"])

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