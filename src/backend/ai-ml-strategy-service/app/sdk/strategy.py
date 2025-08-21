"""
Base strategy class and context for strategy development.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
import logging
import pandas as pd

from app.sdk.data import MarketData
from app.sdk.portfolio import Portfolio
from app.sdk.orders import OrderManager
from app.sdk.risk import RiskManager


class StrategyContext:
    """
    Context object that provides access to market data, portfolio, and trading functions.
    """
    
    def __init__(
        self,
        market_data: MarketData,
        portfolio: Portfolio,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        strategy_id: str,
        user_id: str,
        parameters: Dict[str, Any] = None
    ):
        self.market_data = market_data
        self.portfolio = portfolio
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.strategy_id = strategy_id
        self.user_id = user_id
        self.parameters = parameters or {}
        
        # Strategy state
        self.current_time: Optional[datetime] = None
        self.current_bar: Optional[Dict[str, Any]] = None
        self.bar_count: int = 0
        self.is_live: bool = False
        
        # Logging
        self.logger = logging.getLogger(f"strategy.{strategy_id}")
        
        # Custom variables for strategy state
        self.variables: Dict[str, Any] = {}
        
        # Performance tracking
        self.metrics: Dict[str, Any] = {}
        
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Log a message with strategy context."""
        log_data = {
            "strategy_id": self.strategy_id,
            "timestamp": self.current_time.isoformat() if self.current_time else None,
            "bar_count": self.bar_count,
            **kwargs
        }
        
        if level.upper() == "DEBUG":
            self.logger.debug(message, extra=log_data)
        elif level.upper() == "INFO":
            self.logger.info(message, extra=log_data)
        elif level.upper() == "WARNING":
            self.logger.warning(message, extra=log_data)
        elif level.upper() == "ERROR":
            self.logger.error(message, extra=log_data)
        else:
            self.logger.info(message, extra=log_data)
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get a strategy parameter."""
        return self.parameters.get(name, default)
    
    def set_variable(self, name: str, value: Any):
        """Set a strategy variable for state management."""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a strategy variable."""
        return self.variables.get(name, default)
    
    def record_metric(self, name: str, value: Any):
        """Record a custom metric for performance tracking."""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "timestamp": self.current_time,
            "value": value,
            "bar_count": self.bar_count
        })


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    
    Strategies should inherit from this class and implement the required methods.
    """
    
    def __init__(self, name: str = None, description: str = None):
        self.name = name or self.__class__.__name__
        self.description = description or ""
        self.version = "1.0.0"
        
        # Strategy metadata
        self.author = ""
        self.tags = []
        self.category = "custom"
        
        # Context will be set by the execution engine
        self.context: Optional[StrategyContext] = None
        
        # Strategy state
        self.is_initialized = False
        self.is_running = False
        
    def set_context(self, context: StrategyContext):
        """Set the strategy context (called by execution engine)."""
        self.context = context
        
    @property
    def data(self) -> MarketData:
        """Quick access to market data."""
        return self.context.market_data
    
    @property
    def portfolio(self) -> Portfolio:
        """Quick access to portfolio."""
        return self.context.portfolio
    
    @property
    def orders(self) -> OrderManager:
        """Quick access to order manager."""
        return self.context.order_manager
    
    @property
    def risk(self) -> RiskManager:
        """Quick access to risk manager."""
        return self.context.risk_manager
    
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Log a message."""
        if self.context:
            self.context.log(message, level, **kwargs)
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get a strategy parameter."""
        return self.context.get_parameter(name, default) if self.context else default
    
    def set_variable(self, name: str, value: Any):
        """Set a strategy variable."""
        if self.context:
            self.context.set_variable(name, value)
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a strategy variable."""
        return self.context.get_variable(name, default) if self.context else default
    
    def record_metric(self, name: str, value: Any):
        """Record a custom metric."""
        if self.context:
            self.context.record_metric(name, value)
    
    @abstractmethod
    def initialize(self):
        """
        Initialize the strategy. Called once before the first bar.
        
        Use this method to:
        - Set up indicators
        - Initialize variables
        - Configure parameters
        - Set up any required state
        """
        pass
    
    @abstractmethod
    def on_bar(self):
        """
        Called on each new bar of data.
        
        This is the main strategy logic where you should:
        - Analyze market data
        - Make trading decisions
        - Place orders
        - Update strategy state
        """
        pass
    
    def on_order_filled(self, order):
        """
        Called when an order is filled.
        
        Args:
            order: The filled order object
        """
        pass
    
    def on_order_cancelled(self, order):
        """
        Called when an order is cancelled.
        
        Args:
            order: The cancelled order object
        """
        pass
    
    def on_position_opened(self, position):
        """
        Called when a new position is opened.
        
        Args:
            position: The new position object
        """
        pass
    
    def on_position_closed(self, position):
        """
        Called when a position is closed.
        
        Args:
            position: The closed position object
        """
        pass
    
    def finalize(self):
        """
        Called after the last bar. Use for cleanup and final calculations.
        """
        pass
    
    def validate_parameters(self) -> List[str]:
        """
        Validate strategy parameters.
        
        Returns:
            List of validation error messages. Empty list if valid.
        """
        return []
    
    def get_required_data(self) -> Dict[str, Any]:
        """
        Specify required data for the strategy.
        
        Returns:
            Dictionary with data requirements:
            - symbols: List of required symbols
            - timeframe: Required timeframe
            - history_bars: Number of historical bars needed
            - indicators: List of required indicators
        """
        return {
            "symbols": [],
            "timeframe": "1d",
            "history_bars": 100,
            "indicators": []
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "category": self.category,
            "required_data": self.get_required_data()
        }


