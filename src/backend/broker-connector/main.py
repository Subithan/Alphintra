import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid

import asyncpg
import redis.asyncio as redis
from kafka import KafkaConsumer, KafkaProducer
import ccxt.async_support as ccxt
import websockets
from contextlib import asynccontextmanager
import aiohttp
import hmac
import hashlib
import base64
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra:alphintra@localhost:5432/alphintra")
TIMESCALE_URL = os.getenv("TIMESCALE_URL", "postgresql://tsuser:tspass@localhost:5433/alphintra_ts")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Exchange API credentials (should be encrypted in production)
EXCHANGE_CREDENTIALS = {
    'binance': {
        'apiKey': os.getenv('BINANCE_API_KEY', ''),
        'secret': os.getenv('BINANCE_SECRET', ''),
        'sandbox': os.getenv('BINANCE_SANDBOX', 'true').lower() == 'true'
    },
    'coinbase': {
        'apiKey': os.getenv('COINBASE_API_KEY', ''),
        'secret': os.getenv('COINBASE_SECRET', ''),
        'passphrase': os.getenv('COINBASE_PASSPHRASE', ''),
        'sandbox': os.getenv('COINBASE_SANDBOX', 'true').lower() == 'true'
    },
    'kraken': {
        'apiKey': os.getenv('KRAKEN_API_KEY', ''),
        'secret': os.getenv('KRAKEN_SECRET', ''),
        'sandbox': os.getenv('KRAKEN_SANDBOX', 'true').lower() == 'true'
    }
}

# Global connections
db_pool = None
ts_pool = None
redis_client = None
kafka_consumer = None
kafka_producer = None
exchange_clients = {}
websocket_connections = {}

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
class OrderRequest:
    user_id: int
    account_id: int
    exchange: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    client_order_id: Optional[str] = None

@dataclass
class OrderResponse:
    order_id: str
    client_order_id: Optional[str]
    exchange_order_id: str
    status: OrderStatus
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    filled_quantity: float
    remaining_quantity: float
    price: Optional[float]
    average_price: Optional[float]
    created_at: datetime
    updated_at: datetime
    fees: Optional[Dict[str, Any]] = None
    trades: Optional[List[Dict[str, Any]]] = None

class ExchangeConnector:
    """Base class for exchange connectors"""
    
    def __init__(self, exchange_name: str, credentials: Dict[str, Any]):
        self.exchange_name = exchange_name
        self.credentials = credentials
        self.client = None
        self.websocket = None
        self.is_connected = False
        
    async def initialize(self):
        """Initialize exchange connection"""
        raise NotImplementedError
    
    async def place_order(self, order: OrderRequest) -> OrderResponse:
        """Place an order on the exchange"""
        raise NotImplementedError
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        raise NotImplementedError
    
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResponse:
        """Get order status"""
        raise NotImplementedError
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        raise NotImplementedError
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderResponse]:
        """Get open orders"""
        raise NotImplementedError
    
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[OrderResponse]:
        """Get order history"""
        raise NotImplementedError
    
    async def subscribe_to_market_data(self, symbols: List[str]):
        """Subscribe to real-time market data"""
        raise NotImplementedError
    
    async def subscribe_to_user_data(self):
        """Subscribe to user data updates (orders, trades, balance)"""
        raise NotImplementedError
    
    async def disconnect(self):
        """Disconnect from exchange"""
        if self.client:
            await self.client.close()
        if self.websocket:
            await self.websocket.close()
        self.is_connected = False

