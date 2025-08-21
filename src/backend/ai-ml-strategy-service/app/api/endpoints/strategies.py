"""
Strategy development API endpoints.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user_id, require_permission, create_rate_limit_dependency
from app.services.execution_engine import ExecutionEngine
from app.services.debug_service import DebugService
from app.services.code_analysis_service import CodeAnalysisService
from app.services.strategy_service import StrategyService

router = APIRouter()

# Dependency instances (would be injected in production)
execution_engine = ExecutionEngine()
debug_service = DebugService(execution_engine)
code_analysis_service = CodeAnalysisService()
strategy_service = StrategyService(execution_engine)

# Rate limiting
rate_limit = create_rate_limit_dependency(requests_per_minute=60)


# Request/Response Models
class StrategyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    code: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)


class StrategyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    code: Optional[str] = Field(None, min_length=1)
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class StrategyExecuteRequest(BaseModel):
    dataset_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    initial_capital: Optional[float] = Field(default=100000.0, gt=0)


class CodeValidationRequest(BaseModel):
    code: str = Field(..., min_length=1)


class CodeCompletionRequest(BaseModel):
    code: str = Field(..., min_length=0)
    line: int = Field(..., ge=0)
    column: int = Field(..., ge=0)


class HoverRequest(BaseModel):
    code: str = Field(..., min_length=0)
    line: int = Field(..., ge=0)
    column: int = Field(..., ge=0)


class DebugSessionCreateRequest(BaseModel):
    strategy_id: str
    dataset_id: str
    start_date: str
    end_date: str


class DebugBreakpointRequest(BaseModel):
    line_number: int = Field(..., gt=0)
    condition: Optional[str] = None
    hit_count: Optional[int] = Field(default=0, ge=0)


class DebugEvaluateRequest(BaseModel):
    expression: str = Field(..., min_length=1)


class DebugVariableRequest(BaseModel):
    name: str = Field(..., min_length=1)
    value: Any


# Strategy CRUD Endpoints
@router.post("/strategies", status_code=status.HTTP_201_CREATED)
async def create_strategy(
    request: StrategyCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Create a new code-based strategy."""
    try:
        result = await strategy_service.create_strategy(
            strategy_data=request.dict(),
            user_id=str(user_id),
            db=db
        )
        
        if result["success"]:
            return {
                "strategy_id": result["strategy_id"],
                "validation_warnings": result.get("validation_warnings", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/strategies")
async def list_strategies(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List user's strategies with optional filtering."""
    try:
        filters = {
            "user_id": str(user_id),
            "limit": min(limit, 100),
            "offset": offset
        }
        
        if status_filter:
            filters["status"] = status_filter
        if search:
            filters["search"] = search
        
        strategies = await strategy_service.list_strategies(filters, db)
        
        return {
            "strategies": strategies,
            "total": len(strategies),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/strategies/{strategy_id}")
async def get_strategy(
    strategy_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific strategy."""
    try:
        strategy = await strategy_service.get_strategy(strategy_id, str(user_id), db)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        
        return strategy
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Update an existing strategy."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        result = await strategy_service.update_strategy(
            strategy_id=strategy_id,
            update_data=update_data,
            user_id=str(user_id),
            db=db
        )
        
        if result["success"]:
            return {
                "message": "Strategy updated successfully",
                "validation_warnings": result.get("validation_warnings", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/strategies/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a strategy."""
    try:
        result = await strategy_service.delete_strategy(strategy_id, str(user_id), db)
        
        if result["success"]:
            return {"message": "Strategy deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Strategy Execution Endpoints
@router.post("/strategies/{strategy_id}/execute")
async def execute_strategy(
    strategy_id: str,
    request: StrategyExecuteRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("execute_strategy"))
):
    """Execute a strategy with given parameters."""
    try:
        result = await strategy_service.execute_strategy(
            strategy_id=strategy_id,
            execution_config=request.dict(),
            user_id=str(user_id),
            db=db
        )
        
        if result["success"]:
            return {
                "execution_id": result["execution_id"],
                "status": "started",
                "message": "Strategy execution started"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/strategies/{strategy_id}/executions")
async def get_strategy_executions(
    strategy_id: str,
    limit: int = 20,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get execution history for a strategy."""
    try:
        executions = await strategy_service.get_strategy_executions(
            strategy_id=strategy_id,
            user_id=str(user_id),
            limit=limit,
            db=db
        )
        
        return {
            "executions": executions,
            "total": len(executions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Code Analysis Endpoints
@router.post("/code/validate")
async def validate_code(
    request: CodeValidationRequest,
    _: UUID = Depends(get_current_user_id),
    __: UUID = Depends(rate_limit)
):
    """Validate Python strategy code."""
    try:
        result = code_analysis_service.validate_code(request.code)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/code/completions")
async def get_code_completions(
    request: CodeCompletionRequest,
    _: UUID = Depends(get_current_user_id)
):
    """Get code completion suggestions."""
    try:
        completions = code_analysis_service.get_completions(
            code=request.code,
            line=request.line,
            column=request.column
        )
        
        return {"completions": completions}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/code/hover")
async def get_hover_info(
    request: HoverRequest,
    _: UUID = Depends(get_current_user_id)
):
    """Get hover information for code symbol."""
    try:
        hover_info = code_analysis_service.get_hover_info(
            code=request.code,
            line=request.line,
            column=request.column
        )
        
        return {"hover": hover_info}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/code/diagnostics")
async def get_code_diagnostics(
    request: CodeValidationRequest,
    _: UUID = Depends(get_current_user_id)
):
    """Get code diagnostics (errors, warnings, suggestions)."""
    try:
        diagnostics = code_analysis_service.get_diagnostics(request.code)
        return {"diagnostics": diagnostics}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Debug Session Endpoints
@router.post("/debug/sessions")
async def create_debug_session(
    request: DebugSessionCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("debug_strategy"))
):
    """Create a new debug session."""
    try:
        result = await debug_service.create_debug_session(
            strategy_id=request.strategy_id,
            dataset_id=request.dataset_id,
            user_id=str(user_id),
            start_date=request.start_date,
            end_date=request.end_date,
            db=db
        )
        
        if result["success"]:
            return {
                "session_id": result["session_id"],
                "debugger_info": result["debugger_info"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/debug/sessions")
async def list_debug_sessions(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List debug sessions for the user."""
    try:
        sessions = await debug_service.list_debug_sessions(str(user_id), db)
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/debug/sessions/{session_id}/state")
async def get_debug_session_state(
    session_id: str,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get current debug session state."""
    try:
        debugger = await debug_service.get_debug_session(session_id)
        
        if not debugger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debug session not found"
            )
        
        # Verify ownership (simplified)
        if debugger.user_id != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        state = debugger.get_current_state()
        return {"state": state}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/debug/sessions/{session_id}/breakpoints")
async def set_breakpoint(
    session_id: str,
    request: DebugBreakpointRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """Set a breakpoint in debug session."""
    try:
        debugger = await debug_service.get_debug_session(session_id)
        
        if not debugger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debug session not found"
            )
        
        success = debugger.set_breakpoint(
            line_number=request.line_number,
            condition=request.condition,
            hit_count=request.hit_count
        )
        
        if success:
            return {"message": "Breakpoint set successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to set breakpoint"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/debug/sessions/{session_id}/step")
async def debug_step_over(
    session_id: str,
    user_id: UUID = Depends(get_current_user_id)
):
    """Execute single step in debug session."""
    try:
        debugger = await debug_service.get_debug_session(session_id)
        
        if not debugger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debug session not found"
            )
        
        result = debugger.step_over()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/debug/sessions/{session_id}/continue")
async def debug_continue(
    session_id: str,
    user_id: UUID = Depends(get_current_user_id)
):
    """Continue debug session execution."""
    try:
        debugger = await debug_service.get_debug_session(session_id)
        
        if not debugger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debug session not found"
            )
        
        result = debugger.continue_execution()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/debug/sessions/{session_id}/variables")
async def get_debug_variables(
    session_id: str,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get current debug session variables."""
    try:
        debugger = await debug_service.get_debug_session(session_id)
        
        if not debugger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debug session not found"
            )
        
        variables = debugger.get_variables()
        return {"variables": variables}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/debug/sessions/{session_id}/evaluate")
async def debug_evaluate_expression(
    session_id: str,
    request: DebugEvaluateRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """Evaluate expression in debug context."""
    try:
        debugger = await debug_service.get_debug_session(session_id)
        
        if not debugger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debug session not found"
            )
        
        result = debugger.evaluate_expression(request.expression)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/debug/sessions/{session_id}")
async def close_debug_session(
    session_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Close and cleanup debug session."""
    try:
        result = await debug_service.close_debug_session(session_id, db)
        
        if result["success"]:
            return {"message": "Debug session closed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# SDK Documentation Endpoint
@router.get("/sdk/documentation")
async def get_sdk_documentation():
    """Get Python SDK documentation and examples."""
    try:
        # This would return comprehensive SDK documentation
        documentation = {
            "version": "1.0.0",
            "base_strategy": {
                "description": "Base class for all trading strategies",
                "methods": [
                    {
                        "name": "initialize",
                        "description": "Initialize the strategy",
                        "required": True,
                        "example": "def initialize(self):\n    self.period = self.get_parameter('period', 20)"
                    },
                    {
                        "name": "on_bar",
                        "description": "Called on each new bar of data",
                        "required": True,
                        "example": "def on_bar(self):\n    price = self.data.get_current_price('BTCUSD')"
                    }
                ]
            },
            "market_data": {
                "description": "Access market data and technical indicators",
                "methods": [
                    {
                        "name": "get_current_price",
                        "signature": "get_current_price(symbol: str) -> float",
                        "description": "Get current price for symbol"
                    },
                    {
                        "name": "sma",
                        "signature": "sma(symbol: str, period: int) -> float",
                        "description": "Simple Moving Average"
                    },
                    {
                        "name": "rsi",
                        "signature": "rsi(symbol: str, period: int = 14) -> float",
                        "description": "Relative Strength Index"
                    }
                ]
            },
            "examples": [
                {
                    "name": "Simple Moving Average Strategy",
                    "description": "Basic trend-following strategy",
                    "code": """
class SimpleMAStrategy(BaseStrategy):
    def initialize(self):
        self.short_period = self.get_parameter('short_period', 10)
        self.long_period = self.get_parameter('long_period', 30)
        self.symbol = self.get_parameter('symbol', 'BTCUSD')
    
    def on_bar(self):
        short_ma = self.data.sma(self.symbol, self.short_period)
        long_ma = self.data.sma(self.symbol, self.long_period)
        
        if short_ma > long_ma:
            # Buy signal
            self.orders.market_order(self.symbol, 1.0, 'buy')
        elif short_ma < long_ma:
            # Sell signal  
            self.orders.market_order(self.symbol, 1.0, 'sell')
                    """
                }
            ]
        }
        
        return documentation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )