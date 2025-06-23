"""
High-Frequency Trading (HFT) Engine
Alphintra Trading Platform - Phase 4
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
import asyncio
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
import uuid
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import heapq
from collections import defaultdict, deque

# Async libraries
import aioredis
import aiohttp
import asyncpg

# Low-latency networking
import uvloop
import zmq
import zmq.asyncio

# Mathematical libraries
import numba
from numba import jit, cuda
import cupy as cp  # GPU acceleration

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    IOC = "immediate_or_cancel"
    FOK = "fill_or_kill"


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class StrategyType(Enum):
    """HFT strategy type enumeration"""
    MARKET_MAKING = "market_making"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    LIQUIDATION = "liquidation"
    NEWS_REACTION = "news_reaction"


@dataclass
class MarketData:
    """Real-time market data structure"""
    symbol: str
    timestamp: int  # nanoseconds
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    last_price: float
    last_size: float
    volume: float
    vwap: float
    
    @property
    def spread(self) -> float:
        return self.ask_price - self.bid_price
    
    @property
    def mid_price(self) -> float:
        return (self.bid_price + self.ask_price) / 2


@dataclass
class Order:
    """Order data structure"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    timestamp: int = 0  # nanoseconds
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    avg_fill_price: float = 0.0
    strategy_id: str = ""
    client_order_id: str = ""
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time_ns()
        if self.remaining_quantity == 0.0:
            self.remaining_quantity = self.quantity


@dataclass
class Trade:
    """Trade execution data structure"""
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: int
    commission: float
    strategy_id: str


@dataclass
class StrategyConfig:
    """HFT strategy configuration"""
    strategy_id: str
    strategy_type: StrategyType
    symbols: List[str]
    enabled: bool = True
    max_position: float = 1000000
    max_order_size: float = 10000
    risk_limits: Dict[str, float] = None
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.risk_limits is None:
            self.risk_limits = {}
        if self.parameters is None:
            self.parameters = {}


class LatencyOptimizer:
    """
    Ultra-low latency optimization components
    """
    
    def __init__(self):
        self.cpu_affinity = None
        self.memory_pool = None
        self.optimized_functions = {}
        
    @staticmethod
    @jit(nopython=True, cache=True)
    def calculate_spread_ratio(bid: float, ask: float) -> float:
        """Calculate bid-ask spread ratio (JIT compiled)"""
        mid = (bid + ask) * 0.5
        if mid > 0:
            return (ask - bid) / mid
        return 0.0
    
    @staticmethod
    @jit(nopython=True, cache=True)
    def calculate_vwap(prices: np.ndarray, volumes: np.ndarray) -> float:
        """Calculate VWAP (JIT compiled)"""
        if len(prices) == 0 or len(volumes) == 0:
            return 0.0
        
        total_volume = np.sum(volumes)
        if total_volume == 0:
            return 0.0
        
        return np.sum(prices * volumes) / total_volume
    
    @staticmethod
    @jit(nopython=True, cache=True)
    def calculate_momentum_signal(prices: np.ndarray, window: int) -> float:
        """Calculate momentum signal (JIT compiled)"""
        if len(prices) < window + 1:
            return 0.0
        
        recent_avg = np.mean(prices[-window:])
        prev_avg = np.mean(prices[-window-1:-1])
        
        if prev_avg != 0:
            return (recent_avg - prev_avg) / prev_avg
        return 0.0
    
    def set_cpu_affinity(self, cpu_ids: List[int]):
        """Set CPU affinity for latency optimization"""
        try:
            import os
            os.sched_setaffinity(0, cpu_ids)
            self.cpu_affinity = cpu_ids
            logger.info(f"Set CPU affinity to cores: {cpu_ids}")
        except Exception as e:
            logger.warning(f"Failed to set CPU affinity: {str(e)}")
    
    def initialize_gpu_memory_pool(self):
        """Initialize GPU memory pool for CUDA operations"""
        try:
            import cupy
            mempool = cupy.get_default_memory_pool()
            pinned_mempool = cupy.get_default_pinned_memory_pool()
            
            # Pre-allocate memory
            mempool.set_limit(size=2**30)  # 1GB limit
            self.memory_pool = mempool
            
            logger.info("Initialized GPU memory pool")
        except Exception as e:
            logger.warning(f"Failed to initialize GPU memory pool: {str(e)}")


