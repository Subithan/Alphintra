"""
Alphintra Market Data Engine
Development/Demo Version
"""

from fastapi import FastAPI
import random
from datetime import datetime
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(
    title="Alphintra Market Data Engine",
    description="Real-time market data processing",
    version="1.0.0"
)

quote_counter = Counter('market_data_quotes_total', 'Total market data quotes processed')

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "market-data-engine",
        "timestamp": datetime.now().isoformat(),
        "feeds_connected": 5,
        "latency_us": 50
    }

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/quote/{symbol}")
async def get_quote(symbol: str):
    quote_counter.inc()
    base_price = {"AAPL": 150.0, "GOOGL": 2800.0, "MSFT": 300.0}.get(symbol, 100.0)
    
    return {
        "symbol": symbol,
        "bid": round(base_price * (1 - random.uniform(0.001, 0.005)), 2),
        "ask": round(base_price * (1 + random.uniform(0.001, 0.005)), 2),
        "last": round(base_price * (1 + random.uniform(-0.02, 0.02)), 2),
        "volume": random.randint(100000, 1000000),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)