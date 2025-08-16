"""
Live performance monitoring service for paper trading.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.paper_trading import (
    PaperTradingSession,
    PaperPosition,
    PaperTransaction,
    PaperPortfolioSnapshot
)
from app.services.portfolio_tracker import portfolio_tracker, PerformanceMetrics
from app.services.risk_manager import risk_manager
from app.database.connection import get_db_session


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    alert_type: str
    session_id: int
    message: str
    severity: str
    timestamp: datetime
    value: Optional[Decimal] = None
    threshold: Optional[Decimal] = None


@dataclass
class LiveMetrics:
    """Live performance metrics."""
    session_id: int
    timestamp: datetime
    total_value: Decimal
    total_return_pct: Decimal
    day_pnl: Decimal
    day_pnl_pct: Decimal
    drawdown_pct: Decimal
    sharpe_ratio: Optional[Decimal]
    win_rate: Optional[Decimal]
    num_trades_today: int
    active_positions: int


@dataclass
class TradeSignal:
    """Trade signal for monitoring."""
    session_id: int
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    signal_type: str
    confidence: Optional[Decimal] = None


class MonitoringService:
    """Live performance monitoring and alerting service."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.logger = logging.getLogger(__name__)
        self.redis_url = redis_url
        self.redis = None
        
        # Monitoring state
        self.monitoring_active = False
        self.monitored_sessions: Dict[int, Dict] = {}
        
        # Alert thresholds
        self.alert_thresholds = {
            "daily_loss_pct": Decimal("5.0"),        # 5% daily loss
            "drawdown_pct": Decimal("10.0"),         # 10% drawdown
            "volatility_spike": Decimal("50.0"),     # 50% volatility increase
            "win_rate_drop": Decimal("20.0"),        # 20% win rate drop
            "consecutive_losses": 5,                  # 5 consecutive losses
            "position_concentration": Decimal("30.0") # 30% in single position
        }
        
        # Performance tracking
        self.performance_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.trade_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        self.alerts_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # WebSocket connections for real-time updates
        self.websocket_connections: Dict[str, Any] = {}
        
        # Event subscribers
        self.performance_subscribers: List[Callable] = []
        self.alert_subscribers: List[Callable] = []
        
    async def initialize(self) -> None:
        """Initialize the monitoring service."""
        
        # Connect to Redis
        self.redis = redis.from_url(self.redis_url)
        
        # Load active sessions
        await self._load_active_sessions()
        
        # Start monitoring loops
        if not self.monitoring_active:
            self.monitoring_active = True
            asyncio.create_task(self._performance_monitoring_loop())
            asyncio.create_task(self._alert_monitoring_loop())
            asyncio.create_task(self._real_time_data_publisher())
        
        self.logger.info("Monitoring service initialized")
    
    async def _load_active_sessions(self) -> None:
        """Load active trading sessions for monitoring."""
        
        try:
            with get_db_session() as db:
                active_sessions = db.query(PaperTradingSession).filter(
                    PaperTradingSession.is_active == True
                ).all()
                
                for session in active_sessions:
                    await self.start_monitoring_session(session.id)
                
            self.logger.info(f"Loaded {len(active_sessions)} sessions for monitoring")
            
        except Exception as e:
            self.logger.error(f"Error loading active sessions: {e}")
    
    async def start_monitoring_session(self, session_id: int) -> None:
        """Start monitoring a trading session."""
        
        if session_id not in self.monitored_sessions:
            self.monitored_sessions[session_id] = {
                "start_time": datetime.utcnow(),
                "last_update": datetime.utcnow(),
                "last_snapshot": None,
                "consecutive_losses": 0,
                "peak_value": Decimal("0"),
                "alerts_sent": set()
            }
            
        self.logger.info(f"Started monitoring session {session_id}")
    
    async def stop_monitoring_session(self, session_id: int) -> None:
        """Stop monitoring a trading session."""
        
        if session_id in self.monitored_sessions:
            del self.monitored_sessions[session_id]
            
        self.logger.info(f"Stopped monitoring session {session_id}")
    
    async def _performance_monitoring_loop(self) -> None:
        """Main performance monitoring loop."""
        
        while self.monitoring_active:
            try:
                for session_id in list(self.monitored_sessions.keys()):
                    await self._monitor_session_performance(session_id)
                
                await asyncio.sleep(10.0)  # Monitor every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(30.0)
    
    async def _monitor_session_performance(self, session_id: int) -> None:
        """Monitor performance for a specific session."""
        
        try:
            # Get current portfolio summary
            portfolio = await portfolio_tracker.get_portfolio_summary(session_id)
            if not portfolio:
                return
            
            # Get performance metrics
            performance_metrics = await portfolio_tracker.get_performance_metrics(session_id)
            
            # Create live metrics
            live_metrics = LiveMetrics(
                session_id=session_id,
                timestamp=datetime.utcnow(),
                total_value=portfolio.total_value,
                total_return_pct=portfolio.total_pnl_pct,
                day_pnl=portfolio.day_pnl,
                day_pnl_pct=portfolio.day_pnl_pct,
                drawdown_pct=performance_metrics.max_drawdown_pct if performance_metrics else Decimal("0"),
                sharpe_ratio=performance_metrics.sharpe_ratio if performance_metrics else None,
                win_rate=performance_metrics.win_rate if performance_metrics else None,
                num_trades_today=await self._count_todays_trades(session_id),
                active_positions=portfolio.num_positions
            )
            
            # Store in history
            self.performance_history[session_id].append(live_metrics)
            
            # Update session state
            session_state = self.monitored_sessions[session_id]
            session_state["last_update"] = datetime.utcnow()
            session_state["last_snapshot"] = live_metrics
            
            # Update peak value
            if portfolio.total_value > session_state["peak_value"]:
                session_state["peak_value"] = portfolio.total_value
            
            # Publish real-time update
            await self._publish_performance_update(live_metrics)
            
            # Notify subscribers
            for subscriber in self.performance_subscribers:
                try:
                    await subscriber(live_metrics)
                except Exception as e:
                    self.logger.error(f"Error in performance subscriber: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error monitoring session {session_id} performance: {e}")
    
    async def _count_todays_trades(self, session_id: int) -> int:
        """Count trades executed today."""
        
        try:
            today = datetime.utcnow().date()
            with get_db_session() as db:
                count = db.query(func.count(PaperTransaction.id)).filter(
                    and_(
                        PaperTransaction.session_id == session_id,
                        func.date(PaperTransaction.executed_at) == today
                    )
                ).scalar()
                
                return count or 0
                
        except Exception as e:
            self.logger.error(f"Error counting today's trades: {e}")
            return 0
    
    async def _alert_monitoring_loop(self) -> None:
        """Alert monitoring loop."""
        
        while self.monitoring_active:
            try:
                for session_id in list(self.monitored_sessions.keys()):
                    await self._check_performance_alerts(session_id)
                
                await asyncio.sleep(30.0)  # Check alerts every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _check_performance_alerts(self, session_id: int) -> None:
        """Check for performance-based alerts."""
        
        try:
            session_state = self.monitored_sessions.get(session_id)
            if not session_state or not session_state["last_snapshot"]:
                return
            
            metrics = session_state["last_snapshot"]
            alerts_sent = session_state["alerts_sent"]
            
            # Daily loss alert
            if metrics.day_pnl_pct < -self.alert_thresholds["daily_loss_pct"]:
                alert_key = f"daily_loss_{datetime.utcnow().date()}"
                if alert_key not in alerts_sent:
                    await self._create_performance_alert(
                        session_id=session_id,
                        alert_type="daily_loss",
                        message=f"Daily loss of {metrics.day_pnl_pct:.2f}% exceeds threshold",
                        severity="high",
                        value=abs(metrics.day_pnl_pct),
                        threshold=self.alert_thresholds["daily_loss_pct"]
                    )
                    alerts_sent.add(alert_key)
            
            # Drawdown alert
            if metrics.drawdown_pct > self.alert_thresholds["drawdown_pct"]:
                alert_key = f"drawdown_{int(metrics.drawdown_pct)}"
                if alert_key not in alerts_sent:
                    await self._create_performance_alert(
                        session_id=session_id,
                        alert_type="drawdown",
                        message=f"Drawdown of {metrics.drawdown_pct:.2f}% exceeds threshold",
                        severity="high",
                        value=metrics.drawdown_pct,
                        threshold=self.alert_thresholds["drawdown_pct"]
                    )
                    alerts_sent.add(alert_key)
            
            # Volatility spike alert
            await self._check_volatility_spike(session_id, metrics)
            
            # Win rate drop alert
            if metrics.win_rate and metrics.win_rate < (100 - self.alert_thresholds["win_rate_drop"]):
                alert_key = f"win_rate_{int(metrics.win_rate)}"
                if alert_key not in alerts_sent:
                    await self._create_performance_alert(
                        session_id=session_id,
                        alert_type="win_rate_drop",
                        message=f"Win rate dropped to {metrics.win_rate:.2f}%",
                        severity="medium",
                        value=metrics.win_rate,
                        threshold=100 - self.alert_thresholds["win_rate_drop"]
                    )
                    alerts_sent.add(alert_key)
            
            # Consecutive losses alert
            await self._check_consecutive_losses(session_id)
            
        except Exception as e:
            self.logger.error(f"Error checking performance alerts for session {session_id}: {e}")
    
    async def _check_volatility_spike(self, session_id: int, current_metrics: LiveMetrics) -> None:
        """Check for volatility spikes."""
        
        try:
            history = self.performance_history[session_id]
            if len(history) < 10:  # Need at least 10 data points
                return
            
            # Calculate recent volatility
            recent_returns = []
            for i in range(1, min(10, len(history))):
                prev_value = float(history[-i-1].total_value)
                curr_value = float(history[-i].total_value)
                if prev_value > 0:
                    daily_return = (curr_value - prev_value) / prev_value
                    recent_returns.append(abs(daily_return))
            
            if recent_returns:
                import statistics
                current_volatility = statistics.mean(recent_returns)
                
                # Compare with historical volatility
                if len(history) >= 50:
                    historical_returns = []
                    for i in range(10, min(50, len(history))):
                        prev_value = float(history[-i-1].total_value)
                        curr_value = float(history[-i].total_value)
                        if prev_value > 0:
                            daily_return = (curr_value - prev_value) / prev_value
                            historical_returns.append(abs(daily_return))
                    
                    if historical_returns:
                        historical_volatility = statistics.mean(historical_returns)
                        
                        if historical_volatility > 0:
                            volatility_increase = (current_volatility - historical_volatility) / historical_volatility * 100
                            
                            if volatility_increase > float(self.alert_thresholds["volatility_spike"]):
                                await self._create_performance_alert(
                                    session_id=session_id,
                                    alert_type="volatility_spike",
                                    message=f"Volatility increased by {volatility_increase:.1f}%",
                                    severity="medium",
                                    value=Decimal(str(volatility_increase)),
                                    threshold=self.alert_thresholds["volatility_spike"]
                                )
                                
        except Exception as e:
            self.logger.error(f"Error checking volatility spike: {e}")
    
    async def _check_consecutive_losses(self, session_id: int) -> None:
        """Check for consecutive losses."""
        
        try:
            # Get recent trades
            with get_db_session() as db:
                recent_trades = db.query(PaperTransaction).filter(
                    PaperTransaction.session_id == session_id
                ).order_by(desc(PaperTransaction.executed_at)).limit(10).all()
                
                consecutive_losses = 0
                for trade in recent_trades:
                    # Calculate P&L for this trade (simplified)
                    if trade.side == "sell" and trade.cash_flow > 0:
                        # This is a closing trade, check P&L
                        if trade.cash_flow < trade.gross_amount:  # Loss
                            consecutive_losses += 1
                        else:
                            break
                    else:
                        break
                
                session_state = self.monitored_sessions[session_id]
                session_state["consecutive_losses"] = consecutive_losses
                
                if consecutive_losses >= self.alert_thresholds["consecutive_losses"]:
                    alert_key = f"consecutive_losses_{consecutive_losses}"
                    if alert_key not in session_state["alerts_sent"]:
                        await self._create_performance_alert(
                            session_id=session_id,
                            alert_type="consecutive_losses",
                            message=f"{consecutive_losses} consecutive losses detected",
                            severity="high",
                            value=Decimal(str(consecutive_losses)),
                            threshold=Decimal(str(self.alert_thresholds["consecutive_losses"]))
                        )
                        session_state["alerts_sent"].add(alert_key)
                        
        except Exception as e:
            self.logger.error(f"Error checking consecutive losses: {e}")
    
    async def _create_performance_alert(
        self,
        session_id: int,
        alert_type: str,
        message: str,
        severity: str,
        value: Optional[Decimal] = None,
        threshold: Optional[Decimal] = None
    ) -> None:
        """Create a performance alert."""
        
        alert = PerformanceAlert(
            alert_type=alert_type,
            session_id=session_id,
            message=message,
            severity=severity,
            timestamp=datetime.utcnow(),
            value=value,
            threshold=threshold
        )
        
        # Store in history
        self.alerts_history[session_id].append(alert)
        
        # Publish alert
        await self._publish_alert(alert)
        
        # Notify subscribers
        for subscriber in self.alert_subscribers:
            try:
                await subscriber(alert)
            except Exception as e:
                self.logger.error(f"Error in alert subscriber: {e}")
        
        self.logger.warning(f"Performance alert: {alert_type} - {message}")
    
    async def _real_time_data_publisher(self) -> None:
        """Publish real-time data to Redis channels."""
        
        while self.monitoring_active:
            try:
                for session_id, session_state in self.monitored_sessions.items():
                    if session_state["last_snapshot"]:
                        await self._publish_performance_update(session_state["last_snapshot"])
                
                await asyncio.sleep(5.0)  # Publish every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in real-time data publisher: {e}")
                await asyncio.sleep(10.0)
    
    async def _publish_performance_update(self, metrics: LiveMetrics) -> None:
        """Publish performance update to Redis."""
        
        if not self.redis:
            return
        
        try:
            # Convert to JSON-serializable format
            data = asdict(metrics)
            for key, value in data.items():
                if isinstance(value, Decimal):
                    data[key] = float(value)
                elif isinstance(value, datetime):
                    data[key] = value.isoformat()
            
            # Publish to session-specific channel
            await self.redis.publish(f"performance:{metrics.session_id}", json.dumps(data))
            
            # Publish to general performance channel
            await self.redis.publish("performance:all", json.dumps(data))
            
        except Exception as e:
            self.logger.error(f"Error publishing performance update: {e}")
    
    async def _publish_alert(self, alert: PerformanceAlert) -> None:
        """Publish alert to Redis."""
        
        if not self.redis:
            return
        
        try:
            # Convert to JSON-serializable format
            data = asdict(alert)
            for key, value in data.items():
                if isinstance(value, Decimal):
                    data[key] = float(value)
                elif isinstance(value, datetime):
                    data[key] = value.isoformat()
            
            # Publish to session-specific channel
            await self.redis.publish(f"alerts:{alert.session_id}", json.dumps(data))
            
            # Publish to general alerts channel
            await self.redis.publish("alerts:all", json.dumps(data))
            
        except Exception as e:
            self.logger.error(f"Error publishing alert: {e}")
    
    async def get_live_metrics(self, session_id: int) -> Optional[LiveMetrics]:
        """Get current live metrics for a session."""
        
        session_state = self.monitored_sessions.get(session_id)
        if session_state:
            return session_state["last_snapshot"]
        
        return None
    
    async def get_performance_history(
        self,
        session_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get performance history for a session."""
        
        history = list(self.performance_history[session_id])[-limit:]
        
        return [
            {
                "timestamp": metrics.timestamp.isoformat(),
                "total_value": float(metrics.total_value),
                "total_return_pct": float(metrics.total_return_pct),
                "day_pnl": float(metrics.day_pnl),
                "day_pnl_pct": float(metrics.day_pnl_pct),
                "drawdown_pct": float(metrics.drawdown_pct),
                "sharpe_ratio": float(metrics.sharpe_ratio) if metrics.sharpe_ratio else None,
                "win_rate": float(metrics.win_rate) if metrics.win_rate else None,
                "num_trades_today": metrics.num_trades_today,
                "active_positions": metrics.active_positions
            }
            for metrics in history
        ]
    
    async def get_recent_alerts(
        self,
        session_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent alerts for a session."""
        
        alerts = list(self.alerts_history[session_id])[-limit:]
        
        return [
            {
                "alert_type": alert.alert_type,
                "message": alert.message,
                "severity": alert.severity,
                "timestamp": alert.timestamp.isoformat(),
                "value": float(alert.value) if alert.value else None,
                "threshold": float(alert.threshold) if alert.threshold else None
            }
            for alert in alerts
        ]
    
    async def subscribe_to_performance_updates(self, callback: Callable[[LiveMetrics], None]) -> None:
        """Subscribe to performance updates."""
        
        self.performance_subscribers.append(callback)
    
    async def subscribe_to_alerts(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """Subscribe to performance alerts."""
        
        self.alert_subscribers.append(callback)
    
    async def set_alert_threshold(self, threshold_name: str, value: Decimal) -> None:
        """Set custom alert threshold."""
        
        if threshold_name in self.alert_thresholds:
            self.alert_thresholds[threshold_name] = value
            self.logger.info(f"Updated alert threshold {threshold_name} to {value}")
        else:
            raise ValueError(f"Unknown threshold: {threshold_name}")
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring service status."""
        
        return {
            "monitoring_active": self.monitoring_active,
            "monitored_sessions": len(self.monitored_sessions),
            "alert_thresholds": {k: float(v) if isinstance(v, Decimal) else v 
                               for k, v in self.alert_thresholds.items()},
            "performance_subscribers": len(self.performance_subscribers),
            "alert_subscribers": len(self.alert_subscribers),
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self) -> None:
        """Cleanup monitoring service."""
        
        self.monitoring_active = False
        
        if self.redis:
            await self.redis.close()
        
        self.logger.info("Monitoring service cleaned up")


# Global monitoring service instance
monitoring_service = MonitoringService()