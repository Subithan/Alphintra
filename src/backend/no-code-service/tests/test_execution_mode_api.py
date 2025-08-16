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
    
    @patch('main.NoCodeWorkflow')
    @patch('main.get_db')
    def test_strategy_mode_execution(self, mock_get_db, mock_workflow, valid_workflow, 
                                   execution_mode_request_strategy):
        """Test strategy mode execution path."""
        from main import app
        
        # Mock database workflow
        mock_workflow_instance = Mock()
        mock_workflow_instance.id = 1
        mock_workflow_instance.user_id = 123
        mock_workflow_instance.workflow_data = valid_workflow
        mock_workflow_instance.name = "Test Workflow"
        
        # Mock database session
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_get_db.return_value = mock_session
        
        # Mock code generator
        with patch('main.code_generator') as mock_generator:
            mock_generator.generate_strategy_code.return_value = {
                "success": True,
                "code": "# Generated strategy code",
                "metadata": {"complexity": "medium"}
            }
            
            client = TestClient(app)
            response = client.post(
                "/api/workflows/1/execution-mode",
                json=execution_mode_request_strategy,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["execution_mode"] == "strategy"
            assert data["next_action"] == "execute_strategy"
            assert "strategy_code" in data
            assert data["workflow_info"]["workflow_id"] == 1
    
    @patch('main.NoCodeWorkflow')
    @patch('main.get_db')
    @patch('main.aiml_client')
    def test_model_mode_execution(self, mock_aiml_client, mock_get_db, mock_workflow, 
                                 valid_workflow, execution_mode_request_model):
        """Test model mode execution path."""
        from main import app
        
        # Mock database workflow
        mock_workflow_instance = Mock()
        mock_workflow_instance.id = 1
        mock_workflow_instance.user_id = 123
        mock_workflow_instance.workflow_data = valid_workflow
        mock_workflow_instance.name = "Test Workflow"
        
        # Mock database session
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_get_db.return_value = mock_session
        
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
            mock_aiml_client.create_training_job_from_workflow.return_value = {
                "success": True,
                "job_id": "training_job_123",
                "status": "queued"
            }
            
            client = TestClient(app)
            response = client.post(
                "/api/workflows/1/execution-mode",
                json=execution_mode_request_model,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["execution_mode"] == "model"
            assert data["next_action"] == "monitor_training"
            assert data["training_job_id"] == "training_job_123"
            assert data["workflow_info"]["workflow_id"] == 1
    
    @patch('main.NoCodeWorkflow')
    @patch('main.get_db')
    def test_workflow_not_found(self, mock_get_db, mock_workflow, execution_mode_request_strategy):
        """Test handling of non-existent workflow."""
        from main import app
        
        # Mock database session returning None
        mock_session = Mock()
        mock_session.query().filter().first.return_value = None
        mock_get_db.return_value = mock_session
        
        client = TestClient(app)
        response = client.post(
            "/api/workflows/999/execution-mode",
            json=execution_mode_request_strategy,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 404
        assert "Workflow not found" in response.json()["detail"]
    
    @patch('main.NoCodeWorkflow')
    @patch('main.get_db')
    def test_invalid_workflow_structure(self, mock_get_db, mock_workflow, 
                                      invalid_workflow, execution_mode_request_model):
        """Test handling of invalid workflow structure."""
        from main import app
        
        # Mock database workflow with invalid structure
        mock_workflow_instance = Mock()
        mock_workflow_instance.id = 1
        mock_workflow_instance.user_id = 123
        mock_workflow_instance.workflow_data = invalid_workflow
        mock_workflow_instance.name = "Invalid Workflow"
        
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_get_db.return_value = mock_session
        
        client = TestClient(app)
        response = client.post(
            "/api/workflows/1/execution-mode",
            json=execution_mode_request_model,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 400
        assert "missing required node types" in response.json()["detail"].lower()
    
    @patch('main.NoCodeWorkflow')
    @patch('main.get_db')
    def test_unauthorized_access(self, mock_get_db, mock_workflow, execution_mode_request_strategy):
        """Test unauthorized access to workflow."""
        from main import app
        
        # Mock workflow owned by different user
        mock_workflow_instance = Mock()
        mock_workflow_instance.id = 1
        mock_workflow_instance.user_id = 999  # Different user
        
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_get_db.return_value = mock_session
        
        client = TestClient(app)
        response = client.post(
            "/api/workflows/1/execution-mode",
            json=execution_mode_request_strategy,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()
    
    @patch('main.NoCodeWorkflow')
    @patch('main.get_db')
    def test_database_error_handling(self, mock_get_db, mock_workflow, execution_mode_request_strategy):
        """Test handling of database errors."""
        from main import app
        
        # Mock database session that raises an exception
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database connection failed")
        mock_get_db.return_value = mock_session
        
        client = TestClient(app)
        response = client.post(
            "/api/workflows/1/execution-mode",
            json=execution_mode_request_strategy,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()
    
    @patch('main.NoCodeWorkflow')
    @patch('main.get_db')
    @patch('main.aiml_client')
    def test_aiml_service_failure(self, mock_aiml_client, mock_get_db, mock_workflow, 
                                 valid_workflow, execution_mode_request_model):
        """Test handling of AI-ML service failures."""
        from main import app
        
        # Mock successful database retrieval
        mock_workflow_instance = Mock()
        mock_workflow_instance.id = 1
        mock_workflow_instance.user_id = 123
        mock_workflow_instance.workflow_data = valid_workflow
        mock_workflow_instance.name = "Test Workflow"
        
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_get_db.return_value = mock_session
        
        # Mock workflow converter success
        with patch('main.workflow_converter') as mock_converter:
            mock_converter.convert_to_training_config.return_value = {
                "success": True,
                "training_config": {"test": "config"}
            }
            
            # Mock AI-ML client failure
            mock_aiml_client.create_training_job_from_workflow.return_value = {
                "success": False,
                "error": "AI-ML service unavailable"
            }
            
            client = TestClient(app)
            response = client.post(
                "/api/workflows/1/execution-mode",
                json=execution_mode_request_model,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 500
            assert "ai-ml service" in response.json()["detail"].lower()


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
    
    @patch('main.NoCodeWorkflow')
    @patch('main.get_db')
    def test_workflow_data_corruption(self, mock_get_db, mock_workflow, execution_mode_request_strategy):
        """Test handling of corrupted workflow data."""
        from main import app
        
        # Mock workflow with corrupted JSON data
        mock_workflow_instance = Mock()
        mock_workflow_instance.id = 1
        mock_workflow_instance.user_id = 123
        mock_workflow_instance.workflow_data = {"corrupted": "incomplete"}
        mock_workflow_instance.name = "Corrupted Workflow"
        
        mock_session = Mock()
        mock_session.query().filter().first.return_value = mock_workflow_instance
        mock_get_db.return_value = mock_session
        
        client = TestClient(app)
        response = client.post(
            "/api/workflows/1/execution-mode",
            json=execution_mode_request_strategy,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 400
        assert "invalid workflow" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])