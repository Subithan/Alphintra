"""
Inference engine for executing trading strategies and generating signals.
"""

import asyncio
import sys
import tempfile
import subprocess
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor, Future
import json
import traceback

import structlog
import numpy as np
import pandas as pd

from app.models.strategies import StrategyPackage, StrategySource, StrategyStatus, ExecutionMode
from app.models.signals import TradingSignal, SignalAction, ExecutionParams, MarketConditions
from app.models.market_data import OHLCV, Timeframe
from app.services.strategy_loader import StrategyLoader
from app.services.market_data_client import MarketDataClient
from app.services.signal_distributor import SignalDistributor
from app.utils.sandbox import StrategySandbox

logger = structlog.get_logger(__name__)


class StrategyExecutionError(Exception):
    """Strategy execution error."""
    pass


class InferenceEngine:
    """Main inference engine for strategy execution."""
    
    def __init__(self, strategy_loader: StrategyLoader, 
                 market_data_client: MarketDataClient,
                 signal_distributor: SignalDistributor):
        
        self.strategy_loader = strategy_loader
        self.market_data_client = market_data_client
        self.signal_distributor = signal_distributor
        
        # Active strategy executions
        self.active_strategies: Dict[str, Dict[str, Any]] = {}
        self.execution_tasks: Dict[str, asyncio.Task] = {}
        
        # Thread pool for CPU-intensive strategy execution
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Strategy sandboxes
        self.sandboxes: Dict[str, StrategySandbox] = {}
        
        # Configuration
        self.max_concurrent_strategies = 10
        self.strategy_timeout_seconds = 30
        self.signal_cooldown_seconds = 60
        
        # Metrics
        self.execution_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "signals_generated": 0,
            "average_execution_time": 0.0
        }
        
        # Last signal timestamps to prevent spam
        self.last_signal_times: Dict[str, datetime] = {}
    
    async def initialize(self) -> None:
        """Initialize the inference engine."""
        try:
            # Start background tasks
            asyncio.create_task(self._cleanup_task())
            asyncio.create_task(self._metrics_task())
            
            logger.info("Inference engine initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize inference engine", error=str(e))
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the inference engine."""
        try:
            # Stop all running strategies
            await self.stop_all_strategies()
            
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            # Cleanup sandboxes
            for sandbox in self.sandboxes.values():
                await sandbox.cleanup()
            self.sandboxes.clear()
            
            logger.info("Inference engine shutdown completed")
            
        except Exception as e:
            logger.error("Error during inference engine shutdown", error=str(e))
    
    async def start_strategy(self, strategy_id: str, source: StrategySource,
                           configuration: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start executing a strategy.
        
        Args:
            strategy_id: Strategy identifier
            source: Strategy source
            configuration: Execution configuration
            
        Returns:
            Execution result
        """
        execution_id = str(uuid.uuid4())
        
        try:
            # Check if strategy is already running
            if strategy_id in self.active_strategies:
                return {
                    "success": False,
                    "error": "Strategy is already running",
                    "execution_id": self.active_strategies[strategy_id]["execution_id"]
                }
            
            # Check concurrent strategy limit
            if len(self.active_strategies) >= self.max_concurrent_strategies:
                return {
                    "success": False,
                    "error": "Maximum concurrent strategies reached",
                    "max_concurrent": self.max_concurrent_strategies
                }
            
            # Load strategy
            strategy_package = await self.strategy_loader.load_strategy(
                strategy_id, source, force_reload=True
            )
            
            # Create sandbox
            sandbox = StrategySandbox(strategy_package)
            await sandbox.initialize()
            self.sandboxes[execution_id] = sandbox
            
            # Prepare execution context
            execution_context = {
                "execution_id": execution_id,
                "strategy_id": strategy_id,
                "source": source,
                "strategy_package": strategy_package,
                "configuration": configuration,
                "status": StrategyStatus.LOADING,
                "started_at": datetime.utcnow(),
                "last_execution": None,
                "signals_generated": 0,
                "errors": [],
                "sandbox": sandbox
            }
            
            self.active_strategies[strategy_id] = execution_context
            
            # Start execution task
            task = asyncio.create_task(
                self._strategy_execution_loop(execution_context)
            )
            self.execution_tasks[execution_id] = task
            
            logger.info("Strategy execution started",
                       strategy_id=strategy_id, execution_id=execution_id)
            
            return {
                "success": True,
                "execution_id": execution_id,
                "strategy_name": strategy_package.name,
                "status": "starting"
            }
            
        except Exception as e:
            logger.error("Failed to start strategy execution",
                        strategy_id=strategy_id, error=str(e))
            
            # Cleanup on failure
            if execution_id in self.sandboxes:
                await self.sandboxes[execution_id].cleanup()
                del self.sandboxes[execution_id]
            
            if strategy_id in self.active_strategies:
                del self.active_strategies[strategy_id]
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stop_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Stop executing a strategy."""
        try:
            if strategy_id not in self.active_strategies:
                return {
                    "success": False,
                    "error": "Strategy is not running"
                }
            
            execution_context = self.active_strategies[strategy_id]
            execution_id = execution_context["execution_id"]
            
            # Cancel execution task
            if execution_id in self.execution_tasks:
                task = self.execution_tasks[execution_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.execution_tasks[execution_id]
            
            # Cleanup sandbox
            if execution_id in self.sandboxes:
                await self.sandboxes[execution_id].cleanup()
                del self.sandboxes[execution_id]
            
            # Remove from active strategies
            del self.active_strategies[strategy_id]
            
            logger.info("Strategy execution stopped", 
                       strategy_id=strategy_id, execution_id=execution_id)
            
            return {
                "success": True,
                "execution_id": execution_id,
                "stopped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to stop strategy execution",
                        strategy_id=strategy_id, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stop_all_strategies(self) -> None:
        """Stop all running strategies."""
        strategy_ids = list(self.active_strategies.keys())
        for strategy_id in strategy_ids:
            await self.stop_strategy(strategy_id)
    
    async def get_strategy_status(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get current strategy execution status."""
        if strategy_id not in self.active_strategies:
            return None
        
        context = self.active_strategies[strategy_id]
        return {
            "execution_id": context["execution_id"],
            "strategy_id": strategy_id,
            "status": context["status"].value,
            "started_at": context["started_at"].isoformat(),
            "last_execution": context["last_execution"].isoformat() if context["last_execution"] else None,
            "signals_generated": context["signals_generated"],
            "error_count": len(context["errors"]),
            "last_error": context["errors"][-1] if context["errors"] else None
        }
    
    async def list_active_strategies(self) -> List[Dict[str, Any]]:
        """List all active strategy executions."""
        return [
            await self.get_strategy_status(strategy_id)
            for strategy_id in self.active_strategies.keys()
        ]
    
    async def _strategy_execution_loop(self, execution_context: Dict[str, Any]) -> None:
        """Main execution loop for a strategy."""
        strategy_id = execution_context["strategy_id"]
        execution_id = execution_context["execution_id"]
        configuration = execution_context["configuration"]
        sandbox = execution_context["sandbox"]
        
        try:
            execution_context["status"] = StrategyStatus.ACTIVE
            
            # Get execution parameters
            symbols = configuration.get("symbols", ["BTCUSDT"])
            timeframe = configuration.get("timeframe", "1h")
            execution_interval = configuration.get("execution_interval", 300)  # 5 minutes
            
            logger.info("Starting strategy execution loop",
                       strategy_id=strategy_id, symbols=symbols, timeframe=timeframe)
            
            while execution_context["status"] == StrategyStatus.ACTIVE:
                try:
                    # Execute strategy
                    signals = await self._execute_strategy(
                        execution_context, symbols, timeframe
                    )
                    
                    # Process generated signals
                    if signals:
                        await self._process_signals(execution_context, signals)
                    
                    execution_context["last_execution"] = datetime.utcnow()
                    
                    # Wait for next execution
                    await asyncio.sleep(execution_interval)
                    
                except asyncio.CancelledError:
                    logger.info("Strategy execution cancelled", strategy_id=strategy_id)
                    break
                    
                except Exception as e:
                    error_msg = f"Strategy execution error: {str(e)}"
                    execution_context["errors"].append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": error_msg,
                        "traceback": traceback.format_exc()
                    })
                    
                    logger.error("Strategy execution error",
                               strategy_id=strategy_id, error=error_msg)
                    
                    # Continue execution unless too many errors
                    if len(execution_context["errors"]) > 10:
                        execution_context["status"] = StrategyStatus.ERROR
                        break
                    
                    # Wait before retry
                    await asyncio.sleep(30)
        
        except Exception as e:
            execution_context["status"] = StrategyStatus.ERROR
            logger.error("Fatal error in strategy execution loop",
                        strategy_id=strategy_id, error=str(e))
        
        finally:
            # Cleanup will be handled by stop_strategy
            pass
    
    async def _execute_strategy(self, execution_context: Dict[str, Any],
                              symbols: List[str], timeframe: str) -> List[TradingSignal]:
        """Execute strategy and return generated signals."""
        start_time = time.time()
        
        try:
            # Get market data
            market_data = await self.market_data_client.get_historical_data(
                symbols=symbols,
                timeframe=timeframe,
                limit=200  # Sufficient for most technical indicators
            )
            
            # Execute strategy in sandbox
            sandbox = execution_context["sandbox"]
            signals = await sandbox.execute_strategy(
                market_data=market_data,
                parameters=execution_context["configuration"].get("parameters", {})
            )
            
            # Update metrics
            execution_time = time.time() - start_time
            self.execution_metrics["total_executions"] += 1
            self.execution_metrics["successful_executions"] += 1
            
            # Update average execution time
            current_avg = self.execution_metrics["average_execution_time"]
            total_executions = self.execution_metrics["total_executions"]
            self.execution_metrics["average_execution_time"] = (
                (current_avg * (total_executions - 1) + execution_time) / total_executions
            )
            
            return signals or []
            
        except Exception as e:
            self.execution_metrics["total_executions"] += 1
            self.execution_metrics["failed_executions"] += 1
            raise StrategyExecutionError(f"Strategy execution failed: {e}")
    
    async def _process_signals(self, execution_context: Dict[str, Any],
                             signals: List[TradingSignal]) -> None:
        """Process and distribute generated signals."""
        strategy_id = execution_context["strategy_id"]
        
        for signal in signals:
            try:
                # Check signal cooldown
                if self._is_signal_in_cooldown(strategy_id, signal.symbol):
                    logger.debug("Signal in cooldown, skipping",
                               strategy_id=strategy_id, symbol=signal.symbol)
                    continue
                
                # Validate signal
                if not self._validate_signal(signal):
                    logger.warning("Invalid signal generated, skipping",
                                 strategy_id=strategy_id, signal_id=signal.signal_id)
                    continue
                
                # Enhance signal with metadata
                signal.strategy_id = strategy_id
                signal.strategy_source = execution_context["source"].value
                signal.timestamp = datetime.utcnow()
                
                # Distribute signal
                await self.signal_distributor.distribute_signal(signal)
                
                # Update metrics and state
                execution_context["signals_generated"] += 1
                self.execution_metrics["signals_generated"] += 1
                self.last_signal_times[f"{strategy_id}:{signal.symbol}"] = datetime.utcnow()
                
                logger.info("Signal generated and distributed",
                          strategy_id=strategy_id, signal_id=signal.signal_id,
                          symbol=signal.symbol, action=signal.action.value)
                
            except Exception as e:
                logger.error("Failed to process signal",
                           strategy_id=strategy_id, error=str(e))
    
    def _is_signal_in_cooldown(self, strategy_id: str, symbol: str) -> bool:
        """Check if signal is in cooldown period."""
        key = f"{strategy_id}:{symbol}"
        last_signal_time = self.last_signal_times.get(key)
        
        if not last_signal_time:
            return False
        
        time_diff = (datetime.utcnow() - last_signal_time).total_seconds()
        return time_diff < self.signal_cooldown_seconds
    
    def _validate_signal(self, signal: TradingSignal) -> bool:
        """Validate signal before distribution."""
        try:
            # Basic validation
            if not signal.symbol or not signal.action:
                return False
            
            if not (0 <= signal.confidence <= 1):
                return False
            
            if not (0 <= signal.risk_score <= 1):
                return False
            
            # Execution parameters validation
            if signal.execution_params.quantity <= 0:
                return False
            
            # Price validation
            if signal.current_price and signal.current_price <= 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def _cleanup_task(self) -> None:
        """Background task for periodic cleanup."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up old signal cooldown entries
                current_time = datetime.utcnow()
                expired_keys = [
                    key for key, timestamp in self.last_signal_times.items()
                    if (current_time - timestamp).total_seconds() > self.signal_cooldown_seconds * 2
                ]
                
                for key in expired_keys:
                    del self.last_signal_times[key]
                
                logger.debug(f"Cleaned up {len(expired_keys)} expired signal cooldown entries")
                
            except Exception as e:
                logger.error("Error in cleanup task", error=str(e))
    
    async def _metrics_task(self) -> None:
        """Background task for metrics reporting."""
        while True:
            try:
                await asyncio.sleep(60)  # Report every minute
                
                logger.info("Inference engine metrics",
                          **self.execution_metrics,
                          active_strategies=len(self.active_strategies))
                
            except Exception as e:
                logger.error("Error in metrics task", error=str(e))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            **self.execution_metrics,
            "active_strategies": len(self.active_strategies),
            "active_sandboxes": len(self.sandboxes),
            "signal_cooldowns": len(self.last_signal_times)
        }