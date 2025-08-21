"""
Backtesting API endpoints for Phase 5: Backtesting Engine.
RESTful API for managing backtests, analyzing performance, and generating reports.
"""

import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator

from app.core.database import get_db
from app.core.auth import get_current_user_id, require_permission, create_rate_limit_dependency
from app.services.backtesting_engine import BacktestingEngine
from app.services.performance_calculator import PerformanceCalculator
from app.models.backtesting import (
    BacktestJob, BacktestTrade, DailyReturn, PortfolioSnapshot,
    BacktestComparison, BacktestTemplate, PerformanceMetric,
    BacktestStatus, BacktestMethodology, PositionSizing
)
from app.models.strategy import Strategy
from app.models.dataset import Dataset
from app.services.workflow_parser import WorkflowParser
from app.services.strategy_generator import StrategyGenerator

router = APIRouter(prefix="/backtesting")

# Service instances
backtesting_engine = BacktestingEngine()
performance_calculator = PerformanceCalculator()

# Rate limiting
rate_limit = create_rate_limit_dependency(requests_per_minute=20)


# Request/Response Models
class WorkflowBacktestRequest(BaseModel):
    workflow_definition: Dict[str, Any] = Field(..., description="The workflow definition from the no-code UI")
    config: Dict[str, Any] = Field(..., description="Backtesting configuration")

class BacktestJobRequest(BaseModel):
    """Request model for creating a backtest job."""
    strategy_id: str = Field(..., description="Strategy ID to backtest")
    dataset_id: str = Field(..., description="Dataset ID for backtesting")
    name: str = Field(..., min_length=1, max_length=255, description="Backtest name")
    description: Optional[str] = Field(None, max_length=1000)
    
    # Time period
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    
    # Trading parameters
    initial_capital: float = Field(default=100000.0, ge=1000.0, le=10000000.0)
    commission_rate: float = Field(default=0.001, ge=0.0, le=0.1)
    slippage_rate: float = Field(default=0.0005, ge=0.0, le=0.1)
    
    # Backtest configuration
    methodology: BacktestMethodology = Field(default=BacktestMethodology.STANDARD)
    position_sizing: PositionSizing = Field(default=PositionSizing.FIXED_PERCENTAGE)
    position_sizing_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Risk management
    max_position_size: float = Field(default=0.1, ge=0.01, le=1.0)
    max_portfolio_risk: float = Field(default=0.02, ge=0.001, le=0.5)
    stop_loss_pct: Optional[float] = Field(None, ge=0.01, le=0.5)
    take_profit_pct: Optional[float] = Field(None, ge=0.01, le=2.0)
    max_drawdown_limit: float = Field(default=0.2, ge=0.05, le=0.8)
    
    # Execution settings
    execution_delay_ms: int = Field(default=100, ge=0, le=10000)
    price_improvement_pct: float = Field(default=0.0, ge=0.0, le=0.01)
    partial_fill_probability: float = Field(default=0.05, ge=0.0, le=1.0)
    
    # Benchmark
    benchmark_symbol: Optional[str] = Field(None, max_length=20)
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('end_date')
    def validate_end_after_start(cls, v, values):
        if 'start_date' in values:
            start = datetime.strptime(values['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end <= start:
                raise ValueError('End date must be after start date')
        return v


class BacktestJobResponse(BaseModel):
    """Response model for backtest job."""
    id: str
    user_id: str
    strategy_id: str
    dataset_id: str
    name: str
    description: Optional[str]
    methodology: str
    status: str
    progress_percentage: int
    start_date: str
    end_date: str
    initial_capital: float
    commission_rate: float
    slippage_rate: float
    position_sizing: str
    max_position_size: float
    stop_loss_pct: Optional[float]
    take_profit_pct: Optional[float]
    start_time: Optional[str]
    end_time: Optional[str]
    
    # Results (if completed)
    total_trades: Optional[int]
    winning_trades: Optional[int]
    losing_trades: Optional[int]
    total_return: Optional[float]
    total_return_pct: Optional[float]
    annualized_return: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    win_rate: Optional[float]
    
    created_at: str
    updated_at: str


class TradeAnalysisRequest(BaseModel):
    """Request model for trade analysis."""
    symbol_filter: Optional[str] = None
    side_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_pnl: Optional[float] = None
    max_pnl: Optional[float] = None
    min_duration_days: Optional[int] = None
    max_duration_days: Optional[int] = None


class PerformanceAnalysisRequest(BaseModel):
    """Request model for performance analysis."""
    include_trades: bool = Field(default=True)
    include_daily_returns: bool = Field(default=True)
    include_risk_metrics: bool = Field(default=True)
    include_benchmark_comparison: bool = Field(default=True)
    rolling_window_days: int = Field(default=30, ge=1, le=252)


class BacktestComparisonRequest(BaseModel):
    """Request model for comparing backtests."""
    backtest_ids: List[str] = Field(..., min_items=2, max_items=10)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    comparison_metrics: List[str] = Field(default=[
        'total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate'
    ])


class BacktestTemplateRequest(BaseModel):
    """Request model for backtest template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    methodology: BacktestMethodology
    template_config: Dict[str, Any]
    is_public: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list)


# Backtest Job Management Endpoints
@router.post("/from-workflow", status_code=status.HTTP_202_ACCEPTED)
async def create_backtest_from_workflow(
    request: WorkflowBacktestRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create and start a backtest job from a workflow definition."""
    try:
        # This is a simplified version. In a real scenario, you would:
        # 1. Parse the workflow definition to extract strategy logic, parameters, etc.
        # 2. Generate Python code for the strategy.
        # 3. Create a Strategy record in the database.
        # 4. Create a Dataset record if it doesn't exist.
        # 5. Create and run the backtest job.

        # For now, we'll just log it and return a dummy response.
        import logging
        logging.info(f"Received backtest request from workflow for user {user_id}")

        # In a real implementation, you would generate a strategy and get a strategy_id
        # For this example, we'll assume a placeholder strategy and dataset

        # Placeholder logic
        strategy_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479" # A dummy strategy UUID
        dataset_id = "a1b2c3d4-e5f6-7890-1234-567890abcdef" # A dummy dataset UUID

        job_data = {
            "strategy_id": strategy_id,
            "dataset_id": dataset_id,
            "name": f"Workflow Backtest - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "user_id": str(user_id),
            "start_date": request.config.get("backtest_start", "2023-01-01"),
            "end_date": request.config.get("backtest_end", "2023-12-31"),
            "initial_capital": request.config.get("initial_capital", 10000),
            "commission_rate": request.config.get("commission", 0.001),
            "slippage_rate": 0.0005,
        }

        # Create a BacktestJob instance
        backtest_job = BacktestJob(**job_data)
        db.add(backtest_job)
        await db.commit()
        await db.refresh(backtest_job)

        # Start backtest in background
        background_tasks.add_task(
            _run_backtest_background,
            backtest_job.id,
            db
        )

        return {"job_id": str(backtest_job.id), "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_backtest_job(
    request: BacktestJobRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Create a new backtest job."""
    try:
        # Validate strategy and dataset existence
        strategy_exists = await _check_strategy_exists(request.strategy_id, str(user_id), db)
        if not strategy_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found or access denied"
            )
        
        dataset_exists = await _check_dataset_exists(request.dataset_id, str(user_id), db)
        if not dataset_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or access denied"
            )
        
        # Create backtest job
        job_data = request.dict()
        job_data['user_id'] = str(user_id)
        job_data['start_date'] = datetime.strptime(request.start_date, '%Y-%m-%d').date()
        job_data['end_date'] = datetime.strptime(request.end_date, '%Y-%m-%d').date()
        
        backtest_job = BacktestJob(**job_data)
        db.add(backtest_job)
        await db.commit()
        await db.refresh(backtest_job)
        
        return {
            "success": True,
            "backtest_id": str(backtest_job.id),
            "message": "Backtest job created successfully",
            "status": backtest_job.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs")
async def list_backtest_jobs(
    status_filter: Optional[str] = None,
    methodology_filter: Optional[str] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List backtest jobs for the user."""
    try:
        from sqlalchemy import select, and_, or_, desc, asc
        
        # Build query
        query = select(BacktestJob).where(BacktestJob.user_id == user_id)
        
        # Apply filters
        if status_filter:
            query = query.where(BacktestJob.status == status_filter)
        
        if methodology_filter:
            query = query.where(BacktestJob.methodology == methodology_filter)
        
        if start_date_from:
            start_date = datetime.strptime(start_date_from, '%Y-%m-%d').date()
            query = query.where(BacktestJob.start_date >= start_date)
        
        if start_date_to:
            end_date = datetime.strptime(start_date_to, '%Y-%m-%d').date()
            query = query.where(BacktestJob.start_date <= end_date)
        
        # Apply sorting
        sort_column = getattr(BacktestJob, sort_by, BacktestJob.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        backtest_jobs = result.scalars().all()
        
        # Convert to response format
        jobs_response = []
        for job in backtest_jobs:
            job_dict = {
                "id": str(job.id),
                "user_id": str(job.user_id),
                "strategy_id": str(job.strategy_id),
                "dataset_id": str(job.dataset_id),
                "name": job.name,
                "description": job.description,
                "methodology": job.methodology,
                "status": job.status,
                "progress_percentage": job.progress_percentage,
                "start_date": job.start_date.isoformat(),
                "end_date": job.end_date.isoformat(),
                "initial_capital": float(job.initial_capital),
                "commission_rate": float(job.commission_rate),
                "slippage_rate": float(job.slippage_rate),
                "position_sizing": job.position_sizing,
                "max_position_size": float(job.max_position_size),
                "stop_loss_pct": float(job.stop_loss_pct) if job.stop_loss_pct else None,
                "take_profit_pct": float(job.take_profit_pct) if job.take_profit_pct else None,
                "start_time": job.start_time.isoformat() if job.start_time else None,
                "end_time": job.end_time.isoformat() if job.end_time else None,
                "total_trades": job.total_trades,
                "winning_trades": job.winning_trades,
                "losing_trades": job.losing_trades,
                "total_return": float(job.total_return) if job.total_return else None,
                "total_return_pct": float(job.total_return_pct) if job.total_return_pct else None,
                "annualized_return": float(job.annualized_return) if job.annualized_return else None,
                "max_drawdown": float(job.max_drawdown) if job.max_drawdown else None,
                "sharpe_ratio": float(job.sharpe_ratio) if job.sharpe_ratio else None,
                "win_rate": float(job.win_rate) if job.win_rate else None,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat()
            }
            jobs_response.append(job_dict)
        
        return {
            "backtest_jobs": jobs_response,
            "total_count": len(jobs_response),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs/{backtest_id}")
async def get_backtest_job(
    backtest_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific backtest job."""
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(BacktestJob).where(
                and_(
                    BacktestJob.id == UUID(backtest_id),
                    BacktestJob.user_id == user_id
                )
            )
        )
        backtest_job = result.scalar_one_or_none()
        
        if not backtest_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest job not found"
            )
        
        # Convert to response format (same as list endpoint)
        response = BacktestJobResponse(
            id=str(backtest_job.id),
            user_id=str(backtest_job.user_id),
            strategy_id=str(backtest_job.strategy_id),
            dataset_id=str(backtest_job.dataset_id),
            name=backtest_job.name,
            description=backtest_job.description,
            methodology=backtest_job.methodology,
            status=backtest_job.status,
            progress_percentage=backtest_job.progress_percentage,
            start_date=backtest_job.start_date.isoformat(),
            end_date=backtest_job.end_date.isoformat(),
            initial_capital=float(backtest_job.initial_capital),
            commission_rate=float(backtest_job.commission_rate),
            slippage_rate=float(backtest_job.slippage_rate),
            position_sizing=backtest_job.position_sizing,
            max_position_size=float(backtest_job.max_position_size),
            stop_loss_pct=float(backtest_job.stop_loss_pct) if backtest_job.stop_loss_pct else None,
            take_profit_pct=float(backtest_job.take_profit_pct) if backtest_job.take_profit_pct else None,
            start_time=backtest_job.start_time.isoformat() if backtest_job.start_time else None,
            end_time=backtest_job.end_time.isoformat() if backtest_job.end_time else None,
            total_trades=backtest_job.total_trades,
            winning_trades=backtest_job.winning_trades,
            losing_trades=backtest_job.losing_trades,
            total_return=float(backtest_job.total_return) if backtest_job.total_return else None,
            total_return_pct=float(backtest_job.total_return_pct) if backtest_job.total_return_pct else None,
            annualized_return=float(backtest_job.annualized_return) if backtest_job.annualized_return else None,
            max_drawdown=float(backtest_job.max_drawdown) if backtest_job.max_drawdown else None,
            sharpe_ratio=float(backtest_job.sharpe_ratio) if backtest_job.sharpe_ratio else None,
            win_rate=float(backtest_job.win_rate) if backtest_job.win_rate else None,
            created_at=backtest_job.created_at.isoformat(),
            updated_at=backtest_job.updated_at.isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/jobs/{backtest_id}/start")
async def start_backtest_job(
    backtest_id: str,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("start_backtest"))
):
    """Start a backtest job."""
    try:
        from sqlalchemy import select, and_
        
        # Get backtest job
        result = await db.execute(
            select(BacktestJob).where(
                and_(
                    BacktestJob.id == UUID(backtest_id),
                    BacktestJob.user_id == user_id,
                    BacktestJob.status == BacktestStatus.PENDING.value
                )
            )
        )
        backtest_job = result.scalar_one_or_none()
        
        if not backtest_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest job not found or not in pending status"
            )
        
        # Start backtest in background
        background_tasks.add_task(
            _run_backtest_background,
            backtest_job,
            db
        )
        
        return {
            "success": True,
            "message": "Backtest started successfully",
            "backtest_id": backtest_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/jobs/{backtest_id}/cancel")
async def cancel_backtest_job(
    backtest_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Cancel a running backtest job."""
    try:
        from sqlalchemy import select, update, and_
        
        # Check if backtest exists and is running
        result = await db.execute(
            select(BacktestJob).where(
                and_(
                    BacktestJob.id == UUID(backtest_id),
                    BacktestJob.user_id == user_id,
                    BacktestJob.status.in_([BacktestStatus.PENDING.value, BacktestStatus.RUNNING.value])
                )
            )
        )
        backtest_job = result.scalar_one_or_none()
        
        if not backtest_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest job not found or cannot be cancelled"
            )
        
        # Update status to cancelled
        await db.execute(
            update(BacktestJob)
            .where(BacktestJob.id == UUID(backtest_id))
            .values(
                status=BacktestStatus.CANCELLED.value,
                end_time=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
        
        return {
            "success": True,
            "message": "Backtest cancelled successfully",
            "backtest_id": backtest_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Analysis and Reporting Endpoints
@router.get("/jobs/{backtest_id}/performance")
async def get_performance_analysis(
    backtest_id: str,
    request: PerformanceAnalysisRequest = Depends(),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive performance analysis for a backtest."""
    try:
        # Verify access
        await _verify_backtest_access(backtest_id, str(user_id), db)
        
        # Calculate performance metrics
        performance_results = await performance_calculator.calculate_comprehensive_metrics(
            UUID(backtest_id), db
        )
        
        response = {
            "backtest_id": backtest_id,
            "return_metrics": performance_results.return_metrics,
            "risk_metrics": performance_results.risk_metrics,
            "efficiency_metrics": performance_results.efficiency_metrics,
            "stability_metrics": performance_results.stability_metrics,
            "trade_metrics": performance_results.trade_metrics,
            "benchmark_metrics": performance_results.benchmark_metrics,
            "drawdown_metrics": performance_results.drawdown_metrics
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs/{backtest_id}/trades")
async def get_backtest_trades(
    backtest_id: str,
    filters: TradeAnalysisRequest = Depends(),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get trades from a backtest with optional filtering."""
    try:
        from sqlalchemy import select, and_, or_
        
        # Verify access
        await _verify_backtest_access(backtest_id, str(user_id), db)
        
        # Build query
        query = select(BacktestTrade).where(BacktestTrade.backtest_job_id == UUID(backtest_id))
        
        # Apply filters
        if filters.symbol_filter:
            query = query.where(BacktestTrade.symbol == filters.symbol_filter)
        
        if filters.side_filter:
            query = query.where(BacktestTrade.side == filters.side_filter)
        
        if filters.date_from:
            date_from = datetime.strptime(filters.date_from, '%Y-%m-%d')
            query = query.where(BacktestTrade.entry_date >= date_from)
        
        if filters.date_to:
            date_to = datetime.strptime(filters.date_to, '%Y-%m-%d')
            query = query.where(BacktestTrade.entry_date <= date_to)
        
        if filters.min_pnl is not None:
            query = query.where(BacktestTrade.pnl >= filters.min_pnl)
        
        if filters.max_pnl is not None:
            query = query.where(BacktestTrade.pnl <= filters.max_pnl)
        
        if filters.min_duration_days is not None:
            query = query.where(BacktestTrade.holding_period_days >= filters.min_duration_days)
        
        if filters.max_duration_days is not None:
            query = query.where(BacktestTrade.holding_period_days <= filters.max_duration_days)
        
        # Order by entry date and apply pagination
        query = query.order_by(BacktestTrade.entry_date).offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        trades = result.scalars().all()
        
        # Convert to response format
        trades_response = []
        for trade in trades:
            trade_dict = {
                "id": str(trade.id),
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "side": trade.side,
                "entry_date": trade.entry_date.isoformat(),
                "entry_price": float(trade.entry_price),
                "entry_quantity": float(trade.entry_quantity),
                "entry_value": float(trade.entry_value),
                "exit_date": trade.exit_date.isoformat() if trade.exit_date else None,
                "exit_price": float(trade.exit_price) if trade.exit_price else None,
                "exit_quantity": float(trade.exit_quantity) if trade.exit_quantity else None,
                "exit_value": float(trade.exit_value) if trade.exit_value else None,
                "exit_reason": trade.exit_reason,
                "pnl": float(trade.pnl) if trade.pnl else None,
                "pnl_pct": float(trade.pnl_pct) if trade.pnl_pct else None,
                "holding_period_days": trade.holding_period_days,
                "commission": float(trade.entry_commission + (trade.exit_commission or 0)),
                "slippage": float(trade.entry_slippage + (trade.exit_slippage or 0)),
                "mae": float(trade.mae) if trade.mae else None,
                "mfe": float(trade.mfe) if trade.mfe else None,
                "signal_strength": float(trade.signal_strength) if trade.signal_strength else None,
                "confidence_score": float(trade.confidence_score) if trade.confidence_score else None
            }
            trades_response.append(trade_dict)
        
        return {
            "trades": trades_response,
            "total_count": len(trades_response),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs/{backtest_id}/daily-returns")
async def get_daily_returns(
    backtest_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get daily returns data for a backtest."""
    try:
        from sqlalchemy import select, and_
        
        # Verify access
        await _verify_backtest_access(backtest_id, str(user_id), db)
        
        # Build query
        query = select(DailyReturn).where(DailyReturn.backtest_job_id == UUID(backtest_id))
        
        if date_from:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.where(DailyReturn.date >= start_date)
        
        if date_to:
            end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.where(DailyReturn.date <= end_date)
        
        query = query.order_by(DailyReturn.date)
        
        # Execute query
        result = await db.execute(query)
        daily_returns = result.scalars().all()
        
        # Convert to response format
        returns_response = []
        for dr in daily_returns:
            return_dict = {
                "date": dr.date.isoformat(),
                "portfolio_value": float(dr.portfolio_value),
                "cash_balance": float(dr.cash_balance),
                "invested_amount": float(dr.invested_amount),
                "daily_return": float(dr.daily_return) if dr.daily_return else None,
                "daily_return_pct": float(dr.daily_return_pct) if dr.daily_return_pct else None,
                "cumulative_return": float(dr.cumulative_return) if dr.cumulative_return else None,
                "cumulative_return_pct": float(dr.cumulative_return_pct) if dr.cumulative_return_pct else None,
                "drawdown": float(dr.drawdown) if dr.drawdown else None,
                "positions_count": dr.positions_count,
                "exposure_pct": float(dr.exposure_pct) if dr.exposure_pct else None,
                "benchmark_return": float(dr.benchmark_return) if dr.benchmark_return else None,
                "excess_return": float(dr.excess_return) if dr.excess_return else None
            }
            returns_response.append(return_dict)
        
        return {
            "daily_returns": returns_response,
            "total_count": len(returns_response)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Comparison and Template Endpoints
@router.post("/comparisons", status_code=status.HTTP_201_CREATED)
async def create_backtest_comparison(
    request: BacktestComparisonRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Create a comparison between multiple backtests."""
    try:
        # Verify all backtests exist and belong to user
        for backtest_id in request.backtest_ids:
            await _verify_backtest_access(backtest_id, str(user_id), db)
        
        # Create comparison
        comparison = BacktestComparison(
            user_id=user_id,
            name=request.name,
            description=request.description,
            backtest_ids=request.backtest_ids
        )
        
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)
        
        # Calculate comparison metrics (simplified for now)
        comparison_results = await _calculate_comparison_metrics(
            request.backtest_ids, request.comparison_metrics, db
        )
        
        comparison.comparison_results = comparison_results
        await db.commit()
        
        return {
            "success": True,
            "comparison_id": str(comparison.id),
            "message": "Backtest comparison created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/comparisons/{comparison_id}")
async def get_backtest_comparison(
    comparison_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get backtest comparison results."""
    try:
        from sqlalchemy import select, and_
        
        result = await db.execute(
            select(BacktestComparison).where(
                and_(
                    BacktestComparison.id == UUID(comparison_id),
                    BacktestComparison.user_id == user_id
                )
            )
        )
        comparison = result.scalar_one_or_none()
        
        if not comparison:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comparison not found"
            )
        
        return {
            "id": str(comparison.id),
            "name": comparison.name,
            "description": comparison.description,
            "backtest_ids": comparison.backtest_ids,
            "comparison_results": comparison.comparison_results,
            "statistical_tests": comparison.statistical_tests,
            "created_at": comparison.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_backtest_template(
    request: BacktestTemplateRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Create a reusable backtest template."""
    try:
        template = BacktestTemplate(
            user_id=user_id,
            name=request.name,
            description=request.description,
            methodology=request.methodology.value,
            template_config=request.template_config,
            is_public=request.is_public,
            tags=request.tags
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        return {
            "success": True,
            "template_id": str(template.id),
            "message": "Backtest template created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates")
async def list_backtest_templates(
    include_public: bool = True,
    methodology_filter: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List available backtest templates."""
    try:
        from sqlalchemy import select, or_, and_
        
        # Build query
        query = select(BacktestTemplate)
        
        if include_public:
            query = query.where(
                or_(
                    BacktestTemplate.user_id == user_id,
                    BacktestTemplate.is_public == True
                )
            )
        else:
            query = query.where(BacktestTemplate.user_id == user_id)
        
        if methodology_filter:
            query = query.where(BacktestTemplate.methodology == methodology_filter)
        
        query = query.order_by(BacktestTemplate.created_at.desc()).offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        templates = result.scalars().all()
        
        # Convert to response format
        templates_response = []
        for template in templates:
            template_dict = {
                "id": str(template.id),
                "user_id": str(template.user_id),
                "name": template.name,
                "description": template.description,
                "methodology": template.methodology,
                "is_public": template.is_public,
                "usage_count": template.usage_count,
                "tags": template.tags,
                "created_at": template.created_at.isoformat()
            }
            templates_response.append(template_dict)
        
        return {
            "templates": templates_response,
            "total_count": len(templates_response),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Utility Endpoints
@router.get("/methodologies")
async def get_backtest_methodologies():
    """Get available backtesting methodologies."""
    return {
        "methodologies": [
            {"value": method.value, "name": method.value.replace("_", " ").title()}
            for method in BacktestMethodology
        ]
    }


@router.get("/position-sizing-methods")
async def get_position_sizing_methods():
    """Get available position sizing methods."""
    return {
        "position_sizing_methods": [
            {"value": method.value, "name": method.value.replace("_", " ").title()}
            for method in PositionSizing
        ]
    }


@router.get("/health")
async def backtesting_service_health():
    """Backtesting service health check."""
    return {
        "status": "healthy",
        "service": "backtesting-engine",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "backtesting_engine": "operational",
            "performance_calculator": "operational"
        }
    }


# Helper functions
async def _check_strategy_exists(strategy_id: str, user_id: str, db: AsyncSession) -> bool:
    """Check if strategy exists and user has access."""
    try:
        from sqlalchemy import select, and_
        
        result = await db.execute(
            select(Strategy).where(
                and_(
                    Strategy.id == UUID(strategy_id),
                    Strategy.user_id == UUID(user_id)
                )
            )
        )
        return result.scalar_one_or_none() is not None
        
    except Exception:
        return False


async def _check_dataset_exists(dataset_id: str, user_id: str, db: AsyncSession) -> bool:
    """Check if dataset exists and user has access."""
    try:
        from sqlalchemy import select, and_
        
        result = await db.execute(
            select(Dataset).where(
                and_(
                    Dataset.id == UUID(dataset_id),
                    Dataset.user_id == UUID(user_id)
                )
            )
        )
        return result.scalar_one_or_none() is not None
        
    except Exception:
        return False


async def _verify_backtest_access(backtest_id: str, user_id: str, db: AsyncSession):
    """Verify user has access to backtest."""
    from sqlalchemy import select, and_
    
    result = await db.execute(
        select(BacktestJob).where(
            and_(
                BacktestJob.id == UUID(backtest_id),
                BacktestJob.user_id == UUID(user_id)
            )
        )
    )
    backtest_job = result.scalar_one_or_none()
    
    if not backtest_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found or access denied"
        )


async def _run_backtest_background(backtest_job_id: UUID, db: AsyncSession):
    """Run backtest in background task."""
    try:
        from sqlalchemy import select
        result = await db.execute(select(BacktestJob).where(BacktestJob.id == backtest_job_id))
        backtest_job = result.scalar_one_or_none()
        if backtest_job:
            await backtesting_engine.run_backtest(backtest_job, db)
    except Exception as e:
        # Log error and update job status
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Background backtest failed for job {backtest_job_id}: {str(e)}")


async def _calculate_comparison_metrics(backtest_ids: List[str], 
                                      metrics: List[str], 
                                      db: AsyncSession) -> Dict[str, Any]:
    """Calculate comparison metrics between backtests."""
    try:
        from sqlalchemy import select
        
        comparison_data = {}
        
        for backtest_id in backtest_ids:
            result = await db.execute(
                select(BacktestJob).where(BacktestJob.id == UUID(backtest_id))
            )
            job = result.scalar_one_or_none()
            
            if job:
                job_metrics = {}
                for metric in metrics:
                    if hasattr(job, metric):
                        value = getattr(job, metric)
                        job_metrics[metric] = float(value) if value is not None else None
                
                comparison_data[backtest_id] = {
                    "name": job.name,
                    "metrics": job_metrics
                }
        
        return comparison_data
        
    except Exception as e:
        return {"error": str(e)}