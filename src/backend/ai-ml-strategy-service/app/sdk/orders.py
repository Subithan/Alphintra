"""
Order management system for trading strategies.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union, Callable
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import uuid


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class TimeInForce(Enum):
    """Time-in-force enumeration."""
    DAY = "day"          # Good for day
    GTC = "gtc"          # Good till cancelled
    IOC = "ioc"          # Immediate or cancel
    FOK = "fok"          # Fill or kill


class Order:
    """Represents a trading order."""
    
    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        strategy_id: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force
        self.strategy_id = strategy_id
        
        # Order state
        self.status = OrderStatus.PENDING
        self.filled_quantity = Decimal("0")
        self.remaining_quantity = quantity
        self.avg_fill_price = Decimal("0")
        
        # Timestamps
        self.created_at = datetime.now()
        self.submitted_at: Optional[datetime] = None
        self.filled_at: Optional[datetime] = None
        self.cancelled_at: Optional[datetime] = None
        
        # Execution details
        self.fills: List[Dict] = []
        self.commission = Decimal("0")
        self.reject_reason: Optional[str] = None
        
        # For trailing stops
        self.trail_amount: Optional[Decimal] = None
        self.trail_percent: Optional[Decimal] = None
        self.trail_stop_price: Optional[Decimal] = None
    
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side == OrderSide.BUY
    
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side == OrderSide.SELL
    
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED
    
    def is_active(self) -> bool:
        """Check if order is still active (can be filled)."""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
    
    def add_fill(self, quantity: Decimal, price: Decimal, timestamp: datetime = None, 
                commission: Decimal = Decimal("0")):
        """Add a fill to the order."""
        timestamp = timestamp or datetime.now()
        
        # Validate fill
        if quantity <= 0:
            raise ValueError("Fill quantity must be positive")
        
        if self.filled_quantity + quantity > self.quantity:
            raise ValueError("Fill quantity exceeds remaining quantity")
        
        # Record fill
        fill = {
            "quantity": quantity,
            "price": price,
            "timestamp": timestamp,
            "commission": commission
        }
        self.fills.append(fill)
        
        # Update order state
        self.filled_quantity += quantity
        self.remaining_quantity = self.quantity - self.filled_quantity
        self.commission += commission
        
        # Calculate average fill price
        total_value = sum(fill["quantity"] * fill["price"] for fill in self.fills)
        self.avg_fill_price = total_value / self.filled_quantity
        
        # Update status
        if self.remaining_quantity == 0:
            self.status = OrderStatus.FILLED
            self.filled_at = timestamp
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
    
    def cancel(self, reason: str = None):
        """Cancel the order."""
        if not self.is_active():
            raise ValueError("Cannot cancel inactive order")
        
        self.status = OrderStatus.CANCELLED
        self.cancelled_at = datetime.now()
        self.reject_reason = reason or "Cancelled by user"
    
    def reject(self, reason: str):
        """Reject the order."""
        self.status = OrderStatus.REJECTED
        self.reject_reason = reason
    
    def update_trailing_stop(self, current_price: Decimal):
        """Update trailing stop price based on current market price."""
        if self.order_type != OrderType.TRAILING_STOP:
            return
        
        if self.trail_stop_price is None:
            # Initialize trailing stop
            if self.side == OrderSide.SELL:
                # Trailing stop for long position
                if self.trail_amount:
                    self.trail_stop_price = current_price - self.trail_amount
                elif self.trail_percent:
                    self.trail_stop_price = current_price * (Decimal("1") - self.trail_percent / Decimal("100"))
            else:
                # Trailing stop for short position
                if self.trail_amount:
                    self.trail_stop_price = current_price + self.trail_amount
                elif self.trail_percent:
                    self.trail_stop_price = current_price * (Decimal("1") + self.trail_percent / Decimal("100"))
        else:
            # Update trailing stop
            if self.side == OrderSide.SELL:
                # For long positions, move stop up with price
                if self.trail_amount:
                    new_stop = current_price - self.trail_amount
                    if new_stop > self.trail_stop_price:
                        self.trail_stop_price = new_stop
                elif self.trail_percent:
                    new_stop = current_price * (Decimal("1") - self.trail_percent / Decimal("100"))
                    if new_stop > self.trail_stop_price:
                        self.trail_stop_price = new_stop
            else:
                # For short positions, move stop down with price
                if self.trail_amount:
                    new_stop = current_price + self.trail_amount
                    if new_stop < self.trail_stop_price:
                        self.trail_stop_price = new_stop
                elif self.trail_percent:
                    new_stop = current_price * (Decimal("1") + self.trail_percent / Decimal("100"))
                    if new_stop < self.trail_stop_price:
                        self.trail_stop_price = new_stop
    
    def should_trigger(self, current_price: Decimal) -> bool:
        """Check if order should trigger based on current price."""
        if self.order_type == OrderType.MARKET:
            return True
        
        elif self.order_type == OrderType.LIMIT:
            if self.side == OrderSide.BUY:
                return current_price <= self.price
            else:
                return current_price >= self.price
        
        elif self.order_type == OrderType.STOP:
            if self.side == OrderSide.BUY:
                return current_price >= self.stop_price
            else:
                return current_price <= self.stop_price
        
        elif self.order_type == OrderType.TRAILING_STOP:
            if self.trail_stop_price is None:
                return False
            
            if self.side == OrderSide.SELL:
                return current_price <= self.trail_stop_price
            else:
                return current_price >= self.trail_stop_price
        
        return False
    
    def to_dict(self) -> Dict:
        """Convert order to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": float(self.quantity),
            "order_type": self.order_type.value,
            "price": float(self.price) if self.price else None,
            "stop_price": float(self.stop_price) if self.stop_price else None,
            "status": self.status.value,
            "filled_quantity": float(self.filled_quantity),
            "remaining_quantity": float(self.remaining_quantity),
            "avg_fill_price": float(self.avg_fill_price),
            "commission": float(self.commission),
            "created_at": self.created_at.isoformat(),
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "fills_count": len(self.fills),
            "strategy_id": self.strategy_id
        }


