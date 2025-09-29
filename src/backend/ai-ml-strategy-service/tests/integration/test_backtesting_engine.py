"""Integration tests for the BacktestingEngine."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.services.backtesting_engine import BacktestingEngine
from app.services.data_processor import DataProcessor

class TestBacktestingEngineIntegration:
    """Integration tests for BacktestingEngine with other components."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = BacktestingEngine()
        self.data_processor = DataProcessor(name="Test Processor", description="A test processor")
        
        # Generate sample market data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        self.sample_data = pd.DataFrame({
            'timestamp': dates,
            'open': np.linspace(100, 200, 100),
            'high': np.linspace(105, 205, 100),
            'low': np.linspace(95, 195, 100),
            'close': np.linspace(102, 202, 100),
            'volume': np.random.randint(1000, 10000, 100)
        }).set_index('timestamp')
        
        # Sample strategy configuration
        self.strategy_config = {
            'name': 'MovingAverageCrossover',
            'parameters': {
                'fast_ma': 10,
                'slow_ma': 30
            },
            'symbols': ['TEST'],
            'timeframe': '1d'
        }
    
    @patch('app.services.market_data_service.MarketDataService.get_historical_data')
    def test_end_to_end_backtest(self, mock_get_data):
        """Test complete backtesting workflow with mocked dependencies."""
        # Mock market data service
        mock_get_data.return_value = self.sample_data
        
        # Run backtest
        results = self.engine.run_backtest(
            strategy_config=self.strategy_config,
            start_date='2023-01-01',
            end_date='2023-04-10',
            initial_capital=100000
        )
        
        # Verify results structure
        assert 'returns' in results
        assert 'trades' in results
        assert 'equity_curve' in results
        assert 'performance_metrics' in results
        
        # Verify basic calculations
        assert len(results['trades']) > 0
        assert 'equity_curve' in results
        assert isinstance(results['performance_metrics'], dict)
        
        # Verify performance metrics
        metrics = results['performance_metrics']
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
    
    @patch('app.services.market_data_service.MarketDataService.get_historical_data')
    def test_risk_management_integration(self, mock_get_data):
        """Test integration with risk management components."""
        # Configure test with tight risk parameters
        self.strategy_config['risk_parameters'] = {
            'max_position_size': 0.1,  # 10% of portfolio per position
            'stop_loss': 0.05,         # 5% stop loss
            'take_profit': 0.10        # 10% take profit
        }
        
        # Mock market data with a clear trend
        mock_data = self.sample_data.copy()
        mock_data['close'] = np.linspace(100, 200, 100)  # Clear uptrend
        mock_get_data.return_value = mock_data
        
        # Run backtest
        results = self.engine.run_backtest(
            strategy_config=self.strategy_config,
            start_date='2023-01-01',
            end_date='2023-04-10',
            initial_capital=100000
        )
        
        # Verify risk management was applied
        trades = results['trades']
        for trade in trades:
            # Check position sizing
            assert trade['position_size'] <= 10000  # 10% of 100k
            
            # Check stop loss/take profit levels if applicable
            if 'exit_price' in trade:
                if trade['pnl'] < 0:
                    # Should hit stop loss
                    expected_loss = trade['entry_price'] * 0.05
                    actual_loss = trade['entry_price'] - trade['exit_price']
                    assert abs(actual_loss - expected_loss) < 0.01  # Allow for floating point errors
    
    @patch('app.services.market_data_service.MarketDataService.get_historical_data')
    def test_performance_metrics_calculation(self, mock_get_data):
        """Verify calculation of performance metrics."""
        # Create a perfect trading scenario (buy at low, sell at high)
        mock_data = self.sample_data.copy()
        mock_data['close'] = np.tile([90, 110] * 50, 1)[:100]  # Alternating between 90 and 110
        mock_get_data.return_value = mock_data
        
        # Run backtest with perfect strategy (buy at 90, sell at 110)
        results = self.engine.run_backtest(
            strategy_config=self.strategy_config,
            start_date='2023-01-01',
            end_date='2023-04-10',
            initial_capital=100000
        )
        
        # Verify performance metrics
        metrics = results['performance_metrics']
        
        # Should have positive returns
        assert metrics['total_return'] > 0
        
        # With perfect trades, win rate should be 100%
        assert metrics['win_rate'] == 1.0
        
        # Profit factor should be high (no losing trades)
        assert metrics['profit_factor'] > 10
