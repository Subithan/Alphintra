"""
Core paper trading engine for strategy execution simulation.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.paper_trading import (
    PaperTradingSession,
    PaperOrder,
    PaperPosition,
    PaperTransaction,
    PaperPortfolioSnapshot,
    MarketDataSnapshot,
    OrderStatus,
    OrderType,
    OrderSide
)
from app.models.strategy import Strategy
from app.database.connection import get_db_session


@dataclass
class OrderRequest:
    """Order request data structure."""
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MarketData:
    """Market data structure."""
    symbol: str
    timestamp: datetime
    bid_price: Decimal
    ask_price: Decimal
    last_price: Decimal
    volume: Decimal
    spread: Decimal


class PaperTradingEngine:
    """Core paper trading engine for strategy execution."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_sessions: Dict[int, Dict] = {}
        self.market_data_cache: Dict[str, MarketData] = {}
        
    async def create_session(
        self,
        strategy_id: int,
        name: str,
        initial_capital: Decimal = Decimal("100000.00"),
        description: Optional[str] = None,
        commission_rate: Decimal = Decimal("0.001"),
        slippage_rate: Decimal = Decimal("0.0001")
    ) -> PaperTradingSession:
        """Create a new paper trading session."""
        
        session = PaperTradingSession(
            strategy_id=strategy_id,
            name=name,
            description=description,
            initial_capital=initial_capital,
            current_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            total_return=Decimal("0"),
            total_return_pct=Decimal("0"),
            max_drawdown=Decimal("0"),
            max_drawdown_pct=Decimal("0")
        )
        
        with get_db_session() as db:
            db.add(session)
            db.commit()
            db.refresh(session)
            
        # Initialize session state
        self.active_sessions[session.id] = {
            "session": session,
            "orders": {},
            "positions": {},
            "cash_balance": initial_capital,
            "last_update": datetime.utcnow()
        }
        
        self.logger.info(f"Created paper trading session {session.id} for strategy {strategy_id}")
        return session
    
    async def submit_order(
        self,
        session_id: int,
        order_request: OrderRequest
    ) -> PaperOrder:
        """Submit an order for execution."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Paper trading session {session_id} not found")
        
        session_state = self.active_sessions[session_id]
        session = session_state["session"]
        
        # Generate order ID
        order_id = f"PT_{session_id}_{uuid.uuid4().hex[:8]}"
        
        # Validate order
        await self._validate_order(session_id, order_request)
        
        # Create order record
        order = PaperOrder(
            session_id=session_id,
            order_id=order_id,
            symbol=order_request.symbol,
            side=order_request.side,
            order_type=order_request.order_type,
            quantity=order_request.quantity,
            price=order_request.price,
            stop_price=order_request.stop_price,
            remaining_quantity=order_request.quantity,
            status=OrderStatus.PENDING.value,
            metadata=order_request.metadata
        )
        
        with get_db_session() as db:
            db.add(order)
            db.commit()
            db.refresh(order)
        
        # Store in session state
        session_state["orders"][order.id] = order
        
        # Attempt immediate execution for market orders
        if order_request.order_type == OrderType.MARKET.value:
            await self._execute_market_order(session_id, order.id)
        
        self.logger.info(f"Submitted order {order_id} for session {session_id}")
        return order
    
    async def _validate_order(self, session_id: int, order_request: OrderRequest) -> None:
        """Validate order before submission."""
        
        session_state = self.active_sessions[session_id]
        session = session_state["session"]
        
        # Check if session is active
        if not session.is_active:
            raise ValueError("Paper trading session is not active")
        
        # Validate order parameters
        if order_request.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        
        if order_request.order_type in [OrderType.LIMIT.value, OrderType.STOP_LIMIT.value]:
            if not order_request.price or order_request.price <= 0:
                raise ValueError("Limit orders require a valid price")
        
        if order_request.order_type in [OrderType.STOP.value, OrderType.STOP_LIMIT.value]:
            if not order_request.stop_price or order_request.stop_price <= 0:
                raise ValueError("Stop orders require a valid stop price")
        
        # Check available capital for buy orders
        if order_request.side == OrderSide.BUY.value:
            market_data = await self._get_market_data(order_request.symbol)
            estimated_cost = order_request.quantity * market_data.ask_price
            estimated_cost *= (1 + session.commission_rate + session.slippage_rate)
            
            if estimated_cost > session_state["cash_balance"]:
                raise ValueError("Insufficient capital for order")
        
        # Check position for sell orders
        elif order_request.side == OrderSide.SELL.value:
            position = session_state["positions"].get(order_request.symbol)
            if not position or position.quantity < order_request.quantity:
                raise ValueError("Insufficient position for sell order")
    
    async def _execute_market_order(self, session_id: int, order_id: int) -> None:
        """Execute a market order immediately."""
        
        session_state = self.active_sessions[session_id]
        order = session_state["orders"][order_id]
        
        try:
            # Get current market data
            market_data = await self._get_market_data(order.symbol)
            
            # Determine execution price
            if order.side == OrderSide.BUY.value:
                execution_price = market_data.ask_price
            else:
                execution_price = market_data.bid_price
            
            # Apply slippage
            slippage_factor = session_state["session"].slippage_rate
            if order.side == OrderSide.BUY.value:
                execution_price *= (1 + slippage_factor)
            else:
                execution_price *= (1 - slippage_factor)
            
            # Calculate commission
            gross_amount = order.quantity * execution_price
            commission = gross_amount * session_state["session"].commission_rate
            
            # Execute the trade
            await self._execute_trade(
                session_id=session_id,
                order_id=order_id,
                execution_price=execution_price,
                commission=commission,
                slippage=gross_amount * slippage_factor
            )
            
        except Exception as e:
            self.logger.error(f"Failed to execute market order {order_id}: {e}")
            await self._reject_order(session_id, order_id, str(e))
    
    async def _execute_trade(
        self,
        session_id: int,
        order_id: int,
        execution_price: Decimal,
        commission: Decimal,
        slippage: Decimal
    ) -> None:
        """Execute a trade and update positions."""
        
        session_state = self.active_sessions[session_id]
        order = session_state["orders"][order_id]
        
        # Calculate trade amounts
        gross_amount = order.quantity * execution_price
        net_amount = gross_amount + commission + slippage
        
        if order.side == OrderSide.BUY.value:
            cash_flow = -net_amount
            position_change = order.quantity
        else:
            cash_flow = gross_amount - commission - slippage
            position_change = -order.quantity
        
        # Create transaction record
        transaction_id = f"TXN_{session_id}_{uuid.uuid4().hex[:8]}"
        transaction = PaperTransaction(
            session_id=session_id,
            order_id=order_id,
            transaction_id=transaction_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=execution_price,
            gross_amount=gross_amount,
            commission=commission,
            slippage=slippage,
            net_amount=net_amount,
            cash_flow=cash_flow,
            position_change=position_change
        )
        
        # Update order status
        order.status = OrderStatus.FILLED.value
        order.filled_quantity = order.quantity
        order.remaining_quantity = Decimal("0")
        order.avg_fill_price = execution_price
        order.commission = commission
        order.slippage = slippage
        order.filled_at = datetime.utcnow()
        
        # Update positions
        await self._update_position(session_id, order.symbol, position_change, execution_price)
        
        # Update cash balance
        session_state["cash_balance"] += cash_flow
        
        # Save to database
        with get_db_session() as db:
            db.add(transaction)
            db.merge(order)
            db.commit()
        
        # Update session performance
        await self._update_session_performance(session_id)
        
        self.logger.info(f"Executed trade for order {order_id}: {order.quantity} {order.symbol} @ {execution_price}")
    
    async def _update_position(
        self,
        session_id: int,
        symbol: str,
        quantity_change: Decimal,
        price: Decimal
    ) -> None:
        """Update or create position."""
        
        session_state = self.active_sessions[session_id]
        
        # Get or create position
        position = session_state["positions"].get(symbol)
        
        if not position:
            # Create new position
            position = PaperPosition(
                session_id=session_id,
                symbol=symbol,
                quantity=quantity_change,
                side="long" if quantity_change > 0 else "short",
                avg_price=price,
                total_cost=abs(quantity_change) * price,
                current_price=price,
                market_value=quantity_change * price,
                unrealized_pnl=Decimal("0"),
                unrealized_pnl_pct=Decimal("0")
            )
            session_state["positions"][symbol] = position
        else:
            # Update existing position
            old_quantity = position.quantity
            old_cost = position.total_cost
            
            new_quantity = old_quantity + quantity_change
            
            if new_quantity == 0:
                # Position closed
                position.is_open = False
                position.closed_at = datetime.utcnow()
                position.realized_pnl = position.unrealized_pnl
                position.realized_pnl_pct = position.unrealized_pnl_pct
                del session_state["positions"][symbol]
            else:
                # Position modified
                if (old_quantity > 0 and quantity_change > 0) or (old_quantity < 0 and quantity_change < 0):
                    # Adding to position
                    new_cost = old_cost + abs(quantity_change) * price
                    position.avg_price = new_cost / abs(new_quantity)
                    position.total_cost = new_cost
                else:
                    # Reducing position
                    cost_reduction = (abs(quantity_change) / abs(old_quantity)) * old_cost
                    position.total_cost = old_cost - cost_reduction
                
                position.quantity = new_quantity
                position.side = "long" if new_quantity > 0 else "short"
        
        # Update market value and P&L
        await self._update_position_pnl(position)
        
        # Save to database
        with get_db_session() as db:
            db.merge(position)
            db.commit()
    
    async def _update_position_pnl(self, position: PaperPosition) -> None:
        """Update position P&L based on current market price."""
        
        if not position.is_open:
            return
        
        # Get current market data
        market_data = await self._get_market_data(position.symbol)
        position.current_price = market_data.last_price
        position.market_value = position.quantity * market_data.last_price
        
        # Calculate unrealized P&L
        if position.side == "long":
            position.unrealized_pnl = position.market_value - position.total_cost
        else:
            position.unrealized_pnl = position.total_cost - position.market_value
        
        if position.total_cost > 0:
            position.unrealized_pnl_pct = (position.unrealized_pnl / position.total_cost) * 100
        else:
            position.unrealized_pnl_pct = Decimal("0")
    
    async def _reject_order(self, session_id: int, order_id: int, reason: str) -> None:
        """Reject an order."""
        
        session_state = self.active_sessions[session_id]
        order = session_state["orders"][order_id]
        
        order.status = OrderStatus.REJECTED.value
        order.remaining_quantity = Decimal("0")
        
        with get_db_session() as db:
            db.merge(order)
            db.commit()
        
        self.logger.warning(f"Rejected order {order_id}: {reason}")
    
    async def _get_market_data(self, symbol: str) -> MarketData:
        """Get current market data for symbol."""
        
        # For simulation, generate realistic market data
        # In production, this would connect to real market data feeds
        
        if symbol in self.market_data_cache:
            cached_data = self.market_data_cache[symbol]
            # Update with small random movement
            price_movement = Decimal(str(0.999 + (hash(str(datetime.utcnow().microsecond)) % 2000) / 100000))
            new_price = cached_data.last_price * price_movement
        else:
            # Initial price based on symbol hash for consistency
            base_price = Decimal(str(50 + (hash(symbol) % 1000)))
            new_price = base_price
        
        spread = new_price * Decimal("0.001")  # 0.1% spread
        
        market_data = MarketData(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            bid_price=new_price - spread / 2,
            ask_price=new_price + spread / 2,
            last_price=new_price,
            volume=Decimal("10000"),
            spread=spread
        )
        
        self.market_data_cache[symbol] = market_data
        return market_data
    
    async def _update_session_performance(self, session_id: int) -> None:
        """Update session performance metrics."""
        
        session_state = self.active_sessions[session_id]
        session = session_state["session"]
        
        # Calculate total portfolio value
        total_position_value = Decimal("0")
        total_unrealized_pnl = Decimal("0")
        
        for position in session_state["positions"].values():
            if position.is_open:
                await self._update_position_pnl(position)
                total_position_value += position.market_value
                total_unrealized_pnl += position.unrealized_pnl
        
        total_portfolio_value = session_state["cash_balance"] + total_position_value
        
        # Update session metrics
        session.current_capital = total_portfolio_value
        session.total_return = total_portfolio_value - session.initial_capital
        session.total_return_pct = (session.total_return / session.initial_capital) * 100
        
        # Calculate drawdown
        if total_portfolio_value > session.initial_capital:
            high_water_mark = max(session.initial_capital, total_portfolio_value)
            current_drawdown = high_water_mark - total_portfolio_value
            current_drawdown_pct = (current_drawdown / high_water_mark) * 100
            
            session.max_drawdown = max(session.max_drawdown, current_drawdown)
            session.max_drawdown_pct = max(session.max_drawdown_pct, current_drawdown_pct)
        
        # Save to database
        with get_db_session() as db:
            db.merge(session)
            db.commit()
    
    async def get_session_status(self, session_id: int) -> Dict[str, Any]:
        """Get current session status and performance."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Paper trading session {session_id} not found")
        
        session_state = self.active_sessions[session_id]
        session = session_state["session"]
        
        # Update performance
        await self._update_session_performance(session_id)
        
        # Calculate position summary
        open_positions = []
        for symbol, position in session_state["positions"].items():
            if position.is_open:
                await self._update_position_pnl(position)
                open_positions.append({
                    "symbol": symbol,
                    "quantity": float(position.quantity),
                    "avg_price": float(position.avg_price),
                    "current_price": float(position.current_price),
                    "market_value": float(position.market_value),
                    "unrealized_pnl": float(position.unrealized_pnl),
                    "unrealized_pnl_pct": float(position.unrealized_pnl_pct)
                })
        
        return {
            "session_id": session_id,
            "strategy_id": session.strategy_id,
            "name": session.name,
            "is_active": session.is_active,
            "initial_capital": float(session.initial_capital),
            "current_capital": float(session.current_capital),
            "cash_balance": float(session_state["cash_balance"]),
            "total_return": float(session.total_return),
            "total_return_pct": float(session.total_return_pct),
            "max_drawdown": float(session.max_drawdown),
            "max_drawdown_pct": float(session.max_drawdown_pct),
            "open_positions": open_positions,
            "num_orders": len(session_state["orders"]),
            "last_update": session_state["last_update"].isoformat()
        }
    
    async def stop_session(self, session_id: int) -> None:
        """Stop a paper trading session."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Paper trading session {session_id} not found")
        
        session_state = self.active_sessions[session_id]
        session = session_state["session"]
        
        # Update final performance
        await self._update_session_performance(session_id)
        
        # Deactivate session
        session.is_active = False
        session.end_time = datetime.utcnow()
        
        with get_db_session() as db:
            db.merge(session)
            db.commit()
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        self.logger.info(f"Stopped paper trading session {session_id}")


# Global paper trading engine instance
paper_trading_engine = PaperTradingEngine()