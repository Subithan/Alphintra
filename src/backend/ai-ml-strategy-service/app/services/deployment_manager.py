"""
Strategy deployment and lifecycle management service.
"""

import asyncio
import logging
import json
import yaml
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.execution import (
    StrategyExecution,
    ExecutionEnvironment,
    ExecutionStatus
)
from app.models.strategy import Strategy
from app.services.live_execution_engine import live_execution_engine
from app.services.strategy_orchestrator import strategy_orchestrator
from app.services.broker_integration import broker_integration_service
from app.services.market_data_service import market_data_service
from app.database.connection import get_db_session


class DeploymentStatus(Enum):
    PREPARING = "preparing"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    ROLLBACK = "rollback"


class DeploymentType(Enum):
    PAPER_TRADING = "paper_trading"
    LIVE_TRADING = "live_trading"
    SIMULATION = "simulation"
    BACKTESTING = "backtesting"


@dataclass
class DeploymentConfig:
    """Strategy deployment configuration."""
    strategy_id: int
    environment_id: int
    deployment_name: str
    deployment_type: str
    allocated_capital: Decimal
    symbols: List[str]
    timeframes: List[str]
    position_sizing_method: str
    position_size_config: Dict[str, Any]
    risk_limits: Dict[str, Any]
    execution_config: Dict[str, Any]
    monitoring_config: Dict[str, Any]
    auto_start: bool = True
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DeploymentPlan:
    """Deployment execution plan."""
    deployment_id: str
    config: DeploymentConfig
    validation_steps: List[str]
    deployment_steps: List[str]
    rollback_steps: List[str]
    dependencies: List[str]
    estimated_duration: int  # seconds
    resource_requirements: Dict[str, Any]


@dataclass
class DeploymentMetrics:
    """Deployment performance metrics."""
    deployment_id: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    success_rate: float
    error_count: int
    resource_usage: Dict[str, Any]
    performance_score: float


