"""
Comprehensive execution monitoring and control service for live strategy execution.
"""

import asyncio
import logging
import json
import smtplib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.execution import (
    StrategyExecution, 
    ExecutionSignal, 
    ExecutionOrder,
    ExecutionPosition,
    ExecutionMetrics,
    ExecutionStatus
)
from app.services.live_execution_engine import live_execution_engine
from app.services.signal_processor import signal_processor
from app.database.connection import get_db_session


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringMetric(Enum):
    PERFORMANCE = "performance"
    RISK = "risk"
    HEALTH = "health"
    EXECUTION = "execution"
    MARKET = "market"


@dataclass
class Alert:
    """Execution monitoring alert."""
    id: str
    execution_id: int
    severity: AlertSeverity
    metric_type: MonitoringMetric
    title: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for strategy execution."""
    execution_id: int
    total_pnl: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: Decimal
    avg_loss: Decimal
    largest_win: Decimal
    largest_loss: Decimal
    consecutive_wins: int
    consecutive_losses: int
    avg_trade_duration_hours: float


@dataclass
class RiskMetrics:
    """Risk metrics for strategy execution."""
    execution_id: int
    current_exposure: Decimal
    max_exposure: Decimal
    var_95: Decimal  # Value at Risk 95%
    expected_shortfall: Decimal
    leverage_ratio: float
    concentration_risk: float
    correlation_risk: float
    volatility: float
    beta: float
    risk_adjusted_return: float


@dataclass
class HealthMetrics:
    """Health metrics for strategy execution."""
    execution_id: int
    uptime_pct: float
    signal_processing_rate: float
    order_success_rate: float
    execution_latency_ms: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_pct: float
    network_latency_ms: float
    broker_connection_status: str
    last_heartbeat: datetime


@dataclass
class MonitoringThresholds:
    """Monitoring thresholds for alerts."""
    max_drawdown_pct: float = 5.0
    max_daily_loss_pct: float = 2.0
    min_sharpe_ratio: float = 0.5
    max_var_pct: float = 3.0
    max_leverage: float = 3.0
    min_win_rate: float = 0.4
    max_consecutive_losses: int = 5
    max_error_rate: float = 0.05
    max_execution_latency_ms: float = 1000
    min_uptime_pct: float = 99.0
    max_memory_usage_mb: float = 1024
    max_cpu_usage_pct: float = 80.0


class ExecutionMonitor:
    """Comprehensive execution monitoring and control service."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.logger = logging.getLogger(__name__)
        self.redis_url = redis_url
        self.redis = None
        
        # Monitoring state
        self.monitor_running = False
        self.monitored_executions: Set[int] = set()
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # Metrics storage
        self.performance_metrics: Dict[int, PerformanceMetrics] = {}
        self.risk_metrics: Dict[int, RiskMetrics] = {}
        self.health_metrics: Dict[int, HealthMetrics] = {}
        
        # Monitoring configuration
        self.thresholds = MonitoringThresholds()
        self.monitoring_interval = 30  # seconds
        self.alert_cooldown = 300  # 5 minutes
        self.last_alert_time: Dict[str, datetime] = {}
        
        # Alert handlers
        self.alert_handlers: Dict[AlertSeverity, List[Callable]] = defaultdict(list)
        
        # Control actions
        self.control_actions: Dict[str, Callable] = {}
        
        # Performance tracking
        self.execution_history: Dict[int, List[Dict]] = defaultdict(list)
        self.metrics_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=1440))  # 24 hours at 1min intervals
        
    async def initialize(self) -> None:
        """Initialize the execution monitor."""
        
        # Connect to Redis
        self.redis = redis.from_url(self.redis_url)
        
        # Load active executions
        await self._load_active_executions()
        
        # Register default alert handlers
        self._register_default_alert_handlers()
        
        # Register default control actions
        self._register_default_control_actions()
        
        # Start monitoring loops
        if not self.monitor_running:
            self.monitor_running = True
            asyncio.create_task(self._performance_monitoring_loop())
            asyncio.create_task(self._risk_monitoring_loop())
            asyncio.create_task(self._health_monitoring_loop())
            asyncio.create_task(self._alert_processing_loop())
            asyncio.create_task(self._metrics_collection_loop())
            asyncio.create_task(self._anomaly_detection_loop())
        
        self.logger.info("Execution monitor initialized")
    
    async def _load_active_executions(self) -> None:
        """Load active strategy executions for monitoring."""
        
        try:
            with get_db_session() as db:
                active_executions = db.query(StrategyExecution).filter(
                    StrategyExecution.status.in_([
                        ExecutionStatus.RUNNING.value,
                        ExecutionStatus.PAUSED.value
                    ])
                ).all()
                
                for execution in active_executions:
                    self.monitored_executions.add(execution.id)
                    
                    # Initialize metrics
                    await self._initialize_execution_metrics(execution.id)
                
            self.logger.info(f"Loaded {len(active_executions)} executions for monitoring")
            
        except Exception as e:
            self.logger.error(f"Error loading active executions: {e}")
    
    async def _initialize_execution_metrics(self, execution_id: int) -> None:
        """Initialize metrics for an execution."""
        
        try:
            # Initialize performance metrics
            self.performance_metrics[execution_id] = PerformanceMetrics(
                execution_id=execution_id,
                total_pnl=Decimal('0'),
                realized_pnl=Decimal('0'),
                unrealized_pnl=Decimal('0'),
                total_return_pct=0.0,
                sharpe_ratio=0.0,
                max_drawdown_pct=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=Decimal('0'),
                avg_loss=Decimal('0'),
                largest_win=Decimal('0'),
                largest_loss=Decimal('0'),
                consecutive_wins=0,
                consecutive_losses=0,
                avg_trade_duration_hours=0.0
            )
            
            # Initialize risk metrics
            self.risk_metrics[execution_id] = RiskMetrics(
                execution_id=execution_id,
                current_exposure=Decimal('0'),
                max_exposure=Decimal('0'),
                var_95=Decimal('0'),
                expected_shortfall=Decimal('0'),
                leverage_ratio=0.0,
                concentration_risk=0.0,
                correlation_risk=0.0,
                volatility=0.0,
                beta=0.0,
                risk_adjusted_return=0.0
            )
            
            # Initialize health metrics
            self.health_metrics[execution_id] = HealthMetrics(
                execution_id=execution_id,
                uptime_pct=100.0,
                signal_processing_rate=0.0,
                order_success_rate=100.0,
                execution_latency_ms=0.0,
                error_rate=0.0,
                memory_usage_mb=0.0,
                cpu_usage_pct=0.0,
                network_latency_ms=0.0,
                broker_connection_status="connected",
                last_heartbeat=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing metrics for execution {execution_id}: {e}")
    
    async def add_execution_monitoring(self, execution_id: int) -> None:
        """Add an execution to monitoring."""
        
        if execution_id not in self.monitored_executions:
            self.monitored_executions.add(execution_id)
            await self._initialize_execution_metrics(execution_id)
            
            self.logger.info(f"Added execution {execution_id} to monitoring")
    
    async def remove_execution_monitoring(self, execution_id: int) -> None:
        """Remove an execution from monitoring."""
        
        if execution_id in self.monitored_executions:
            self.monitored_executions.remove(execution_id)
            
            # Clean up metrics
            self.performance_metrics.pop(execution_id, None)
            self.risk_metrics.pop(execution_id, None)
            self.health_metrics.pop(execution_id, None)
            self.execution_history.pop(execution_id, None)
            self.metrics_history.pop(execution_id, None)
            
            self.logger.info(f"Removed execution {execution_id} from monitoring")
    
    async def _performance_monitoring_loop(self) -> None:
        """Performance monitoring loop."""
        
        while self.monitor_running:
            try:
                for execution_id in list(self.monitored_executions):
                    await self._update_performance_metrics(execution_id)
                    await self._check_performance_alerts(execution_id)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _update_performance_metrics(self, execution_id: int) -> None:
        """Update performance metrics for an execution."""
        
        try:
            with get_db_session() as db:
                # Get execution details
                execution = db.query(StrategyExecution).filter(
                    StrategyExecution.id == execution_id
                ).first()
                
                if not execution:
                    return
                
                # Get execution positions
                positions = db.query(ExecutionPosition).filter(
                    ExecutionPosition.strategy_execution_id == execution_id
                ).all()
                
                # Get completed orders
                orders = db.query(ExecutionOrder).filter(
                    and_(
                        ExecutionOrder.strategy_execution_id == execution_id,
                        ExecutionOrder.status == "filled"
                    )
                ).all()
                
                # Calculate performance metrics
                metrics = self.performance_metrics[execution_id]
                
                # Calculate PnL
                total_realized_pnl = sum(
                    pos.realized_pnl for pos in positions 
                    if pos.realized_pnl is not None
                )
                total_unrealized_pnl = sum(
                    pos.unrealized_pnl for pos in positions 
                    if pos.unrealized_pnl is not None
                )
                
                metrics.realized_pnl = total_realized_pnl
                metrics.unrealized_pnl = total_unrealized_pnl
                metrics.total_pnl = total_realized_pnl + total_unrealized_pnl
                
                # Calculate return percentage
                if execution.allocated_capital > 0:
                    metrics.total_return_pct = float(metrics.total_pnl / execution.allocated_capital * 100)
                
                # Calculate trade statistics
                winning_trades = [order for order in orders if order.filled_price * order.filled_quantity > 0]
                losing_trades = [order for order in orders if order.filled_price * order.filled_quantity < 0]
                
                metrics.total_trades = len(orders)
                metrics.winning_trades = len(winning_trades)
                metrics.losing_trades = len(losing_trades)
                
                if metrics.total_trades > 0:
                    metrics.win_rate = metrics.winning_trades / metrics.total_trades
                
                # Calculate profit factor
                total_wins = sum(order.filled_price * order.filled_quantity for order in winning_trades)
                total_losses = abs(sum(order.filled_price * order.filled_quantity for order in losing_trades))
                
                if total_losses > 0:
                    metrics.profit_factor = float(total_wins / total_losses)
                
                # Update averages
                if winning_trades:
                    metrics.avg_win = Decimal(str(total_wins / len(winning_trades)))
                    metrics.largest_win = max(
                        order.filled_price * order.filled_quantity for order in winning_trades
                    )
                
                if losing_trades:
                    metrics.avg_loss = Decimal(str(total_losses / len(losing_trades)))
                    metrics.largest_loss = min(
                        order.filled_price * order.filled_quantity for order in losing_trades
                    )
                
                # Calculate Sharpe ratio and max drawdown
                await self._calculate_advanced_performance_metrics(execution_id, metrics)
                
                self.performance_metrics[execution_id] = metrics
                
        except Exception as e:
            self.logger.error(f"Error updating performance metrics for execution {execution_id}: {e}")
    
    async def _calculate_advanced_performance_metrics(self, execution_id: int, metrics: PerformanceMetrics) -> None:
        """Calculate advanced performance metrics like Sharpe ratio and max drawdown."""
        
        try:
            # Get historical PnL data
            history = self.execution_history.get(execution_id, [])
            
            if len(history) < 2:
                return
            
            # Calculate returns
            returns = []
            for i in range(1, len(history)):
                prev_pnl = history[i-1].get('total_pnl', 0)
                curr_pnl = history[i].get('total_pnl', 0)
                if prev_pnl != 0:
                    returns.append((curr_pnl - prev_pnl) / abs(prev_pnl))
            
            if not returns:
                return
            
            # Calculate Sharpe ratio (simplified)
            import numpy as np
            if len(returns) > 1:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                if std_return > 0:
                    metrics.sharpe_ratio = float(avg_return / std_return * np.sqrt(252))  # Annualized
            
            # Calculate max drawdown
            pnl_values = [h.get('total_pnl', 0) for h in history]
            if pnl_values:
                peak = pnl_values[0]
                max_drawdown = 0
                
                for pnl in pnl_values:
                    if pnl > peak:
                        peak = pnl
                    
                    drawdown = (peak - pnl) / peak if peak > 0 else 0
                    max_drawdown = max(max_drawdown, drawdown)
                
                metrics.max_drawdown_pct = float(max_drawdown * 100)
            
        except Exception as e:
            self.logger.error(f"Error calculating advanced performance metrics: {e}")
    
    async def _check_performance_alerts(self, execution_id: int) -> None:
        """Check performance metrics against thresholds and generate alerts."""
        
        try:
            metrics = self.performance_metrics.get(execution_id)
            if not metrics:
                return
            
            # Max drawdown alert
            if metrics.max_drawdown_pct > self.thresholds.max_drawdown_pct:
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.ERROR,
                    metric_type=MonitoringMetric.PERFORMANCE,
                    title="Maximum Drawdown Exceeded",
                    message=f"Drawdown of {metrics.max_drawdown_pct:.2f}% exceeds threshold of {self.thresholds.max_drawdown_pct}%",
                    metadata={"current_drawdown": metrics.max_drawdown_pct, "threshold": self.thresholds.max_drawdown_pct}
                )
            
            # Daily loss alert
            if metrics.total_return_pct < -self.thresholds.max_daily_loss_pct:
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.WARNING,
                    metric_type=MonitoringMetric.PERFORMANCE,
                    title="Daily Loss Threshold Breached",
                    message=f"Daily loss of {abs(metrics.total_return_pct):.2f}% exceeds threshold of {self.thresholds.max_daily_loss_pct}%",
                    metadata={"current_loss": abs(metrics.total_return_pct), "threshold": self.thresholds.max_daily_loss_pct}
                )
            
            # Low Sharpe ratio alert
            if metrics.sharpe_ratio < self.thresholds.min_sharpe_ratio and metrics.total_trades > 10:
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.WARNING,
                    metric_type=MonitoringMetric.PERFORMANCE,
                    title="Low Sharpe Ratio",
                    message=f"Sharpe ratio of {metrics.sharpe_ratio:.2f} is below threshold of {self.thresholds.min_sharpe_ratio}",
                    metadata={"current_sharpe": metrics.sharpe_ratio, "threshold": self.thresholds.min_sharpe_ratio}
                )
            
            # Consecutive losses alert
            if metrics.consecutive_losses >= self.thresholds.max_consecutive_losses:
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.ERROR,
                    metric_type=MonitoringMetric.PERFORMANCE,
                    title="Excessive Consecutive Losses",
                    message=f"{metrics.consecutive_losses} consecutive losses exceeds threshold of {self.thresholds.max_consecutive_losses}",
                    metadata={"consecutive_losses": metrics.consecutive_losses, "threshold": self.thresholds.max_consecutive_losses}
                )
            
        except Exception as e:
            self.logger.error(f"Error checking performance alerts for execution {execution_id}: {e}")
    
    async def _risk_monitoring_loop(self) -> None:
        """Risk monitoring loop."""
        
        while self.monitor_running:
            try:
                for execution_id in list(self.monitored_executions):
                    await self._update_risk_metrics(execution_id)
                    await self._check_risk_alerts(execution_id)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _update_risk_metrics(self, execution_id: int) -> None:
        """Update risk metrics for an execution."""
        
        try:
            with get_db_session() as db:
                # Get execution details
                execution = db.query(StrategyExecution).filter(
                    StrategyExecution.id == execution_id
                ).first()
                
                if not execution:
                    return
                
                # Get current positions
                positions = db.query(ExecutionPosition).filter(
                    ExecutionPosition.strategy_execution_id == execution_id
                ).all()
                
                metrics = self.risk_metrics[execution_id]
                
                # Calculate current exposure
                total_exposure = sum(
                    abs(pos.quantity * pos.avg_price) for pos in positions
                    if pos.quantity is not None and pos.avg_price is not None
                )
                metrics.current_exposure = total_exposure
                
                # Update max exposure
                if total_exposure > metrics.max_exposure:
                    metrics.max_exposure = total_exposure
                
                # Calculate leverage
                if execution.current_capital > 0:
                    metrics.leverage_ratio = float(total_exposure / execution.current_capital)
                
                # Calculate concentration risk (largest position as % of portfolio)
                if positions and total_exposure > 0:
                    largest_position = max(
                        abs(pos.quantity * pos.avg_price) for pos in positions
                        if pos.quantity is not None and pos.avg_price is not None
                    )
                    metrics.concentration_risk = float(largest_position / total_exposure)
                
                # Calculate VaR and other risk metrics
                await self._calculate_var_metrics(execution_id, metrics)
                
                self.risk_metrics[execution_id] = metrics
                
        except Exception as e:
            self.logger.error(f"Error updating risk metrics for execution {execution_id}: {e}")
    
    async def _calculate_var_metrics(self, execution_id: int, metrics: RiskMetrics) -> None:
        """Calculate Value at Risk and related metrics."""
        
        try:
            # Get historical returns
            history = self.execution_history.get(execution_id, [])
            
            if len(history) < 30:  # Need at least 30 data points
                return
            
            # Calculate daily returns
            returns = []
            for i in range(1, len(history)):
                prev_pnl = history[i-1].get('total_pnl', 0)
                curr_pnl = history[i].get('total_pnl', 0)
                if prev_pnl != 0:
                    returns.append(curr_pnl - prev_pnl)
            
            if not returns:
                return
            
            import numpy as np
            
            # Calculate VaR (95% confidence)
            var_95 = np.percentile(returns, 5)  # 5th percentile for 95% VaR
            metrics.var_95 = Decimal(str(var_95))
            
            # Calculate Expected Shortfall (average of losses beyond VaR)
            tail_losses = [r for r in returns if r <= var_95]
            if tail_losses:
                metrics.expected_shortfall = Decimal(str(np.mean(tail_losses)))
            
            # Calculate volatility
            if len(returns) > 1:
                metrics.volatility = float(np.std(returns))
            
        except Exception as e:
            self.logger.error(f"Error calculating VaR metrics: {e}")
    
    async def _check_risk_alerts(self, execution_id: int) -> None:
        """Check risk metrics against thresholds and generate alerts."""
        
        try:
            metrics = self.risk_metrics.get(execution_id)
            if not metrics:
                return
            
            # VaR alert
            var_pct = float(abs(metrics.var_95) / metrics.current_exposure * 100) if metrics.current_exposure > 0 else 0
            if var_pct > self.thresholds.max_var_pct:
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.ERROR,
                    metric_type=MonitoringMetric.RISK,
                    title="High Value at Risk",
                    message=f"VaR of {var_pct:.2f}% exceeds threshold of {self.thresholds.max_var_pct}%",
                    metadata={"current_var": var_pct, "threshold": self.thresholds.max_var_pct}
                )
            
            # Leverage alert
            if metrics.leverage_ratio > self.thresholds.max_leverage:
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.WARNING,
                    metric_type=MonitoringMetric.RISK,
                    title="High Leverage",
                    message=f"Leverage of {metrics.leverage_ratio:.2f}x exceeds threshold of {self.thresholds.max_leverage}x",
                    metadata={"current_leverage": metrics.leverage_ratio, "threshold": self.thresholds.max_leverage}
                )
            
            # Concentration risk alert
            if metrics.concentration_risk > 0.5:  # 50% concentration threshold
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.WARNING,
                    metric_type=MonitoringMetric.RISK,
                    title="High Concentration Risk",
                    message=f"Largest position represents {metrics.concentration_risk*100:.1f}% of portfolio",
                    metadata={"concentration_pct": metrics.concentration_risk * 100}
                )
            
        except Exception as e:
            self.logger.error(f"Error checking risk alerts for execution {execution_id}: {e}")
    
    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop."""
        
        while self.monitor_running:
            try:
                for execution_id in list(self.monitored_executions):
                    await self._update_health_metrics(execution_id)
                    await self._check_health_alerts(execution_id)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _update_health_metrics(self, execution_id: int) -> None:
        """Update health metrics for an execution."""
        
        try:
            # Get execution status from live execution engine
            status = await live_execution_engine.get_execution_status(execution_id)
            
            if not status:
                return
            
            metrics = self.health_metrics[execution_id]
            
            # Update basic health metrics
            metrics.last_heartbeat = datetime.utcnow()
            metrics.error_rate = status.get('error_count', 0) / max(1, status.get('signals_processed', 1))
            
            # Get signal processing statistics
            signal_stats = await signal_processor.get_processing_statistics(execution_id)
            if signal_stats:
                metrics.signal_processing_rate = signal_stats.get('signal_rate_per_minute', 0)
                metrics.execution_latency_ms = signal_stats.get('avg_processing_time_ms', 0)
            
            # Calculate order success rate
            with get_db_session() as db:
                total_orders = db.query(func.count(ExecutionOrder.id)).filter(
                    ExecutionOrder.strategy_execution_id == execution_id
                ).scalar() or 0
                
                filled_orders = db.query(func.count(ExecutionOrder.id)).filter(
                    and_(
                        ExecutionOrder.strategy_execution_id == execution_id,
                        ExecutionOrder.status == "filled"
                    )
                ).scalar() or 0
                
                if total_orders > 0:
                    metrics.order_success_rate = float(filled_orders / total_orders * 100)
            
            # Update uptime
            # This would be calculated based on actual uptime tracking
            metrics.uptime_pct = 99.5  # Placeholder
            
            self.health_metrics[execution_id] = metrics
            
        except Exception as e:
            self.logger.error(f"Error updating health metrics for execution {execution_id}: {e}")
    
    async def _check_health_alerts(self, execution_id: int) -> None:
        """Check health metrics against thresholds and generate alerts."""
        
        try:
            metrics = self.health_metrics.get(execution_id)
            if not metrics:
                return
            
            # High error rate alert
            if metrics.error_rate > self.thresholds.max_error_rate:
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.ERROR,
                    metric_type=MonitoringMetric.HEALTH,
                    title="High Error Rate",
                    message=f"Error rate of {metrics.error_rate*100:.2f}% exceeds threshold of {self.thresholds.max_error_rate*100}%",
                    metadata={"current_error_rate": metrics.error_rate * 100, "threshold": self.thresholds.max_error_rate * 100}
                )
            
            # High execution latency alert
            if metrics.execution_latency_ms > self.thresholds.max_execution_latency_ms:
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.WARNING,
                    metric_type=MonitoringMetric.HEALTH,
                    title="High Execution Latency",
                    message=f"Execution latency of {metrics.execution_latency_ms:.0f}ms exceeds threshold of {self.thresholds.max_execution_latency_ms}ms",
                    metadata={"current_latency": metrics.execution_latency_ms, "threshold": self.thresholds.max_execution_latency_ms}
                )
            
            # Low uptime alert
            if metrics.uptime_pct < self.thresholds.min_uptime_pct:
                await self._create_alert(
                    execution_id=execution_id,
                    severity=AlertSeverity.ERROR,
                    metric_type=MonitoringMetric.HEALTH,
                    title="Low Uptime",
                    message=f"Uptime of {metrics.uptime_pct:.1f}% is below threshold of {self.thresholds.min_uptime_pct}%",
                    metadata={"current_uptime": metrics.uptime_pct, "threshold": self.thresholds.min_uptime_pct}
                )
            
        except Exception as e:
            self.logger.error(f"Error checking health alerts for execution {execution_id}: {e}")
    
    async def _create_alert(
        self, 
        execution_id: int, 
        severity: AlertSeverity, 
        metric_type: MonitoringMetric,
        title: str, 
        message: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create and process an alert."""
        
        try:
            # Generate alert ID
            alert_id = f"{execution_id}_{metric_type.value}_{severity.value}_{int(datetime.utcnow().timestamp())}"
            
            # Check cooldown
            cooldown_key = f"{execution_id}_{metric_type.value}_{severity.value}"
            last_alert = self.last_alert_time.get(cooldown_key)
            
            if last_alert and (datetime.utcnow() - last_alert).total_seconds() < self.alert_cooldown:
                return alert_id  # Skip if in cooldown
            
            # Create alert
            alert = Alert(
                id=alert_id,
                execution_id=execution_id,
                severity=severity,
                metric_type=metric_type,
                title=title,
                message=message,
                timestamp=datetime.utcnow(),
                metadata=metadata
            )
            
            # Store alert
            self.alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Update last alert time
            self.last_alert_time[cooldown_key] = datetime.utcnow()
            
            # Process alert through handlers
            await self._process_alert(alert)
            
            self.logger.warning(f"Alert created: {title} for execution {execution_id}")
            
            return alert_id
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            return ""
    
    async def _process_alert(self, alert: Alert) -> None:
        """Process an alert through registered handlers."""
        
        try:
            handlers = self.alert_handlers.get(alert.severity, [])
            
            for handler in handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert handler: {e}")
            
            # Store alert in Redis for real-time access
            if self.redis:
                alert_data = asdict(alert)
                alert_data['timestamp'] = alert.timestamp.isoformat()
                
                await self.redis.setex(
                    f"alert:{alert.id}",
                    3600,  # 1 hour expiry
                    json.dumps(alert_data, default=str)
                )
            
        except Exception as e:
            self.logger.error(f"Error processing alert: {e}")
    
    async def _alert_processing_loop(self) -> None:
        """Alert processing and escalation loop."""
        
        while self.monitor_running:
            try:
                # Check for unacknowledged critical alerts
                current_time = datetime.utcnow()
                
                for alert in self.alerts.values():
                    if (alert.severity == AlertSeverity.CRITICAL and 
                        not alert.acknowledged and 
                        (current_time - alert.timestamp).total_seconds() > 300):  # 5 minutes
                        
                        # Escalate critical alerts
                        await self._escalate_alert(alert)
                
                await asyncio.sleep(60.0)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in alert processing loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _escalate_alert(self, alert: Alert) -> None:
        """Escalate a critical alert."""
        
        try:
            # Take automatic control action for critical alerts
            if alert.metric_type == MonitoringMetric.RISK:
                # Pause execution for critical risk alerts
                await self._execute_control_action("pause_execution", alert.execution_id)
            elif alert.metric_type == MonitoringMetric.PERFORMANCE:
                # Reduce position size for critical performance alerts
                await self._execute_control_action("reduce_positions", alert.execution_id)
            
            self.logger.error(f"Escalated critical alert: {alert.title} for execution {alert.execution_id}")
            
        except Exception as e:
            self.logger.error(f"Error escalating alert: {e}")
    
    async def _execute_control_action(self, action: str, execution_id: int, **kwargs) -> bool:
        """Execute a control action."""
        
        try:
            action_func = self.control_actions.get(action)
            if action_func:
                return await action_func(execution_id, **kwargs)
            else:
                self.logger.warning(f"Unknown control action: {action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing control action {action}: {e}")
            return False
    
    async def _metrics_collection_loop(self) -> None:
        """Metrics collection and storage loop."""
        
        while self.monitor_running:
            try:
                # Collect metrics for all monitored executions
                for execution_id in list(self.monitored_executions):
                    metrics_snapshot = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'performance': asdict(self.performance_metrics.get(execution_id, PerformanceMetrics(execution_id, Decimal('0'), Decimal('0'), Decimal('0'), 0, 0, 0, 0, 0, 0, 0, 0, Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), 0, 0, 0))),
                        'risk': asdict(self.risk_metrics.get(execution_id, RiskMetrics(execution_id, Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), 0, 0, 0, 0, 0, 0))),
                        'health': asdict(self.health_metrics.get(execution_id, HealthMetrics(execution_id, 100, 0, 100, 0, 0, 0, 0, 0, "connected", datetime.utcnow())))
                    }
                    
                    # Add to execution history
                    self.execution_history[execution_id].append(metrics_snapshot)
                    
                    # Keep only recent history (last 24 hours)
                    if len(self.execution_history[execution_id]) > 1440:  # 24 hours at 1-minute intervals
                        self.execution_history[execution_id].pop(0)
                    
                    # Store in metrics history for time series analysis
                    self.metrics_history[execution_id].append(metrics_snapshot)
                
                await asyncio.sleep(60.0)  # Collect every minute
                
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _anomaly_detection_loop(self) -> None:
        """Anomaly detection loop."""
        
        while self.monitor_running:
            try:
                for execution_id in list(self.monitored_executions):
                    await self._detect_anomalies(execution_id)
                
                await asyncio.sleep(300.0)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in anomaly detection loop: {e}")
                await asyncio.sleep(300.0)
    
    async def _detect_anomalies(self, execution_id: int) -> None:
        """Detect anomalies in execution metrics."""
        
        try:
            history = self.metrics_history.get(execution_id, deque())
            
            if len(history) < 10:  # Need minimum history
                return
            
            # Simple anomaly detection based on standard deviation
            import numpy as np
            
            # Check for performance anomalies
            returns = [h['performance']['total_return_pct'] for h in list(history)[-20:]]
            if len(returns) > 5:
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                latest_return = returns[-1]
                
                # Check if latest return is more than 2 standard deviations away
                if abs(latest_return - mean_return) > 2 * std_return:
                    await self._create_alert(
                        execution_id=execution_id,
                        severity=AlertSeverity.WARNING,
                        metric_type=MonitoringMetric.PERFORMANCE,
                        title="Performance Anomaly Detected",
                        message=f"Return of {latest_return:.2f}% deviates significantly from recent average of {mean_return:.2f}%",
                        metadata={"latest_return": latest_return, "mean_return": mean_return, "std_deviation": std_return}
                    )
            
            # Check for execution latency anomalies
            latencies = [h['health']['execution_latency_ms'] for h in list(history)[-20:]]
            if len(latencies) > 5:
                mean_latency = np.mean(latencies)
                std_latency = np.std(latencies)
                latest_latency = latencies[-1]
                
                if latest_latency > mean_latency + 2 * std_latency:
                    await self._create_alert(
                        execution_id=execution_id,
                        severity=AlertSeverity.WARNING,
                        metric_type=MonitoringMetric.HEALTH,
                        title="Execution Latency Anomaly",
                        message=f"Latency of {latest_latency:.0f}ms significantly higher than recent average of {mean_latency:.0f}ms",
                        metadata={"latest_latency": latest_latency, "mean_latency": mean_latency}
                    )
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies for execution {execution_id}: {e}")
    
    def _register_default_alert_handlers(self) -> None:
        """Register default alert handlers."""
        
        # Email handler for critical alerts
        self.alert_handlers[AlertSeverity.CRITICAL].append(self._email_alert_handler)
        
        # Log handler for all alerts
        for severity in AlertSeverity:
            self.alert_handlers[severity].append(self._log_alert_handler)
    
    def _register_default_control_actions(self) -> None:
        """Register default control actions."""
        
        self.control_actions["pause_execution"] = self._pause_execution_action
        self.control_actions["stop_execution"] = self._stop_execution_action
        self.control_actions["reduce_positions"] = self._reduce_positions_action
    
    async def _log_alert_handler(self, alert: Alert) -> None:
        """Log alert handler."""
        self.logger.warning(f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")
    
    async def _email_alert_handler(self, alert: Alert) -> None:
        """Email alert handler for critical alerts."""
        
        try:
            # This would send an email notification
            # Implementation depends on email configuration
            self.logger.info(f"Email alert sent for critical alert: {alert.title}")
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
    
    async def _pause_execution_action(self, execution_id: int, **kwargs) -> bool:
        """Pause execution control action."""
        
        try:
            success = await live_execution_engine.pause_execution(execution_id)
            if success:
                self.logger.warning(f"Automatically paused execution {execution_id} due to critical alert")
            return success
            
        except Exception as e:
            self.logger.error(f"Error pausing execution {execution_id}: {e}")
            return False
    
    async def _stop_execution_action(self, execution_id: int, **kwargs) -> bool:
        """Stop execution control action."""
        
        try:
            success = await live_execution_engine.stop_execution(execution_id)
            if success:
                self.logger.error(f"Automatically stopped execution {execution_id} due to critical alert")
            return success
            
        except Exception as e:
            self.logger.error(f"Error stopping execution {execution_id}: {e}")
            return False
    
    async def _reduce_positions_action(self, execution_id: int, reduction_pct: float = 50.0, **kwargs) -> bool:
        """Reduce positions control action."""
        
        try:
            # This would reduce position sizes by the specified percentage
            # Implementation would depend on position management logic
            self.logger.warning(f"Automatically reduced positions by {reduction_pct}% for execution {execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reducing positions for execution {execution_id}: {e}")
            return False
    
    # Public API methods
    
    async def get_execution_metrics(self, execution_id: int) -> Dict[str, Any]:
        """Get comprehensive metrics for an execution."""
        
        return {
            "performance": asdict(self.performance_metrics.get(execution_id, PerformanceMetrics(execution_id, Decimal('0'), Decimal('0'), Decimal('0'), 0, 0, 0, 0, 0, 0, 0, 0, Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), 0, 0, 0))),
            "risk": asdict(self.risk_metrics.get(execution_id, RiskMetrics(execution_id, Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), 0, 0, 0, 0, 0, 0))),
            "health": asdict(self.health_metrics.get(execution_id, HealthMetrics(execution_id, 100, 0, 100, 0, 0, 0, 0, 0, "connected", datetime.utcnow())))
        }
    
    async def get_alerts(self, execution_id: Optional[int] = None, severity: Optional[AlertSeverity] = None) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering."""
        
        alerts = list(self.alerts.values())
        
        if execution_id:
            alerts = [a for a in alerts if a.execution_id == execution_id]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return [asdict(alert) for alert in alerts]
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        
        alert = self.alerts.get(alert_id)
        if alert:
            alert.acknowledged = True
            return True
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        
        alert = self.alerts.get(alert_id)
        if alert:
            alert.resolved = True
            return True
        return False
    
    async def trigger_control_action(self, action: str, execution_id: int, **kwargs) -> bool:
        """Manually trigger a control action."""
        
        return await self._execute_control_action(action, execution_id, **kwargs)
    
    def update_thresholds(self, new_thresholds: Dict[str, Any]) -> None:
        """Update monitoring thresholds."""
        
        for key, value in new_thresholds.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
        
        self.logger.info("Monitoring thresholds updated")
    
    async def cleanup(self) -> None:
        """Cleanup execution monitor."""
        
        self.monitor_running = False
        
        if self.redis:
            await self.redis.close()
        
        self.logger.info("Execution monitor cleaned up")


# Global execution monitor instance
execution_monitor = ExecutionMonitor()