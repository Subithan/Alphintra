"""
Unit tests for AI-ML service client.
Tests HTTP client functionality, retry logic, and error handling.
"""

import pytest
import httpx
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import sys
from pathlib import Path

# Add the parent directory to the path to import the client
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from clients.aiml_client import AIMLClient, AIMLServiceError, AIMLAuthenticationError, AIMLTimeoutError


@pytest.fixture
def sample_workflow_request():
    """Sample workflow training request data."""
    return {
        "workflow_id": 123,
        "workflow_name": "Test Strategy",
        "workflow_definition": {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {"id": "rsi-1", "type": "technicalIndicator", "data": {"indicator": "rsi", "period": 14}},
                {"id": "condition-1", "type": "condition", "data": {"threshold": 30, "operator": "<"}},
                {"id": "action-1", "type": "action", "data": {"action": "buy", "quantity": 100}}
            ],
            "edges": [
                {"source": "data-1", "target": "rsi-1"},
                {"source": "rsi-1", "target": "condition-1"},
                {"source": "condition-1", "target": "action-1"}
            ]
        },
        "training_config": {
            "optimization_parameters": ["rsi_period", "threshold"],
            "parameter_bounds": {"rsi_period": [10, 20], "threshold": [20, 40]}
        },
        "optimization_objective": "sharpe_ratio",
        "max_trials": 50
    }

@pytest.fixture
def mock_successful_response():
    """Mock successful API response."""
    return {
        "success": True,
        "job_id": "training_job_abc123",
        "status": "queued",
        "estimated_duration_hours": 2.5,
        "queue_position": 3
    }

@pytest.fixture
def mock_error_response():
    """Mock error API response."""
    return {
        "success": False,
        "error": "Invalid workflow definition",
        "error_code": "VALIDATION_ERROR",
        "details": ["Missing required node types"]
    }