class SimpleStrategy(BaseStrategy):
    """
    A simple example strategy for demonstration purposes.
    """
    
    def __init__(self):
        super().__init__(
            name="Simple Moving Average Strategy",
            description="A basic strategy using moving average crossover"
        )
        self.author = "Alphintra"
        self.tags = ["moving_average", "trend_following", "beginner"]
        self.category = "trend"
    
    def initialize(self):
        """Initialize the strategy."""
        self.log("Initializing Simple MA Strategy")
        
        # Get parameters
        self.short_period = self.get_parameter("short_period", 10)
        self.long_period = self.get_parameter("long_period", 30)
        self.symbol = self.get_parameter("symbol", "BTCUSD")
        
        # Initialize variables
        self.set_variable("position_size", 0)
        self.set_variable("last_signal", None)
        
        self.log(f"Configured with short_period={self.short_period}, long_period={self.long_period}")
    
    def on_bar(self):
        """Main strategy logic."""
        # Get current price data
        current_price = self.data.get_current_price(self.symbol)
        
        # Calculate moving averages
        short_ma = self.data.sma(self.symbol, self.short_period)
        long_ma = self.data.sma(self.symbol, self.long_period)
        
        if short_ma is None or long_ma is None:
            return  # Not enough data yet
        
        # Get current position
        position = self.portfolio.get_position(self.symbol)
        current_size = position.quantity if position else 0
        
        # Generate signals
        if short_ma > long_ma and current_size <= 0:
            # Buy signal
            if current_size < 0:
                # Close short position first
                self.orders.market_order(self.symbol, abs(current_size), "buy")
            
            # Open long position
            order_size = self.calculate_position_size()
            self.orders.market_order(self.symbol, order_size, "buy")
            self.set_variable("last_signal", "buy")
            self.log(f"BUY signal: {self.symbol} at {current_price}")
            
        elif short_ma < long_ma and current_size >= 0:
            # Sell signal
            if current_size > 0:
                # Close long position first
                self.orders.market_order(self.symbol, current_size, "sell")
                
            # Open short position
            order_size = self.calculate_position_size()
            self.orders.market_order(self.symbol, order_size, "sell")
            self.set_variable("last_signal", "sell")
            self.log(f"SELL signal: {self.symbol} at {current_price}")
        
        # Record metrics
        self.record_metric("short_ma", short_ma)
        self.record_metric("long_ma", long_ma)
        self.record_metric("price", current_price)
    
    def calculate_position_size(self) -> Decimal:
        """Calculate position size based on available capital."""
        account_value = self.portfolio.total_value
        position_pct = self.get_parameter("position_percent", 0.1)  # 10% default
        
        max_position_value = account_value * Decimal(str(position_pct))
        current_price = self.data.get_current_price(self.symbol)
        
        if current_price and current_price > 0:
            position_size = max_position_value / Decimal(str(current_price))
            return position_size
        
        return Decimal("0")
    
    def get_required_data(self) -> Dict[str, Any]:
        """Specify data requirements."""
        return {
            "symbols": [self.get_parameter("symbol", "BTCUSD")],
            "timeframe": self.get_parameter("timeframe", "1h"),
            "history_bars": max(self.get_parameter("long_period", 30) + 10, 100),
            "indicators": ["sma"]
        }
    
    def validate_parameters(self) -> List[str]:
        """Validate strategy parameters."""
        errors = []
        
        short_period = self.get_parameter("short_period", 10)
        long_period = self.get_parameter("long_period", 30)
        
        if short_period >= long_period:
            errors.append("short_period must be less than long_period")
        
        if short_period < 1:
            errors.append("short_period must be greater than 0")
            
        if long_period < 2:
            errors.append("long_period must be greater than 1")
        
        position_percent = self.get_parameter("position_percent", 0.1)
        if position_percent <= 0 or position_percent > 1:
            errors.append("position_percent must be between 0 and 1")
        
        return errors