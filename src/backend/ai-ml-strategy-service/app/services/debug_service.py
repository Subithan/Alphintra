"""
Interactive debugging service for strategy development.
"""

import json
import pickle
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from uuid import UUID, uuid4
import logging
import copy

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.core.database import get_db
from app.models.strategy import DebugSession, DebugStatus
from app.models.dataset import Dataset
from app.services.execution_engine import ExecutionEngine
from app.sdk.strategy import BaseStrategy, StrategyContext
from app.sdk.data import MarketData
from app.sdk.portfolio import Portfolio
from app.sdk.orders import OrderManager
from app.sdk.risk import RiskManager


class DebugBreakpoint:
    """Represents a breakpoint in strategy code."""
    
    def __init__(self, line_number: int, condition: str = None, 
                 hit_count: int = 0, enabled: bool = True):
        self.line_number = line_number
        self.condition = condition  # Python expression that must be True to trigger
        self.hit_count = hit_count
        self.enabled = enabled
        self.hits = 0
    
    def should_trigger(self, context: StrategyContext) -> bool:
        """Check if breakpoint should trigger."""
        if not self.enabled:
            return False
        
        self.hits += 1
        
        # Check hit count condition
        if self.hit_count > 0 and self.hits < self.hit_count:
            return False
        
        # Check custom condition
        if self.condition:
            try:
                # Create safe evaluation context
                eval_context = {
                    'context': context,
                    'data': context.market_data,
                    'portfolio': context.portfolio,
                    'orders': context.order_manager,
                    'variables': context.variables,
                    'bar_count': context.bar_count,
                    'current_time': context.current_time
                }
                
                return bool(eval(self.condition, {"__builtins__": {}}, eval_context))
            except Exception:
                # If condition evaluation fails, don't trigger
                return False
        
        return True


