"""
Error scenario tests for network failures between services.
Tests handling of connection errors, timeouts, and service unavailability.
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json


@pytest.fixture
def sample_workflow_request():
    """Sample workflow request for testing."""
    return {
        "mode": "model",
        "config": {
            "optimization_objective": "sharpe_ratio",
            "max_trials": 50,
            "timeout_hours": 12,
            "instance_type": "CPU_MEDIUM",
            "priority": "high"
        }
    }

@pytest.fixture
def mock_workflow_data():
    """Mock workflow stored in database."""
    return {
        "id": 999,
        "user_id": "test_user_123",
        "name": "Network Test Strategy",
        "workflow_data": {
            "nodes": [
                {
                    "id": "data-1",
                    "type": "dataSource",
                    "data": {"symbol": "BTCUSDT", "timeframe": "1h"}
                },
                {
                    "id": "rsi-1",
                    "type": "technicalIndicator", 
                    "data": {"indicator": "rsi", "period": 14}
                },
                {
                    "id": "condition-1",
                    "type": "condition",
                    "data": {"threshold": 30, "operator": "<"}
                },
                {
                    "id": "action-1",
                    "type": "action",
                    "data": {"action": "buy", "quantity": 100}
                }
            ],
            "edges": [
                {"source": "data-1", "target": "rsi-1"},
                {"source": "rsi-1", "target": "condition-1"},
                {"source": "condition-1", "target": "action-1"}
            ]
        }
    }


class TestNetworkFailureScenarios:
    """Test network failure scenarios between no-code and AI-ML services."""
    
    @pytest.mark.asyncio
    async def test_connection_refused_error(self, sample_workflow_request, mock_workflow_data):
        """Test handling when AI-ML service connection is refused."""
        workflow_id = mock_workflow_data["id"]
        
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Import and test the actual client
            from clients.aiml_client import AIMLClient
            
            client = AIMLClient(base_url="http://localhost:8002")
            
            # Should handle connection error gracefully
            result = await client.create_training_job_from_workflow(
                workflow_id=workflow_id,
                workflow_name="Test Strategy",
                workflow_definition=mock_workflow_data["workflow_data"],
                training_config={},
                optimization_objective="sharpe_ratio",
                max_trials=50,
                instance_type="cpu_medium",
                timeout_hours=12,
                priority="normal"
            )
            
            # Should return error response
            assert result["success"] is False
            assert "Connection refused" in result["error"]
            assert result["error_type"] == "connection_error"
            assert "retry_after_seconds" in result
            assert result["retry_after_seconds"] > 0
    
    @pytest.mark.asyncio
    async def test_timeout_error_with_retry(self, sample_workflow_request):
        """Test handling of timeout errors with retry logic."""
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            
            # First two calls timeout, third succeeds
            mock_response = Mock()
            mock_response.json.return_value = {
                "success": True,
                "job_id": "retry_success_job_123",
                "status": "queued"
            }
            mock_response.status_code = 201
            mock_response.raise_for_status = Mock()
            
            mock_client.post.side_effect = [
                httpx.TimeoutException("Request timed out after 30s"),
                httpx.TimeoutException("Request timed out after 30s"),
                mock_response  # Third attempt succeeds
            ]
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="http://localhost:8002")
            
            result = await client.create_training_job_from_workflow(
                workflow_id=999,
                workflow_name="Timeout Test Strategy",
                workflow_definition={},
                training_config={},
                optimization_objective="sharpe_ratio",
                max_trials=50
            )
            
            # Should eventually succeed after retries
            assert result["success"] is True
            assert result["job_id"] == "retry_success_job_123"
            assert result["status"] == "queued"
            
            # Verify retry attempts were made
            assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_persistent_timeout_failure(self):
        """Test handling when all retry attempts fail due to timeout."""
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="http://localhost:8002")
            
            result = await client.create_training_job_from_workflow(
                workflow_id=999,
                workflow_name="Persistent Timeout Test",
                workflow_definition={}
            )
            
            # Should fail after all retries exhausted
            assert result["success"] is False
            assert "Request timed out" in result["error"]
            assert result["error_type"] == "timeout_error"
            assert "max_retries_reached" in result
            assert result["max_retries_reached"] is True
            
            # Should have attempted maximum retries (3)
            assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Name or service not known")
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="http://nonexistent-service.local:8002")
            
            result = await client.get_training_job_status("test_job_123")
            
            assert result["success"] is False
            assert "Name or service not known" in result["error"]
            assert result["error_type"] == "dns_error"
    
    @pytest.mark.asyncio
    async def test_ssl_certificate_error(self):
        """Test handling of SSL certificate errors."""
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.SSLError("SSL certificate verification failed")
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="https://secure-service.example.com")
            
            result = await client.get_training_job_status("ssl_test_job")
            
            assert result["success"] is False
            assert "SSL certificate verification failed" in result["error"]
            assert result["error_type"] == "ssl_error"
    
    @pytest.mark.asyncio
    async def test_network_unreachable_error(self):
        """Test handling of network unreachable errors."""
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Network unreachable")
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="http://10.0.0.1:8002")
            
            result = await client.create_training_job_from_workflow(
                workflow_id=123,
                workflow_name="Network Unreachable Test",
                workflow_definition={}
            )
            
            assert result["success"] is False
            assert "Network unreachable" in result["error"]
            assert result["error_type"] == "network_error"
    
    @pytest.mark.asyncio
    async def test_partial_response_error(self):
        """Test handling of partial/corrupted response data."""
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            
            # Mock corrupted response
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
            mock_response.status_code = 200
            mock_response.text = "Partial response data..."
            mock_response.raise_for_status = Mock()
            mock_client.post.return_value = mock_response
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="http://localhost:8002")
            
            result = await client.create_training_job_from_workflow(
                workflow_id=456,
                workflow_name="Partial Response Test",
                workflow_definition={}
            )
            
            assert result["success"] is False
            assert "Failed to parse response JSON" in result["error"]
            assert result["error_type"] == "response_parsing_error"
            assert "raw_response" in result
            assert result["raw_response"] == "Partial response data..."


class TestCircuitBreakerScenarios:
    """Test circuit breaker behavior under various failure conditions."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test that circuit breaker opens after consecutive failures."""
        failure_threshold = 3
        
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection failed")
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="http://localhost:8002", 
                              circuit_breaker_failure_threshold=failure_threshold)
            
            results = []
            
            # Make multiple failing requests to trip circuit breaker
            for i in range(failure_threshold + 2):
                result = await client.create_training_job_from_workflow(
                    workflow_id=i,
                    workflow_name=f"CB Test {i}",
                    workflow_definition={}
                )
                results.append(result)
                
                # Small delay between requests
                await asyncio.sleep(0.1)
            
            # First 3 requests should fail with connection error
            for i in range(failure_threshold):
                assert results[i]["success"] is False
                assert "Connection failed" in results[i]["error"]
            
            # Subsequent requests should fail with circuit breaker open error
            for i in range(failure_threshold, len(results)):
                assert results[i]["success"] is False
                assert results[i]["error_type"] == "circuit_breaker_open"
                assert "Circuit breaker is open" in results[i]["error"]
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery to half-open state."""
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            
            # First request fails, second succeeds for recovery test
            mock_success_response = Mock()
            mock_success_response.json.return_value = {
                "success": True,
                "job_id": "recovery_test_job",
                "status": "queued"
            }
            mock_success_response.status_code = 201
            mock_success_response.raise_for_status = Mock()
            
            mock_client.post.side_effect = [
                httpx.ConnectError("Initial failure"),  # Trip the breaker
                httpx.ConnectError("Second failure"),
                httpx.ConnectError("Third failure"),  # Now breaker is open
                mock_success_response  # Recovery attempt succeeds
            ]
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="http://localhost:8002",
                              circuit_breaker_failure_threshold=3,
                              circuit_breaker_recovery_timeout=1)  # 1 second recovery
            
            # Trip the circuit breaker
            for i in range(3):
                await client.create_training_job_from_workflow(
                    workflow_id=i, workflow_name=f"Trip {i}", workflow_definition={}
                )
            
            # Wait for recovery timeout
            await asyncio.sleep(1.2)
            
            # Next request should attempt recovery
            result = await client.create_training_job_from_workflow(
                workflow_id=999,
                workflow_name="Recovery Test",
                workflow_definition={}
            )
            
            # Should succeed and close the circuit breaker
            assert result["success"] is True
            assert result["job_id"] == "recovery_test_job"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_mixed_endpoints(self):
        """Test circuit breaker behavior across different endpoints."""
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            
            # Create job fails, but status check succeeds
            mock_success_response = Mock()
            mock_success_response.json.return_value = {
                "job_id": "test_job",
                "status": "running",
                "progress": 0.5
            }
            mock_success_response.status_code = 200
            mock_success_response.raise_for_status = Mock()
            
            mock_client.post.side_effect = httpx.ConnectError("Create job failed")
            mock_client.get.return_value = mock_success_response
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="http://localhost:8002")
            
            # Create job should fail
            create_result = await client.create_training_job_from_workflow(
                workflow_id=123,
                workflow_name="Mixed Test",
                workflow_definition={}
            )
            assert create_result["success"] is False
            
            # Status check should still work (different endpoint)
            status_result = await client.get_training_job_status("test_job")
            assert status_result["success"] is True
            assert status_result["status"] == "running"


class TestServiceUnavailabilityScenarios:
    """Test scenarios when AI-ML service is completely unavailable."""
    
    @pytest.mark.asyncio
    async def test_service_down_graceful_degradation(self, mock_workflow_data):
        """Test graceful degradation when AI-ML service is down."""
        workflow_id = mock_workflow_data["id"]
        
        # Mock the execution mode endpoint from no-code service
        with patch('main.get_workflow_from_db') as mock_get_workflow:
            mock_get_workflow.return_value = mock_workflow_data
            
            with patch('main.AIMLClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.create_training_job_from_workflow.return_value = {
                    "success": False,
                    "error": "AI-ML service is currently unavailable",
                    "error_type": "service_unavailable"
                }
                mock_client_class.return_value = mock_client
                
                # Test the execution mode endpoint
                request_data = {
                    "mode": "model",
                    "config": {"max_trials": 50}
                }
                
                # Simulate API call (would normally be HTTP request)
                result = await self._simulate_execution_mode_call(
                    workflow_id, request_data, mock_workflow_data["user_id"]
                )
                
                # Should handle service unavailability gracefully
                assert result["success"] is False
                assert "AI-ML service is currently unavailable" in result["error"]
                assert result["fallback_mode"] == "strategy"
                assert "strategy_code" in result  # Fallback to strategy generation
                assert result["next_action"] == "execute_strategy_fallback"
    
    @pytest.mark.asyncio
    async def test_service_maintenance_mode(self):
        """Test handling of service maintenance mode."""
        with patch('clients.aiml_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            
            # Mock maintenance mode response
            mock_response = Mock()
            mock_response.json.return_value = {
                "error": "Service temporarily unavailable for maintenance",
                "maintenance_window": {
                    "start": "2025-08-08T10:00:00Z",
                    "end": "2025-08-08T12:00:00Z",
                    "estimated_completion": "2025-08-08T11:30:00Z"
                },
                "retry_after": 3600
            }
            mock_response.status_code = 503
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "503 Service Unavailable", request=Mock(), response=mock_response
            )
            mock_client.post.return_value = mock_response
            
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from clients.aiml_client import AIMLClient
            client = AIMLClient(base_url="http://localhost:8002")
            
            result = await client.create_training_job_from_workflow(
                workflow_id=789,
                workflow_name="Maintenance Test",
                workflow_definition={}
            )
            
            assert result["success"] is False
            assert result["error_type"] == "service_maintenance"
            assert "Service temporarily unavailable for maintenance" in result["error"]
            assert "maintenance_window" in result
            assert result["retry_after_seconds"] == 3600
    
    @pytest.mark.asyncio
    async def test_cascading_service_failures(self):
        """Test handling of cascading failures across multiple services."""
        # Simulate database unavailable AND AI-ML service unavailable
        with patch('main.get_workflow_from_db') as mock_get_workflow:
            mock_get_workflow.side_effect = Exception("Database connection failed")
            
            # Even if AI-ML service is available, should fail gracefully
            result = await self._simulate_execution_mode_call(
                999, {"mode": "model"}, "test_user"
            )
            
            assert result["success"] is False
            assert "Database connection failed" in result["error"]
            assert result["error_type"] == "database_error"
            assert "retry_strategy" in result
            assert result["retry_strategy"] == "exponential_backoff"
    
    # Helper methods
    
    async def _simulate_execution_mode_call(self, workflow_id, request_data, user_id):
        """Simulate execution mode API call for testing."""
        try:
            # This would normally be the actual endpoint logic
            workflow = await self._get_workflow_from_db(workflow_id)
            
            if request_data["mode"] == "model":
                # Try to create training job
                aiml_client = self._get_aiml_client()
                result = await aiml_client.create_training_job_from_workflow(
                    workflow_id=workflow_id,
                    workflow_name=workflow["name"],
                    workflow_definition=workflow["workflow_data"]
                )
                
                if result["success"]:
                    return {
                        "success": True,
                        "execution_mode": "model",
                        "training_job_id": result["job_id"],
                        "next_action": "monitor_training"
                    }
                else:
                    # Fallback to strategy mode
                    return {
                        "success": False,
                        "error": result["error"],
                        "fallback_mode": "strategy",
                        "strategy_code": "# Fallback strategy code",
                        "next_action": "execute_strategy_fallback"
                    }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "database_error" if "Database" in str(e) else "unknown_error",
                "retry_strategy": "exponential_backoff"
            }
    
    async def _get_workflow_from_db(self, workflow_id):
        """Mock database workflow retrieval."""
        # This would normally query the actual database
        raise Exception("Database connection failed")
    
    def _get_aiml_client(self):
        """Mock AI-ML client creation."""
        from clients.aiml_client import AIMLClient
        return AIMLClient(base_url="http://localhost:8002")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])