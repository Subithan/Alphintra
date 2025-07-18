"""
GraphQL Gateway Service - Unified API Layer
Provides a single GraphQL endpoint that federates all microservices with comprehensive security
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from typing import List, Optional, Dict, Any
import httpx
import asyncio
import os
import logging
from datetime import datetime
import redis.asyncio as redis
from prometheus_fastapi_instrumentator import Instrumentator
from security_middleware import (
    GraphQLSecurityMiddleware, 
    get_current_user, 
    require_role, 
    require_permission, 
    require_user_access,
    init_graphql_security,
    get_context,
    UserContext
)

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
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

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
    performance_metrics: Optional[str] = None  # JSON string

@strawberry.type
class NoCodeWorkflow:
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    workflow_data: str  # JSON string
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
    positions: str  # JSON string of positions list
    performance: str  # JSON string of performance metrics
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
    config: str  # JSON string

@strawberry.input
class WorkflowInput:
    name: str
    description: Optional[str] = None
    workflow_data: str  # JSON string

# Service Communication Helper
async def call_service(service_name: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None, user_context: Optional[UserContext] = None) -> Dict[str, Any]:
    """Make HTTP calls to microservices with error handling, caching, and security headers"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
    
    url = f"{SERVICES[service_name]}/{endpoint.lstrip('/')}"
    cache_key = f"gql_cache:{service_name}:{endpoint}:{method}:{user_context.id if user_context else 'anonymous'}"
    
    # Prepare headers for microservice communication
    headers = {
        "x-gateway-routed": "true",
        "x-service-type": "graphql",
        "x-internal-service-token": os.getenv('INTERNAL_SERVICE_TOKEN', 'alphintra-internal-token-2024')
    }
    
    # Add user context headers if available
    if user_context:
        headers.update({
            "x-user-id": user_context.id,
            "x-user-roles": ",".join(user_context.roles),
            "x-user-permissions": ",".join(user_context.permissions)
        })
    
    try:
        # Try cache for GET requests (only for non-sensitive data)
        if method == "GET" and redis_client and not data:
            cached = await redis_client.get(cache_key)
            if cached:
                import json
                return json.loads(cached)
        
        # Make HTTP request with security headers
        async with http_client.request(method, url, json=data, headers=headers, timeout=30.0) as response:
            if response.status_code == 200:
                result = response.json()
                
                # Cache successful GET responses for 2 minutes (shorter for security)
                if method == "GET" and redis_client and not data:
                    import json
                    await redis_client.setex(cache_key, 120, json.dumps(result))
                
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