class OrderBook:
    """
    High-performance order book implementation
    """
    
    def __init__(self, symbol: str, max_levels: int = 1000):
        self.symbol = symbol
        self.max_levels = max_levels
        
        # Using heaps for efficient price-level management
        self.bids = []  # Max heap (negative prices for max behavior)
        self.asks = []  # Min heap
        
        # Price level mapping for O(1) access
        self.bid_levels: Dict[float, float] = {}  # price -> size
        self.ask_levels: Dict[float, float] = {}  # price -> size
        
        # Order tracking
        self.orders: Dict[str, Order] = {}
        
        # Statistics
        self.last_update_time = 0
        self.update_count = 0
        
    def update_bid(self, price: float, size: float):
        """Update bid level"""
        self.last_update_time = time.time_ns()
        self.update_count += 1
        
        if size == 0:
            # Remove level
            if price in self.bid_levels:
                del self.bid_levels[price]
                # Remove from heap (lazy deletion)
        else:
            # Add or update level
            self.bid_levels[price] = size
            heapq.heappush(self.bids, -price)  # Negative for max heap
            
        # Maintain heap size
        if len(self.bids) > self.max_levels * 2:
            self._cleanup_bid_heap()
    
    def update_ask(self, price: float, size: float):
        """Update ask level"""
        self.last_update_time = time.time_ns()
        self.update_count += 1
        
        if size == 0:
            # Remove level
            if price in self.ask_levels:
                del self.ask_levels[price]
        else:
            # Add or update level
            self.ask_levels[price] = size
            heapq.heappush(self.asks, price)
            
        # Maintain heap size
        if len(self.asks) > self.max_levels * 2:
            self._cleanup_ask_heap()
    
    def _cleanup_bid_heap(self):
        """Clean up bid heap by removing invalid entries"""
        valid_bids = []
        for neg_price in self.bids:
            price = -neg_price
            if price in self.bid_levels:
                valid_bids.append(neg_price)
        
        self.bids = valid_bids
        heapq.heapify(self.bids)
    
    def _cleanup_ask_heap(self):
        """Clean up ask heap by removing invalid entries"""
        valid_asks = []
        for price in self.asks:
            if price in self.ask_levels:
                valid_asks.append(price)
        
        self.asks = valid_asks
        heapq.heapify(self.asks)
    
    def get_best_bid(self) -> Optional[Tuple[float, float]]:
        """Get best bid (highest price)"""
        while self.bids:
            price = -self.bids[0]
            if price in self.bid_levels:
                return price, self.bid_levels[price]
            else:
                heapq.heappop(self.bids)
        return None
    
    def get_best_ask(self) -> Optional[Tuple[float, float]]:
        """Get best ask (lowest price)"""
        while self.asks:
            price = self.asks[0]
            if price in self.ask_levels:
                return price, self.ask_levels[price]
            else:
                heapq.heappop(self.asks)
        return None
    
    def get_spread(self) -> Optional[float]:
        """Get bid-ask spread"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return best_ask[0] - best_bid[0]
        return None
    
    def get_mid_price(self) -> Optional[float]:
        """Get mid price"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return (best_bid[0] + best_ask[0]) / 2
        return None
    
    def get_market_data(self) -> Optional[MarketData]:
        """Get current market data snapshot"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if not best_bid or not best_ask:
            return None
        
        return MarketData(
            symbol=self.symbol,
            timestamp=self.last_update_time,
            bid_price=best_bid[0],
            ask_price=best_ask[0],
            bid_size=best_bid[1],
            ask_size=best_ask[1],
            last_price=best_bid[0],  # Simplified
            last_size=0.0,
            volume=0.0,
            vwap=0.0
        )


class HighSpeedOrderManager:
    """
    High-speed order management system
    """
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.order_queue = asyncio.Queue(maxsize=10000)
        self.execution_callbacks: List[Callable] = []
        self.latency_tracker = deque(maxlen=1000)
        
        # Performance metrics
        self.orders_per_second = 0
        self.avg_latency_ns = 0
        self.last_metrics_update = time.time()
        
    async def submit_order(self, order: Order) -> str:
        """Submit order for execution"""
        start_time = time.time_ns()
        
        try:
            # Validate order
            if not self._validate_order(order):
                order.status = OrderStatus.REJECTED
                return order.order_id
            
            # Add to order tracking
            self.orders[order.order_id] = order
            order.status = OrderStatus.SUBMITTED
            
            # Queue for processing
            await self.order_queue.put(order)
            
            # Track latency
            latency_ns = time.time_ns() - start_time
            self.latency_tracker.append(latency_ns)
            
            return order.order_id
            
        except Exception as e:
            logger.error(f"Error submitting order: {str(e)}")
            order.status = OrderStatus.REJECTED
            return order.order_id
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        try:
            if order_id in self.orders:
                order = self.orders[order_id]
                if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL]:
                    order.status = OrderStatus.CANCELLED
                    logger.info(f"Order {order_id} cancelled")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False
    
    def _validate_order(self, order: Order) -> bool:
        """Validate order parameters"""
        try:
            # Basic validation
            if order.quantity <= 0:
                logger.error(f"Invalid quantity: {order.quantity}")
                return False
            
            if order.order_type == OrderType.LIMIT and order.price is None:
                logger.error("Limit order requires price")
                return False
            
            if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and order.stop_price is None:
                logger.error("Stop order requires stop price")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Order validation error: {str(e)}")
            return False
    
    async def process_order_queue(self):
        """Process order queue continuously"""
        while True:
            try:
                # Get order from queue
                order = await self.order_queue.get()
                
                # Simulate order execution
                await self._execute_order(order)
                
                # Mark task done
                self.order_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing order queue: {str(e)}")
                await asyncio.sleep(0.001)  # Brief pause on error
    
    async def _execute_order(self, order: Order):
        """Execute order (simplified simulation)"""
        try:
            # Simulate execution latency (real system would interface with exchange)
            await asyncio.sleep(0.0001)  # 0.1ms simulated latency
            
            # Simulate fill
            order.filled_quantity = order.quantity
            order.remaining_quantity = 0.0
            order.avg_fill_price = order.price or 100.0  # Simplified
            order.status = OrderStatus.FILLED
            
            # Create trade record
            trade = Trade(
                trade_id=str(uuid.uuid4()),
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.filled_quantity,
                price=order.avg_fill_price,
                timestamp=time.time_ns(),
                commission=order.filled_quantity * order.avg_fill_price * 0.0001,  # 0.01% commission
                strategy_id=order.strategy_id
            )
            
            # Notify callbacks
            for callback in self.execution_callbacks:
                try:
                    await callback(trade)
                except Exception as e:
                    logger.error(f"Error in execution callback: {str(e)}")
            
            logger.debug(f"Order {order.order_id} executed: {order.filled_quantity} @ {order.avg_fill_price}")
            
        except Exception as e:
            logger.error(f"Error executing order {order.order_id}: {str(e)}")
            order.status = OrderStatus.REJECTED
    
    def add_execution_callback(self, callback: Callable):
        """Add execution callback"""
        self.execution_callbacks.append(callback)
    
    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """Get order status"""
        order = self.orders.get(order_id)
        return order.status if order else None
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics"""
        now = time.time()
        
        # Calculate orders per second
        if now - self.last_metrics_update >= 1.0:
            recent_orders = sum(1 for order in self.orders.values() 
                              if order.timestamp > (now - 1.0) * 1e9)
            self.orders_per_second = recent_orders
            self.last_metrics_update = now
        
        # Calculate average latency
        if self.latency_tracker:
            self.avg_latency_ns = sum(self.latency_tracker) / len(self.latency_tracker)
        
        return {
            'orders_per_second': self.orders_per_second,
            'avg_latency_ns': self.avg_latency_ns,
            'avg_latency_us': self.avg_latency_ns / 1000,
            'total_orders': len(self.orders),
            'queue_size': self.order_queue.qsize()
        }


