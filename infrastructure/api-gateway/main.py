"""
Alphintra API Gateway
Routes requests to appropriate trading services
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import logging
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
request_count = Counter('api_gateway_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('api_gateway_request_duration_seconds', 'Request duration')

app = FastAPI(
    title="Alphintra API Gateway",
    description="Central API gateway for Alphintra Trading Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
TRADING_ENGINE_URL = os.getenv("TRADING_ENGINE_URL", "http://trading-engine:8080")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://market-data-engine:8080")
RISK_ENGINE_URL = os.getenv("RISK_ENGINE_URL", "http://risk-engine:8080")
LLM_ANALYZER_URL = os.getenv("LLM_ANALYZER_URL", "http://llm-analyzer:8080")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "api-gateway",
        "version": "1.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Alphintra Trading Platform API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

@app.post("/api/v1/orders")
async def submit_order(order_data: dict):
    """Submit trading order"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{TRADING_ENGINE_URL}/orders", json=order_data)
            request_count.labels(method="POST", endpoint="/orders", status=response.status_code).inc()
            return response.json()
    except Exception as e:
        logger.error(f"Error submitting order: {e}")
        raise HTTPException(status_code=500, detail="Order submission failed")

@app.get("/api/v1/orders/{order_id}")
async def get_order(order_id: str):
    """Get order status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TRADING_ENGINE_URL}/orders/{order_id}")
            request_count.labels(method="GET", endpoint="/orders", status=response.status_code).inc()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        raise HTTPException(status_code=500, detail="Order retrieval failed")

@app.get("/api/v1/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for symbol"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MARKET_DATA_URL}/quote/{symbol}")
            request_count.labels(method="GET", endpoint="/market-data", status=response.status_code).inc()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail="Market data retrieval failed")

@app.get("/api/v1/portfolio/{account_id}")
async def get_portfolio(account_id: str):
    """Get portfolio information"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TRADING_ENGINE_URL}/portfolio/{account_id}")
            request_count.labels(method="GET", endpoint="/portfolio", status=response.status_code).inc()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Portfolio retrieval failed")

@app.get("/api/v1/risk/{account_id}")
async def get_risk_metrics(account_id: str):
    """Get risk metrics"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RISK_ENGINE_URL}/risk/{account_id}")
            request_count.labels(method="GET", endpoint="/risk", status=response.status_code).inc()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Risk metrics retrieval failed")

@app.get("/api/v1/analysis/market")
async def get_market_analysis():
    """Get AI market analysis"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LLM_ANALYZER_URL}/analysis/latest")
            request_count.labels(method="GET", endpoint="/analysis", status=response.status_code).inc()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting market analysis: {e}")
        raise HTTPException(status_code=500, detail="Market analysis retrieval failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)