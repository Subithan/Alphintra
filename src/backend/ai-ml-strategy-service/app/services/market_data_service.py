"""
Market data service for real-time and historical data integration.
"""

import asyncio
import logging
import json
import websockets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import redis.asyncio as redis
from sqlalchemy.orm import Session

from app.models.paper_trading import MarketDataSnapshot
from app.database.connection import get_db_session


class DataProvider(Enum):
    SIMULATION = "simulation"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    TWELVEDATA = "twelvedata"
    INTERNAL = "internal"


@dataclass
class Tick:
    """Real-time tick data."""
    symbol: str
    timestamp: datetime
    price: Decimal
    volume: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    bid_size: Optional[Decimal] = None
    ask_size: Optional[Decimal] = None


@dataclass
class Quote:
    """Bid/Ask quote data."""
    symbol: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal
    spread: Decimal


@dataclass
class Bar:
    """OHLCV bar data."""
    symbol: str
    timestamp: datetime
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


class MarketDataService:
    """Market data service for real-time and historical data."""
    
    def __init__(
        self,
        provider: DataProvider = DataProvider.SIMULATION,
        redis_url: str = "redis://localhost:6379"
    ):
        self.provider = provider
        self.logger = logging.getLogger(__name__)
        
        # Redis for caching and pub/sub
        self.redis = None
        self.redis_url = redis_url
        
        # Subscriptions and callbacks
        self.tick_subscribers: Dict[str, List[Callable]] = {}
        self.quote_subscribers: Dict[str, List[Callable]] = {}
        self.bar_subscribers: Dict[str, List[Callable]] = {}
        
        # Market data cache
        self.tick_cache: Dict[str, Tick] = {}
        self.quote_cache: Dict[str, Quote] = {}
        
        # WebSocket connections
        self.ws_connections: Dict[str, Any] = {}
        
        # Data provider configurations
        self.provider_configs = {
            DataProvider.ALPHA_VANTAGE: {
                "base_url": "https://www.alphavantage.co/query",
                "ws_url": None,
                "api_key": None  # Set from environment
            },
            DataProvider.POLYGON: {
                "base_url": "https://api.polygon.io",
                "ws_url": "wss://socket.polygon.io",
                "api_key": None  # Set from environment
            },
            DataProvider.TWELVEDATA: {
                "base_url": "https://api.twelvedata.com",
                "ws_url": "wss://ws.twelvedata.com/v1",
                "api_key": None  # Set from environment
            }
        }
        
        # Simulation parameters
        self.simulation_symbols: Dict[str, Dict] = {}
        self.simulation_running = False
    
    async def initialize(self) -> None:
        """Initialize the market data service."""
        
        # Connect to Redis
        self.redis = redis.from_url(self.redis_url)
        
        # Initialize provider-specific setup
        if self.provider == DataProvider.SIMULATION:
            await self._initialize_simulation()
        elif self.provider in [DataProvider.POLYGON, DataProvider.TWELVEDATA]:
            await self._initialize_websocket_provider()
        
        self.logger.info(f"Market data service initialized with provider: {self.provider.value}")
    
    async def _initialize_simulation(self) -> None:
        """Initialize simulation mode."""
        
        # Default simulation symbols with realistic parameters
        default_symbols = {
            "AAPL": {"base_price": Decimal("150.00"), "volatility": 0.02, "trend": 0.0001},
            "GOOGL": {"base_price": Decimal("2800.00"), "volatility": 0.025, "trend": 0.0002},
            "TSLA": {"base_price": Decimal("800.00"), "volatility": 0.04, "trend": -0.0001},
            "SPY": {"base_price": Decimal("420.00"), "volatility": 0.015, "trend": 0.0001},
            "BTC-USD": {"base_price": Decimal("45000.00"), "volatility": 0.05, "trend": 0.0005},
            "EUR/USD": {"base_price": Decimal("1.0850"), "volatility": 0.008, "trend": 0.0}
        }
        
        for symbol, params in default_symbols.items():
            self.simulation_symbols[symbol] = {
                "current_price": params["base_price"],
                "volatility": params["volatility"],
                "trend": params["trend"],
                "last_update": datetime.utcnow()
            }
    
    async def _initialize_websocket_provider(self) -> None:
        """Initialize WebSocket-based data provider."""
        
        if self.provider == DataProvider.POLYGON:
            await self._initialize_polygon_ws()
        elif self.provider == DataProvider.TWELVEDATA:
            await self._initialize_twelvedata_ws()
    
    async def subscribe_ticks(self, symbol: str, callback: Callable[[Tick], None]) -> None:
        """Subscribe to real-time tick data."""
        
        if symbol not in self.tick_subscribers:
            self.tick_subscribers[symbol] = []
        
        self.tick_subscribers[symbol].append(callback)
        
        # Start data feed for this symbol
        if self.provider == DataProvider.SIMULATION:
            await self._start_simulation_ticks(symbol)
        else:
            await self._subscribe_external_ticks(symbol)
        
        self.logger.info(f"Subscribed to tick data for {symbol}")
    
    async def subscribe_quotes(self, symbol: str, callback: Callable[[Quote], None]) -> None:
        """Subscribe to real-time quote data."""
        
        if symbol not in self.quote_subscribers:
            self.quote_subscribers[symbol] = []
        
        self.quote_subscribers[symbol].append(callback)
        
        # Start quote feed for this symbol
        if self.provider == DataProvider.SIMULATION:
            await self._start_simulation_quotes(symbol)
        else:
            await self._subscribe_external_quotes(symbol)
        
        self.logger.info(f"Subscribed to quote data for {symbol}")
    
    async def _start_simulation_ticks(self, symbol: str) -> None:
        """Start simulated tick data generation."""
        
        if symbol not in self.simulation_symbols:
            # Add new symbol with default parameters
            self.simulation_symbols[symbol] = {
                "current_price": Decimal("100.00"),
                "volatility": 0.02,
                "trend": 0.0,
                "last_update": datetime.utcnow()
            }
        
        if not self.simulation_running:
            self.simulation_running = True
            asyncio.create_task(self._simulation_tick_generator())
    
    async def _simulation_tick_generator(self) -> None:
        """Generate simulated tick data."""
        
        import random
        import math
        
        while self.simulation_running:
            try:
                current_time = datetime.utcnow()
                
                for symbol, params in self.simulation_symbols.items():
                    if symbol in self.tick_subscribers:
                        # Generate price movement
                        dt = 1.0  # 1 second interval
                        volatility = params["volatility"]
                        trend = params["trend"]
                        
                        # Geometric Brownian Motion
                        random_factor = random.gauss(0, 1)
                        price_change = (trend - 0.5 * volatility ** 2) * dt + volatility * math.sqrt(dt) * random_factor
                        
                        new_price = params["current_price"] * Decimal(str(math.exp(price_change)))
                        params["current_price"] = new_price
                        params["last_update"] = current_time
                        
                        # Generate bid/ask spread (0.01% to 0.1%)
                        spread_pct = Decimal(str(0.0001 + random.random() * 0.0009))
                        spread = new_price * spread_pct
                        
                        bid = new_price - spread / 2
                        ask = new_price + spread / 2
                        
                        # Generate volume
                        volume = Decimal(str(random.randint(100, 10000)))
                        bid_size = Decimal(str(random.randint(10, 1000)))
                        ask_size = Decimal(str(random.randint(10, 1000)))
                        
                        # Create tick
                        tick = Tick(
                            symbol=symbol,
                            timestamp=current_time,
                            price=new_price,
                            volume=volume,
                            bid=bid,
                            ask=ask,
                            bid_size=bid_size,
                            ask_size=ask_size
                        )
                        
                        # Cache and publish
                        self.tick_cache[symbol] = tick
                        await self._publish_tick(tick)
                
                await asyncio.sleep(1.0)  # 1 second intervals
                
            except Exception as e:
                self.logger.error(f"Error in simulation tick generator: {e}")
                await asyncio.sleep(1.0)
    
    async def _start_simulation_quotes(self, symbol: str) -> None:
        """Start simulated quote data generation."""
        
        # Use the same tick generator, quotes are derived from ticks
        await self._start_simulation_ticks(symbol)
    
    async def _publish_tick(self, tick: Tick) -> None:
        """Publish tick data to subscribers."""
        
        # Call local subscribers
        if tick.symbol in self.tick_subscribers:
            for callback in self.tick_subscribers[tick.symbol]:
                try:
                    await callback(tick)
                except Exception as e:
                    self.logger.error(f"Error in tick callback for {tick.symbol}: {e}")
        
        # Publish to Redis for other services
        if self.redis:
            try:
                tick_data = asdict(tick)
                # Convert Decimal to string for JSON serialization
                for key, value in tick_data.items():
                    if isinstance(value, Decimal):
                        tick_data[key] = str(value)
                    elif isinstance(value, datetime):
                        tick_data[key] = value.isoformat()
                
                await self.redis.publish(f"ticks:{tick.symbol}", json.dumps(tick_data))
            except Exception as e:
                self.logger.error(f"Error publishing tick to Redis: {e}")
        
        # Generate quote from tick
        if tick.bid and tick.ask:
            quote = Quote(
                symbol=tick.symbol,
                timestamp=tick.timestamp,
                bid=tick.bid,
                ask=tick.ask,
                bid_size=tick.bid_size or Decimal("100"),
                ask_size=tick.ask_size or Decimal("100"),
                spread=tick.ask - tick.bid
            )
            
            self.quote_cache[tick.symbol] = quote
            await self._publish_quote(quote)
    
    async def _publish_quote(self, quote: Quote) -> None:
        """Publish quote data to subscribers."""
        
        # Call local subscribers
        if quote.symbol in self.quote_subscribers:
            for callback in self.quote_subscribers[quote.symbol]:
                try:
                    await callback(quote)
                except Exception as e:
                    self.logger.error(f"Error in quote callback for {quote.symbol}: {e}")
        
        # Publish to Redis
        if self.redis:
            try:
                quote_data = asdict(quote)
                # Convert Decimal to string for JSON serialization
                for key, value in quote_data.items():
                    if isinstance(value, Decimal):
                        quote_data[key] = str(value)
                    elif isinstance(value, datetime):
                        quote_data[key] = value.isoformat()
                
                await self.redis.publish(f"quotes:{quote.symbol}", json.dumps(quote_data))
            except Exception as e:
                self.logger.error(f"Error publishing quote to Redis: {e}")
    
    async def get_current_quote(self, symbol: str) -> Optional[Quote]:
        """Get current quote for symbol."""
        
        # Try cache first
        if symbol in self.quote_cache:
            quote = self.quote_cache[symbol]
            # Check if quote is recent (within last 10 seconds)
            if (datetime.utcnow() - quote.timestamp).total_seconds() < 10:
                return quote
        
        # Try Redis cache
        if self.redis:
            try:
                cached_data = await self.redis.get(f"quote:{symbol}")
                if cached_data:
                    quote_data = json.loads(cached_data)
                    # Convert strings back to appropriate types
                    for key in ["bid", "ask", "bid_size", "ask_size", "spread"]:
                        if key in quote_data:
                            quote_data[key] = Decimal(quote_data[key])
                    if "timestamp" in quote_data:
                        quote_data["timestamp"] = datetime.fromisoformat(quote_data["timestamp"])
                    
                    return Quote(**quote_data)
            except Exception as e:
                self.logger.error(f"Error retrieving quote from Redis: {e}")
        
        # Generate quote if in simulation mode
        if self.provider == DataProvider.SIMULATION and symbol in self.simulation_symbols:
            params = self.simulation_symbols[symbol]
            price = params["current_price"]
            spread = price * Decimal("0.0005")  # 0.05% spread
            
            quote = Quote(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                bid=price - spread / 2,
                ask=price + spread / 2,
                bid_size=Decimal("100"),
                ask_size=Decimal("100"),
                spread=spread
            )
            
            self.quote_cache[symbol] = quote
            return quote
        
        return None
    
    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price for symbol."""
        
        quote = await self.get_current_quote(symbol)
        if quote:
            return (quote.bid + quote.ask) / 2
        
        # Fallback to tick cache
        if symbol in self.tick_cache:
            return self.tick_cache[symbol].price
        
        return None
    
    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[Bar]:
        """Get historical bar data."""
        
        if self.provider == DataProvider.SIMULATION:
            return await self._generate_simulation_bars(symbol, timeframe, start_date, end_date, limit)
        
        # Implementation for external providers would go here
        # For now, return empty list
        return []
    
    async def _generate_simulation_bars(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        limit: int
    ) -> List[Bar]:
        """Generate simulated historical bars."""
        
        import random
        import math
        
        bars = []
        
        # Parse timeframe (e.g., "1m", "5m", "1h", "1d")
        timeframe_minutes = self._parse_timeframe(timeframe)
        interval = timedelta(minutes=timeframe_minutes)
        
        # Get symbol parameters
        if symbol not in self.simulation_symbols:
            self.simulation_symbols[symbol] = {
                "current_price": Decimal("100.00"),
                "volatility": 0.02,
                "trend": 0.0,
                "last_update": datetime.utcnow()
            }
        
        params = self.simulation_symbols[symbol]
        base_price = params["current_price"]
        volatility = params["volatility"]
        trend = params["trend"]
        
        current_time = start_date
        current_price = base_price * Decimal("0.9")  # Start 10% below current
        
        while current_time <= end_date and len(bars) < limit:
            # Generate OHLCV for this period
            open_price = current_price
            
            # Generate minute-by-minute movements within the timeframe
            high_price = open_price
            low_price = open_price
            volume = Decimal("0")
            
            for _ in range(timeframe_minutes):
                # Price movement
                dt = 1.0 / (24 * 60)  # 1 minute as fraction of day
                random_factor = random.gauss(0, 1)
                price_change = (trend - 0.5 * volatility ** 2) * dt + volatility * math.sqrt(dt) * random_factor
                
                current_price *= Decimal(str(math.exp(price_change)))
                high_price = max(high_price, current_price)
                low_price = min(low_price, current_price)
                
                # Volume (random but realistic)
                volume += Decimal(str(random.randint(100, 5000)))
            
            close_price = current_price
            
            bar = Bar(
                symbol=symbol,
                timestamp=current_time,
                timeframe=timeframe,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume
            )
            
            bars.append(bar)
            current_time += interval
        
        return bars
    
    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to minutes."""
        
        timeframe = timeframe.lower()
        
        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 24 * 60
        else:
            return 1  # Default to 1 minute
    
    async def save_market_data_snapshot(self, tick: Tick) -> None:
        """Save market data snapshot to database."""
        
        try:
            snapshot = MarketDataSnapshot(
                symbol=tick.symbol,
                timestamp=tick.timestamp,
                close_price=tick.price,
                bid_price=tick.bid,
                ask_price=tick.ask,
                bid_size=tick.bid_size,
                ask_size=tick.ask_size,
                spread=tick.ask - tick.bid if tick.ask and tick.bid else None,
                volume=tick.volume,
                source=self.provider.value
            )
            
            with get_db_session() as db:
                db.add(snapshot)
                db.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving market data snapshot: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        
        self.simulation_running = False
        
        # Close WebSocket connections
        for ws in self.ws_connections.values():
            if hasattr(ws, 'close'):
                await ws.close()
        
        # Close Redis connection
        if self.redis:
            await self.redis.close()
        
        self.logger.info("Market data service cleaned up")


# Global market data service instance
market_data_service = MarketDataService()