class HFTStrategy:
    """
    Base class for HFT strategies
    """
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.positions: Dict[str, float] = defaultdict(float)
        self.pnl = 0.0
        self.trade_count = 0
        self.last_update_time = 0
        
        # Strategy state
        self.running = False
        self.risk_breached = False
        
    async def on_market_data(self, market_data: MarketData) -> List[Order]:
        """Handle market data update"""
        raise NotImplementedError("Strategy must implement on_market_data")
    
    async def on_trade(self, trade: Trade):
        """Handle trade execution"""
        # Update position
        if trade.side == OrderSide.BUY:
            self.positions[trade.symbol] += trade.quantity
        else:
            self.positions[trade.symbol] -= trade.quantity
        
        # Update P&L (simplified)
        self.pnl += trade.quantity * trade.price * (1 if trade.side == OrderSide.SELL else -1)
        self.trade_count += 1
        
        logger.debug(f"Strategy {self.config.strategy_id} trade: {trade.symbol} {trade.side.value} {trade.quantity} @ {trade.price}")
    
    def check_risk_limits(self) -> bool:
        """Check if strategy violates risk limits"""
        try:
            # Check position limits
            for symbol, position in self.positions.items():
                if abs(position) > self.config.max_position:
                    logger.warning(f"Position limit breached for {symbol}: {position}")
                    return False
            
            # Check P&L limits
            max_loss = self.config.risk_limits.get('max_loss', float('inf'))
            if self.pnl < -max_loss:
                logger.warning(f"Max loss breached: {self.pnl}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {str(e)}")
            return False
    
    def get_strategy_metrics(self) -> Dict[str, Any]:
        """Get strategy performance metrics"""
        return {
            'strategy_id': self.config.strategy_id,
            'strategy_type': self.config.strategy_type.value,
            'running': self.running,
            'positions': dict(self.positions),
            'pnl': self.pnl,
            'trade_count': self.trade_count,
            'risk_breached': self.risk_breached
        }


