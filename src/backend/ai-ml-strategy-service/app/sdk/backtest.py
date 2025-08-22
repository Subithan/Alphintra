"""
Backtesting framework for strategy validation.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Callable
from decimal import Decimal
import logging
from dataclasses import dataclass

from app.sdk.strategy import BaseStrategy, StrategyContext
from app.sdk.data import MarketData
from app.sdk.portfolio import Portfolio
from app.sdk.orders import OrderManager
from app.sdk.risk import RiskManager


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal = Decimal("100000")
    commission: Decimal = Decimal("0.001")      # 0.1%
    slippage: Decimal = Decimal("0.0005")       # 0.05%
    symbols: List[str] = None
    timeframe: str = "1d"
    benchmark_symbol: str = "SPY"
    
    # Risk management
    max_leverage: float = 1.0
    max_position_size: float = 0.20             # 20% max position
    
    # Advanced settings
    market_impact: bool = False
    realistic_fills: bool = True
    partial_fills: bool = False


class BacktestResult:
    """Comprehensive backtest results and analytics."""
    
    def __init__(self):
        # Basic metrics
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.duration_days: int = 0
        
        # Performance metrics
        self.initial_capital: Decimal = Decimal("0")
        self.final_capital: Decimal = Decimal("0")
        self.total_return: Decimal = Decimal("0")
        self.annualized_return: Decimal = Decimal("0")
        self.volatility: Decimal = Decimal("0")
        
        # Risk metrics
        self.max_drawdown: Decimal = Decimal("0")
        self.sharpe_ratio: float = 0.0
        self.sortino_ratio: float = 0.0
        self.calmar_ratio: float = 0.0
        
        # Trading metrics
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.losing_trades: int = 0
        self.win_rate: float = 0.0
        self.profit_factor: float = 0.0
        self.avg_win: Decimal = Decimal("0")
        self.avg_loss: Decimal = Decimal("0")
        self.largest_win: Decimal = Decimal("0")
        self.largest_loss: Decimal = Decimal("0")
        
        # Detailed data
        self.equity_curve: List[Dict] = []
        self.trades: List[Dict] = []
        self.daily_returns: List[float] = []
        self.monthly_returns: List[float] = []
        
        # Benchmark comparison
        self.benchmark_return: Decimal = Decimal("0")
        self.alpha: float = 0.0
        self.beta: float = 0.0
        self.correlation: float = 0.0
        
        # Execution stats
        self.execution_time: float = 0.0
        self.bars_processed: int = 0
        
    def calculate_metrics(self):
        """Calculate derived metrics from basic data."""
        if self.initial_capital > 0:
            self.total_return = ((self.final_capital - self.initial_capital) / 
                               self.initial_capital) * Decimal("100")
        
        # Annualized return
        if self.duration_days > 0:
            years = self.duration_days / 365.25
            if years > 0:
                total_return_ratio = float(self.total_return) / 100.0
                self.annualized_return = Decimal(str(
                    ((1 + total_return_ratio) ** (1/years) - 1) * 100
                ))
        
        # Trading metrics
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        # Volatility from daily returns
        if len(self.daily_returns) > 1:
            mean_return = sum(self.daily_returns) / len(self.daily_returns)
            variance = sum((r - mean_return) ** 2 for r in self.daily_returns) / (len(self.daily_returns) - 1)
            daily_vol = variance ** 0.5
            self.volatility = Decimal(str(daily_vol * (252 ** 0.5) * 100))  # Annualized volatility
        
        # Sharpe ratio
        if self.volatility > 0:
            excess_return = float(self.annualized_return) - 2.0  # Assume 2% risk-free rate
            self.sharpe_ratio = excess_return / float(self.volatility)
        
        # Calmar ratio
        if self.max_drawdown > 0:
            self.calmar_ratio = float(self.annualized_return) / float(self.max_drawdown)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary."""
        return {
            "period": {
                "start_date": self.start_date.isoformat() if self.start_date else None,
                "end_date": self.end_date.isoformat() if self.end_date else None,
                "duration_days": self.duration_days
            },
            "performance": {
                "initial_capital": float(self.initial_capital),
                "final_capital": float(self.final_capital),
                "total_return": float(self.total_return),
                "annualized_return": float(self.annualized_return),
                "volatility": float(self.volatility),
                "max_drawdown": float(self.max_drawdown),
                "sharpe_ratio": self.sharpe_ratio,
                "sortino_ratio": self.sortino_ratio,
                "calmar_ratio": self.calmar_ratio
            },
            "trading": {
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "win_rate": self.win_rate,
                "profit_factor": self.profit_factor,
                "avg_win": float(self.avg_win),
                "avg_loss": float(self.avg_loss),
                "largest_win": float(self.largest_win),
                "largest_loss": float(self.largest_loss)
            },
            "benchmark": {
                "benchmark_return": float(self.benchmark_return),
                "alpha": self.alpha,
                "beta": self.beta,
                "correlation": self.correlation
            },
            "execution": {
                "execution_time": self.execution_time,
                "bars_processed": self.bars_processed
            }
        }


