"""
Portfolio and position management for trading strategies.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


class PositionSide(Enum):
    """Position side enumeration."""
    LONG = "long"
    SHORT = "short"


class Position:
    """Represents a trading position."""
    
    def __init__(self, symbol: str, side: PositionSide, quantity: Decimal, 
                 avg_price: Decimal, timestamp: datetime = None):
        self.symbol = symbol
        self.side = side
        self.quantity = abs(quantity)  # Always positive
        self.avg_price = avg_price
        self.opened_at = timestamp or datetime.now()
        
        # Tracking
        self.realized_pnl = Decimal("0")
        self.total_cost = self.quantity * self.avg_price
        
        # For partial closes
        self.trades: List[Dict] = []
    
    @property
    def market_value(self) -> Decimal:
        """Current market value of the position."""
        return self.quantity * self.avg_price
    
    def get_unrealized_pnl(self, current_price: Decimal) -> Decimal:
        """Calculate unrealized PnL at current price."""
        if self.side == PositionSide.LONG:
            return (current_price - self.avg_price) * self.quantity
        else:  # SHORT
            return (self.avg_price - current_price) * self.quantity
    
    def get_unrealized_pnl_percent(self, current_price: Decimal) -> Decimal:
        """Calculate unrealized PnL percentage."""
        pnl = self.get_unrealized_pnl(current_price)
        if self.total_cost == 0:
            return Decimal("0")
        return (pnl / self.total_cost) * Decimal("100")
    
    def update_position(self, quantity: Decimal, price: Decimal, timestamp: datetime = None):
        """Update position with new trade."""
        timestamp = timestamp or datetime.now()
        
        if self.side == PositionSide.LONG and quantity > 0:
            # Adding to long position
            total_cost = self.total_cost + (quantity * price)
            total_quantity = self.quantity + quantity
            self.avg_price = total_cost / total_quantity
            self.quantity = total_quantity
            self.total_cost = total_cost
            
        elif self.side == PositionSide.SHORT and quantity < 0:
            # Adding to short position
            quantity = abs(quantity)
            total_cost = self.total_cost + (quantity * price)
            total_quantity = self.quantity + quantity
            self.avg_price = total_cost / total_quantity
            self.quantity = total_quantity
            self.total_cost = total_cost
            
        else:
            # Reducing position (partial close)
            quantity = abs(quantity)
            if quantity >= self.quantity:
                # Full close
                if self.side == PositionSide.LONG:
                    pnl = (price - self.avg_price) * self.quantity
                else:
                    pnl = (self.avg_price - price) * self.quantity
                
                self.realized_pnl += pnl
                self.quantity = Decimal("0")
                self.total_cost = Decimal("0")
            else:
                # Partial close
                if self.side == PositionSide.LONG:
                    pnl = (price - self.avg_price) * quantity
                else:
                    pnl = (self.avg_price - price) * quantity
                
                self.realized_pnl += pnl
                self.quantity -= quantity
                self.total_cost = self.quantity * self.avg_price
        
        # Record trade
        self.trades.append({
            "timestamp": timestamp,
            "quantity": quantity,
            "price": price,
            "type": "add" if (self.side == PositionSide.LONG and quantity > 0) or 
                              (self.side == PositionSide.SHORT and quantity < 0) else "reduce"
        })
    
    def is_closed(self) -> bool:
        """Check if position is closed."""
        return self.quantity == 0
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": float(self.quantity),
            "avg_price": float(self.avg_price),
            "market_value": float(self.market_value),
            "realized_pnl": float(self.realized_pnl),
            "opened_at": self.opened_at.isoformat(),
            "is_closed": self.is_closed(),
            "trades_count": len(self.trades)
        }


class Portfolio:
    """Manages portfolio positions and performance."""
    
    def __init__(self, initial_capital: Decimal = Decimal("100000")):
        self.initial_capital = initial_capital
        self.cash_balance = initial_capital
        self.positions: Dict[str, Position] = {}
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_realized_pnl = Decimal("0")
        self.max_drawdown = Decimal("0")
        self.peak_value = initial_capital
        
        # Historical values for performance calculation
        self.value_history: List[Dict] = []
        
    @property
    def total_value(self) -> Decimal:
        """Total portfolio value (cash + positions)."""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash_balance + positions_value
    
    @property
    def positions_value(self) -> Decimal:
        """Total value of all positions."""
        return sum(pos.market_value for pos in self.positions.values())
    
    @property
    def unrealized_pnl(self) -> Decimal:
        """Total unrealized PnL from all positions."""
        # Would need current prices to calculate properly
        return Decimal("0")  # Placeholder
    
    @property
    def total_pnl(self) -> Decimal:
        """Total PnL (realized + unrealized)."""
        return self.total_realized_pnl + self.unrealized_pnl
    
    @property
    def total_return(self) -> Decimal:
        """Total return percentage."""
        if self.initial_capital == 0:
            return Decimal("0")
        return ((self.total_value - self.initial_capital) / self.initial_capital) * Decimal("100")
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol."""
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Check if there's an open position for a symbol."""
        position = self.positions.get(symbol)
        return position is not None and not position.is_closed()
    
    def open_position(self, symbol: str, side: PositionSide, quantity: Decimal, 
                     price: Decimal, timestamp: datetime = None) -> Position:
        """Open a new position."""
        timestamp = timestamp or datetime.now()
        
        # Calculate required cash
        required_cash = quantity * price
        
        if required_cash > self.cash_balance:
            raise ValueError(f"Insufficient cash: required {required_cash}, available {self.cash_balance}")
        
        # Create position
        position = Position(symbol, side, quantity, price, timestamp)
        self.positions[symbol] = position
        
        # Update cash balance
        self.cash_balance -= required_cash
        
        return position
    
    def update_position(self, symbol: str, quantity: Decimal, price: Decimal, 
                       timestamp: datetime = None) -> Optional[Position]:
        """Update existing position with new trade."""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        old_quantity = position.quantity
        
        # Check if this closes the position
        if abs(quantity) >= position.quantity:
            # Closing position
            if position.side == PositionSide.LONG:
                cash_from_close = position.quantity * price
            else:
                cash_from_close = position.quantity * price
            
            self.cash_balance += cash_from_close
            
            # Record trade stats
            pnl = position.get_unrealized_pnl(price)
            self.total_realized_pnl += pnl
            self.total_trades += 1
            
            if pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Update position
            position.update_position(quantity, price, timestamp)
            
            if position.is_closed():
                del self.positions[symbol]
            
        else:
            # Partial close
            close_quantity = abs(quantity)
            cash_from_partial = close_quantity * price
            self.cash_balance += cash_from_partial
            
            position.update_position(quantity, price, timestamp)
        
        return position
    
    def close_position(self, symbol: str, price: Decimal, timestamp: datetime = None) -> bool:
        """Close entire position for a symbol."""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        
        # Close with opposite quantity
        if position.side == PositionSide.LONG:
            close_quantity = -position.quantity
        else:
            close_quantity = position.quantity
        
        self.update_position(symbol, close_quantity, price, timestamp)
        return True
    
    def close_all_positions(self, current_prices: Dict[str, Decimal], 
                           timestamp: datetime = None):
        """Close all open positions."""
        symbols_to_close = list(self.positions.keys())
        
        for symbol in symbols_to_close:
            if symbol in current_prices:
                self.close_position(symbol, current_prices[symbol], timestamp)
    
    def calculate_drawdown(self, current_value: Decimal = None) -> Decimal:
        """Calculate current drawdown."""
        current_value = current_value or self.total_value
        
        if current_value > self.peak_value:
            self.peak_value = current_value
            return Decimal("0")
        
        if self.peak_value == 0:
            return Decimal("0")
        
        drawdown = ((self.peak_value - current_value) / self.peak_value) * Decimal("100")
        
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        return drawdown
    
    def record_value(self, timestamp: datetime = None, additional_data: Dict = None):
        """Record portfolio value for performance tracking."""
        timestamp = timestamp or datetime.now()
        
        value_record = {
            "timestamp": timestamp,
            "total_value": float(self.total_value),
            "cash_balance": float(self.cash_balance),
            "positions_value": float(self.positions_value),
            "total_pnl": float(self.total_pnl),
            "drawdown": float(self.calculate_drawdown()),
            "position_count": len([p for p in self.positions.values() if not p.is_closed()])
        }
        
        if additional_data:
            value_record.update(additional_data)
        
        self.value_history.append(value_record)
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics."""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            "initial_capital": float(self.initial_capital),
            "current_value": float(self.total_value),
            "cash_balance": float(self.cash_balance),
            "positions_value": float(self.positions_value),
            "total_return": float(self.total_return),
            "total_pnl": float(self.total_pnl),
            "realized_pnl": float(self.total_realized_pnl),
            "unrealized_pnl": float(self.unrealized_pnl),
            "max_drawdown": float(self.max_drawdown),
            "current_drawdown": float(self.calculate_drawdown()),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "open_positions": len([p for p in self.positions.values() if not p.is_closed()]),
            "peak_value": float(self.peak_value)
        }
    
    def get_positions_summary(self) -> List[Dict]:
        """Get summary of all positions."""
        return [pos.to_dict() for pos in self.positions.values() if not pos.is_closed()]
    
    def reset(self, new_capital: Decimal = None):
        """Reset portfolio to initial state."""
        self.initial_capital = new_capital or self.initial_capital
        self.cash_balance = self.initial_capital
        self.positions.clear()
        
        # Reset performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_realized_pnl = Decimal("0")
        self.max_drawdown = Decimal("0")
        self.peak_value = self.initial_capital
        self.value_history.clear()
    
    def validate_trade(self, symbol: str, quantity: Decimal, price: Decimal, 
                      side: str) -> Dict[str, Union[bool, str]]:
        """Validate if a trade can be executed."""
        errors = []
        
        # Check for valid inputs
        if quantity <= 0:
            errors.append("Quantity must be positive")
        
        if price <= 0:
            errors.append("Price must be positive")
        
        # Check cash requirements for new positions
        if not self.has_position(symbol) and side.lower() in ["buy", "long"]:
            required_cash = quantity * price
            if required_cash > self.cash_balance:
                errors.append(f"Insufficient cash: required {required_cash}, available {self.cash_balance}")
        
        # Check position size for closes
        if self.has_position(symbol) and side.lower() in ["sell", "short"]:
            position = self.get_position(symbol)
            if position and quantity > position.quantity:
                errors.append(f"Cannot sell {quantity} shares, only {position.quantity} available")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }