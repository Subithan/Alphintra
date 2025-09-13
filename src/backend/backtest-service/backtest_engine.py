#!/usr/bin/env python3
"""
Backtest Engine for Trading Strategy Microservice

Standalone backtest engine that executes strategy code and returns performance metrics.
"""

import uuid
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import warnings
import tempfile
import os
import sys
warnings.filterwarnings('ignore')


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    commission: float = 0.001
    symbols: List[str] = None
    timeframe: str = "1h"
    slippage: float = 0.0001
    max_positions: int = 1


@dataclass
class Trade:
    """Represents a single trade in the backtest."""
    timestamp: datetime
    symbol: str
    action: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    commission: float
    total_cost: float


@dataclass
class PerformanceMetrics:
    """Performance metrics for backtest results."""
    total_return: float
    total_return_percent: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    calmar_ratio: float
    sortino_ratio: float
    final_capital: float
    equity_curve: List[float]
    daily_returns: List[float]


class MarketDataProvider:
    """Provides historical market data for backtesting."""
    
    def __init__(self):
        self.data_cache = {}
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, timeframe: str = "1h") -> pd.DataFrame:
        """Get historical market data."""
        cache_key = f"{symbol}_{start_date}_{end_date}_{timeframe}"
        
        if cache_key in self.data_cache:
            return self.data_cache[cache_key].copy()
        
        # Generate synthetic data for demo
        data = self._generate_synthetic_data(symbol, start_date, end_date, timeframe)
        self.data_cache[cache_key] = data
        return data.copy()
    
    def _generate_synthetic_data(self, symbol: str, start_date: str, end_date: str, timeframe: str) -> pd.DataFrame:
        """Generate synthetic market data for testing."""
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        freq_map = {
            '1m': '1T', '5m': '5T', '15m': '15T',
            '1h': '1H', '4h': '4H', '1d': '1D'
        }
        freq = freq_map.get(timeframe, '1H')
        
        dates = pd.date_range(start=start, end=end, freq=freq)
        
        # Generate realistic price data
        np.random.seed(hash(symbol) % 2**32)
        initial_price = 100.0 if 'BTC' not in symbol else 45000.0
        returns = np.random.normal(0.0001, 0.02, len(dates))
        
        prices = [initial_price]
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        prices = np.array(prices[1:])
        
        # Add intraday variation
        high_mult = 1 + np.abs(np.random.normal(0, 0.005, len(prices)))
        low_mult = 1 - np.abs(np.random.normal(0, 0.005, len(prices)))
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * high_mult,
            'low': prices * low_mult, 
            'close': prices,
            'volume': np.random.randint(1000, 100000, len(prices))
        })
        
        # Ensure OHLC relationships
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        data.set_index('timestamp', inplace=True)
        return data


class StrategyExecutor:
    """Executes strategy code with market data."""
    
    def __init__(self, strategy_code: str, config: BacktestConfig):
        self.strategy_code = strategy_code
        self.config = config
        self.trades = []
        self.positions = {}
        self.capital = config.initial_capital
        
    def execute_strategy(self, market_data: pd.DataFrame) -> Tuple[List[Trade], PerformanceMetrics]:
        """Execute strategy against market data."""
        
        # Create execution environment
        exec_globals = {
            'pd': pd,
            'np': np,
            'data': market_data,
            'trades': self.trades,
            'capital': self.capital,
            'positions': self.positions,
            'config': self.config,
            'datetime': datetime,
            'warnings': warnings,
            'ta': self._mock_talib(),
            'math': __import__('math'),
        }
        
        try:
            # Execute strategy code
            exec(self.strategy_code, exec_globals)
            
            # Extract results
            self.trades = exec_globals.get('trades', [])
            self.capital = exec_globals.get('capital', self.config.initial_capital)
            
            # Calculate performance
            performance = self._calculate_performance_metrics(market_data)
            return self.trades, performance
            
        except Exception as e:
            print(f"Strategy execution failed: {e}")
            return [], self._empty_performance_metrics()
    
    def _mock_talib(self):
        """Mock talib for demo."""
        class MockTalib:
            @staticmethod
            def SMA(prices, timeperiod=14):
                return pd.Series(prices).rolling(window=timeperiod).mean()
            
            @staticmethod
            def EMA(prices, timeperiod=14):
                return pd.Series(prices).ewm(span=timeperiod).mean()
            
            @staticmethod
            def RSI(prices, timeperiod=14):
                delta = pd.Series(prices).diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=timeperiod).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=timeperiod).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))
        
        return MockTalib()
    
    def _calculate_performance_metrics(self, market_data: pd.DataFrame) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        
        if not self.trades:
            return self._empty_performance_metrics()
        
        # Calculate equity curve
        equity_curve = [self.config.initial_capital]
        running_capital = self.config.initial_capital
        
        for trade in self.trades:
            if isinstance(trade, dict):
                action = trade.get('action')
                total_cost = trade.get('total_cost', 0)
            else:
                action = trade.action
                total_cost = trade.total_cost
                
            if action == 'BUY':
                running_capital -= total_cost
            else:  # SELL
                running_capital += total_cost
            equity_curve.append(running_capital)
        
        equity_series = pd.Series(equity_curve)
        returns = equity_series.pct_change().dropna()
        
        # Basic metrics
        total_return = self.capital - self.config.initial_capital
        total_return_percent = (total_return / self.config.initial_capital) * 100
        
        # Risk metrics
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        max_drawdown, max_drawdown_percent = self._calculate_max_drawdown(equity_series)
        sortino_ratio = self._calculate_sortino_ratio(returns)
        
        # Trade analysis
        trade_returns = []
        for trade in self.trades:
            if isinstance(trade, dict):
                if trade.get('action') == 'SELL':
                    trade_returns.append(trade.get('total_cost', 0))
            else:
                if trade.action == 'SELL':
                    trade_returns.append(trade.total_cost)
        
        winning_trades = len([r for r in trade_returns if r > 0])
        losing_trades = len([r for r in trade_returns if r < 0])
        win_rate = (winning_trades / len(trade_returns)) * 100 if trade_returns else 0
        
        wins = [r for r in trade_returns if r > 0]
        losses = [abs(r) for r in trade_returns if r < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        profit_factor = sum(wins) / sum(losses) if losses else float('inf')
        
        calmar_ratio = (total_return_percent / abs(max_drawdown_percent)) if max_drawdown_percent != 0 else 0
        
        return PerformanceMetrics(
            total_return=total_return,
            total_return_percent=total_return_percent,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            total_trades=len(self.trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            final_capital=self.capital,
            equity_curve=equity_curve,
            daily_returns=returns.tolist()
        )
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        if returns.std() == 0:
            return 0
        excess_returns = returns - (risk_free_rate / 252)
        return (excess_returns.mean() / returns.std()) * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio."""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0
        excess_returns = returns - (risk_free_rate / 252)
        return (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)
    
    def _calculate_max_drawdown(self, equity_series: pd.Series) -> Tuple[float, float]:
        """Calculate maximum drawdown."""
        peak = equity_series.cummax()
        drawdown = equity_series - peak
        max_drawdown_value = drawdown.min()
        max_drawdown_percent = (max_drawdown_value / peak.max()) * 100
        return max_drawdown_value, max_drawdown_percent
    
    def _empty_performance_metrics(self) -> PerformanceMetrics:
        """Return empty performance metrics."""
        return PerformanceMetrics(
            total_return=0.0, total_return_percent=0.0, sharpe_ratio=0.0,
            max_drawdown=0.0, max_drawdown_percent=0.0, total_trades=0,
            winning_trades=0, losing_trades=0, win_rate=0.0, avg_win=0.0,
            avg_loss=0.0, profit_factor=0.0, calmar_ratio=0.0, sortino_ratio=0.0,
            final_capital=self.config.initial_capital, equity_curve=[self.config.initial_capital],
            daily_returns=[]
        )


class BacktestEngine:
    """Main backtest engine for the microservice."""
    
    def __init__(self):
        self.market_data_provider = MarketDataProvider()
    
    def run_backtest_from_code(
        self, 
        strategy_code: str, 
        config: BacktestConfig,
        workflow_id: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run backtest from strategy code.
        
        Args:
            strategy_code: Python strategy code to execute
            config: Backtest configuration
            workflow_id: ID of the workflow that generated the strategy
            metadata: Additional metadata
            
        Returns:
            Dictionary with backtest results
        """
        
        execution_id = str(uuid.uuid4())
        
        try:
            # Get market data
            symbols = config.symbols or ['AAPL']
            market_data = self.market_data_provider.get_historical_data(
                symbol=symbols[0],
                start_date=config.start_date,
                end_date=config.end_date,
                timeframe=config.timeframe
            )
            
            if market_data.empty:
                return {
                    'success': False,
                    'execution_id': execution_id,
                    'error': 'No market data available for specified period'
                }
            
            # Execute strategy
            executor = StrategyExecutor(strategy_code, config)
            trades, performance = executor.execute_strategy(market_data)
            
            # Format results
            return {
                'success': True,
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'performance_metrics': {
                    'total_return': performance.total_return,
                    'total_return_percent': performance.total_return_percent,
                    'sharpe_ratio': performance.sharpe_ratio,
                    'max_drawdown_percent': performance.max_drawdown_percent,
                    'total_trades': performance.total_trades,
                    'win_rate': performance.win_rate,
                    'profit_factor': performance.profit_factor,
                    'final_capital': performance.final_capital,
                    'calmar_ratio': performance.calmar_ratio,
                    'sortino_ratio': performance.sortino_ratio
                },
                'trade_summary': {
                    'total_trades': len(trades),
                    'winning_trades': performance.winning_trades,
                    'losing_trades': performance.losing_trades,
                    'avg_win': performance.avg_win,
                    'avg_loss': performance.avg_loss
                },
                'market_data_stats': {
                    'data_points': len(market_data),
                    'date_range': f"{market_data.index[0]} to {market_data.index[-1]}",
                    'price_range': f"{market_data['close'].min():.2f} - {market_data['close'].max():.2f}",
                    'symbol': symbols[0],
                    'timeframe': config.timeframe
                },
                'execution_config': {
                    'start_date': config.start_date,
                    'end_date': config.end_date,
                    'initial_capital': config.initial_capital,
                    'commission': config.commission,
                    'symbols': symbols,
                    'timeframe': config.timeframe
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'execution_id': execution_id,
                'error': f'Backtest execution failed: {str(e)}',
                'exception_type': type(e).__name__
            }


if __name__ == "__main__":
    # Demo usage
    print("🔄 Backtest Engine Microservice")
    print("=" * 40)
    print("Features:")
    print("✅ Strategy code execution")
    print("✅ Market data simulation")
    print("✅ Performance analysis")
    print("✅ Risk metrics calculation")
    print("✅ Trade statistics")
    print("\nReady for strategy backtesting! 🎯")