"""
Alphintra Risk Engine
Development/Demo Version
"""

from fastapi import FastAPI
import random
from datetime import datetime
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(
    title="Alphintra Risk Engine",
    description="Real-time risk management and monitoring",
    version="1.0.0"
)

risk_check_counter = Counter('risk_checks_total', 'Total risk checks performed')

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "risk-engine",
        "timestamp": datetime.now().isoformat(),
        "risk_models_active": 5,
        "monitoring": "real-time"
    }

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/risk/{account_id}")
async def get_risk_metrics(account_id: str):
    risk_check_counter.inc()
    
    return {
        "account_id": account_id,
        "var_1day": random.uniform(15000, 25000),
        "var_5day": random.uniform(45000, 65000),
        "expected_shortfall": random.uniform(75000, 95000),
        "gross_exposure": random.uniform(450000, 550000),
        "net_exposure": random.uniform(400000, 500000),
        "leverage": random.uniform(2.0, 2.5),
        "risk_status": "WITHIN_LIMITS",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)