class DeploymentManager:
    """Manages strategy deployment and lifecycle operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Deployment state
        self.active_deployments: Dict[str, Dict] = {}
        self.deployment_queue: asyncio.Queue = asyncio.Queue()
        self.deployment_history: List[DeploymentMetrics] = []
        
        # Lifecycle management
        self.lifecycle_schedules: Dict[str, Dict] = {}
        self.health_checks: Dict[str, Dict] = {}
        
        # Resource management
        self.resource_limits: Dict[str, Any] = {
            "max_concurrent_deployments": 5,
            "max_strategies_per_environment": 10,
            "max_total_allocated_capital": Decimal("1000000.00"),
            "memory_limit_mb": 1024,
            "cpu_limit_percent": 50
        }
        
        # Configuration
        self.manager_running = False
        self.deployment_timeout = 300  # 5 minutes
        self.health_check_interval = 60  # 1 minute
        self.cleanup_interval = 3600  # 1 hour
        
    async def initialize(self) -> None:
        """Initialize the deployment manager."""
        
        # Load active deployments
        await self._load_active_deployments()
        
        # Start management loops
        if not self.manager_running:
            self.manager_running = True
            asyncio.create_task(self._deployment_processing_loop())
            asyncio.create_task(self._lifecycle_management_loop())
            asyncio.create_task(self._health_monitoring_loop())
            asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Deployment manager initialized")
    
    async def _load_active_deployments(self) -> None:
        """Load active deployments from database."""
        
        try:
            with get_db_session() as db:
                active_executions = db.query(StrategyExecution).filter(
                    StrategyExecution.status.in_([
                        ExecutionStatus.RUNNING.value,
                        ExecutionStatus.PAUSED.value
                    ])
                ).all()
                
                for execution in active_executions:
                    deployment_id = f"deployment_{execution.id}"
                    self.active_deployments[deployment_id] = {
                        "execution": execution,
                        "status": DeploymentStatus.DEPLOYED,
                        "created_at": execution.created_at,
                        "last_health_check": datetime.utcnow(),
                        "health_status": "healthy"
                    }
                    
                    # Schedule health checks
                    self.health_checks[deployment_id] = {
                        "next_check": datetime.utcnow() + timedelta(seconds=self.health_check_interval),
                        "consecutive_failures": 0,
                        "last_check_result": "healthy"
                    }
                
            self.logger.info(f"Loaded {len(self.active_deployments)} active deployments")
            
        except Exception as e:
            self.logger.error(f"Error loading active deployments: {e}")
    
    async def create_deployment_plan(self, config: DeploymentConfig) -> DeploymentPlan:
        """Create a deployment plan from configuration."""
        
        try:
            deployment_id = f"deploy_{config.strategy_id}_{int(datetime.utcnow().timestamp())}"
            
            # Validation steps
            validation_steps = [
                "validate_strategy",
                "validate_environment",
                "validate_capital_allocation",
                "validate_symbols",
                "validate_risk_limits",
                "check_dependencies",
                "check_resource_availability"
            ]
            
            # Deployment steps
            deployment_steps = [
                "create_execution_record",
                "initialize_broker_connection",
                "setup_market_data_feeds",
                "configure_risk_management",
                "initialize_position_tracking",
                "start_execution_engine",
                "register_with_orchestrator",
                "enable_monitoring"
            ]
            
            # Rollback steps
            rollback_steps = [
                "stop_execution_engine",
                "close_positions",
                "disconnect_broker",
                "cleanup_resources",
                "update_status"
            ]
            
            # Check dependencies
            dependencies = await self._check_deployment_dependencies(config)
            
            # Estimate duration
            estimated_duration = len(deployment_steps) * 30 + len(validation_steps) * 10  # seconds
            
            # Calculate resource requirements
            resource_requirements = {
                "memory_mb": 256,  # Base memory requirement
                "cpu_percent": 10,  # Base CPU requirement
                "network_bandwidth": "low",
                "storage_mb": 100
            }
            
            return DeploymentPlan(
                deployment_id=deployment_id,
                config=config,
                validation_steps=validation_steps,
                deployment_steps=deployment_steps,
                rollback_steps=rollback_steps,
                dependencies=dependencies,
                estimated_duration=estimated_duration,
                resource_requirements=resource_requirements
            )
            
        except Exception as e:
            self.logger.error(f"Error creating deployment plan: {e}")
            raise
    
    async def _check_deployment_dependencies(self, config: DeploymentConfig) -> List[str]:
        """Check deployment dependencies."""
        
        dependencies = []
        
        try:
            # Check if strategy exists
            with get_db_session() as db:
                strategy = db.query(Strategy).filter(Strategy.id == config.strategy_id).first()
                if not strategy:
                    dependencies.append(f"strategy_{config.strategy_id}")
                
                # Check if environment exists
                environment = db.query(ExecutionEnvironment).filter(
                    ExecutionEnvironment.id == config.environment_id
                ).first()
                if not environment:
                    dependencies.append(f"environment_{config.environment_id}")
                elif not environment.is_active:
                    dependencies.append(f"environment_{config.environment_id}_activation")
            
            # Check market data availability
            for symbol in config.symbols:
                price = await market_data_service.get_current_price(symbol)
                if not price:
                    dependencies.append(f"market_data_{symbol}")
            
            return dependencies
            
        except Exception as e:
            self.logger.error(f"Error checking dependencies: {e}")
            return ["dependency_check_failed"]
    
    async def deploy_strategy(self, config: DeploymentConfig) -> str:
        """Deploy a strategy using the provided configuration."""
        
        try:
            # Create deployment plan
            plan = await self.create_deployment_plan(config)
            
            # Check resource limits
            if not await self._check_resource_limits(plan):
                raise Exception("Resource limits exceeded")
            
            # Add to deployment queue
            await self.deployment_queue.put(plan)
            
            self.logger.info(f"Queued deployment {plan.deployment_id}")
            return plan.deployment_id
            
        except Exception as e:
            self.logger.error(f"Error deploying strategy: {e}")
            raise
    
    async def _check_resource_limits(self, plan: DeploymentPlan) -> bool:
        """Check if deployment fits within resource limits."""
        
        try:
            # Check concurrent deployments
            if len(self.active_deployments) >= self.resource_limits["max_concurrent_deployments"]:
                return False
            
            # Check strategies per environment
            environment_count = defaultdict(int)
            for deployment in self.active_deployments.values():
                environment_count[deployment["execution"].environment_id] += 1
            
            if environment_count[plan.config.environment_id] >= self.resource_limits["max_strategies_per_environment"]:
                return False
            
            # Check total allocated capital
            total_capital = sum(
                deployment["execution"].allocated_capital 
                for deployment in self.active_deployments.values()
            )
            
            if total_capital + plan.config.allocated_capital > self.resource_limits["max_total_allocated_capital"]:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking resource limits: {e}")
            return False
    
    async def _deployment_processing_loop(self) -> None:
        """Main deployment processing loop."""
        
        while self.manager_running:
            try:
                # Get deployment from queue
                try:
                    plan = await asyncio.wait_for(self.deployment_queue.get(), timeout=1.0)
                    await self._execute_deployment(plan)
                except asyncio.TimeoutError:
                    continue
                
            except Exception as e:
                self.logger.error(f"Error in deployment processing loop: {e}")
                await asyncio.sleep(5.0)
    
    async def _execute_deployment(self, plan: DeploymentPlan) -> None:
        """Execute a deployment plan."""
        
        deployment_id = plan.deployment_id
        start_time = datetime.utcnow()
        
        try:
            # Initialize deployment tracking
            self.active_deployments[deployment_id] = {
                "plan": plan,
                "status": DeploymentStatus.PREPARING,
                "created_at": start_time,
                "started_at": start_time,
                "current_step": None,
                "completed_steps": [],
                "error_message": None
            }
            
            deployment = self.active_deployments[deployment_id]
            
            # Validation phase
            deployment["status"] = DeploymentStatus.VALIDATING
            for step in plan.validation_steps:
                deployment["current_step"] = step
                await self._execute_validation_step(step, plan)
                deployment["completed_steps"].append(step)
            
            # Deployment phase
            deployment["status"] = DeploymentStatus.DEPLOYING
            for step in plan.deployment_steps:
                deployment["current_step"] = step
                await self._execute_deployment_step(step, plan)
                deployment["completed_steps"].append(step)
            
            # Mark as deployed
            deployment["status"] = DeploymentStatus.DEPLOYED
            deployment["completed_at"] = datetime.utcnow()
            
            # Schedule health checks
            self.health_checks[deployment_id] = {
                "next_check": datetime.utcnow() + timedelta(seconds=self.health_check_interval),
                "consecutive_failures": 0,
                "last_check_result": "healthy"
            }
            
            # Auto-start if configured
            if plan.config.auto_start:
                await self.start_deployment(deployment_id)
            
            self.logger.info(f"Successfully deployed {deployment_id}")
            
        except Exception as e:
            self.logger.error(f"Deployment {deployment_id} failed: {e}")
            
            # Update deployment status
            if deployment_id in self.active_deployments:
                self.active_deployments[deployment_id]["status"] = DeploymentStatus.FAILED
                self.active_deployments[deployment_id]["error_message"] = str(e)
            
            # Attempt rollback
            await self._rollback_deployment(deployment_id, plan)
    
    async def _execute_validation_step(self, step: str, plan: DeploymentPlan) -> None:
        """Execute a validation step."""
        
        config = plan.config
        
        if step == "validate_strategy":
            with get_db_session() as db:
                strategy = db.query(Strategy).filter(Strategy.id == config.strategy_id).first()
                if not strategy:
                    raise Exception(f"Strategy {config.strategy_id} not found")
                if not strategy.is_active:
                    raise Exception(f"Strategy {config.strategy_id} is not active")
        
        elif step == "validate_environment":
            with get_db_session() as db:
                environment = db.query(ExecutionEnvironment).filter(
                    ExecutionEnvironment.id == config.environment_id
                ).first()
                if not environment:
                    raise Exception(f"Environment {config.environment_id} not found")
                if not environment.is_active:
                    raise Exception(f"Environment {config.environment_id} is not active")
        
        elif step == "validate_capital_allocation":
            if config.allocated_capital <= 0:
                raise Exception("Invalid capital allocation")
        
        elif step == "validate_symbols":
            if not config.symbols:
                raise Exception("No symbols specified")
            
            # Check if symbols are valid
            for symbol in config.symbols:
                price = await market_data_service.get_current_price(symbol)
                if not price:
                    self.logger.warning(f"Cannot get price for symbol {symbol}")
        
        elif step == "validate_risk_limits":
            risk_limits = config.risk_limits
            if "max_position_size" in risk_limits:
                if risk_limits["max_position_size"] > config.allocated_capital:
                    raise Exception("Max position size exceeds allocated capital")
        
        elif step == "check_dependencies":
            dependencies = await self._check_deployment_dependencies(config)
            if dependencies:
                raise Exception(f"Unmet dependencies: {dependencies}")
        
        elif step == "check_resource_availability":
            if not await self._check_resource_limits(plan):
                raise Exception("Resource limits exceeded")
        
        self.logger.debug(f"Validation step completed: {step}")
    
    async def _execute_deployment_step(self, step: str, plan: DeploymentPlan) -> None:
        """Execute a deployment step."""
        
        config = plan.config
        
        if step == "create_execution_record":
            # Create StrategyExecution record
            execution = StrategyExecution(
                strategy_id=config.strategy_id,
                environment_id=config.environment_id,
                name=config.deployment_name,
                allocated_capital=config.allocated_capital,
                current_capital=config.allocated_capital,
                symbols=config.symbols,
                timeframes=config.timeframes,
                position_sizing_method=config.position_sizing_method,
                position_size_config=config.position_size_config,
                max_position_size=config.risk_limits.get("max_position_size"),
                max_daily_loss=config.risk_limits.get("max_daily_loss"),
                stop_loss_pct=config.risk_limits.get("stop_loss_pct"),
                take_profit_pct=config.risk_limits.get("take_profit_pct"),
                status=ExecutionStatus.INACTIVE.value,
                config=config.execution_config,
                metadata=config.metadata or {}
            )
            
            with get_db_session() as db:
                db.add(execution)
                db.commit()
                db.refresh(execution)
            
            # Store execution in deployment
            deployment = self.active_deployments[plan.deployment_id]
            deployment["execution"] = execution
        
        elif step == "initialize_broker_connection":
            # Initialize broker connection for the environment
            success = await broker_integration_service.initialize_environment(config.environment_id)
            if not success:
                raise Exception("Failed to initialize broker connection")
        
        elif step == "setup_market_data_feeds":
            # Subscribe to market data for symbols
            for symbol in config.symbols:
                # This would set up real-time data feeds
                pass
        
        elif step == "configure_risk_management":
            # Configure risk management parameters
            pass
        
        elif step == "initialize_position_tracking":
            # Initialize position tracking
            pass
        
        elif step == "start_execution_engine":
            # Initialize execution in the live execution engine
            execution = self.active_deployments[plan.deployment_id]["execution"]
            await live_execution_engine._initialize_execution_state(execution)
        
        elif step == "register_with_orchestrator":
            # Register with strategy orchestrator if multiple strategies
            pass
        
        elif step == "enable_monitoring":
            # Enable monitoring and alerting
            pass
        
        self.logger.debug(f"Deployment step completed: {step}")
    
    async def _rollback_deployment(self, deployment_id: str, plan: DeploymentPlan) -> None:
        """Rollback a failed deployment."""
        
        try:
            self.logger.info(f"Rolling back deployment {deployment_id}")
            
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                return
            
            deployment["status"] = DeploymentStatus.ROLLBACK
            
            # Execute rollback steps in reverse order
            for step in reversed(plan.rollback_steps):
                try:
                    await self._execute_rollback_step(step, deployment)
                except Exception as e:
                    self.logger.error(f"Rollback step {step} failed: {e}")
            
            # Remove from active deployments
            del self.active_deployments[deployment_id]
            
            self.logger.info(f"Rollback completed for {deployment_id}")
            
        except Exception as e:
            self.logger.error(f"Error during rollback: {e}")
    
    async def _execute_rollback_step(self, step: str, deployment: Dict) -> None:
        """Execute a rollback step."""
        
        if step == "stop_execution_engine":
            if "execution" in deployment:
                execution_id = deployment["execution"].id
                await live_execution_engine.stop_execution(execution_id)
        
        elif step == "close_positions":
            # Close any open positions
            pass
        
        elif step == "disconnect_broker":
            if "execution" in deployment:
                environment_id = deployment["execution"].environment_id
                await broker_integration_service.disconnect_environment(environment_id)
        
        elif step == "cleanup_resources":
            # Cleanup any allocated resources
            pass
        
        elif step == "update_status":
            if "execution" in deployment:
                with get_db_session() as db:
                    execution = db.query(StrategyExecution).filter(
                        StrategyExecution.id == deployment["execution"].id
                    ).first()
                    if execution:
                        execution.status = ExecutionStatus.STOPPED.value
                        db.commit()
    
    async def start_deployment(self, deployment_id: str) -> bool:
        """Start a deployed strategy."""
        
        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")
            
            if deployment["status"] != DeploymentStatus.DEPLOYED:
                raise ValueError(f"Deployment {deployment_id} is not in deployed state")
            
            execution = deployment["execution"]
            
            # Start execution
            success = await live_execution_engine.start_execution(execution.id)
            if success:
                deployment["status"] = DeploymentStatus.RUNNING
                deployment["started_at"] = datetime.utcnow()
                
                self.logger.info(f"Started deployment {deployment_id}")
                return True
            else:
                raise Exception("Failed to start execution")
                
        except Exception as e:
            self.logger.error(f"Error starting deployment {deployment_id}: {e}")
            return False
    
    async def stop_deployment(self, deployment_id: str) -> bool:
        """Stop a running deployment."""
        
        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")
            
            execution = deployment["execution"]
            
            # Stop execution
            success = await live_execution_engine.stop_execution(execution.id)
            if success:
                deployment["status"] = DeploymentStatus.STOPPED
                deployment["stopped_at"] = datetime.utcnow()
                
                # Remove from active deployments
                del self.active_deployments[deployment_id]
                
                # Clean up health checks
                if deployment_id in self.health_checks:
                    del self.health_checks[deployment_id]
                
                self.logger.info(f"Stopped deployment {deployment_id}")
                return True
            else:
                raise Exception("Failed to stop execution")
                
        except Exception as e:
            self.logger.error(f"Error stopping deployment {deployment_id}: {e}")
            return False
    
    async def pause_deployment(self, deployment_id: str) -> bool:
        """Pause a running deployment."""
        
        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")
            
            execution = deployment["execution"]
            
            # Pause execution
            success = await live_execution_engine.pause_execution(execution.id)
            if success:
                deployment["status"] = DeploymentStatus.PAUSED
                self.logger.info(f"Paused deployment {deployment_id}")
                return True
            else:
                raise Exception("Failed to pause execution")
                
        except Exception as e:
            self.logger.error(f"Error pausing deployment {deployment_id}: {e}")
            return False
    
    async def resume_deployment(self, deployment_id: str) -> bool:
        """Resume a paused deployment."""
        
        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")
            
            execution = deployment["execution"]
            
            # Resume execution
            success = await live_execution_engine.resume_execution(execution.id)
            if success:
                deployment["status"] = DeploymentStatus.RUNNING
                self.logger.info(f"Resumed deployment {deployment_id}")
                return True
            else:
                raise Exception("Failed to resume execution")
                
        except Exception as e:
            self.logger.error(f"Error resuming deployment {deployment_id}: {e}")
            return False
    
    async def _lifecycle_management_loop(self) -> None:
        """Lifecycle management loop."""
        
        while self.manager_running:
            try:
                # Check lifecycle schedules
                current_time = datetime.utcnow()
                
                for deployment_id, schedule in list(self.lifecycle_schedules.items()):
                    if current_time >= schedule.get("next_action_time", current_time):
                        await self._execute_lifecycle_action(deployment_id, schedule)
                
                await asyncio.sleep(60.0)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in lifecycle management loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _execute_lifecycle_action(self, deployment_id: str, schedule: Dict) -> None:
        """Execute a scheduled lifecycle action."""
        
        try:
            action = schedule.get("action")
            
            if action == "auto_stop":
                await self.stop_deployment(deployment_id)
            elif action == "auto_restart":
                await self.stop_deployment(deployment_id)
                # Could re-deploy or restart here
            elif action == "health_check":
                await self._perform_health_check(deployment_id)
            
            # Update next action time
            interval = schedule.get("interval_hours", 24)
            schedule["next_action_time"] = datetime.utcnow() + timedelta(hours=interval)
            
        except Exception as e:
            self.logger.error(f"Error executing lifecycle action for {deployment_id}: {e}")
    
    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop."""
        
        while self.manager_running:
            try:
                current_time = datetime.utcnow()
                
                for deployment_id, health_check in list(self.health_checks.items()):
                    if current_time >= health_check["next_check"]:
                        await self._perform_health_check(deployment_id)
                
                await asyncio.sleep(30.0)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _perform_health_check(self, deployment_id: str) -> None:
        """Perform health check on a deployment."""
        
        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                return
            
            health_check = self.health_checks.get(deployment_id)
            if not health_check:
                return
            
            # Check execution status
            execution = deployment["execution"]
            status = await live_execution_engine.get_execution_status(execution.id)
            
            is_healthy = True
            health_issues = []
            
            if not status:
                is_healthy = False
                health_issues.append("execution_not_found")
            elif status.get("status") == "error":
                is_healthy = False
                health_issues.append("execution_error")
            elif status.get("error_count", 0) > 10:
                is_healthy = False
                health_issues.append("high_error_count")
            
            # Update health check
            if is_healthy:
                health_check["consecutive_failures"] = 0
                health_check["last_check_result"] = "healthy"
                deployment["health_status"] = "healthy"
            else:
                health_check["consecutive_failures"] += 1
                health_check["last_check_result"] = f"unhealthy: {', '.join(health_issues)}"
                deployment["health_status"] = "unhealthy"
                
                # Take action if too many consecutive failures
                if health_check["consecutive_failures"] >= 3:
                    self.logger.warning(f"Deployment {deployment_id} failed health checks, taking action")
                    # Could restart, pause, or alert here
            
            health_check["next_check"] = datetime.utcnow() + timedelta(seconds=self.health_check_interval)
            deployment["last_health_check"] = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Error performing health check for {deployment_id}: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Cleanup loop for old deployments."""
        
        while self.manager_running:
            try:
                # Clean up old deployment history
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                self.deployment_history = [
                    metrics for metrics in self.deployment_history
                    if metrics.created_at > cutoff_time
                ]
                
                await asyncio.sleep(self.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(self.cleanup_interval)
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status."""
        
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            return None
        
        execution_status = None
        if "execution" in deployment:
            execution_status = await live_execution_engine.get_execution_status(deployment["execution"].id)
        
        return {
            "deployment_id": deployment_id,
            "status": deployment["status"].value if hasattr(deployment["status"], 'value') else deployment["status"],
            "created_at": deployment["created_at"].isoformat(),
            "started_at": deployment.get("started_at", {}).isoformat() if deployment.get("started_at") else None,
            "completed_at": deployment.get("completed_at", {}).isoformat() if deployment.get("completed_at") else None,
            "current_step": deployment.get("current_step"),
            "completed_steps": deployment.get("completed_steps", []),
            "error_message": deployment.get("error_message"),
            "health_status": deployment.get("health_status"),
            "last_health_check": deployment.get("last_health_check", {}).isoformat() if deployment.get("last_health_check") else None,
            "execution_status": execution_status
        }
    
    async def get_all_deployments(self) -> List[Dict[str, Any]]:
        """Get all active deployments."""
        
        deployments = []
        for deployment_id in self.active_deployments:
            status = await self.get_deployment_status(deployment_id)
            if status:
                deployments.append(status)
        
        return deployments
    
    def schedule_lifecycle_action(
        self, 
        deployment_id: str, 
        action: str, 
        schedule_time: datetime,
        interval_hours: Optional[int] = None
    ) -> None:
        """Schedule a lifecycle action."""
        
        self.lifecycle_schedules[deployment_id] = {
            "action": action,
            "next_action_time": schedule_time,
            "interval_hours": interval_hours
        }
        
        self.logger.info(f"Scheduled {action} for deployment {deployment_id} at {schedule_time}")
    
    async def cleanup(self) -> None:
        """Cleanup deployment manager."""
        
        self.manager_running = False
        
        # Stop all active deployments
        for deployment_id in list(self.active_deployments.keys()):
            await self.stop_deployment(deployment_id)
        
        self.logger.info("Deployment manager cleaned up")


# Global deployment manager instance
deployment_manager = DeploymentManager()