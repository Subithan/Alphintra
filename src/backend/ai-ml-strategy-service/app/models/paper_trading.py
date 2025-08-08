"""
Paper trading related database models.
"""

from decimal import Decimal
from enum import Enum as PyEnum
from typing import Dict, Any, List

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, Enum, ForeignKey, DateTime, Index, DECIMAL
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, UserMixin, MetadataMixin
from app.models.types import StringArray, FloatArray


class AccountStatus(PyEnum):
    """Paper trading account status."""
    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class PositionSide(PyEnum):
    """Position side enumeration."""
    LONG = "long"
    SHORT = "short"


class OrderType(PyEnum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(PyEnum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(PyEnum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class StrategyDeploymentStatus(PyEnum):
    """Strategy deployment status."""
    DEPLOYING = "deploying"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class PaperAccount(BaseModel, UserMixin, MetadataMixin):
    """
    Paper trading account for virtual trading simulation.
    """
    __tablename__ = "paper_accounts"
    
    # Account information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False, index=True)
    
    # Capital and balances
    initial_capital = Column(DECIMAL(15, 2), nullable=False)
    current_capital = Column(DECIMAL(15, 2), nullable=False)
    available_balance = Column(DECIMAL(15, 2), nullable=False)
    margin_used = Column(DECIMAL(15, 2), default=0)
    
    # Performance metrics
    total_pnl = Column(DECIMAL(15, 2), default=0)
    realized_pnl = Column(DECIMAL(15, 2), default=0)
    unrealized_pnl = Column(DECIMAL(15, 2), default=0)
    daily_pnl = Column(DECIMAL(15, 2), default=0)
    
    # Trading statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(DECIMAL(10, 4), default=0)
    current_drawdown = Column(DECIMAL(10, 4), default=0)
    max_leverage = Column(Float, default=1.0)
    current_leverage = Column(Float, default=0.0)
    
    # Account settings
    max_position_size = Column(DECIMAL(15, 2))
    max_daily_loss = Column(DECIMAL(15, 2))
    max_positions = Column(Integer, default=20)
    margin_ratio = Column(Float, default=1.0)
    
    # Activity tracking
    last_trade_time = Column(String(30))    # ISO datetime string
    last_reset_time = Column(String(30))    # ISO datetime string
    reset_count = Column(Integer, default=0)
    
    # Risk management flags
    is_risk_limited = Column(Boolean, default=False)
    risk_limit_reason = Column(String(255))
    auto_liquidation_enabled = Column(Boolean, default=True)
    
    # Relationships
    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    trades = relationship("PaperTrade", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("PaperOrder", back_populates="account", cascade="all, delete-orphan")
    deployed_strategies = relationship("StrategyDeployment", back_populates="account", cascade="all, delete-orphan")
    performance_snapshots = relationship("AccountPerformanceSnapshot", back_populates="account", cascade="all, delete-orphan")


class Position(BaseModel):
    """
    Current position in paper trading account.
    """
    __tablename__ = "positions"
    
    account_id = Column(UUID(as_uuid=True), ForeignKey("paper_accounts.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum(PositionSide), nullable=False)
    
    # Position size
    quantity = Column(DECIMAL(18, 8), nullable=False)
    avg_price = Column(DECIMAL(18, 8), nullable=False)
    current_price = Column(DECIMAL(18, 8), nullable=False)
    market_value = Column(DECIMAL(15, 2), nullable=False)
    
    # PnL calculation
    unrealized_pnl = Column(DECIMAL(15, 2), nullable=False)
    unrealized_pnl_percentage = Column(DECIMAL(8, 4), nullable=False)
    
    # Position tracking
    opened_at = Column(String(30), nullable=False)  # ISO datetime string
    last_updated = Column(String(30), nullable=False)
    
    # Risk metrics
    stop_loss_price = Column(DECIMAL(18, 8))
    take_profit_price = Column(DECIMAL(18, 8))
    max_loss = Column(DECIMAL(15, 2))
    max_gain = Column(DECIMAL(15, 2))
    
    # Margin information
    margin_required = Column(DECIMAL(15, 2), default=0)
    leverage = Column(Float, default=1.0)
    
    # Strategy context
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"))
    entry_signal = Column(String(255))
    entry_conditions = Column(JSON, default=dict)
    
    # Relationships
    account = relationship("PaperAccount", back_populates="positions")
    strategy = relationship("Strategy")


class PaperTrade(BaseModel):
    """
    Executed trade in paper trading system.
    """
    __tablename__ = "paper_trades"
    
    account_id = Column(UUID(as_uuid=True), ForeignKey("paper_accounts.id"), nullable=False, index=True)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("paper_trading_sessions.id"), index=True)
    
    # Trade identification
    trade_id = Column(String(100), nullable=False, unique=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    
    # Trade execution
    quantity = Column(DECIMAL(18, 8), nullable=False)
    price = Column(DECIMAL(18, 8), nullable=False)
    timestamp = Column(String(30), nullable=False, index=True)  # ISO datetime string
    
    # Order information
    order_type = Column(String(20), default="market")  # market, limit, stop
    order_id = Column(UUID(as_uuid=True), ForeignKey("paper_orders.id"))
    
    # Cost calculation
    commission = Column(DECIMAL(10, 2), default=0)
    slippage = Column(DECIMAL(10, 2), default=0)
    total_cost = Column(DECIMAL(15, 2), nullable=False)
    
    # PnL (for closing trades)
    pnl = Column(DECIMAL(15, 2))
    pnl_percentage = Column(DECIMAL(8, 4))
    
    # Market context
    market_price = Column(DECIMAL(18, 8))  # Market price at execution
    bid_price = Column(DECIMAL(18, 8))
    ask_price = Column(DECIMAL(18, 8))
    spread = Column(DECIMAL(18, 8))
    
    # Trade context
    is_virtual = Column(Boolean, default=True, nullable=False)
    execution_latency_ms = Column(Integer)  # Simulated execution delay
    
    # Strategy context
    signal_name = Column(String(255))
    signal_strength = Column(Float)
    entry_conditions = Column(JSON, default=dict)
    
    # Portfolio impact
    portfolio_value_before = Column(DECIMAL(15, 2))
    portfolio_value_after = Column(DECIMAL(15, 2))
    position_size_percentage = Column(DECIMAL(8, 4))
    
    # Relationships
    account = relationship("PaperAccount", back_populates="trades")
    strategy = relationship("Strategy")
    order = relationship("PaperOrder", back_populates="trades")


class PaperOrder(BaseModel):
    """
    Order management for paper trading.
    """
    __tablename__ = "paper_orders"
    
    account_id = Column(UUID(as_uuid=True), ForeignKey("paper_accounts.id"), nullable=False, index=True)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), index=True)
    
    # Order identification
    order_id = Column(String(100), nullable=False, unique=True, index=True)
    client_order_id = Column(String(100), index=True)
    
    # Order details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False)  # market, limit, stop, stop_limit
    
    # Quantities and prices
    quantity = Column(DECIMAL(18, 8), nullable=False)
    filled_quantity = Column(DECIMAL(18, 8), default=0)
    remaining_quantity = Column(DECIMAL(18, 8))
    
    price = Column(DECIMAL(18, 8))  # Limit price
    stop_price = Column(DECIMAL(18, 8))  # Stop price
    avg_fill_price = Column(DECIMAL(18, 8))
    
    # Order status and timing
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    created_at_time = Column(String(30), nullable=False)  # ISO datetime string
    updated_at_time = Column(String(30), nullable=False)
    filled_at_time = Column(String(30))
    
    # Time in force
    time_in_force = Column(String(10), default="DAY")  # DAY, GTC, IOC, FOK
    expire_time = Column(String(30))
    
    # Order conditions
    conditions = Column(JSON, default=dict)
    trigger_conditions = Column(JSON, default=dict)
    
    # Execution details
    commission = Column(DECIMAL(10, 2), default=0)
    slippage = Column(DECIMAL(10, 2), default=0)
    reject_reason = Column(String(255))
    
    # Market data at order time
    market_price_at_creation = Column(DECIMAL(18, 8))
    bid_ask_spread_at_creation = Column(DECIMAL(18, 8))
    
    # Relationships
    account = relationship("PaperAccount", back_populates="orders")
    strategy = relationship("Strategy")
    session = relationship("PaperTradingSession", back_populates="orders")
    trades = relationship("PaperTrade", back_populates="order", cascade="all, delete-orphan")


class StrategyDeployment(BaseModel, UserMixin):
    """
    Strategy deployment to paper trading account.
    """
    __tablename__ = "strategy_deployments"
    
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("paper_accounts.id"), nullable=False, index=True)
    
    # Deployment information
    deployment_name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(StrategyDeploymentStatus), default=StrategyDeploymentStatus.DEPLOYING, nullable=False, index=True)
    
    # Deployment configuration
    allocated_capital = Column(DECIMAL(15, 2), nullable=False)
    max_position_size = Column(DECIMAL(15, 2))
    max_daily_loss = Column(DECIMAL(15, 2))
    risk_parameters = Column(JSON, default=dict)
    
    # Execution settings
    symbols = Column(StringArray(), nullable=False)
    timeframe = Column(String(20), nullable=False)
    execution_mode = Column(String(50), default="live")  # live, simulation
    
    # Performance tracking
    total_pnl = Column(DECIMAL(15, 2), default=0)
    daily_pnl = Column(DECIMAL(15, 2), default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    
    # Timing
    deployed_at = Column(String(30), nullable=False)    # ISO datetime string
    last_signal_at = Column(String(30))                 # ISO datetime string
    stopped_at = Column(String(30))                     # ISO datetime string
    
    # Error handling
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    last_error_at = Column(String(30))
    
    # Resource usage
    cpu_usage_percentage = Column(Float, default=0.0)
    memory_usage_mb = Column(Integer, default=0)
    
    # Relationships
    strategy = relationship("Strategy")
    account = relationship("PaperAccount", back_populates="deployed_strategies")


class AccountPerformanceSnapshot(BaseModel):
    """
    Periodic performance snapshots for paper trading accounts.
    """
    __tablename__ = "account_performance_snapshots"
    
    account_id = Column(UUID(as_uuid=True), ForeignKey("paper_accounts.id"), nullable=False, index=True)
    snapshot_time = Column(String(30), nullable=False, index=True)  # ISO datetime string
    
    # Portfolio values
    total_value = Column(DECIMAL(15, 2), nullable=False)
    cash_balance = Column(DECIMAL(15, 2), nullable=False)
    positions_value = Column(DECIMAL(15, 2), nullable=False)
    margin_used = Column(DECIMAL(15, 2), default=0)
    
    # Performance metrics
    daily_return = Column(DECIMAL(10, 6))
    cumulative_return = Column(DECIMAL(10, 4))
    volatility = Column(DECIMAL(10, 4))
    sharpe_ratio = Column(Float)
    max_drawdown = Column(DECIMAL(10, 4))
    
    # Trading activity
    trades_today = Column(Integer, default=0)
    volume_today = Column(DECIMAL(15, 2), default=0)
    commission_paid_today = Column(DECIMAL(10, 2), default=0)
    
    # Position summary
    open_positions = Column(Integer, default=0)
    long_positions = Column(Integer, default=0)
    short_positions = Column(Integer, default=0)
    largest_position_percentage = Column(DECIMAL(8, 4))
    
    # Risk metrics
    leverage = Column(Float, default=0.0)
    risk_score = Column(Float)  # 0-100 risk score
    
    # Market context
    market_conditions = Column(JSON, default=dict)
    correlation_to_market = Column(Float)
    
    # Relationships
    account = relationship("PaperAccount", back_populates="performance_snapshots")


class PaperTradingSettings(BaseModel, UserMixin):
    """
    Global paper trading settings and preferences.
    """
    __tablename__ = "paper_trading_settings"
    
    # Execution settings
    default_slippage = Column(DECIMAL(8, 6), default=0.0005)
    default_commission = Column(DECIMAL(8, 6), default=0.001)
    execution_delay_ms = Column(Integer, default=100)
    price_improvement_enabled = Column(Boolean, default=True)
    
    # Risk management
    max_leverage = Column(Float, default=5.0)
    max_position_concentration = Column(DECIMAL(4, 2), default=0.20)  # 20%
    auto_liquidation_threshold = Column(DECIMAL(4, 2), default=0.80)  # 80% of account
    
    # Market data
    use_real_time_data = Column(Boolean, default=True)
    data_provider = Column(String(100), default="internal")
    data_latency_ms = Column(Integer, default=50)
    
    # Notifications
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=False)
    trade_confirmations = Column(Boolean, default=True)
    daily_reports = Column(Boolean, default=True)
    
    # Advanced features
    partial_fills_enabled = Column(Boolean, default=True)
    order_rejection_rate = Column(DECIMAL(4, 2), default=0.01)  # 1%
    market_impact_simulation = Column(Boolean, default=False)
    
    # Performance benchmarks
    benchmark_symbols = Column(StringArray(), default=list)
    benchmark_weights = Column(FloatArray(), default=list)


class PaperTradingSession(BaseModel, UserMixin):
    """
    Paper trading session for tracking trading activities.
    """
    __tablename__ = "paper_trading_sessions"
    
    # Session identification
    session_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Session configuration
    account_id = Column(UUID(as_uuid=True), ForeignKey("paper_accounts.id"), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), index=True)
    
    # Session status
    status = Column(String(50), default="active", nullable=False, index=True)
    started_at = Column(String(30), nullable=False)  # ISO datetime string
    ended_at = Column(String(30))  # ISO datetime string
    
    # Trading parameters
    initial_balance = Column(DECIMAL(20, 8), nullable=False)
    current_balance = Column(DECIMAL(20, 8), nullable=False)
    max_drawdown = Column(DECIMAL(10, 4), default=0.0)
    
    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(20, 8), default=0.0)
    
    # Risk metrics
    max_position_size = Column(DECIMAL(20, 8))
    leverage_used = Column(Float, default=1.0)
    
    # Session settings
    session_config = Column(JSON, default=dict)
    
    # Relationships
    account = relationship("PaperAccount")
    orders = relationship("PaperOrder", back_populates="session")
    positions = relationship("PaperPosition", back_populates="session")
    transactions = relationship("PaperTransaction", back_populates="session")


