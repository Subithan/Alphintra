"""
Database models for live strategy execution.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Boolean, Text, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.models.base import Base


class ExecutionMode(Enum):
    PAPER = "paper"
    LIVE = "live"
    SIMULATION = "simulation"


class ExecutionStatus(Enum):
    INACTIVE = "inactive"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class SignalType(Enum):
    ENTRY_LONG = "entry_long"
    ENTRY_SHORT = "entry_short"
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"
    POSITION_ADJUST = "position_adjust"
    RISK_MANAGEMENT = "risk_management"


class ExecutionEnvironment(Base):
    """Live execution environment configuration."""
    
    __tablename__ = "execution_environments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    
    # Environment type
    execution_mode = Column(String(20), nullable=False, default="paper")
    
    # Broker/Exchange configuration
    broker_name = Column(String(100), nullable=False)
    broker_config = Column(JSON, default=dict)
    api_credentials = Column(JSON, default=dict)  # Encrypted
    
    # Trading parameters
    default_commission_rate = Column(DECIMAL(8, 6), default=0.001)
    default_slippage_rate = Column(DECIMAL(8, 6), default=0.0001)
    max_leverage = Column(Float, default=1.0)
    
    # Risk limits
    max_daily_loss = Column(DECIMAL(15, 2))
    max_position_size = Column(DECIMAL(15, 2))
    max_order_size = Column(DECIMAL(15, 2))
    
    # Execution settings
    order_timeout_seconds = Column(Integer, default=300)
    max_concurrent_orders = Column(Integer, default=10)
    enable_pre_trade_checks = Column(Boolean, default=True)
    enable_post_trade_analysis = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_maintenance = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy_deployments = relationship("StrategyExecution", back_populates="environment")


class StrategyExecution(Base):
    """Live strategy execution instance."""
    
    __tablename__ = "strategy_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    environment_id = Column(Integer, ForeignKey("execution_environments.id"), nullable=False)
    
    # Execution configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Capital allocation
    allocated_capital = Column(DECIMAL(15, 2), nullable=False)
    current_capital = Column(DECIMAL(15, 2))
    
    # Trading parameters
    symbols = Column(JSON, nullable=False)  # List of symbols to trade
    timeframes = Column(JSON, nullable=False)  # List of timeframes
    position_sizing_method = Column(String(50), default="fixed_percentage")
    position_size_config = Column(JSON, default=dict)
    
    # Risk management
    max_position_size = Column(DECIMAL(15, 2))
    max_daily_loss = Column(DECIMAL(15, 2))
    stop_loss_pct = Column(DECIMAL(8, 4))
    take_profit_pct = Column(DECIMAL(8, 4))
    
    # Execution status
    status = Column(String(20), nullable=False, default="inactive")
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    last_signal_time = Column(DateTime)
    last_execution_time = Column(DateTime)
    
    # Performance tracking
    total_pnl = Column(DECIMAL(15, 2), default=0)
    realized_pnl = Column(DECIMAL(15, 2), default=0)
    unrealized_pnl = Column(DECIMAL(15, 2), default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    
    # Error handling
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    last_error_time = Column(DateTime)
    
    # Resource monitoring
    cpu_usage_pct = Column(Float, default=0.0)
    memory_usage_mb = Column(Integer, default=0)
    signal_latency_ms = Column(Integer, default=0)
    execution_latency_ms = Column(Integer, default=0)
    
    # Configuration
    config = Column(JSON, default=dict)
    extra_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="executions")
    environment = relationship("ExecutionEnvironment", back_populates="strategy_deployments")
    signals = relationship("ExecutionSignal", back_populates="strategy_execution", cascade="all, delete-orphan")
    orders = relationship("ExecutionOrder", back_populates="strategy_execution", cascade="all, delete-orphan")
    positions = relationship("ExecutionPosition", back_populates="strategy_execution", cascade="all, delete-orphan")


class ExecutionSignal(Base):
    """Trading signal generated by strategy execution."""
    
    __tablename__ = "execution_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_execution_id = Column(Integer, ForeignKey("strategy_executions.id"), nullable=False)
    
    # Signal identification
    signal_id = Column(String(100), unique=True, nullable=False, index=True)
    signal_type = Column(String(20), nullable=False)  # SignalType enum
    
    # Market data
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Signal details
    action = Column(String(20), nullable=False)  # buy, sell, hold
    quantity = Column(DECIMAL(15, 8))
    price = Column(DECIMAL(15, 8))
    confidence = Column(Float)  # 0.0 to 1.0
    
    # Risk parameters
    stop_loss = Column(DECIMAL(15, 8))
    take_profit = Column(DECIMAL(15, 8))
    position_size_pct = Column(DECIMAL(8, 4))
    
    # Signal context
    indicators = Column(JSON, default=dict)  # Technical indicator values
    features = Column(JSON, default=dict)    # ML model features
    model_output = Column(JSON, default=dict) # Raw model predictions
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    processing_latency_ms = Column(Integer)
    
    # Execution results
    order_id = Column(Integer, ForeignKey("execution_orders.id"))
    execution_status = Column(String(20), default="pending")
    execution_error = Column(Text)
    
    # Metadata
    strategy_version = Column(String(50))
    model_version = Column(String(50))
    extra_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy_execution = relationship("StrategyExecution", back_populates="signals")
    order = relationship("ExecutionOrder", back_populates="signal")


class ExecutionOrder(Base):
    """Order placed by strategy execution."""
    
    __tablename__ = "execution_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_execution_id = Column(Integer, ForeignKey("strategy_executions.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("execution_signals.id"))
    
    # Order identification
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    broker_order_id = Column(String(100), index=True)  # Broker's order ID
    
    # Order details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), nullable=False)  # market, limit, stop
    quantity = Column(DECIMAL(15, 8), nullable=False)
    price = Column(DECIMAL(15, 8))
    stop_price = Column(DECIMAL(15, 8))
    
    # Execution details
    status = Column(String(20), nullable=False, default="pending")
    filled_quantity = Column(DECIMAL(15, 8), default=0)
    remaining_quantity = Column(DECIMAL(15, 8))
    avg_fill_price = Column(DECIMAL(15, 8))
    
    # Costs
    commission = Column(DECIMAL(10, 4), default=0)
    slippage = Column(DECIMAL(10, 4), default=0)
    total_cost = Column(DECIMAL(15, 2))
    
    # Timing
    submitted_at = Column(DateTime, nullable=False)
    acknowledged_at = Column(DateTime)
    filled_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    # Performance tracking
    submission_latency_ms = Column(Integer)  # Time to submit to broker
    fill_latency_ms = Column(Integer)        # Time from submission to fill
    
    # Risk and compliance
    pre_trade_checks = Column(JSON, default=dict)
    post_trade_analysis = Column(JSON, default=dict)
    risk_score = Column(Float)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    extra_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy_execution = relationship("StrategyExecution", back_populates="orders")
    signal = relationship("ExecutionSignal", back_populates="order")
    position_updates = relationship("ExecutionPositionUpdate", back_populates="order")


class ExecutionPosition(Base):
    """Current position held by strategy execution."""
    
    __tablename__ = "execution_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_execution_id = Column(Integer, ForeignKey("strategy_executions.id"), nullable=False)
    
    # Position details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # long, short
    quantity = Column(DECIMAL(15, 8), nullable=False)
    
    # Entry details
    avg_entry_price = Column(DECIMAL(15, 8), nullable=False)
    total_cost = Column(DECIMAL(15, 2), nullable=False)
    
    # Current valuation
    current_price = Column(DECIMAL(15, 8))
    market_value = Column(DECIMAL(15, 2))
    unrealized_pnl = Column(DECIMAL(15, 2), default=0)
    unrealized_pnl_pct = Column(DECIMAL(8, 4), default=0)
    
    # Risk management
    stop_loss_price = Column(DECIMAL(15, 8))
    take_profit_price = Column(DECIMAL(15, 8))
    trailing_stop_pct = Column(DECIMAL(8, 4))
    
    # Position tracking
    opened_at = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, nullable=False)
    is_open = Column(Boolean, default=True)
    closed_at = Column(DateTime)
    
    # Performance (when closed)
    realized_pnl = Column(DECIMAL(15, 2))
    realized_pnl_pct = Column(DECIMAL(8, 4))
    holding_period_hours = Column(Integer)
    
    # Strategy context
    entry_signal_id = Column(String(100))
    exit_signal_id = Column(String(100))
    entry_reason = Column(String(255))
    exit_reason = Column(String(255))
    
    # Metadata
    extra_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy_execution = relationship("StrategyExecution", back_populates="positions")
    updates = relationship("ExecutionPositionUpdate", back_populates="position", cascade="all, delete-orphan")


class ExecutionPositionUpdate(Base):
    """Position update history."""
    
    __tablename__ = "execution_position_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("execution_positions.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("execution_orders.id"))
    
    # Update details
    update_type = Column(String(20), nullable=False)  # open, add, reduce, close
    quantity_change = Column(DECIMAL(15, 8), nullable=False)
    price = Column(DECIMAL(15, 8), nullable=False)
    
    # Position state after update
    new_quantity = Column(DECIMAL(15, 8), nullable=False)
    new_avg_price = Column(DECIMAL(15, 8), nullable=False)
    new_market_value = Column(DECIMAL(15, 2), nullable=False)
    
    # PnL impact
    realized_pnl = Column(DECIMAL(15, 2), default=0)
    unrealized_pnl_change = Column(DECIMAL(15, 2), default=0)
    
    # Metadata
    extra_metadata = Column(JSON, default=dict)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    position = relationship("ExecutionPosition", back_populates="updates")
    order = relationship("ExecutionOrder", back_populates="position_updates")


class ExecutionMetrics(Base):
    """Execution performance metrics snapshots."""
    
    __tablename__ = "execution_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_execution_id = Column(Integer, ForeignKey("strategy_executions.id"), nullable=False)
    
    # Snapshot timing
    snapshot_time = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # minute, hour, day
    
    # Portfolio metrics
    total_value = Column(DECIMAL(15, 2), nullable=False)
    cash_balance = Column(DECIMAL(15, 2), nullable=False)
    positions_value = Column(DECIMAL(15, 2), nullable=False)
    
    # Performance metrics
    period_pnl = Column(DECIMAL(15, 2), default=0)
    period_return_pct = Column(DECIMAL(8, 4), default=0)
    cumulative_pnl = Column(DECIMAL(15, 2), default=0)
    cumulative_return_pct = Column(DECIMAL(8, 4), default=0)
    
    # Risk metrics
    max_drawdown = Column(DECIMAL(8, 4), default=0)
    current_drawdown = Column(DECIMAL(8, 4), default=0)
    volatility = Column(DECIMAL(8, 4))
    sharpe_ratio = Column(Float)
    var_95 = Column(DECIMAL(15, 2))  # Value at Risk 95%
    
    # Trading activity
    signals_generated = Column(Integer, default=0)
    orders_submitted = Column(Integer, default=0)
    orders_filled = Column(Integer, default=0)
    orders_cancelled = Column(Integer, default=0)
    
    # Execution quality
    avg_fill_latency_ms = Column(Integer)
    avg_slippage_bps = Column(Integer)  # Basis points
    fill_rate_pct = Column(DECIMAL(8, 4))
    
    # Position metrics
    active_positions = Column(Integer, default=0)
    avg_position_duration_hours = Column(Float)
    win_rate_pct = Column(DECIMAL(8, 4))
    profit_factor = Column(Float)
    
    # System metrics
    cpu_usage_pct = Column(Float)
    memory_usage_mb = Column(Integer)
    signal_processing_latency_ms = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy_execution = relationship("StrategyExecution")