class MarketMakingStrategy(HFTStrategy):
    """
    Market making HFT strategy
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # Market making parameters
        self.spread_multiplier = config.parameters.get('spread_multiplier', 1.2)
        self.inventory_target = config.parameters.get('inventory_target', 0.0)
        self.max_quote_size = config.parameters.get('max_quote_size', 1000)
        self.min_spread_bps = config.parameters.get('min_spread_bps', 5)  # Basis points
        
        # State tracking
        self.active_quotes: Dict[str, List[str]] = defaultdict(list)  # symbol -> order_ids
    
    async def on_market_data(self, market_data: MarketData) -> List[Order]:
        """Generate market making quotes"""
        orders = []
        
        try:
            # Check if spread is sufficient
            spread_bps = (market_data.spread / market_data.mid_price) * 10000
            if spread_bps < self.min_spread_bps:
                return orders  # Spread too tight
            
            # Calculate quote parameters
            current_position = self.positions[market_data.symbol]
            inventory_skew = (current_position - self.inventory_target) / self.config.max_position
            
            # Adjust quotes based on inventory
            bid_skew = -inventory_skew * 0.1  # Reduce bids if long
            ask_skew = inventory_skew * 0.1   # Reduce asks if short
            
            # Calculate quote prices
            spread_half = market_data.spread / 2 * self.spread_multiplier
            
            bid_price = market_data.mid_price - spread_half * (1 + bid_skew)
            ask_price = market_data.mid_price + spread_half * (1 + ask_skew)
            
            # Quote size
            quote_size = min(self.max_quote_size, 
                           self.config.max_order_size,
                           (self.config.max_position - abs(current_position)) / 2)
            
            if quote_size > 0:
                # Create bid order
                bid_order = Order(
                    order_id=str(uuid.uuid4()),
                    symbol=market_data.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    quantity=quote_size,
                    price=bid_price,
                    time_in_force="IOC",
                    strategy_id=self.config.strategy_id
                )
                orders.append(bid_order)
                
                # Create ask order
                ask_order = Order(
                    order_id=str(uuid.uuid4()),
                    symbol=market_data.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    quantity=quote_size,
                    price=ask_price,
                    time_in_force="IOC",
                    strategy_id=self.config.strategy_id
                )
                orders.append(ask_order)
                
                # Track active quotes
                self.active_quotes[market_data.symbol].extend([bid_order.order_id, ask_order.order_id])
        
        except Exception as e:
            logger.error(f"Error generating market making quotes: {str(e)}")
        
        return orders


class MomentumStrategy(HFTStrategy):
    """
    Momentum-based HFT strategy
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # Momentum parameters
        self.lookback_periods = config.parameters.get('lookback_periods', 10)
        self.momentum_threshold = config.parameters.get('momentum_threshold', 0.001)
        self.order_size = config.parameters.get('order_size', 100)
        
        # Price history
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.lookback_periods))
    
    async def on_market_data(self, market_data: MarketData) -> List[Order]:
        """Generate momentum-based orders"""
        orders = []
        
        try:
            # Update price history
            self.price_history[market_data.symbol].append(market_data.mid_price)
            
            # Need sufficient history
            if len(self.price_history[market_data.symbol]) < self.lookback_periods:
                return orders
            
            # Calculate momentum signal
            prices = np.array(self.price_history[market_data.symbol])
            momentum = LatencyOptimizer.calculate_momentum_signal(prices, self.lookback_periods // 2)
            
            # Generate signal
            if abs(momentum) > self.momentum_threshold:
                side = OrderSide.BUY if momentum > 0 else OrderSide.SELL
                
                # Check position limits
                current_position = self.positions[market_data.symbol]
                max_additional = self.config.max_position - abs(current_position)
                
                if max_additional > 0:
                    order_size = min(self.order_size, max_additional)
                    
                    # Use market order for speed
                    order = Order(
                        order_id=str(uuid.uuid4()),
                        symbol=market_data.symbol,
                        side=side,
                        order_type=OrderType.MARKET,
                        quantity=order_size,
                        price=None,
                        strategy_id=self.config.strategy_id
                    )
                    orders.append(order)
        
        except Exception as e:
            logger.error(f"Error generating momentum signal: {str(e)}")
        
        return orders


class HFTEngine:
    """
    Main HFT engine coordinating all components
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        
        # Core components
        self.latency_optimizer = LatencyOptimizer()
        self.order_manager = HighSpeedOrderManager()
        self.order_books: Dict[str, OrderBook] = {}
        self.strategies: Dict[str, HFTStrategy] = {}
        
        # Data feeds
        self.market_data_queue = asyncio.Queue(maxsize=100000)
        self.trade_queue = asyncio.Queue(maxsize=10000)
        
        # Performance tracking
        self.start_time = time.time()
        self.message_count = 0
        self.last_performance_log = time.time()
        
        # Event loop optimization
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def initialize(self):
        """Initialize HFT engine"""
        try:
            # Initialize Redis
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Optimize latency
            self.latency_optimizer.set_cpu_affinity([0, 1])  # Use specific CPU cores
            self.latency_optimizer.initialize_gpu_memory_pool()
            
            # Set up order execution callbacks
            self.order_manager.add_execution_callback(self._on_trade_execution)
            
            # Start background tasks
            asyncio.create_task(self.order_manager.process_order_queue())
            asyncio.create_task(self._process_market_data())
            asyncio.create_task(self._performance_monitor())
            
            logger.info("HFT Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing HFT engine: {str(e)}")
            raise
    
    def add_strategy(self, strategy: HFTStrategy):
        """Add HFT strategy"""
        self.strategies[strategy.config.strategy_id] = strategy
        logger.info(f"Added strategy: {strategy.config.strategy_id} ({strategy.config.strategy_type.value})")
    
    def add_symbol(self, symbol: str):
        """Add symbol for trading"""
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook(symbol)
            logger.info(f"Added symbol: {symbol}")
    
    async def _process_market_data(self):
        """Process market data in real-time"""
        while True:
            try:
                # Get market data (timeout to prevent blocking)
                market_data = await asyncio.wait_for(
                    self.market_data_queue.get(), 
                    timeout=0.001
                )
                
                # Update order book
                if market_data.symbol in self.order_books:
                    order_book = self.order_books[market_data.symbol]
                    order_book.update_bid(market_data.bid_price, market_data.bid_size)
                    order_book.update_ask(market_data.ask_price, market_data.ask_size)
                
                # Process strategies
                for strategy in self.strategies.values():
                    if (strategy.config.enabled and 
                        strategy.running and 
                        market_data.symbol in strategy.config.symbols):
                        
                        # Check risk limits
                        if not strategy.check_risk_limits():
                            strategy.risk_breached = True
                            strategy.running = False
                            logger.warning(f"Strategy {strategy.config.strategy_id} stopped due to risk breach")
                            continue
                        
                        # Generate orders
                        try:
                            orders = await strategy.on_market_data(market_data)
                            
                            # Submit orders
                            for order in orders:
                                await self.order_manager.submit_order(order)
                        
                        except Exception as e:
                            logger.error(f"Error in strategy {strategy.config.strategy_id}: {str(e)}")
                
                self.message_count += 1
                
            except asyncio.TimeoutError:
                # No market data available, continue
                await asyncio.sleep(0.0001)  # 0.1ms
            except Exception as e:
                logger.error(f"Error processing market data: {str(e)}")
                await asyncio.sleep(0.001)  # 1ms pause on error
    
    async def _on_trade_execution(self, trade: Trade):
        """Handle trade execution"""
        try:
            # Notify relevant strategy
            if trade.strategy_id in self.strategies:
                strategy = self.strategies[trade.strategy_id]
                await strategy.on_trade(trade)
            
            # Store trade (Redis/database)
            if self.redis_client:
                trade_data = asdict(trade)
                await self.redis_client.lpush("trades", json.dumps(trade_data, default=str))
            
            # Add to trade queue for further processing
            await self.trade_queue.put(trade)
            
        except Exception as e:
            logger.error(f"Error handling trade execution: {str(e)}")
    
    async def _performance_monitor(self):
        """Monitor and log performance metrics"""
        while True:
            try:
                await asyncio.sleep(10)  # Log every 10 seconds
                
                now = time.time()
                if now - self.last_performance_log >= 10:
                    # Calculate message rate
                    elapsed = now - self.start_time
                    messages_per_second = self.message_count / elapsed if elapsed > 0 else 0
                    
                    # Get order manager metrics
                    order_metrics = self.order_manager.get_performance_metrics()
                    
                    # Log performance
                    logger.info(f"HFT Performance - Messages/sec: {messages_per_second:.0f}, "
                              f"Orders/sec: {order_metrics['orders_per_second']}, "
                              f"Avg Latency: {order_metrics['avg_latency_us']:.1f}μs")
                    
                    self.last_performance_log = now
            
            except Exception as e:
                logger.error(f"Error in performance monitor: {str(e)}")
    
    async def feed_market_data(self, market_data: MarketData):
        """Feed market data to the engine"""
        try:
            await self.market_data_queue.put(market_data)
        except asyncio.QueueFull:
            logger.warning("Market data queue full, dropping message")
    
    def start_strategy(self, strategy_id: str):
        """Start a strategy"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].running = True
            self.strategies[strategy_id].risk_breached = False
            logger.info(f"Started strategy: {strategy_id}")
    
    def stop_strategy(self, strategy_id: str):
        """Stop a strategy"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].running = False
            logger.info(f"Stopped strategy: {strategy_id}")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            'uptime_seconds': time.time() - self.start_time,
            'message_count': self.message_count,
            'active_strategies': len([s for s in self.strategies.values() if s.running]),
            'total_strategies': len(self.strategies),
            'symbols': list(self.order_books.keys()),
            'order_queue_size': self.order_manager.order_queue.qsize(),
            'market_data_queue_size': self.market_data_queue.qsize()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        # Stop all strategies
        for strategy in self.strategies.values():
            strategy.running = False
        
        # Cleanup Redis
        if self.redis_client:
            await self.redis_client.close()
        
        # Cleanup executor
        self.executor.shutdown(wait=True)
        
        logger.info("HFT Engine cleanup completed")


# Example usage and testing
if __name__ == "__main__":
    async def test_hft_engine():
        """Test the HFT engine"""
        
        # Initialize engine
        engine = HFTEngine()
        await engine.initialize()
        
        # Add symbols
        symbols = ["AAPL", "GOOGL", "TSLA"]
        for symbol in symbols:
            engine.add_symbol(symbol)
        
        # Create market making strategy
        mm_config = StrategyConfig(
            strategy_id="market_maker_1",
            strategy_type=StrategyType.MARKET_MAKING,
            symbols=symbols,
            max_position=10000,
            max_order_size=1000,
            parameters={
                'spread_multiplier': 1.1,
                'max_quote_size': 500,
                'min_spread_bps': 3
            }
        )
        mm_strategy = MarketMakingStrategy(mm_config)
        engine.add_strategy(mm_strategy)
        
        # Create momentum strategy
        momentum_config = StrategyConfig(
            strategy_id="momentum_1",
            strategy_type=StrategyType.MOMENTUM,
            symbols=symbols,
            max_position=5000,
            max_order_size=500,
            parameters={
                'lookback_periods': 20,
                'momentum_threshold': 0.002,
                'order_size': 100
            }
        )
        momentum_strategy = MomentumStrategy(momentum_config)
        engine.add_strategy(momentum_strategy)
        
        # Start strategies
        engine.start_strategy("market_maker_1")
        engine.start_strategy("momentum_1")
        
        # Simulate market data feed
        print("Starting market data simulation...")
        
        for i in range(1000):
            for symbol in symbols:
                # Generate realistic market data
                base_price = 100 + np.random.normal(0, 0.1)
                spread = 0.01 + np.random.exponential(0.005)
                
                market_data = MarketData(
                    symbol=symbol,
                    timestamp=time.time_ns(),
                    bid_price=base_price - spread/2,
                    ask_price=base_price + spread/2,
                    bid_size=np.random.uniform(100, 1000),
                    ask_size=np.random.uniform(100, 1000),
                    last_price=base_price,
                    last_size=np.random.uniform(10, 100),
                    volume=np.random.uniform(1000, 10000),
                    vwap=base_price
                )
                
                await engine.feed_market_data(market_data)
            
            # Brief pause to simulate realistic data rates
            await asyncio.sleep(0.001)  # 1ms = 1000 updates/second
            
            # Log status periodically
            if i % 100 == 0:
                status = engine.get_engine_status()
                print(f"Processed {i} updates, {status['message_count']} total messages")
        
        # Get final status
        print("\nFinal Engine Status:")
        status = engine.get_engine_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\nStrategy Performance:")
        for strategy in engine.strategies.values():
            metrics = strategy.get_strategy_metrics()
            print(f"  {metrics['strategy_id']}: PnL={metrics['pnl']:.2f}, Trades={metrics['trade_count']}")
        
        # Cleanup
        await engine.cleanup()
        print("\nHFT Engine test completed!")
    
    # Run with uvloop for better performance
    try:
        uvloop.install()
    except:
        pass
    
    asyncio.run(test_hft_engine())