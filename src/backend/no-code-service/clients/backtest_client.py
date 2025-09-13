#!/usr/bin/env python3
"""
Backtest Service Client

Client for communicating with the backtest microservice.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class BacktestServiceError(Exception):
    """Exception raised when backtest service encounters an error."""
    pass


class BacktestServiceUnavailable(Exception):
    """Exception raised when backtest service is unavailable."""
    pass


class BacktestClient:
    """Client for the backtest microservice."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("BACKTEST_SERVICE_URL", "http://localhost:8007")
        self.timeout = 300.0  # 5 minutes timeout for backtests
    
    async def run_backtest(
        self, 
        workflow_id: str,
        strategy_code: str, 
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run backtest on the backtest service.
        
        Args:
            workflow_id: ID of the workflow
            strategy_code: Generated strategy code to backtest
            config: Backtest configuration
            metadata: Optional metadata
            
        Returns:
            Dictionary with backtest results
        """
        
        payload = {
            "workflow_id": workflow_id,
            "strategy_code": strategy_code,
            "config": config,
            "metadata": metadata or {}
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Sending backtest request to {self.base_url}/api/backtest/run")
                
                response = await client.post(
                    f"{self.base_url}/api/backtest/run",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Backtest completed for workflow {workflow_id}")
                    return result
                
                elif response.status_code == 400:
                    error_detail = response.json().get("detail", "Bad request")
                    logger.error(f"Backtest service bad request: {error_detail}")
                    raise BacktestServiceError(f"Invalid request: {error_detail}")
                
                elif response.status_code == 500:
                    error_detail = response.json().get("detail", "Internal server error")
                    logger.error(f"Backtest service internal error: {error_detail}")
                    raise BacktestServiceError(f"Service error: {error_detail}")
                
                else:
                    logger.error(f"Unexpected response status: {response.status_code}")
                    raise BacktestServiceError(f"Unexpected response: {response.status_code}")
                    
        except httpx.ConnectError:
            logger.error(f"Cannot connect to backtest service at {self.base_url}")
            raise BacktestServiceUnavailable(
                f"Backtest service unavailable at {self.base_url}"
            )
        
        except httpx.TimeoutException:
            logger.error(f"Backtest request timed out after {self.timeout} seconds")
            raise BacktestServiceError(
                f"Backtest timed out after {self.timeout} seconds"
            )
        
        except Exception as e:
            logger.error(f"Unexpected error calling backtest service: {str(e)}")
            raise BacktestServiceError(f"Unexpected error: {str(e)}")
    
    async def get_backtest_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a running backtest."""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/backtest/status/{execution_id}"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise BacktestServiceError(f"Status check failed: {response.status_code}")
                    
        except httpx.ConnectError:
            raise BacktestServiceUnavailable(f"Backtest service unavailable at {self.base_url}")
        except Exception as e:
            raise BacktestServiceError(f"Error getting status: {str(e)}")
    
    async def get_available_symbols(self) -> Dict[str, Any]:
        """Get list of available symbols for backtesting."""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/backtest/market-data/symbols"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise BacktestServiceError(f"Failed to get symbols: {response.status_code}")
                    
        except httpx.ConnectError:
            raise BacktestServiceUnavailable(f"Backtest service unavailable at {self.base_url}")
        except Exception as e:
            raise BacktestServiceError(f"Error getting symbols: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if backtest service is healthy."""
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False


# Convenience function for synchronous usage
def run_backtest_sync(
    workflow_id: str,
    strategy_code: str, 
    config: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    base_url: str = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for running backtest.
    
    Args:
        workflow_id: ID of the workflow
        strategy_code: Generated strategy code
        config: Backtest configuration
        metadata: Optional metadata
        base_url: Backtest service URL
        
    Returns:
        Dictionary with backtest results
    """
    
    client = BacktestClient(base_url)
    
    async def _run():
        return await client.run_backtest(workflow_id, strategy_code, config, metadata)
    
    # Run in asyncio loop
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_run())
    except RuntimeError:
        # If no loop is running, create a new one
        return asyncio.run(_run())


if __name__ == "__main__":
    # Demo usage
    print("🔗 Backtest Service Client")
    print("=" * 30)
    print("Features:")
    print("✅ Async backtest execution")
    print("✅ Status monitoring")
    print("✅ Error handling")
    print("✅ Health checks")
    print("✅ Symbol lookup")
    print("\nReady for backtest service communication! 📡")