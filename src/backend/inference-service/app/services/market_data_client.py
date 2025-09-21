"""
Market data client for fetching real-time and historical data from multiple providers.
"""

import asyncio
import aiohttp
import ccxt.async_support as ccxt
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import websockets
from urllib.parse import urlencode

import structlog
import pandas as pd
import yfinance as yf

from app.models.market_data import (
    OHLCV, TickData, OrderBook, MarketDataRequest, MarketDataResponse,
    MarketDataStream, DataProvider, DataType, Timeframe, MarketDataStatus
)

logger = structlog.get_logger(__name__)


class MarketDataError(Exception):
    """Market data error."""
    pass


class RateLimitError(Exception):
    """Rate limit exceeded."""
    pass


class MarketDataClient:
    """Client for fetching market data from multiple providers."""
    
    def __init__(self):
        # Exchange clients
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        
        # HTTP session for API calls
        self.session: Optional[aiohttp.ClientSession] = None
        
        # WebSocket connections
        self.websocket_streams: Dict[str, Any] = {}
        
        # Rate limiting
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.last_requests: Dict[str, datetime] = {}
        
        # Configuration
        self.default_provider = DataProvider.BINANCE
        self.request_timeout = 30
        self.max_retries = 3
        
        # API keys (to be set from environment)
        self.api_keys = {
            DataProvider.POLYGON: {
                'api_key': None  # Set from environment
            },
            DataProvider.ALPHA_VANTAGE: {
                'api_key': None  # Set from environment
            },
            DataProvider.IEX_CLOUD: {
                'api_key': None  # Set from environment
            }
        }
        
        # Provider configurations
        self.provider_configs = {
            DataProvider.BINANCE: {
                'base_url': 'https://api.binance.com',
                'websocket_url': 'wss://stream.binance.com:9443/ws',
                'rate_limit': 1200,  # requests per minute
                'weight_limit': 6000,  # weight per minute
            },
            DataProvider.POLYGON: {
                'base_url': 'https://api.polygon.io',
                'rate_limit': 5,  # requests per minute for free tier
            },
            DataProvider.ALPHA_VANTAGE: {
                'base_url': 'https://www.alphavantage.co',
                'rate_limit': 5,  # requests per minute for free tier
            }
        }
    
    async def initialize(self) -> None:
        """Initialize market data client."""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.request_timeout)
            )
            
            # Initialize CCXT exchanges
            await self._initialize_exchanges()
            
            # Initialize rate limiters
            self._initialize_rate_limiters()
            
            logger.info("Market data client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize market data client", error=str(e))
            raise
    
    async def shutdown(self) -> None:
        """Shutdown market data client."""
        try:
            # Close websocket streams
            for stream_id in list(self.websocket_streams.keys()):
                await self.close_stream(stream_id)
            
            # Close exchanges
            for exchange in self.exchanges.values():
                await exchange.close()
            
            # Close HTTP session
            if self.session:
                await self.session.close()
            
            logger.info("Market data client shutdown completed")
            
        except Exception as e:
            logger.error("Error during market data client shutdown", error=str(e))
    
    async def get_historical_data(self, symbols: List[str], timeframe: str,
                                limit: int = 100, provider: Optional[DataProvider] = None,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Dict[str, List[OHLCV]]:
        """
        Get historical OHLCV data.
        
        Args:
            symbols: List of trading symbols
            timeframe: Data timeframe (1m, 5m, 1h, 1d, etc.)
            limit: Maximum number of candles
            provider: Preferred data provider
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            Dictionary mapping symbols to OHLCV data
        """
        provider = provider or self.default_provider
        result = {}
        
        for symbol in symbols:
            try:
                ohlcv_data = await self._fetch_historical_ohlcv(
                    symbol, timeframe, limit, provider, start_date, end_date
                )
                result[symbol] = ohlcv_data
                
            except Exception as e:
                logger.error("Failed to fetch historical data",
                           symbol=symbol, provider=provider, error=str(e))
                result[symbol] = []
        
        return result
    
    async def get_real_time_data(self, symbols: List[str], 
                               data_types: List[DataType],
                               provider: Optional[DataProvider] = None) -> MarketDataResponse:
        """Get real-time market data."""
        provider = provider or self.default_provider
        
        try:
            if DataType.OHLCV in data_types:
                # Get latest OHLCV data
                ohlcv_data = []
                for symbol in symbols:
                    latest = await self._fetch_latest_ohlcv(symbol, provider)
                    if latest:
                        ohlcv_data.extend(latest)
                
                return MarketDataResponse(
                    request_id=f"realtime_{int(time.time())}",
                    symbol=','.join(symbols),
                    data_type=DataType.OHLCV,
                    provider=provider,
                    ohlcv_data=ohlcv_data,
                    total_records=len(ohlcv_data),
                    timestamp=datetime.utcnow()
                )
            
        except Exception as e:
            logger.error("Failed to fetch real-time data", error=str(e))
            raise MarketDataError(f"Real-time data fetch failed: {e}")
    
    async def start_websocket_stream(self, symbols: List[str], 
                                   data_types: List[DataType],
                                   provider: Optional[DataProvider] = None,
                                   callback: Optional[callable] = None) -> str:
        """Start a WebSocket stream for real-time data."""
        provider = provider or self.default_provider
        stream_id = f"stream_{provider}_{int(time.time())}"
        
        try:
            if provider == DataProvider.BINANCE:
                task = asyncio.create_task(
                    self._binance_websocket_stream(stream_id, symbols, data_types, callback)
                )
                
                self.websocket_streams[stream_id] = {
                    'task': task,
                    'provider': provider,
                    'symbols': symbols,
                    'data_types': data_types,
                    'callback': callback,
                    'started_at': datetime.utcnow()
                }
            
            logger.info("Started WebSocket stream", 
                       stream_id=stream_id, provider=provider, symbols=symbols)
            
            return stream_id
            
        except Exception as e:
            logger.error("Failed to start WebSocket stream", error=str(e))
            raise MarketDataError(f"WebSocket stream failed: {e}")
    
    async def close_stream(self, stream_id: str) -> None:
        """Close a WebSocket stream."""
        if stream_id in self.websocket_streams:
            stream_info = self.websocket_streams[stream_id]
            task = stream_info['task']
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self.websocket_streams[stream_id]
            logger.info("Closed WebSocket stream", stream_id=stream_id)
    
    async def _initialize_exchanges(self) -> None:
        """Initialize CCXT exchange clients."""
        try:
            # Binance
            self.exchanges['binance'] = ccxt.binance({
                'apiKey': '',  # Public endpoints only
                'secret': '',
                'sandbox': False,
                'enableRateLimit': True,
            })
            
            # Add more exchanges as needed
            
            logger.debug("CCXT exchanges initialized")
            
        except Exception as e:
            logger.error("Failed to initialize exchanges", error=str(e))
    
    def _initialize_rate_limiters(self) -> None:
        """Initialize rate limiting structures."""
        for provider in DataProvider:
            self.rate_limits[provider] = {
                'requests': 0,
                'window_start': datetime.utcnow(),
                'window_duration': 60,  # 1 minute
                'limit': self.provider_configs.get(provider, {}).get('rate_limit', 100)
            }
    
    async def _fetch_historical_ohlcv(self, symbol: str, timeframe: str, 
                                    limit: int, provider: DataProvider,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> List[OHLCV]:
        """Fetch historical OHLCV data from provider."""
        if provider == DataProvider.BINANCE:
            return await self._fetch_binance_ohlcv(symbol, timeframe, limit, start_date, end_date)
        elif provider == DataProvider.YAHOO_FINANCE:
            return await self._fetch_yahoo_ohlcv(symbol, timeframe, limit, start_date, end_date)
        else:
            raise MarketDataError(f"Provider {provider} not supported for historical OHLCV")
    
    async def _fetch_binance_ohlcv(self, symbol: str, timeframe: str, 
                                 limit: int, start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> List[OHLCV]:
        """Fetch OHLCV data from Binance."""
        try:
            # Check rate limit
            await self._check_rate_limit(DataProvider.BINANCE)
            
            exchange = self.exchanges.get('binance')
            if not exchange:
                raise MarketDataError("Binance exchange not initialized")
            
            # Fetch data using CCXT
            since = int(start_date.timestamp() * 1000) if start_date else None
            
            ohlcv_raw = await exchange.fetch_ohlcv(
                symbol, timeframe, since=since, limit=limit
            )
            
            # Convert to OHLCV objects
            ohlcv_data = []
            for candle in ohlcv_raw:
                timestamp, open_price, high_price, low_price, close_price, volume = candle
                
                ohlcv = OHLCV(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(timestamp / 1000),
                    timeframe=Timeframe(timeframe),
                    open_price=float(open_price),
                    high_price=float(high_price),
                    low_price=float(low_price),
                    close_price=float(close_price),
                    volume=float(volume),
                    provider=DataProvider.BINANCE,
                    status=MarketDataStatus.HISTORICAL
                )
                ohlcv_data.append(ohlcv)
            
            return ohlcv_data
            
        except Exception as e:
            logger.error("Failed to fetch Binance OHLCV", symbol=symbol, error=str(e))
            raise MarketDataError(f"Binance OHLCV fetch failed: {e}")
    
    async def _fetch_yahoo_ohlcv(self, symbol: str, timeframe: str,
                               limit: int, start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[OHLCV]:
        """Fetch OHLCV data from Yahoo Finance."""
        try:
            # Yahoo Finance is synchronous, run in thread pool
            loop = asyncio.get_event_loop()
            
            # Calculate date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                # Default to 100 periods back
                if timeframe == '1d':
                    start_date = end_date - timedelta(days=limit)
                elif timeframe == '1h':
                    start_date = end_date - timedelta(hours=limit)
                else:
                    start_date = end_date - timedelta(days=30)  # Default fallback
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            data = await loop.run_in_executor(
                None, 
                lambda: ticker.history(
                    start=start_date.date(),
                    end=end_date.date(),
                    interval=timeframe
                )
            )
            
            # Convert to OHLCV objects
            ohlcv_data = []
            for timestamp, row in data.iterrows():
                ohlcv = OHLCV(
                    symbol=symbol,
                    timestamp=timestamp.to_pydatetime(),
                    timeframe=Timeframe(timeframe),
                    open_price=float(row['Open']),
                    high_price=float(row['High']),
                    low_price=float(row['Low']),
                    close_price=float(row['Close']),
                    volume=float(row['Volume']),
                    provider=DataProvider.YAHOO_FINANCE,
                    status=MarketDataStatus.HISTORICAL
                )
                ohlcv_data.append(ohlcv)
            
            # Limit to requested number of records
            return ohlcv_data[-limit:] if len(ohlcv_data) > limit else ohlcv_data
            
        except Exception as e:
            logger.error("Failed to fetch Yahoo Finance OHLCV", symbol=symbol, error=str(e))
            raise MarketDataError(f"Yahoo Finance OHLCV fetch failed: {e}")
    
    async def _fetch_latest_ohlcv(self, symbol: str, provider: DataProvider) -> List[OHLCV]:
        """Fetch latest OHLCV data."""
        if provider == DataProvider.BINANCE:
            return await self._fetch_binance_ohlcv(symbol, '1m', 1)
        else:
            return []
    
    async def _binance_websocket_stream(self, stream_id: str, symbols: List[str],
                                      data_types: List[DataType], callback: Optional[callable]) -> None:
        """Binance WebSocket stream handler."""
        try:
            # Create stream URL
            streams = []
            for symbol in symbols:
                symbol_lower = symbol.lower()
                if DataType.OHLCV in data_types:
                    streams.append(f"{symbol_lower}@kline_1m")
                if DataType.TICK in data_types:
                    streams.append(f"{symbol_lower}@trade")
            
            stream_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
            
            async with websockets.connect(stream_url) as websocket:
                logger.info("Connected to Binance WebSocket", stream_id=stream_id)
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        if 'data' in data:
                            stream_data = data['data']
                            
                            # Process kline data
                            if 'k' in stream_data:
                                ohlcv = self._parse_binance_kline(stream_data)
                                if callback:
                                    await callback('ohlcv', ohlcv)
                            
                            # Process trade data
                            elif 'p' in stream_data:  # Trade data
                                tick = self._parse_binance_trade(stream_data)
                                if callback:
                                    await callback('tick', tick)
                    
                    except Exception as e:
                        logger.error("Error processing WebSocket message", 
                                   stream_id=stream_id, error=str(e))
                        
        except Exception as e:
            logger.error("WebSocket stream error", stream_id=stream_id, error=str(e))
    
    def _parse_binance_kline(self, data: Dict[str, Any]) -> OHLCV:
        """Parse Binance kline data to OHLCV."""
        kline = data['k']
        
        return OHLCV(
            symbol=kline['s'],
            timestamp=datetime.fromtimestamp(kline['t'] / 1000),
            timeframe=Timeframe('1m'),
            open_price=float(kline['o']),
            high_price=float(kline['h']),
            low_price=float(kline['l']),
            close_price=float(kline['c']),
            volume=float(kline['v']),
            provider=DataProvider.BINANCE,
            status=MarketDataStatus.LIVE
        )
    
    def _parse_binance_trade(self, data: Dict[str, Any]) -> TickData:
        """Parse Binance trade data to TickData."""
        return TickData(
            symbol=data['s'],
            timestamp=datetime.fromtimestamp(data['T'] / 1000),
            price=float(data['p']),
            size=float(data['q']),
            trade_id=str(data['t']),
            side='buy' if data['m'] else 'sell',
            provider=DataProvider.BINANCE
        )
    
    async def _check_rate_limit(self, provider: DataProvider) -> None:
        """Check and enforce rate limits."""
        rate_info = self.rate_limits.get(provider)
        if not rate_info:
            return
        
        now = datetime.utcnow()
        
        # Reset window if needed
        if (now - rate_info['window_start']).seconds >= rate_info['window_duration']:
            rate_info['requests'] = 0
            rate_info['window_start'] = now
        
        # Check if limit exceeded
        if rate_info['requests'] >= rate_info['limit']:
            raise RateLimitError(f"Rate limit exceeded for {provider}")
        
        # Increment request count
        rate_info['requests'] += 1
        self.last_requests[provider] = now