# GraphQL Resolvers with Security
@strawberry.type
class Query:
    @strawberry.field
    async def users(self, info: Info, limit: Optional[int] = 10) -> List[User]:
        """Get list of users - Admin only"""
        user = get_current_user(info)
        
        # Only admins can list all users
        if not user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="Access denied: Admin role required to list users"
            )
        
        data = await call_service("user", f"users?limit={limit}", user_context=user)
        return [User(**user_data) for user_data in data.get("users", [])]
    
    @strawberry.field
    async def user(self, info: Info, user_id: str) -> Optional[User]:
        """Get user by ID - Own data or Admin only"""
        user = get_current_user(info)
        
        # Users can only access their own data, admins can access any
        if not user.can_access_user_data(user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Cannot access other user's data"
            )
        
        try:
            data = await call_service("user", f"users/{user_id}", user_context=user)
            return User(**data) if data else None
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise e
    
    @strawberry.field
    async def trades(self, info: Info, user_id: Optional[str] = None, symbol: Optional[str] = None, limit: Optional[int] = 20) -> List[Trade]:
        """Get trades with optional filtering - Own trades or Admin"""
        user = get_current_user(info)
        
        # If user_id is specified, validate access
        if user_id and not user.can_access_user_data(user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Cannot access other user's trades"
            )
        
        # If no user_id specified, default to current user (non-admins)
        if not user_id and not user.is_admin:
            user_id = user.id
        
        params = []
        if user_id:
            params.append(f"user_id={user_id}")
        if symbol:
            params.append(f"symbol={symbol}")
        params.append(f"limit={limit}")
        
        query_string = "&".join(params)
        data = await call_service("trading", f"api/v1/trades?{query_string}", user_context=user)
        return [Trade(**trade) for trade in data.get("trades", [])]
    
    @strawberry.field
    async def strategies(self, info: Info, user_id: Optional[str] = None, is_active: Optional[bool] = None) -> List[Strategy]:
        """Get trading strategies - Own strategies or Admin"""
        user = get_current_user(info)
        
        # If user_id is specified, validate access
        if user_id and not user.can_access_user_data(user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Cannot access other user's strategies"
            )
        
        # If no user_id specified, default to current user (non-admins)
        if not user_id and not user.is_admin:
            user_id = user.id
        
        params = []
        if user_id:
            params.append(f"user_id={user_id}")
        if is_active is not None:
            params.append(f"is_active={is_active}")
        
        query_string = "&".join(params)
        data = await call_service("strategy", f"api/v1/strategies?{query_string}", user_context=user)
        return [Strategy(**strategy) for strategy in data.get("strategies", [])]
    
    @strawberry.field
    async def workflows(self, info: Info, user_id: Optional[str] = None) -> List[NoCodeWorkflow]:
        """Get no-code workflows - Own workflows or Admin"""
        user = get_current_user(info)
        
        # If user_id is specified, validate access
        if user_id and not user.can_access_user_data(user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Cannot access other user's workflows"
            )
        
        # If no user_id specified, default to current user (non-admins)
        if not user_id and not user.is_admin:
            user_id = user.id
        
        params = []
        if user_id:
            params.append(f"user_id={user_id}")
        
        query_string = "&".join(params)
        data = await call_service("nocode", f"api/v1/workflows?{query_string}", user_context=user)
        return [NoCodeWorkflow(**workflow) for workflow in data.get("workflows", [])]
    
    @strawberry.field
    async def portfolio(self, info: Info, user_id: str) -> Optional[Portfolio]:
        """Get user portfolio - Own portfolio or Admin"""
        user = get_current_user(info)
        
        # Validate access to user's portfolio
        if not user.can_access_user_data(user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Cannot access other user's portfolio"
            )
        
        try:
            data = await call_service("trading", f"api/v1/portfolio", user_context=user)
            return Portfolio(**data) if data else None
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise e
    
    @strawberry.field
    async def risk_assessment(self, info: Info, user_id: str) -> Optional[RiskAssessment]:
        """Get user risk assessment - Own assessment or Admin"""
        user = get_current_user(info)
        
        # Validate access to user's risk assessment
        if not user.can_access_user_data(user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Cannot access other user's risk assessment"
            )
        
        try:
            data = await call_service("risk", f"api/v1/assessment/{user_id}", user_context=user)
            return RiskAssessment(**data) if data else None
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise e
    
    @strawberry.field
    async def market_data(self, info: Info, symbols: List[str]) -> List[MarketData]:
        """Get real-time market data for symbols - Authenticated users"""
        user = get_current_user(info)
        
        # All authenticated users can access market data
        data = await call_service("trading", f"api/v1/market-data", "POST", {"symbols": symbols}, user_context=user)
        return [MarketData(**item) for item in data.get("market_data", [])]

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_trade(self, info: Info, trade_input: TradeInput) -> Trade:
        """Create a new trade - Authenticated users with TRADER role"""
        user = get_current_user(info)
        
        # Require TRADER role for trading operations
        if not user.has_role("TRADER"):
            raise HTTPException(
                status_code=403,
                detail="Access denied: TRADER role required for trading operations"
            )
        
        trade_data = {
            "symbol": trade_input.symbol,
            "side": trade_input.side,
            "quantity": trade_input.quantity,
            "order_type": trade_input.order_type,
            "price": trade_input.price
        }
        
        data = await call_service("trading", "api/v1/trades", "POST", trade_data, user_context=user)
        return Trade(**data)
    
    @strawberry.mutation
    async def create_strategy(self, info: Info, strategy_input: StrategyInput) -> Strategy:
        """Create a new trading strategy - Authenticated users"""
        user = get_current_user(info)
        
        strategy_data = {
            "name": strategy_input.name,
            "description": strategy_input.description,
            "config": strategy_input.config
        }
        
        data = await call_service("strategy", "api/v1/strategies", "POST", strategy_data, user_context=user)
        return Strategy(**data)
    
    @strawberry.mutation
    async def create_workflow(self, info: Info, workflow_input: WorkflowInput) -> NoCodeWorkflow:
        """Create a new no-code workflow - Authenticated users"""
        user = get_current_user(info)
        
        workflow_data = {
            "name": workflow_input.name,
            "description": workflow_input.description,
            "workflow_data": workflow_input.workflow_data
        }
        
        data = await call_service("nocode", "api/v1/workflows", "POST", workflow_data, user_context=user)
        return NoCodeWorkflow(**data)
    
    @strawberry.mutation
    async def execute_workflow(self, info: Info, workflow_id: str, target_user_id: Optional[str] = None) -> bool:
        """Execute a no-code workflow - Own workflows or Admin"""
        user = get_current_user(info)
        
        # If target_user_id is specified, validate access
        if target_user_id and not user.can_access_user_data(target_user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Cannot execute other user's workflows"
            )
        
        # Use current user if no target specified
        execution_user_id = target_user_id or user.id
        
        data = await call_service("nocode", f"api/v1/workflows/{workflow_id}/execute", "POST", 
                                  {"user_id": execution_user_id}, user_context=user)
        return data.get("success", False)

# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# FastAPI application
app = FastAPI(
    title="Alphintra GraphQL Gateway",
    description="Unified GraphQL API for Alphintra Trading Platform with Security",
    version="1.0.0"
)

# Security middleware (must be added first)
strict_mode = os.getenv('ENVIRONMENT', 'development') != 'development'
app.add_middleware(GraphQLSecurityMiddleware, strict_mode=strict_mode)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize security
init_graphql_security(app)

# Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# GraphQL router with context
graphql_app = GraphQLRouter(schema, context_getter=get_context)
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
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")