"""
Market data models and schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class DataProvider(str, Enum):
    """Market data providers."""
    BINANCE = "binance"
    POLYGON = "polygon"
    ALPHA_VANTAGE = "alpha_vantage"
    IEX_CLOUD = "iex_cloud"
    YAHOO_FINANCE = "yahoo_finance"


class DataType(str, Enum):
    """Market data types."""
    OHLCV = "ohlcv"  # Open, High, Low, Close, Volume
    TICK = "tick"
    ORDERBOOK = "orderbook"
    TRADES = "trades"


class Timeframe(str, Enum):
    """Supported timeframes."""
    T1m = "1m"
    T5m = "5m"
    T15m = "15m"
    T30m = "30m"
    T1h = "1h"
    T4h = "4h"
    T1d = "1d"
    T1w = "1w"
    T1M = "1M"


class MarketDataStatus(str, Enum):
    """Market data status."""
    LIVE = "live"
    DELAYED = "delayed"
    HISTORICAL = "historical"
    STALE = "stale"
    ERROR = "error"


class OHLCV(BaseModel):
    """Open, High, Low, Close, Volume data."""
    
    symbol: str = Field(..., description="Trading symbol")
    timestamp: datetime = Field(..., description="Data timestamp")
    timeframe: Timeframe = Field(..., description="Data timeframe")
    
    open_price: float = Field(..., gt=0, description="Opening price")
    high_price: float = Field(..., gt=0, description="Highest price")
    low_price: float = Field(..., gt=0, description="Lowest price")
    close_price: float = Field(..., gt=0, description="Closing price")
    volume: float = Field(..., ge=0, description="Trading volume")
    
    # Additional fields
    vwap: Optional[float] = Field(None, gt=0, description="Volume Weighted Average Price")
    trades_count: Optional[int] = Field(None, ge=0, description="Number of trades")
    
    # Data quality
    provider: DataProvider = Field(..., description="Data provider")
    status: MarketDataStatus = Field(MarketDataStatus.LIVE, description="Data status")
    latency_ms: Optional[float] = Field(None, ge=0, description="Data latency in milliseconds")
    
    @validator('high_price')
    def validate_high_price(cls, v, values):
        if 'low_price' in values and v < values['low_price']:
            raise ValueError("High price cannot be less than low price")
        return v
    
    @validator('low_price')
    def validate_low_price(cls, v, values):
        if 'high_price' in values and v > values['high_price']:
            raise ValueError("Low price cannot be greater than high price")
        return v
    
    @validator('close_price')
    def validate_close_price(cls, v, values):
        if 'high_price' in values and 'low_price' in values:
            if not (values['low_price'] <= v <= values['high_price']):
                raise ValueError("Close price must be within high-low range")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: float
        }


class TickData(BaseModel):
    """Individual tick/trade data."""
    
    symbol: str = Field(..., description="Trading symbol")
    timestamp: datetime = Field(..., description="Trade timestamp")
    price: float = Field(..., gt=0, description="Trade price")
    size: float = Field(..., gt=0, description="Trade size")
    
    # Trade details
    trade_id: Optional[str] = Field(None, description="Unique trade ID")
    side: Optional[str] = Field(None, description="Trade side (buy/sell)")
    conditions: Optional[List[str]] = Field(None, description="Trade conditions")
    
    # Data source
    provider: DataProvider = Field(..., description="Data provider")
    exchange: Optional[str] = Field(None, description="Exchange name")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderBookLevel(BaseModel):
    """Order book level data."""
    
    price: float = Field(..., gt=0, description="Price level")
    size: float = Field(..., gt=0, description="Size at price level")
    orders_count: Optional[int] = Field(None, ge=0, description="Number of orders")


class OrderBook(BaseModel):
    """Order book snapshot."""
    
    symbol: str = Field(..., description="Trading symbol")
    timestamp: datetime = Field(..., description="Snapshot timestamp")
    
    bids: List[OrderBookLevel] = Field(..., description="Bid levels")
    asks: List[OrderBookLevel] = Field(..., description="Ask levels")
    
    # Derived values
    best_bid: Optional[float] = Field(None, gt=0, description="Best bid price")
    best_ask: Optional[float] = Field(None, gt=0, description="Best ask price")
    spread: Optional[float] = Field(None, ge=0, description="Bid-ask spread")
    mid_price: Optional[float] = Field(None, gt=0, description="Mid price")
    
    # Data source
    provider: DataProvider = Field(..., description="Data provider")
    sequence: Optional[int] = Field(None, description="Sequence number")
    
    @validator('spread')
    def calculate_spread(cls, v, values):
        if v is None and values.get('best_bid') and values.get('best_ask'):
            return values['best_ask'] - values['best_bid']
        return v
    
    @validator('mid_price')
    def calculate_mid_price(cls, v, values):
        if v is None and values.get('best_bid') and values.get('best_ask'):
            return (values['best_bid'] + values['best_ask']) / 2
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MarketDataRequest(BaseModel):
    """Market data subscription request."""
    
    symbols: List[str] = Field(..., min_items=1, description="List of symbols")
    data_types: List[DataType] = Field(..., min_items=1, description="Data types to subscribe")
    timeframes: Optional[List[Timeframe]] = Field(None, description="Timeframes for OHLCV data")
    
    # Provider preferences
    preferred_providers: Optional[List[DataProvider]] = Field(None, description="Preferred providers")
    require_real_time: bool = Field(True, description="Require real-time data")
    max_latency_ms: Optional[float] = Field(None, gt=0, description="Maximum acceptable latency")
    
    # Subscription settings
    start_time: Optional[datetime] = Field(None, description="Start time for historical data")
    end_time: Optional[datetime] = Field(None, description="End time for historical data")
    limit: Optional[int] = Field(None, ge=1, le=10000, description="Maximum number of records")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MarketDataResponse(BaseModel):
    """Market data response."""
    
    request_id: str = Field(..., description="Request identifier")
    symbol: str = Field(..., description="Symbol")
    data_type: DataType = Field(..., description="Data type")
    provider: DataProvider = Field(..., description="Data provider")
    
    # Response data (union of different data types)
    ohlcv_data: Optional[List[OHLCV]] = Field(None, description="OHLCV data")
    tick_data: Optional[List[TickData]] = Field(None, description="Tick data")
    orderbook_data: Optional[OrderBook] = Field(None, description="Order book data")
    
    # Response metadata
    total_records: int = Field(..., ge=0, description="Total records returned")
    has_more: bool = Field(False, description="More data available")
    next_cursor: Optional[str] = Field(None, description="Pagination cursor")
    
    # Quality metrics
    latency_ms: Optional[float] = Field(None, ge=0, description="Response latency")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MarketDataStream(BaseModel):
    """Real-time market data stream."""
    
    stream_id: str = Field(..., description="Stream identifier")
    symbols: List[str] = Field(..., description="Subscribed symbols")
    data_types: List[DataType] = Field(..., description="Subscribed data types")
    provider: DataProvider = Field(..., description="Data provider")
    
    # Stream status
    status: str = Field("active", description="Stream status")
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = Field(None)
    messages_received: int = Field(0, ge=0)
    
    # Quality metrics
    avg_latency_ms: Optional[float] = Field(None, ge=0)
    error_count: int = Field(0, ge=0)
    reconnect_count: int = Field(0, ge=0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TechnicalIndicator(BaseModel):
    """Technical indicator calculation result."""
    
    symbol: str = Field(..., description="Symbol")
    indicator_name: str = Field(..., description="Indicator name")
    timestamp: datetime = Field(..., description="Calculation timestamp")
    timeframe: Timeframe = Field(..., description="Data timeframe")
    
    # Indicator values (flexible structure)
    values: Dict[str, Union[float, List[float]]] = Field(..., description="Indicator values")
    
    # Calculation metadata
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Calculation parameters")
    lookback_periods: int = Field(..., ge=1, description="Periods used in calculation")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MarketSummary(BaseModel):
    """Market summary statistics."""
    
    symbol: str = Field(..., description="Symbol")
    timestamp: datetime = Field(..., description="Summary timestamp")
    period: str = Field(..., description="Summary period")
    
    # Price data
    current_price: float = Field(..., gt=0)
    price_change: float = Field(...)
    price_change_percent: float = Field(...)
    
    # Volume data
    volume_24h: float = Field(..., ge=0)
    volume_change_percent: Optional[float] = Field(None)
    
    # High/Low data
    high_24h: float = Field(..., gt=0)
    low_24h: float = Field(..., gt=0)
    
    # Market cap (for tokens/stocks)
    market_cap: Optional[float] = Field(None, ge=0)
    
    # Data source
    provider: DataProvider = Field(...)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }