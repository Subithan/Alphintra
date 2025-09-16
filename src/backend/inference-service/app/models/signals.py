"""
Trading signal data models and schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class SignalAction(str, Enum):
    """Signal action types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    CLOSE_ALL = "CLOSE_ALL"


class SignalStatus(str, Enum):
    """Signal status types."""
    PENDING = "pending"
    ACTIVE = "active"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderType(str, Enum):
    """Order types for signal execution."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class TimeInForce(str, Enum):
    """Time in force options."""
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    DAY = "DAY"  # Day order


class ExecutionParams(BaseModel):
    """Order execution parameters."""
    quantity: float = Field(..., gt=0, description="Order quantity")
    price_target: Optional[float] = Field(None, gt=0, description="Target price for limit orders")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
    order_type: OrderType = Field(OrderType.MARKET, description="Order type")
    time_in_force: TimeInForce = Field(TimeInForce.GTC, description="Time in force")
    max_slippage: float = Field(0.001, ge=0, le=1, description="Maximum allowed slippage")
    
    @validator('stop_loss', 'take_profit')
    def validate_prices(cls, v, values):
        if v is not None and v <= 0:
            raise ValueError("Prices must be positive")
        return v


class MarketConditions(BaseModel):
    """Market condition metadata."""
    trend: Optional[str] = Field(None, description="Market trend (bullish/bearish/sideways)")
    volatility: Optional[str] = Field(None, description="Volatility level (low/medium/high)")
    volume_profile: Optional[str] = Field(None, description="Volume profile")
    support_level: Optional[float] = Field(None, description="Support price level")
    resistance_level: Optional[float] = Field(None, description="Resistance price level")


class TradingSignal(BaseModel):
    """Core trading signal model."""
    
    signal_id: str = Field(default_factory=lambda: f"sig_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Strategy information
    strategy_id: str = Field(..., description="Strategy identifier")
    strategy_source: str = Field(..., description="Strategy source (ai_ml/no_code)")
    strategy_version: Optional[str] = Field(None, description="Strategy version")
    
    # Trading information
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    exchange: str = Field("binance", description="Exchange name")
    action: SignalAction = Field(..., description="Signal action")
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence score")
    
    # Execution parameters
    execution_params: ExecutionParams = Field(..., description="Order execution parameters")
    
    # Risk management
    risk_score: float = Field(0.0, ge=0, le=1, description="Risk assessment score")
    position_size: Optional[float] = Field(None, description="Position size percentage")
    max_drawdown: Optional[float] = Field(None, description="Maximum allowed drawdown")
    
    # Market context
    current_price: Optional[float] = Field(None, gt=0, description="Current market price")
    market_conditions: Optional[MarketConditions] = Field(None, description="Market conditions")
    
    # Signal metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    status: SignalStatus = Field(SignalStatus.PENDING, description="Signal status")
    
    # Expiration
    expires_at: Optional[datetime] = Field(None, description="Signal expiration time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class SignalBatch(BaseModel):
    """Batch of trading signals."""
    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signals: List[TradingSignal] = Field(..., description="List of signals")
    total_count: int = Field(..., ge=0, description="Total number of signals")
    
    @validator('total_count')
    def validate_count(cls, v, values):
        signals = values.get('signals', [])
        if v != len(signals):
            raise ValueError("total_count must match the number of signals")
        return v


class SignalFilter(BaseModel):
    """Filter parameters for querying signals."""
    strategy_ids: Optional[List[str]] = Field(None, description="Filter by strategy IDs")
    strategy_source: Optional[str] = Field(None, description="Filter by strategy source")
    symbols: Optional[List[str]] = Field(None, description="Filter by symbols")
    actions: Optional[List[SignalAction]] = Field(None, description="Filter by actions")
    status: Optional[List[SignalStatus]] = Field(None, description="Filter by status")
    min_confidence: Optional[float] = Field(None, ge=0, le=1, description="Minimum confidence")
    max_risk_score: Optional[float] = Field(None, ge=0, le=1, description="Maximum risk score")
    from_timestamp: Optional[datetime] = Field(None, description="From timestamp")
    to_timestamp: Optional[datetime] = Field(None, description="To timestamp")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class SignalPerformance(BaseModel):
    """Signal performance metrics."""
    signal_id: str = Field(..., description="Signal identifier")
    execution_price: Optional[float] = Field(None, description="Actual execution price")
    execution_time: Optional[datetime] = Field(None, description="Execution timestamp")
    pnl: Optional[float] = Field(None, description="Profit and loss")
    pnl_percentage: Optional[float] = Field(None, description="PnL percentage")
    slippage: Optional[float] = Field(None, description="Price slippage")
    fill_rate: Optional[float] = Field(None, ge=0, le=1, description="Order fill rate")
    execution_duration: Optional[float] = Field(None, description="Execution duration in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SignalAnalytics(BaseModel):
    """Aggregated signal analytics."""
    total_signals: int = Field(..., ge=0)
    signals_by_action: Dict[str, int] = Field(...)
    signals_by_status: Dict[str, int] = Field(...)
    average_confidence: float = Field(..., ge=0, le=1)
    average_risk_score: float = Field(..., ge=0, le=1)
    success_rate: Optional[float] = Field(None, ge=0, le=1)
    total_pnl: Optional[float] = Field(None)
    time_period: str = Field(..., description="Analytics time period")