class DebugFrame:
    """Represents the current state at a debug point."""
    
    def __init__(self, timestamp: datetime, bar_count: int, 
                 context: StrategyContext, line_number: int = None):
        self.timestamp = timestamp
        self.bar_count = bar_count
        self.line_number = line_number
        
        # Capture context state
        self.market_data_snapshot = self._capture_market_data(context.market_data)
        self.portfolio_snapshot = self._capture_portfolio(context.portfolio)
        self.variables_snapshot = copy.deepcopy(context.variables)
        self.metrics_snapshot = copy.deepcopy(context.metrics)
        
        # Current bar data
        self.current_bar = context.current_bar
        self.current_time = context.current_time
        
    def _capture_market_data(self, market_data: MarketData) -> Dict[str, Any]:
        """Capture current market data state."""
        snapshot = {
            "current_time": market_data.current_time,
            "current_bar_indices": market_data._current_bar_index.copy(),
            "available_symbols": list(market_data._data_cache.keys())
        }
        
        # Capture recent prices for each symbol
        for cache_key in market_data._data_cache.keys():
            symbol = cache_key.split(',')[0]
            current_bar = market_data.get_current_bar(symbol)
            if current_bar:
                snapshot[f"{symbol}_current_bar"] = current_bar.to_dict()
        
        return snapshot
    
    def _capture_portfolio(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Capture current portfolio state."""
        return {
            "total_value": float(portfolio.total_value),
            "cash_balance": float(portfolio.cash_balance),
            "positions_value": float(portfolio.positions_value),
            "positions": portfolio.get_positions_summary(),
            "performance_stats": portfolio.get_performance_stats(),
            "total_trades": portfolio.total_trades,
            "winning_trades": portfolio.winning_trades,
            "losing_trades": portfolio.losing_trades
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert frame to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "bar_count": self.bar_count,
            "line_number": self.line_number,
            "market_data": self.market_data_snapshot,
            "portfolio": self.portfolio_snapshot,
            "variables": self.variables_snapshot,
            "metrics": self.metrics_snapshot,
            "current_bar": self.current_bar,
            "current_time": self.current_time.isoformat() if self.current_time else None
        }


class InteractiveDebugger:
    """Interactive debugger for strategy development."""
    
    def __init__(self, session_id: str, strategy_code: str, dataset_id: str,
                 user_id: str, execution_engine: ExecutionEngine):
        self.session_id = session_id
        self.strategy_code = strategy_code
        self.dataset_id = dataset_id
        self.user_id = user_id
        self.execution_engine = execution_engine
        
        self.logger = logging.getLogger(__name__)
        
        # Debug state
        self.is_running = False
        self.is_paused = False
        self.current_frame: Optional[DebugFrame] = None
        self.breakpoints: Dict[int, DebugBreakpoint] = {}
        self.call_stack: List[DebugFrame] = []
        
        # Strategy execution components
        self.strategy_instance: Optional[BaseStrategy] = None
        self.context: Optional[StrategyContext] = None
        
        # Data replay
        self.data_iterator = None
        self.current_bar_index = 0
        self.total_bars = 0
        
        # Event callbacks
        self.on_breakpoint: Optional[Callable] = None
        self.on_step: Optional[Callable] = None
        self.on_variable_change: Optional[Callable] = None
    
    async def initialize(self, db: AsyncSession) -> Dict[str, Any]:
        """Initialize the debug session."""
        try:
            # Load dataset
            dataset_result = await db.execute(
                select(Dataset).where(Dataset.id == UUID(self.dataset_id))
            )
            dataset = dataset_result.scalar_one_or_none()
            
            if not dataset:
                raise ValueError(f"Dataset not found: {self.dataset_id}")
            
            # Compile strategy
            compilation_result = self.execution_engine.compile_strategy(
                self.strategy_code, f"debug_strategy_{self.session_id}"
            )
            
            if not compilation_result["success"]:
                raise Exception(f"Strategy compilation failed: {compilation_result['error']}")
            
            # Get strategy class
            strategy_classes = compilation_result["strategy_classes"]
            if not strategy_classes:
                raise Exception("No strategy class found")
            
            strategy_class = strategy_classes[0]["class"]
            self.strategy_instance = strategy_class()
            
            # Setup context
            market_data = MarketData()
            portfolio = Portfolio()
            order_manager = OrderManager(portfolio)
            risk_manager = RiskManager(portfolio)
            
            self.context = StrategyContext(
                market_data=market_data,
                portfolio=portfolio,
                order_manager=order_manager,
                risk_manager=risk_manager,
                strategy_id=f"debug_{self.session_id}",
                user_id=self.user_id
            )
            
            self.strategy_instance.set_context(self.context)
            
            # Load market data (simplified - would load from dataset)
            # For now, generate sample data
            symbols = ["BTCUSD"]  # Default symbol
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()
            
            for symbol in symbols:
                market_data.load_data(symbol, start_date, end_date, "1d")
            
            # Setup data iterator
            primary_symbol = symbols[0]
            cache_key = f"{primary_symbol},1d"
            if cache_key in market_data._data_cache:
                data_df = market_data._data_cache[cache_key]
                self.total_bars = len(data_df)
                self.data_iterator = data_df.iterrows()
            
            # Initialize strategy
            self.strategy_instance.initialize()
            
            self.logger.info(f"Debug session initialized: {self.session_id}")
            
            return {
                "success": True,
                "session_id": self.session_id,
                "total_bars": self.total_bars,
                "symbols": symbols,
                "strategy_info": self.strategy_instance.get_strategy_info()
            }
            
        except Exception as e:
            self.logger.error(f"Debug session initialization failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def set_breakpoint(self, line_number: int, condition: str = None, 
                      hit_count: int = 0) -> bool:
        """Set a breakpoint at the specified line."""
        try:
            breakpoint = DebugBreakpoint(line_number, condition, hit_count)
            self.breakpoints[line_number] = breakpoint
            
            self.logger.info(f"Breakpoint set at line {line_number}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set breakpoint: {str(e)}")
            return False
    
    def remove_breakpoint(self, line_number: int) -> bool:
        """Remove a breakpoint."""
        if line_number in self.breakpoints:
            del self.breakpoints[line_number]
            self.logger.info(f"Breakpoint removed from line {line_number}")
            return True
        return False
    
    def toggle_breakpoint(self, line_number: int) -> bool:
        """Toggle breakpoint enabled/disabled."""
        if line_number in self.breakpoints:
            self.breakpoints[line_number].enabled = not self.breakpoints[line_number].enabled
            return True
        return False
    
    def clear_all_breakpoints(self):
        """Clear all breakpoints."""
        self.breakpoints.clear()
        self.logger.info("All breakpoints cleared")
    
    def start_debugging(self) -> Dict[str, Any]:
        """Start or resume debugging."""
        if not self.strategy_instance or not self.context:
            return {"success": False, "error": "Debug session not initialized"}
        
        self.is_running = True
        self.is_paused = False
        
        return {"success": True, "status": "running"}
    
    def pause_debugging(self) -> Dict[str, Any]:
        """Pause debugging execution."""
        self.is_paused = True
        return {"success": True, "status": "paused"}
    
    def step_over(self) -> Dict[str, Any]:
        """Execute next line (step over)."""
        if not self.is_running:
            return {"success": False, "error": "Debug session not running"}
        
        try:
            # Execute next bar
            result = self._execute_next_bar()
            
            if result["success"]:
                # Create debug frame
                self.current_frame = DebugFrame(
                    timestamp=self.context.current_time,
                    bar_count=self.context.bar_count,
                    context=self.context
                )
                
                if self.on_step:
                    self.on_step(self.current_frame)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Step over failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def step_into(self) -> Dict[str, Any]:
        """Step into function calls (same as step over for now)."""
        return self.step_over()
    
    def continue_execution(self) -> Dict[str, Any]:
        """Continue execution until next breakpoint or end."""
        if not self.is_running:
            return {"success": False, "error": "Debug session not running"}
        
        self.is_paused = False
        
        try:
            while not self.is_paused and self.current_bar_index < self.total_bars:
                result = self._execute_next_bar()
                
                if not result["success"]:
                    break
                
                # Check for breakpoints
                if self._check_breakpoints():
                    self.is_paused = True
                    break
            
            status = "paused" if self.is_paused else "completed"
            return {"success": True, "status": status}
            
        except Exception as e:
            self.logger.error(f"Continue execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def stop_debugging(self) -> Dict[str, Any]:
        """Stop debugging session."""
        self.is_running = False
        self.is_paused = False
        
        # Finalize strategy
        if self.strategy_instance:
            try:
                self.strategy_instance.finalize()
            except Exception as e:
                self.logger.error(f"Strategy finalization failed: {str(e)}")
        
        return {"success": True, "status": "stopped"}
    
    def _execute_next_bar(self) -> Dict[str, Any]:
        """Execute the next bar of data."""
        if self.current_bar_index >= self.total_bars:
            return {"success": False, "error": "No more data to process"}
        
        try:
            # Get next bar data
            if self.data_iterator is None:
                return {"success": False, "error": "Data iterator not initialized"}
            
            # Advance to next bar
            timestamp, bar_data = next(self.data_iterator)
            
            # Update context
            self.context.current_time = timestamp
            self.context.current_bar = bar_data.to_dict()
            self.context.bar_count = self.current_bar_index
            
            # Update market data indices
            for cache_key in self.context.market_data._current_bar_index:
                self.context.market_data._current_bar_index[cache_key] = self.current_bar_index
            
            # Execute strategy logic
            self.strategy_instance.on_bar()
            
            self.current_bar_index += 1
            
            return {
                "success": True,
                "bar_index": self.current_bar_index,
                "timestamp": timestamp.isoformat(),
                "total_bars": self.total_bars
            }
            
        except StopIteration:
            return {"success": False, "error": "End of data reached"}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def _check_breakpoints(self) -> bool:
        """Check if any breakpoints should trigger."""
        for line_number, breakpoint in self.breakpoints.items():
            if breakpoint.should_trigger(self.context):
                self.current_frame = DebugFrame(
                    timestamp=self.context.current_time,
                    bar_count=self.context.bar_count,
                    context=self.context,
                    line_number=line_number
                )
                
                self.logger.info(f"Breakpoint hit at line {line_number}")
                
                if self.on_breakpoint:
                    self.on_breakpoint(self.current_frame, breakpoint)
                
                return True
        
        return False
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current debugging state."""
        if not self.context:
            return {"initialized": False}
        
        state = {
            "initialized": True,
            "running": self.is_running,
            "paused": self.is_paused,
            "current_bar_index": self.current_bar_index,
            "total_bars": self.total_bars,
            "progress": (self.current_bar_index / self.total_bars * 100) if self.total_bars > 0 else 0,
            "breakpoints": {
                line: {
                    "condition": bp.condition,
                    "hit_count": bp.hit_count,
                    "enabled": bp.enabled,
                    "hits": bp.hits
                } for line, bp in self.breakpoints.items()
            }
        }
        
        if self.current_frame:
            state["current_frame"] = self.current_frame.to_dict()
        
        return state
    
    def get_variables(self) -> Dict[str, Any]:
        """Get current strategy variables."""
        if not self.context:
            return {}
        
        return {
            "strategy_variables": self.context.variables,
            "context_data": {
                "current_time": self.context.current_time.isoformat() if self.context.current_time else None,
                "bar_count": self.context.bar_count,
                "current_bar": self.context.current_bar
            },
            "portfolio_state": self.context.portfolio.get_performance_stats(),
            "positions": self.context.portfolio.get_positions_summary(),
            "orders": [order.to_dict() for order in self.context.order_manager.get_orders()],
            "metrics": self.context.metrics
        }
    
    def evaluate_expression(self, expression: str) -> Dict[str, Any]:
        """Evaluate a Python expression in the current context."""
        if not self.context:
            return {"success": False, "error": "No active context"}
        
        try:
            # Create safe evaluation context
            eval_context = {
                'context': self.context,
                'data': self.context.market_data,
                'portfolio': self.context.portfolio,
                'orders': self.context.order_manager,
                'risk': self.context.risk_manager,
                'variables': self.context.variables,
                'metrics': self.context.metrics,
                'bar_count': self.context.bar_count,
                'current_time': self.context.current_time
            }
            
            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, eval_context)
            
            return {
                "success": True,
                "result": str(result),
                "type": type(result).__name__
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def modify_variable(self, name: str, value: Any) -> Dict[str, Any]:
        """Modify a strategy variable."""
        if not self.context:
            return {"success": False, "error": "No active context"}
        
        try:
            # Store old value for callback
            old_value = self.context.variables.get(name)
            
            # Set new value
            self.context.variables[name] = value
            
            # Trigger callback
            if self.on_variable_change:
                self.on_variable_change(name, old_value, value)
            
            return {
                "success": True,
                "old_value": str(old_value),
                "new_value": str(value)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class DebugService:
    """Service for managing debug sessions."""
    
    def __init__(self, execution_engine: ExecutionEngine):
        self.execution_engine = execution_engine
        self.logger = logging.getLogger(__name__)
        
        # Active debug sessions
        self.active_sessions: Dict[str, InteractiveDebugger] = {}
    
    async def create_debug_session(self, strategy_id: str, dataset_id: str, 
                                  user_id: str, start_date: str, end_date: str,
                                  db: AsyncSession) -> Dict[str, Any]:
        """Create a new debug session."""
        try:
            # Load strategy
            from app.models.strategy import Strategy
            strategy_result = await db.execute(
                select(Strategy).where(Strategy.id == UUID(strategy_id))
            )
            strategy = strategy_result.scalar_one_or_none()
            
            if not strategy:
                return {"success": False, "error": "Strategy not found"}
            
            # Create session ID
            session_id = str(uuid4())
            
            # Create debug session record
            debug_session = DebugSession(
                id=UUID(session_id),
                strategy_id=UUID(strategy_id),
                dataset_id=UUID(dataset_id),
                user_id=UUID(user_id),
                start_date=start_date,
                end_date=end_date,
                status=DebugStatus.ACTIVE
            )
            
            db.add(debug_session)
            await db.commit()
            
            # Create interactive debugger
            debugger = InteractiveDebugger(
                session_id=session_id,
                strategy_code=strategy.code,
                dataset_id=dataset_id,
                user_id=user_id,
                execution_engine=self.execution_engine
            )
            
            # Initialize debugger
            init_result = await debugger.initialize(db)
            
            if init_result["success"]:
                self.active_sessions[session_id] = debugger
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "debugger_info": init_result
                }
            else:
                # Clean up failed session
                await db.execute(
                    delete(DebugSession).where(DebugSession.id == UUID(session_id))
                )
                await db.commit()
                
                return init_result
                
        except Exception as e:
            self.logger.error(f"Failed to create debug session: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def get_debug_session(self, session_id: str) -> Optional[InteractiveDebugger]:
        """Get active debug session."""
        return self.active_sessions.get(session_id)
    
    async def close_debug_session(self, session_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Close and clean up debug session."""
        try:
            # Stop debugger if active
            if session_id in self.active_sessions:
                debugger = self.active_sessions[session_id]
                debugger.stop_debugging()
                del self.active_sessions[session_id]
            
            # Update database record
            await db.execute(
                update(DebugSession)
                .where(DebugSession.id == UUID(session_id))
                .values(status=DebugStatus.COMPLETED)
            )
            await db.commit()
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to close debug session: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def list_debug_sessions(self, user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
        """List debug sessions for a user."""
        try:
            result = await db.execute(
                select(DebugSession)
                .where(DebugSession.user_id == UUID(user_id))
                .order_by(DebugSession.created_at.desc())
                .limit(50)
            )
            
            sessions = result.scalars().all()
            
            return [
                {
                    "session_id": str(session.id),
                    "strategy_id": str(session.strategy_id),
                    "dataset_id": str(session.dataset_id),
                    "status": session.status.value,
                    "start_date": session.start_date,
                    "end_date": session.end_date,
                    "created_at": session.created_at.isoformat(),
                    "is_active": str(session.id) in self.active_sessions
                }
                for session in sessions
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to list debug sessions: {str(e)}")
            return []
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """Clean up inactive debug sessions."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for session_id, debugger in self.active_sessions.items():
            # Check if session has been inactive
            if not debugger.is_running:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            debugger = self.active_sessions[session_id]
            debugger.stop_debugging()
            del self.active_sessions[session_id]
            self.logger.info(f"Cleaned up inactive debug session: {session_id}")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active debug sessions."""
        return len(self.active_sessions)