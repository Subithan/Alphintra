"""
Database models for Phase 5: Backtesting Engine.
Comprehensive backtesting infrastructure with multiple methodologies and detailed trade tracking.
"""

import enum
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, JSON, ForeignKey, Index, CheckConstraint, DECIMAL
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base


class BacktestStatus(enum.Enum):
    """Backtest job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class BacktestMethodology(enum.Enum):
    """Backtesting methodology types."""
    STANDARD = "standard"
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"
    CROSS_VALIDATION = "cross_validation"
    PAPER_TRADING = "paper_trading"


class TradeSide(enum.Enum):
    """Trade side (buy/sell)."""
    BUY = "buy"
    SELL = "sell"


class OrderType(enum.Enum):
    """Order type for trades."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class ExitReason(enum.Enum):
    """Reason for exiting a trade."""
    SIGNAL = "signal"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TIME_LIMIT = "time_limit"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"
    RISK_MANAGEMENT = "risk_management"
    END_OF_BACKTEST = "end_of_backtest"


class PositionSizing(enum.Enum):
    """Position sizing algorithms."""
    FIXED_AMOUNT = "fixed_amount"
    FIXED_PERCENTAGE = "fixed_percentage"
    KELLY_CRITERION = "kelly_criterion"
    RISK_PARITY = "risk_parity"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    OPTIMAL_F = "optimal_f"