class BacktestRunner:
    """Runs backtests for trading strategies."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Event callbacks
        self.on_bar: Optional[Callable] = None
        self.on_trade: Optional[Callable] = None
        self.on_order: Optional[Callable] = None
        
        # Progress tracking
        self.progress_callback: Optional[Callable] = None
        
    def run_backtest(self, strategy: BaseStrategy, config: BacktestConfig) -> BacktestResult:
        """
        Run a comprehensive backtest.
        
        Args:
            strategy: Strategy to test
            config: Backtest configuration
            
        Returns:
            BacktestResult with comprehensive metrics
        """
        start_time = datetime.now()
        self.logger.info(f"Starting backtest: {strategy.name}")
        
        # Initialize result
        result = BacktestResult()
        result.start_date = config.start_date
        result.end_date = config.end_date
        result.duration_days = (config.end_date - config.start_date).days
        result.initial_capital = config.initial_capital
        
        try:
            # Setup components
            market_data = MarketData()
            portfolio = Portfolio(config.initial_capital)
            order_manager = OrderManager(portfolio)
            risk_manager = RiskManager(portfolio)
            
            # Configure risk limits
            risk_manager.set_risk_limit("max_position_size", config.max_position_size)
            risk_manager.set_risk_limit("max_leverage", config.max_leverage)
            
            # Create strategy context
            context = StrategyContext(
                market_data=market_data,
                portfolio=portfolio,
                order_manager=order_manager,
                risk_manager=risk_manager,
                strategy_id=f"backtest_{strategy.name}",
                user_id="backtest_user",
                parameters=getattr(strategy, 'parameters', {})
            )
            
            # Set strategy context
            strategy.set_context(context)
            
            # Load market data
            symbols = config.symbols or ["BTCUSD"]  # Default symbol
            for symbol in symbols:
                market_data.load_data(symbol, config.start_date, config.end_date, config.timeframe)
            
            # Initialize strategy
            if not strategy.is_initialized:
                strategy.initialize()
                strategy.is_initialized = True
            
            # Run backtest simulation
            self._run_simulation(strategy, context, config, result)
            
            # Finalize strategy
            strategy.finalize()
            
            # Calculate final metrics
            result.final_capital = portfolio.total_value
            result.total_trades = portfolio.total_trades
            result.winning_trades = portfolio.winning_trades
            result.losing_trades = portfolio.losing_trades
            
            # Get portfolio performance
            portfolio_stats = portfolio.get_performance_stats()
            result.max_drawdown = Decimal(str(portfolio_stats["max_drawdown"]))
            
            # Calculate additional metrics
            result.calculate_metrics()
            
            # Execution stats
            result.execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Backtest completed: {result.total_return:.2f}% return, "
                           f"{result.total_trades} trades, {result.win_rate:.1f}% win rate")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}")
            result.execution_time = (datetime.now() - start_time).total_seconds()
            raise
    
    def _run_simulation(self, strategy: BaseStrategy, context: StrategyContext, 
                       config: BacktestConfig, result: BacktestResult):
        """Run the main backtest simulation loop."""
        
        # Get data for primary symbol
        primary_symbol = config.symbols[0] if config.symbols else "BTCUSD"
        data = context.market_data._data_cache.get(f"{primary_symbol},{config.timeframe}")
        
        if data is None or data.empty:
            raise ValueError(f"No data available for {primary_symbol}")
        
        total_bars = len(data)
        result.bars_processed = total_bars
        
        # Simulation loop
        for i, (timestamp, row) in enumerate(data.iterrows()):
            # Update context
            context.current_time = timestamp
            context.current_bar = row.to_dict()
            context.bar_count = i
            
            # Update market data indices
            for symbol in config.symbols or [primary_symbol]:
                cache_key = f"{symbol},{config.timeframe}"
                if cache_key in context.market_data._current_bar_index:
                    context.market_data._current_bar_index[cache_key] = i
            
            # Process market updates for order manager
            current_price = Decimal(str(row['close']))
            context.order_manager.process_market_update(primary_symbol, current_price, timestamp)
            
            # Execute strategy logic
            try:
                strategy.on_bar()
            except Exception as e:
                self.logger.error(f"Strategy error at bar {i}: {str(e)}")
                continue
            
            # Record portfolio value
            portfolio_value = float(context.portfolio.total_value)
            context.portfolio.record_value(timestamp)
            
            # Update equity curve
            if i == 0:
                daily_return = 0.0
            else:
                prev_value = result.equity_curve[-1]["value"] if result.equity_curve else float(config.initial_capital)
                daily_return = (portfolio_value - prev_value) / prev_value if prev_value > 0 else 0.0
                result.daily_returns.append(daily_return)
            
            result.equity_curve.append({
                "timestamp": timestamp,
                "value": portfolio_value,
                "cash": float(context.portfolio.cash_balance),
                "positions": float(context.portfolio.positions_value),
                "daily_return": daily_return,
                "drawdown": float(context.portfolio.calculate_drawdown())
            })
            
            # Check risk limits
            risk_violations = context.risk_manager.check_portfolio_risk()
            if risk_violations:
                for violation in risk_violations:
                    self.logger.warning(f"Risk violation: {violation.message}")
            
            # Progress callback
            if self.progress_callback and i % 100 == 0:
                progress = (i / total_bars) * 100
                self.progress_callback(progress, i, total_bars)
            
            # Event callbacks
            if self.on_bar:
                self.on_bar(timestamp, row, context)
        
        # Record final trades
        for order in context.order_manager.orders.values():
            if order.is_filled():
                trade_record = {
                    "timestamp": order.filled_at.isoformat() if order.filled_at else timestamp.isoformat(),
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "quantity": float(order.quantity),
                    "price": float(order.avg_fill_price),
                    "commission": float(order.commission),
                    "strategy_id": order.strategy_id
                }
                result.trades.append(trade_record)
    
    def run_walk_forward_analysis(self, strategy: BaseStrategy, config: BacktestConfig,
                                 training_months: int = 12, testing_months: int = 3,
                                 step_months: int = 1) -> Dict[str, Any]:
        """
        Run walk-forward analysis for strategy robustness testing.
        
        Args:
            strategy: Strategy to test
            config: Base backtest configuration
            training_months: Months of data for training
            testing_months: Months of data for testing
            step_months: Step size between tests
            
        Returns:
            Walk-forward analysis results
        """
        self.logger.info("Starting walk-forward analysis")
        
        results = []
        current_date = config.start_date
        
        while current_date + timedelta(days=30 * (training_months + testing_months)) <= config.end_date:
            # Define training and testing periods
            training_start = current_date
            training_end = current_date + timedelta(days=30 * training_months)
            testing_start = training_end
            testing_end = testing_start + timedelta(days=30 * testing_months)
            
            # Run training period (optimization would happen here)
            training_config = BacktestConfig(
                start_date=training_start,
                end_date=training_end,
                initial_capital=config.initial_capital,
                commission=config.commission,
                slippage=config.slippage,
                symbols=config.symbols,
                timeframe=config.timeframe
            )
            
            # Run testing period
            testing_config = BacktestConfig(
                start_date=testing_start,
                end_date=testing_end,
                initial_capital=config.initial_capital,
                commission=config.commission,
                slippage=config.slippage,
                symbols=config.symbols,
                timeframe=config.timeframe
            )
            
            try:
                # For now, just run the test period (training optimization would be added)
                test_result = self.run_backtest(strategy, testing_config)
                
                results.append({
                    "training_period": {
                        "start": training_start.isoformat(),
                        "end": training_end.isoformat()
                    },
                    "testing_period": {
                        "start": testing_start.isoformat(),
                        "end": testing_end.isoformat()
                    },
                    "test_result": test_result.to_dict()
                })
                
            except Exception as e:
                self.logger.error(f"Walk-forward window failed: {str(e)}")
                results.append({
                    "training_period": {
                        "start": training_start.isoformat(),
                        "end": training_end.isoformat()
                    },
                    "testing_period": {
                        "start": testing_start.isoformat(),
                        "end": testing_end.isoformat()
                    },
                    "error": str(e)
                })
            
            # Move to next window
            current_date += timedelta(days=30 * step_months)
        
        # Calculate walk-forward metrics
        successful_tests = [r for r in results if "test_result" in r]
        
        if successful_tests:
            returns = [r["test_result"]["performance"]["total_return"] for r in successful_tests]
            avg_return = sum(returns) / len(returns)
            return_std = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
        else:
            avg_return = return_std = win_rate = 0.0
        
        return {
            "summary": {
                "total_windows": len(results),
                "successful_windows": len(successful_tests),
                "average_return": avg_return,
                "return_volatility": return_std,
                "win_rate": win_rate
            },
            "windows": results
        }
    
    def compare_strategies(self, strategies: List[BaseStrategy], config: BacktestConfig) -> Dict[str, Any]:
        """
        Compare multiple strategies on the same data.
        
        Args:
            strategies: List of strategies to compare
            config: Backtest configuration
            
        Returns:
            Comparison results
        """
        self.logger.info(f"Comparing {len(strategies)} strategies")
        
        results = {}
        
        for strategy in strategies:
            try:
                result = self.run_backtest(strategy, config)
                results[strategy.name] = result.to_dict()
            except Exception as e:
                self.logger.error(f"Strategy {strategy.name} failed: {str(e)}")
                results[strategy.name] = {"error": str(e)}
        
        # Create comparison summary
        successful_results = {name: result for name, result in results.items() if "error" not in result}
        
        if successful_results:
            # Rank by total return
            ranking = sorted(
                successful_results.items(),
                key=lambda x: x[1]["performance"]["total_return"],
                reverse=True
            )
            
            comparison_summary = {
                "best_return": ranking[0][0] if ranking else None,
                "best_sharpe": max(
                    successful_results.items(),
                    key=lambda x: x[1]["performance"]["sharpe_ratio"]
                )[0] if successful_results else None,
                "lowest_drawdown": min(
                    successful_results.items(),
                    key=lambda x: x[1]["performance"]["max_drawdown"]
                )[0] if successful_results else None,
                "ranking": [{"strategy": name, "return": result["performance"]["total_return"]}
                           for name, result in ranking]
            }
        else:
            comparison_summary = {"error": "No strategies completed successfully"}
        
        return {
            "summary": comparison_summary,
            "results": results
        }