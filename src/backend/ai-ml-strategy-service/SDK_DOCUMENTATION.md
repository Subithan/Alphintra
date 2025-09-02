# Alphintra Python SDK Documentation

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Components](#core-components)
5. [Strategy Development](#strategy-development)
6. [Market Data](#market-data)
7. [Portfolio Management](#portfolio-management)
8. [Order Management](#order-management)
9. [Risk Management](#risk-management)
10. [Technical Indicators](#technical-indicators)
11. [Backtesting](#backtesting)
12. [Examples](#examples)
13. [Best Practices](#best-practices)

## Overview

The Alphintra Python SDK provides a comprehensive framework for developing, testing, and deploying algorithmic trading strategies. It offers a high-level API that abstracts the complexity of market data handling, order management, and risk controls while providing flexibility for advanced users.

### Key Features

- **Strategy Framework**: Base classes for building robust trading strategies
- **Market Data Access**: Real-time and historical data with built-in caching
- **Portfolio Management**: Position tracking, P&L calculation, and performance metrics
- **Order Management**: Multiple order types with smart routing and execution
- **Risk Management**: Built-in risk controls and position sizing
- **Technical Indicators**: Comprehensive library of technical analysis tools
- **Backtesting**: Advanced backtesting engine with realistic market simulation
- **Live Trading**: Seamless transition from backtesting to live execution

## Installation

### From PyPI (Recommended)

```bash
pip install alphintra-sdk
```

### From Source

```bash
git clone https://github.com/alphintra/python-sdk.git
cd python-sdk
pip install -e .
```

### Dependencies

The SDK requires Python 3.8+ and the following packages:

- pandas >= 1.5.0
- numpy >= 1.21.0
- requests >= 2.28.0
- websocket-client >= 1.4.0
- ta-lib >= 0.4.25 (optional, for additional indicators)

## Quick Start

### Basic Strategy Example

```python
from alphintra import BaseStrategy

class SimpleMovingAverageStrategy(BaseStrategy):
    """Simple moving average crossover strategy."""
    
    def initialize(self, context):
        """Initialize strategy parameters and state."""
        # Set strategy parameters
        self.short_window = context.get_parameter("short_window", 10)
        self.long_window = context.get_parameter("long_window", 30)
        
        # Initialize state variables
        context.set_variable("position", 0)
        context.set_variable("last_signal", None)
        
        # Log initialization
        context.log(f"Strategy initialized with {self.short_window}/{self.long_window} MA crossover")
    
    def on_bar(self, context):
        """Process new market data bar."""
        # Get historical data
        data = context.market_data.get_bars(count=max(self.short_window, self.long_window) + 1)
        
        if len(data) < self.long_window:
            return  # Not enough data
        
        # Calculate moving averages
        short_ma = data.close.rolling(self.short_window).mean().iloc[-1]
        long_ma = data.close.rolling(self.long_window).mean().iloc[-1]
        
        # Get current position
        current_position = context.get_variable("position")
        
        # Generate signals
        if short_ma > long_ma and current_position <= 0:
            # Buy signal
            context.order_manager.market_order("BTCUSDT", 1.0)
            context.set_variable("position", 1)
            context.set_variable("last_signal", "buy")
            context.log(f"Buy signal: Short MA ({short_ma:.2f}) > Long MA ({long_ma:.2f})")
            
        elif short_ma < long_ma and current_position >= 0:
            # Sell signal
            context.order_manager.market_order("BTCUSDT", -1.0)
            context.set_variable("position", -1)
            context.set_variable("last_signal", "sell")
            context.log(f"Sell signal: Short MA ({short_ma:.2f}) < Long MA ({long_ma:.2f})")
    
    def on_order_fill(self, context, order):
        """Handle order execution."""
        context.log(f"Order filled: {order.symbol} {order.side} {order.quantity} @ {order.fill_price}")
        
        # Record custom metrics
        context.record_metric("fill_price", order.fill_price)
        context.record_metric("slippage", abs(order.fill_price - order.limit_price) if order.limit_price else 0)
```

### Running the Strategy

```python
# Strategy parameters
parameters = {
    "short_window": 10,
    "long_window": 30
}

# Create strategy instance
strategy = SimpleMovingAverageStrategy()

# Run backtest
from alphintra import BacktestRunner

backtest = BacktestRunner(
    strategy=strategy,
    dataset="crypto_1min_2023",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=100000,
    parameters=parameters
)

results = backtest.run()
print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
```

## Core Components

### BaseStrategy Class

The foundation class for all trading strategies.

```python
from abc import ABC, abstractmethod
from alphintra import StrategyContext

class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def initialize(self, context: StrategyContext):
        """
        Called once at strategy startup.
        
        Args:
            context: Strategy execution context
        """
        pass
    
    def on_bar(self, context: StrategyContext):
        """
        Called for each new data bar.
        
        Args:
            context: Strategy execution context with current market data
        """
        pass
    
    def on_order_fill(self, context: StrategyContext, order):
        """
        Called when an order is filled.
        
        Args:
            context: Strategy execution context
            order: Filled order object
        """
        pass
    
    def on_error(self, context: StrategyContext, error: Exception):
        """
        Called when an error occurs during strategy execution.
        
        Args:
            context: Strategy execution context
            error: Exception that occurred
        """
        pass
    
    def on_market_open(self, context: StrategyContext):
        """Called when market opens."""
        pass
    
    def on_market_close(self, context: StrategyContext):
        """Called when market closes."""
        pass
```

### StrategyContext Class

Provides access to market data, portfolio, and trading functions.

```python
class StrategyContext:
    """Strategy execution context."""
    
    def __init__(self, market_data, portfolio, order_manager, risk_manager, 
                 strategy_id, user_id, parameters=None):
        # Core components
        self.market_data = market_data
        self.portfolio = portfolio
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        
        # Strategy metadata
        self.strategy_id = strategy_id
        self.user_id = user_id
        self.parameters = parameters or {}
        
        # Runtime state
        self.current_time = None
        self.current_bar = None
        self.bar_count = 0
        self.is_live = False
        
        # Custom variables
        self.variables = {}
        self.metrics = {}
    
    def get_parameter(self, name: str, default=None):
        """Get strategy parameter value."""
        return self.parameters.get(name, default)
    
    def set_variable(self, name: str, value):
        """Set custom strategy variable."""
        self.variables[name] = value
    
    def get_variable(self, name: str, default=None):
        """Get custom strategy variable."""
        return self.variables.get(name, default)
    
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Log message with strategy context."""
        # Implementation handles structured logging
        pass
    
    def record_metric(self, name: str, value):
        """Record custom performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "timestamp": self.current_time,
            "value": value,
            "bar_count": self.bar_count
        })
```

## Strategy Development

### Strategy Lifecycle

1. **Initialization**: `initialize()` method called once at startup
2. **Data Processing**: `on_bar()` called for each new data bar
3. **Order Handling**: `on_order_fill()` called when orders execute
4. **Error Handling**: `on_error()` called for exceptions
5. **Market Events**: `on_market_open()` and `on_market_close()` for session events

### Parameter Management

```python
class ParameterizedStrategy(BaseStrategy):
    def initialize(self, context):
        # Required parameters
        self.symbol = context.get_parameter("symbol")
        if not self.symbol:
            raise ValueError("Symbol parameter is required")
        
        # Optional parameters with defaults
        self.lookback_period = context.get_parameter("lookback_period", 20)
        self.threshold = context.get_parameter("threshold", 0.02)
        self.max_position_size = context.get_parameter("max_position_size", 1.0)
        
        # Validate parameters
        if self.lookback_period < 1:
            raise ValueError("Lookback period must be positive")
        
        context.log(f"Strategy initialized for {self.symbol}")
```

### State Management

```python
class StatefulStrategy(BaseStrategy):
    def initialize(self, context):
        # Initialize state variables
        context.set_variable("trend_direction", "neutral")
        context.set_variable("entry_price", None)
        context.set_variable("position_size", 0)
        context.set_variable("consecutive_losses", 0)
    
    def on_bar(self, context):
        # Access state variables
        trend = context.get_variable("trend_direction")
        position_size = context.get_variable("position_size")
        
        # Update state based on market conditions
        if self.detect_trend_change(context):
            new_trend = self.calculate_trend(context)
            context.set_variable("trend_direction", new_trend)
            context.log(f"Trend changed to {new_trend}")
    
    def on_order_fill(self, context, order):
        # Update position state
        current_size = context.get_variable("position_size")
        new_size = current_size + order.quantity
        context.set_variable("position_size", new_size)
        
        if order.side == "buy":
            context.set_variable("entry_price", order.fill_price)
```

### Error Handling

```python
class RobustStrategy(BaseStrategy):
    def on_bar(self, context):
        try:
            # Main strategy logic
            self.process_signals(context)
            
        except Exception as e:
            context.log(f"Error in signal processing: {str(e)}", level="ERROR")
            # Implement recovery logic
            self.handle_error(context, e)
    
    def on_error(self, context, error):
        """Global error handler."""
        context.log(f"Strategy error: {str(error)}", level="ERROR")
        
        # Emergency position closure on critical errors
        if isinstance(error, CriticalError):
            self.emergency_exit(context)
    
    def handle_error(self, context, error):
        """Implement specific error recovery logic."""
        if isinstance(error, DataError):
            # Skip this bar and continue
            context.log("Skipping bar due to data error", level="WARNING")
        elif isinstance(error, OrderError):
            # Cancel pending orders
            self.cancel_all_orders(context)
```

## Market Data

### MarketData Class

Provides access to market data with built-in caching and validation.

```python
class MarketData:
    """Market data interface."""
    
    def get_bars(self, symbol: str = None, count: int = 100, 
                 timeframe: str = "1m") -> pd.DataFrame:
        """
        Get historical OHLCV bars.
        
        Args:
            symbol: Trading symbol (uses default if None)
            count: Number of bars to retrieve
            timeframe: Bar timeframe (1m, 5m, 1h, 1d, etc.)
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass
    
    def get_current_price(self, symbol: str) -> float:
        """Get current market price."""
        pass
    
    def get_bid_ask(self, symbol: str) -> tuple[float, float]:
        """Get current bid and ask prices."""
        pass
    
    def get_orderbook(self, symbol: str, depth: int = 10) -> dict:
        """Get order book data."""
        pass
    
    def get_trades(self, symbol: str, count: int = 100) -> pd.DataFrame:
        """Get recent trades."""
        pass
    
    def is_market_open(self, symbol: str = None) -> bool:
        """Check if market is currently open."""
        pass
    
    def get_market_hours(self, symbol: str) -> dict:
        """Get market hours information."""
        pass
```

### Data Access Examples

```python
class DataDrivenStrategy(BaseStrategy):
    def on_bar(self, context):
        # Get different timeframes
        minute_bars = context.market_data.get_bars("BTCUSDT", count=60, timeframe="1m")
        hourly_bars = context.market_data.get_bars("BTCUSDT", count=24, timeframe="1h")
        daily_bars = context.market_data.get_bars("BTCUSDT", count=30, timeframe="1d")
        
        # Get current market data
        current_price = context.market_data.get_current_price("BTCUSDT")
        bid, ask = context.market_data.get_bid_ask("BTCUSDT")
        
        # Check market status
        if not context.market_data.is_market_open("BTCUSDT"):
            context.log("Market is closed, skipping signals")
            return
        
        # Get order book for liquidity analysis
        orderbook = context.market_data.get_orderbook("BTCUSDT", depth=20)
        
        # Analyze market microstructure
        spread = ask - bid
        spread_pct = spread / current_price
        
        if spread_pct > 0.001:  # 0.1% spread threshold
            context.log(f"Wide spread detected: {spread_pct:.4%}")
```

## Portfolio Management

### Portfolio Class

Tracks positions, calculates performance, and manages portfolio state.

```python
class Portfolio:
    """Portfolio management interface."""
    
    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions)."""
        pass
    
    @property
    def cash_balance(self) -> float:
        """Available cash balance."""
        pass
    
    @property
    def positions_value(self) -> float:
        """Total value of all positions."""
        pass
    
    @property
    def positions(self) -> dict:
        """Dictionary of current positions by symbol."""
        pass
    
    def get_position(self, symbol: str) -> Position:
        """Get position for specific symbol."""
        pass
    
    def get_performance_metrics(self) -> dict:
        """Get portfolio performance metrics."""
        pass
    
    def get_daily_pnl(self) -> float:
        """Get today's profit/loss."""
        pass
    
    def get_unrealized_pnl(self) -> float:
        """Get unrealized profit/loss."""
        pass
    
    def get_realized_pnl(self) -> float:
        """Get realized profit/loss."""
        pass
```

### Position Class

Represents an individual position in a trading symbol.

```python
class Position:
    """Individual position in a trading symbol."""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.quantity = 0.0
        self.avg_price = 0.0
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        self.last_price = 0.0
    
    @property
    def market_value(self) -> float:
        """Current market value of position."""
        return self.quantity * self.last_price
    
    @property
    def is_long(self) -> bool:
        """True if position is long."""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """True if position is short."""
        return self.quantity < 0
    
    @property
    def is_flat(self) -> bool:
        """True if no position."""
        return self.quantity == 0
    
    def update_price(self, price: float):
        """Update position with current market price."""
        self.last_price = price
        if self.quantity != 0:
            self.unrealized_pnl = (price - self.avg_price) * self.quantity
```

### Portfolio Usage Examples

```python
class PortfolioAwareStrategy(BaseStrategy):
    def on_bar(self, context):
        # Get portfolio information
        portfolio = context.portfolio
        
        # Check cash availability
        available_cash = portfolio.cash_balance
        if available_cash < 1000:
            context.log("Insufficient cash for new positions")
            return
        
        # Check current positions
        btc_position = portfolio.get_position("BTCUSDT")
        
        if btc_position.is_flat:
            # No position, consider entry
            position_size = min(available_cash * 0.1, 5000)  # 10% of cash or $5000
            shares = position_size / context.market_data.get_current_price("BTCUSDT")
            
            context.order_manager.market_order("BTCUSDT", shares)
            
        elif btc_position.is_long:
            # Long position, check for exit
            if btc_position.unrealized_pnl < -500:  # $500 stop loss
                context.order_manager.market_order("BTCUSDT", -btc_position.quantity)
                context.log("Stop loss triggered")
        
        # Portfolio performance monitoring
        metrics = portfolio.get_performance_metrics()
        if metrics["drawdown"] > 0.1:  # 10% drawdown
            context.log("High drawdown detected, reducing risk")
            self.reduce_position_sizes(context)
    
    def reduce_position_sizes(self, context):
        """Reduce all positions by 50%."""
        for symbol, position in context.portfolio.positions.items():
            if not position.is_flat:
                reduction = -position.quantity * 0.5
                context.order_manager.market_order(symbol, reduction)
```

## Order Management

### OrderManager Class

Handles order submission, modification, and tracking.

```python
class OrderManager:
    """Order management interface."""
    
    def market_order(self, symbol: str, quantity: float, 
                    client_id: str = None) -> str:
        """
        Submit market order.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity (positive for buy, negative for sell)
            client_id: Optional client order ID
            
        Returns:
            Order ID
        """
        pass
    
    def limit_order(self, symbol: str, quantity: float, price: float,
                   client_id: str = None, time_in_force: str = "GTC") -> str:
        """Submit limit order."""
        pass
    
    def stop_order(self, symbol: str, quantity: float, stop_price: float,
                  client_id: str = None) -> str:
        """Submit stop order."""
        pass
    
    def stop_limit_order(self, symbol: str, quantity: float, 
                        stop_price: float, limit_price: float,
                        client_id: str = None) -> str:
        """Submit stop-limit order."""
        pass
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel existing order."""
        pass
    
    def cancel_all_orders(self, symbol: str = None) -> int:
        """Cancel all open orders for symbol (or all symbols)."""
        pass
    
    def get_open_orders(self, symbol: str = None) -> list:
        """Get list of open orders."""
        pass
    
    def get_order_status(self, order_id: str) -> dict:
        """Get order status and details."""
        pass
```

### Order Types and Examples

```python
class OrderStrategy(BaseStrategy):
    def on_bar(self, context):
        current_price = context.market_data.get_current_price("BTCUSDT")
        
        # Market order - immediate execution
        context.order_manager.market_order("BTCUSDT", 1.0)
        
        # Limit order - buy below current price
        buy_price = current_price * 0.99  # 1% below market
        context.order_manager.limit_order("BTCUSDT", 1.0, buy_price)
        
        # Stop loss order
        stop_price = current_price * 0.95  # 5% stop loss
        context.order_manager.stop_order("BTCUSDT", -1.0, stop_price)
        
        # Stop-limit order (more control over execution price)
        stop_price = current_price * 0.95
        limit_price = current_price * 0.94
        context.order_manager.stop_limit_order("BTCUSDT", -1.0, stop_price, limit_price)
        
        # Bracket order (entry + stop + target)
        self.submit_bracket_order(context, "BTCUSDT", 1.0, current_price, 
                                 stop_loss_pct=0.05, take_profit_pct=0.10)
    
    def submit_bracket_order(self, context, symbol, quantity, entry_price,
                           stop_loss_pct, take_profit_pct):
        """Submit bracket order with stop loss and take profit."""
        # Entry order
        entry_id = context.order_manager.limit_order(symbol, quantity, entry_price)
        
        # Stop loss
        stop_price = entry_price * (1 - stop_loss_pct)
        stop_id = context.order_manager.stop_order(symbol, -quantity, stop_price)
        
        # Take profit
        target_price = entry_price * (1 + take_profit_pct)
        target_id = context.order_manager.limit_order(symbol, -quantity, target_price)
        
        # Store order IDs for management
        context.set_variable("bracket_orders", {
            "entry": entry_id,
            "stop": stop_id,
            "target": target_id
        })
    
    def on_order_fill(self, context, order):
        """Handle order fills and manage bracket orders."""
        bracket_orders = context.get_variable("bracket_orders", {})
        
        if order.id == bracket_orders.get("entry"):
            context.log("Entry order filled, bracket active")
        elif order.id in [bracket_orders.get("stop"), bracket_orders.get("target")]:
            # One leg filled, cancel the other
            if order.id == bracket_orders.get("stop"):
                context.order_manager.cancel_order(bracket_orders.get("target"))
            else:
                context.order_manager.cancel_order(bracket_orders.get("stop"))
            context.log("Bracket order completed")
```

## Risk Management

### RiskManager Class

Provides risk controls and position sizing functionality.

```python
class RiskManager:
    """Risk management interface."""
    
    def check_order(self, symbol: str, quantity: float, price: float = None) -> dict:
        """
        Check if order passes risk controls.
        
        Returns:
            dict with 'allowed' bool and 'reason' if rejected
        """
        pass
    
    def calculate_position_size(self, symbol: str, risk_amount: float,
                              entry_price: float, stop_price: float) -> float:
        """Calculate position size based on risk amount."""
        pass
    
    def get_portfolio_risk(self) -> dict:
        """Get current portfolio risk metrics."""
        pass
    
    def get_var(self, confidence: float = 0.95, days: int = 1) -> float:
        """Calculate Value at Risk."""
        pass
    
    def get_max_position_size(self, symbol: str) -> float:
        """Get maximum allowed position size for symbol."""
        pass
```

### Risk Management Examples

```python
class RiskManagedStrategy(BaseStrategy):
    def initialize(self, context):
        # Risk parameters
        self.max_risk_per_trade = context.get_parameter("max_risk_per_trade", 0.01)  # 1%
        self.max_portfolio_risk = context.get_parameter("max_portfolio_risk", 0.02)  # 2%
        self.max_drawdown_limit = context.get_parameter("max_drawdown_limit", 0.15)  # 15%
    
    def on_bar(self, context):
        # Check portfolio risk before trading
        portfolio_risk = context.risk_manager.get_portfolio_risk()
        
        if portfolio_risk["total_risk"] > self.max_portfolio_risk:
            context.log("Portfolio risk limit exceeded, skipping trades")
            return
        
        # Check drawdown
        metrics = context.portfolio.get_performance_metrics()
        if metrics.get("drawdown", 0) > self.max_drawdown_limit:
            context.log("Maximum drawdown exceeded, halting trading")
            self.emergency_exit(context)
            return
        
        # Generate signal
        signal = self.generate_signal(context)
        if signal:
            self.execute_risk_managed_trade(context, signal)
    
    def execute_risk_managed_trade(self, context, signal):
        """Execute trade with proper risk management."""
        symbol = signal["symbol"]
        direction = signal["direction"]  # 1 for long, -1 for short
        entry_price = context.market_data.get_current_price(symbol)
        
        # Calculate stop loss
        if direction == 1:  # Long
            stop_price = entry_price * 0.98  # 2% stop loss
        else:  # Short
            stop_price = entry_price * 1.02  # 2% stop loss
        
        # Calculate position size based on risk
        portfolio_value = context.portfolio.total_value
        risk_amount = portfolio_value * self.max_risk_per_trade
        
        position_size = context.risk_manager.calculate_position_size(
            symbol, risk_amount, entry_price, stop_price
        )
        
        # Check if order passes risk controls
        risk_check = context.risk_manager.check_order(symbol, position_size, entry_price)
        
        if not risk_check["allowed"]:
            context.log(f"Order rejected by risk manager: {risk_check['reason']}")
            return
        
        # Submit order
        order_quantity = position_size * direction
        order_id = context.order_manager.market_order(symbol, order_quantity)
        
        # Submit stop loss
        stop_quantity = -order_quantity
        stop_id = context.order_manager.stop_order(symbol, stop_quantity, stop_price)
        
        context.log(f"Trade executed: {symbol} {direction} {position_size} @ {entry_price}")
        context.log(f"Stop loss set at {stop_price}")
    
    def emergency_exit(self, context):
        """Close all positions immediately."""
        for symbol, position in context.portfolio.positions.items():
            if not position.is_flat:
                exit_quantity = -position.quantity
                context.order_manager.market_order(symbol, exit_quantity)
        
        context.log("Emergency exit: All positions closed")
```

## Technical Indicators

### Built-in Indicators

The SDK provides a comprehensive library of technical indicators.

```python
from alphintra.indicators import (
    SMA, EMA, RSI, MACD, BollingerBands, ATR, 
    Stochastic, Williams, CCI, MFI, OBV
)

class IndicatorStrategy(BaseStrategy):
    def initialize(self, context):
        # Initialize indicators
        self.sma_20 = SMA(period=20)
        self.sma_50 = SMA(period=50)
        self.rsi = RSI(period=14)
        self.macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        self.bb = BollingerBands(period=20, std_dev=2)
        self.atr = ATR(period=14)
    
    def on_bar(self, context):
        # Get price data
        data = context.market_data.get_bars(count=100)
        
        # Calculate indicators
        sma_20 = self.sma_20.calculate(data.close)
        sma_50 = self.sma_50.calculate(data.close)
        rsi_value = self.rsi.calculate(data.close)
        
        # MACD returns multiple values
        macd_line, signal_line, histogram = self.macd.calculate(data.close)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.bb.calculate(data.close)
        
        # ATR for volatility
        atr_value = self.atr.calculate(data.high, data.low, data.close)
        
        # Generate signals based on multiple indicators
        signals = self.analyze_indicators(
            sma_20, sma_50, rsi_value, macd_line, signal_line,
            bb_upper, bb_lower, data.close.iloc[-1], atr_value
        )
        
        if signals["buy"]:
            context.order_manager.market_order("BTCUSDT", 1.0)
        elif signals["sell"]:
            context.order_manager.market_order("BTCUSDT", -1.0)
    
    def analyze_indicators(self, sma_20, sma_50, rsi, macd_line, signal_line,
                          bb_upper, bb_lower, price, atr):
        """Combine multiple indicators for signal generation."""
        signals = {"buy": False, "sell": False}
        
        # Trend: SMA crossover
        trend_bullish = sma_20 > sma_50
        trend_bearish = sma_20 < sma_50
        
        # Momentum: RSI
        rsi_oversold = rsi < 30
        rsi_overbought = rsi > 70
        
        # MACD momentum
        macd_bullish = macd_line > signal_line
        macd_bearish = macd_line < signal_line
        
        # Bollinger Bands mean reversion
        bb_oversold = price < bb_lower
        bb_overbought = price > bb_upper
        
        # Buy signal: Multiple confirmations
        if (trend_bullish and rsi_oversold and macd_bullish) or \
           (bb_oversold and rsi_oversold):
            signals["buy"] = True
        
        # Sell signal: Multiple confirmations
        if (trend_bearish and rsi_overbought and macd_bearish) or \
           (bb_overbought and rsi_overbought):
            signals["sell"] = True
        
        return signals
```

### Custom Indicators

You can create custom indicators by extending the base indicator class:

```python
from alphintra.indicators.base import BaseIndicator
import pandas as pd
import numpy as np

class VWAP(BaseIndicator):
    """Volume Weighted Average Price indicator."""
    
    def __init__(self, period: int = 20):
        super().__init__(period)
        self.period = period
    
    def calculate(self, high: pd.Series, low: pd.Series, 
                 close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate VWAP."""
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).rolling(self.period).sum() / \
               volume.rolling(self.period).sum()
        return vwap

class ZScore(BaseIndicator):
    """Z-Score indicator for mean reversion."""
    
    def __init__(self, period: int = 20):
        super().__init__(period)
        self.period = period
    
    def calculate(self, series: pd.Series) -> pd.Series:
        """Calculate Z-Score."""
        rolling_mean = series.rolling(self.period).mean()
        rolling_std = series.rolling(self.period).std()
        z_score = (series - rolling_mean) / rolling_std
        return z_score

# Usage in strategy
class CustomIndicatorStrategy(BaseStrategy):
    def initialize(self, context):
        self.vwap = VWAP(period=20)
        self.zscore = ZScore(period=20)
    
    def on_bar(self, context):
        data = context.market_data.get_bars(count=50)
        
        # Calculate custom indicators
        vwap_value = self.vwap.calculate(data.high, data.low, data.close, data.volume)
        zscore_value = self.zscore.calculate(data.close)
        
        current_price = data.close.iloc[-1]
        current_vwap = vwap_value.iloc[-1]
        current_zscore = zscore_value.iloc[-1]
        
        # Mean reversion signals
        if current_zscore < -2 and current_price < current_vwap:
            # Oversold and below VWAP - buy signal
            context.order_manager.market_order("BTCUSDT", 1.0)
        elif current_zscore > 2 and current_price > current_vwap:
            # Overbought and above VWAP - sell signal
            context.order_manager.market_order("BTCUSDT", -1.0)
```

## Backtesting

### BacktestRunner Class

Comprehensive backtesting engine with realistic market simulation.

```python
from alphintra import BacktestRunner, BacktestResult

class BacktestRunner:
    """Advanced backtesting engine."""
    
    def __init__(self, strategy, dataset, start_date, end_date, 
                 initial_capital=100000, commission=0.001, slippage=0.0005):
        self.strategy = strategy
        self.dataset = dataset
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
    
    def run(self) -> BacktestResult:
        """Run backtest and return results."""
        pass
    
    def run_walk_forward(self, train_period_days=252, 
                        test_period_days=63) -> BacktestResult:
        """Run walk-forward analysis."""
        pass
    
    def run_monte_carlo(self, num_simulations=1000) -> BacktestResult:
        """Run Monte Carlo simulation."""
        pass
```

### Backtest Configuration

```python
# Basic backtest
backtest = BacktestRunner(
    strategy=MyStrategy(),
    dataset="crypto_1min_2023",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=100000,
    commission=0.001,  # 0.1% commission
    slippage=0.0005    # 0.05% slippage
)

# Advanced backtest with custom settings
backtest = BacktestRunner(
    strategy=MyStrategy(),
    dataset="stocks_daily_sp500",
    start_date="2020-01-01",
    end_date="2023-12-31",
    initial_capital=1000000,
    commission=0.0005,
    slippage=0.0002,
    # Advanced settings
    benchmark="SPY",
    risk_free_rate=0.02,
    position_sizing="percent_risk",
    max_positions=10,
    margin_requirement=0.3
)

results = backtest.run()
```

### BacktestResult Analysis

```python
class BacktestResult:
    """Backtest results with comprehensive metrics."""
    
    @property
    def total_return(self) -> float:
        """Total return percentage."""
        pass
    
    @property
    def annualized_return(self) -> float:
        """Annualized return percentage."""
        pass
    
    @property
    def sharpe_ratio(self) -> float:
        """Sharpe ratio."""
        pass
    
    @property
    def max_drawdown(self) -> float:
        """Maximum drawdown percentage."""
        pass
    
    @property
    def win_rate(self) -> float:
        """Percentage of winning trades."""
        pass
    
    def plot_equity_curve(self):
        """Plot equity curve."""
        pass
    
    def plot_drawdown(self):
        """Plot drawdown chart."""
        pass
    
    def get_trade_analysis(self) -> pd.DataFrame:
        """Get detailed trade analysis."""
        pass
    
    def generate_report(self) -> str:
        """Generate comprehensive backtest report."""
        pass

# Analyze results
results = backtest.run()

print(f"Total Return: {results.total_return:.2%}")
print(f"Annualized Return: {results.annualized_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
print(f"Win Rate: {results.win_rate:.2%}")

# Generate visualizations
results.plot_equity_curve()
results.plot_drawdown()

# Get detailed trade analysis
trades = results.get_trade_analysis()
print(f"Total Trades: {len(trades)}")
print(f"Average Trade: {trades['pnl'].mean():.2f}")
print(f"Best Trade: {trades['pnl'].max():.2f}")
print(f"Worst Trade: {trades['pnl'].min():.2f}")

# Generate full report
report = results.generate_report()
print(report)
```

## Examples

### Complete Strategy Examples

#### 1. RSI Mean Reversion Strategy

```python
from alphintra import BaseStrategy
from alphintra.indicators import RSI, SMA

class RSIMeanReversionStrategy(BaseStrategy):
    """RSI-based mean reversion strategy with trend filter."""
    
    def initialize(self, context):
        # Parameters
        self.rsi_period = context.get_parameter("rsi_period", 14)
        self.rsi_oversold = context.get_parameter("rsi_oversold", 30)
        self.rsi_overbought = context.get_parameter("rsi_overbought", 70)
        self.trend_period = context.get_parameter("trend_period", 50)
        self.position_size = context.get_parameter("position_size", 0.1)
        
        # Indicators
        self.rsi = RSI(period=self.rsi_period)
        self.trend_sma = SMA(period=self.trend_period)
        
        # State
        context.set_variable("position", 0)
        context.set_variable("last_rsi", None)
        
        context.log(f"RSI Mean Reversion Strategy initialized")
        context.log(f"RSI period: {self.rsi_period}, Oversold: {self.rsi_oversold}, Overbought: {self.rsi_overbought}")
    
    def on_bar(self, context):
        # Get market data
        data = context.market_data.get_bars(count=max(self.rsi_period, self.trend_period) + 10)
        
        if len(data) < max(self.rsi_period, self.trend_period):
            return
        
        # Calculate indicators
        rsi_values = self.rsi.calculate(data.close)
        trend_values = self.trend_sma.calculate(data.close)
        
        current_rsi = rsi_values.iloc[-1]
        current_price = data.close.iloc[-1]
        trend_price = trend_values.iloc[-1]
        
        # Get current position
        position = context.get_variable("position")
        last_rsi = context.get_variable("last_rsi")
        
        # Determine trend direction
        trend_up = current_price > trend_price
        trend_down = current_price < trend_price
        
        # Generate signals
        if position == 0:  # No position
            if trend_up and current_rsi < self.rsi_oversold and (last_rsi is None or last_rsi >= current_rsi):
                # Buy signal: uptrend + oversold RSI + RSI turning up
                self.enter_long(context)
            elif trend_down and current_rsi > self.rsi_overbought and (last_rsi is None or last_rsi <= current_rsi):
                # Sell signal: downtrend + overbought RSI + RSI turning down
                self.enter_short(context)
        
        elif position > 0:  # Long position
            if current_rsi > self.rsi_overbought or not trend_up:
                # Exit long: overbought or trend changed
                self.exit_long(context)
        
        elif position < 0:  # Short position
            if current_rsi < self.rsi_oversold or not trend_down:
                # Exit short: oversold or trend changed
                self.exit_short(context)
        
        # Update state
        context.set_variable("last_rsi", current_rsi)
        
        # Record metrics
        context.record_metric("rsi", current_rsi)
        context.record_metric("trend_price", trend_price)
        context.record_metric("current_price", current_price)
    
    def enter_long(self, context):
        """Enter long position."""
        portfolio_value = context.portfolio.total_value
        position_value = portfolio_value * self.position_size
        current_price = context.market_data.get_current_price("BTCUSDT")
        quantity = position_value / current_price
        
        context.order_manager.market_order("BTCUSDT", quantity)
        context.set_variable("position", 1)
        context.log(f"Entering long position: {quantity:.4f} @ {current_price:.2f}")
    
    def enter_short(self, context):
        """Enter short position."""
        portfolio_value = context.portfolio.total_value
        position_value = portfolio_value * self.position_size
        current_price = context.market_data.get_current_price("BTCUSDT")
        quantity = position_value / current_price
        
        context.order_manager.market_order("BTCUSDT", -quantity)
        context.set_variable("position", -1)
        context.log(f"Entering short position: {quantity:.4f} @ {current_price:.2f}")
    
    def exit_long(self, context):
        """Exit long position."""
        position = context.portfolio.get_position("BTCUSDT")
        if position.quantity > 0:
            context.order_manager.market_order("BTCUSDT", -position.quantity)
            context.set_variable("position", 0)
            context.log(f"Exiting long position: {position.quantity:.4f}")
    
    def exit_short(self, context):
        """Exit short position."""
        position = context.portfolio.get_position("BTCUSDT")
        if position.quantity < 0:
            context.order_manager.market_order("BTCUSDT", -position.quantity)
            context.set_variable("position", 0)
            context.log(f"Exiting short position: {abs(position.quantity):.4f}")
    
    def on_order_fill(self, context, order):
        """Handle order fills."""
        context.log(f"Order filled: {order.symbol} {order.side} {order.quantity:.4f} @ {order.fill_price:.2f}")
        
        # Calculate and log slippage
        if hasattr(order, 'expected_price'):
            slippage = abs(order.fill_price - order.expected_price) / order.expected_price
            context.record_metric("slippage", slippage)
```

#### 2. Multi-Timeframe Momentum Strategy

```python
from alphintra import BaseStrategy
from alphintra.indicators import EMA, ATR, RSI

class MultiTimeframeMomentumStrategy(BaseStrategy):
    """Momentum strategy using multiple timeframes."""
    
    def initialize(self, context):
        # Parameters
        self.fast_ema = context.get_parameter("fast_ema", 12)
        self.slow_ema = context.get_parameter("slow_ema", 26)
        self.atr_period = context.get_parameter("atr_period", 14)
        self.rsi_period = context.get_parameter("rsi_period", 14)
        self.risk_pct = context.get_parameter("risk_pct", 0.02)
        
        # Indicators for different timeframes
        self.indicators = {
            "1m": {
                "fast_ema": EMA(period=self.fast_ema),
                "slow_ema": EMA(period=self.slow_ema),
                "atr": ATR(period=self.atr_period)
            },
            "5m": {
                "fast_ema": EMA(period=self.fast_ema),
                "slow_ema": EMA(period=self.slow_ema),
                "rsi": RSI(period=self.rsi_period)
            },
            "1h": {
                "trend_ema": EMA(period=50)
            }
        }
        
        context.set_variable("position", 0)
        context.log("Multi-timeframe momentum strategy initialized")
    
    def on_bar(self, context):
        # Get data for multiple timeframes
        data_1m = context.market_data.get_bars(count=100, timeframe="1m")
        data_5m = context.market_data.get_bars(count=100, timeframe="5m")
        data_1h = context.market_data.get_bars(count=100, timeframe="1h")
        
        if len(data_1m) < 50 or len(data_5m) < 50 or len(data_1h) < 50:
            return
        
        # Calculate indicators for each timeframe
        signals_1m = self.analyze_1m_timeframe(data_1m)
        signals_5m = self.analyze_5m_timeframe(data_5m)
        signals_1h = self.analyze_1h_timeframe(data_1h)
        
        # Combine signals
        combined_signal = self.combine_signals(signals_1m, signals_5m, signals_1h)
        
        # Execute trades based on combined signal
        self.execute_signal(context, combined_signal, data_1m)
    
    def analyze_1m_timeframe(self, data):
        """Analyze 1-minute timeframe for entry/exit signals."""
        fast_ema = self.indicators["1m"]["fast_ema"].calculate(data.close)
        slow_ema = self.indicators["1m"]["slow_ema"].calculate(data.close)
        atr = self.indicators["1m"]["atr"].calculate(data.high, data.low, data.close)
        
        # EMA crossover
        ema_bullish = fast_ema.iloc[-1] > slow_ema.iloc[-1]
        ema_bearish = fast_ema.iloc[-1] < slow_ema.iloc[-1]
        
        # Recent crossover
        recent_cross_up = (fast_ema.iloc[-1] > slow_ema.iloc[-1] and 
                          fast_ema.iloc[-2] <= slow_ema.iloc[-2])
        recent_cross_down = (fast_ema.iloc[-1] < slow_ema.iloc[-1] and 
                            fast_ema.iloc[-2] >= slow_ema.iloc[-2])
        
        return {
            "trend": "bullish" if ema_bullish else "bearish",
            "entry_signal": recent_cross_up,
            "exit_signal": recent_cross_down,
            "atr": atr.iloc[-1]
        }
    
    def analyze_5m_timeframe(self, data):
        """Analyze 5-minute timeframe for momentum confirmation."""
        fast_ema = self.indicators["5m"]["fast_ema"].calculate(data.close)
        slow_ema = self.indicators["5m"]["slow_ema"].calculate(data.close)
        rsi = self.indicators["5m"]["rsi"].calculate(data.close)
        
        momentum_bullish = (fast_ema.iloc[-1] > slow_ema.iloc[-1] and 
                           rsi.iloc[-1] > 50 and rsi.iloc[-1] < 80)
        momentum_bearish = (fast_ema.iloc[-1] < slow_ema.iloc[-1] and 
                           rsi.iloc[-1] < 50 and rsi.iloc[-1] > 20)
        
        return {
            "momentum": "bullish" if momentum_bullish else "bearish" if momentum_bearish else "neutral",
            "rsi": rsi.iloc[-1]
        }
    
    def analyze_1h_timeframe(self, data):
        """Analyze 1-hour timeframe for overall trend."""
        trend_ema = self.indicators["1h"]["trend_ema"].calculate(data.close)
        current_price = data.close.iloc[-1]
        
        trend_bullish = current_price > trend_ema.iloc[-1]
        
        return {
            "long_term_trend": "bullish" if trend_bullish else "bearish"
        }
    
    def combine_signals(self, signals_1m, signals_5m, signals_1h):
        """Combine signals from multiple timeframes."""
        # Buy signal: all timeframes align bullish
        buy_signal = (signals_1m["entry_signal"] and 
                     signals_1m["trend"] == "bullish" and
                     signals_5m["momentum"] == "bullish" and
                     signals_1h["long_term_trend"] == "bullish")
        
        # Sell signal: trend changes or momentum weakens
        sell_signal = (signals_1m["exit_signal"] or 
                      signals_5m["momentum"] == "bearish" or
                      signals_1h["long_term_trend"] == "bearish")
        
        return {
            "action": "buy" if buy_signal else "sell" if sell_signal else "hold",
            "confidence": self.calculate_confidence(signals_1m, signals_5m, signals_1h),
            "atr": signals_1m["atr"]
        }
    
    def calculate_confidence(self, signals_1m, signals_5m, signals_1h):
        """Calculate signal confidence based on alignment."""
        score = 0
        
        # Trend alignment
        if signals_1m["trend"] == signals_1h["long_term_trend"]:
            score += 1
        
        # Momentum confirmation
        if signals_5m["momentum"] != "neutral":
            score += 1
        
        # RSI in good range
        rsi = signals_5m["rsi"]
        if 30 < rsi < 70:
            score += 1
        
        return score / 3  # Normalize to 0-1
    
    def execute_signal(self, context, signal, data):
        """Execute trading signal."""
        position = context.get_variable("position")
        current_price = data.close.iloc[-1]
        
        if signal["action"] == "buy" and position <= 0 and signal["confidence"] > 0.7:
            # Calculate position size based on ATR and risk
            portfolio_value = context.portfolio.total_value
            risk_amount = portfolio_value * self.risk_pct
            
            # Use ATR for stop loss
            stop_distance = signal["atr"] * 2  # 2x ATR stop
            position_size = risk_amount / stop_distance
            
            # Limit position size
            max_position_value = portfolio_value * 0.2  # 20% max
            max_position_size = max_position_value / current_price
            position_size = min(position_size, max_position_size)
            
            context.order_manager.market_order("BTCUSDT", position_size)
            context.set_variable("position", 1)
            
            # Set stop loss
            stop_price = current_price - stop_distance
            context.order_manager.stop_order("BTCUSDT", -position_size, stop_price)
            
            context.log(f"Buy signal executed: {position_size:.4f} @ {current_price:.2f}")
            context.log(f"Stop loss set at {stop_price:.2f}")
        
        elif signal["action"] == "sell" and position > 0:
            # Close position
            btc_position = context.portfolio.get_position("BTCUSDT")
            if btc_position.quantity > 0:
                context.order_manager.market_order("BTCUSDT", -btc_position.quantity)
                context.set_variable("position", 0)
                context.log(f"Position closed: {btc_position.quantity:.4f}")
        
        # Record metrics
        context.record_metric("signal_confidence", signal["confidence"])
        context.record_metric("atr", signal["atr"])
```

## Best Practices

### 1. Strategy Design Principles

- **Keep it Simple**: Start with simple strategies and add complexity gradually
- **Parameter Validation**: Always validate input parameters in `initialize()`
- **State Management**: Use context variables for strategy state, not class attributes
- **Error Handling**: Implement robust error handling for market data and execution issues
- **Logging**: Use structured logging for debugging and monitoring

### 2. Risk Management

- **Position Sizing**: Always calculate position sizes based on risk, not arbitrary amounts
- **Stop Losses**: Implement stop losses for every position
- **Portfolio Risk**: Monitor overall portfolio risk, not just individual positions
- **Drawdown Limits**: Set maximum drawdown limits and halt trading when exceeded

### 3. Performance Optimization

- **Data Efficiency**: Only request the data you need
- **Indicator Caching**: Reuse indicator calculations when possible
- **Vectorized Operations**: Use pandas vectorized operations for calculations
- **Memory Management**: Clean up large datasets when no longer needed

### 4. Testing and Validation

- **Out-of-Sample Testing**: Always test on unseen data
- **Walk-Forward Analysis**: Use walk-forward testing for realistic results
- **Multiple Markets**: Test strategies across different market conditions
- **Statistical Significance**: Ensure sufficient trade count for meaningful results

### 5. Code Organization

```python
class WellStructuredStrategy(BaseStrategy):
    """Example of well-structured strategy code."""
    
    def __init__(self):
        # Initialize indicators and state in __init__ if needed
        self.indicators_initialized = False
    
    def initialize(self, context):
        """Initialize strategy with proper validation."""
        # Validate required parameters
        required_params = ["symbol", "lookback_period"]
        for param in required_params:
            if context.get_parameter(param) is None:
                raise ValueError(f"Required parameter '{param}' not provided")
        
        # Initialize indicators
        self._initialize_indicators(context)
        
        # Initialize state
        self._initialize_state(context)
        
        # Log configuration
        self._log_configuration(context)
    
    def _initialize_indicators(self, context):
        """Initialize technical indicators."""
        period = context.get_parameter("lookback_period", 20)
        self.sma = SMA(period=period)
        self.rsi = RSI(period=14)
        self.indicators_initialized = True
    
    def _initialize_state(self, context):
        """Initialize strategy state variables."""
        context.set_variable("position", 0)
        context.set_variable("last_signal_time", None)
        context.set_variable("trade_count", 0)
    
    def _log_configuration(self, context):
        """Log strategy configuration."""
        symbol = context.get_parameter("symbol")
        lookback = context.get_parameter("lookback_period")
        context.log(f"Strategy initialized for {symbol} with {lookback}-period lookback")
    
    def on_bar(self, context):
        """Main strategy logic with error handling."""
        try:
            if not self._validate_market_conditions(context):
                return
            
            signal = self._generate_signal(context)
            if signal:
                self._execute_signal(context, signal)
                
        except Exception as e:
            context.log(f"Error in on_bar: {str(e)}", level="ERROR")
            self._handle_strategy_error(context, e)
    
    def _validate_market_conditions(self, context):
        """Validate market conditions before trading."""
        # Check market hours
        if not context.market_data.is_market_open():
            return False
        
        # Check data availability
        data = context.market_data.get_bars(count=50)
        if len(data) < 20:
            context.log("Insufficient data for analysis")
            return False
        
        return True
    
    def _generate_signal(self, context):
        """Generate trading signal based on indicators."""
        data = context.market_data.get_bars(count=50)
        
        # Calculate indicators
        sma_values = self.sma.calculate(data.close)
        rsi_values = self.rsi.calculate(data.close)
        
        # Signal logic
        current_price = data.close.iloc[-1]
        current_sma = sma_values.iloc[-1]
        current_rsi = rsi_values.iloc[-1]
        
        if current_price > current_sma and current_rsi < 70:
            return {"action": "buy", "confidence": 0.8}
        elif current_price < current_sma and current_rsi > 30:
            return {"action": "sell", "confidence": 0.8}
        
        return None
    
    def _execute_signal(self, context, signal):
        """Execute trading signal with risk management."""
        # Implementation details...
        pass
    
    def _handle_strategy_error(self, context, error):
        """Handle strategy errors gracefully."""
        # Log error
        context.log(f"Strategy error: {str(error)}", level="ERROR")
        
        # Implement recovery logic
        if isinstance(error, DataError):
            context.log("Data error detected, skipping this bar")
        else:
            # More serious error - consider stopping strategy
            context.log("Serious error detected, consider manual intervention")
```

This comprehensive SDK documentation provides developers with everything they need to build sophisticated trading strategies using the Alphintra platform. The examples demonstrate real-world usage patterns and best practices for robust strategy development.