"""
Signal distribution service for broadcasting trading signals via multiple channels.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Callable
from uuid import uuid4

import structlog
import aioredis
from kafka import KafkaProducer
from kafka.errors import KafkaError
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

from app.models.signals import TradingSignal, SignalBatch, SignalStatus

logger = structlog.get_logger(__name__)


class SignalDistributionError(Exception):
    """Signal distribution error."""
    pass


class WebSocketManager:
    """Manages WebSocket connections for real-time signal streaming."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # connection_id -> set of symbols
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    def add_connection(self, connection_id: str, websocket: WebSocketServerProtocol,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a new WebSocket connection."""
        self.connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()
        self.connection_metadata[connection_id] = metadata or {}
        
        logger.info("WebSocket connection added", connection_id=connection_id)
    
    def remove_connection(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        self.connections.pop(connection_id, None)
        self.subscriptions.pop(connection_id, None)
        self.connection_metadata.pop(connection_id, None)
        
        logger.info("WebSocket connection removed", connection_id=connection_id)
    
    def subscribe_to_symbol(self, connection_id: str, symbol: str) -> None:
        """Subscribe a connection to signals for a specific symbol."""
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].add(symbol.upper())
            logger.debug("WebSocket subscribed to symbol", 
                        connection_id=connection_id, symbol=symbol)
    
    def unsubscribe_from_symbol(self, connection_id: str, symbol: str) -> None:
        """Unsubscribe a connection from signals for a specific symbol."""
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].discard(symbol.upper())
            logger.debug("WebSocket unsubscribed from symbol", 
                        connection_id=connection_id, symbol=symbol)
    
    async def broadcast_to_subscribers(self, signal: TradingSignal) -> None:
        """Broadcast signal to subscribed connections."""
        symbol = signal.symbol.upper()
        message = {
            "type": "signal",
            "data": signal.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Find connections subscribed to this symbol or all symbols
        target_connections = []
        for connection_id, subscribed_symbols in self.subscriptions.items():
            if symbol in subscribed_symbols or "*" in subscribed_symbols:
                if connection_id in self.connections:
                    target_connections.append((connection_id, self.connections[connection_id]))
        
        # Send to all target connections
        if target_connections:
            await self._send_to_connections(target_connections, json.dumps(message))
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        if self.connections:
            connections = [(cid, ws) for cid, ws in self.connections.items()]
            await self._send_to_connections(connections, json.dumps(message))
    
    async def _send_to_connections(self, connections: List[tuple], message: str) -> None:
        """Send message to multiple connections."""
        if not connections:
            return
        
        tasks = []
        for connection_id, websocket in connections:
            tasks.append(self._send_safe(connection_id, websocket, message))
        
        # Send to all connections concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_safe(self, connection_id: str, websocket: WebSocketServerProtocol, message: str) -> None:
        """Safely send message to a WebSocket connection."""
        try:
            await websocket.send(message)
        except ConnectionClosed:
            self.remove_connection(connection_id)
        except Exception as e:
            logger.error("Error sending WebSocket message", 
                        connection_id=connection_id, error=str(e))
            self.remove_connection(connection_id)


class SignalDistributor:
    """Main signal distribution service."""
    
    def __init__(self, kafka_servers: str, redis_url: str):
        self.kafka_servers = kafka_servers
        self.redis_url = redis_url
        
        # Kafka producer
        self.kafka_producer: Optional[KafkaProducer] = None
        
        # Redis client for caching and pub/sub
        self.redis_client: Optional[aioredis.Redis] = None
        
        # WebSocket manager
        self.websocket_manager = WebSocketManager()
        
        # Signal storage and caching
        self.signal_cache: Dict[str, TradingSignal] = {}
        self.signal_history: List[TradingSignal] = []
        self.max_cache_size = 1000
        self.max_history_size = 10000
        
        # Distribution metrics
        self.metrics = {
            "signals_distributed": 0,
            "kafka_messages_sent": 0,
            "websocket_messages_sent": 0,
            "redis_messages_published": 0,
            "distribution_errors": 0,
            "active_websocket_connections": 0
        }
        
        # Configuration
        self.kafka_topics = {
            "signals": "trading_signals",
            "signal_updates": "trading_signal_updates",
            "strategy_status": "strategy_status"
        }
    
    async def initialize(self) -> None:
        """Initialize signal distributor."""
        try:
            # Initialize Kafka producer
            await self._initialize_kafka()
            
            # Initialize Redis client
            await self._initialize_redis()
            
            # Start background tasks
            asyncio.create_task(self._cleanup_task())
            asyncio.create_task(self._metrics_task())
            
            logger.info("Signal distributor initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize signal distributor", error=str(e))
            raise SignalDistributionError(f"Initialization failed: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown signal distributor."""
        try:
            # Close Kafka producer
            if self.kafka_producer:
                self.kafka_producer.close()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            # Close WebSocket connections
            for connection_id in list(self.websocket_manager.connections.keys()):
                self.websocket_manager.remove_connection(connection_id)
            
            logger.info("Signal distributor shutdown completed")
            
        except Exception as e:
            logger.error("Error during signal distributor shutdown", error=str(e))
    
    async def distribute_signal(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        Distribute a trading signal via all channels.
        
        Args:
            signal: Trading signal to distribute
            
        Returns:
            Distribution result summary
        """
        start_time = time.time()
        distribution_results = {
            "signal_id": signal.signal_id,
            "kafka": {"success": False, "error": None},
            "websocket": {"success": False, "error": None, "connections": 0},
            "redis": {"success": False, "error": None},
            "cached": False
        }
        
        try:
            # Update signal status
            signal.status = SignalStatus.ACTIVE
            signal.timestamp = datetime.utcnow()
            
            # Cache the signal
            self._cache_signal(signal)
            distribution_results["cached"] = True
            
            # Distribute via Kafka
            try:
                await self._distribute_via_kafka(signal)
                distribution_results["kafka"]["success"] = True
                self.metrics["kafka_messages_sent"] += 1
            except Exception as e:
                distribution_results["kafka"]["error"] = str(e)
                logger.error("Kafka distribution failed", 
                           signal_id=signal.signal_id, error=str(e))
            
            # Distribute via WebSocket
            try:
                await self.websocket_manager.broadcast_to_subscribers(signal)
                distribution_results["websocket"]["success"] = True
                distribution_results["websocket"]["connections"] = len(self.websocket_manager.connections)
                self.metrics["websocket_messages_sent"] += 1
            except Exception as e:
                distribution_results["websocket"]["error"] = str(e)
                logger.error("WebSocket distribution failed", 
                           signal_id=signal.signal_id, error=str(e))
            
            # Distribute via Redis pub/sub
            try:
                await self._distribute_via_redis(signal)
                distribution_results["redis"]["success"] = True
                self.metrics["redis_messages_published"] += 1
            except Exception as e:
                distribution_results["redis"]["error"] = str(e)
                logger.error("Redis distribution failed", 
                           signal_id=signal.signal_id, error=str(e))
            
            # Update metrics
            self.metrics["signals_distributed"] += 1
            
            # Log successful distribution
            distribution_time = time.time() - start_time
            logger.info("Signal distributed successfully",
                       signal_id=signal.signal_id,
                       symbol=signal.symbol,
                       action=signal.action.value,
                       distribution_time=distribution_time)
            
            return distribution_results
            
        except Exception as e:
            self.metrics["distribution_errors"] += 1
            logger.error("Signal distribution failed", 
                        signal_id=signal.signal_id, error=str(e))
            raise SignalDistributionError(f"Distribution failed: {e}")
    
    async def distribute_signal_batch(self, signals: List[TradingSignal]) -> Dict[str, Any]:
        """Distribute multiple signals as a batch."""
        batch = SignalBatch(
            signals=signals,
            total_count=len(signals)
        )
        
        results = []
        for signal in signals:
            try:
                result = await self.distribute_signal(signal)
                results.append(result)
            except Exception as e:
                results.append({
                    "signal_id": signal.signal_id,
                    "error": str(e)
                })
        
        return {
            "batch_id": batch.batch_id,
            "total_signals": len(signals),
            "results": results,
            "timestamp": batch.timestamp.isoformat()
        }
    
    def add_websocket_connection(self, connection_id: str, websocket: WebSocketServerProtocol,
                               metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a WebSocket connection for signal streaming."""
        self.websocket_manager.add_connection(connection_id, websocket, metadata)
        self.metrics["active_websocket_connections"] = len(self.websocket_manager.connections)
    
    def remove_websocket_connection(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        self.websocket_manager.remove_connection(connection_id)
        self.metrics["active_websocket_connections"] = len(self.websocket_manager.connections)
    
    def subscribe_websocket(self, connection_id: str, symbols: List[str]) -> None:
        """Subscribe a WebSocket connection to specific symbols."""
        for symbol in symbols:
            self.websocket_manager.subscribe_to_symbol(connection_id, symbol)
    
    def unsubscribe_websocket(self, connection_id: str, symbols: List[str]) -> None:
        """Unsubscribe a WebSocket connection from specific symbols."""
        for symbol in symbols:
            self.websocket_manager.unsubscribe_from_symbol(connection_id, symbol)
    
    def get_cached_signals(self, symbol: Optional[str] = None, limit: int = 100) -> List[TradingSignal]:
        """Get cached signals, optionally filtered by symbol."""
        signals = list(self.signal_history)
        
        if symbol:
            signals = [s for s in signals if s.symbol.upper() == symbol.upper()]
        
        return signals[-limit:] if len(signals) > limit else signals
    
    def get_signal_by_id(self, signal_id: str) -> Optional[TradingSignal]:
        """Get a specific signal by ID from cache."""
        return self.signal_cache.get(signal_id)
    
    async def _initialize_kafka(self) -> None:
        """Initialize Kafka producer."""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=10,
                max_request_size=1048576
            )
            
            logger.debug("Kafka producer initialized")
            
        except Exception as e:
            logger.error("Failed to initialize Kafka producer", error=str(e))
            raise
    
    async def _initialize_redis(self) -> None:
        """Initialize Redis client."""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            
            # Test connection
            await self.redis_client.ping()
            
            logger.debug("Redis client initialized")
            
        except Exception as e:
            logger.error("Failed to initialize Redis client", error=str(e))
            raise
    
    async def _distribute_via_kafka(self, signal: TradingSignal) -> None:
        """Distribute signal via Kafka."""
        try:
            # Prepare message
            message = {
                "signal": signal.dict(),
                "timestamp": datetime.utcnow().isoformat(),
                "distributor": "inference-service"
            }
            
            # Send to main signals topic
            future = self.kafka_producer.send(
                self.kafka_topics["signals"],
                key=signal.signal_id,
                value=message
            )
            
            # Wait for acknowledgment (optional, for reliability)
            record_metadata = future.get(timeout=10)
            
            logger.debug("Signal sent to Kafka",
                        topic=record_metadata.topic,
                        partition=record_metadata.partition,
                        offset=record_metadata.offset)
            
        except KafkaError as e:
            raise SignalDistributionError(f"Kafka distribution failed: {e}")
    
    async def _distribute_via_redis(self, signal: TradingSignal) -> None:
        """Distribute signal via Redis pub/sub."""
        try:
            # Publish to symbol-specific channel
            symbol_channel = f"signals:{signal.symbol.upper()}"
            await self.redis_client.publish(symbol_channel, signal.json())
            
            # Publish to general signals channel
            await self.redis_client.publish("signals:all", signal.json())
            
            # Store in Redis for historical access
            await self.redis_client.setex(
                f"signal:{signal.signal_id}",
                3600,  # 1 hour expiry
                signal.json()
            )
            
        except Exception as e:
            raise SignalDistributionError(f"Redis distribution failed: {e}")
    
    def _cache_signal(self, signal: TradingSignal) -> None:
        """Cache signal in memory."""
        # Add to cache by ID
        self.signal_cache[signal.signal_id] = signal
        
        # Add to history
        self.signal_history.append(signal)
        
        # Maintain cache size limits
        if len(self.signal_cache) > self.max_cache_size:
            # Remove oldest from cache (FIFO)
            oldest_signals = sorted(self.signal_cache.items(), 
                                  key=lambda x: x[1].timestamp)[:100]
            for signal_id, _ in oldest_signals:
                self.signal_cache.pop(signal_id)
        
        if len(self.signal_history) > self.max_history_size:
            # Keep only recent history
            self.signal_history = self.signal_history[-self.max_history_size//2:]
    
    async def _cleanup_task(self) -> None:
        """Background cleanup task."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up expired signals from cache
                current_time = datetime.utcnow()
                expired_signals = []
                
                for signal_id, signal in self.signal_cache.items():
                    if signal.expires_at and signal.expires_at < current_time:
                        expired_signals.append(signal_id)
                
                for signal_id in expired_signals:
                    self.signal_cache.pop(signal_id)
                
                if expired_signals:
                    logger.debug(f"Cleaned up {len(expired_signals)} expired signals")
                
            except Exception as e:
                logger.error("Error in cleanup task", error=str(e))
    
    async def _metrics_task(self) -> None:
        """Background metrics reporting task."""
        while True:
            try:
                await asyncio.sleep(60)  # Report every minute
                
                logger.info("Signal distributor metrics", **self.metrics)
                
            except Exception as e:
                logger.error("Error in metrics task", error=str(e))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            **self.metrics,
            "cached_signals": len(self.signal_cache),
            "signal_history_size": len(self.signal_history)
        }