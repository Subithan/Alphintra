"""Integration tests for API endpoints."""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from app.core.config import settings

class TestStrategyAPI:
    """Test suite for Strategy API endpoints."""
    
    @patch('app.services.strategy_service.StrategyService.create_strategy')
    def test_create_strategy(self, mock_create, client):
        """Test creating a new strategy."""
        # Mock the service response
        mock_create.return_value = {
            "success": True,
            "strategy_id": "test_strategy_123",
            "validation_warnings": []
        }
        
        # Test data that matches the StrategyCreateRequest model
        strategy_data = {
            "name": "Test Strategy",
            "description": "A test strategy",
            "code": "class MyStrategy:\n    pass",
            "parameters": {"param1": "value1"},
            "tags": ["test", "example"]
        }
        
        # Make request
        response = client.post(
            f"{settings.API_V1_STR}/strategies/",
            json=strategy_data
        )
        
        # Verify response
        assert response.status_code == 201
        assert response.json()["strategy_id"] == "test_strategy_123"
        mock_create.assert_called_once_with(
            strategy_data=strategy_data,
            user_id=mock_create.call_args[1]['user_id'], # user_id is dynamic
            db=mock_create.call_args[1]['db']
        )
    
    @patch('app.api.endpoints.backtesting._check_dataset_exists', return_value=True)
    @patch('app.api.endpoints.backtesting._check_strategy_exists', return_value=True)
    def test_create_backtest_job(self, mock_check_strategy, mock_check_dataset, client):
        """Test creating a new backtest job."""
        # Test data that matches the BacktestJobRequest model
        backtest_data = {
            "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "dataset_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "name": "Test Backtest Job",
            "start_date": "2023-01-01",
            "end_date": "2023-04-01",
            "initial_capital": 100000.0,
        }
        
        # Make request
        response = client.post(
            f"{settings.API_V1_STR}/backtesting/jobs",
            json=backtest_data
        )
        
        # Verify response
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert "backtest_id" in result
        mock_check_strategy.assert_called_once()
        mock_check_dataset.assert_called_once()
    
    @patch('app.api.endpoints.training.training_manager.create_training_job')
    def test_create_training_job(self, mock_create_job, client):
        """Test creating a new training job."""
        # Mock the service response
        mock_create_job.return_value = {
            "success": True,
            "job_id": "job_123",
            "message": "Training job created successfully",
        }

        # Test data that matches the TrainingJobRequest model
        job_data = {
            "strategy_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "dataset_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "job_name": "Test Training Job",
            "instance_type": "cpu_medium",
            "ml_model_config": {"model_name": "xgboost"}
        }

        # Make request
        response = client.post(
            f"{settings.API_V1_STR}/training/jobs",
            json=job_data
        )

        # Verify response
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["job_id"] == "job_123"
        mock_create_job.assert_called_once()

class TestMarketDataAPI:
    """Test suite for Market Data API endpoints."""
    
    @patch('app.services.market_data_service.MarketDataService.get_historical_data')
    def test_get_historical_data(self, mock_get_data, client):
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
    def test_get_latest_data(self, mock_latest, client):
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
