from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import asyncpg
import redis.asyncio as redis
from kafka import KafkaProducer
import json
import uuid
from datetime import datetime, timedelta
import logging
import os
from decimal import Decimal
import mlflow
import mlflow.sklearn
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra:alphintra@localhost:5432/alphintra")
TIMESCALE_URL = os.getenv("TIMESCALE_URL", "postgresql://tsuser:tspass@localhost:5433/alphintra_ts")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

# Global connections
db_pool = None
ts_pool = None
redis_client = None
kafka_producer = None

# Pydantic models
class TradeRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., description="buy or sell")
    order_type: str = Field(default="market", description="market, limit, stop, stop_limit")
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, description="Order price for limit orders")
    stop_price: Optional[float] = Field(None, description="Stop price for stop orders")
    strategy_id: Optional[int] = Field(None, description="Associated strategy ID")
    exchange: str = Field(default="binance", description="Target exchange")

class TradeResponse(BaseModel):
    trade_id: str
    status: str
    message: str
    order_details: Optional[Dict[str, Any]] = None

class PortfolioResponse(BaseModel):
    user_id: int
    total_value: float
    available_balance: float
    locked_balance: float
    assets: List[Dict[str, Any]]
    unrealized_pnl: float
    realized_pnl: float

class MarketDataRequest(BaseModel):
    symbol: str
    timeframe: str = Field(default="1m", description="1m, 5m, 15m, 1h, 4h, 1d")
    limit: int = Field(default=100, le=1000, description="Number of candles")
    exchange: str = Field(default="binance")

