"""
Real-time Risk Management System
Alphintra Trading Platform - Phase 4
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
import asyncio
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime, timedelta
import warnings
from concurrent.futures import ThreadPoolExecutor
import redis
import yaml

# Mathematical libraries
from scipy import stats
from scipy.optimize import minimize
import numpy.linalg as la

# Async libraries
import aioredis
import aiohttp

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert type enumeration"""
    POSITION_LIMIT = "position_limit"
    VAR_BREACH = "var_breach"
    DRAWDOWN = "drawdown"
    CONCENTRATION = "concentration"
    CORRELATION = "correlation"
    LIQUIDITY = "liquidity"
    MARGIN_CALL = "margin_call"
    STOP_LOSS = "stop_loss"


@dataclass
class Position:
    """Trading position data structure"""
    symbol: str
    quantity: float
    price: float
    timestamp: datetime
    side: str = "long"  # long or short
    portfolio_id: str = "default"
    
    @property
    def market_value(self) -> float:
        return abs(self.quantity * self.price)
    
    @property
    def notional_value(self) -> float:
        return self.quantity * self.price


@dataclass
class RiskMetrics:
    """Risk metrics data structure"""
    portfolio_id: str
    timestamp: datetime
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    var_1d: float
    var_1w: float
    expected_shortfall: float
    maximum_drawdown: float
    current_drawdown: float
    beta: float
    correlation_risk: float
    concentration_risk: float
    liquidity_risk: float
    leverage: float
    margin_used: float
    available_margin: float
    risk_level: RiskLevel


@dataclass
class RiskAlert:
    """Risk alert data structure"""
    alert_id: str
    alert_type: AlertType
    risk_level: RiskLevel
    portfolio_id: str
    symbol: Optional[str]
    message: str
    timestamp: datetime
    current_value: float
    threshold: float
    recommended_action: str
    acknowledged: bool = False


@dataclass
class RiskLimits:
    """Risk limits configuration"""
    max_position_size: float = 1000000  # Maximum position size in USD
    max_portfolio_value: float = 10000000  # Maximum portfolio value
    max_var_1d: float = 100000  # Maximum 1-day VaR
    max_var_1w: float = 500000  # Maximum 1-week VaR
    max_drawdown: float = 0.05  # Maximum drawdown (5%)
    max_leverage: float = 3.0  # Maximum leverage ratio
    max_concentration: float = 0.25  # Maximum concentration per position (25%)
    max_correlation: float = 0.8  # Maximum correlation threshold
    min_liquidity_score: float = 0.5  # Minimum liquidity score
    margin_call_threshold: float = 0.25  # Margin call at 25% margin
    stop_loss_threshold: float = 0.02  # Stop loss at 2% loss