class OrderManager:
    """Manages order submission, tracking, and execution."""
    
    def __init__(self, portfolio=None, execution_engine=None):
        self.portfolio = portfolio
        self.execution_engine = execution_engine
        
        # Order tracking
        self.orders: Dict[str, Order] = {}
        self.active_orders: Dict[str, Order] = {}
        
        # Callbacks
        self.on_order_filled: Optional[Callable] = None
        self.on_order_cancelled: Optional[Callable] = None
        self.on_order_rejected: Optional[Callable] = None
        
        # Default settings
        self.default_commission_rate = Decimal("0.001")  # 0.1%
        self.default_slippage = Decimal("0.0005")        # 0.05%
    
    def market_order(self, symbol: str, quantity: Decimal, side: str, 
                    strategy_id: str = None) -> Order:
        """Create and submit a market order."""
        order_side = OrderSide.BUY if side.lower() in ["buy", "long"] else OrderSide.SELL
        
        order = Order(
            symbol=symbol,
            side=order_side,
            quantity=quantity,
            order_type=OrderType.MARKET,
            strategy_id=strategy_id
        )
        
        return self.submit_order(order)
    
    def limit_order(self, symbol: str, quantity: Decimal, side: str, price: Decimal,
                   strategy_id: str = None) -> Order:
        """Create and submit a limit order."""
        order_side = OrderSide.BUY if side.lower() in ["buy", "long"] else OrderSide.SELL
        
        order = Order(
            symbol=symbol,
            side=order_side,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            price=price,
            strategy_id=strategy_id
        )
        
        return self.submit_order(order)
    
    def stop_order(self, symbol: str, quantity: Decimal, side: str, stop_price: Decimal,
                  strategy_id: str = None) -> Order:
        """Create and submit a stop order."""
        order_side = OrderSide.BUY if side.lower() in ["buy", "long"] else OrderSide.SELL
        
        order = Order(
            symbol=symbol,
            side=order_side,
            quantity=quantity,
            order_type=OrderType.STOP,
            stop_price=stop_price,
            strategy_id=strategy_id
        )
        
        return self.submit_order(order)
    
    def trailing_stop_order(self, symbol: str, quantity: Decimal, side: str,
                           trail_amount: Decimal = None, trail_percent: Decimal = None,
                           strategy_id: str = None) -> Order:
        """Create and submit a trailing stop order."""
        if trail_amount is None and trail_percent is None:
            raise ValueError("Must specify either trail_amount or trail_percent")
        
        order_side = OrderSide.BUY if side.lower() in ["buy", "long"] else OrderSide.SELL
        
        order = Order(
            symbol=symbol,
            side=order_side,
            quantity=quantity,
            order_type=OrderType.TRAILING_STOP,
            strategy_id=strategy_id
        )
        
        order.trail_amount = trail_amount
        order.trail_percent = trail_percent
        
        return self.submit_order(order)
    
    def submit_order(self, order: Order) -> Order:
        """Submit an order for execution."""
        # Validate order
        validation_result = self._validate_order(order)
        if not validation_result["valid"]:
            order.reject("; ".join(validation_result["errors"]))
            self.orders[order.id] = order
            if self.on_order_rejected:
                self.on_order_rejected(order)
            return order
        
        # Add to tracking
        order.status = OrderStatus.SUBMITTED
        order.submitted_at = datetime.now()
        self.orders[order.id] = order
        self.active_orders[order.id] = order
        
        # Submit to execution engine
        if self.execution_engine:
            self.execution_engine.submit_order(order)
        
        return order
    
    def cancel_order(self, order_id: str, reason: str = None) -> bool:
        """Cancel an active order."""
        if order_id not in self.active_orders:
            return False
        
        order = self.active_orders[order_id]
        order.cancel(reason)
        
        # Remove from active orders
        del self.active_orders[order_id]
        
        if self.on_order_cancelled:
            self.on_order_cancelled(order)
        
        return True
    
    def cancel_all_orders(self, symbol: str = None, strategy_id: str = None):
        """Cancel all active orders, optionally filtered by symbol or strategy."""
        orders_to_cancel = []
        
        for order in self.active_orders.values():
            if symbol and order.symbol != symbol:
                continue
            if strategy_id and order.strategy_id != strategy_id:
                continue
            orders_to_cancel.append(order.id)
        
        for order_id in orders_to_cancel:
            self.cancel_order(order_id, "Cancelled by strategy")
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    def get_orders(self, symbol: str = None, strategy_id: str = None, 
                  status: OrderStatus = None) -> List[Order]:
        """Get orders with optional filtering."""
        orders = []
        
        for order in self.orders.values():
            if symbol and order.symbol != symbol:
                continue
            if strategy_id and order.strategy_id != strategy_id:
                continue
            if status and order.status != status:
                continue
            orders.append(order)
        
        return orders
    
    def get_active_orders(self, symbol: str = None) -> List[Order]:
        """Get all active orders."""
        if symbol:
            return [order for order in self.active_orders.values() if order.symbol == symbol]
        return list(self.active_orders.values())
    
    def process_market_update(self, symbol: str, price: Decimal, timestamp: datetime = None):
        """Process market price update and check for order triggers."""
        timestamp = timestamp or datetime.now()
        
        # Check active orders for this symbol
        orders_to_trigger = []
        
        for order in self.active_orders.values():
            if order.symbol != symbol:
                continue
            
            # Update trailing stops
            if order.order_type == OrderType.TRAILING_STOP:
                order.update_trailing_stop(price)
            
            # Check if order should trigger
            if order.should_trigger(price):
                orders_to_trigger.append(order)
        
        # Execute triggered orders
        for order in orders_to_trigger:
            self._execute_order(order, price, timestamp)
    
    def _execute_order(self, order: Order, price: Decimal, timestamp: datetime):
        """Execute an order at the given price."""
        # Apply slippage for market orders
        execution_price = price
        if order.order_type == OrderType.MARKET:
            if order.side == OrderSide.BUY:
                execution_price = price * (Decimal("1") + self.default_slippage)
            else:
                execution_price = price * (Decimal("1") - self.default_slippage)
        
        # Calculate commission
        commission = order.quantity * execution_price * self.default_commission_rate
        
        # Fill the order
        order.add_fill(order.remaining_quantity, execution_price, timestamp, commission)
        
        # Remove from active orders if filled
        if order.is_filled() and order.id in self.active_orders:
            del self.active_orders[order.id]
        
        # Notify callback
        if self.on_order_filled:
            self.on_order_filled(order)
    
    def _validate_order(self, order: Order) -> Dict[str, Union[bool, List[str]]]:
        """Validate an order before submission."""
        errors = []
        
        # Basic validation
        if order.quantity <= 0:
            errors.append("Order quantity must be positive")
        
        if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and order.price is None:
            errors.append("Limit orders require a price")
        
        if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and order.stop_price is None:
            errors.append("Stop orders require a stop price")
        
        # Portfolio validation
        if self.portfolio:
            portfolio_validation = self.portfolio.validate_trade(
                order.symbol, order.quantity, order.price or Decimal("0"), order.side.value
            )
            if not portfolio_validation["valid"]:
                errors.extend(portfolio_validation["errors"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def get_order_stats(self) -> Dict:
        """Get order statistics."""
        total_orders = len(self.orders)
        filled_orders = len([o for o in self.orders.values() if o.is_filled()])
        cancelled_orders = len([o for o in self.orders.values() if o.status == OrderStatus.CANCELLED])
        rejected_orders = len([o for o in self.orders.values() if o.status == OrderStatus.REJECTED])
        
        total_commission = sum(o.commission for o in self.orders.values())
        
        return {
            "total_orders": total_orders,
            "filled_orders": filled_orders,
            "cancelled_orders": cancelled_orders,
            "rejected_orders": rejected_orders,
            "active_orders": len(self.active_orders),
            "fill_rate": (filled_orders / total_orders * 100) if total_orders > 0 else 0,
            "total_commission": float(total_commission)
        }