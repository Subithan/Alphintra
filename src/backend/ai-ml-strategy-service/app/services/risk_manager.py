"""
Risk management service for paper trading.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.paper_trading import (
    PaperTradingSession,
    PaperPosition,
    PaperOrder,
    OrderSide
)
from app.services.portfolio_tracker import portfolio_tracker, PortfolioSummary
from app.services.market_data_service import market_data_service
from app.database.connection import get_db_session


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAlert(Enum):
    POSITION_SIZE_LIMIT = "position_size_limit"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    DRAWDOWN_LIMIT = "drawdown_limit"
    LEVERAGE_LIMIT = "leverage_limit"
    CONCENTRATION_LIMIT = "concentration_limit"
    VOLATILITY_SPIKE = "volatility_spike"
    MARGIN_CALL = "margin_call"


@dataclass
class RiskMetric:
    """Risk metric data structure."""
    name: str
    value: Decimal
    limit: Decimal
    utilization_pct: Decimal
    risk_level: RiskLevel
    breach: bool


@dataclass
class RiskAlert:
    """Risk alert data structure."""
    alert_type: str
    severity: RiskLevel
    message: str
    timestamp: datetime
    session_id: int
    symbol: Optional[str] = None
    current_value: Optional[Decimal] = None
    limit_value: Optional[Decimal] = None


@dataclass
class PositionSizing:
    """Position sizing recommendation."""
    symbol: str
    recommended_quantity: Decimal
    max_quantity: Decimal
    risk_percentage: Decimal
    stop_loss_price: Optional[Decimal] = None
    position_value: Optional[Decimal] = None
    rationale: str = ""


class RiskManager:
    """Comprehensive risk management service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_monitoring_active = False
        self.risk_alerts: Dict[int, List[RiskAlert]] = {}
        
        # Default risk parameters
        self.default_max_position_size_pct = Decimal("0.10")  # 10% of portfolio
        self.default_max_daily_loss_pct = Decimal("0.02")     # 2% daily loss limit
        self.default_max_drawdown_pct = Decimal("0.15")       # 15% drawdown limit
        self.default_max_leverage = Decimal("2.0")            # 2x leverage limit
        self.default_max_concentration_pct = Decimal("0.25")  # 25% in single position
        
        # Volatility thresholds
        self.volatility_spike_threshold = Decimal("0.05")     # 5% volatility spike
        self.margin_threshold = Decimal("0.75")               # 75% margin utilization
        
    async def initialize(self) -> None:
        """Initialize the risk management service."""
        
        # Start risk monitoring
        if not self.risk_monitoring_active:
            self.risk_monitoring_active = True
            asyncio.create_task(self._risk_monitoring_loop())
        
        self.logger.info("Risk management service initialized")
    
    async def _risk_monitoring_loop(self) -> None:
        """Main risk monitoring loop."""
        
        while self.risk_monitoring_active:
            try:
                # Get all active sessions
                with get_db_session() as db:
                    active_sessions = db.query(PaperTradingSession).filter(
                        PaperTradingSession.is_active == True
                    ).all()
                    
                    for session in active_sessions:
                        await self._monitor_session_risk(session.id)
                
                await asyncio.sleep(30.0)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _monitor_session_risk(self, session_id: int) -> None:
        """Monitor risk for a specific session."""
        
        try:
            # Get portfolio summary
            portfolio = await portfolio_tracker.get_portfolio_summary(session_id)
            if not portfolio:
                return
            
            # Check all risk metrics
            risk_metrics = await self.calculate_risk_metrics(session_id)
            
            # Check for risk breaches
            for metric in risk_metrics:
                if metric.breach:
                    await self._create_risk_alert(
                        session_id=session_id,
                        alert_type=metric.name,
                        severity=metric.risk_level,
                        message=f"{metric.name} breach: {metric.value} exceeds limit of {metric.limit}",
                        current_value=metric.value,
                        limit_value=metric.limit
                    )
            
            # Check for volatility spikes
            await self._check_volatility_spikes(session_id, portfolio)
            
            # Auto-liquidation if critical risk
            await self._check_auto_liquidation(session_id, risk_metrics)
            
        except Exception as e:
            self.logger.error(f"Error monitoring risk for session {session_id}: {e}")
    
    async def calculate_risk_metrics(self, session_id: int) -> List[RiskMetric]:
        """Calculate comprehensive risk metrics for a session."""
        
        risk_metrics = []
        
        try:
            # Get session and portfolio data
            with get_db_session() as db:
                session = db.query(PaperTradingSession).filter(
                    PaperTradingSession.id == session_id
                ).first()
                
                if not session:
                    return risk_metrics
            
            portfolio = await portfolio_tracker.get_portfolio_summary(session_id)
            if not portfolio:
                return risk_metrics
            
            # 1. Position Size Risk
            max_position_size = session.max_position_size or (portfolio.total_value * self.default_max_position_size_pct)
            largest_position = max((pos.market_value for pos in portfolio.positions), default=Decimal("0"))
            
            position_size_utilization = (largest_position / max_position_size) * 100 if max_position_size > 0 else Decimal("0")
            position_size_breach = largest_position > max_position_size
            
            risk_metrics.append(RiskMetric(
                name="position_size",
                value=largest_position,
                limit=max_position_size,
                utilization_pct=position_size_utilization,
                risk_level=self._get_risk_level(position_size_utilization),
                breach=position_size_breach
            ))
            
            # 2. Daily Loss Risk
            daily_loss_limit = session.max_daily_loss or (portfolio.total_value * self.default_max_daily_loss_pct)
            current_daily_loss = abs(min(portfolio.day_pnl, Decimal("0")))
            
            daily_loss_utilization = (current_daily_loss / daily_loss_limit) * 100 if daily_loss_limit > 0 else Decimal("0")
            daily_loss_breach = current_daily_loss > daily_loss_limit
            
            risk_metrics.append(RiskMetric(
                name="daily_loss",
                value=current_daily_loss,
                limit=daily_loss_limit,
                utilization_pct=daily_loss_utilization,
                risk_level=self._get_risk_level(daily_loss_utilization),
                breach=daily_loss_breach
            ))
            
            # 3. Drawdown Risk
            max_drawdown_limit = portfolio.total_value * self.default_max_drawdown_pct
            performance_metrics = await portfolio_tracker.get_performance_metrics(session_id)
            current_drawdown = performance_metrics.max_drawdown if performance_metrics else Decimal("0")
            
            drawdown_utilization = (current_drawdown / max_drawdown_limit) * 100 if max_drawdown_limit > 0 else Decimal("0")
            drawdown_breach = current_drawdown > max_drawdown_limit
            
            risk_metrics.append(RiskMetric(
                name="drawdown",
                value=current_drawdown,
                limit=max_drawdown_limit,
                utilization_pct=drawdown_utilization,
                risk_level=self._get_risk_level(drawdown_utilization),
                breach=drawdown_breach
            ))
            
            # 4. Leverage Risk
            leverage_limit = self.default_max_leverage
            current_leverage = portfolio.leverage
            
            leverage_utilization = (current_leverage / leverage_limit) * 100 if leverage_limit > 0 else Decimal("0")
            leverage_breach = current_leverage > leverage_limit
            
            risk_metrics.append(RiskMetric(
                name="leverage",
                value=current_leverage,
                limit=leverage_limit,
                utilization_pct=leverage_utilization,
                risk_level=self._get_risk_level(leverage_utilization),
                breach=leverage_breach
            ))
            
            # 5. Concentration Risk
            concentration_limit = portfolio.total_value * self.default_max_concentration_pct
            largest_position_value = max((pos.market_value for pos in portfolio.positions), default=Decimal("0"))
            
            concentration_utilization = (largest_position_value / concentration_limit) * 100 if concentration_limit > 0 else Decimal("0")
            concentration_breach = largest_position_value > concentration_limit
            
            risk_metrics.append(RiskMetric(
                name="concentration",
                value=largest_position_value,
                limit=concentration_limit,
                utilization_pct=concentration_utilization,
                risk_level=self._get_risk_level(concentration_utilization),
                breach=concentration_breach
            ))
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics for session {session_id}: {e}")
        
        return risk_metrics
    
    def _get_risk_level(self, utilization_pct: Decimal) -> RiskLevel:
        """Determine risk level based on utilization percentage."""
        
        if utilization_pct >= 100:
            return RiskLevel.CRITICAL
        elif utilization_pct >= 80:
            return RiskLevel.HIGH
        elif utilization_pct >= 60:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def _check_volatility_spikes(self, session_id: int, portfolio: PortfolioSummary) -> None:
        """Check for volatility spikes in positions."""
        
        try:
            for position in portfolio.positions:
                # Calculate recent volatility (simplified)
                daily_return_pct = abs(position.day_pnl_pct)
                
                if daily_return_pct > self.volatility_spike_threshold * 100:
                    await self._create_risk_alert(
                        session_id=session_id,
                        alert_type="volatility_spike",
                        severity=RiskLevel.HIGH,
                        message=f"Volatility spike detected in {position.symbol}: {daily_return_pct:.2f}% daily change",
                        symbol=position.symbol,
                        current_value=daily_return_pct
                    )
        
        except Exception as e:
            self.logger.error(f"Error checking volatility spikes: {e}")
    
    async def _check_auto_liquidation(self, session_id: int, risk_metrics: List[RiskMetric]) -> None:
        """Check if auto-liquidation should be triggered."""
        
        try:
            critical_breaches = [metric for metric in risk_metrics if metric.risk_level == RiskLevel.CRITICAL]
            
            if critical_breaches:
                with get_db_session() as db:
                    session = db.query(PaperTradingSession).filter(
                        PaperTradingSession.id == session_id
                    ).first()
                    
                    if session and session.auto_liquidation_enabled:
                        self.logger.warning(
                            f"Auto-liquidation triggered for session {session_id} "
                            f"due to critical risk breaches: {[m.name for m in critical_breaches]}"
                        )
                        
                        # Implement auto-liquidation logic here
                        # For now, just create alert
                        await self._create_risk_alert(
                            session_id=session_id,
                            alert_type="auto_liquidation",
                            severity=RiskLevel.CRITICAL,
                            message=f"Auto-liquidation triggered due to critical risk breaches"
                        )
        
        except Exception as e:
            self.logger.error(f"Error checking auto-liquidation: {e}")
    
    async def _create_risk_alert(
        self,
        session_id: int,
        alert_type: str,
        severity: RiskLevel,
        message: str,
        symbol: Optional[str] = None,
        current_value: Optional[Decimal] = None,
        limit_value: Optional[Decimal] = None
    ) -> None:
        """Create a risk alert."""
        
        alert = RiskAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            session_id=session_id,
            symbol=symbol,
            current_value=current_value,
            limit_value=limit_value
        )
        
        if session_id not in self.risk_alerts:
            self.risk_alerts[session_id] = []
        
        self.risk_alerts[session_id].append(alert)
        
        # Keep only last 100 alerts per session
        self.risk_alerts[session_id] = self.risk_alerts[session_id][-100:]
        
        self.logger.warning(f"Risk alert created: {alert_type} - {message}")
    
    async def calculate_position_size(
        self,
        session_id: int,
        symbol: str,
        side: str,
        risk_percentage: Decimal = Decimal("0.01"),  # 1% risk per trade
        stop_loss_pct: Optional[Decimal] = None
    ) -> PositionSizing:
        """Calculate optimal position size based on risk parameters."""
        
        try:
            # Get portfolio summary
            portfolio = await portfolio_tracker.get_portfolio_summary(session_id)
            if not portfolio:
                raise ValueError("Portfolio not found")
            
            # Get current market price
            current_price = await market_data_service.get_current_price(symbol)
            if not current_price:
                raise ValueError("Current price not available")
            
            # Get session risk parameters
            with get_db_session() as db:
                session = db.query(PaperTradingSession).filter(
                    PaperTradingSession.id == session_id
                ).first()
                
                if not session:
                    raise ValueError("Session not found")
            
            # Calculate risk amount
            risk_amount = portfolio.total_value * risk_percentage
            
            # Calculate stop loss price if not provided
            stop_loss_price = None
            if stop_loss_pct:
                if side == OrderSide.BUY.value:
                    stop_loss_price = current_price * (1 - stop_loss_pct)
                else:
                    stop_loss_price = current_price * (1 + stop_loss_pct)
            
            # Calculate position size based on risk
            if stop_loss_price:
                price_diff = abs(current_price - stop_loss_price)
                if price_diff > 0:
                    recommended_quantity = risk_amount / price_diff
                else:
                    recommended_quantity = Decimal("0")
            else:
                # Default to 2% price movement risk
                default_stop_pct = Decimal("0.02")
                price_diff = current_price * default_stop_pct
                recommended_quantity = risk_amount / price_diff
            
            # Apply position size limits
            max_position_size = session.max_position_size or (portfolio.total_value * self.default_max_position_size_pct)
            max_quantity_by_size = max_position_size / current_price
            
            # Apply concentration limits
            concentration_limit = portfolio.total_value * self.default_max_concentration_pct
            max_quantity_by_concentration = concentration_limit / current_price
            
            # Take the minimum of all limits
            max_quantity = min(max_quantity_by_size, max_quantity_by_concentration)
            recommended_quantity = min(recommended_quantity, max_quantity)
            
            # Calculate position value
            position_value = recommended_quantity * current_price
            
            # Generate rationale
            rationale_parts = []
            if recommended_quantity == max_quantity_by_size:
                rationale_parts.append("limited by max position size")
            if recommended_quantity == max_quantity_by_concentration:
                rationale_parts.append("limited by concentration limit")
            if stop_loss_price:
                rationale_parts.append(f"based on {risk_percentage*100:.1f}% risk with stop loss")
            else:
                rationale_parts.append(f"based on {risk_percentage*100:.1f}% risk with 2% default stop")
            
            rationale = ", ".join(rationale_parts)
            
            return PositionSizing(
                symbol=symbol,
                recommended_quantity=recommended_quantity,
                max_quantity=max_quantity,
                risk_percentage=risk_percentage,
                stop_loss_price=stop_loss_price,
                position_value=position_value,
                rationale=rationale
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return PositionSizing(
                symbol=symbol,
                recommended_quantity=Decimal("0"),
                max_quantity=Decimal("0"),
                risk_percentage=risk_percentage,
                rationale=f"Error: {str(e)}"
            )
    
    async def validate_order_risk(
        self,
        session_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Optional[Decimal] = None
    ) -> Tuple[bool, List[str]]:
        """Validate if an order meets risk requirements."""
        
        validation_errors = []
        
        try:
            # Get current market price if not provided
            if not price:
                price = await market_data_service.get_current_price(symbol)
                if not price:
                    validation_errors.append("Current price not available")
                    return False, validation_errors
            
            # Get portfolio summary
            portfolio = await portfolio_tracker.get_portfolio_summary(session_id)
            if not portfolio:
                validation_errors.append("Portfolio not found")
                return False, validation_errors
            
            # Calculate position value
            position_value = quantity * price
            
            # Get session risk parameters
            with get_db_session() as db:
                session = db.query(PaperTradingSession).filter(
                    PaperTradingSession.id == session_id
                ).first()
                
                if not session:
                    validation_errors.append("Session not found")
                    return False, validation_errors
            
            # Check position size limit
            max_position_size = session.max_position_size or (portfolio.total_value * self.default_max_position_size_pct)
            if position_value > max_position_size:
                validation_errors.append(
                    f"Position size {position_value} exceeds limit of {max_position_size}"
                )
            
            # Check concentration limit
            concentration_limit = portfolio.total_value * self.default_max_concentration_pct
            
            # Get existing position value
            existing_position_value = Decimal("0")
            for pos in portfolio.positions:
                if pos.symbol == symbol:
                    existing_position_value = pos.market_value
                    break
            
            total_position_value = existing_position_value + position_value
            if total_position_value > concentration_limit:
                validation_errors.append(
                    f"Total position value {total_position_value} exceeds concentration limit of {concentration_limit}"
                )
            
            # Check leverage after order
            new_positions_value = portfolio.positions_value + position_value
            new_leverage = new_positions_value / portfolio.total_value if portfolio.total_value > 0 else Decimal("0")
            
            if new_leverage > self.default_max_leverage:
                validation_errors.append(
                    f"Order would result in leverage of {new_leverage}, exceeding limit of {self.default_max_leverage}"
                )
            
            # Check buying power for buy orders
            if side == OrderSide.BUY.value:
                estimated_cost = position_value * Decimal("1.002")  # Include commission buffer
                if estimated_cost > portfolio.cash_balance:
                    validation_errors.append(
                        f"Insufficient buying power: need {estimated_cost}, have {portfolio.cash_balance}"
                    )
            
            return len(validation_errors) == 0, validation_errors
            
        except Exception as e:
            self.logger.error(f"Error validating order risk: {e}")
            validation_errors.append(f"Validation error: {str(e)}")
            return False, validation_errors
    
    async def get_risk_alerts(self, session_id: int) -> List[Dict[str, Any]]:
        """Get risk alerts for a session."""
        
        alerts = self.risk_alerts.get(session_id, [])
        
        return [
            {
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "symbol": alert.symbol,
                "current_value": float(alert.current_value) if alert.current_value else None,
                "limit_value": float(alert.limit_value) if alert.limit_value else None
            }
            for alert in alerts
        ]
    
    async def get_risk_summary(self, session_id: int) -> Dict[str, Any]:
        """Get comprehensive risk summary for a session."""
        
        try:
            risk_metrics = await self.calculate_risk_metrics(session_id)
            recent_alerts = [alert for alert in self.risk_alerts.get(session_id, []) 
                           if (datetime.utcnow() - alert.timestamp).total_seconds() < 3600]  # Last hour
            
            # Calculate overall risk score (0-100)
            risk_scores = []
            for metric in risk_metrics:
                if metric.utilization_pct <= 100:
                    risk_scores.append(float(metric.utilization_pct))
            
            overall_risk_score = max(risk_scores) if risk_scores else 0.0
            
            # Determine overall risk level
            if overall_risk_score >= 100:
                overall_risk_level = RiskLevel.CRITICAL
            elif overall_risk_score >= 80:
                overall_risk_level = RiskLevel.HIGH
            elif overall_risk_score >= 60:
                overall_risk_level = RiskLevel.MEDIUM
            else:
                overall_risk_level = RiskLevel.LOW
            
            return {
                "session_id": session_id,
                "overall_risk_score": overall_risk_score,
                "overall_risk_level": overall_risk_level.value,
                "risk_metrics": [
                    {
                        "name": metric.name,
                        "value": float(metric.value),
                        "limit": float(metric.limit),
                        "utilization_pct": float(metric.utilization_pct),
                        "risk_level": metric.risk_level.value,
                        "breach": metric.breach
                    }
                    for metric in risk_metrics
                ],
                "recent_alerts": len(recent_alerts),
                "critical_alerts": len([a for a in recent_alerts if a.severity == RiskLevel.CRITICAL]),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting risk summary for session {session_id}: {e}")
            return {
                "session_id": session_id,
                "overall_risk_score": 0.0,
                "overall_risk_level": RiskLevel.LOW.value,
                "risk_metrics": [],
                "recent_alerts": 0,
                "critical_alerts": 0,
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup risk manager."""
        
        self.risk_monitoring_active = False
        self.logger.info("Risk management service cleaned up")


# Global risk manager instance
risk_manager = RiskManager()