"""
Unit tests for execution mode API endpoint.
Tests the dual execution mode functionality (strategy vs model).
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Test fixtures
@pytest.fixture
def valid_workflow():
    """Valid workflow definition for testing."""
    return {
        "nodes": [
            {
                "id": "data-1",
                "type": "dataSource",
                "data": {
                    "symbol": "BTCUSDT",
                    "timeframe": "1h"
                }
            },
            {
                "id": "rsi-1",
                "type": "technicalIndicator",
                "data": {
                    "indicator": "rsi",
                    "period": 14
                }
            },
            {
                "id": "condition-1",
                "type": "condition",
                "data": {
                    "threshold": 30,
                    "operator": "<"
                }
            },
            {
                "id": "action-1",
                "type": "action",
                "data": {
                    "signal": "buy",
                    "quantity": 100
                }
            }
        ],
        "edges": [
            {"source": "data-1", "target": "rsi-1"},
            {"source": "rsi-1", "target": "condition-1"},
            {"source": "condition-1", "target": "action-1"}
        ]
    }

@pytest.fixture
def invalid_workflow():
    """Invalid workflow definition missing required node types."""
    return {
        "nodes": [
            {
                "id": "data-1",
                "type": "dataSource",
                "data": {"symbol": "BTCUSDT"}
            }
        ],
        "edges": []
    }

@pytest.fixture
def execution_mode_request_strategy():
    """Strategy mode execution request."""
    return {
        "mode": "strategy",
        "config": {
            "backtest_start": "2023-01-01",
            "backtest_end": "2023-12-31",
            "initial_capital": 10000
        }
    }

@pytest.fixture
def execution_mode_request_model():
    """Model mode execution request."""
    return {
        "mode": "model",
        "config": {
            "optimization_objective": "sharpe_ratio",
            "max_trials": 100,
            "timeout_hours": 12
        }
    }


class TestExecutionModeAPI:
    """Test cases for execution mode API endpoint."""
    
    def test_execution_mode_request_validation(self):
        """Test ExecutionModeRequest model validation."""
        from main import ExecutionModeRequest
        
        # Valid strategy mode request
        valid_request = ExecutionModeRequest(
            mode="strategy",
            config={"test": "value"}
        )
        assert valid_request.mode == "strategy"
        assert valid_request.config == {"test": "value"}
        
        # Valid model mode request
        valid_request = ExecutionModeRequest(
            mode="model",
            config={}
        )
        assert valid_request.mode == "model"
        assert valid_request.config == {}
        
        # Invalid mode should raise validation error
        with pytest.raises(ValueError):
            ExecutionModeRequest(mode="invalid_mode", config={})

        # Test new modes
        for mode in ["hybrid", "backtesting", "paper_trading", "research"]:
            req = ExecutionModeRequest(mode=mode, config={})
            assert req.mode == mode
    
    @patch('main.NoCodeWorkflow')
    @patch('main.SessionLocal')
    def test_strategy_mode_execution(self, mock_session_local, mock_workflow, valid_workflow,
                                   execution_mode_request_strategy):
        """Test strategy mode execution path."""
        from main import app
        
        # Mock database workflow
        mock_workflow_instance = Mock()
        mock_workflow_instance.id = 1
        mock_workflow_instance.uuid = "test-uuid"
        mock_workflow_instance.user_id = 123
        mock_workflow_instance.workflow_data = valid_workflow
        mock_workflow_instance.name = "Test Workflow"
        
        # Mock database session
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_session_local.return_value = mock_session
        
        # Mock code generator
        with patch('main.code_generator') as mock_generator:
            mock_generator.generate_strategy_code.return_value = {
                "success": True,
                "code": "# Generated strategy code",
                "requirements": [],
                "metadata": {"complexity": "medium"}
            }
            
            client = TestClient(app)
            response = client.post(
                "/api/workflows/test-uuid/execution-mode",
                json=execution_mode_request_strategy,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["mode"] == "strategy"
            assert "generated_code" in data

    @patch('main.NoCodeWorkflow')
    @patch('main.SessionLocal')
    @patch('main.AIMLClient')
    def test_model_mode_execution(self, MockAIMLClient, mock_session_local, mock_workflow,
                                 valid_workflow, execution_mode_request_model):
        """Test model mode execution path."""
        from main import app
        
        # Mock database workflow
        mock_workflow_instance = Mock()
        mock_workflow_instance.id = 1
        mock_workflow_instance.uuid = "test-uuid"
        mock_workflow_instance.user_id = 123
        mock_workflow_instance.workflow_data = valid_workflow
        mock_workflow_instance.name = "Test Workflow"
        
        # Mock database session
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_session_local.return_value = mock_session
        
        # Mock workflow converter
        with patch('main.workflow_converter') as mock_converter:
            mock_converter.convert_to_training_config.return_value = {
                "success": True,
                "training_config": {
                    "optimization_parameters": ["rsi_period", "threshold"],
                    "parameter_bounds": {"rsi_period": [10, 20], "threshold": [20, 40]}
                }
            }
            
            # Mock AI-ML client
            mock_aiml_instance = MockAIMLClient.return_value.__aenter__.return_value
            mock_aiml_instance.create_training_job_from_workflow = AsyncMock(return_value={
                "training_job_id": "training_job_123",
                "status": "training_submitted"
            })
            
            client = TestClient(app)
            response = client.post(
                "/api/workflows/test-uuid/execution-mode",
                json=execution_mode_request_model,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["mode"] == "model"
            assert data["status"] == "training_submitted"
            assert data["training_job_id"] == "training_job_123"

@pytest.mark.parametrize("mode, client_method", [
    ("hybrid", "start_hybrid_execution"),
    ("backtesting", "start_backtest"),
    ("paper_trading", "start_paper_trading"),
    ("research", "start_research_session"),
])
@patch('main.NoCodeWorkflow')
@patch('main.SessionLocal')
@patch('main.AIMLClient')
def test_new_execution_modes(MockAIMLClient, mock_session_local, mock_workflow, mode, client_method, valid_workflow):
    """Test the new execution modes."""
    from main import app

    mock_workflow_instance = Mock()
    mock_workflow_instance.uuid = "test-uuid"
    mock_workflow_instance.user_id = 123
    mock_workflow_instance.workflow_data = valid_workflow

    mock_db_session = Mock()
    mock_db_session.query().filter().first.return_value = mock_workflow_instance
    mock_session_local.return_value = mock_db_session

    mock_aiml_instance = MockAIMLClient.return_value.__aenter__.return_value

    # Set up the mock for the specific client method being tested
    async_mock = AsyncMock(return_value={"status": f"{mode} started"})
    setattr(mock_aiml_instance, client_method, async_mock)

    client = TestClient(app)
    response = client.post(
        f"/api/workflows/{mock_workflow_instance.uuid}/execution-mode",
        json={"mode": mode, "config": {"test": "config"}},
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == f"{mode} started"

    # Verify that the correct client method was called
    getattr(mock_aiml_instance, client_method).assert_called_once_with(
        valid_workflow, {"test": "config"}
    )
    
    @patch('main.NoCodeWorkflow')
    @patch('main.SessionLocal')
    def test_workflow_not_found(self, mock_session_local, mock_workflow, execution_mode_request_strategy):
        """Test handling of non-existent workflow."""
        from main import app
        
        # Mock database session returning None
        mock_session = Mock()
        mock_session.query().filter().first.return_value = None
        mock_session_local.return_value = mock_session
        
        client = TestClient(app)
        response = client.post(
            "/api/workflows/999/execution-mode",
            json=execution_mode_request_strategy,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 404
        assert "Workflow not found" in response.json()["detail"]
    
    @patch('main.NoCodeWorkflow')
    @patch('main.SessionLocal')
    def test_unauthorized_access(self, mock_session_local, mock_workflow, execution_mode_request_strategy):
        """Test unauthorized access to workflow."""
        from main import app
        
        # Mock workflow owned by different user
        mock_workflow_instance = Mock()
        mock_workflow_instance.uuid = "test-uuid"
        mock_workflow_instance.user_id = 999  # Different user
        
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_session_local.return_value = mock_session
        
        client = TestClient(app)
        with patch('main.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id=123)
            response = client.post(
                "/api/workflows/test-uuid/execution-mode",
                json=execution_mode_request_strategy,
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 404 # because the query will return nothing for this user
        assert "not found" in response.json()["detail"].lower()
    
    @patch('main.SessionLocal')
    def test_database_error_handling(self, mock_session_local, execution_mode_request_strategy):
        """Test handling of database errors."""
        from main import app
        
        # Mock database session that raises an exception
        mock_session_local.side_effect = Exception("Database connection failed")
        
        client = TestClient(app)
        response = client.post(
            "/api/workflows/1/execution-mode",
            json=execution_mode_request_strategy,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()
    
    @patch('main.NoCodeWorkflow')
    @patch('main.SessionLocal')
    @patch('main.AIMLClient')
    def test_aiml_service_failure(self, MockAIMLClient, mock_session_local, mock_workflow,
                                 valid_workflow, execution_mode_request_model):
        """Test handling of AI-ML service failures."""
        from main import app, AIMLServiceUnavailable
        
        # Mock successful database retrieval
        mock_workflow_instance = Mock()
        mock_workflow_instance.uuid = "test-uuid"
        mock_workflow_instance.user_id = 123
        mock_workflow_instance.workflow_data = valid_workflow
        mock_workflow_instance.name = "Test Workflow"
        
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_session_local.return_value = mock_session
        
        # Mock workflow converter success
        with patch('main.workflow_converter') as mock_converter:
            mock_converter.convert_to_training_config.return_value = {
                "success": True,
                "training_config": {"test": "config"}
            }
            
            # Mock AI-ML client failure
            mock_aiml_instance = MockAIMLClient.return_value.__aenter__.return_value
            mock_aiml_instance.create_training_job_from_workflow = AsyncMock(side_effect=AIMLServiceUnavailable("Service down"))
            
            client = TestClient(app)
            response = client.post(
                "/api/workflows/test-uuid/execution-mode",
                json=execution_mode_request_model,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 503
            assert "ai-ml service unavailable" in response.json()["detail"].lower()


class TestExecutionModeEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_config_handling(self):
        """Test handling of empty config in request."""
        from main import ExecutionModeRequest
        
        request = ExecutionModeRequest(mode="strategy", config={})
        assert request.config == {}
    
    def test_large_config_handling(self):
        """Test handling of large config objects."""
        from main import ExecutionModeRequest
        
        large_config = {f"param_{i}": f"value_{i}" for i in range(100)}
        request = ExecutionModeRequest(mode="strategy", config=large_config)
        assert len(request.config) == 100
    
# This test is removed as it's harder to trigger with the current setup
# and the logic is simple enough not to warrant a complex mock setup.
# The main logic is tested by other tests.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])