class VaRCalculator:
    """
    Value at Risk (VaR) calculator with multiple methodologies
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
        
    async def calculate_parametric_var(self, returns: np.ndarray, holding_period: int = 1) -> float:
        """Calculate parametric VaR assuming normal distribution"""
        try:
            if len(returns) < 30:
                logger.warning("Insufficient data for reliable VaR calculation")
                return 0.0
                
            # Calculate mean and standard deviation
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=1)
            
            # Adjust for holding period
            adjusted_mean = mean_return * holding_period
            adjusted_std = std_return * np.sqrt(holding_period)
            
            # Calculate VaR using normal distribution
            z_score = stats.norm.ppf(self.alpha)
            var = -(adjusted_mean + z_score * adjusted_std)
            
            return max(var, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating parametric VaR: {str(e)}")
            return 0.0
    
    async def calculate_historical_var(self, returns: np.ndarray, holding_period: int = 1) -> float:
        """Calculate historical VaR using historical simulation"""
        try:
            if len(returns) < 100:
                logger.warning("Insufficient data for reliable historical VaR")
                return 0.0
            
            # Adjust returns for holding period
            if holding_period > 1:
                # Simulate holding period returns using overlapping periods
                adjusted_returns = []
                for i in range(len(returns) - holding_period + 1):
                    period_return = np.sum(returns[i:i + holding_period])
                    adjusted_returns.append(period_return)
                adjusted_returns = np.array(adjusted_returns)
            else:
                adjusted_returns = returns
            
            # Calculate VaR as the percentile
            var = -np.percentile(adjusted_returns, self.alpha * 100)
            
            return max(var, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating historical VaR: {str(e)}")
            return 0.0
    
    async def calculate_monte_carlo_var(self, returns: np.ndarray, num_simulations: int = 10000, 
                                     holding_period: int = 1) -> float:
        """Calculate Monte Carlo VaR using simulation"""
        try:
            if len(returns) < 50:
                logger.warning("Insufficient data for Monte Carlo VaR")
                return 0.0
            
            # Fit parameters
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=1)
            
            # Generate random scenarios
            np.random.seed(42)  # For reproducibility
            simulated_returns = np.random.normal(
                mean_return, std_return, (num_simulations, holding_period)
            )
            
            # Calculate cumulative returns for each simulation
            cumulative_returns = np.sum(simulated_returns, axis=1)
            
            # Calculate VaR
            var = -np.percentile(cumulative_returns, self.alpha * 100)
            
            return max(var, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating Monte Carlo VaR: {str(e)}")
            return 0.0
    
    async def calculate_expected_shortfall(self, returns: np.ndarray, holding_period: int = 1) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        try:
            if len(returns) < 100:
                return 0.0
            
            # Adjust returns for holding period
            if holding_period > 1:
                adjusted_returns = []
                for i in range(len(returns) - holding_period + 1):
                    period_return = np.sum(returns[i:i + holding_period])
                    adjusted_returns.append(period_return)
                adjusted_returns = np.array(adjusted_returns)
            else:
                adjusted_returns = returns
            
            # Calculate VaR threshold
            var_threshold = -np.percentile(adjusted_returns, self.alpha * 100)
            
            # Calculate Expected Shortfall as average of losses beyond VaR
            tail_losses = adjusted_returns[adjusted_returns <= -var_threshold]
            
            if len(tail_losses) == 0:
                return var_threshold
            
            expected_shortfall = -np.mean(tail_losses)
            
            return max(expected_shortfall, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating Expected Shortfall: {str(e)}")
            return 0.0


class CorrelationMonitor:
    """
    Monitor correlation between positions and detect correlation risk
    """
    
    def __init__(self, lookback_period: int = 252):
        self.lookback_period = lookback_period
        
    async def calculate_correlation_matrix(self, returns_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix from returns data"""
        try:
            if returns_data.empty or len(returns_data) < 30:
                return pd.DataFrame()
            
            # Use only the most recent data
            recent_data = returns_data.tail(self.lookback_period)
            
            # Calculate correlation matrix
            correlation_matrix = recent_data.corr()
            
            # Fill NaN values with 0
            correlation_matrix.fillna(0, inplace=True)
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {str(e)}")
            return pd.DataFrame()
    
    async def detect_high_correlations(self, correlation_matrix: pd.DataFrame, 
                                     threshold: float = 0.8) -> List[Tuple[str, str, float]]:
        """Detect pairs with high correlation"""
        high_correlations = []
        
        try:
            # Get upper triangle of correlation matrix (excluding diagonal)
            upper_triangle = np.triu(correlation_matrix.values, k=1)
            
            # Find high correlations
            high_corr_indices = np.where(np.abs(upper_triangle) > threshold)
            
            for i, j in zip(high_corr_indices[0], high_corr_indices[1]):
                symbol1 = correlation_matrix.index[i]
                symbol2 = correlation_matrix.columns[j]
                correlation = correlation_matrix.iloc[i, j]
                
                high_correlations.append((symbol1, symbol2, correlation))
            
        except Exception as e:
            logger.error(f"Error detecting high correlations: {str(e)}")
        
        return high_correlations
    
    async def calculate_portfolio_correlation_risk(self, positions: List[Position], 
                                                 correlation_matrix: pd.DataFrame) -> float:
        """Calculate overall portfolio correlation risk"""
        try:
            if correlation_matrix.empty or not positions:
                return 0.0
            
            # Create position weights
            total_value = sum(pos.market_value for pos in positions)
            if total_value == 0:
                return 0.0
            
            weights = {}
            for pos in positions:
                weights[pos.symbol] = pos.market_value / total_value
            
            # Calculate weighted correlation risk
            correlation_risk = 0.0
            count = 0
            
            for symbol1 in weights:
                for symbol2 in weights:
                    if symbol1 != symbol2 and symbol1 in correlation_matrix.index and symbol2 in correlation_matrix.columns:
                        correlation = correlation_matrix.loc[symbol1, symbol2]
                        weight_product = weights[symbol1] * weights[symbol2]
                        correlation_risk += abs(correlation) * weight_product
                        count += 1
            
            # Normalize by number of pairs
            if count > 0:
                correlation_risk /= count
            
            return correlation_risk
            
        except Exception as e:
            logger.error(f"Error calculating portfolio correlation risk: {str(e)}")
            return 0.0


