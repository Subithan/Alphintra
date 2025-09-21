"""
Strategy data models and schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, validator


class StrategySource(str, Enum):
    """Strategy source types."""
    AI_ML = "ai_ml"
    NO_CODE = "no_code"


class StrategyStatus(str, Enum):
    """Strategy execution status."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    LOADING = "loading"


class ExecutionMode(str, Enum):
    """Strategy execution modes."""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"


class StrategyFile(BaseModel):
    """Individual strategy file."""
    filename: str = Field(..., description="File name")
    content: str = Field(..., description="File content")
    file_type: str = Field("python", description="File type")
    encoding: str = Field("utf-8", description="File encoding")
    checksum: Optional[str] = Field(None, description="File checksum")


class StrategyPackage(BaseModel):
    """Complete strategy package with all files."""
    
    strategy_id: str = Field(..., description="Unique strategy identifier")
    source: StrategySource = Field(..., description="Strategy source")
    name: str = Field(..., description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    version: str = Field("1.0", description="Strategy version")
    
    # Files
    files: Dict[str, StrategyFile] = Field(..., description="Strategy files")
    main_file: str = Field("main.py", description="Main execution file")
    requirements: List[str] = Field(default_factory=list, description="Python requirements")
    
    # Configuration
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    symbols: List[str] = Field(default_factory=list, description="Trading symbols")
    timeframes: List[str] = Field(default_factory=list, description="Timeframes")
    
    # Metadata
    author_id: Optional[str] = Field(None, description="Strategy author")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Strategy tags")
    
    # Performance metrics (from backtesting)
    performance_metrics: Optional[Dict[str, float]] = Field(None, description="Performance metrics")
    
    @validator('files')
    def validate_main_file_exists(cls, v, values):
        main_file = values.get('main_file', 'main.py')
        if main_file not in v:
            raise ValueError(f"Main file '{main_file}' not found in files")
        return v
    
    def get_main_content(self) -> str:
        """Get the main file content."""
        return self.files[self.main_file].content
    
    def get_requirements_content(self) -> str:
        """Get requirements.txt content if exists."""
        requirements_file = self.files.get('requirements.txt')
        if requirements_file:
            return requirements_file.content
        return '\n'.join(self.requirements)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class StrategyExecution(BaseModel):
    """Strategy execution instance."""
    
    execution_id: str = Field(..., description="Unique execution identifier")
    strategy_id: str = Field(..., description="Strategy identifier")
    status: StrategyStatus = Field(StrategyStatus.INACTIVE, description="Execution status")
    mode: ExecutionMode = Field(ExecutionMode.PAPER, description="Execution mode")
    
    # Configuration
    symbols: List[str] = Field(..., description="Trading symbols")
    timeframe: str = Field("1h", description="Data timeframe")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")
    
    # Runtime information
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    stopped_at: Optional[datetime] = Field(None, description="Stop timestamp")
    last_signal_at: Optional[datetime] = Field(None, description="Last signal timestamp")
    signals_generated: int = Field(0, ge=0, description="Number of signals generated")
    
    # Performance tracking
    total_trades: int = Field(0, ge=0, description="Total trades executed")
    successful_trades: int = Field(0, ge=0, description="Successful trades")
    total_pnl: Optional[float] = Field(None, description="Total profit/loss")
    win_rate: Optional[float] = Field(None, ge=0, le=1, description="Win rate")
    
    # Error tracking
    error_count: int = Field(0, ge=0, description="Number of errors")
    last_error: Optional[str] = Field(None, description="Last error message")
    last_error_at: Optional[datetime] = Field(None, description="Last error timestamp")
    
    # Resource usage
    cpu_usage: Optional[float] = Field(None, ge=0, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, ge=0, description="Memory usage in MB")
    execution_time_avg: Optional[float] = Field(None, ge=0, description="Average execution time in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class StrategyMetrics(BaseModel):
    """Strategy performance metrics."""
    
    strategy_id: str = Field(..., description="Strategy identifier")
    time_period: str = Field(..., description="Metrics time period")
    
    # Signal metrics
    signals_generated: int = Field(0, ge=0)
    signals_executed: int = Field(0, ge=0)
    execution_rate: float = Field(0.0, ge=0, le=1)
    average_confidence: float = Field(0.0, ge=0, le=1)
    
    # Trading metrics
    total_trades: int = Field(0, ge=0)
    winning_trades: int = Field(0, ge=0)
    losing_trades: int = Field(0, ge=0)
    win_rate: float = Field(0.0, ge=0, le=1)
    
    # Financial metrics
    total_return: Optional[float] = Field(None)
    annualized_return: Optional[float] = Field(None)
    max_drawdown: Optional[float] = Field(None)
    sharpe_ratio: Optional[float] = Field(None)
    sortino_ratio: Optional[float] = Field(None)
    
    # Risk metrics
    average_risk_score: float = Field(0.0, ge=0, le=1)
    volatility: Optional[float] = Field(None, ge=0)
    beta: Optional[float] = Field(None)
    var_95: Optional[float] = Field(None)  # Value at Risk 95%
    
    # Operational metrics
    uptime_percentage: float = Field(100.0, ge=0, le=100)
    average_latency: Optional[float] = Field(None, ge=0)
    error_rate: float = Field(0.0, ge=0, le=1)
    
    # Updated timestamp
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StrategyConfiguration(BaseModel):
    """Strategy runtime configuration."""
    
    strategy_id: str = Field(..., description="Strategy identifier")
    
    # Execution settings
    enabled: bool = Field(True, description="Strategy enabled")
    mode: ExecutionMode = Field(ExecutionMode.PAPER, description="Execution mode")
    max_concurrent_signals: int = Field(5, ge=1, le=50, description="Max concurrent signals")
    signal_cooldown: int = Field(300, ge=0, description="Signal cooldown in seconds")
    
    # Market data settings
    symbols: List[str] = Field(..., description="Trading symbols")
    timeframes: List[str] = Field(["1h"], description="Data timeframes")
    lookback_periods: int = Field(100, ge=10, le=1000, description="Historical data periods")
    
    # Risk management
    max_position_size: float = Field(0.1, gt=0, le=1, description="Maximum position size")
    max_daily_loss: float = Field(0.05, gt=0, le=1, description="Maximum daily loss")
    stop_loss_percentage: float = Field(0.02, gt=0, le=0.5, description="Default stop loss")
    take_profit_percentage: float = Field(0.04, gt=0, le=1, description="Default take profit")
    
    # Signal filtering
    min_confidence_threshold: float = Field(0.6, ge=0, le=1, description="Minimum signal confidence")
    max_risk_threshold: float = Field(0.5, ge=0, le=1, description="Maximum risk score")
    
    # Notification settings
    notify_on_signals: bool = Field(True, description="Send signal notifications")
    notify_on_errors: bool = Field(True, description="Send error notifications")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")
    
    # Advanced settings
    custom_parameters: Dict[str, Any] = Field(default_factory=dict, description="Custom parameters")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StrategyListItem(BaseModel):
    """Simplified strategy item for listing."""
    
    strategy_id: str = Field(...)
    source: StrategySource = Field(...)
    name: str = Field(...)
    description: Optional[str] = Field(None)
    status: StrategyStatus = Field(...)
    mode: ExecutionMode = Field(...)
    
    # Quick stats
    signals_today: int = Field(0, ge=0)
    last_signal_at: Optional[datetime] = Field(None)
    uptime_percentage: float = Field(100.0, ge=0, le=100)
    current_pnl: Optional[float] = Field(None)
    
    # Timestamps
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }