"""Test utilities for the AI/ML Strategy Service."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sample_market_data(
    symbols=None,
    start_date='2023-01-01',
    periods=100,
    freq='D',
    add_indicators=True
):
    """
    Create sample market data for testing.
    
    Args:
        symbols: List of symbols to generate data for
        start_date: Start date for the data
        periods: Number of periods to generate
        freq: Frequency of the data (e.g., 'D' for daily)
        add_indicators: Whether to add technical indicators
        
    Returns:
        pd.DataFrame: Sample market data
    """
    if symbols is None:
        symbols = ['AAPL', 'MSFT']
    
    date_range = pd.date_range(start=start_date, periods=periods, freq=freq)
    
    dfs = []
    for symbol in symbols:
        # Base prices with some randomness
        base = np.linspace(100, 200, periods)
        noise = np.random.normal(0, 5, periods)
        
        df = pd.DataFrame({
            'symbol': symbol,
            'timestamp': date_range,
            'open': base + noise,
            'high': base + noise + np.random.uniform(1, 5, periods),
            'low': base + noise - np.random.uniform(1, 5, periods),
            'close': base + noise,
            'volume': np.random.randint(1000, 10000, periods),
            'dividends': 0.0,
            'splits': 1.0
        })
        
        # Add some trends and seasonality
        df['close'] = df['close'] + 10 * np.sin(np.linspace(0, 10, periods))
        
        # Recalculate high/low based on close
        df['high'] = df[['high', 'close']].max(axis=1)
        df['low'] = df[['low', 'close']].min(axis=1)
        
        if add_indicators:
            # Add some technical indicators
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp1 - exp2
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        dfs.append(df)
    
    return pd.concat(dfs, ignore_index=True)

def create_sample_strategy_config():
    """Create a sample strategy configuration for testing."""
    return {
        "name": "TestStrategy",
        "description": "A test strategy for unit testing",
        "version": "1.0.0",
        "author": "Test User",
        "parameters": {
            "fast_ma": 10,
            "slow_ma": 30,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30
        },
        "symbols": ["AAPL", "MSFT"],
        "timeframe": "1d",
        "initial_capital": 100000,
        "commission": 0.001,
        "slippage": 0.0005,
        "risk_parameters": {
            "max_position_size": 0.1,
            "stop_loss": 0.05,
            "take_profit": 0.10,
            "max_drawdown": 0.20
        },
        "data_requirements": {
            "start_date": "2023-01-01",
            "end_date": "2023-04-10",
            "indicators": ["sma", "rsi", "macd"]
        }
    }

def assert_dataframe_structure(df, expected_columns=None):
    """
    Assert that a DataFrame has the expected structure.
    
    Args:
        df: DataFrame to check
        expected_columns: List of expected column names
    """
    assert isinstance(df, pd.DataFrame), "Expected a pandas DataFrame"
    assert not df.empty, "DataFrame is empty"
    
    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        assert not missing, f"Missing columns: {missing}"

def assert_backtest_results(results):
    """
    Assert that backtest results have the expected structure.
    
    Args:
        results: Backtest results dictionary
    """
    required_keys = {
        'returns', 'equity_curve', 'trades', 'positions',
        'performance_metrics', 'risk_metrics'
    }
    
    missing = required_keys - set(results.keys())
    assert not missing, f"Missing required keys in results: {missing}"
    
    # Check equity curve
    assert_dataframe_structure(
        results['equity_curve'],
        ['equity', 'returns', 'drawdown']
    )
    
    # Check trades
    if len(results['trades']) > 0:
        assert_dataframe_structure(
            results['trades'],
            ['entry_time', 'exit_time', 'symbol', 'quantity', 
             'entry_price', 'exit_price', 'pnl', 'return_pct']
        )
    
    # Check performance metrics
    required_metrics = {
        'total_return', 'annualized_return', 'volatility',
        'sharpe_ratio', 'sortino_ratio', 'max_drawdown',
        'win_rate', 'profit_factor'
    }
    
    metrics = results['performance_metrics']
    missing_metrics = required_metrics - set(metrics.keys())
    assert not missing_metrics, f"Missing performance metrics: {missing_metrics}"
