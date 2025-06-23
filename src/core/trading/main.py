"""
Alphintra Trading Engine
Development/Demo Version
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import logging
from datetime import datetime
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Alphintra Trading Engine",
    description="Ultra-low latency trading engine",
    version="1.0.0"
)

# Metrics
order_counter = Counter('trading_orders_total', 'Total trading orders processed')

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "trading-engine",
        "timestamp": datetime.now().isoformat(),
        "latency_ms": 0.3,
        "throughput_capacity": "1.2M orders/sec"
    }

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/orders")
async def submit_order(order: dict):
    order_counter.inc()
    logger.info(f"Order received: {order}")
    return {
        "order_id": f"ord-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "status": "PENDING",
        "message": "Order submitted successfully"
    }

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    return {
        "order_id": order_id,
        "status": "EXECUTED",
        "symbol": "AAPL",
        "quantity": 100,
        "price": 150.0,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/portfolio/{account_id}")
async def get_portfolio(account_id: str):
    return {
        "account_id": account_id,
        "total_value": 1000000.0,
        "cash_balance": 50000.0,
        "positions": [
            {"symbol": "AAPL", "quantity": 100, "market_value": 15000.0},
            {"symbol": "GOOGL", "quantity": 10, "market_value": 28000.0}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)