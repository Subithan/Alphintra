"""
Live strategy execution engine for real-time trading.
"""

import asyncio
import logging
import uuid
import json
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.execution import (
    StrategyExecution,
    ExecutionSignal,
    ExecutionOrder,
    ExecutionPosition,
    ExecutionPositionUpdate,
    ExecutionMetrics,
    ExecutionEnvironment,
    ExecutionMode,
    ExecutionStatus,
    SignalType
)
from app.models.strategy import Strategy
from app.services.market_data_service import market_data_service
from app.services.risk_manager import risk_manager
from app.database.connection import get_db_session


@dataclass
class SignalData:
    """Trading signal data structure."""
    strategy_execution_id: int
    signal_type: str
    symbol: str
    timeframe: str
    action: str
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    confidence: Optional[float] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    indicators: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    model_output: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class OrderData:
    """Order execution data structure."""
    strategy_execution_id: int
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    signal_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Execution result data structure."""
    success: bool
    order_id: Optional[str] = None
    execution_price: Optional[Decimal] = None
    executed_quantity: Optional[Decimal] = None
    error_message: Optional[str] = None
    latency_ms: Optional[int] = None


class LiveExecutionEngine:
    """Live strategy execution engine for real-time trading."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Execution state
        self.active_executions: Dict[int, Dict] = {}
        self.signal_queue: asyncio.Queue = asyncio.Queue()
        self.order_queue: asyncio.Queue = asyncio.Queue()
        
        # Engine status
        self.engine_running = False
        self.signal_processor_running = False
        self.order_processor_running = False
        
        # Performance tracking
        self.execution_stats = defaultdict(lambda: {
            "signals_processed": 0,
            "orders_submitted": 0,
            "orders_filled": 0,
            "avg_latency_ms": 0,
            "last_activity": datetime.utcnow()
        })
        
        # Event callbacks
        self.signal_callbacks: List[Callable] = []
        self.order_callbacks: List[Callable] = []
        self.execution_callbacks: List[Callable] = []
        
        # Configuration
        self.max_signal_queue_size = 1000
        self.max_order_queue_size = 500
        self.signal_processing_interval = 0.1  # 100ms
        self.order_processing_interval = 0.05  # 50ms
        
    async def initialize(self) -> None:
        """Initialize the execution engine."""
        
        # Load active strategy executions
        await self._load_active_executions()
        
        # Start processing loops
        if not self.engine_running:
            self.engine_running = True
            self.signal_processor_running = True
            self.order_processor_running = True
            
            asyncio.create_task(self._signal_processing_loop())
            asyncio.create_task(self._order_processing_loop())
            asyncio.create_task(self._position_monitoring_loop())
            asyncio.create_task(self._metrics_collection_loop())
        
        self.logger.info("Live execution engine initialized")
    
    async def _load_active_executions(self) -> None:
        """Load active strategy executions from database."""
        
        try:
            with get_db_session() as db:
                active_executions = db.query(StrategyExecution).filter(
                    StrategyExecution.status.in_([
                        ExecutionStatus.RUNNING.value,
                        ExecutionStatus.PAUSED.value
                    ])
                ).all()
                
                for execution in active_executions:
                    await self._initialize_execution_state(execution)
                
            self.logger.info(f"Loaded {len(active_executions)} active executions")
            
        except Exception as e:
            self.logger.error(f"Error loading active executions: {e}")
    
    async def _initialize_execution_state(self, execution: StrategyExecution) -> None:
        """Initialize execution state for a strategy."""
        
        try:
            # Load current positions
            with get_db_session() as db:
                positions = db.query(ExecutionPosition).filter(
                    and_(
                        ExecutionPosition.strategy_execution_id == execution.id,
                        ExecutionPosition.is_open == True
                    )
                ).all()
                
                pending_orders = db.query(ExecutionOrder).filter(
                    and_(
                        ExecutionOrder.strategy_execution_id == execution.id,
                        ExecutionOrder.status.in_(["pending", "partially_filled"])
                    )
                ).all()
            
            # Initialize execution state
            self.active_executions[execution.id] = {
                "execution": execution,
                "positions": {pos.symbol: pos for pos in positions},
                "pending_orders": {order.id: order for order in pending_orders},
                "last_signal_time": execution.last_signal_time or datetime.utcnow(),
                "last_execution_time": execution.last_execution_time or datetime.utcnow(),
                "signal_count": 0,
                "order_count": 0,
                "error_count": 0
            }
            
            self.logger.info(f"Initialized execution state for strategy {execution.id}")
            
        except Exception as e:
            self.logger.error(f"Error initializing execution state for {execution.id}: {e}")
    
    async def start_execution(self, execution_id: int) -> bool:
        """Start a strategy execution."""
        
        try:
            with get_db_session() as db:
                execution = db.query(StrategyExecution).filter(
                    StrategyExecution.id == execution_id
                ).first()
                
                if not execution:
                    raise ValueError(f"Execution {execution_id} not found")
                
                if execution.status == ExecutionStatus.RUNNING.value:
                    return True  # Already running
                
                # Validate execution environment
                if not execution.environment.is_active:
                    raise ValueError("Execution environment is not active")
                
                # Perform pre-start checks
                await self._perform_pre_start_checks(execution)
                
                # Update status
                execution.status = ExecutionStatus.RUNNING.value
                execution.start_time = datetime.utcnow()
                db.commit()
                
                # Initialize execution state
                await self._initialize_execution_state(execution)
                
            self.logger.info(f"Started execution {execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting execution {execution_id}: {e}")
            # Update status to error
            with get_db_session() as db:
                execution = db.query(StrategyExecution).filter(
                    StrategyExecution.id == execution_id
                ).first()
                if execution:
                    execution.status = ExecutionStatus.ERROR.value
                    execution.last_error = str(e)
                    execution.last_error_time = datetime.utcnow()
                    db.commit()
            return False
    
    async def stop_execution(self, execution_id: int) -> bool:
        """Stop a strategy execution."""
        
        try:
            with get_db_session() as db:
                execution = db.query(StrategyExecution).filter(
                    StrategyExecution.id == execution_id
                ).first()
                
                if not execution:
                    raise ValueError(f"Execution {execution_id} not found")
                
                # Cancel pending orders
                await self._cancel_pending_orders(execution_id)
                
                # Update status
                execution.status = ExecutionStatus.STOPPED.value
                execution.stop_time = datetime.utcnow()
                db.commit()
                
                # Remove from active executions
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]
                
            self.logger.info(f"Stopped execution {execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping execution {execution_id}: {e}")
            return False
    
    async def pause_execution(self, execution_id: int) -> bool:
        """Pause a strategy execution."""
        
        try:
            with get_db_session() as db:
                execution = db.query(StrategyExecution).filter(
                    StrategyExecution.id == execution_id
                ).first()
                
                if not execution:
                    raise ValueError(f"Execution {execution_id} not found")
                
                execution.status = ExecutionStatus.PAUSED.value
                db.commit()
                
            self.logger.info(f"Paused execution {execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing execution {execution_id}: {e}")
            return False
    
    async def resume_execution(self, execution_id: int) -> bool:
        """Resume a paused strategy execution."""
        
        try:
            with get_db_session() as db:
                execution = db.query(StrategyExecution).filter(
                    StrategyExecution.id == execution_id
                ).first()
                
                if not execution:
                    raise ValueError(f"Execution {execution_id} not found")
                
                if execution.status != ExecutionStatus.PAUSED.value:
                    raise ValueError("Execution is not paused")
                
                execution.status = ExecutionStatus.RUNNING.value
                db.commit()
                
            self.logger.info(f"Resumed execution {execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming execution {execution_id}: {e}")
            return False
    
    async def submit_signal(self, signal_data: SignalData) -> bool:
        """Submit a trading signal for processing."""
        
        try:
            # Validate signal
            if signal_data.strategy_execution_id not in self.active_executions:
                raise ValueError("Strategy execution not active")
            
            execution_state = self.active_executions[signal_data.strategy_execution_id]
            execution = execution_state["execution"]
            
            if execution.status != ExecutionStatus.RUNNING.value:
                self.logger.warning(f"Ignoring signal for non-running execution {execution.id}")
                return False
            
            # Check queue size
            if self.signal_queue.qsize() >= self.max_signal_queue_size:
                self.logger.warning("Signal queue full, dropping signal")
                return False
            
            # Add to queue
            await self.signal_queue.put(signal_data)
            
            # Update stats
            execution_state["signal_count"] += 1
            execution_state["last_signal_time"] = datetime.utcnow()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error submitting signal: {e}")
            return False
    
    async def _signal_processing_loop(self) -> None:
        """Main signal processing loop."""
        
        while self.signal_processor_running:
            try:
                # Get signal from queue with timeout
                try:
                    signal_data = await asyncio.wait_for(
                        self.signal_queue.get(), 
                        timeout=self.signal_processing_interval
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process signal
                await self._process_signal(signal_data)
                
            except Exception as e:
                self.logger.error(f"Error in signal processing loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_signal(self, signal_data: SignalData) -> None:
        """Process a trading signal."""
        
        start_time = datetime.utcnow()
        
        try:
            # Create signal record
            signal_id = f"SIG_{signal_data.strategy_execution_id}_{uuid.uuid4().hex[:8]}"
            
            signal = ExecutionSignal(
                strategy_execution_id=signal_data.strategy_execution_id,
                signal_id=signal_id,
                signal_type=signal_data.signal_type,
                symbol=signal_data.symbol,
                timeframe=signal_data.timeframe,
                timestamp=start_time,
                action=signal_data.action,
                quantity=signal_data.quantity,
                price=signal_data.price,
                confidence=signal_data.confidence,
                stop_loss=signal_data.stop_loss,
                take_profit=signal_data.take_profit,
                indicators=signal_data.indicators or {},
                features=signal_data.features or {},
                model_output=signal_data.model_output or {},
                metadata=signal_data.metadata or {}
            )
            
            # Save signal to database
            with get_db_session() as db:
                db.add(signal)
                db.commit()
                db.refresh(signal)
            
            # Process signal based on type and action
            if signal_data.action in ["buy", "sell"]:
                await self._process_trade_signal(signal, signal_data)
            elif signal_data.action == "hold":
                # No action needed for hold signals
                pass
            
            # Mark signal as processed
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            with get_db_session() as db:
                signal.is_processed = True
                signal.processed_at = datetime.utcnow()
                signal.processing_latency_ms = int(processing_time)
                db.commit()
            
            # Update execution stats
            execution_state = self.active_executions[signal_data.strategy_execution_id]
            self.execution_stats[signal_data.strategy_execution_id]["signals_processed"] += 1
            
            # Notify callbacks
            for callback in self.signal_callbacks:
                try:
                    await callback(signal, signal_data)
                except Exception as e:
                    self.logger.error(f"Error in signal callback: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")
            
            # Update signal with error
            with get_db_session() as db:
                signal.execution_status = "error"
                signal.execution_error = str(e)
                db.commit()
    
    async def _process_trade_signal(self, signal: ExecutionSignal, signal_data: SignalData) -> None:
        """Process a trade signal (buy/sell)."""
        
        try:
            execution_state = self.active_executions[signal_data.strategy_execution_id]
            execution = execution_state["execution"]
            
            # Determine order details
            side = "buy" if signal_data.action == "buy" else "sell"
            
            # Calculate position size if not provided
            if not signal_data.quantity:
                signal_data.quantity = await self._calculate_position_size(
                    execution, signal_data.symbol, side
                )
            
            # Get current market price if not provided
            if not signal_data.price:
                signal_data.price = await market_data_service.get_current_price(signal_data.symbol)
            
            if not signal_data.price:
                raise ValueError("Unable to get current market price")
            
            # Validate order with risk manager
            is_valid, validation_errors = await risk_manager.validate_order_risk(
                session_id=execution.id,  # Using execution ID as session ID
                symbol=signal_data.symbol,
                side=side,
                quantity=signal_data.quantity,
                price=signal_data.price
            )
            
            if not is_valid:
                raise ValueError(f"Risk validation failed: {', '.join(validation_errors)}")
            
            # Create order
            order_data = OrderData(
                strategy_execution_id=signal_data.strategy_execution_id,
                symbol=signal_data.symbol,
                side=side,
                order_type="market",  # Default to market orders for now
                quantity=signal_data.quantity,
                price=signal_data.price,
                signal_id=signal.id,
                metadata={"signal_id": signal.signal_id}
            )
            
            # Submit order to order queue
            await self.order_queue.put(order_data)
            
        except Exception as e:
            self.logger.error(f"Error processing trade signal: {e}")
            raise
    
    async def _calculate_position_size(
        self, 
        execution: StrategyExecution, 
        symbol: str, 
        side: str
    ) -> Decimal:
        """Calculate position size based on execution configuration."""
        
        try:
            # Get current portfolio value
            portfolio_value = execution.current_capital or execution.allocated_capital
            
            # Apply position sizing method
            if execution.position_sizing_method == "fixed_percentage":
                percentage = execution.position_size_config.get("percentage", 0.05)  # 5% default
                position_value = portfolio_value * Decimal(str(percentage))
            elif execution.position_sizing_method == "fixed_amount":
                position_value = Decimal(str(execution.position_size_config.get("amount", 1000)))
            elif execution.position_sizing_method == "volatility_adjusted":
                # Implement volatility-based position sizing
                base_percentage = execution.position_size_config.get("base_percentage", 0.05)
                position_value = portfolio_value * Decimal(str(base_percentage))
            else:
                # Default to 5% of portfolio
                position_value = portfolio_value * Decimal("0.05")
            
            # Get current price
            current_price = await market_data_service.get_current_price(symbol)
            if not current_price:
                raise ValueError("Unable to get current price for position sizing")
            
            # Calculate quantity
            quantity = position_value / current_price
            
            # Apply maximum position size limit
            if execution.max_position_size:
                max_quantity = execution.max_position_size / current_price
                quantity = min(quantity, max_quantity)
            
            return quantity.quantize(Decimal("0.00000001"))  # 8 decimal places
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return Decimal("0")
    
    async def _order_processing_loop(self) -> None:
        """Main order processing loop."""
        
        while self.order_processor_running:
            try:
                # Get order from queue with timeout
                try:
                    order_data = await asyncio.wait_for(
                        self.order_queue.get(), 
                        timeout=self.order_processing_interval
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process order
                await self._process_order(order_data)
                
            except Exception as e:
                self.logger.error(f"Error in order processing loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_order(self, order_data: OrderData) -> None:
        """Process an order."""
        
        start_time = datetime.utcnow()
        
        try:
            # Create order record
            order_id = f"ORD_{order_data.strategy_execution_id}_{uuid.uuid4().hex[:8]}"
            
            order = ExecutionOrder(
                strategy_execution_id=order_data.strategy_execution_id,
                signal_id=order_data.signal_id,
                order_id=order_id,
                symbol=order_data.symbol,
                side=order_data.side,
                order_type=order_data.order_type,
                quantity=order_data.quantity,
                price=order_data.price,
                stop_price=order_data.stop_price,
                remaining_quantity=order_data.quantity,
                status="pending",
                submitted_at=start_time,
                metadata=order_data.metadata or {}
            )
            
            # Save order to database
            with get_db_session() as db:
                db.add(order)
                db.commit()
                db.refresh(order)
            
            # Execute order (simulate for now)
            execution_result = await self._execute_order(order)
            
            # Update order with execution result
            await self._update_order_execution(order, execution_result)
            
            # Update position if order was filled
            if execution_result.success:
                await self._update_position_from_order(order, execution_result)
            
            # Update execution stats
            execution_state = self.active_executions[order_data.strategy_execution_id]
            self.execution_stats[order_data.strategy_execution_id]["orders_submitted"] += 1
            if execution_result.success:
                self.execution_stats[order_data.strategy_execution_id]["orders_filled"] += 1
            
            # Notify callbacks
            for callback in self.order_callbacks:
                try:
                    await callback(order, execution_result)
                except Exception as e:
                    self.logger.error(f"Error in order callback: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error processing order: {e}")
    
    async def _execute_order(self, order: ExecutionOrder) -> ExecutionResult:
        """Execute an order (simulate execution for now)."""
        
        start_time = datetime.utcnow()
        
        try:
            # Get execution environment
            with get_db_session() as db:
                execution = db.query(StrategyExecution).filter(
                    StrategyExecution.id == order.strategy_execution_id
                ).first()
                
                if not execution:
                    raise ValueError("Strategy execution not found")
                
                environment = execution.environment
            
            # Simulate execution based on environment mode
            if environment.execution_mode == ExecutionMode.PAPER.value:
                # Paper trading execution
                result = await self._execute_paper_order(order, environment)
            elif environment.execution_mode == ExecutionMode.LIVE.value:
                # Live trading execution (implement broker integration)
                result = await self._execute_live_order(order, environment)
            else:
                # Simulation mode
                result = await self._execute_simulation_order(order, environment)
            
            # Calculate execution latency
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            result.latency_ms = latency_ms
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing order {order.order_id}: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
                latency_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )
    
    async def _execute_paper_order(self, order: ExecutionOrder, environment: ExecutionEnvironment) -> ExecutionResult:
        """Execute order in paper trading mode."""
        
        try:
            # Get current market data
            quote = await market_data_service.get_current_quote(order.symbol)
            if not quote:
                raise ValueError("Market data not available")
            
            # Determine execution price
            if order.side == "buy":
                execution_price = quote.ask
            else:
                execution_price = quote.bid
            
            # Apply slippage
            slippage_factor = environment.default_slippage_rate
            if order.side == "buy":
                execution_price *= (1 + slippage_factor)
            else:
                execution_price *= (1 - slippage_factor)
            
            # For market orders, execute immediately
            if order.order_type == "market":
                return ExecutionResult(
                    success=True,
                    order_id=order.order_id,
                    execution_price=execution_price,
                    executed_quantity=order.quantity
                )
            else:
                # For limit orders, simulate based on current market
                # For now, execute immediately for simplicity
                return ExecutionResult(
                    success=True,
                    order_id=order.order_id,
                    execution_price=execution_price,
                    executed_quantity=order.quantity
                )
                
        except Exception as e:
            raise ValueError(f"Paper execution failed: {e}")
    
    async def _execute_live_order(self, order: ExecutionOrder, environment: ExecutionEnvironment) -> ExecutionResult:
        """Execute order in live trading mode."""
        
        # TODO: Implement broker integration
        # For now, return error
        return ExecutionResult(
            success=False,
            error_message="Live trading not yet implemented"
        )
    
    async def _execute_simulation_order(self, order: ExecutionOrder, environment: ExecutionEnvironment) -> ExecutionResult:
        """Execute order in simulation mode."""
        
        # Similar to paper trading but with perfect fills
        try:
            current_price = await market_data_service.get_current_price(order.symbol)
            if not current_price:
                raise ValueError("Market data not available")
            
            return ExecutionResult(
                success=True,
                order_id=order.order_id,
                execution_price=current_price,
                executed_quantity=order.quantity
            )
            
        except Exception as e:
            raise ValueError(f"Simulation execution failed: {e}")
    
    async def _update_order_execution(self, order: ExecutionOrder, result: ExecutionResult) -> None:
        """Update order with execution result."""
        
        try:
            with get_db_session() as db:
                if result.success:
                    order.status = "filled"
                    order.filled_quantity = result.executed_quantity
                    order.remaining_quantity = order.quantity - result.executed_quantity
                    order.avg_fill_price = result.execution_price
                    order.filled_at = datetime.utcnow()
                    
                    # Calculate commission
                    execution = db.query(StrategyExecution).filter(
                        StrategyExecution.id == order.strategy_execution_id
                    ).first()
                    
                    if execution:
                        gross_amount = result.executed_quantity * result.execution_price
                        order.commission = gross_amount * execution.environment.default_commission_rate
                        order.total_cost = gross_amount + order.commission
                else:
                    order.status = "rejected"
                    order.error_message = result.error_message
                
                if result.latency_ms:
                    order.fill_latency_ms = result.latency_ms
                
                db.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating order execution: {e}")
    
    async def _update_position_from_order(self, order: ExecutionOrder, result: ExecutionResult) -> None:
        """Update position based on order execution."""
        
        try:
            execution_state = self.active_executions[order.strategy_execution_id]
            
            with get_db_session() as db:
                # Get or create position
                position = db.query(ExecutionPosition).filter(
                    and_(
                        ExecutionPosition.strategy_execution_id == order.strategy_execution_id,
                        ExecutionPosition.symbol == order.symbol,
                        ExecutionPosition.is_open == True
                    )
                ).first()
                
                if not position:
                    # Create new position
                    position = ExecutionPosition(
                        strategy_execution_id=order.strategy_execution_id,
                        symbol=order.symbol,
                        side="long" if order.side == "buy" else "short",
                        quantity=result.executed_quantity,
                        avg_entry_price=result.execution_price,
                        total_cost=result.executed_quantity * result.execution_price,
                        current_price=result.execution_price,
                        market_value=result.executed_quantity * result.execution_price,
                        opened_at=datetime.utcnow(),
                        last_updated=datetime.utcnow(),
                        entry_signal_id=order.signal.signal_id if order.signal else None
                    )
                    db.add(position)
                else:
                    # Update existing position
                    await self._update_existing_position(position, order, result)
                
                db.commit()
                db.refresh(position)
                
                # Update execution state
                execution_state["positions"][order.symbol] = position
                
        except Exception as e:
            self.logger.error(f"Error updating position from order: {e}")
    
    async def _update_existing_position(
        self, 
        position: ExecutionPosition, 
        order: ExecutionOrder, 
        result: ExecutionResult
    ) -> None:
        """Update an existing position with new order."""
        
        # Implementation depends on whether this is adding to or reducing position
        # For now, simple implementation
        
        if order.side == "buy" and position.side == "long":
            # Adding to long position
            old_cost = position.total_cost
            new_cost = result.executed_quantity * result.execution_price
            
            position.quantity += result.executed_quantity
            position.total_cost += new_cost
            position.avg_entry_price = position.total_cost / position.quantity
            
        elif order.side == "sell" and position.side == "long":
            # Reducing long position
            position.quantity -= result.executed_quantity
            
            if position.quantity <= 0:
                # Position closed
                position.is_open = False
                position.closed_at = datetime.utcnow()
                position.realized_pnl = (result.execution_price - position.avg_entry_price) * result.executed_quantity
                position.realized_pnl_pct = (position.realized_pnl / position.total_cost) * 100
        
        # Update market value and unrealized P&L
        position.current_price = result.execution_price
        position.market_value = position.quantity * result.execution_price
        
        if position.is_open:
            position.unrealized_pnl = position.market_value - position.total_cost
            if position.total_cost > 0:
                position.unrealized_pnl_pct = (position.unrealized_pnl / position.total_cost) * 100
        
        position.last_updated = datetime.utcnow()
    
    async def _position_monitoring_loop(self) -> None:
        """Monitor positions for risk management."""
        
        while self.engine_running:
            try:
                for execution_id in list(self.active_executions.keys()):
                    await self._monitor_execution_positions(execution_id)
                
                await asyncio.sleep(30.0)  # Monitor every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in position monitoring loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _monitor_execution_positions(self, execution_id: int) -> None:
        """Monitor positions for a specific execution."""
        
        try:
            execution_state = self.active_executions.get(execution_id)
            if not execution_state:
                return
            
            for symbol, position in execution_state["positions"].items():
                if not position.is_open:
                    continue
                
                # Update current price and P&L
                current_price = await market_data_service.get_current_price(symbol)
                if current_price:
                    position.current_price = current_price
                    position.market_value = position.quantity * current_price
                    position.unrealized_pnl = position.market_value - position.total_cost
                    if position.total_cost > 0:
                        position.unrealized_pnl_pct = (position.unrealized_pnl / position.total_cost) * 100
                    
                    # Check stop loss and take profit
                    await self._check_position_exits(position)
            
        except Exception as e:
            self.logger.error(f"Error monitoring positions for execution {execution_id}: {e}")
    
    async def _check_position_exits(self, position: ExecutionPosition) -> None:
        """Check if position should be exited based on stop loss or take profit."""
        
        try:
            exit_signal = None
            
            # Check stop loss
            if position.stop_loss_price:
                if position.side == "long" and position.current_price <= position.stop_loss_price:
                    exit_signal = "stop_loss"
                elif position.side == "short" and position.current_price >= position.stop_loss_price:
                    exit_signal = "stop_loss"
            
            # Check take profit
            if position.take_profit_price:
                if position.side == "long" and position.current_price >= position.take_profit_price:
                    exit_signal = "take_profit"
                elif position.side == "short" and position.current_price <= position.take_profit_price:
                    exit_signal = "take_profit"
            
            # Generate exit signal if needed
            if exit_signal:
                await self._generate_exit_signal(position, exit_signal)
                
        except Exception as e:
            self.logger.error(f"Error checking position exits: {e}")
    
    async def _generate_exit_signal(self, position: ExecutionPosition, reason: str) -> None:
        """Generate an exit signal for a position."""
        
        try:
            signal_data = SignalData(
                strategy_execution_id=position.strategy_execution_id,
                signal_type=SignalType.EXIT_LONG.value if position.side == "long" else SignalType.EXIT_SHORT.value,
                symbol=position.symbol,
                timeframe="1m",  # Default timeframe
                action="sell" if position.side == "long" else "buy",
                quantity=position.quantity,
                price=position.current_price,
                confidence=1.0,  # High confidence for risk management exits
                metadata={"reason": reason, "position_id": position.id}
            )
            
            await self.submit_signal(signal_data)
            
        except Exception as e:
            self.logger.error(f"Error generating exit signal: {e}")
    
    async def _metrics_collection_loop(self) -> None:
        """Collect execution metrics periodically."""
        
        while self.engine_running:
            try:
                for execution_id in list(self.active_executions.keys()):
                    await self._collect_execution_metrics(execution_id)
                
                await asyncio.sleep(300.0)  # Collect every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(600.0)
    
    async def _collect_execution_metrics(self, execution_id: int) -> None:
        """Collect metrics for a specific execution."""
        
        try:
            # Implementation would collect and store execution metrics
            # For now, just log
            stats = self.execution_stats[execution_id]
            self.logger.info(f"Execution {execution_id} stats: {stats}")
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics for execution {execution_id}: {e}")
    
    async def _perform_pre_start_checks(self, execution: StrategyExecution) -> None:
        """Perform pre-start validation checks."""
        
        # Check if strategy exists and is valid
        if not execution.strategy:
            raise ValueError("Strategy not found")
        
        # Check if symbols are valid
        if not execution.symbols:
            raise ValueError("No symbols configured")
        
        # Check capital allocation
        if execution.allocated_capital <= 0:
            raise ValueError("Invalid capital allocation")
        
        # Check environment connectivity (for live trading)
        if execution.environment.execution_mode == ExecutionMode.LIVE.value:
            # TODO: Check broker connectivity
            pass
    
    async def _cancel_pending_orders(self, execution_id: int) -> None:
        """Cancel all pending orders for an execution."""
        
        try:
            with get_db_session() as db:
                pending_orders = db.query(ExecutionOrder).filter(
                    and_(
                        ExecutionOrder.strategy_execution_id == execution_id,
                        ExecutionOrder.status.in_(["pending", "partially_filled"])
                    )
                ).all()
                
                for order in pending_orders:
                    order.status = "cancelled"
                    order.cancelled_at = datetime.utcnow()
                
                db.commit()
                
        except Exception as e:
            self.logger.error(f"Error cancelling pending orders: {e}")
    
    async def get_execution_status(self, execution_id: int) -> Optional[Dict[str, Any]]:
        """Get execution status and metrics."""
        
        if execution_id not in self.active_executions:
            return None
        
        execution_state = self.active_executions[execution_id]
        execution = execution_state["execution"]
        stats = self.execution_stats[execution_id]
        
        return {
            "execution_id": execution_id,
            "status": execution.status,
            "strategy_id": execution.strategy_id,
            "allocated_capital": float(execution.allocated_capital),
            "current_capital": float(execution.current_capital or execution.allocated_capital),
            "symbols": execution.symbols,
            "start_time": execution.start_time.isoformat() if execution.start_time else None,
            "last_signal_time": execution_state["last_signal_time"].isoformat(),
            "active_positions": len(execution_state["positions"]),
            "pending_orders": len(execution_state["pending_orders"]),
            "signals_processed": stats["signals_processed"],
            "orders_submitted": stats["orders_submitted"],
            "orders_filled": stats["orders_filled"],
            "error_count": execution_state["error_count"],
            "last_error": execution.last_error
        }
    
    async def cleanup(self) -> None:
        """Cleanup execution engine."""
        
        self.engine_running = False
        self.signal_processor_running = False
        self.order_processor_running = False
        
        self.logger.info("Live execution engine cleaned up")


# Global live execution engine instance
live_execution_engine = LiveExecutionEngine()