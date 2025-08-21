"""
Strategy orchestration service for managing multiple strategy executions.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.execution import (
    StrategyExecution,
    ExecutionEnvironment,
    ExecutionSignal,
    ExecutionOrder,
    ExecutionPosition,
    ExecutionStatus
)
from app.models.strategy import Strategy
from app.services.live_execution_engine import live_execution_engine, SignalData
from app.services.broker_integration import broker_integration_service
from app.services.market_data_service import market_data_service
from app.services.risk_manager import risk_manager
from app.database.connection import get_db_session


class OrchestrationMode(Enum):
    STANDALONE = "standalone"  # Each strategy runs independently
    PORTFOLIO = "portfolio"    # Strategies coordinate for portfolio optimization
    COMPETITIVE = "competitive"  # Strategies compete for capital allocation


@dataclass
class StrategyAllocation:
    """Capital allocation for a strategy."""
    strategy_execution_id: int
    allocated_capital: Decimal
    max_allocation_pct: Decimal
    current_allocation_pct: Decimal
    performance_score: Decimal
    risk_score: Decimal


@dataclass
class OrchestrationMetrics:
    """Orchestration performance metrics."""
    total_strategies: int
    active_strategies: int
    total_allocated_capital: Decimal
    total_portfolio_value: Decimal
    portfolio_return: Decimal
    portfolio_return_pct: Decimal
    sharpe_ratio: Optional[Decimal]
    max_drawdown_pct: Decimal
    diversification_score: Decimal


class StrategyOrchestrator:
    """Orchestrates multiple strategy executions with portfolio management."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Orchestration state
        self.active_orchestrations: Dict[str, Dict] = {}
        self.strategy_allocations: Dict[int, StrategyAllocation] = {}
        
        # Portfolio management
        self.portfolio_managers: Dict[str, Any] = {}
        self.rebalance_schedules: Dict[str, datetime] = {}
        
        # Performance tracking
        self.orchestration_metrics: Dict[str, OrchestrationMetrics] = {}
        
        # Configuration
        self.orchestrator_running = False
        self.rebalance_interval_hours = 24  # Daily rebalancing
        self.min_allocation_pct = Decimal("0.01")  # 1% minimum allocation
        self.max_strategies_per_portfolio = 10
        
    async def initialize(self) -> None:
        """Initialize the strategy orchestrator."""
        
        # Load active orchestrations
        await self._load_active_orchestrations()
        
        # Start orchestration loops
        if not self.orchestrator_running:
            self.orchestrator_running = True
            asyncio.create_task(self._orchestration_monitoring_loop())
            asyncio.create_task(self._portfolio_rebalancing_loop())
            asyncio.create_task(self._performance_tracking_loop())
        
        self.logger.info("Strategy orchestrator initialized")
    
    async def _load_active_orchestrations(self) -> None:
        """Load active orchestrations from database."""
        
        try:
            with get_db_session() as db:
                # Group active executions by environment
                active_executions = db.query(StrategyExecution).filter(
                    StrategyExecution.status == ExecutionStatus.RUNNING.value
                ).all()
                
                # Group by environment for portfolio management
                environment_groups = defaultdict(list)
                for execution in active_executions:
                    environment_groups[execution.environment_id].append(execution)
                
                # Create orchestration contexts
                for env_id, executions in environment_groups.items():
                    if len(executions) > 1:
                        # Multiple strategies in same environment - create portfolio
                        orchestration_id = f"portfolio_{env_id}"
                        await self._create_portfolio_orchestration(orchestration_id, executions)
                    else:
                        # Single strategy - standalone mode
                        orchestration_id = f"standalone_{executions[0].id}"
                        await self._create_standalone_orchestration(orchestration_id, executions[0])
                
            self.logger.info(f"Loaded {len(self.active_orchestrations)} orchestrations")
            
        except Exception as e:
            self.logger.error(f"Error loading active orchestrations: {e}")
    
    async def _create_portfolio_orchestration(self, orchestration_id: str, executions: List[StrategyExecution]) -> None:
        """Create a portfolio orchestration for multiple strategies."""
        
        try:
            # Calculate total allocated capital
            total_capital = sum(exec.allocated_capital for exec in executions)
            
            # Initialize strategy allocations
            for execution in executions:
                allocation_pct = (execution.allocated_capital / total_capital) * 100
                
                self.strategy_allocations[execution.id] = StrategyAllocation(
                    strategy_execution_id=execution.id,
                    allocated_capital=execution.allocated_capital,
                    max_allocation_pct=Decimal("50.0"),  # Default 50% max allocation
                    current_allocation_pct=allocation_pct,
                    performance_score=Decimal("0.0"),
                    risk_score=Decimal("0.0")
                )
            
            # Create orchestration context
            self.active_orchestrations[orchestration_id] = {
                "mode": OrchestrationMode.PORTFOLIO,
                "environment_id": executions[0].environment_id,
                "strategy_executions": {exec.id: exec for exec in executions},
                "total_capital": total_capital,
                "rebalance_enabled": True,
                "last_rebalance": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            
            # Schedule next rebalance
            self.rebalance_schedules[orchestration_id] = datetime.utcnow() + timedelta(hours=self.rebalance_interval_hours)
            
            self.logger.info(f"Created portfolio orchestration {orchestration_id} with {len(executions)} strategies")
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio orchestration: {e}")
    
    async def _create_standalone_orchestration(self, orchestration_id: str, execution: StrategyExecution) -> None:
        """Create a standalone orchestration for a single strategy."""
        
        try:
            self.active_orchestrations[orchestration_id] = {
                "mode": OrchestrationMode.STANDALONE,
                "environment_id": execution.environment_id,
                "strategy_executions": {execution.id: execution},
                "total_capital": execution.allocated_capital,
                "rebalance_enabled": False,
                "created_at": datetime.utcnow()
            }
            
            self.logger.info(f"Created standalone orchestration {orchestration_id}")
            
        except Exception as e:
            self.logger.error(f"Error creating standalone orchestration: {e}")
    
    async def start_orchestration(self, orchestration_id: str) -> bool:
        """Start an orchestration."""
        
        try:
            orchestration = self.active_orchestrations.get(orchestration_id)
            if not orchestration:
                raise ValueError(f"Orchestration {orchestration_id} not found")
            
            # Start all strategy executions
            success_count = 0
            for execution_id in orchestration["strategy_executions"]:
                success = await live_execution_engine.start_execution(execution_id)
                if success:
                    success_count += 1
            
            if success_count > 0:
                orchestration["status"] = "running"
                orchestration["started_at"] = datetime.utcnow()
                self.logger.info(f"Started orchestration {orchestration_id} with {success_count} strategies")
                return True
            else:
                raise Exception("Failed to start any strategies")
                
        except Exception as e:
            self.logger.error(f"Error starting orchestration {orchestration_id}: {e}")
            return False
    
    async def stop_orchestration(self, orchestration_id: str) -> bool:
        """Stop an orchestration."""
        
        try:
            orchestration = self.active_orchestrations.get(orchestration_id)
            if not orchestration:
                raise ValueError(f"Orchestration {orchestration_id} not found")
            
            # Stop all strategy executions
            for execution_id in orchestration["strategy_executions"]:
                await live_execution_engine.stop_execution(execution_id)
            
            orchestration["status"] = "stopped"
            orchestration["stopped_at"] = datetime.utcnow()
            
            # Remove from active orchestrations
            del self.active_orchestrations[orchestration_id]
            
            # Clean up rebalance schedule
            if orchestration_id in self.rebalance_schedules:
                del self.rebalance_schedules[orchestration_id]
            
            self.logger.info(f"Stopped orchestration {orchestration_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping orchestration {orchestration_id}: {e}")
            return False
    
    async def add_strategy_to_orchestration(
        self, 
        orchestration_id: str, 
        strategy_execution: StrategyExecution,
        allocation_pct: Optional[Decimal] = None
    ) -> bool:
        """Add a strategy to an existing orchestration."""
        
        try:
            orchestration = self.active_orchestrations.get(orchestration_id)
            if not orchestration:
                raise ValueError(f"Orchestration {orchestration_id} not found")
            
            # Check strategy limit
            if len(orchestration["strategy_executions"]) >= self.max_strategies_per_portfolio:
                raise ValueError("Maximum strategies per portfolio exceeded")
            
            # Add strategy to orchestration
            orchestration["strategy_executions"][strategy_execution.id] = strategy_execution
            
            # Update capital allocation
            if allocation_pct:
                new_allocation = orchestration["total_capital"] * (allocation_pct / 100)
                
                # Create allocation record
                self.strategy_allocations[strategy_execution.id] = StrategyAllocation(
                    strategy_execution_id=strategy_execution.id,
                    allocated_capital=new_allocation,
                    max_allocation_pct=Decimal("50.0"),
                    current_allocation_pct=allocation_pct,
                    performance_score=Decimal("0.0"),
                    risk_score=Decimal("0.0")
                )
                
                # Rebalance existing allocations
                await self._rebalance_portfolio(orchestration_id)
            
            self.logger.info(f"Added strategy {strategy_execution.id} to orchestration {orchestration_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding strategy to orchestration: {e}")
            return False
    
    async def remove_strategy_from_orchestration(
        self, 
        orchestration_id: str, 
        strategy_execution_id: int
    ) -> bool:
        """Remove a strategy from an orchestration."""
        
        try:
            orchestration = self.active_orchestrations.get(orchestration_id)
            if not orchestration:
                raise ValueError(f"Orchestration {orchestration_id} not found")
            
            if strategy_execution_id not in orchestration["strategy_executions"]:
                raise ValueError("Strategy not found in orchestration")
            
            # Stop the strategy execution
            await live_execution_engine.stop_execution(strategy_execution_id)
            
            # Remove from orchestration
            del orchestration["strategy_executions"][strategy_execution_id]
            
            # Remove allocation
            if strategy_execution_id in self.strategy_allocations:
                del self.strategy_allocations[strategy_execution_id]
            
            # Rebalance remaining strategies
            if len(orchestration["strategy_executions"]) > 1:
                await self._rebalance_portfolio(orchestration_id)
            
            self.logger.info(f"Removed strategy {strategy_execution_id} from orchestration {orchestration_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing strategy from orchestration: {e}")
            return False
    
    async def _orchestration_monitoring_loop(self) -> None:
        """Main orchestration monitoring loop."""
        
        while self.orchestrator_running:
            try:
                for orchestration_id in list(self.active_orchestrations.keys()):
                    await self._monitor_orchestration(orchestration_id)
                
                await asyncio.sleep(30.0)  # Monitor every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in orchestration monitoring loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _monitor_orchestration(self, orchestration_id: str) -> None:
        """Monitor a specific orchestration."""
        
        try:
            orchestration = self.active_orchestrations.get(orchestration_id)
            if not orchestration:
                return
            
            # Check strategy health
            unhealthy_strategies = []
            for execution_id in orchestration["strategy_executions"]:
                status = await live_execution_engine.get_execution_status(execution_id)
                if not status or status.get("status") == "error":
                    unhealthy_strategies.append(execution_id)
            
            # Handle unhealthy strategies
            if unhealthy_strategies:
                await self._handle_unhealthy_strategies(orchestration_id, unhealthy_strategies)
            
            # Update performance metrics
            await self._update_orchestration_metrics(orchestration_id)
            
            # Check risk limits
            await self._check_orchestration_risk_limits(orchestration_id)
            
        except Exception as e:
            self.logger.error(f"Error monitoring orchestration {orchestration_id}: {e}")
    
    async def _handle_unhealthy_strategies(self, orchestration_id: str, unhealthy_strategies: List[int]) -> None:
        """Handle unhealthy strategies in an orchestration."""
        
        try:
            orchestration = self.active_orchestrations[orchestration_id]
            
            for strategy_id in unhealthy_strategies:
                self.logger.warning(f"Strategy {strategy_id} is unhealthy in orchestration {orchestration_id}")
                
                # Attempt to restart strategy
                restart_success = await live_execution_engine.start_execution(strategy_id)
                
                if not restart_success:
                    # If restart fails, remove from orchestration
                    self.logger.error(f"Failed to restart strategy {strategy_id}, removing from orchestration")
                    await self.remove_strategy_from_orchestration(orchestration_id, strategy_id)
            
        except Exception as e:
            self.logger.error(f"Error handling unhealthy strategies: {e}")
    
    async def _portfolio_rebalancing_loop(self) -> None:
        """Portfolio rebalancing loop."""
        
        while self.orchestrator_running:
            try:
                current_time = datetime.utcnow()
                
                # Check for orchestrations that need rebalancing
                for orchestration_id, next_rebalance in list(self.rebalance_schedules.items()):
                    if current_time >= next_rebalance:
                        await self._rebalance_portfolio(orchestration_id)
                        
                        # Schedule next rebalance
                        self.rebalance_schedules[orchestration_id] = current_time + timedelta(hours=self.rebalance_interval_hours)
                
                await asyncio.sleep(3600.0)  # Check every hour
                
            except Exception as e:
                self.logger.error(f"Error in portfolio rebalancing loop: {e}")
                await asyncio.sleep(3600.0)
    
    async def _rebalance_portfolio(self, orchestration_id: str) -> None:
        """Rebalance portfolio allocations based on performance."""
        
        try:
            orchestration = self.active_orchestrations.get(orchestration_id)
            if not orchestration or orchestration["mode"] != OrchestrationMode.PORTFOLIO:
                return
            
            if not orchestration.get("rebalance_enabled", False):
                return
            
            # Calculate performance scores for each strategy
            performance_scores = {}
            risk_scores = {}
            
            for execution_id in orchestration["strategy_executions"]:
                # Get strategy performance metrics
                perf_score = await self._calculate_strategy_performance_score(execution_id)
                risk_score = await self._calculate_strategy_risk_score(execution_id)
                
                performance_scores[execution_id] = perf_score
                risk_scores[execution_id] = risk_score
            
            # Calculate new allocations based on performance and risk
            new_allocations = await self._optimize_portfolio_allocations(
                orchestration["strategy_executions"].keys(),
                performance_scores,
                risk_scores,
                orchestration["total_capital"]
            )
            
            # Update strategy allocations
            for execution_id, new_allocation in new_allocations.items():
                if execution_id in self.strategy_allocations:
                    allocation = self.strategy_allocations[execution_id]
                    allocation.allocated_capital = new_allocation
                    allocation.current_allocation_pct = (new_allocation / orchestration["total_capital"]) * 100
                    allocation.performance_score = performance_scores[execution_id]
                    allocation.risk_score = risk_scores[execution_id]
            
            orchestration["last_rebalance"] = datetime.utcnow()
            
            self.logger.info(f"Rebalanced portfolio {orchestration_id}")
            
        except Exception as e:
            self.logger.error(f"Error rebalancing portfolio {orchestration_id}: {e}")
    
    async def _calculate_strategy_performance_score(self, execution_id: int) -> Decimal:
        """Calculate performance score for a strategy."""
        
        try:
            # Get strategy execution status
            status = await live_execution_engine.get_execution_status(execution_id)
            if not status:
                return Decimal("0.0")
            
            # Simple performance score based on returns and win rate
            # In a real implementation, this would be more sophisticated
            base_score = Decimal("50.0")  # Neutral score
            
            # Adjust based on current capital vs allocated
            current_capital = Decimal(str(status.get("current_capital", 0)))
            allocated_capital = Decimal(str(status.get("allocated_capital", 1)))
            
            if allocated_capital > 0:
                return_pct = ((current_capital - allocated_capital) / allocated_capital) * 100
                performance_score = base_score + return_pct
                
                # Cap between 0 and 100
                return max(Decimal("0.0"), min(Decimal("100.0"), performance_score))
            
            return base_score
            
        except Exception as e:
            self.logger.error(f"Error calculating performance score for strategy {execution_id}: {e}")
            return Decimal("50.0")
    
    async def _calculate_strategy_risk_score(self, execution_id: int) -> Decimal:
        """Calculate risk score for a strategy."""
        
        try:
            # Get risk metrics from risk manager
            risk_summary = await risk_manager.get_risk_summary(execution_id)
            
            if risk_summary:
                # Use overall risk score from risk manager
                return Decimal(str(risk_summary.get("overall_risk_score", 50.0)))
            
            return Decimal("50.0")  # Neutral risk score
            
        except Exception as e:
            self.logger.error(f"Error calculating risk score for strategy {execution_id}: {e}")
            return Decimal("50.0")
    
    async def _optimize_portfolio_allocations(
        self,
        strategy_ids: Set[int],
        performance_scores: Dict[int, Decimal],
        risk_scores: Dict[int, Decimal],
        total_capital: Decimal
    ) -> Dict[int, Decimal]:
        """Optimize portfolio allocations based on performance and risk."""
        
        try:
            # Simple allocation optimization based on risk-adjusted performance
            # In practice, this could use modern portfolio theory, Black-Litterman, etc.
            
            allocations = {}
            
            # Calculate risk-adjusted scores
            risk_adjusted_scores = {}
            total_score = Decimal("0.0")
            
            for strategy_id in strategy_ids:
                perf_score = performance_scores[strategy_id]
                risk_score = risk_scores[strategy_id]
                
                # Higher performance, lower risk = better score
                # Risk score: 0 = high risk, 100 = low risk
                risk_adjusted_score = perf_score * (risk_score / 100)
                risk_adjusted_scores[strategy_id] = risk_adjusted_score
                total_score += risk_adjusted_score
            
            # Allocate capital proportionally to risk-adjusted scores
            if total_score > 0:
                for strategy_id in strategy_ids:
                    allocation_pct = risk_adjusted_scores[strategy_id] / total_score
                    
                    # Apply minimum allocation
                    allocation_pct = max(allocation_pct, self.min_allocation_pct / 100)
                    
                    # Apply maximum allocation from strategy settings
                    if strategy_id in self.strategy_allocations:
                        max_pct = self.strategy_allocations[strategy_id].max_allocation_pct / 100
                        allocation_pct = min(allocation_pct, max_pct)
                    
                    allocations[strategy_id] = total_capital * allocation_pct
            else:
                # Equal allocation if no performance data
                equal_allocation = total_capital / len(strategy_ids)
                for strategy_id in strategy_ids:
                    allocations[strategy_id] = equal_allocation
            
            return allocations
            
        except Exception as e:
            self.logger.error(f"Error optimizing portfolio allocations: {e}")
            # Fallback to equal allocation
            equal_allocation = total_capital / len(strategy_ids)
            return {strategy_id: equal_allocation for strategy_id in strategy_ids}
    
    async def _performance_tracking_loop(self) -> None:
        """Performance tracking loop."""
        
        while self.orchestrator_running:
            try:
                for orchestration_id in self.active_orchestrations:
                    await self._update_orchestration_metrics(orchestration_id)
                
                await asyncio.sleep(300.0)  # Update every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in performance tracking loop: {e}")
                await asyncio.sleep(300.0)
    
    async def _update_orchestration_metrics(self, orchestration_id: str) -> None:
        """Update performance metrics for an orchestration."""
        
        try:
            orchestration = self.active_orchestrations.get(orchestration_id)
            if not orchestration:
                return
            
            # Collect metrics from all strategies
            total_value = Decimal("0.0")
            total_return = Decimal("0.0")
            active_count = 0
            
            for execution_id in orchestration["strategy_executions"]:
                status = await live_execution_engine.get_execution_status(execution_id)
                if status:
                    current_capital = Decimal(str(status.get("current_capital", 0)))
                    allocated_capital = Decimal(str(status.get("allocated_capital", 0)))
                    
                    total_value += current_capital
                    total_return += (current_capital - allocated_capital)
                    
                    if status.get("status") == "running":
                        active_count += 1
            
            # Calculate portfolio metrics
            total_capital = orchestration["total_capital"]
            portfolio_return_pct = (total_return / total_capital) * 100 if total_capital > 0 else Decimal("0.0")
            
            # Create metrics object
            metrics = OrchestrationMetrics(
                total_strategies=len(orchestration["strategy_executions"]),
                active_strategies=active_count,
                total_allocated_capital=total_capital,
                total_portfolio_value=total_value,
                portfolio_return=total_return,
                portfolio_return_pct=portfolio_return_pct,
                sharpe_ratio=None,  # TODO: Calculate Sharpe ratio
                max_drawdown_pct=Decimal("0.0"),  # TODO: Calculate max drawdown
                diversification_score=Decimal("0.0")  # TODO: Calculate diversification
            )
            
            self.orchestration_metrics[orchestration_id] = metrics
            
        except Exception as e:
            self.logger.error(f"Error updating orchestration metrics: {e}")
    
    async def _check_orchestration_risk_limits(self, orchestration_id: str) -> None:
        """Check risk limits for an orchestration."""
        
        try:
            orchestration = self.active_orchestrations.get(orchestration_id)
            if not orchestration:
                return
            
            metrics = self.orchestration_metrics.get(orchestration_id)
            if not metrics:
                return
            
            # Check portfolio drawdown limit
            if metrics.max_drawdown_pct > Decimal("20.0"):  # 20% max drawdown
                self.logger.warning(f"Orchestration {orchestration_id} exceeded drawdown limit")
                # Could implement automatic position reduction here
            
            # Check individual strategy risk limits
            for execution_id in orchestration["strategy_executions"]:
                risk_summary = await risk_manager.get_risk_summary(execution_id)
                if risk_summary and risk_summary.get("overall_risk_score", 0) > 90:
                    self.logger.warning(f"Strategy {execution_id} has high risk score")
            
        except Exception as e:
            self.logger.error(f"Error checking orchestration risk limits: {e}")
    
    async def get_orchestration_status(self, orchestration_id: str) -> Optional[Dict[str, Any]]:
        """Get orchestration status and metrics."""
        
        orchestration = self.active_orchestrations.get(orchestration_id)
        if not orchestration:
            return None
        
        metrics = self.orchestration_metrics.get(orchestration_id)
        
        # Get strategy statuses
        strategy_statuses = {}
        for execution_id in orchestration["strategy_executions"]:
            status = await live_execution_engine.get_execution_status(execution_id)
            if status:
                strategy_statuses[execution_id] = status
        
        return {
            "orchestration_id": orchestration_id,
            "mode": orchestration["mode"].value,
            "environment_id": orchestration["environment_id"],
            "status": orchestration.get("status", "unknown"),
            "total_strategies": len(orchestration["strategy_executions"]),
            "strategy_statuses": strategy_statuses,
            "allocations": {
                str(k): {
                    "allocated_capital": float(v.allocated_capital),
                    "current_allocation_pct": float(v.current_allocation_pct),
                    "performance_score": float(v.performance_score),
                    "risk_score": float(v.risk_score)
                }
                for k, v in self.strategy_allocations.items()
                if k in orchestration["strategy_executions"]
            },
            "metrics": {
                "total_strategies": metrics.total_strategies,
                "active_strategies": metrics.active_strategies,
                "total_allocated_capital": float(metrics.total_allocated_capital),
                "total_portfolio_value": float(metrics.total_portfolio_value),
                "portfolio_return": float(metrics.portfolio_return),
                "portfolio_return_pct": float(metrics.portfolio_return_pct),
                "sharpe_ratio": float(metrics.sharpe_ratio) if metrics.sharpe_ratio else None,
                "max_drawdown_pct": float(metrics.max_drawdown_pct),
                "diversification_score": float(metrics.diversification_score)
            } if metrics else None,
            "last_rebalance": orchestration.get("last_rebalance", {}).isoformat() if orchestration.get("last_rebalance") else None,
            "next_rebalance": self.rebalance_schedules.get(orchestration_id, {}).isoformat() if orchestration_id in self.rebalance_schedules else None
        }
    
    async def get_all_orchestrations(self) -> List[Dict[str, Any]]:
        """Get all active orchestrations."""
        
        orchestrations = []
        for orchestration_id in self.active_orchestrations:
            status = await self.get_orchestration_status(orchestration_id)
            if status:
                orchestrations.append(status)
        
        return orchestrations
    
    async def trigger_rebalance(self, orchestration_id: str) -> bool:
        """Manually trigger portfolio rebalancing."""
        
        try:
            await self._rebalance_portfolio(orchestration_id)
            return True
        except Exception as e:
            self.logger.error(f"Error triggering rebalance: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup strategy orchestrator."""
        
        self.orchestrator_running = False
        
        # Stop all orchestrations
        for orchestration_id in list(self.active_orchestrations.keys()):
            await self.stop_orchestration(orchestration_id)
        
        self.logger.info("Strategy orchestrator cleaned up")


# Global strategy orchestrator instance
strategy_orchestrator = StrategyOrchestrator()