class PaperPosition(BaseModel, UserMixin):
    """
    Paper trading position model.
    """
    __tablename__ = "paper_positions"
    
    # Position identification
    session_id = Column(UUID(as_uuid=True), ForeignKey("paper_trading_sessions.id"), nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    
    # Position details
    side = Column(Enum(PositionSide), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    avg_entry_price = Column(DECIMAL(20, 8), nullable=False)
    current_price = Column(DECIMAL(20, 8))
    
    # P&L
    unrealized_pnl = Column(DECIMAL(20, 8), default=0.0)
    realized_pnl = Column(DECIMAL(20, 8), default=0.0)
    
    # Risk metrics
    stop_loss = Column(DECIMAL(20, 8))
    take_profit = Column(DECIMAL(20, 8))
    
    # Timestamps
    opened_at = Column(String(30), nullable=False)
    closed_at = Column(String(30))
    
    # Relationships
    session = relationship("PaperTradingSession", back_populates="positions")


class PaperTransaction(BaseModel, UserMixin):
    """
    Paper trading transaction model.
    """
    __tablename__ = "paper_transactions"
    
    # Transaction identification
    session_id = Column(UUID(as_uuid=True), ForeignKey("paper_trading_sessions.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("paper_orders.id"))
    
    # Transaction details
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=False)
    
    # Fees and costs
    commission = Column(DECIMAL(20, 8), default=0.0)
    slippage = Column(DECIMAL(20, 8), default=0.0)
    
    # Timestamps
    executed_at = Column(String(30), nullable=False)
    
    # Relationships
    session = relationship("PaperTradingSession", back_populates="transactions")
    order = relationship("PaperOrder")


class PaperPortfolioSnapshot(BaseModel, UserMixin):
    """
    Paper trading portfolio snapshot model.
    """
    __tablename__ = "paper_portfolio_snapshots"
    
    # Snapshot identification
    session_id = Column(UUID(as_uuid=True), ForeignKey("paper_trading_sessions.id"), nullable=False)
    
    # Portfolio metrics
    total_value = Column(DECIMAL(20, 8), nullable=False)
    cash_balance = Column(DECIMAL(20, 8), nullable=False)
    positions_value = Column(DECIMAL(20, 8), default=0.0)
    
    # Performance metrics
    total_pnl = Column(DECIMAL(20, 8), default=0.0)
    daily_pnl = Column(DECIMAL(20, 8), default=0.0)
    
    # Timestamp
    snapshot_time = Column(String(30), nullable=False)
    
    # Relationships
    session = relationship("PaperTradingSession")


class MarketDataSnapshot(BaseModel):
    """
    Market data snapshot for paper trading.
    """
    __tablename__ = "market_data_snapshots"
    
    # Market data
    symbol = Column(String(50), nullable=False, index=True)
    price = Column(DECIMAL(20, 8), nullable=False)
    bid = Column(DECIMAL(20, 8))
    ask = Column(DECIMAL(20, 8))
    volume = Column(DECIMAL(20, 8))
    
    # Timestamp
    timestamp = Column(String(30), nullable=False, index=True)
    
    # Market context
    market_data = Column(JSON, default=dict)