class TestAIMLClient:
    """Test cases for AIMLClient class."""
    
    def test_client_initialization(self):
        """Test AIMLClient initialization with different configurations."""
        # Default initialization
        client = AIMLClient()
        assert client.base_url == "http://localhost:8001"
        assert client.timeout == 30.0
        assert client.max_retries == 3
        
        # Custom initialization
        custom_client = AIMLClient(
            base_url="https://api.example.com",
            timeout=60.0,
            max_retries=5,
            auth_token="test-token"
        )
        assert custom_client.base_url == "https://api.example.com"
        assert custom_client.timeout == 60.0
        assert custom_client.max_retries == 5
    
    @pytest.mark.asyncio
    async def test_successful_training_job_creation(self, sample_workflow_request, mock_successful_response):
        """Test successful training job creation."""
        client = AIMLClient()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_successful_response
            
            result = await client.create_training_job_from_workflow(sample_workflow_request)
            
            assert result["success"] is True
            assert result["job_id"] == "training_job_abc123"
            assert result["status"] == "queued"
            
            # Verify request was made with correct parameters
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert "/api/training/from-workflow" in call_args[0][1]
            assert call_args[1]["json"] == sample_workflow_request
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, sample_workflow_request):
        """Test handling of authentication errors."""
        client = AIMLClient()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = AIMLAuthenticationError("Invalid token")
            
            with pytest.raises(AIMLAuthenticationError):
                await client.create_training_job_from_workflow(sample_workflow_request)
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, sample_workflow_request):
        """Test handling of timeout errors."""
        client = AIMLClient()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = AIMLTimeoutError("Request timed out")
            
            with pytest.raises(AIMLTimeoutError):
                await client.create_training_job_from_workflow(sample_workflow_request)
    
    @pytest.mark.asyncio
    async def test_service_error_handling(self, sample_workflow_request, mock_error_response):
        """Test handling of service errors."""
        client = AIMLClient()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_error_response
            
            result = await client.create_training_job_from_workflow(sample_workflow_request)
            
            assert result["success"] is False
            assert result["error"] == "Invalid workflow definition"
            assert "VALIDATION_ERROR" in result["error_code"]
    
    @pytest.mark.asyncio
    async def test_get_training_job_status(self):
        """Test getting training job status."""
        client = AIMLClient()
        job_id = "training_job_123"
        
        expected_response = {
            "job_id": job_id,
            "status": "running",
            "progress": 0.45,
            "current_step": "hyperparameter_tuning",
            "metrics": {
                "current_trial": 12,
                "best_score": 0.823,
                "trials_remaining": 38
            }
        }
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = expected_response
            
            result = await client.get_training_job_status(job_id)
            
            assert result["job_id"] == job_id
            assert result["status"] == "running"
            assert result["progress"] == 0.45
            assert "metrics" in result
            
            # Verify correct endpoint was called
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert f"/api/training/jobs/{job_id}" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_get_training_job_results(self):
        """Test getting training job results."""
        client = AIMLClient()
        job_id = "training_job_123"
        
        expected_response = {
            "job_id": job_id,
            "status": "completed",
            "final_metrics": {
                "best_parameters": {
                    "rsi_period": 16,
                    "threshold": 28.5
                },
                "performance_metrics": {
                    "sharpe_ratio": 1.85,
                    "max_drawdown": -0.12,
                    "total_return": 0.34
                }
            },
            "optimization_results": {
                "total_trials": 50,
                "best_trial": 42,
                "convergence_achieved": True
            }
        }
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = expected_response
            
            result = await client.get_training_job_results(job_id)
            
            assert result["job_id"] == job_id
            assert result["status"] == "completed"
            assert "final_metrics" in result
            assert "best_parameters" in result["final_metrics"]
            assert result["final_metrics"]["best_parameters"]["rsi_period"] == 16
    
    @pytest.mark.asyncio
    async def test_retry_logic_on_network_error(self, sample_workflow_request, mock_successful_response):
        """Test retry logic on network errors."""
        client = AIMLClient(max_retries=3)
        
        with patch('httpx.AsyncClient.request', new_callable=AsyncMock) as mock_httpx:
            # First two calls fail with network error, third succeeds
            mock_httpx.side_effect = [
                httpx.NetworkError("Connection failed"),
                httpx.NetworkError("Connection failed"),
                httpx.Response(
                    200,
                    content=json.dumps(mock_successful_response).encode(),
                    headers={"content-type": "application/json"}
                )
            ]
            
            result = await client.create_training_job_from_workflow(sample_workflow_request)
            
            # Should eventually succeed after retries
            assert result["success"] is True
            assert result["job_id"] == "training_job_abc123"
            
            # Verify it made 3 attempts
            assert mock_httpx.call_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, sample_workflow_request):
        """Test circuit breaker functionality."""
        client = AIMLClient()
        
        # Simulate multiple consecutive failures to trigger circuit breaker
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = AIMLServiceError("Service unavailable")
            
            # Make multiple requests that should trigger circuit breaker
            for i in range(client._circuit_breaker_threshold + 1):
                try:
                    await client.create_training_job_from_workflow(sample_workflow_request)
                except AIMLServiceError:
                    pass
            
            # Circuit breaker should now be open
            assert client._circuit_breaker_open is True
            
            # Next request should fail immediately without making HTTP call
            with pytest.raises(AIMLServiceError, match="Circuit breaker"):
                await client.create_training_job_from_workflow(sample_workflow_request)
    
    @pytest.mark.asyncio
    async def test_request_timeout_handling(self, sample_workflow_request):
        """Test request timeout handling."""
        client = AIMLClient(timeout=1.0)  # Very short timeout
        
        with patch('httpx.AsyncClient.request', new_callable=AsyncMock) as mock_httpx:
            mock_httpx.side_effect = httpx.TimeoutException("Request timed out")
            
            with pytest.raises(AIMLTimeoutError):
                await client.create_training_job_from_workflow(sample_workflow_request)
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self, sample_workflow_request):
        """Test handling of malformed JSON responses."""
        client = AIMLClient()
        
        with patch('httpx.AsyncClient.request', new_callable=AsyncMock) as mock_httpx:
            # Return malformed JSON
            mock_httpx.return_value = httpx.Response(
                200,
                content=b"invalid json{",
                headers={"content-type": "application/json"}
            )
            
            with pytest.raises(AIMLServiceError, match="Invalid response format"):
                await client.create_training_job_from_workflow(sample_workflow_request)
    
    @pytest.mark.asyncio
    async def test_http_error_status_codes(self, sample_workflow_request):
        """Test handling of various HTTP error status codes."""
        client = AIMLClient()
        
        error_scenarios = [
            (400, "Bad Request"),
            (401, "Unauthorized"), 
            (403, "Forbidden"),
            (404, "Not Found"),
            (500, "Internal Server Error"),
            (503, "Service Unavailable")
        ]
        
        for status_code, status_text in error_scenarios:
            with patch('httpx.AsyncClient.request', new_callable=AsyncMock) as mock_httpx:
                mock_httpx.return_value = httpx.Response(
                    status_code,
                    content=json.dumps({"error": status_text}).encode(),
                    headers={"content-type": "application/json"}
                )
                
                if status_code == 401:
                    with pytest.raises(AIMLAuthenticationError):
                        await client.create_training_job_from_workflow(sample_workflow_request)
                elif status_code >= 500:
                    with pytest.raises(AIMLServiceError):
                        await client.create_training_job_from_workflow(sample_workflow_request)
                else:
                    # Should return error response for client errors
                    result = await client.create_training_job_from_workflow(sample_workflow_request)
                    assert result["success"] is False


