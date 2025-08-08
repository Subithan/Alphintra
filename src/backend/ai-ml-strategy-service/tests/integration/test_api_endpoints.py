"""Integration tests for API endpoints."""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from app.core.config import settings

# Test client
client = TestClient(app)

class TestStrategyAPI:
    """Test suite for Strategy API endpoints."""
    
    @patch('app.services.strategy_service.StrategyService.create_strategy')
    def test_create_strategy(self, mock_create):
        """Test creating a new strategy."""
        # Mock the service response
        mock_strategy = {
            "id": "test_strategy_123",
            "name": "Test Strategy",
            "status": "active",
            "created_at": "2023-01-01T00:00:00"
        }
        mock_create.return_value = mock_strategy
        
        # Test data
        strategy_data = {
            "name": "Test Strategy",
            "description": "A test strategy",
            "parameters": {"param1": "value1"},
            "symbols": ["AAPL", "MSFT"],
            "timeframe": "1d"
        }
        
        # Make request
        response = client.post(
            f"{settings.API_V1_STR}/strategies/",
            json=strategy_data
        )
        
        # Verify response
        assert response.status_code == 201
        assert response.json()["id"] == "test_strategy_123"
        mock_create.assert_called_once()
    
    @patch('app.services.backtesting_engine.BacktestingEngine.run_backtest')
    def test_run_backtest(self, mock_backtest):
        """Test running a backtest."""
        # Mock backtest results
        mock_results = {
            "returns": 0.15,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.12,
            "trades": [],
            "equity_curve": {}
        }
        mock_backtest.return_value = mock_results
        
        # Test data
        backtest_data = {
            "strategy_id": "test_strategy_123",
            "start_date": "2023-01-01",
            "end_date": "2023-04-01",
            "initial_capital": 100000,
            "parameters": {}
        }
        
        # Make request
        response = client.post(
            f"{settings.API_V1_STR}/backtest/",
            json=backtest_data
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert "returns" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        mock_backtest.assert_called_once()
    
    @patch('app.services.training_job_manager.TrainingJobManager.train_model')
    def test_train_model(self, mock_train):
        """Test training a model."""
        # Mock training response
        mock_result = {
            "job_id": "train_123",
            "status": "started",
            "model_id": "model_456"
        }
        mock_train.return_value = mock_result
        
        # Test data
        train_data = {
            "strategy_id": "test_strategy_123",
            "model_type": "random_forest",
            "parameters": {"n_estimators": 100},
            "data_range": {"start": "2022-01-01", "end": "2023-01-01"}
        }
        
        # Make request
        response = client.post(
            f"{settings.API_V1_STR}/models/train/",
            json=train_data
        )
        
        # Verify response
        assert response.status_code == 202
        result = response.json()
        assert "job_id" in result
        assert "status" in result
        assert result["status"] == "started"
        mock_train.assert_called_once()

class TestMarketDataAPI:
    """Test suite for Market Data API endpoints."""
    
    @patch('app.services.market_data_service.MarketDataService.get_historical_data')
    def test_get_historical_data(self, mock_get_data):
        """Test fetching historical market data."""
        # Mock data
        mock_data = {
            "symbol": "AAPL",
            "data": [
                {"date": "2023-01-01", "open": 100, "high": 105, "low": 99, "close": 102, "volume": 1000000},
                {"date": "2023-01-02", "open": 102, "high": 108, "low": 101, "close": 107, "volume": 1200000}
            ]
        }
        mock_get_data.return_value = mock_data
        
        # Make request
        response = client.get(
            f"{settings.API_V1_STR}/market/data/historical/",
            params={
                "symbol": "AAPL",
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
                "timeframe": "1d"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "data" in data
        assert len(data["data"]) == 2
        mock_get_data.assert_called_once()
    
    @patch('app.services.market_data_service.MarketDataService.get_latest_data')
    def test_get_latest_data(self, mock_latest):
        """Test fetching latest market data."""
        # Mock data
        mock_data = {
            "symbol": "AAPL",
            "timestamp": "2023-01-02T16:00:00",
            "open": 102.5,
            "high": 103.2,
            "low": 101.8,
            "close": 102.9,
            "volume": 500000
        }
        mock_latest.return_value = mock_data
        
        # Make request
        response = client.get(
            f"{settings.API_V1_STR}/market/data/latest/",
            params={"symbol": "AAPL"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "timestamp" in data
        assert "close" in data
        mock_latest.assert_called_once()
