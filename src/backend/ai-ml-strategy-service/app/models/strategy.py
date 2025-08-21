"""
Strategy-related database models.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, UserMixin, MetadataMixin
from app.models.types import StringArray, IntegerArray


class StrategyStatus(PyEnum):
    """Strategy status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    TESTING = "testing"
    DEPLOYED = "deployed"


class DifficultyLevel(PyEnum):
    """Strategy difficulty level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class DebugStatus(PyEnum):
    """Debug session status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Strategy(BaseModel, UserMixin, MetadataMixin):
    """
    Code-based trading strategy model.
    """
    __tablename__ = "strategies"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    code = Column(Text, nullable=False)
    language = Column(String(50), default="python", nullable=False)
    sdk_version = Column(String(50), nullable=False)
    parameters = Column(JSON, default=dict)
    status = Column(Enum(StrategyStatus), default=StrategyStatus.DRAFT, nullable=False, index=True)
    tags = Column(StringArray(), default=list)
    
    # Performance metrics (if backtested)
    total_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    win_rate = Column(Float)
    
    # Relationships
    backtest_jobs = relationship("BacktestJob", back_populates="strategy", cascade="all, delete-orphan")
    training_jobs = relationship("TrainingJob", back_populates="strategy", cascade="all, delete-orphan")
    debug_sessions = relationship("DebugSession", back_populates="strategy", cascade="all, delete-orphan")


class StrategyTemplate(BaseModel, MetadataMixin):
    """
    Strategy template for code snippets and examples.
    """
    __tablename__ = "strategy_templates"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    code = Column(Text, nullable=False)
    parameters = Column(JSON, default=dict)
    documentation = Column(Text)
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False, index=True)
    is_public = Column(Boolean, default=True, nullable=False)
    author_id = Column(UUID(as_uuid=True), nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    rating = Column(Float, default=0.0)
    tags = Column(StringArray(), default=list)


class DebugSession(BaseModel, UserMixin):
    """
    Interactive debugging session for strategies.
    """
    __tablename__ = "debug_sessions"
    
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    start_date = Column(String(20), nullable=False)  # ISO date string
    end_date = Column(String(20), nullable=False)    # ISO date string
    breakpoints = Column(IntegerArray(), default=list)
    variables = Column(JSON, default=dict)
    status = Column(Enum(DebugStatus), default=DebugStatus.ACTIVE, nullable=False)
    current_timestamp = Column(String(20))  # Current position in debug session
    
    # Relationships
    strategy = relationship("Strategy", back_populates="debug_sessions")
    dataset = relationship("Dataset", back_populates="debug_sessions")


class StrategyVersion(BaseModel, UserMixin):
    """
    Strategy version control for tracking changes.
    """
    __tablename__ = "strategy_versions"
    
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    code = Column(Text, nullable=False)
    parameters = Column(JSON, default=dict)
    change_summary = Column(Text)
    is_current = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    strategy = relationship("Strategy")


class StrategyPerformanceMetrics(BaseModel):
    """
    Detailed performance metrics for strategies.
    """
    __tablename__ = "strategy_performance_metrics"
    
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtest_jobs.id"))
    paper_account_id = Column(UUID(as_uuid=True), ForeignKey("paper_accounts.id"))
    
    # Performance metrics
    total_return = Column(Float, nullable=False)
    annualized_return = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    calmar_ratio = Column(Float)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    total_trades = Column(Integer, default=0)
    avg_trade_duration = Column(Float)  # in hours
    longest_winning_streak = Column(Integer, default=0)
    longest_losing_streak = Column(Integer, default=0)
    correlation_to_benchmark = Column(Float)
    volatility = Column(Float)
    
    # Additional metrics
    avg_win = Column(Float)
    avg_loss = Column(Float)
    largest_win = Column(Float)
    largest_loss = Column(Float)
    recovery_factor = Column(Float)
    expectancy = Column(Float)
    
    # Relationships
    strategy = relationship("Strategy")
    backtest = relationship("BacktestJob")
    paper_account = relationship("PaperAccount")