"""
AI-ML Service HTTP Client

Handles HTTP communication with the ai-ml-strategy-service.
Implements circuit breaker pattern, retry logic, and comprehensive error handling.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import httpx
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"


class AIMLServiceError(Exception):
    """Base exception for AI-ML service communication"""
    pass


class AIMLServiceUnavailable(AIMLServiceError):
    """AI-ML service is unavailable"""
    pass


class AIMLAuthenticationError(AIMLServiceError):
    """Authentication failed with AI-ML service"""
    pass


class AIMLValidationError(AIMLServiceError):
    """Request validation failed"""
    pass


class CircuitBreaker:
    """Circuit breaker for AI-ML service calls"""
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = AIMLServiceError
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        
    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        return False
        
    def record_success(self):
        """Record successful execution"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class AIMLClient:
    """HTTP client for AI-ML strategy service"""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.circuit_breaker = CircuitBreaker()
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=self._get_default_headers()
        )
        
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'no-code-service/2.0.0'
        }
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
            
        return headers
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    def _check_circuit_breaker(self):
        """Check circuit breaker before execution"""
        if not self.circuit_breaker.can_execute():
            raise AIMLServiceUnavailable(
                f"Circuit breaker is {self.circuit_breaker.state.value}. "
                f"Service unavailable after {self.circuit_breaker.failure_count} failures."
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        self._check_circuit_breaker()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.info(f"Making {method} request to {url}")
            
            if method.upper() == 'GET':
                response = await self.client.get(url, params=params)
            elif method.upper() == 'POST':
                response = await self.client.post(url, json=data, params=params)
            elif method.upper() == 'PUT':
                response = await self.client.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = await self.client.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle different response status codes
            if response.status_code == 200:
                self.circuit_breaker.record_success()
                return response.json()
            elif response.status_code == 401:
                self.circuit_breaker.record_failure()
                raise AIMLAuthenticationError("Authentication failed with AI-ML service")
            elif response.status_code == 400:
                self.circuit_breaker.record_failure()
                error_detail = response.text
                raise AIMLValidationError(f"Request validation failed: {error_detail}")
            elif response.status_code == 404:
                self.circuit_breaker.record_failure()
                raise AIMLServiceError(f"Endpoint not found: {url}")
            elif response.status_code >= 500:
                self.circuit_breaker.record_failure()
                raise AIMLServiceUnavailable(f"AI-ML service error: {response.status_code}")
            else:
                self.circuit_breaker.record_failure()
                raise AIMLServiceError(f"Unexpected response: {response.status_code}")
                
        except httpx.RequestError as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Request error for {url}: {str(e)}")
            raise AIMLServiceUnavailable(f"Failed to connect to AI-ML service: {str(e)}")
        except httpx.TimeoutException:
            self.circuit_breaker.record_failure()
            logger.error(f"Timeout for {url}")
            raise AIMLServiceUnavailable("AI-ML service request timeout")
    
    async def create_training_job_from_workflow(
        self, 
        workflow_definition: Dict[str, Any],
        workflow_name: str,
        user_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create training job from workflow definition
        
        Args:
            workflow_definition: React Flow workflow data
            workflow_name: Name of the workflow
            user_id: User ID creating the job
            config: Additional configuration
            
        Returns:
            Training job response with job_id and status
        """
        try:
            payload = {
                'workflow_definition': workflow_definition,
                'workflow_name': workflow_name,
                'user_id': user_id,
                'generated_by': 'no_code_workflow',
                'optimization_target': 'profit'
            }
            
            if config:
                payload.update(config)
            
            logger.info(f"Creating training job for workflow: {workflow_name}")
            
            response = await self._make_request(
                'POST', 
                '/api/training/from-workflow',
                data=payload
            )
            
            logger.info(f"Training job created successfully: {response.get('training_job_id')}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create training job from workflow: {str(e)}")
            raise
    
    async def get_training_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get training job status
        
        Args:
            job_id: Training job ID
            
        Returns:
            Job status information
        """
        try:
            logger.info(f"Getting status for training job: {job_id}")
            
            response = await self._make_request(
                'GET',
                f'/api/training/jobs/{job_id}/status'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get training job status for {job_id}: {str(e)}")
            raise
    
    async def get_training_job_results(self, job_id: str) -> Dict[str, Any]:
        """
        Get training job results
        
        Args:
            job_id: Training job ID
            
        Returns:
            Training results and optimized parameters
        """
        try:
            logger.info(f"Getting results for training job: {job_id}")
            
            response = await self._make_request(
                'GET',
                f'/api/training/jobs/{job_id}/results'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get training job results for {job_id}: {str(e)}")
            raise
    
    async def cancel_training_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel training job
        
        Args:
            job_id: Training job ID
            
        Returns:
            Cancellation confirmation
        """
        try:
            logger.info(f"Cancelling training job: {job_id}")
            
            response = await self._make_request(
                'DELETE',
                f'/api/training/jobs/{job_id}'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to cancel training job {job_id}: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if AI-ML service is healthy
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self._make_request('GET', '/health')
            return response.get('status') == 'healthy'
        except Exception:
            return False

    async def start_hybrid_execution(self, workflow_definition: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a hybrid execution job."""
        payload = {"workflow_definition": workflow_definition, "config": config}
        return await self._make_request('POST', '/api/executions/hybrid', data=payload)

    async def start_backtest(self, workflow_definition: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a backtesting job."""
        payload = {"workflow_definition": workflow_definition, "config": config}
        return await self._make_request('POST', '/api/backtesting/from-workflow', data=payload)

    async def start_paper_trading(self, workflow_definition: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a paper trading job."""
        payload = {"workflow_definition": workflow_definition, "config": config}
        return await self._make_request('POST', '/api/paper-trading/from-workflow', data=payload)

    async def start_research_session(self, workflow_definition: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a research session."""
        payload = {"workflow_definition": workflow_definition, "config": config}
        return await self._make_request('POST', '/api/research/from-workflow', data=payload)