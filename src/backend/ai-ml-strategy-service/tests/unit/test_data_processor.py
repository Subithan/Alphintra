"""Unit tests for the DataProcessor service."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.services.data_processor import DataProcessor

class TestDataProcessor:
    """Test suite for DataProcessor service."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.processor = DataProcessor()
        self.sample_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='D'),
            'open': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(200, 300, 100),
            'low': np.random.uniform(50, 150, 100),
            'close': np.random.uniform(150, 250, 100),
            'volume': np.random.randint(1000, 10000, 100)
        })
    
    def test_calculate_technical_indicators(self):
        """Test calculation of technical indicators."""
        processed_data = self.processor.calculate_technical_indicators(
            self.sample_data, 
            indicators=['sma', 'rsi', 'macd']
        )
        
        # Check if indicators are added
        assert 'sma_20' in processed_data.columns
        assert 'rsi_14' in processed_data.columns
        assert 'macd' in processed_data.columns
        assert 'signal' in processed_data.columns
        
        # Check for NaN values (should be less than initial rows due to rolling windows)
        assert processed_data['sma_20'].isna().sum() == 19  # First 19 should be NaN for SMA 20
    
    def test_preprocess_data(self):
        """Test data preprocessing."""
        # Add some NaN values to test handling
        test_data = self.sample_data.copy()
        test_data.loc[10:15, 'close'] = np.nan
        
        processed = self.processor.preprocess_data(test_data)
        
        # Check if NaNs are handled
        assert processed.isna().sum().sum() == 0
        
        # Check if datetime index is set
        assert isinstance(processed.index, pd.DatetimeIndex)
    
    @patch('app.services.data_processor.DataProcessor._load_model')
    def test_generate_signals(self, mock_load_model):
        """Test signal generation."""
        # Mock model prediction
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1, 0, 1, 0, 1])
        mock_load_model.return_value = mock_model
        
        signals = self.processor.generate_signals(
            self.sample_data, 
            model_name='test_model',
            features=['close', 'volume']
        )
        
        # Verify signals are generated
        assert len(signals) == len(self.sample_data)
        assert set(signals.unique()).issubset({-1, 0, 1})  # Only valid signal values
    
    def test_split_train_test(self):
        """Test train-test split functionality."""
        X_train, X_test, y_train, y_test = self.processor.split_train_test(
            self.sample_data, 
            target='close',
            test_size=0.2,
            shuffle=False
        )
        
        # Verify split sizes
        assert len(X_train) == 80  # 80% of 100
        assert len(X_test) == 20   # 20% of 100
        assert len(y_train) == 80
        assert len(y_test) == 20
        
        # Verify no data leakage
        assert X_train.index.max() < X_test.index.min()  # No future data in train
