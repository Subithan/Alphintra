"""
GraphQL Gateway Service - Unified API Layer
Provides a single GraphQL endpoint that federates all microservices
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional, Dict, Any
import httpx
import asyncio
import os
import logging
from datetime import datetime
import redis.asyncio as redis
from prometheus_fastapi_instrumentator import Instrumentator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs with K3D internal networking
SERVICES = {
    "trading": os.getenv("TRADING_SERVICE_URL", "http://trading-service.alphintra.svc.cluster.local:8080"),
    "risk": os.getenv("RISK_SERVICE_URL", "http://risk-service.alphintra.svc.cluster.local:8080"),
    "user": os.getenv("USER_SERVICE_URL", "http://user-service.alphintra.svc.cluster.local:8080"),
    "nocode": os.getenv("NO_CODE_SERVICE_URL", "http://no-code-service.alphintra.svc.cluster.local:8080"),
    "strategy": os.getenv("STRATEGY_SERVICE_URL", "http://strategy-service.alphintra.svc.cluster.local:8080"),
    "broker": os.getenv("BROKER_SERVICE_URL", "http://broker-service.alphintra.svc.cluster.local:8080"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service.alphintra.svc.cluster.local:8080"),
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service.alphintra.svc.cluster.local:8080")
}

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/7")

# Global HTTP client and Redis client
http_client = None
redis_client = None

# GraphQL Types
@strawberry.type
class User:
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime

@strawberry.type
class Trade:
    id: str
    user_id: str
    symbol: str
    side: str
    quantity: float
    price: Optional[float] = None
    status: str
    created_at: datetime
    executed_at: Optional[datetime] = None

@strawberry.type
class Strategy:
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    is_active: bool
    created_at: datetime
    performance_metrics: Optional[Dict[str, Any]] = None

@strawberry.type
class NoCodeWorkflow:
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    workflow_data: Dict[str, Any]
    is_active: bool
    created_at: datetime
    last_executed: Optional[datetime] = None

@strawberry.type
class RiskAssessment:
    id: str
    user_id: str
    risk_score: float
    risk_level: str
    recommendations: List[str]
    created_at: datetime

@strawberry.type
class Portfolio:
    user_id: str
    total_value: float
    cash_balance: float
    positions: List[Dict[str, Any]]
    performance: Dict[str, float]
    last_updated: datetime

@strawberry.type
class MarketData:
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime

# Input Types
@strawberry.input
class TradeInput:
    symbol: str
    side: str
    quantity: float
    order_type: str = "market"
    price: Optional[float] = None

@strawberry.input
class StrategyInput:
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]

@strawberry.input
class WorkflowInput:
    name: str
    description: Optional[str] = None
    workflow_data: Dict[str, Any]

# Service Communication Helper
async def call_service(service_name: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP calls to microservices with error handling and caching"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
    
    url = f"{SERVICES[service_name]}/{endpoint.lstrip('/')}"
    cache_key = f"gql_cache:{service_name}:{endpoint}:{method}"
    
    try:
        # Try cache for GET requests
        if method == "GET" and redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                import json
                return json.loads(cached)
        
        # Make HTTP request
        async with http_client.request(method, url, json=data, timeout=30.0) as response:
            if response.status_code == 200:
                result = response.json()
                
                # Cache successful GET responses for 5 minutes
                if method == "GET" and redis_client:
                    import json
                    await redis_client.setex(cache_key, 300, json.dumps(result))
                
                return result
            else:
                logger.error(f"Service {service_name} returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Service error: {response.text}")
                
    except httpx.TimeoutException:
        logger.error(f"Timeout calling {service_name} service")
        raise HTTPException(status_code=504, detail=f"Service {service_name} timeout")
    except Exception as e:
        logger.error(f"Error calling {service_name} service: {e}")
        raise HTTPException(status_code=500, detail=f"Service communication error: {str(e)}")

# GraphQL Resolvers
@strawberry.type
class Query:
    @strawberry.field
    async def users(self, limit: Optional[int] = 10) -> List[User]:
        """Get list of users"""
        data = await call_service("user", f"users?limit={limit}")
        return [User(**user) for user in data.get("users", [])]
    
    @strawberry.field
    async def user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            data = await call_service("user", f"users/{user_id}")
            return User(**data) if data else None
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise e
    
    @strawberry.field
    async def trades(self, user_id: Optional[str] = None, symbol: Optional[str] = None, limit: Optional[int] = 20) -> List[Trade]:
        """Get trades with optional filtering"""
        params = []
        if user_id:
            params.append(f"user_id={user_id}")
        if symbol:
            params.append(f"symbol={symbol}")
        params.append(f"limit={limit}")
        
        query_string = "&".join(params)
        data = await call_service("trading", f"trades?{query_string}")
        return [Trade(**trade) for trade in data.get("trades", [])]
    
    @strawberry.field
    async def strategies(self, user_id: Optional[str] = None, is_active: Optional[bool] = None) -> List[Strategy]:
        """Get trading strategies"""
        params = []
        if user_id:
            params.append(f"user_id={user_id}")
        if is_active is not None:
            params.append(f"is_active={is_active}")
        
        query_string = "&".join(params)
        data = await call_service("strategy", f"strategies?{query_string}")
        return [Strategy(**strategy) for strategy in data.get("strategies", [])]
    
    @strawberry.field
    async def workflows(self, user_id: Optional[str] = None) -> List[NoCodeWorkflow]:
        """Get no-code workflows"""
        params = []
        if user_id:
            params.append(f"user_id={user_id}")
        
        query_string = "&".join(params)
        data = await call_service("nocode", f"workflows?{query_string}")
        return [NoCodeWorkflow(**workflow) for workflow in data.get("workflows", [])]
    
    @strawberry.field
    async def portfolio(self, user_id: str) -> Optional[Portfolio]:
        """Get user portfolio"""
        try:
            data = await call_service("trading", f"portfolio/{user_id}")
            return Portfolio(**data) if data else None
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise e
    
    @strawberry.field
    async def risk_assessment(self, user_id: str) -> Optional[RiskAssessment]:
        """Get user risk assessment"""
        try:
            data = await call_service("risk", f"assessment/{user_id}")
            return RiskAssessment(**data) if data else None
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise e
    
    @strawberry.field
    async def market_data(self, symbols: List[str]) -> List[MarketData]:
        """Get real-time market data for symbols"""
        data = await call_service("trading", f"market-data", "POST", {"symbols": symbols})
        return [MarketData(**item) for item in data.get("market_data", [])]

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_trade(self, trade_input: TradeInput, user_id: str) -> Trade:
        """Create a new trade"""
        trade_data = {
            "symbol": trade_input.symbol,
            "side": trade_input.side,
            "quantity": trade_input.quantity,
            "order_type": trade_input.order_type,
            "price": trade_input.price,
            "user_id": user_id
        }
        
        data = await call_service("trading", "trades", "POST", trade_data)
        return Trade(**data)
    
    @strawberry.mutation
    async def create_strategy(self, strategy_input: StrategyInput, user_id: str) -> Strategy:
        """Create a new trading strategy"""
        strategy_data = {
            "name": strategy_input.name,
            "description": strategy_input.description,
            "config": strategy_input.config,
            "user_id": user_id
        }
        
        data = await call_service("strategy", "strategies", "POST", strategy_data)
        return Strategy(**data)
    
    @strawberry.mutation
    async def create_workflow(self, workflow_input: WorkflowInput, user_id: str) -> NoCodeWorkflow:
        """Create a new no-code workflow"""
        workflow_data = {
            "name": workflow_input.name,
            "description": workflow_input.description,
            "workflow_data": workflow_input.workflow_data,
            "user_id": user_id
        }
        
        data = await call_service("nocode", "workflows", "POST", workflow_data)
        return NoCodeWorkflow(**data)
    
    @strawberry.mutation
    async def execute_workflow(self, workflow_id: str, user_id: str) -> bool:
        """Execute a no-code workflow"""
        data = await call_service("nocode", f"workflows/{workflow_id}/execute", "POST", {"user_id": user_id})
        return data.get("success", False)

# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# FastAPI application
app = FastAPI(
    title="Alphintra GraphQL Gateway",
    description="Unified GraphQL API for Alphintra Trading Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# GraphQL router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    global http_client, redis_client
    
    # Initialize HTTP client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
    )
    
    # Initialize Redis client
    try:
        redis_client = redis.from_url(REDIS_URL)
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None
    
    logger.info("GraphQL Gateway started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections on shutdown"""
    global http_client, redis_client
    
    if http_client:
        await http_client.aclose()
    
    if redis_client:
        await redis_client.close()
    
    logger.info("GraphQL Gateway shutdown complete")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": list(SERVICES.keys())
    }

# Service status endpoint
@app.get("/status")
async def service_status():
    """Check status of all downstream services"""
    statuses = {}
    
    async def check_service(name: str, url: str):
        try:
            async with http_client.get(f"{url}/health", timeout=5.0) as response:
                statuses[name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
                }
        except Exception as e:
            statuses[name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Check all services concurrently
    await asyncio.gather(*[check_service(name, url) for name, url in SERVICES.items()])
    
    return {
        "gateway_status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": statuses
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")