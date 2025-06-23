import asyncio
import json
import logging
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import math

import asyncpg
import redis.asyncio as redis
from kafka import KafkaConsumer, KafkaProducer
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra:alphintra@localhost:5432/alphintra")
TIMESCALE_URL = os.getenv("TIMESCALE_URL", "postgresql://tsuser:tspass@localhost:5433/alphintra_ts")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SIMULATOR_PORT = int(os.getenv("SIMULATOR_PORT", "8006"))

# Global connections
db_pool = None
ts_pool = None
redis_client = None
kafka_consumer = None
kafka_producer = None

# FastAPI app
app = FastAPI(title="alphintra Broker Simulator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class SimulatedOrder:
    order_id: str
    user_id: int
    account_id: int
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    average_price: Optional[float] = None
    created_at: datetime = None
    updated_at: datetime = None
    fees: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.remaining_quantity == 0.0:
            self.remaining_quantity = self.quantity

@dataclass
class MarketData:
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: datetime
    volatility: float = 0.02  # 2% default volatility

class BrokerSimulator:
    """Simulates a cryptocurrency exchange for testing"""
    
    def __init__(self):
        self.orders: Dict[str, SimulatedOrder] = {}
        self.market_data: Dict[str, MarketData] = {}
        self.account_balances: Dict[int, Dict[str, float]] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.running = False
        
        # Initialize market data for popular trading pairs
        self.initialize_market_data()
        
        # Simulation parameters
        self.maker_fee = 0.001  # 0.1%
        self.taker_fee = 0.001  # 0.1%
        self.slippage_factor = 0.0005  # 0.05% slippage
        self.latency_ms = random.randint(10, 100)  # Simulated latency
        
    def initialize_market_data(self):
        """Initialize market data for popular trading pairs"""
        initial_prices = {
            'BTCUSDT': 45000.0,
            'ETHUSDT': 3000.0,
            'ADAUSDT': 0.5,
            'DOTUSDT': 8.0,
            'LINKUSDT': 15.0,
            'BNBUSDT': 300.0,
            'SOLUSDT': 100.0,
            'MATICUSDT': 1.0,
            'AVAXUSDT': 40.0,
            'ATOMUSDT': 12.0
        }
        
        for symbol, price in initial_prices.items():
            spread = price * 0.001  # 0.1% spread
            self.market_data[symbol] = MarketData(
                symbol=symbol,
                price=price,
                bid=price - spread/2,
                ask=price + spread/2,
                volume=random.uniform(1000000, 10000000),
                timestamp=datetime.utcnow(),
                volatility=random.uniform(0.01, 0.05)
            )
    
    async def initialize_account_balance(self, user_id: int, account_id: int):
        """Initialize account balance for simulation"""
        if account_id not in self.account_balances:
            # Give users some initial balance for testing
            self.account_balances[account_id] = {
                'USDT': 10000.0,  # $10,000 USDT
                'BTC': 0.1,       # 0.1 BTC
                'ETH': 1.0,       # 1 ETH
                'ADA': 1000.0,    # 1000 ADA
                'DOT': 100.0,     # 100 DOT
                'LINK': 50.0,     # 50 LINK
                'BNB': 10.0,      # 10 BNB
                'SOL': 20.0,      # 20 SOL
                'MATIC': 1000.0,  # 1000 MATIC
                'AVAX': 25.0,     # 25 AVAX
                'ATOM': 100.0     # 100 ATOM
            }
            
            logger.info(f"Initialized balance for account {account_id}")
    
    async def place_order(self, order_data: Dict[str, Any]) -> SimulatedOrder:
        """Place a simulated order"""
        try:
            # Simulate network latency
            await asyncio.sleep(self.latency_ms / 1000)
            
            # Create order
            order = SimulatedOrder(
                order_id=str(uuid.uuid4()),
                user_id=order_data['user_id'],
                account_id=order_data['account_id'],
                symbol=order_data['symbol'],
                side=OrderSide(order_data['side']),
                order_type=OrderType(order_data['order_type']),
                quantity=order_data['quantity'],
                price=order_data.get('price'),
                stop_price=order_data.get('stop_price'),
                status=OrderStatus.PENDING
            )
            
            # Initialize account balance if needed
            await self.initialize_account_balance(order.user_id, order.account_id)
            
            # Validate order
            if not await self.validate_order(order):
                order.status = OrderStatus.REJECTED
                self.orders[order.order_id] = order
                return order
            
            # Store order
            self.orders[order.order_id] = order
            
            # Process order based on type
            if order.order_type == OrderType.MARKET:
                await self.execute_market_order(order)
            else:
                order.status = OrderStatus.OPEN
                await self.check_limit_order_execution(order)
            
            # Update database
            await self.update_order_in_database(order)
            
            # Publish order update
            await self.publish_order_update(order)
            
            logger.info(f"Order placed: {order.order_id} - {order.symbol} {order.side.value} {order.quantity}")
            
            return order
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def validate_order(self, order: SimulatedOrder) -> bool:
        """Validate order parameters and account balance"""
        try:
            # Check if symbol exists
            if order.symbol not in self.market_data:
                logger.error(f"Invalid symbol: {order.symbol}")
                return False
            
            # Check minimum quantity
            if order.quantity <= 0:
                logger.error(f"Invalid quantity: {order.quantity}")
                return False
            
            # Check account balance
            balance = self.account_balances.get(order.account_id, {})
            
            if order.side == OrderSide.BUY:
                # Check USDT balance for buy orders
                required_amount = order.quantity * (order.price or self.market_data[order.symbol].ask)
                if balance.get('USDT', 0) < required_amount:
                    logger.error(f"Insufficient USDT balance: {balance.get('USDT', 0)} < {required_amount}")
                    return False
            else:
                # Check asset balance for sell orders
                base_asset = order.symbol.replace('USDT', '')
                if balance.get(base_asset, 0) < order.quantity:
                    logger.error(f"Insufficient {base_asset} balance: {balance.get(base_asset, 0)} < {order.quantity}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating order: {e}")
            return False
    
    async def execute_market_order(self, order: SimulatedOrder):
        """Execute market order immediately"""
        try:
            market_data = self.market_data[order.symbol]
            
            # Determine execution price with slippage
            if order.side == OrderSide.BUY:
                base_price = market_data.ask
                slippage = base_price * self.slippage_factor * random.uniform(0.5, 1.5)
                execution_price = base_price + slippage
            else:
                base_price = market_data.bid
                slippage = base_price * self.slippage_factor * random.uniform(0.5, 1.5)
                execution_price = base_price - slippage
            
            # Simulate partial fills for large orders
            if order.quantity * execution_price > 50000:  # Large order threshold
                # Fill 70-90% immediately
                fill_percentage = random.uniform(0.7, 0.9)
                filled_quantity = order.quantity * fill_percentage
                order.status = OrderStatus.PARTIALLY_FILLED
            else:
                filled_quantity = order.quantity
                order.status = OrderStatus.FILLED
            
            # Update order
            order.filled_quantity = filled_quantity
            order.remaining_quantity = order.quantity - filled_quantity
            order.average_price = execution_price
            order.updated_at = datetime.utcnow()
            
            # Calculate fees
            order.fees = filled_quantity * execution_price * self.taker_fee
            
            # Update account balance
            await self.update_account_balance(order, filled_quantity, execution_price)
            
            # Create trade record
            await self.create_trade_record(order, filled_quantity, execution_price)
            
            logger.info(f"Market order executed: {order.order_id} - {filled_quantity} @ {execution_price}")
            
        except Exception as e:
            logger.error(f"Error executing market order: {e}")
            order.status = OrderStatus.REJECTED
    
    async def check_limit_order_execution(self, order: SimulatedOrder):
        """Check if limit order can be executed"""
        try:
            if order.status != OrderStatus.OPEN:
                return
            
            market_data = self.market_data[order.symbol]
            
            # Check if limit order can be executed
            can_execute = False
            
            if order.side == OrderSide.BUY and order.price >= market_data.ask:
                can_execute = True
                execution_price = min(order.price, market_data.ask)
            elif order.side == OrderSide.SELL and order.price <= market_data.bid:
                can_execute = True
                execution_price = max(order.price, market_data.bid)
            
            if can_execute:
                # Simulate execution probability (90% chance)
                if random.random() < 0.9:
                    # Execute order
                    filled_quantity = order.remaining_quantity
                    
                    order.filled_quantity += filled_quantity
                    order.remaining_quantity = 0
                    order.status = OrderStatus.FILLED
                    order.average_price = execution_price
                    order.updated_at = datetime.utcnow()
                    
                    # Calculate fees (maker fee for limit orders)
                    order.fees = filled_quantity * execution_price * self.maker_fee
                    
                    # Update account balance
                    await self.update_account_balance(order, filled_quantity, execution_price)
                    
                    # Create trade record
                    await self.create_trade_record(order, filled_quantity, execution_price)
                    
                    # Publish order update
                    await self.publish_order_update(order)
                    
                    logger.info(f"Limit order executed: {order.order_id} - {filled_quantity} @ {execution_price}")
            
        except Exception as e:
            logger.error(f"Error checking limit order execution: {e}")
    
    async def update_account_balance(self, order: SimulatedOrder, filled_quantity: float, execution_price: float):
        """Update account balance after trade execution"""
        try:
            balance = self.account_balances[order.account_id]
            base_asset = order.symbol.replace('USDT', '')
            
            if order.side == OrderSide.BUY:
                # Deduct USDT, add base asset
                total_cost = filled_quantity * execution_price + order.fees
                balance['USDT'] -= total_cost
                balance[base_asset] = balance.get(base_asset, 0) + filled_quantity
            else:
                # Deduct base asset, add USDT
                total_received = filled_quantity * execution_price - order.fees
                balance[base_asset] -= filled_quantity
                balance['USDT'] = balance.get('USDT', 0) + total_received
            
            # Update balance in Redis
            await redis_client.setex(
                f"balance:simulator:{order.account_id}",
                300,  # 5 minutes TTL
                json.dumps(balance, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
    
    async def create_trade_record(self, order: SimulatedOrder, filled_quantity: float, execution_price: float):
        """Create trade record"""
        try:
            trade = {
                'trade_id': str(uuid.uuid4()),
                'order_id': order.order_id,
                'user_id': order.user_id,
                'account_id': order.account_id,
                'symbol': order.symbol,
                'side': order.side.value,
                'quantity': filled_quantity,
                'price': execution_price,
                'fees': order.fees,
                'timestamp': datetime.utcnow(),
                'exchange': 'simulator'
            }
            
            self.trade_history.append(trade)
            
            # Store in database
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO trades (trade_id, user_id, account_id, symbol, side, 
                                      quantity, price, fees, status, exchange, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'filled', 'simulator', NOW())
                    ON CONFLICT (trade_id) DO NOTHING
                    """,
                    trade['trade_id'], trade['user_id'], trade['account_id'],
                    trade['symbol'], trade['side'], trade['quantity'],
                    trade['price'], trade['fees']
                )
            
            # Publish trade event
            kafka_producer.send('trade-executed', trade)
            
        except Exception as e:
            logger.error(f"Error creating trade record: {e}")
    
    async def update_order_in_database(self, order: SimulatedOrder):
        """Update order in database"""
        try:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO trades (trade_id, user_id, account_id, symbol, side, order_type,
                                      quantity, price, filled_quantity, remaining_quantity,
                                      average_price, status, fees, exchange, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'simulator', $14, $15)
                    ON CONFLICT (trade_id) DO UPDATE SET
                        filled_quantity = EXCLUDED.filled_quantity,
                        remaining_quantity = EXCLUDED.remaining_quantity,
                        average_price = EXCLUDED.average_price,
                        status = EXCLUDED.status,
                        fees = EXCLUDED.fees,
                        updated_at = EXCLUDED.updated_at
                    """,
                    order.order_id, order.user_id, order.account_id, order.symbol,
                    order.side.value, order.order_type.value, order.quantity,
                    order.price, order.filled_quantity, order.remaining_quantity,
                    order.average_price, order.status.value, order.fees,
                    order.created_at, order.updated_at
                )
        except Exception as e:
            logger.error(f"Error updating order in database: {e}")
    
    async def publish_order_update(self, order: SimulatedOrder):
        """Publish order update to Kafka"""
        try:
            order_update = {
                'order_id': order.order_id,
                'user_id': order.user_id,
                'account_id': order.account_id,
                'symbol': order.symbol,
                'side': order.side.value,
                'order_type': order.order_type.value,
                'quantity': order.quantity,
                'filled_quantity': order.filled_quantity,
                'remaining_quantity': order.remaining_quantity,
                'price': order.price,
                'average_price': order.average_price,
                'status': order.status.value,
                'fees': order.fees,
                'exchange': 'simulator',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            kafka_producer.send('order-updates', order_update)
            
        except Exception as e:
            logger.error(f"Error publishing order update: {e}")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            if order_id not in self.orders:
                return False
            
            order = self.orders[order_id]
            
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                return False
            
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.utcnow()
            
            # Update database
            await self.update_order_in_database(order)
            
            # Publish order update
            await self.publish_order_update(order)
            
            logger.info(f"Order cancelled: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[SimulatedOrder]:
        """Get order status"""
        return self.orders.get(order_id)
    
    async def get_account_balance(self, account_id: int) -> Dict[str, float]:
        """Get account balance"""
        await self.initialize_account_balance(0, account_id)  # Ensure balance exists
        return self.account_balances.get(account_id, {})
    
    async def update_market_data(self):
        """Update market data with random price movements"""
        try:
            for symbol, data in self.market_data.items():
                # Generate random price movement
                price_change_pct = np.random.normal(0, data.volatility)
                new_price = data.price * (1 + price_change_pct)
                
                # Ensure price doesn't go negative
                new_price = max(new_price, data.price * 0.5)
                
                # Update market data
                spread = new_price * 0.001
                data.price = new_price
                data.bid = new_price - spread/2
                data.ask = new_price + spread/2
                data.volume = random.uniform(1000000, 10000000)
                data.timestamp = datetime.utcnow()
                
                # Store in TimescaleDB
                await self.store_market_data(data)
                
                # Publish market data update
                market_update = {
                    'symbol': symbol,
                    'price': new_price,
                    'bid': data.bid,
                    'ask': data.ask,
                    'volume': data.volume,
                    'timestamp': data.timestamp.isoformat(),
                    'exchange': 'simulator'
                }
                
                kafka_producer.send('market-data-ticker', market_update)
            
            # Check limit orders for execution
            for order in self.orders.values():
                if order.status == OrderStatus.OPEN:
                    await self.check_limit_order_execution(order)
            
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    
    async def store_market_data(self, data: MarketData):
        """Store market data in TimescaleDB"""
        try:
            async with ts_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO market_data (time, exchange, symbol, timeframe, open_price,
                                           high_price, low_price, close_price, volume, trades)
                    VALUES ($1, 'simulator', $2, '1m', $3, $4, $5, $6, $7, 1)
                    ON CONFLICT (time, exchange, symbol, timeframe) DO UPDATE SET
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume
                    """,
                    data.timestamp, data.symbol, data.price, data.price,
                    data.price, data.price, data.volume
                )
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
    
    async def run_simulation(self):
        """Main simulation loop"""
        self.running = True
        logger.info("Broker simulator started")
        
        while self.running:
            try:
                # Update market data every 5 seconds
                await self.update_market_data()
                
                # Process Kafka messages
                await self.process_kafka_messages()
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(1)
    
    async def process_kafka_messages(self):
        """Process incoming Kafka messages"""
        try:
            message_batch = kafka_consumer.poll(timeout_ms=100)
            
            for topic_partition, messages in message_batch.items():
                for message in messages:
                    if message.topic == 'trade-execution':
                        await self.place_order(message.value)
                    elif message.topic == 'order-management':
                        await self.handle_order_management(message.value)
        
        except Exception as e:
            logger.error(f"Error processing Kafka messages: {e}")
    
    async def handle_order_management(self, order_data: Dict[str, Any]):
        """Handle order management requests"""
        try:
            action = order_data.get('action')
            
            if action == 'cancel':
                await self.cancel_order(order_data['order_id'])
            elif action == 'status':
                order = await self.get_order_status(order_data['order_id'])
                if order:
                    await self.publish_order_update(order)
        
        except Exception as e:
            logger.error(f"Error handling order management: {e}")
    
    def stop_simulation(self):
        """Stop simulation"""
        self.running = False
        logger.info("Broker simulator stopped")

# Global simulator instance
simulator = BrokerSimulator()

# API Models
class OrderRequest(BaseModel):
    user_id: int
    account_id: int
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None

class OrderResponse(BaseModel):
    order_id: str
    status: str
    message: str

# API Endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/orders", response_model=OrderResponse)
async def place_order(order_request: OrderRequest):
    """Place a simulated order"""
    try:
        order = await simulator.place_order(order_request.dict())
        return OrderResponse(
            order_id=order.order_id,
            status=order.status.value,
            message="Order placed successfully"
        )
    except Exception as e:
        logger.error(f"Error placing order via API: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order"""
    try:
        success = await simulator.cancel_order(order_id)
        if success:
            return {"message": "Order cancelled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Order not found or cannot be cancelled")
    except Exception as e:
        logger.error(f"Error cancelling order via API: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders/{order_id}")
async def get_order_status(order_id: str):
    """Get order status"""
    try:
        order = await simulator.get_order_status(order_id)
        if order:
            return asdict(order)
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    except Exception as e:
        logger.error(f"Error getting order status via API: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/balance/{account_id}")
async def get_account_balance(account_id: int):
    """Get account balance"""
    try:
        balance = await simulator.get_account_balance(account_id)
        return {"account_id": account_id, "balance": balance}
    except Exception as e:
        logger.error(f"Error getting balance via API: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/market-data")
async def get_market_data():
    """Get current market data"""
    try:
        market_data = {}
        for symbol, data in simulator.market_data.items():
            market_data[symbol] = {
                'price': data.price,
                'bid': data.bid,
                'ask': data.ask,
                'volume': data.volume,
                'timestamp': data.timestamp.isoformat()
            }
        return market_data
    except Exception as e:
        logger.error(f"Error getting market data via API: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/market-data/{symbol}")
async def get_symbol_market_data(symbol: str):
    """Get market data for specific symbol"""
    try:
        if symbol not in simulator.market_data:
            raise HTTPException(status_code=404, detail="Symbol not found")
        
        data = simulator.market_data[symbol]
        return {
            'symbol': symbol,
            'price': data.price,
            'bid': data.bid,
            'ask': data.ask,
            'volume': data.volume,
            'timestamp': data.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting symbol market data via API: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/trades/{account_id}")
async def get_trade_history(account_id: int, limit: int = 100):
    """Get trade history for account"""
    try:
        trades = [
            trade for trade in simulator.trade_history
            if trade['account_id'] == account_id
        ][-limit:]
        
        return {"account_id": account_id, "trades": trades}
    except Exception as e:
        logger.error(f"Error getting trade history via API: {e}")
        raise HTTPException(status_code=400, detail=str(e))

async def initialize_connections():
    """Initialize database and messaging connections"""
    global db_pool, ts_pool, redis_client, kafka_consumer, kafka_producer
    
    try:
        # Initialize database connections
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
        ts_pool = await asyncpg.create_pool(TIMESCALE_URL, min_size=3, max_size=10)
        
        # Initialize Redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Initialize Kafka
        kafka_consumer = KafkaConsumer(
            'trade-execution',
            'order-management',
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='broker-simulator'
        )
        
        kafka_producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        
        logger.info("Broker simulator connections initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    await initialize_connections()
    
    # Start simulation in background
    asyncio.create_task(simulator.run_simulation())
    
    logger.info("Broker simulator started")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    simulator.stop_simulation()
    
    # Cleanup connections
    if db_pool:
        await db_pool.close()
    if ts_pool:
        await ts_pool.close()
    if redis_client:
        await redis_client.close()
    if kafka_producer:
        kafka_producer.close()
    
    logger.info("Broker simulator stopped")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SIMULATOR_PORT,
        reload=True,
        log_level="info"
    )