class TestAIMLClientIntegration:
    """Integration-like tests for AIMLClient."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_training_lifecycle(self, sample_workflow_request):
        """Test complete workflow training lifecycle."""
        client = AIMLClient()
        
        # Mock the sequence of API calls for a complete lifecycle
        mock_responses = [
            # Create training job
            {
                "success": True,
                "job_id": "training_job_xyz",
                "status": "queued"
            },
            # Get status - running
            {
                "job_id": "training_job_xyz",
                "status": "running",
                "progress": 0.3
            },
            # Get status - completed
            {
                "job_id": "training_job_xyz",
                "status": "completed",
                "progress": 1.0
            },
            # Get results
            {
                "job_id": "training_job_xyz",
                "status": "completed",
                "final_metrics": {
                    "best_parameters": {"rsi_period": 18},
                    "performance_metrics": {"sharpe_ratio": 1.65}
                }
            }
        ]
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = mock_responses
            
            # 1. Create training job
            create_result = await client.create_training_job_from_workflow(sample_workflow_request)
            assert create_result["success"] is True
            job_id = create_result["job_id"]
            
            # 2. Check status (running)
            status_result = await client.get_training_job_status(job_id)
            assert status_result["status"] == "running"
            assert status_result["progress"] == 0.3
            
            # 3. Check status (completed)
            status_result = await client.get_training_job_status(job_id)
            assert status_result["status"] == "completed"
            assert status_result["progress"] == 1.0
            
            # 4. Get final results
            results = await client.get_training_job_results(job_id)
            assert "final_metrics" in results
            assert "best_parameters" in results["final_metrics"]
            assert results["final_metrics"]["best_parameters"]["rsi_period"] == 18
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, sample_workflow_request, mock_successful_response):
        """Test handling of concurrent requests."""
        client = AIMLClient()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_successful_response
            
            # Make multiple concurrent requests
            tasks = [
                client.create_training_job_from_workflow(sample_workflow_request)
                for _ in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            for result in results:
                assert result["success"] is True
                assert result["job_id"] == "training_job_abc123"
            
            # Verify all requests were made
            assert mock_request.call_count == 5


class TestAIMLClientConfiguration:
    """Test configuration and initialization edge cases."""
    
    def test_invalid_base_url_handling(self):
        """Test handling of invalid base URLs."""
        with pytest.raises(ValueError):
            AIMLClient(base_url="invalid-url")
        
        with pytest.raises(ValueError):
            AIMLClient(base_url="")
    
    def test_negative_timeout_handling(self):
        """Test handling of negative timeout values."""
        with pytest.raises(ValueError):
            AIMLClient(timeout=-1.0)
    
    def test_invalid_retry_count(self):
        """Test handling of invalid retry counts."""
        with pytest.raises(ValueError):
            AIMLClient(max_retries=-1)
        
        with pytest.raises(ValueError):
            AIMLClient(max_retries=100)  # Too high
    
    @pytest.mark.asyncio
    async def test_client_cleanup(self):
        """Test proper client cleanup."""
        client = AIMLClient()
        
        # Use client
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True}
            await client.get_training_job_status("test-job")
        
        # Close client
        await client.close()
        
        # Verify client is properly closed
        # (In real implementation, this would check that HTTP connections are closed)
        assert client._client is None or client._client.is_closed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])