class TradingSignal(BaseModel):
    strategy_id: int
    symbol: str
    signal_type: str  # buy, sell, hold, close
    strength: float = Field(..., ge=0, le=1)
    price: Optional[float] = None
    quantity: Optional[float] = None
    confidence: float = Field(..., ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = None

class StrategyConfig(BaseModel):
    name: str
    description: Optional[str] = None
    strategy_type: str  # dca, grid, momentum, mean_reversion, arbitrage, ml_based
    config: Dict[str, Any]
    is_active: bool = False
    is_public: bool = False

# Database connection management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool, ts_pool, redis_client, kafka_producer
    
    try:
        # Initialize database connections
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
        ts_pool = await asyncpg.create_pool(TIMESCALE_URL, min_size=3, max_size=10)
        
        # Initialize Redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Initialize Kafka producer
        kafka_producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        
        # Initialize MLflow
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        
        logger.info("All connections initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        if db_pool:
            await db_pool.close()
        if ts_pool:
            await ts_pool.close()
        if redis_client:
            await redis_client.close()
        if kafka_producer:
            kafka_producer.close()
        logger.info("All connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="alphintra Trading API",
    description="Comprehensive trading API for alphintra platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user from JWT token - simplified for demo"""
    # In production, implement proper JWT validation
    token = credentials.credentials
    
    # For demo, extract user_id from token (implement proper JWT validation)
    try:
        # Simplified: assume token format is "user_{user_id}"
        if token.startswith("user_"):
            user_id = int(token.split("_")[1])
            return user_id
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except:
        raise HTTPException(status_code=401, detail="Invalid token format")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Redis connectivity
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {
                "database": "connected",
                "redis": "connected",
                "kafka": "connected" if kafka_producer else "disconnected"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Trading endpoints
@app.post("/api/v1/trades", response_model=TradeResponse)
async def create_trade(
    trade_request: TradeRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user)
):
    """Create a new trade order"""
    try:
        trade_id = str(uuid.uuid4())
        
        # Get user's trading account
        async with db_pool.acquire() as conn:
            account = await conn.fetchrow(
                "SELECT * FROM user_accounts WHERE user_id = $1 AND account_type = 'spot' AND is_active = true LIMIT 1",
                user_id
            )
            
            if not account:
                raise HTTPException(status_code=404, detail="No active trading account found")
            
            # Check available balance for buy orders
            if trade_request.side.lower() == "buy":
                required_amount = trade_request.quantity * (trade_request.price or 0)
                if account['available_balance'] < required_amount:
                    raise HTTPException(status_code=400, detail="Insufficient balance")
            
            # Insert trade record
            await conn.execute(
                """
                INSERT INTO trades (trade_id, user_id, account_id, strategy_id, exchange, symbol, 
                                  side, order_type, quantity, price, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'pending')
                """,
                trade_id, user_id, account['id'], trade_request.strategy_id,
                trade_request.exchange, trade_request.symbol, trade_request.side,
                trade_request.order_type, trade_request.quantity, trade_request.price
            )
        
        # Send to Kafka for processing
        trade_event = {
            "trade_id": trade_id,
            "user_id": user_id,
            "account_id": account['id'],
            "symbol": trade_request.symbol,
            "side": trade_request.side,
            "order_type": trade_request.order_type,
            "quantity": trade_request.quantity,
            "price": trade_request.price,
            "exchange": trade_request.exchange,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        kafka_producer.send('trade-execution', trade_event)
        
        # Cache trade in Redis for quick access
        await redis_client.setex(
            f"trade:{trade_id}",
            3600,  # 1 hour TTL
            json.dumps(trade_event, default=str)
        )
        
        # Add background task for risk checking
        background_tasks.add_task(check_trade_risk, trade_id, user_id)
        
        return TradeResponse(
            trade_id=trade_id,
            status="pending",
            message="Trade order created successfully",
            order_details=trade_event
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating trade: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/trades/{trade_id}")
async def get_trade(trade_id: str, user_id: int = Depends(get_current_user)):
    """Get trade details by ID"""
    try:
        # Try Redis cache first
        cached_trade = await redis_client.get(f"trade:{trade_id}")
        if cached_trade:
            return json.loads(cached_trade)
        
        # Fallback to database
        async with db_pool.acquire() as conn:
            trade = await conn.fetchrow(
                "SELECT * FROM trades WHERE trade_id = $1 AND user_id = $2",
                trade_id, user_id
            )
            
            if not trade:
                raise HTTPException(status_code=404, detail="Trade not found")
            
            return dict(trade)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trade: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/trades", response_model=List[Dict[str, Any]])
async def get_user_trades(
    user_id: int = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    symbol: Optional[str] = None,
    status: Optional[str] = None
):
    """Get user's trading history"""
    try:
        query = "SELECT * FROM trades WHERE user_id = $1"
        params = [user_id]
        param_count = 1
        
        if symbol:
            param_count += 1
            query += f" AND symbol = ${param_count}"
            params.append(symbol)
        
        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)
        
        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])
        
        async with db_pool.acquire() as conn:
            trades = await conn.fetch(query, *params)
            return [dict(trade) for trade in trades]
            
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Portfolio endpoints
@app.get("/api/v1/portfolio", response_model=PortfolioResponse)
async def get_portfolio(user_id: int = Depends(get_current_user)):
    """Get user's portfolio summary"""
    try:
        async with db_pool.acquire() as conn:
            # Get user accounts
            accounts = await conn.fetch(
                "SELECT * FROM user_accounts WHERE user_id = $1 AND is_active = true",
                user_id
            )
            
            if not accounts:
                raise HTTPException(status_code=404, detail="No active accounts found")
            
            total_value = 0
            available_balance = 0
            locked_balance = 0
            assets = []
            
            for account in accounts:
                # Get asset balances for this account
                balances = await conn.fetch(
                    "SELECT * FROM asset_balances WHERE account_id = $1",
                    account['id']
                )
                
                for balance in balances:
                    total_value += float(balance['total_balance'])
                    available_balance += float(balance['available_balance'])
                    locked_balance += float(balance['locked_balance'])
                    
                    assets.append({
                        "asset": balance['asset'],
                        "total_balance": float(balance['total_balance']),
                        "available_balance": float(balance['available_balance']),
                        "locked_balance": float(balance['locked_balance'])
                    })
            
            # Get latest portfolio metrics from TimescaleDB
            unrealized_pnl = 0
            realized_pnl = 0
            
            async with ts_pool.acquire() as ts_conn:
                latest_metrics = await ts_conn.fetchrow(
                    """
                    SELECT unrealized_pnl, realized_pnl 
                    FROM portfolio_metrics 
                    WHERE user_id = $1 
                    ORDER BY time DESC 
                    LIMIT 1
                    """,
                    user_id
                )
                
                if latest_metrics:
                    unrealized_pnl = float(latest_metrics['unrealized_pnl'] or 0)
                    realized_pnl = float(latest_metrics['realized_pnl'] or 0)
            
            return PortfolioResponse(
                user_id=user_id,
                total_value=total_value,
                available_balance=available_balance,
                locked_balance=locked_balance,
                assets=assets,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Market data endpoints
@app.post("/api/v1/market-data")
async def get_market_data(request: MarketDataRequest):
    """Get historical market data"""
    try:
        async with ts_pool.acquire() as conn:
            market_data = await conn.fetch(
                """
                SELECT time, open_price, high_price, low_price, close_price, volume
                FROM market_data
                WHERE symbol = $1 AND timeframe = $2 AND exchange = $3
                ORDER BY time DESC
                LIMIT $4
                """,
                request.symbol, request.timeframe, request.exchange, request.limit
            )
            
            return {
                "symbol": request.symbol,
                "timeframe": request.timeframe,
                "data": [
                    {
                        "timestamp": row['time'].isoformat(),
                        "open": float(row['open_price']),
                        "high": float(row['high_price']),
                        "low": float(row['low_price']),
                        "close": float(row['close_price']),
                        "volume": float(row['volume'])
                    }
                    for row in reversed(market_data)
                ]
            }
            
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Trading signals endpoints
@app.post("/api/v1/signals")
async def create_trading_signal(
    signal: TradingSignal,
    user_id: int = Depends(get_current_user)
):
    """Create a new trading signal"""
    try:
        async with ts_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO trading_signals (time, strategy_id, symbol, signal_type, 
                                           strength, price, quantity, confidence, metadata)
                VALUES (NOW(), $1, $2, $3, $4, $5, $6, $7, $8)
                """,
                signal.strategy_id, signal.symbol, signal.signal_type,
                signal.strength, signal.price, signal.quantity,
                signal.confidence, json.dumps(signal.metadata) if signal.metadata else None
            )
        
        # Send signal to Kafka
        signal_event = {
            "strategy_id": signal.strategy_id,
            "symbol": signal.symbol,
            "signal_type": signal.signal_type,
            "strength": signal.strength,
            "price": signal.price,
            "quantity": signal.quantity,
            "confidence": signal.confidence,
            "metadata": signal.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        kafka_producer.send('strategy-signals', signal_event)
        
        return {"message": "Trading signal created successfully", "signal": signal_event}
        
    except Exception as e:
        logger.error(f"Error creating trading signal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/signals/{strategy_id}")
async def get_strategy_signals(
    strategy_id: int,
    user_id: int = Depends(get_current_user),
    limit: int = 100
):
    """Get trading signals for a strategy"""
    try:
        async with ts_pool.acquire() as conn:
            signals = await conn.fetch(
                """
                SELECT * FROM trading_signals
                WHERE strategy_id = $1
                ORDER BY time DESC
                LIMIT $2
                """,
                strategy_id, limit
            )
            
            return {
                "strategy_id": strategy_id,
                "signals": [
                    {
                        "timestamp": signal['time'].isoformat(),
                        "symbol": signal['symbol'],
                        "signal_type": signal['signal_type'],
                        "strength": float(signal['strength']),
                        "price": float(signal['price']) if signal['price'] else None,
                        "quantity": float(signal['quantity']) if signal['quantity'] else None,
                        "confidence": float(signal['confidence']),
                        "metadata": json.loads(signal['metadata']) if signal['metadata'] else None,
                        "processed": signal['processed']
                    }
                    for signal in signals
                ]
            }
            
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Strategy management endpoints
@app.post("/api/v1/strategies")
async def create_strategy(
    strategy: StrategyConfig,
    user_id: int = Depends(get_current_user)
):
    """Create a new trading strategy"""
    try:
        async with db_pool.acquire() as conn:
            strategy_id = await conn.fetchval(
                """
                INSERT INTO trading_strategies (user_id, name, description, strategy_type, config, is_active, is_public)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                user_id, strategy.name, strategy.description, strategy.strategy_type,
                json.dumps(strategy.config), strategy.is_active, strategy.is_public
            )
            
            return {
                "strategy_id": strategy_id,
                "message": "Strategy created successfully",
                "strategy": strategy.dict()
            }
            
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/strategies")
async def get_user_strategies(user_id: int = Depends(get_current_user)):
    """Get user's trading strategies"""
    try:
        async with db_pool.acquire() as conn:
            strategies = await conn.fetch(
                "SELECT * FROM trading_strategies WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            
            return {
                "strategies": [
                    {
                        "id": strategy['id'],
                        "uuid": str(strategy['uuid']),
                        "name": strategy['name'],
                        "description": strategy['description'],
                        "strategy_type": strategy['strategy_type'],
                        "config": json.loads(strategy['config']),
                        "is_active": strategy['is_active'],
                        "is_public": strategy['is_public'],
                        "created_at": strategy['created_at'].isoformat(),
                        "updated_at": strategy['updated_at'].isoformat()
                    }
                    for strategy in strategies
                ]
            }
            
    except Exception as e:
        logger.error(f"Error fetching strategies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Background tasks
async def check_trade_risk(trade_id: str, user_id: int):
    """Background task to check trade risk"""
    try:
        # Implement risk checking logic
        logger.info(f"Checking risk for trade {trade_id} by user {user_id}")
        
        # Example: Check if trade exceeds daily limit
        async with db_pool.acquire() as conn:
            daily_volume = await conn.fetchval(
                """
                SELECT COALESCE(SUM(quantity * COALESCE(average_price, price)), 0)
                FROM trades
                WHERE user_id = $1 AND created_at >= CURRENT_DATE
                """,
                user_id
            )
            
            # Example risk limit: $10,000 per day
            if daily_volume > 10000:
                # Send risk alert
                risk_alert = {
                    "user_id": user_id,
                    "trade_id": trade_id,
                    "alert_type": "daily_limit_exceeded",
                    "daily_volume": float(daily_volume),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                kafka_producer.send('risk-alerts', risk_alert)
                logger.warning(f"Daily trading limit exceeded for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in risk checking: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)