class BinanceConnector(ExchangeConnector):
    """Binance exchange connector"""
    
    async def initialize(self):
        """Initialize Binance connection"""
        try:
            self.client = ccxt.binance({
                'apiKey': self.credentials['apiKey'],
                'secret': self.credentials['secret'],
                'sandbox': self.credentials.get('sandbox', True),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'  # spot, margin, future, delivery
                }
            })
            
            # Test connection
            await self.client.load_markets()
            balance = await self.client.fetch_balance()
            
            self.is_connected = True
            logger.info(f"Binance connector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Binance connector: {e}")
            raise
    
    async def place_order(self, order: OrderRequest) -> OrderResponse:
        """Place order on Binance"""
        try:
            # Convert order parameters
            symbol = order.symbol
            side = order.side.value
            order_type = order.order_type.value
            amount = order.quantity
            
            params = {
                'timeInForce': order.time_in_force
            }
            
            if order.client_order_id:
                params['newClientOrderId'] = order.client_order_id
            
            # Place order based on type
            if order.order_type == OrderType.MARKET:
                result = await self.client.create_market_order(
                    symbol, side, amount, None, None, params
                )
            elif order.order_type == OrderType.LIMIT:
                result = await self.client.create_limit_order(
                    symbol, side, amount, order.price, None, params
                )
            elif order.order_type == OrderType.STOP:
                params['stopPrice'] = order.stop_price
                result = await self.client.create_order(
                    symbol, 'stop_loss', side, amount, None, None, params
                )
            elif order.order_type == OrderType.STOP_LIMIT:
                params['stopPrice'] = order.stop_price
                result = await self.client.create_order(
                    symbol, 'stop_loss_limit', side, amount, order.price, None, params
                )
            else:
                raise ValueError(f"Unsupported order type: {order.order_type}")
            
            # Convert response
            return OrderResponse(
                order_id=str(uuid.uuid4()),  # Internal order ID
                client_order_id=result.get('clientOrderId'),
                exchange_order_id=result['id'],
                status=OrderStatus(result['status'].lower()),
                symbol=result['symbol'],
                side=OrderSide(result['side'].lower()),
                order_type=OrderType(result['type'].lower()),
                quantity=float(result['amount']),
                filled_quantity=float(result['filled']),
                remaining_quantity=float(result['remaining']),
                price=float(result['price']) if result['price'] else None,
                average_price=float(result['average']) if result['average'] else None,
                created_at=datetime.fromtimestamp(result['timestamp'] / 1000),
                updated_at=datetime.fromtimestamp(result['lastTradeTimestamp'] / 1000) if result['lastTradeTimestamp'] else datetime.utcnow(),
                fees=result.get('fees'),
                trades=result.get('trades')
            )
            
        except Exception as e:
            logger.error(f"Error placing Binance order: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel Binance order"""
        try:
            result = await self.client.cancel_order(order_id, symbol)
            return result['status'] == 'canceled'
        except Exception as e:
            logger.error(f"Error cancelling Binance order: {e}")
            return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResponse:
        """Get Binance order status"""
        try:
            result = await self.client.fetch_order(order_id, symbol)
            
            return OrderResponse(
                order_id=order_id,
                client_order_id=result.get('clientOrderId'),
                exchange_order_id=result['id'],
                status=OrderStatus(result['status'].lower()),
                symbol=result['symbol'],
                side=OrderSide(result['side'].lower()),
                order_type=OrderType(result['type'].lower()),
                quantity=float(result['amount']),
                filled_quantity=float(result['filled']),
                remaining_quantity=float(result['remaining']),
                price=float(result['price']) if result['price'] else None,
                average_price=float(result['average']) if result['average'] else None,
                created_at=datetime.fromtimestamp(result['timestamp'] / 1000),
                updated_at=datetime.fromtimestamp(result['lastTradeTimestamp'] / 1000) if result['lastTradeTimestamp'] else datetime.utcnow(),
                fees=result.get('fees'),
                trades=result.get('trades')
            )
            
        except Exception as e:
            logger.error(f"Error fetching Binance order status: {e}")
            raise
    
    async def get_balance(self) -> Dict[str, float]:
        """Get Binance account balance"""
        try:
            balance = await self.client.fetch_balance()
            return {
                asset: {
                    'free': info['free'],
                    'used': info['used'],
                    'total': info['total']
                }
                for asset, info in balance.items()
                if isinstance(info, dict) and 'free' in info
            }
        except Exception as e:
            logger.error(f"Error fetching Binance balance: {e}")
            raise
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderResponse]:
        """Get Binance open orders"""
        try:
            orders = await self.client.fetch_open_orders(symbol)
            
            return [
                OrderResponse(
                    order_id=str(uuid.uuid4()),
                    client_order_id=order.get('clientOrderId'),
                    exchange_order_id=order['id'],
                    status=OrderStatus(order['status'].lower()),
                    symbol=order['symbol'],
                    side=OrderSide(order['side'].lower()),
                    order_type=OrderType(order['type'].lower()),
                    quantity=float(order['amount']),
                    filled_quantity=float(order['filled']),
                    remaining_quantity=float(order['remaining']),
                    price=float(order['price']) if order['price'] else None,
                    average_price=float(order['average']) if order['average'] else None,
                    created_at=datetime.fromtimestamp(order['timestamp'] / 1000),
                    updated_at=datetime.fromtimestamp(order['lastTradeTimestamp'] / 1000) if order['lastTradeTimestamp'] else datetime.utcnow(),
                    fees=order.get('fees'),
                    trades=order.get('trades')
                )
                for order in orders
            ]
            
        except Exception as e:
            logger.error(f"Error fetching Binance open orders: {e}")
            raise
    
    async def subscribe_to_market_data(self, symbols: List[str]):
        """Subscribe to Binance market data WebSocket"""
        try:
            # Convert symbols to Binance format
            binance_symbols = [symbol.lower() for symbol in symbols]
            
            # Create WebSocket streams
            streams = []
            for symbol in binance_symbols:
                streams.extend([
                    f"{symbol}@ticker",
                    f"{symbol}@depth20@100ms",
                    f"{symbol}@kline_1m"
                ])
            
            stream_url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"
            
            async def handle_message(websocket, path):
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self.process_market_data(data)
                    except Exception as e:
                        logger.error(f"Error processing market data: {e}")
            
            # Start WebSocket connection
            self.websocket = await websockets.connect(stream_url)
            asyncio.create_task(handle_message(self.websocket, None))
            
            logger.info(f"Subscribed to Binance market data for {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error subscribing to Binance market data: {e}")
    
    async def process_market_data(self, data: Dict[str, Any]):
        """Process incoming market data"""
        try:
            if 'stream' in data:
                stream = data['stream']
                event_data = data['data']
                
                if '@ticker' in stream:
                    # Price ticker data
                    ticker_data = {
                        'exchange': 'binance',
                        'symbol': event_data['s'],
                        'price': float(event_data['c']),
                        'volume': float(event_data['v']),
                        'change': float(event_data['P']),
                        'timestamp': datetime.fromtimestamp(event_data['E'] / 1000)
                    }
                    
                    # Publish to Kafka
                    kafka_producer.send('market-data-ticker', ticker_data)
                    
                elif '@depth' in stream:
                    # Order book data
                    orderbook_data = {
                        'exchange': 'binance',
                        'symbol': event_data['s'],
                        'bids': [[float(bid[0]), float(bid[1])] for bid in event_data['bids']],
                        'asks': [[float(ask[0]), float(ask[1])] for ask in event_data['asks']],
                        'timestamp': datetime.utcnow()
                    }
                    
                    # Store in TimescaleDB
                    await self.store_orderbook_data(orderbook_data)
                    
                elif '@kline' in stream:
                    # Candlestick data
                    kline = event_data['k']
                    if kline['x']:  # Only process closed candles
                        candle_data = {
                            'exchange': 'binance',
                            'symbol': kline['s'],
                            'timeframe': '1m',
                            'open_time': datetime.fromtimestamp(kline['t'] / 1000),
                            'close_time': datetime.fromtimestamp(kline['T'] / 1000),
                            'open_price': float(kline['o']),
                            'high_price': float(kline['h']),
                            'low_price': float(kline['l']),
                            'close_price': float(kline['c']),
                            'volume': float(kline['v']),
                            'trades': int(kline['n'])
                        }
                        
                        # Store in TimescaleDB
                        await self.store_market_data(candle_data)
                        
                        # Publish to Kafka
                        kafka_producer.send('market-data', candle_data)
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
    
    async def store_market_data(self, data: Dict[str, Any]):
        """Store market data in TimescaleDB"""
        try:
            async with ts_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO market_data (time, exchange, symbol, timeframe, open_price, 
                                           high_price, low_price, close_price, volume, trades)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (time, exchange, symbol, timeframe) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume,
                        trades = EXCLUDED.trades
                    """,
                    data['open_time'], data['exchange'], data['symbol'], data['timeframe'],
                    data['open_price'], data['high_price'], data['low_price'],
                    data['close_price'], data['volume'], data['trades']
                )
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
    
    async def store_orderbook_data(self, data: Dict[str, Any]):
        """Store order book data in TimescaleDB"""
        try:
            async with ts_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO orderbook_snapshots (time, exchange, symbol, bids, asks)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    data['timestamp'], data['exchange'], data['symbol'],
                    json.dumps(data['bids']), json.dumps(data['asks'])
                )
        except Exception as e:
            logger.error(f"Error storing orderbook data: {e}")

class CoinbaseConnector(ExchangeConnector):
    """Coinbase Pro exchange connector"""
    
    async def initialize(self):
        """Initialize Coinbase connection"""
        try:
            self.client = ccxt.coinbasepro({
                'apiKey': self.credentials['apiKey'],
                'secret': self.credentials['secret'],
                'passphrase': self.credentials['passphrase'],
                'sandbox': self.credentials.get('sandbox', True),
                'enableRateLimit': True
            })
            
            # Test connection
            await self.client.load_markets()
            balance = await self.client.fetch_balance()
            
            self.is_connected = True
            logger.info(f"Coinbase connector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Coinbase connector: {e}")
            raise
    
    async def place_order(self, order: OrderRequest) -> OrderResponse:
        """Place order on Coinbase Pro"""
        try:
            symbol = order.symbol
            side = order.side.value
            order_type = order.order_type.value
            amount = order.quantity
            
            params = {}
            if order.client_order_id:
                params['client_oid'] = order.client_order_id
            
            # Place order based on type
            if order.order_type == OrderType.MARKET:
                result = await self.client.create_market_order(
                    symbol, side, amount, None, None, params
                )
            elif order.order_type == OrderType.LIMIT:
                result = await self.client.create_limit_order(
                    symbol, side, amount, order.price, None, params
                )
            else:
                raise ValueError(f"Unsupported order type for Coinbase: {order.order_type}")
            
            # Convert response
            return OrderResponse(
                order_id=str(uuid.uuid4()),
                client_order_id=result.get('clientOrderId'),
                exchange_order_id=result['id'],
                status=OrderStatus(result['status'].lower()),
                symbol=result['symbol'],
                side=OrderSide(result['side'].lower()),
                order_type=OrderType(result['type'].lower()),
                quantity=float(result['amount']),
                filled_quantity=float(result['filled']),
                remaining_quantity=float(result['remaining']),
                price=float(result['price']) if result['price'] else None,
                average_price=float(result['average']) if result['average'] else None,
                created_at=datetime.fromtimestamp(result['timestamp'] / 1000),
                updated_at=datetime.fromtimestamp(result['lastTradeTimestamp'] / 1000) if result['lastTradeTimestamp'] else datetime.utcnow(),
                fees=result.get('fees'),
                trades=result.get('trades')
            )
            
        except Exception as e:
            logger.error(f"Error placing Coinbase order: {e}")
            raise
    
    # Implement other methods similar to Binance...
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        try:
            result = await self.client.cancel_order(order_id, symbol)
            return result['status'] == 'canceled'
        except Exception as e:
            logger.error(f"Error cancelling Coinbase order: {e}")
            return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResponse:
        # Similar implementation to Binance
        pass
    
    async def get_balance(self) -> Dict[str, float]:
        try:
            balance = await self.client.fetch_balance()
            return {
                asset: {
                    'free': info['free'],
                    'used': info['used'],
                    'total': info['total']
                }
                for asset, info in balance.items()
                if isinstance(info, dict) and 'free' in info
            }
        except Exception as e:
            logger.error(f"Error fetching Coinbase balance: {e}")
            raise
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderResponse]:
        # Similar implementation to Binance
        pass

class BrokerConnectorService:
    """Main broker connector service"""
    
    def __init__(self):
        self.connectors: Dict[str, ExchangeConnector] = {}
        self.running = False
        
    async def initialize(self):
        """Initialize broker connector service"""
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
                group_id='broker-connector'
            )
            
            kafka_producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
            )
            
            # Initialize exchange connectors
            await self.initialize_connectors()
            
            logger.info("Broker connector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize broker connector service: {e}")
            raise
    
    async def initialize_connectors(self):
        """Initialize exchange connectors"""
        try:
            # Initialize Binance connector
            if EXCHANGE_CREDENTIALS['binance']['apiKey']:
                binance_connector = BinanceConnector('binance', EXCHANGE_CREDENTIALS['binance'])
                await binance_connector.initialize()
                self.connectors['binance'] = binance_connector
                
                # Subscribe to market data for popular pairs
                popular_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
                await binance_connector.subscribe_to_market_data(popular_symbols)
            
            # Initialize Coinbase connector
            if EXCHANGE_CREDENTIALS['coinbase']['apiKey']:
                coinbase_connector = CoinbaseConnector('coinbase', EXCHANGE_CREDENTIALS['coinbase'])
                await coinbase_connector.initialize()
                self.connectors['coinbase'] = coinbase_connector
            
            logger.info(f"Initialized {len(self.connectors)} exchange connectors")
            
        except Exception as e:
            logger.error(f"Error initializing connectors: {e}")
    
    async def process_trade_execution(self, trade_data: Dict[str, Any]):
        """Process trade execution request"""
        try:
            exchange = trade_data.get('exchange', 'binance')
            
            if exchange not in self.connectors:
                logger.error(f"Exchange {exchange} not available")
                return
            
            connector = self.connectors[exchange]
            
            # Create order request
            order_request = OrderRequest(
                user_id=trade_data['user_id'],
                account_id=trade_data['account_id'],
                exchange=exchange,
                symbol=trade_data['symbol'],
                side=OrderSide(trade_data['side']),
                order_type=OrderType(trade_data['order_type']),
                quantity=trade_data['quantity'],
                price=trade_data.get('price'),
                stop_price=trade_data.get('stop_price'),
                client_order_id=trade_data.get('trade_id')
            )
            
            # Place order
            order_response = await connector.place_order(order_request)
            
            # Update order in database
            await self.update_order_in_database(trade_data['trade_id'], order_response)
            
            # Publish order update
            order_update = {
                'trade_id': trade_data['trade_id'],
                'exchange_order_id': order_response.exchange_order_id,
                'status': order_response.status.value,
                'filled_quantity': order_response.filled_quantity,
                'average_price': order_response.average_price,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            kafka_producer.send('order-updates', order_update)
            
            logger.info(f"Order placed successfully: {order_response.exchange_order_id}")
            
        except Exception as e:
            logger.error(f"Error processing trade execution: {e}")
            
            # Publish error event
            error_event = {
                'trade_id': trade_data.get('trade_id'),
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
            kafka_producer.send('order-errors', error_event)
    
    async def update_order_in_database(self, trade_id: str, order_response: OrderResponse):
        """Update order information in database"""
        try:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE trades SET 
                        exchange_order_id = $1,
                        status = $2,
                        filled_quantity = $3,
                        remaining_quantity = $4,
                        average_price = $5,
                        updated_at = NOW()
                    WHERE trade_id = $6
                    """,
                    order_response.exchange_order_id,
                    order_response.status.value,
                    order_response.filled_quantity,
                    order_response.remaining_quantity,
                    order_response.average_price,
                    trade_id
                )
        except Exception as e:
            logger.error(f"Error updating order in database: {e}")
    
    async def run(self):
        """Main service loop"""
        self.running = True
        logger.info("Broker connector service started")
        
        while self.running:
            try:
                # Process Kafka messages
                message_batch = kafka_consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        if message.topic == 'trade-execution':
                            await self.process_trade_execution(message.value)
                        elif message.topic == 'order-management':
                            await self.process_order_management(message.value)
                
                # Periodic tasks
                await self.sync_order_status()
                await self.sync_account_balances()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in broker connector loop: {e}")
                await asyncio.sleep(5)
    
    async def process_order_management(self, order_data: Dict[str, Any]):
        """Process order management requests (cancel, modify, etc.)"""
        try:
            action = order_data.get('action')
            exchange = order_data.get('exchange')
            
            if exchange not in self.connectors:
                logger.error(f"Exchange {exchange} not available")
                return
            
            connector = self.connectors[exchange]
            
            if action == 'cancel':
                success = await connector.cancel_order(
                    order_data['exchange_order_id'],
                    order_data['symbol']
                )
                
                if success:
                    # Update database
                    async with db_pool.acquire() as conn:
                        await conn.execute(
                            "UPDATE trades SET status = 'cancelled' WHERE exchange_order_id = $1",
                            order_data['exchange_order_id']
                        )
                    
                    # Publish update
                    cancel_update = {
                        'exchange_order_id': order_data['exchange_order_id'],
                        'status': 'cancelled',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    kafka_producer.send('order-updates', cancel_update)
            
        except Exception as e:
            logger.error(f"Error processing order management: {e}")
    
    async def sync_order_status(self):
        """Sync order status with exchanges"""
        try:
            # Get pending/open orders from database
            async with db_pool.acquire() as conn:
                orders = await conn.fetch(
                    """
                    SELECT * FROM trades 
                    WHERE status IN ('pending', 'open', 'partially_filled') 
                    AND exchange_order_id IS NOT NULL
                    """
                )
                
                for order in orders:
                    exchange = order['exchange']
                    if exchange in self.connectors:
                        try:
                            connector = self.connectors[exchange]
                            order_status = await connector.get_order_status(
                                order['exchange_order_id'],
                                order['symbol']
                            )
                            
                            # Update if status changed
                            if order_status.status.value != order['status']:
                                await conn.execute(
                                    """
                                    UPDATE trades SET 
                                        status = $1,
                                        filled_quantity = $2,
                                        average_price = $3,
                                        updated_at = NOW()
                                    WHERE id = $4
                                    """,
                                    order_status.status.value,
                                    order_status.filled_quantity,
                                    order_status.average_price,
                                    order['id']
                                )
                                
                                # Publish update
                                status_update = {
                                    'trade_id': order['trade_id'],
                                    'exchange_order_id': order['exchange_order_id'],
                                    'status': order_status.status.value,
                                    'filled_quantity': order_status.filled_quantity,
                                    'average_price': order_status.average_price,
                                    'timestamp': datetime.utcnow().isoformat()
                                }
                                kafka_producer.send('order-updates', status_update)
                        
                        except Exception as e:
                            logger.error(f"Error syncing order {order['id']}: {e}")
        
        except Exception as e:
            logger.error(f"Error in sync_order_status: {e}")
    
    async def sync_account_balances(self):
        """Sync account balances with exchanges"""
        try:
            for exchange_name, connector in self.connectors.items():
                try:
                    balance = await connector.get_balance()
                    
                    # Store balance in Redis for quick access
                    await redis_client.setex(
                        f"balance:{exchange_name}",
                        300,  # 5 minutes TTL
                        json.dumps(balance, default=str)
                    )
                    
                    # Publish balance update
                    balance_update = {
                        'exchange': exchange_name,
                        'balance': balance,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    kafka_producer.send('balance-updates', balance_update)
                    
                except Exception as e:
                    logger.error(f"Error syncing balance for {exchange_name}: {e}")
        
        except Exception as e:
            logger.error(f"Error in sync_account_balances: {e}")
    
    async def stop(self):
        """Stop broker connector service"""
        self.running = False
        
        # Disconnect from exchanges
        for connector in self.connectors.values():
            await connector.disconnect()
        
        logger.info("Broker connector service stopped")

async def main():
    """Main function"""
    service = BrokerConnectorService()
    
    try:
        await service.initialize()
        await service.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await service.stop()
        
        # Cleanup connections
        if db_pool:
            await db_pool.close()
        if ts_pool:
            await ts_pool.close()
        if redis_client:
            await redis_client.close()
        if kafka_producer:
            kafka_producer.close()

if __name__ == "__main__":
    asyncio.run(main())