class BacktestJob(Base):
    """Main backtest job configuration and results."""
    __tablename__ = "backtest_jobs"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    strategy_id = Column(PostgresUUID(as_uuid=True), ForeignKey('strategies.id'), nullable=False)
    dataset_id = Column(PostgresUUID(as_uuid=True), ForeignKey('datasets.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Backtest configuration
    methodology = Column(String(50), nullable=False, default=BacktestMethodology.STANDARD.value)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(DECIMAL(20, 8), nullable=False, default=Decimal('100000.00'))
    commission_rate = Column(DECIMAL(10, 6), nullable=False, default=Decimal('0.001'))
    slippage_rate = Column(DECIMAL(10, 6), nullable=False, default=Decimal('0.0005'))
    position_sizing = Column(String(50), nullable=False, default=PositionSizing.FIXED_PERCENTAGE.value)
    position_sizing_config = Column(JSON, default={})
    
    # Risk management
    max_position_size = Column(DECIMAL(10, 6), default=Decimal('0.1'))  # 10% max per position
    max_portfolio_risk = Column(DECIMAL(10, 6), default=Decimal('0.02'))  # 2% max portfolio risk
    stop_loss_pct = Column(DECIMAL(10, 6))
    take_profit_pct = Column(DECIMAL(10, 6))
    max_drawdown_limit = Column(DECIMAL(10, 6), default=Decimal('0.2'))  # 20% max drawdown
    
    # Execution settings
    execution_delay_ms = Column(Integer, default=100)  # Execution delay simulation
    price_improvement_pct = Column(DECIMAL(10, 6), default=Decimal('0.0'))
    partial_fill_probability = Column(DECIMAL(5, 4), default=Decimal('0.05'))
    
    # Status and timing
    status = Column(String(20), nullable=False, default=BacktestStatus.PENDING.value)
    progress_percentage = Column(Integer, default=0)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    # Results summary
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_return = Column(DECIMAL(15, 8), default=Decimal('0.0'))
    total_return_pct = Column(DECIMAL(10, 6), default=Decimal('0.0'))
    annualized_return = Column(DECIMAL(10, 6), default=Decimal('0.0'))
    max_drawdown = Column(DECIMAL(10, 6), default=Decimal('0.0'))
    sharpe_ratio = Column(DECIMAL(10, 6))
    sortino_ratio = Column(DECIMAL(10, 6))
    calmar_ratio = Column(DECIMAL(10, 6))
    win_rate = Column(DECIMAL(5, 4), default=Decimal('0.0'))
    profit_factor = Column(DECIMAL(10, 6))
    
    # Additional configuration
    benchmark_symbol = Column(String(20))
    benchmark_return = Column(DECIMAL(10, 6))
    alpha = Column(DECIMAL(10, 6))
    beta = Column(DECIMAL(10, 6))
    
    # Metadata
    backtest_config = Column(JSON, default={})
    error_details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    strategy = relationship("Strategy", back_populates="backtest_jobs")
    dataset = relationship("Dataset", back_populates="backtest_jobs")
    trades = relationship("BacktestTrade", back_populates="backtest_job", cascade="all, delete-orphan")
    daily_returns = relationship("DailyReturn", back_populates="backtest_job", cascade="all, delete-orphan")
    portfolio_snapshots = relationship("PortfolioSnapshot", back_populates="backtest_job", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetric", back_populates="backtest_job", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_user_strategy', 'user_id', 'strategy_id'),
        Index('idx_backtest_status_created', 'status', 'created_at'),
        Index('idx_backtest_date_range', 'start_date', 'end_date'),
        CheckConstraint('start_date <= end_date', name='check_date_range'),
        CheckConstraint('initial_capital > 0', name='check_positive_capital'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='check_progress_range'),
    )

    @validates('methodology')
    def validate_methodology(self, key, methodology):
        if methodology not in [m.value for m in BacktestMethodology]:
            raise ValueError(f"Invalid methodology: {methodology}")
        return methodology

    @validates('position_sizing')
    def validate_position_sizing(self, key, position_sizing):
        if position_sizing not in [p.value for p in PositionSizing]:
            raise ValueError(f"Invalid position sizing: {position_sizing}")
        return position_sizing


class BacktestTrade(Base):
    """Individual trade records from backtesting."""
    __tablename__ = "backtest_trades"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    backtest_job_id = Column(PostgresUUID(as_uuid=True), ForeignKey('backtest_jobs.id'), nullable=False)
    
    # Trade identification
    trade_id = Column(String(100), nullable=False)  # Internal trade ID
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # buy/sell
    
    # Entry details
    entry_date = Column(DateTime(timezone=True), nullable=False)
    entry_price = Column(DECIMAL(20, 8), nullable=False)
    entry_quantity = Column(DECIMAL(20, 8), nullable=False)
    entry_value = Column(DECIMAL(20, 8), nullable=False)
    entry_commission = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    entry_slippage = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    entry_order_type = Column(String(20), default=OrderType.MARKET.value)
    
    # Exit details
    exit_date = Column(DateTime(timezone=True))
    exit_price = Column(DECIMAL(20, 8))
    exit_quantity = Column(DECIMAL(20, 8))
    exit_value = Column(DECIMAL(20, 8))
    exit_commission = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    exit_slippage = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    exit_order_type = Column(String(20), default=OrderType.MARKET.value)
    exit_reason = Column(String(30))
    
    # Trade performance
    pnl = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    pnl_pct = Column(DECIMAL(10, 6), default=Decimal('0.0'))
    holding_period_days = Column(Integer)
    
    # Risk metrics
    mae = Column(DECIMAL(20, 8))  # Maximum Adverse Excursion
    mfe = Column(DECIMAL(20, 8))  # Maximum Favorable Excursion
    risk_amount = Column(DECIMAL(20, 8))
    risk_reward_ratio = Column(DECIMAL(10, 6))
    
    # Portfolio context
    portfolio_value_at_entry = Column(DECIMAL(20, 8))
    position_size_pct = Column(DECIMAL(10, 6))
    portfolio_allocation_pct = Column(DECIMAL(10, 6))
    
    # Strategy context
    signal_strength = Column(DECIMAL(5, 4))
    confidence_score = Column(DECIMAL(5, 4))
    strategy_context = Column(JSON, default={})
    
    # Execution details
    fill_time_ms = Column(Integer)  # Simulated fill time
    partial_fill = Column(Boolean, default=False)
    rejected = Column(Boolean, default=False)
    rejection_reason = Column(String(255))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    backtest_job = relationship("BacktestJob", back_populates="trades")

    # Indexes
    __table_args__ = (
        Index('idx_trade_backtest_symbol', 'backtest_job_id', 'symbol'),
        Index('idx_trade_entry_date', 'entry_date'),
        Index('idx_trade_exit_date', 'exit_date'),
        Index('idx_trade_pnl', 'pnl'),
        Index('idx_trade_side_symbol', 'side', 'symbol'),
        CheckConstraint('entry_quantity > 0', name='check_positive_quantity'),
        CheckConstraint('entry_price > 0', name='check_positive_price'),
    )

    @validates('side')
    def validate_side(self, key, side):
        if side not in [s.value for s in TradeSide]:
            raise ValueError(f"Invalid trade side: {side}")
        return side

    @validates('exit_reason')
    def validate_exit_reason(self, key, exit_reason):
        if exit_reason and exit_reason not in [r.value for r in ExitReason]:
            raise ValueError(f"Invalid exit reason: {exit_reason}")
        return exit_reason


class DailyReturn(Base):
    """Daily portfolio returns and statistics."""
    __tablename__ = "daily_returns"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    backtest_job_id = Column(PostgresUUID(as_uuid=True), ForeignKey('backtest_jobs.id'), nullable=False)
    
    date = Column(Date, nullable=False)
    portfolio_value = Column(DECIMAL(20, 8), nullable=False)
    cash_balance = Column(DECIMAL(20, 8), nullable=False)
    invested_amount = Column(DECIMAL(20, 8), nullable=False)
    
    # Returns
    daily_return = Column(DECIMAL(10, 6), default=Decimal('0.0'))
    daily_return_pct = Column(DECIMAL(10, 6), default=Decimal('0.0'))
    cumulative_return = Column(DECIMAL(15, 8), default=Decimal('0.0'))
    cumulative_return_pct = Column(DECIMAL(10, 6), default=Decimal('0.0'))
    
    # Benchmark comparison
    benchmark_return = Column(DECIMAL(10, 6))
    benchmark_cumulative_return = Column(DECIMAL(10, 6))
    excess_return = Column(DECIMAL(10, 6))
    
    # Risk metrics
    volatility = Column(DECIMAL(10, 6))
    drawdown = Column(DECIMAL(10, 6), default=Decimal('0.0'))
    drawdown_duration_days = Column(Integer, default=0)
    
    # Position metrics
    positions_count = Column(Integer, default=0)
    exposure_pct = Column(DECIMAL(5, 4), default=Decimal('0.0'))
    leverage = Column(DECIMAL(10, 6), default=Decimal('1.0'))
    
    # Trading activity
    trades_opened = Column(Integer, default=0)
    trades_closed = Column(Integer, default=0)
    trade_pnl = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    commission_paid = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    backtest_job = relationship("BacktestJob", back_populates="daily_returns")

    # Indexes
    __table_args__ = (
        Index('idx_daily_return_backtest_date', 'backtest_job_id', 'date'),
        Index('idx_daily_return_date', 'date'),
        Index('idx_daily_return_portfolio_value', 'portfolio_value'),
        CheckConstraint('portfolio_value >= 0', name='check_non_negative_portfolio'),
        CheckConstraint('cash_balance >= 0', name='check_non_negative_cash'),
    )


class PortfolioSnapshot(Base):
    """Portfolio composition snapshots during backtesting."""
    __tablename__ = "portfolio_snapshots"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    backtest_job_id = Column(PostgresUUID(as_uuid=True), ForeignKey('backtest_jobs.id'), nullable=False)
    
    timestamp = Column(DateTime(timezone=True), nullable=False)
    portfolio_value = Column(DECIMAL(20, 8), nullable=False)
    cash_balance = Column(DECIMAL(20, 8), nullable=False)
    
    # Holdings breakdown
    holdings = Column(JSON, default={})  # {"AAPL": {"quantity": 100, "value": 15000, "weight": 0.15}}
    positions_count = Column(Integer, default=0)
    
    # Risk metrics at snapshot
    total_exposure = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    max_position_weight = Column(DECIMAL(5, 4), default=Decimal('0.0'))
    concentration_risk = Column(DECIMAL(5, 4), default=Decimal('0.0'))
    
    # Performance since last snapshot
    return_since_last = Column(DECIMAL(10, 6))
    period_high = Column(DECIMAL(20, 8))
    period_low = Column(DECIMAL(20, 8))
    
    # Strategy context
    signal_count = Column(Integer, default=0)
    active_signals = Column(JSON, default={})
    
    # Metadata
    snapshot_trigger = Column(String(50))  # 'daily', 'trade', 'signal', 'manual'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    backtest_job = relationship("BacktestJob", back_populates="portfolio_snapshots")

    # Indexes
    __table_args__ = (
        Index('idx_snapshot_backtest_timestamp', 'backtest_job_id', 'timestamp'),
        Index('idx_snapshot_trigger', 'snapshot_trigger'),
        CheckConstraint('portfolio_value >= 0', name='check_non_negative_snapshot_value'),
        CheckConstraint('positions_count >= 0', name='check_non_negative_positions'),
    )


class BacktestComparison(Base):
    """Comparison between multiple backtest runs."""
    __tablename__ = "backtest_comparisons"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Backtest IDs being compared
    backtest_ids = Column(JSON, nullable=False)  # List of backtest job IDs
    
    # Comparison metrics
    comparison_results = Column(JSON, default={})
    winner_criteria = Column(JSON, default={})  # Criteria used to determine winner
    
    # Statistical tests
    statistical_tests = Column(JSON, default={})  # T-tests, chi-square, etc.
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_comparison_user', 'user_id'),
        Index('idx_comparison_created', 'created_at'),
    )


class BacktestTemplate(Base):
    """Reusable backtest configuration templates."""
    __tablename__ = "backtest_templates"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Template configuration
    template_config = Column(JSON, nullable=False)
    methodology = Column(String(50), nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    
    # Sharing
    is_public = Column(Boolean, default=False)
    tags = Column(JSON, default=[])
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_template_user_public', 'user_id', 'is_public'),
        Index('idx_template_methodology', 'methodology'),
        Index('idx_template_usage', 'usage_count'),
    )


class PerformanceMetric(Base):
    """Detailed performance metrics for backtests."""
    __tablename__ = "performance_metrics"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    backtest_job_id = Column(PostgresUUID(as_uuid=True), ForeignKey('backtest_jobs.id'), nullable=False)
    
    metric_category = Column(String(50), nullable=False)  # 'return', 'risk', 'efficiency', 'stability'
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(DECIMAL(15, 8), nullable=False)
    metric_percentile = Column(DECIMAL(5, 4))  # Percentile vs benchmark/universe
    
    # Calculation details
    calculation_period = Column(String(50))  # 'daily', 'monthly', 'yearly', 'full_period'
    calculation_method = Column(String(100))  # Method used to calculate
    calculation_parameters = Column(JSON, default={})
    
    # Confidence and stability
    confidence_interval_95 = Column(JSON)  # {"lower": 0.05, "upper": 0.15}
    statistical_significance = Column(DECIMAL(5, 4))
    
    # Benchmark comparison
    benchmark_value = Column(DECIMAL(15, 8))
    excess_value = Column(DECIMAL(15, 8))
    
    # Metadata
    calculation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    backtest_job = relationship("BacktestJob", back_populates="performance_metrics")

    # Indexes
    __table_args__ = (
        Index('idx_metric_backtest_category', 'backtest_job_id', 'metric_category'),
        Index('idx_metric_name_category', 'metric_name', 'metric_category'),
        Index('idx_metric_value', 'metric_value'),
    )


class BacktestAlert(Base):
    """Alerts and notifications during backtesting."""
    __tablename__ = "backtest_alerts"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    backtest_job_id = Column(PostgresUUID(as_uuid=True), ForeignKey('backtest_jobs.id'), nullable=False)
    
    alert_type = Column(String(50), nullable=False)  # 'drawdown', 'performance', 'risk', 'system'
    severity = Column(String(20), nullable=False)    # 'info', 'warning', 'critical'
    message = Column(Text, nullable=False)
    
    # Alert details
    trigger_value = Column(DECIMAL(15, 8))
    threshold_value = Column(DECIMAL(15, 8))
    alert_timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Context
    context_data = Column(JSON, default={})
    affected_symbols = Column(JSON, default=[])
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_timestamp = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    backtest_job = relationship("BacktestJob")

    # Indexes
    __table_args__ = (
        Index('idx_alert_backtest_type', 'backtest_job_id', 'alert_type'),
        Index('idx_alert_severity_timestamp', 'severity', 'alert_timestamp'),
        Index('idx_alert_resolved', 'resolved'),
    )


class BacktestResult(Base):
    """Consolidated backtest results."""
    
    __tablename__ = "backtest_results"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    backtest_job_id = Column(PostgresUUID(as_uuid=True), ForeignKey('backtest_jobs.id'), nullable=False)
    
    # Summary metrics
    total_return = Column(DECIMAL(15, 8), nullable=False)
    total_return_pct = Column(DECIMAL(10, 6), nullable=False)
    annualized_return = Column(DECIMAL(10, 6), nullable=False)
    volatility = Column(DECIMAL(10, 6), nullable=False)
    sharpe_ratio = Column(DECIMAL(10, 6))
    max_drawdown = Column(DECIMAL(10, 6), nullable=False)
    
    # Trade statistics
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    win_rate = Column(DECIMAL(5, 4), nullable=False)
    
    # Additional metrics
    profit_factor = Column(DECIMAL(10, 6))
    sortino_ratio = Column(DECIMAL(10, 6))
    calmar_ratio = Column(DECIMAL(10, 6))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    backtest_job = relationship("BacktestJob")


class Trade(Base):
    """Alias for BacktestTrade for backward compatibility."""
    
    __tablename__ = "trades"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    backtest_job_id = Column(PostgresUUID(as_uuid=True), ForeignKey('backtest_jobs.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    entry_date = Column(DateTime(timezone=True), nullable=False)
    entry_price = Column(DECIMAL(20, 8), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    exit_date = Column(DateTime(timezone=True))
    exit_price = Column(DECIMAL(20, 8))
    pnl = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    backtest_job = relationship("BacktestJob")


class EquityCurvePoint(Base):
    """Points on the equity curve for visualization."""
    
    __tablename__ = "equity_curve_points"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    backtest_job_id = Column(PostgresUUID(as_uuid=True), ForeignKey('backtest_jobs.id'), nullable=False)
    
    timestamp = Column(DateTime(timezone=True), nullable=False)
    portfolio_value = Column(DECIMAL(20, 8), nullable=False)
    cash_balance = Column(DECIMAL(20, 8), nullable=False)
    unrealized_pnl = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    realized_pnl = Column(DECIMAL(20, 8), default=Decimal('0.0'))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    backtest_job = relationship("BacktestJob")
    
    __table_args__ = (
        Index('idx_equity_curve_backtest_timestamp', 'backtest_job_id', 'timestamp'),
    )


class WalkForwardAnalysis(Base):
    """Walk-forward analysis results."""
    
    __tablename__ = "walk_forward_analysis"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    backtest_job_id = Column(PostgresUUID(as_uuid=True), ForeignKey('backtest_jobs.id'), nullable=False)
    
    window_start = Column(Date, nullable=False)
    window_end = Column(Date, nullable=False)
    training_start = Column(Date, nullable=False)
    training_end = Column(Date, nullable=False)
    testing_start = Column(Date, nullable=False)
    testing_end = Column(Date, nullable=False)
    
    # Performance metrics for this window
    return_pct = Column(DECIMAL(10, 6), nullable=False)
    sharpe_ratio = Column(DECIMAL(10, 6))
    max_drawdown = Column(DECIMAL(10, 6))
    trades_count = Column(Integer, default=0)
    
    # Model/strategy parameters used
    parameters = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    backtest_job = relationship("BacktestJob")
    
    __table_args__ = (
        Index('idx_walk_forward_backtest_window', 'backtest_job_id', 'window_start', 'window_end'),
    )