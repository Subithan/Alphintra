"""
Order management system for paper trading.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.paper_trading import (
    PaperOrder,
    PaperTransaction,
    OrderStatus,
    OrderType,
    OrderSide
)
from app.services.market_data_service import market_data_service, Quote
from app.services.paper_trading_engine import paper_trading_engine
from app.database.connection import get_db_session


class OrderValidationError(Exception):
    """Order validation error."""
    pass


class OrderExecutionError(Exception):
    """Order execution error."""
    pass


@dataclass
class OrderExecutionResult:
    """Order execution result."""
    order_id: int
    executed: bool
    execution_price: Optional[Decimal] = None
    executed_quantity: Optional[Decimal] = None
    remaining_quantity: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    error_message: Optional[str] = None


class OrderManager:
    """Advanced order management system for paper trading."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pending_orders: Dict[int, PaperOrder] = {}
        self.order_book: Dict[str, Dict] = {}  # Symbol -> {bids: [], asks: []}
        self.execution_engine_running = False
        
        # Execution parameters
        self.max_slippage_pct = Decimal("0.005")  # 0.5% max slippage
        self.partial_fill_threshold = Decimal("0.1")  # Minimum 10% fill
        self.order_timeout_minutes = 1440  # 24 hours default timeout
        
    async def initialize(self) -> None:
        """Initialize the order management system."""
        
        # Load pending orders from database
        await self._load_pending_orders()
        
        # Start execution engine
        if not self.execution_engine_running:
            self.execution_engine_running = True
            asyncio.create_task(self._execution_engine())
        
        self.logger.info("Order management system initialized")
    
    async def _load_pending_orders(self) -> None:
        """Load pending orders from database."""
        
        try:
            with get_db_session() as db:
                pending_orders = db.query(PaperOrder).filter(
                    PaperOrder.status.in_([OrderStatus.PENDING.value, OrderStatus.PARTIALLY_FILLED.value])
                ).all()
                
                for order in pending_orders:
                    self.pending_orders[order.id] = order
                
            self.logger.info(f"Loaded {len(self.pending_orders)} pending orders")
            
        except Exception as e:
            self.logger.error(f"Error loading pending orders: {e}")
    
    async def submit_order(
        self,
        session_id: int,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "DAY",
        client_order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaperOrder:
        """Submit a new order."""
        
        # Validate order parameters
        await self._validate_order_params(
            session_id, symbol, side, order_type, quantity, price, stop_price
        )
        
        # Generate order ID
        order_id = f"ORD_{session_id}_{uuid.uuid4().hex[:8]}"
        
        # Create order record
        order = PaperOrder(
            session_id=session_id,
            order_id=order_id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            remaining_quantity=quantity,
            price=price,
            stop_price=stop_price,
            status=OrderStatus.PENDING.value,
            time_in_force=time_in_force,
            metadata=metadata or {}
        )
        
        # Set expiration time
        if time_in_force == "DAY":
            # Expire at end of trading day (assume 24 hours for simplicity)
            order.expire_time = datetime.utcnow() + timedelta(hours=24)
        elif time_in_force == "GTC":
            # Good Till Cancelled - no expiration
            order.expire_time = None
        
        # Get current market data for reference
        current_quote = await market_data_service.get_current_quote(symbol)
        if current_quote:
            order.market_price_at_creation = (current_quote.bid + current_quote.ask) / 2
            order.bid_ask_spread_at_creation = current_quote.spread
        
        # Save to database
        with get_db_session() as db:
            db.add(order)
            db.commit()
            db.refresh(order)
        
        # Add to pending orders
        self.pending_orders[order.id] = order
        
        # Try immediate execution for market orders
        if order_type == OrderType.MARKET.value:
            await self._execute_market_order(order.id)
        
        self.logger.info(f"Submitted order {order_id}: {side} {quantity} {symbol} @ {order_type}")
        return order
    
    async def _validate_order_params(
        self,
        session_id: int,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal],
        stop_price: Optional[Decimal]
    ) -> None:
        """Validate order parameters."""
        
        # Check basic parameters
        if quantity <= 0:
            raise OrderValidationError("Order quantity must be positive")
        
        if side not in [OrderSide.BUY.value, OrderSide.SELL.value]:
            raise OrderValidationError("Invalid order side")
        
        if order_type not in [OrderType.MARKET.value, OrderType.LIMIT.value, 
                             OrderType.STOP.value, OrderType.STOP_LIMIT.value]:
            raise OrderValidationError("Invalid order type")
        
        # Validate price parameters
        if order_type in [OrderType.LIMIT.value, OrderType.STOP_LIMIT.value]:
            if not price or price <= 0:
                raise OrderValidationError("Limit orders require a valid price")
        
        if order_type in [OrderType.STOP.value, OrderType.STOP_LIMIT.value]:
            if not stop_price or stop_price <= 0:
                raise OrderValidationError("Stop orders require a valid stop price")
        
        # Check session status
        session_status = await paper_trading_engine.get_session_status(session_id)
        if not session_status["is_active"]:
            raise OrderValidationError("Paper trading session is not active")
        
        # Check buying power for buy orders
        if side == OrderSide.BUY.value:
            current_quote = await market_data_service.get_current_quote(symbol)
            if current_quote:
                estimated_cost = quantity * current_quote.ask
                # Add buffer for commission and slippage (0.2%)
                estimated_cost *= Decimal("1.002")
                
                if estimated_cost > session_status["cash_balance"]:
                    raise OrderValidationError("Insufficient buying power")
        
        # Check position for sell orders
        elif side == OrderSide.SELL.value:
            # Get current positions
            for position in session_status["open_positions"]:
                if position["symbol"] == symbol and position["quantity"] >= quantity:
                    break
            else:
                raise OrderValidationError("Insufficient position for sell order")
    
    async def _execution_engine(self) -> None:
        """Main execution engine loop."""
        
        while self.execution_engine_running:
            try:
                # Process pending orders
                orders_to_process = list(self.pending_orders.values())
                
                for order in orders_to_process:
                    if order.id not in self.pending_orders:
                        continue  # Order was already processed
                    
                    # Check if order has expired
                    if order.expire_time and datetime.utcnow() > order.expire_time:
                        await self._expire_order(order.id)
                        continue
                    
                    # Try to execute order
                    if order.order_type == OrderType.LIMIT.value:
                        await self._check_limit_order_execution(order.id)
                    elif order.order_type == OrderType.STOP.value:
                        await self._check_stop_order_execution(order.id)
                    elif order.order_type == OrderType.STOP_LIMIT.value:
                        await self._check_stop_limit_order_execution(order.id)
                
                await asyncio.sleep(0.1)  # 100ms execution cycle
                
            except Exception as e:
                self.logger.error(f"Error in execution engine: {e}")
                await asyncio.sleep(1.0)
    
    async def _execute_market_order(self, order_id: int) -> OrderExecutionResult:
        """Execute a market order immediately."""
        
        order = self.pending_orders.get(order_id)
        if not order:
            return OrderExecutionResult(order_id, False, error_message="Order not found")
        
        try:
            # Get current market data
            current_quote = await market_data_service.get_current_quote(order.symbol)
            if not current_quote:
                raise OrderExecutionError("No market data available")
            
            # Determine execution price
            if order.side == OrderSide.BUY.value:
                execution_price = current_quote.ask
            else:
                execution_price = current_quote.bid
            
            # Apply realistic slippage for market orders
            slippage_factor = min(self.max_slippage_pct, current_quote.spread / execution_price)
            slippage_amount = execution_price * slippage_factor
            
            if order.side == OrderSide.BUY.value:
                execution_price += slippage_amount
            else:
                execution_price -= slippage_amount
            
            # Execute the order
            result = await self._execute_order_fill(
                order_id=order_id,
                execution_price=execution_price,
                fill_quantity=order.quantity,
                slippage=slippage_amount * order.quantity
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute market order {order_id}: {e}")
            await self._reject_order(order_id, str(e))
            return OrderExecutionResult(order_id, False, error_message=str(e))
    
    async def _check_limit_order_execution(self, order_id: int) -> None:
        """Check if a limit order can be executed."""
        
        order = self.pending_orders.get(order_id)
        if not order or not order.price:
            return
        
        try:
            current_quote = await market_data_service.get_current_quote(order.symbol)
            if not current_quote:
                return
            
            can_execute = False
            execution_price = None
            
            if order.side == OrderSide.BUY.value:
                # Buy limit: execute if ask price <= limit price
                if current_quote.ask <= order.price:
                    can_execute = True
                    execution_price = min(current_quote.ask, order.price)
            else:
                # Sell limit: execute if bid price >= limit price
                if current_quote.bid >= order.price:
                    can_execute = True
                    execution_price = max(current_quote.bid, order.price)
            
            if can_execute:
                # Apply minimal slippage for limit orders
                slippage_amount = execution_price * Decimal("0.0001")  # 0.01% slippage
                
                await self._execute_order_fill(
                    order_id=order_id,
                    execution_price=execution_price,
                    fill_quantity=order.remaining_quantity,
                    slippage=slippage_amount * order.remaining_quantity
                )
                
        except Exception as e:
            self.logger.error(f"Error checking limit order {order_id}: {e}")
    
    async def _check_stop_order_execution(self, order_id: int) -> None:
        """Check if a stop order should be triggered."""
        
        order = self.pending_orders.get(order_id)
        if not order or not order.stop_price:
            return
        
        try:
            current_quote = await market_data_service.get_current_quote(order.symbol)
            if not current_quote:
                return
            
            current_price = (current_quote.bid + current_quote.ask) / 2
            triggered = False
            
            if order.side == OrderSide.BUY.value:
                # Buy stop: trigger if price >= stop price
                triggered = current_price >= order.stop_price
            else:
                # Sell stop: trigger if price <= stop price
                triggered = current_price <= order.stop_price
            
            if triggered:
                # Convert to market order and execute
                execution_price = current_quote.ask if order.side == OrderSide.BUY.value else current_quote.bid
                
                # Apply slippage for stop orders (higher than limit orders)
                slippage_factor = min(self.max_slippage_pct, Decimal("0.002"))  # 0.2% slippage
                slippage_amount = execution_price * slippage_factor
                
                if order.side == OrderSide.BUY.value:
                    execution_price += slippage_amount
                else:
                    execution_price -= slippage_amount
                
                await self._execute_order_fill(
                    order_id=order_id,
                    execution_price=execution_price,
                    fill_quantity=order.remaining_quantity,
                    slippage=slippage_amount * order.remaining_quantity
                )
                
        except Exception as e:
            self.logger.error(f"Error checking stop order {order_id}: {e}")
    
    async def _check_stop_limit_order_execution(self, order_id: int) -> None:
        """Check if a stop-limit order should be triggered and executed."""
        
        order = self.pending_orders.get(order_id)
        if not order or not order.stop_price or not order.price:
            return
        
        try:
            current_quote = await market_data_service.get_current_quote(order.symbol)
            if not current_quote:
                return
            
            current_price = (current_quote.bid + current_quote.ask) / 2
            
            # First check if stop is triggered
            stop_triggered = False
            if order.side == OrderSide.BUY.value:
                stop_triggered = current_price >= order.stop_price
            else:
                stop_triggered = current_price <= order.stop_price
            
            if not stop_triggered:
                return
            
            # Stop triggered, now check if limit price can be executed
            can_execute = False
            execution_price = None
            
            if order.side == OrderSide.BUY.value:
                if current_quote.ask <= order.price:
                    can_execute = True
                    execution_price = min(current_quote.ask, order.price)
            else:
                if current_quote.bid >= order.price:
                    can_execute = True
                    execution_price = max(current_quote.bid, order.price)
            
            if can_execute:
                slippage_amount = execution_price * Decimal("0.0001")
                
                await self._execute_order_fill(
                    order_id=order_id,
                    execution_price=execution_price,
                    fill_quantity=order.remaining_quantity,
                    slippage=slippage_amount * order.remaining_quantity
                )
                
        except Exception as e:
            self.logger.error(f"Error checking stop-limit order {order_id}: {e}")
    
    async def _execute_order_fill(
        self,
        order_id: int,
        execution_price: Decimal,
        fill_quantity: Decimal,
        slippage: Decimal = Decimal("0")
    ) -> OrderExecutionResult:
        """Execute an order fill."""
        
        order = self.pending_orders.get(order_id)
        if not order:
            return OrderExecutionResult(order_id, False, error_message="Order not found")
        
        try:
            # Calculate commission
            gross_amount = fill_quantity * execution_price
            
            # Get session for commission rate
            with get_db_session() as db:
                from app.models.paper_trading import PaperTradingSession
                session = db.query(PaperTradingSession).filter(
                    PaperTradingSession.id == order.session_id
                ).first()
                
                if not session:
                    raise OrderExecutionError("Trading session not found")
                
                commission = gross_amount * session.commission_rate
            
            # Update order status
            order.filled_quantity += fill_quantity
            order.remaining_quantity -= fill_quantity
            order.commission += commission
            order.slippage += slippage
            
            if order.remaining_quantity <= 0:
                order.status = OrderStatus.FILLED.value
                order.filled_at = datetime.utcnow()
                # Remove from pending orders
                if order.id in self.pending_orders:
                    del self.pending_orders[order.id]
            else:
                order.status = OrderStatus.PARTIALLY_FILLED.value
            
            # Calculate average fill price
            if order.filled_quantity > 0:
                total_cost = (order.avg_fill_price or Decimal("0")) * (order.filled_quantity - fill_quantity)
                total_cost += execution_price * fill_quantity
                order.avg_fill_price = total_cost / order.filled_quantity
            else:
                order.avg_fill_price = execution_price
            
            # Save order updates
            with get_db_session() as db:
                db.merge(order)
                db.commit()
            
            # Notify paper trading engine
            await paper_trading_engine._execute_trade(
                session_id=order.session_id,
                order_id=order.id,
                execution_price=execution_price,
                commission=commission,
                slippage=slippage
            )
            
            self.logger.info(
                f"Executed fill for order {order.order_id}: "
                f"{fill_quantity} @ {execution_price} "
                f"(remaining: {order.remaining_quantity})"
            )
            
            return OrderExecutionResult(
                order_id=order_id,
                executed=True,
                execution_price=execution_price,
                executed_quantity=fill_quantity,
                remaining_quantity=order.remaining_quantity,
                commission=commission,
                slippage=slippage
            )
            
        except Exception as e:
            self.logger.error(f"Error executing order fill {order_id}: {e}")
            return OrderExecutionResult(order_id, False, error_message=str(e))
    
    async def _reject_order(self, order_id: int, reason: str) -> None:
        """Reject an order."""
        
        order = self.pending_orders.get(order_id)
        if not order:
            return
        
        order.status = OrderStatus.REJECTED.value
        order.reject_reason = reason
        order.remaining_quantity = Decimal("0")
        
        with get_db_session() as db:
            db.merge(order)
            db.commit()
        
        # Remove from pending orders
        if order.id in self.pending_orders:
            del self.pending_orders[order.id]
        
        self.logger.warning(f"Rejected order {order.order_id}: {reason}")
    
    async def _expire_order(self, order_id: int) -> None:
        """Expire an order."""
        
        order = self.pending_orders.get(order_id)
        if not order:
            return
        
        order.status = OrderStatus.EXPIRED.value
        order.remaining_quantity = Decimal("0")
        
        with get_db_session() as db:
            db.merge(order)
            db.commit()
        
        # Remove from pending orders
        if order.id in self.pending_orders:
            del self.pending_orders[order.id]
        
        self.logger.info(f"Expired order {order.order_id}")
    
    async def cancel_order(self, order_id: int) -> bool:
        """Cancel a pending order."""
        
        order = self.pending_orders.get(order_id)
        if not order:
            return False
        
        order.status = OrderStatus.CANCELLED.value
        order.remaining_quantity = Decimal("0")
        
        with get_db_session() as db:
            db.merge(order)
            db.commit()
        
        # Remove from pending orders
        if order.id in self.pending_orders:
            del self.pending_orders[order.id]
        
        self.logger.info(f"Cancelled order {order.order_id}")
        return True
    
    async def get_order_status(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order status."""
        
        with get_db_session() as db:
            order = db.query(PaperOrder).filter(PaperOrder.id == order_id).first()
            
            if not order:
                return None
            
            return {
                "order_id": order.order_id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "order_type": order.order_type,
                "quantity": float(order.quantity),
                "filled_quantity": float(order.filled_quantity),
                "remaining_quantity": float(order.remaining_quantity),
                "price": float(order.price) if order.price else None,
                "stop_price": float(order.stop_price) if order.stop_price else None,
                "avg_fill_price": float(order.avg_fill_price) if order.avg_fill_price else None,
                "status": order.status,
                "commission": float(order.commission),
                "slippage": float(order.slippage),
                "time_in_force": order.time_in_force,
                "created_at": order.created_at.isoformat(),
                "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                "reject_reason": order.reject_reason
            }
    
    async def get_orders_for_session(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a trading session."""
        
        with get_db_session() as db:
            orders = db.query(PaperOrder).filter(
                PaperOrder.session_id == session_id
            ).order_by(desc(PaperOrder.created_at)).all()
            
            return [await self.get_order_status(order.id) for order in orders]
    
    async def cleanup(self) -> None:
        """Cleanup order manager."""
        
        self.execution_engine_running = False
        self.logger.info("Order management system cleaned up")


# Global order manager instance
order_manager = OrderManager()