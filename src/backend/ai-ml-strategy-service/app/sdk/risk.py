"""
Risk management components for trading strategies.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Callable
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import logging


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskViolation:
    """Represents a risk rule violation."""
    
    def __init__(self, rule_name: str, severity: RiskLevel, message: str, 
                 current_value: float, limit_value: float, symbol: str = None):
        self.rule_name = rule_name
        self.severity = severity
        self.message = message
        self.current_value = current_value
        self.limit_value = limit_value
        self.symbol = symbol
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "current_value": self.current_value,
            "limit_value": self.limit_value,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat()
        }


class RiskMetrics:
    """Calculate and track risk metrics for portfolios."""
    
    @staticmethod
    def calculate_var(returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: List of historical returns
            confidence_level: Confidence level (0.95 = 95%)
            
        Returns:
            VaR value
        """
        if not returns:
            return 0.0
        
        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        
        if index >= len(sorted_returns):
            index = len(sorted_returns) - 1
        
        return abs(sorted_returns[index])
    
    @staticmethod
    def calculate_cvar(returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR).
        
        Args:
            returns: List of historical returns
            confidence_level: Confidence level (0.95 = 95%)
            
        Returns:
            CVaR value
        """
        if not returns:
            return 0.0
        
        sorted_returns = sorted(returns)
        cutoff_index = int((1 - confidence_level) * len(sorted_returns))
        
        if cutoff_index == 0:
            return abs(sorted_returns[0])
        
        tail_returns = sorted_returns[:cutoff_index]
        return abs(sum(tail_returns) / len(tail_returns)) if tail_returns else 0.0
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: List of returns
            risk_free_rate: Risk-free rate (annual)
            
        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        
        # Calculate standard deviation
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        return (mean_return - risk_free_rate / 252) / std_dev  # Assuming daily returns
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: List[float]) -> Dict[str, float]:
        """
        Calculate maximum drawdown from equity curve.
        
        Args:
            equity_curve: List of portfolio values over time
            
        Returns:
            Dictionary with max drawdown info
        """
        if not equity_curve:
            return {"max_drawdown": 0.0, "duration": 0, "start_index": 0, "end_index": 0}
        
        peak = equity_curve[0]
        max_dd = 0.0
        max_dd_duration = 0
        current_dd_duration = 0
        dd_start = 0
        dd_end = 0
        max_dd_start = 0
        max_dd_end = 0
        
        for i, value in enumerate(equity_curve):
            if value > peak:
                peak = value
                if current_dd_duration > 0:
                    current_dd_duration = 0
            else:
                if current_dd_duration == 0:
                    dd_start = i
                current_dd_duration += 1
                
                drawdown = (peak - value) / peak
                if drawdown > max_dd:
                    max_dd = drawdown
                    max_dd_start = dd_start
                    max_dd_end = i
                    max_dd_duration = current_dd_duration
        
        return {
            "max_drawdown": max_dd,
            "duration": max_dd_duration,
            "start_index": max_dd_start,
            "end_index": max_dd_end
        }
    
    @staticmethod
    def calculate_beta(portfolio_returns: List[float], market_returns: List[float]) -> float:
        """
        Calculate portfolio beta relative to market.
        
        Args:
            portfolio_returns: Portfolio returns
            market_returns: Market/benchmark returns
            
        Returns:
            Beta value
        """
        if len(portfolio_returns) != len(market_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        # Calculate means
        p_mean = sum(portfolio_returns) / len(portfolio_returns)
        m_mean = sum(market_returns) / len(market_returns)
        
        # Calculate covariance and market variance
        covariance = sum((p - p_mean) * (m - m_mean) 
                        for p, m in zip(portfolio_returns, market_returns))
        market_variance = sum((m - m_mean) ** 2 for m in market_returns)
        
        if market_variance == 0:
            return 0.0
        
        return covariance / market_variance


class RiskManager:
    """Manages risk rules and monitoring for trading strategies."""
    
    def __init__(self, portfolio=None):
        self.portfolio = portfolio
        self.logger = logging.getLogger(__name__)
        
        # Risk rules and limits
        self.rules: Dict[str, Dict] = {}
        self.violations: List[RiskViolation] = []
        
        # Risk monitoring
        self.is_enabled = True
        self.auto_liquidate = False
        
        # Callbacks
        self.on_violation: Optional[Callable] = None
        self.on_critical_violation: Optional[Callable] = None
        
        # Default risk limits
        self._set_default_limits()
    
    def _set_default_limits(self):
        """Set default risk limits."""
        self.rules = {
            "max_portfolio_loss": {
                "limit": 0.10,  # 10% max loss
                "current_value": 0.0,
                "severity": RiskLevel.CRITICAL,
                "enabled": True,
                "description": "Maximum portfolio loss percentage"
            },
            "max_daily_loss": {
                "limit": 0.05,  # 5% max daily loss
                "current_value": 0.0,
                "severity": RiskLevel.HIGH,
                "enabled": True,
                "description": "Maximum daily loss percentage"
            },
            "max_position_size": {
                "limit": 0.20,  # 20% max position size
                "current_value": 0.0,
                "severity": RiskLevel.MEDIUM,
                "enabled": True,
                "description": "Maximum position size as % of portfolio"
            },
            "max_leverage": {
                "limit": 2.0,   # 2x max leverage
                "current_value": 1.0,
                "severity": RiskLevel.HIGH,
                "enabled": True,
                "description": "Maximum leverage ratio"
            },
            "max_correlation": {
                "limit": 0.80,  # 80% max correlation between positions
                "current_value": 0.0,
                "severity": RiskLevel.MEDIUM,
                "enabled": False,  # Disabled by default (requires historical data)
                "description": "Maximum correlation between positions"
            },
            "min_liquidity": {
                "limit": 1000000,  # Minimum $1M daily volume
                "current_value": 0.0,
                "severity": RiskLevel.LOW,
                "enabled": False,
                "description": "Minimum daily trading volume"
            }
        }
    
    def set_risk_limit(self, rule_name: str, limit: float, severity: RiskLevel = RiskLevel.MEDIUM,
                      enabled: bool = True, description: str = ""):
        """Set or update a risk limit."""
        self.rules[rule_name] = {
            "limit": limit,
            "current_value": self.rules.get(rule_name, {}).get("current_value", 0.0),
            "severity": severity,
            "enabled": enabled,
            "description": description or f"Risk limit: {rule_name}"
        }
        
        self.logger.info(f"Risk limit set: {rule_name} = {limit} ({severity.value})")
    
    def enable_rule(self, rule_name: str, enabled: bool = True):
        """Enable or disable a risk rule."""
        if rule_name in self.rules:
            self.rules[rule_name]["enabled"] = enabled
            self.logger.info(f"Risk rule {rule_name} {'enabled' if enabled else 'disabled'}")
    
    def check_portfolio_risk(self, current_prices: Dict[str, Decimal] = None) -> List[RiskViolation]:
        """
        Check all portfolio-level risk rules.
        
        Args:
            current_prices: Current market prices for positions
            
        Returns:
            List of risk violations
        """
        if not self.is_enabled or not self.portfolio:
            return []
        
        violations = []
        
        # Update current values and check limits
        self._update_portfolio_metrics(current_prices)
        
        for rule_name, rule in self.rules.items():
            if not rule["enabled"]:
                continue
            
            current_value = rule["current_value"]
            limit = rule["limit"]
            severity = rule["severity"]
            
            # Check if limit is violated
            violated = False
            
            if rule_name in ["max_portfolio_loss", "max_daily_loss"]:
                # Loss limits (current_value should be <= limit)
                violated = current_value > limit
            elif rule_name in ["max_position_size", "max_correlation", "max_leverage"]:
                # Percentage/ratio limits
                violated = current_value > limit
            elif rule_name == "min_liquidity":
                # Minimum limits
                violated = current_value < limit
            
            if violated:
                violation = RiskViolation(
                    rule_name=rule_name,
                    severity=severity,
                    message=f"{rule['description']}: {current_value:.4f} exceeds limit {limit:.4f}",
                    current_value=current_value,
                    limit_value=limit
                )
                violations.append(violation)
                
                # Log violation
                self.logger.warning(f"Risk violation: {violation.message}")
        
        # Store violations
        self.violations.extend(violations)
        
        # Trigger callbacks
        for violation in violations:
            if self.on_violation:
                self.on_violation(violation)
            
            if violation.severity == RiskLevel.CRITICAL and self.on_critical_violation:
                self.on_critical_violation(violation)
        
        return violations
    
    def check_position_risk(self, symbol: str, quantity: Decimal, price: Decimal,
                          side: str) -> List[RiskViolation]:
        """
        Check risk for a specific position/trade.
        
        Args:
            symbol: Trading symbol
            quantity: Position quantity
            price: Position price
            side: Position side (buy/sell)
            
        Returns:
            List of risk violations
        """
        if not self.is_enabled or not self.portfolio:
            return []
        
        violations = []
        
        # Calculate position value
        position_value = quantity * price
        portfolio_value = self.portfolio.total_value
        
        if portfolio_value == 0:
            return violations
        
        position_percentage = float(position_value / portfolio_value)
        
        # Check position size limit
        if "max_position_size" in self.rules and self.rules["max_position_size"]["enabled"]:
            max_position_size = self.rules["max_position_size"]["limit"]
            
            if position_percentage > max_position_size:
                violation = RiskViolation(
                    rule_name="max_position_size",
                    severity=self.rules["max_position_size"]["severity"],
                    message=f"Position size {position_percentage:.4f} exceeds limit {max_position_size:.4f}",
                    current_value=position_percentage,
                    limit_value=max_position_size,
                    symbol=symbol
                )
                violations.append(violation)
        
        return violations
    
    def _update_portfolio_metrics(self, current_prices: Dict[str, Decimal] = None):
        """Update current risk metric values."""
        if not self.portfolio:
            return
        
        portfolio_stats = self.portfolio.get_performance_stats()
        
        # Update portfolio loss
        total_return_pct = portfolio_stats["total_return"] / 100.0
        if "max_portfolio_loss" in self.rules:
            self.rules["max_portfolio_loss"]["current_value"] = max(0, -total_return_pct)
        
        # Daily loss (simplified - would need daily tracking)
        if "max_daily_loss" in self.rules:
            # For now, use total loss as proxy
            self.rules["max_daily_loss"]["current_value"] = max(0, -total_return_pct)
        
        # Position size (largest position as % of portfolio)
        if "max_position_size" in self.rules:
            max_position_pct = 0.0
            portfolio_value = self.portfolio.total_value
            
            if portfolio_value > 0:
                for position in self.portfolio.positions.values():
                    if not position.is_closed():
                        position_pct = float(position.market_value / portfolio_value)
                        max_position_pct = max(max_position_pct, position_pct)
            
            self.rules["max_position_size"]["current_value"] = max_position_pct
        
        # Leverage (simplified calculation)
        if "max_leverage" in self.rules:
            leverage = 1.0  # Default no leverage
            if portfolio_stats["cash_balance"] < portfolio_stats["current_value"]:
                # Using margin
                leverage = portfolio_stats["current_value"] / portfolio_stats["cash_balance"]
            
            self.rules["max_leverage"]["current_value"] = leverage
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary."""
        if not self.portfolio:
            return {"error": "No portfolio attached"}
        
        # Check current risk
        violations = self.check_portfolio_risk()
        
        # Calculate risk metrics
        portfolio_stats = self.portfolio.get_performance_stats()
        
        # Get violation summary
        violation_summary = {
            "total": len(violations),
            "critical": len([v for v in violations if v.severity == RiskLevel.CRITICAL]),
            "high": len([v for v in violations if v.severity == RiskLevel.HIGH]),
            "medium": len([v for v in violations if v.severity == RiskLevel.MEDIUM]),
            "low": len([v for v in violations if v.severity == RiskLevel.LOW])
        }
        
        # Overall risk score (0-100)
        risk_score = self._calculate_risk_score()
        
        return {
            "risk_score": risk_score,
            "violations": violation_summary,
            "current_rules": {name: {
                "limit": rule["limit"],
                "current": rule["current_value"],
                "violated": rule["current_value"] > rule["limit"] if "max_" in name else rule["current_value"] < rule["limit"],
                "severity": rule["severity"].value,
                "enabled": rule["enabled"]
            } for name, rule in self.rules.items()},
            "portfolio_metrics": {
                "total_return": portfolio_stats["total_return"],
                "max_drawdown": portfolio_stats["max_drawdown"],
                "current_drawdown": portfolio_stats["current_drawdown"],
                "win_rate": portfolio_stats["win_rate"],
                "total_trades": portfolio_stats["total_trades"]
            },
            "recent_violations": [v.to_dict() for v in self.violations[-10:]]  # Last 10 violations
        }
    
    def _calculate_risk_score(self) -> float:
        """
        Calculate overall risk score (0-100).
        Lower scores indicate lower risk.
        """
        if not self.portfolio:
            return 50.0  # Neutral score
        
        score = 0.0
        weight_sum = 0.0
        
        for rule_name, rule in self.rules.items():
            if not rule["enabled"]:
                continue
            
            current = rule["current_value"]
            limit = rule["limit"]
            
            # Calculate violation ratio
            if "max_" in rule_name:
                ratio = current / limit if limit > 0 else 0
            else:  # min_ rules
                ratio = limit / current if current > 0 else 10  # High penalty for zero
            
            # Weight by severity
            severity_weights = {
                RiskLevel.LOW: 1.0,
                RiskLevel.MEDIUM: 2.0,
                RiskLevel.HIGH: 4.0,
                RiskLevel.CRITICAL: 8.0
            }
            
            weight = severity_weights.get(rule["severity"], 2.0)
            score += ratio * weight
            weight_sum += weight
        
        if weight_sum == 0:
            return 50.0
        
        # Normalize to 0-100 scale
        normalized_score = (score / weight_sum) * 50  # Scale so 1.0 ratio = 50 points
        return min(100.0, max(0.0, normalized_score))
    
    def reset_violations(self):
        """Clear violation history."""
        self.violations.clear()
        self.logger.info("Risk violations cleared")
    
    def enable_auto_liquidation(self, enabled: bool = True):
        """Enable or disable automatic liquidation on critical violations."""
        self.auto_liquidate = enabled
        self.logger.info(f"Auto-liquidation {'enabled' if enabled else 'disabled'}")
    
    def emergency_liquidation(self, reason: str = "Risk violation"):
        """Emergency liquidation of all positions."""
        if not self.portfolio:
            return False
        
        self.logger.critical(f"Emergency liquidation triggered: {reason}")
        
        # In a real implementation, this would:
        # 1. Cancel all pending orders
        # 2. Market sell all long positions
        # 3. Market buy to cover all short positions
        # 4. Log all actions
        
        return True