class LiquidityAnalyzer:
    """
    Analyze position liquidity and market impact
    """
    
    def __init__(self):
        self.liquidity_cache = {}
        self.cache_duration = timedelta(hours=1)
        
    async def calculate_liquidity_score(self, symbol: str, volume_data: Optional[pd.Series] = None) -> float:
        """Calculate liquidity score for a symbol"""
        try:
            # Check cache first
            if symbol in self.liquidity_cache:
                cached_time, cached_score = self.liquidity_cache[symbol]
                if datetime.now() - cached_time < self.cache_duration:
                    return cached_score
            
            if volume_data is None or volume_data.empty:
                # Default score if no volume data
                score = 0.5
            else:
                # Calculate liquidity metrics
                avg_volume = volume_data.mean()
                volume_std = volume_data.std()
                
                # Normalize volume (higher volume = higher liquidity)
                volume_score = min(avg_volume / 1000000, 1.0)  # Normalize to max 1M volume
                
                # Stability score (lower volatility in volume = better liquidity)
                if avg_volume > 0:
                    volume_cv = volume_std / avg_volume  # Coefficient of variation
                    stability_score = max(0, 1 - volume_cv)
                else:
                    stability_score = 0
                
                # Combine scores
                score = 0.7 * volume_score + 0.3 * stability_score
                score = max(0, min(1, score))  # Ensure between 0 and 1
            
            # Cache the result
            self.liquidity_cache[symbol] = (datetime.now(), score)
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating liquidity score for {symbol}: {str(e)}")
            return 0.5  # Default moderate liquidity
    
    async def estimate_market_impact(self, symbol: str, trade_size: float, 
                                   avg_volume: float = None) -> float:
        """Estimate market impact of a trade"""
        try:
            if avg_volume is None or avg_volume <= 0:
                # Default impact if no volume data
                return 0.001  # 0.1% default impact
            
            # Calculate participation rate
            participation_rate = abs(trade_size) / avg_volume
            
            # Market impact model: impact = k * (participation_rate)^0.5
            # where k is a market impact coefficient
            k = 0.01  # Typical market impact coefficient
            impact = k * np.sqrt(participation_rate)
            
            # Cap maximum impact
            impact = min(impact, 0.05)  # Max 5% impact
            
            return impact
            
        except Exception as e:
            logger.error(f"Error estimating market impact for {symbol}: {str(e)}")
            return 0.001


class RealTimeRiskMonitor:
    """
    Real-time risk monitoring and alerting system
    """
    
    def __init__(self, risk_limits: RiskLimits = None, redis_url: str = "redis://localhost:6379"):
        self.risk_limits = risk_limits or RiskLimits()
        self.redis_url = redis_url
        self.redis_client = None
        
        # Initialize risk calculation components
        self.var_calculator = VaRCalculator()
        self.correlation_monitor = CorrelationMonitor()
        self.liquidity_analyzer = LiquidityAnalyzer()
        
        # Risk monitoring state
        self.active_alerts = {}
        self.risk_history = []
        self.positions_cache = {}
        self.market_data_cache = {}
        
        # Async executor for CPU-intensive tasks
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def initialize(self):
        """Initialize Redis connection and other async components"""
        try:
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis for risk monitoring")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            # Continue without Redis caching
            self.redis_client = None
    
    async def monitor_portfolio_risk(self, portfolio_id: str, positions: List[Position], 
                                   market_data: Dict[str, pd.DataFrame]) -> RiskMetrics:
        """
        Comprehensive portfolio risk monitoring
        
        Args:
            portfolio_id: Portfolio identifier
            positions: List of current positions
            market_data: Market data dictionary with symbol -> OHLCV DataFrame
            
        Returns:
            RiskMetrics object with current risk assessment
        """
        try:
            logger.info(f"Monitoring risk for portfolio {portfolio_id} with {len(positions)} positions")
            
            # Calculate basic portfolio metrics
            total_pnl = await self._calculate_total_pnl(positions, market_data)
            unrealized_pnl = await self._calculate_unrealized_pnl(positions, market_data)
            realized_pnl = total_pnl - unrealized_pnl
            
            # Calculate VaR metrics
            var_1d = await self._calculate_portfolio_var(positions, market_data, holding_period=1)
            var_1w = await self._calculate_portfolio_var(positions, market_data, holding_period=5)
            
            # Calculate Expected Shortfall
            expected_shortfall = await self._calculate_expected_shortfall(positions, market_data)
            
            # Calculate drawdown metrics
            max_drawdown, current_drawdown = await self._calculate_drawdown_metrics(portfolio_id, total_pnl)
            
            # Calculate portfolio beta
            beta = await self._calculate_portfolio_beta(positions, market_data)
            
            # Calculate correlation risk
            correlation_risk = await self._calculate_correlation_risk(positions, market_data)
            
            # Calculate concentration risk
            concentration_risk = await self._calculate_concentration_risk(positions)
            
            # Calculate liquidity risk
            liquidity_risk = await self._calculate_liquidity_risk(positions, market_data)
            
            # Calculate leverage and margin metrics
            leverage, margin_used, available_margin = await self._calculate_leverage_metrics(positions, market_data)
            
            # Determine overall risk level
            risk_level = self._determine_risk_level(var_1d, max_drawdown, leverage, concentration_risk)
            
            # Create risk metrics object
            risk_metrics = RiskMetrics(
                portfolio_id=portfolio_id,
                timestamp=datetime.now(),
                total_pnl=total_pnl,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                var_1d=var_1d,
                var_1w=var_1w,
                expected_shortfall=expected_shortfall,
                maximum_drawdown=max_drawdown,
                current_drawdown=current_drawdown,
                beta=beta,
                correlation_risk=correlation_risk,
                concentration_risk=concentration_risk,
                liquidity_risk=liquidity_risk,
                leverage=leverage,
                margin_used=margin_used,
                available_margin=available_margin,
                risk_level=risk_level
            )
            
            # Check for risk limit violations
            await self._check_risk_limits(risk_metrics, positions)
            
            # Cache risk metrics
            await self._cache_risk_metrics(risk_metrics)
            
            # Add to history
            self.risk_history.append(risk_metrics)
            
            # Limit history size
            if len(self.risk_history) > 1000:
                self.risk_history = self.risk_history[-1000:]
            
            logger.info(f"Risk monitoring completed for {portfolio_id}. Risk level: {risk_level.value}")
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"Error monitoring portfolio risk: {str(e)}")
            raise
    
    async def _calculate_total_pnl(self, positions: List[Position], market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate total portfolio P&L"""
        total_pnl = 0.0
        
        for position in positions:
            try:
                if position.symbol in market_data and not market_data[position.symbol].empty:
                    current_price = market_data[position.symbol]['close'].iloc[-1]
                    pnl = (current_price - position.price) * position.quantity
                    total_pnl += pnl
            except Exception as e:
                logger.warning(f"Error calculating P&L for {position.symbol}: {str(e)}")
        
        return total_pnl
    
    async def _calculate_unrealized_pnl(self, positions: List[Position], market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate unrealized P&L (same as total P&L for now)"""
        return await self._calculate_total_pnl(positions, market_data)
    
    async def _calculate_portfolio_var(self, positions: List[Position], market_data: Dict[str, pd.DataFrame], 
                                     holding_period: int = 1) -> float:
        """Calculate portfolio VaR using historical simulation"""
        try:
            if not positions:
                return 0.0
            
            # Collect returns for all positions
            portfolio_returns = []
            
            for position in positions:
                if position.symbol in market_data and not market_data[position.symbol].empty:
                    prices = market_data[position.symbol]['close']
                    returns = prices.pct_change().dropna()
                    
                    if len(returns) > 30:
                        # Weight returns by position size
                        position_value = position.market_value
                        weighted_returns = returns * position_value
                        portfolio_returns.append(weighted_returns)
            
            if not portfolio_returns:
                return 0.0
            
            # Combine all position returns
            combined_returns = pd.concat(portfolio_returns, axis=1)
            combined_returns.fillna(0, inplace=True)
            
            # Calculate portfolio returns
            portfolio_returns_series = combined_returns.sum(axis=1)
            
            # Calculate VaR
            var = await self.var_calculator.calculate_historical_var(
                portfolio_returns_series.values, holding_period
            )
            
            return var
            
        except Exception as e:
            logger.error(f"Error calculating portfolio VaR: {str(e)}")
            return 0.0
    
    async def _calculate_expected_shortfall(self, positions: List[Position], 
                                          market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate Expected Shortfall for the portfolio"""
        try:
            if not positions:
                return 0.0
            
            # Collect portfolio returns (similar to VaR calculation)
            portfolio_returns = []
            
            for position in positions:
                if position.symbol in market_data and not market_data[position.symbol].empty:
                    prices = market_data[position.symbol]['close']
                    returns = prices.pct_change().dropna()
                    
                    if len(returns) > 30:
                        position_value = position.market_value
                        weighted_returns = returns * position_value
                        portfolio_returns.append(weighted_returns)
            
            if not portfolio_returns:
                return 0.0
            
            # Combine returns
            combined_returns = pd.concat(portfolio_returns, axis=1)
            combined_returns.fillna(0, inplace=True)
            portfolio_returns_series = combined_returns.sum(axis=1)
            
            # Calculate Expected Shortfall
            es = await self.var_calculator.calculate_expected_shortfall(
                portfolio_returns_series.values
            )
            
            return es
            
        except Exception as e:
            logger.error(f"Error calculating Expected Shortfall: {str(e)}")
            return 0.0
    
    async def _calculate_drawdown_metrics(self, portfolio_id: str, current_pnl: float) -> Tuple[float, float]:
        """Calculate maximum and current drawdown"""
        try:
            # Get historical P&L for this portfolio
            historical_pnl = [rm.total_pnl for rm in self.risk_history if rm.portfolio_id == portfolio_id]
            
            if not historical_pnl:
                return 0.0, 0.0
            
            # Add current P&L
            pnl_series = historical_pnl + [current_pnl]
            pnl_array = np.array(pnl_series)
            
            # Calculate running maximum
            running_max = np.maximum.accumulate(pnl_array)
            
            # Calculate drawdowns
            drawdowns = (pnl_array - running_max) / np.maximum(running_max, 1)  # Avoid division by zero
            
            # Maximum drawdown
            max_drawdown = abs(np.min(drawdowns))
            
            # Current drawdown
            current_drawdown = abs(drawdowns[-1])
            
            return max_drawdown, current_drawdown
            
        except Exception as e:
            logger.error(f"Error calculating drawdown metrics: {str(e)}")
            return 0.0, 0.0
    
    async def _calculate_portfolio_beta(self, positions: List[Position], 
                                      market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate portfolio beta relative to market"""
        try:
            # This is a simplified beta calculation
            # In practice, you'd want to use a market index
            
            if not positions or not market_data:
                return 1.0
            
            # Use the first available symbol as market proxy (simplified)
            market_symbol = next(iter(market_data.keys()))
            if market_symbol not in market_data or market_data[market_symbol].empty:
                return 1.0
            
            market_returns = market_data[market_symbol]['close'].pct_change().dropna()
            
            if len(market_returns) < 30:
                return 1.0
            
            # Calculate weighted portfolio beta
            total_value = sum(pos.market_value for pos in positions)
            if total_value == 0:
                return 1.0
            
            portfolio_beta = 0.0
            
            for position in positions:
                if position.symbol in market_data and not market_data[position.symbol].empty:
                    asset_returns = market_data[position.symbol]['close'].pct_change().dropna()
                    
                    if len(asset_returns) >= len(market_returns):
                        # Align returns
                        common_index = asset_returns.index.intersection(market_returns.index)
                        if len(common_index) > 30:
                            aligned_asset = asset_returns.loc[common_index]
                            aligned_market = market_returns.loc[common_index]
                            
                            # Calculate beta
                            covariance = np.cov(aligned_asset, aligned_market)[0, 1]
                            market_variance = np.var(aligned_market)
                            
                            if market_variance > 0:
                                asset_beta = covariance / market_variance
                                weight = position.market_value / total_value
                                portfolio_beta += asset_beta * weight
            
            return portfolio_beta
            
        except Exception as e:
            logger.error(f"Error calculating portfolio beta: {str(e)}")
            return 1.0
    
    async def _calculate_correlation_risk(self, positions: List[Position], 
                                        market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate portfolio correlation risk"""
        try:
            if len(positions) < 2:
                return 0.0
            
            # Create returns DataFrame
            returns_data = {}
            
            for position in positions:
                if position.symbol in market_data and not market_data[position.symbol].empty:
                    returns = market_data[position.symbol]['close'].pct_change().dropna()
                    if len(returns) > 30:
                        returns_data[position.symbol] = returns
            
            if len(returns_data) < 2:
                return 0.0
            
            # Create aligned DataFrame
            returns_df = pd.DataFrame(returns_data)
            returns_df.fillna(0, inplace=True)
            
            # Calculate correlation matrix
            correlation_matrix = await self.correlation_monitor.calculate_correlation_matrix(returns_df)
            
            # Calculate portfolio correlation risk
            correlation_risk = await self.correlation_monitor.calculate_portfolio_correlation_risk(
                positions, correlation_matrix
            )
            
            return correlation_risk
            
        except Exception as e:
            logger.error(f"Error calculating correlation risk: {str(e)}")
            return 0.0
    
    async def _calculate_concentration_risk(self, positions: List[Position]) -> float:
        """Calculate portfolio concentration risk"""
        try:
            if not positions:
                return 0.0
            
            # Calculate total portfolio value
            total_value = sum(pos.market_value for pos in positions)
            if total_value == 0:
                return 0.0
            
            # Calculate position weights
            weights = [pos.market_value / total_value for pos in positions]
            
            # Concentration risk as maximum weight
            max_weight = max(weights)
            
            # Alternatively, use Herfindahl-Hirschman Index
            hhi = sum(w ** 2 for w in weights)
            
            # Return the maximum of relative concentration metrics
            return max(max_weight, hhi)
            
        except Exception as e:
            logger.error(f"Error calculating concentration risk: {str(e)}")
            return 0.0
    
    async def _calculate_liquidity_risk(self, positions: List[Position], 
                                      market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate portfolio liquidity risk"""
        try:
            if not positions:
                return 0.0
            
            total_value = sum(pos.market_value for pos in positions)
            if total_value == 0:
                return 0.0
            
            weighted_liquidity_risk = 0.0
            
            for position in positions:
                # Get volume data if available
                volume_data = None
                if position.symbol in market_data and 'volume' in market_data[position.symbol].columns:
                    volume_data = market_data[position.symbol]['volume']
                
                # Calculate liquidity score
                liquidity_score = await self.liquidity_analyzer.calculate_liquidity_score(
                    position.symbol, volume_data
                )
                
                # Liquidity risk is inverse of liquidity score
                liquidity_risk = 1 - liquidity_score
                
                # Weight by position size
                weight = position.market_value / total_value
                weighted_liquidity_risk += liquidity_risk * weight
            
            return weighted_liquidity_risk
            
        except Exception as e:
            logger.error(f"Error calculating liquidity risk: {str(e)}")
            return 0.0
    
    async def _calculate_leverage_metrics(self, positions: List[Position], 
                                        market_data: Dict[str, pd.DataFrame]) -> Tuple[float, float, float]:
        """Calculate leverage and margin metrics"""
        try:
            # Calculate total market value
            total_market_value = sum(pos.market_value for pos in positions)
            
            # Calculate total notional value (considering long/short)
            total_notional = sum(abs(pos.notional_value) for pos in positions)
            
            # Leverage ratio
            leverage = total_notional / max(total_market_value, 1)
            
            # Simplified margin calculation (would be more complex in practice)
            margin_used = total_notional * 0.1  # Assume 10% margin requirement
            available_margin = max(0, total_market_value - margin_used)
            
            return leverage, margin_used, available_margin
            
        except Exception as e:
            logger.error(f"Error calculating leverage metrics: {str(e)}")
            return 1.0, 0.0, 0.0
    
    def _determine_risk_level(self, var_1d: float, max_drawdown: float, 
                            leverage: float, concentration_risk: float) -> RiskLevel:
        """Determine overall risk level based on key metrics"""
        try:
            risk_score = 0
            
            # VaR risk
            if var_1d > self.risk_limits.max_var_1d * 0.8:
                risk_score += 3
            elif var_1d > self.risk_limits.max_var_1d * 0.6:
                risk_score += 2
            elif var_1d > self.risk_limits.max_var_1d * 0.4:
                risk_score += 1
            
            # Drawdown risk
            if max_drawdown > self.risk_limits.max_drawdown * 0.8:
                risk_score += 3
            elif max_drawdown > self.risk_limits.max_drawdown * 0.6:
                risk_score += 2
            elif max_drawdown > self.risk_limits.max_drawdown * 0.4:
                risk_score += 1
            
            # Leverage risk
            if leverage > self.risk_limits.max_leverage * 0.8:
                risk_score += 3
            elif leverage > self.risk_limits.max_leverage * 0.6:
                risk_score += 2
            elif leverage > self.risk_limits.max_leverage * 0.4:
                risk_score += 1
            
            # Concentration risk
            if concentration_risk > self.risk_limits.max_concentration * 0.8:
                risk_score += 2
            elif concentration_risk > self.risk_limits.max_concentration * 0.6:
                risk_score += 1
            
            # Determine risk level
            if risk_score >= 8:
                return RiskLevel.CRITICAL
            elif risk_score >= 5:
                return RiskLevel.HIGH
            elif risk_score >= 2:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW
                
        except Exception as e:
            logger.error(f"Error determining risk level: {str(e)}")
            return RiskLevel.MEDIUM
    
    async def _check_risk_limits(self, risk_metrics: RiskMetrics, positions: List[Position]):
        """Check risk limits and generate alerts"""
        try:
            # VaR limit check
            if risk_metrics.var_1d > self.risk_limits.max_var_1d:
                await self._generate_alert(
                    AlertType.VAR_BREACH,
                    RiskLevel.HIGH,
                    risk_metrics.portfolio_id,
                    None,
                    f"1-day VaR breach: ${risk_metrics.var_1d:,.2f} exceeds limit ${self.risk_limits.max_var_1d:,.2f}",
                    risk_metrics.var_1d,
                    self.risk_limits.max_var_1d,
                    "Reduce position sizes or hedge exposure"
                )
            
            # Drawdown limit check
            if risk_metrics.maximum_drawdown > self.risk_limits.max_drawdown:
                await self._generate_alert(
                    AlertType.DRAWDOWN,
                    RiskLevel.HIGH,
                    risk_metrics.portfolio_id,
                    None,
                    f"Maximum drawdown breach: {risk_metrics.maximum_drawdown:.2%} exceeds limit {self.risk_limits.max_drawdown:.2%}",
                    risk_metrics.maximum_drawdown,
                    self.risk_limits.max_drawdown,
                    "Implement stop-loss or reduce position sizes"
                )
            
            # Leverage limit check
            if risk_metrics.leverage > self.risk_limits.max_leverage:
                await self._generate_alert(
                    AlertType.MARGIN_CALL,
                    RiskLevel.HIGH,
                    risk_metrics.portfolio_id,
                    None,
                    f"Leverage breach: {risk_metrics.leverage:.2f}x exceeds limit {self.risk_limits.max_leverage:.2f}x",
                    risk_metrics.leverage,
                    self.risk_limits.max_leverage,
                    "Reduce leverage by closing positions"
                )
            
            # Concentration limit check
            if risk_metrics.concentration_risk > self.risk_limits.max_concentration:
                await self._generate_alert(
                    AlertType.CONCENTRATION,
                    RiskLevel.MEDIUM,
                    risk_metrics.portfolio_id,
                    None,
                    f"Concentration risk breach: {risk_metrics.concentration_risk:.2%} exceeds limit {self.risk_limits.max_concentration:.2%}",
                    risk_metrics.concentration_risk,
                    self.risk_limits.max_concentration,
                    "Diversify portfolio by reducing large positions"
                )
            
            # Individual position limit checks
            for position in positions:
                if position.market_value > self.risk_limits.max_position_size:
                    await self._generate_alert(
                        AlertType.POSITION_LIMIT,
                        RiskLevel.MEDIUM,
                        risk_metrics.portfolio_id,
                        position.symbol,
                        f"Position size limit breach for {position.symbol}: ${position.market_value:,.2f} exceeds limit ${self.risk_limits.max_position_size:,.2f}",
                        position.market_value,
                        self.risk_limits.max_position_size,
                        f"Reduce {position.symbol} position size"
                    )
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {str(e)}")
    
    async def _generate_alert(self, alert_type: AlertType, risk_level: RiskLevel, 
                            portfolio_id: str, symbol: Optional[str], message: str,
                            current_value: float, threshold: float, recommended_action: str):
        """Generate and store risk alert"""
        try:
            alert_id = f"{alert_type.value}_{portfolio_id}_{symbol or 'portfolio'}_{int(datetime.now().timestamp())}"
            
            alert = RiskAlert(
                alert_id=alert_id,
                alert_type=alert_type,
                risk_level=risk_level,
                portfolio_id=portfolio_id,
                symbol=symbol,
                message=message,
                timestamp=datetime.now(),
                current_value=current_value,
                threshold=threshold,
                recommended_action=recommended_action
            )
            
            # Store alert
            self.active_alerts[alert_id] = alert
            
            # Log alert
            logger.warning(f"RISK ALERT [{risk_level.value.upper()}]: {message}")
            
            # Send to external systems (Redis, webhook, etc.)
            await self._send_alert_notification(alert)
            
        except Exception as e:
            logger.error(f"Error generating alert: {str(e)}")
    
    async def _send_alert_notification(self, alert: RiskAlert):
        """Send alert notification to external systems"""
        try:
            # Send to Redis if available
            if self.redis_client:
                alert_data = asdict(alert)
                alert_data['timestamp'] = alert.timestamp.isoformat()
                
                await self.redis_client.lpush("risk_alerts", json.dumps(alert_data, default=str))
                await self.redis_client.expire("risk_alerts", 86400)  # 24 hours
            
            # Here you could add other notification methods:
            # - Email alerts
            # - Slack/Teams notifications
            # - Webhook calls
            # - SMS alerts for critical risks
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {str(e)}")
    
    async def _cache_risk_metrics(self, risk_metrics: RiskMetrics):
        """Cache risk metrics in Redis"""
        try:
            if self.redis_client:
                cache_key = f"risk_metrics:{risk_metrics.portfolio_id}"
                metrics_data = asdict(risk_metrics)
                metrics_data['timestamp'] = risk_metrics.timestamp.isoformat()
                
                await self.redis_client.setex(
                    cache_key, 
                    300,  # 5 minutes TTL
                    json.dumps(metrics_data, default=str)
                )
        except Exception as e:
            logger.error(f"Error caching risk metrics: {str(e)}")
    
    async def get_active_alerts(self, portfolio_id: Optional[str] = None) -> List[RiskAlert]:
        """Get active risk alerts"""
        if portfolio_id:
            return [alert for alert in self.active_alerts.values() 
                   if alert.portfolio_id == portfolio_id and not alert.acknowledged]
        else:
            return [alert for alert in self.active_alerts.values() if not alert.acknowledged]
    
    async def acknowledge_alert(self, alert_id: str):
        """Acknowledge a risk alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged")
    
    async def get_risk_history(self, portfolio_id: str, hours: int = 24) -> List[RiskMetrics]:
        """Get risk metrics history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [rm for rm in self.risk_history 
                if rm.portfolio_id == portfolio_id and rm.timestamp >= cutoff_time]
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.executor:
            self.executor.shutdown(wait=True)


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_risk_monitoring():
        """Test the risk monitoring system"""
        
        # Initialize risk monitor
        risk_monitor = RealTimeRiskMonitor()
        await risk_monitor.initialize()
        
        # Create sample positions
        positions = [
            Position("AAPL", 100, 150.0, datetime.now(), "long", "test_portfolio"),
            Position("GOOGL", 50, 2500.0, datetime.now(), "long", "test_portfolio"),
            Position("TSLA", -25, 800.0, datetime.now(), "short", "test_portfolio"),
        ]
        
        # Generate sample market data
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=252, freq='1D')
        
        market_data = {}
        for symbol in ["AAPL", "GOOGL", "TSLA"]:
            # Generate realistic price data
            returns = np.random.normal(0.001, 0.02, 252)
            prices = 100 * np.exp(np.cumsum(returns))
            volumes = np.random.uniform(1000000, 10000000, 252)
            
            market_data[symbol] = pd.DataFrame({
                'close': prices,
                'volume': volumes
            }, index=dates)
        
        # Monitor portfolio risk
        print("Monitoring portfolio risk...")
        risk_metrics = await risk_monitor.monitor_portfolio_risk(
            "test_portfolio", positions, market_data
        )
        
        print(f"\nRisk Assessment Results:")
        print(f"Portfolio ID: {risk_metrics.portfolio_id}")
        print(f"Risk Level: {risk_metrics.risk_level.value}")
        print(f"Total P&L: ${risk_metrics.total_pnl:,.2f}")
        print(f"VaR (1d): ${risk_metrics.var_1d:,.2f}")
        print(f"VaR (1w): ${risk_metrics.var_1w:,.2f}")
        print(f"Expected Shortfall: ${risk_metrics.expected_shortfall:,.2f}")
        print(f"Maximum Drawdown: {risk_metrics.maximum_drawdown:.2%}")
        print(f"Current Drawdown: {risk_metrics.current_drawdown:.2%}")
        print(f"Portfolio Beta: {risk_metrics.beta:.2f}")
        print(f"Correlation Risk: {risk_metrics.correlation_risk:.2%}")
        print(f"Concentration Risk: {risk_metrics.concentration_risk:.2%}")
        print(f"Liquidity Risk: {risk_metrics.liquidity_risk:.2%}")
        print(f"Leverage: {risk_metrics.leverage:.2f}x")
        
        # Check for active alerts
        active_alerts = await risk_monitor.get_active_alerts("test_portfolio")
        if active_alerts:
            print(f"\nActive Alerts ({len(active_alerts)}):")
            for alert in active_alerts:
                print(f"  [{alert.risk_level.value.upper()}] {alert.message}")
                print(f"    Recommended Action: {alert.recommended_action}")
        else:
            print("\nNo active risk alerts")
        
        # Cleanup
        await risk_monitor.cleanup()
        
        print("\nRisk monitoring test completed!")
    
    # Run the test
    asyncio.run(test_risk_monitoring())