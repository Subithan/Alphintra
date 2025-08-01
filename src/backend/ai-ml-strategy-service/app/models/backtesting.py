"""
Backtesting related database models.
"""

from decimal import Decimal
from enum import Enum as PyEnum
from typing import Dict, Any, List

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, Enum, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, UserMixin, MetadataMixin


class BacktestMethodology(PyEnum):
    """Backtest methodology enumeration."""
    STANDARD = "standard"
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"
    CROSS_VALIDATION = "cross_validation"
    PURGED_CROSS_VALIDATION = "purged_cross_validation"


class TradeSide(PyEnum):
    """Trade side enumeration."""
    BUY = "buy"
    SELL = "sell"
    LONG = "long"
    SHORT = "short"


class OrderType(PyEnum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class ExitReason(PyEnum):
    """Trade exit reason."""
    SIGNAL = "signal"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TIMEOUT = "timeout"
    END_OF_DATA = "end_of_data"
    RISK_MANAGEMENT = "risk_management"


class BacktestJob(BaseModel, UserMixin, MetadataMixin):
    """
    Backtest job configuration and execution tracking.
    """
    __tablename__ = "backtest_jobs"
    
    # Basic information
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Time period
    start_date = Column(String(20), nullable=False)  # ISO date string
    end_date = Column(String(20), nullable=False)    # ISO date string
    
    # Trading parameters
    initial_capital = Column(DECIMAL(15, 2), nullable=False)
    commission = Column(DECIMAL(8, 6), nullable=False)
    slippage = Column(DECIMAL(8, 6), nullable=False)
    
    # Backtest configuration
    methodology = Column(Enum(BacktestMethodology), default=BacktestMethodology.STANDARD, nullable=False)
    methodology_config = Column(JSON, default=dict)  # Method-specific parameters
    
    # Execution tracking
    status = Column(String(50), default="pending", nullable=False, index=True)
    progress_percentage = Column(Integer, default=0)
    start_time = Column(String(30))      # ISO datetime string
    completed_at = Column(String(30))    # ISO datetime string
    duration_seconds = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    warnings = Column(ARRAY(String), default=list)
    
    # Resource usage
    memory_usage_mb = Column(Integer)
    cpu_time_seconds = Column(Float)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="backtest_jobs")
    dataset = relationship("Dataset", back_populates="backtest_jobs")
    results = relationship("BacktestResult", back_populates="backtest", uselist=False, cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")
    equity_curve = relationship("EquityCurvePoint", back_populates="backtest", cascade="all, delete-orphan")


class BacktestResult(BaseModel):
    """
    Comprehensive backtest performance results.
    """
    __tablename__ = "backtest_results"
    
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtest_jobs.id"), nullable=False, unique=True)
    
    # Return metrics
    total_return = Column(DECIMAL(10, 4), nullable=False)
    annualized_return = Column(DECIMAL(10, 4), nullable=False)
    excess_return = Column(DECIMAL(10, 4))  # vs benchmark
    
    # Risk metrics
    max_drawdown = Column(DECIMAL(10, 4), nullable=False)
    max_drawdown_duration = Column(Integer)  # days
    volatility = Column(DECIMAL(10, 4))
    downside_deviation = Column(DECIMAL(10, 4))
    
    # Risk-adjusted returns
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    calmar_ratio = Column(Float)
    information_ratio = Column(Float)
    treynor_ratio = Column(Float)
    
    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    
    # Trade performance
    avg_win = Column(DECIMAL(10, 2))
    avg_loss = Column(DECIMAL(10, 2))
    largest_win = Column(DECIMAL(10, 2))
    largest_loss = Column(DECIMAL(10, 2))
    avg_trade_duration = Column(Float)  # hours
    
    # Streaks
    longest_winning_streak = Column(Integer, default=0)
    longest_losing_streak = Column(Integer, default=0)
    max_consecutive_wins = Column(Integer, default=0)
    max_consecutive_losses = Column(Integer, default=0)
    
    # Statistical measures
    correlation_to_benchmark = Column(Float)
    beta = Column(Float)
    alpha = Column(Float)
    tracking_error = Column(Float)
    
    # Additional metrics
    expectancy = Column(Float)
    recovery_factor = Column(Float)
    profit_to_max_drawdown = Column(Float)
    gain_to_pain_ratio = Column(Float)
    
    # Final portfolio state
    final_capital = Column(DECIMAL(15, 2))
    cash_balance = Column(DECIMAL(15, 2))
    positions_value = Column(DECIMAL(15, 2))
    
    # Benchmark comparison
    benchmark_symbol = Column(String(20))
    benchmark_return = Column(DECIMAL(10, 4))
    outperformance = Column(DECIMAL(10, 4))
    
    # Monte Carlo results (if applicable)
    confidence_intervals = Column(JSON, default=dict)
    var_95 = Column(DECIMAL(10, 4))  # Value at Risk
    cvar_95 = Column(DECIMAL(10, 4))  # Conditional Value at Risk
    
    # Relationships
    backtest = relationship("BacktestJob", back_populates="results")


class Trade(BaseModel):
    """
    Individual trade record from backtest.
    """
    __tablename__ = "trades"
    
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtest_jobs.id"), nullable=False, index=True)
    trade_number = Column(Integer, nullable=False)
    
    # Trade identification
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum(TradeSide), nullable=False)
    quantity = Column(DECIMAL(18, 8), nullable=False)
    
    # Entry information
    entry_price = Column(DECIMAL(18, 8), nullable=False)
    entry_time = Column(String(30), nullable=False)  # ISO datetime string
    entry_reason = Column(String(100))
    
    # Exit information
    exit_price = Column(DECIMAL(18, 8))
    exit_time = Column(String(30))  # ISO datetime string
    exit_reason = Column(Enum(ExitReason))
    
    # Trade performance
    pnl = Column(DECIMAL(15, 2))
    pnl_percentage = Column(DECIMAL(8, 4))
    commission = Column(DECIMAL(10, 2))
    slippage = Column(DECIMAL(10, 2))
    net_pnl = Column(DECIMAL(15, 2))  # PnL after costs
    
    # Trade duration
    duration_hours = Column(Float)
    bars_held = Column(Integer)
    
    # Portfolio impact
    portfolio_value_before = Column(DECIMAL(15, 2))
    portfolio_value_after = Column(DECIMAL(15, 2))
    portfolio_percentage = Column(DECIMAL(8, 4))  # % of portfolio
    
    # Risk metrics
    max_adverse_excursion = Column(DECIMAL(10, 2))  # MAE
    max_favorable_excursion = Column(DECIMAL(10, 2))  # MFE
    
    # Order details
    order_type = Column(Enum(OrderType), default=OrderType.MARKET)
    limit_price = Column(DECIMAL(18, 8))
    stop_price = Column(DECIMAL(18, 8))
    
    # Context data
    market_conditions = Column(JSON, default=dict)
    indicators_at_entry = Column(JSON, default=dict)
    indicators_at_exit = Column(JSON, default=dict)
    
    # Relationships
    backtest = relationship("BacktestJob", back_populates="trades")


class EquityCurvePoint(BaseModel):
    """
    Equity curve data points for portfolio value over time.
    """
    __tablename__ = "equity_curve_points"
    
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtest_jobs.id"), nullable=False, index=True)
    timestamp = Column(String(30), nullable=False, index=True)  # ISO datetime string
    
    # Portfolio values
    total_value = Column(DECIMAL(15, 2), nullable=False)
    cash_balance = Column(DECIMAL(15, 2), nullable=False)
    positions_value = Column(DECIMAL(15, 2), nullable=False)
    
    # Returns
    daily_return = Column(DECIMAL(10, 6))
    cumulative_return = Column(DECIMAL(10, 4))
    
    # Drawdown
    drawdown = Column(DECIMAL(10, 4))
    underwater_duration = Column(Integer)  # days since last high
    
    # Benchmark comparison
    benchmark_value = Column(DECIMAL(15, 2))
    benchmark_return = Column(DECIMAL(10, 6))
    relative_performance = Column(DECIMAL(10, 4))
    
    # Risk metrics
    volatility_window = Column(DECIMAL(10, 4))  # Rolling volatility
    sharpe_window = Column(Float)               # Rolling Sharpe ratio
    
    # Market data
    market_price = Column(JSON, default=dict)   # Current market prices
    
    # Relationships
    backtest = relationship("BacktestJob", back_populates="equity_curve")


class BacktestComparison(BaseModel, UserMixin):
    """
    Comparison between multiple backtest results.
    """
    __tablename__ = "backtest_comparisons"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    backtest_ids = Column(ARRAY(String), nullable=False)  # List of backtest UUIDs
    
    # Comparison results
    comparison_metrics = Column(JSON, default=dict)
    ranking = Column(JSON, default=dict)
    statistical_tests = Column(JSON, default=dict)
    
    # Visualization data
    chart_data = Column(JSON, default=dict)
    
    # Report generation
    report_path = Column(String(500))  # Path to generated report
    report_format = Column(String(20), default="pdf")


class BacktestTemplate(BaseModel, UserMixin):
    """
    Reusable backtest configuration templates.
    """
    __tablename__ = "backtest_templates"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), index=True)
    
    # Template configuration
    default_config = Column(JSON, nullable=False)
    methodology = Column(Enum(BacktestMethodology), nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)
    
    # Validation
    is_validated = Column(Boolean, default=False)
    validation_notes = Column(Text)


class WalkForwardAnalysis(BaseModel):
    """
    Walk-forward analysis results for strategy robustness testing.
    """
    __tablename__ = "walk_forward_analyses"
    
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtest_jobs.id"), nullable=False, unique=True)
    
    # Configuration
    training_window_days = Column(Integer, nullable=False)
    testing_window_days = Column(Integer, nullable=False)
    step_size_days = Column(Integer, nullable=False)
    
    # Results summary
    total_windows = Column(Integer, nullable=False)
    profitable_windows = Column(Integer, default=0)
    consistency_score = Column(Float)  # 0-1 score
    
    # Performance across windows
    avg_return_per_window = Column(DECIMAL(10, 4))
    std_return_per_window = Column(DECIMAL(10, 4))
    min_return = Column(DECIMAL(10, 4))
    max_return = Column(DECIMAL(10, 4))
    
    # Detailed results
    window_results = Column(JSON, default=list)  # List of per-window metrics
    
    # Relationships
    backtest = relationship("BacktestJob")