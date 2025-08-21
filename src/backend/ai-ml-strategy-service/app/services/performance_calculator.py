"""
Performance Calculation and Metrics Engine for Phase 5: Backtesting Engine.
Comprehensive performance analysis and risk metrics calculation.
"""

import logging
import asyncio
import json
import math
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd
from dataclasses import dataclass
from scipy import stats

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.backtesting import (
    BacktestJob, BacktestTrade, DailyReturn, PortfolioSnapshot,
    PerformanceMetric, BacktestStatus
)
from app.core.config import get_settings


@dataclass
class PerformanceResults:
    """Container for performance calculation results."""
    return_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    efficiency_metrics: Dict[str, float]
    stability_metrics: Dict[str, float]
    trade_metrics: Dict[str, float]
    benchmark_metrics: Dict[str, float]
    drawdown_metrics: Dict[str, float]


class PerformanceCalculator:
    """Comprehensive performance and risk metrics calculator."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # Risk-free rate (can be configured)
        self.risk_free_rate = 0.02  # 2% annual
        
        # Trading days per year
        self.trading_days_per_year = 252
    
    async def calculate_comprehensive_metrics(self, backtest_job_id: UUID, 
                                            db: AsyncSession) -> PerformanceResults:
        """Calculate all performance metrics for a backtest."""
        try:
            self.logger.info(f"Calculating performance metrics for backtest: {backtest_job_id}")
            
            # Load required data
            data = await self._load_backtest_data(backtest_job_id, db)
            
            if not data['success']:
                raise ValueError(f"Failed to load backtest data: {data['error']}")
            
            daily_returns = data['daily_returns']
            trades = data['trades']
            backtest_job = data['backtest_job']
            
            # Calculate different metric categories
            return_metrics = self._calculate_return_metrics(daily_returns, backtest_job)
            risk_metrics = self._calculate_risk_metrics(daily_returns, backtest_job)
            efficiency_metrics = self._calculate_efficiency_metrics(daily_returns, trades, backtest_job)
            stability_metrics = self._calculate_stability_metrics(daily_returns)
            trade_metrics = self._calculate_trade_metrics(trades)
            benchmark_metrics = self._calculate_benchmark_metrics(daily_returns, backtest_job)
            drawdown_metrics = self._calculate_drawdown_metrics(daily_returns)
            
            results = PerformanceResults(
                return_metrics=return_metrics,
                risk_metrics=risk_metrics,
                efficiency_metrics=efficiency_metrics,
                stability_metrics=stability_metrics,
                trade_metrics=trade_metrics,
                benchmark_metrics=benchmark_metrics,
                drawdown_metrics=drawdown_metrics
            )
            
            # Store metrics in database
            await self._store_performance_metrics(backtest_job_id, results, db)
            
            self.logger.info(f"Performance metrics calculated successfully for: {backtest_job_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to calculate performance metrics: {str(e)}")
            raise
    
    def _calculate_return_metrics(self, daily_returns: List, backtest_job) -> Dict[str, float]:
        """Calculate return-based performance metrics."""
        try:
            if not daily_returns:
                return {}
            
            returns = [float(dr.daily_return_pct) / 100.0 for dr in daily_returns if dr.daily_return_pct]
            portfolio_values = [float(dr.portfolio_value) for dr in daily_returns]
            initial_capital = float(backtest_job.initial_capital)
            
            if not returns or not portfolio_values:
                return {}
            
            # Basic return metrics
            total_return = (portfolio_values[-1] - initial_capital) / initial_capital
            annualized_return = self._annualize_return(total_return, len(daily_returns))
            
            # Compound Annual Growth Rate (CAGR)
            days = len(daily_returns)
            years = days / 365.25
            cagr = (portfolio_values[-1] / initial_capital) ** (1/years) - 1 if years > 0 else 0
            
            # Geometric mean return
            geometric_returns = [(1 + r) for r in returns]
            geometric_mean = (np.prod(geometric_returns) ** (1/len(geometric_returns))) - 1 if geometric_returns else 0
            
            # Arithmetic mean return
            arithmetic_mean = np.mean(returns) if returns else 0
            
            # Return statistics
            return_std = np.std(returns) if len(returns) > 1 else 0
            return_skewness = stats.skew(returns) if len(returns) > 2 else 0
            return_kurtosis = stats.kurtosis(returns) if len(returns) > 3 else 0
            
            # Best and worst periods
            best_day = max(returns) if returns else 0
            worst_day = min(returns) if returns else 0
            
            # Monthly returns analysis
            monthly_returns = self._calculate_monthly_returns(daily_returns)
            best_month = max(monthly_returns) if monthly_returns else 0
            worst_month = min(monthly_returns) if monthly_returns else 0
            
            # Positive/negative return periods
            positive_days = sum(1 for r in returns if r > 0)
            negative_days = sum(1 for r in returns if r < 0)
            positive_ratio = positive_days / len(returns) if returns else 0
            
            return {
                'total_return': total_return,
                'total_return_pct': total_return * 100,
                'annualized_return': annualized_return,
                'annualized_return_pct': annualized_return * 100,
                'cagr': cagr,
                'cagr_pct': cagr * 100,
                'geometric_mean_return': geometric_mean,
                'arithmetic_mean_return': arithmetic_mean,
                'return_volatility': return_std,
                'return_skewness': return_skewness,
                'return_kurtosis': return_kurtosis,
                'best_day_return': best_day,
                'worst_day_return': worst_day,
                'best_month_return': best_month,
                'worst_month_return': worst_month,
                'positive_days_ratio': positive_ratio,
                'positive_days_count': positive_days,
                'negative_days_count': negative_days
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate return metrics: {str(e)}")
            return {}
    
    def _calculate_risk_metrics(self, daily_returns: List, backtest_job) -> Dict[str, float]:
        """Calculate risk-based performance metrics."""
        try:
            if not daily_returns:
                return {}
            
            returns = [float(dr.daily_return_pct) / 100.0 for dr in daily_returns if dr.daily_return_pct]
            portfolio_values = [float(dr.portfolio_value) for dr in daily_returns]
            
            if not returns or len(returns) < 2:
                return {}
            
            # Volatility measures
            daily_volatility = np.std(returns)
            annualized_volatility = daily_volatility * np.sqrt(self.trading_days_per_year)
            
            # Downside deviation (volatility of negative returns only)
            negative_returns = [r for r in returns if r < 0]
            downside_deviation = np.std(negative_returns) if negative_returns else 0
            annualized_downside_deviation = downside_deviation * np.sqrt(self.trading_days_per_year)
            
            # Semi-deviation (deviation below mean)
            mean_return = np.mean(returns)
            below_mean_returns = [r for r in returns if r < mean_return]
            semi_deviation = np.std(below_mean_returns) if below_mean_returns else 0
            
            # Value at Risk (VaR)
            var_95 = np.percentile(returns, 5) if returns else 0  # 5th percentile
            var_99 = np.percentile(returns, 1) if returns else 0  # 1st percentile
            
            # Expected Shortfall (Conditional VaR)
            cvar_95 = np.mean([r for r in returns if r <= var_95]) if returns else 0
            cvar_99 = np.mean([r for r in returns if r <= var_99]) if returns else 0
            
            # Maximum daily loss
            max_daily_loss = min(returns) if returns else 0
            
            # Tracking error (if benchmark data available)
            tracking_error = 0.0
            if hasattr(daily_returns[0], 'benchmark_return') and daily_returns[0].benchmark_return:
                benchmark_returns = [float(dr.benchmark_return) / 100.0 for dr in daily_returns 
                                   if dr.benchmark_return is not None]
                if benchmark_returns and len(benchmark_returns) == len(returns):
                    excess_returns = [r - b for r, b in zip(returns, benchmark_returns)]
                    tracking_error = np.std(excess_returns) * np.sqrt(self.trading_days_per_year)
            
            # Beta (systematic risk)
            beta = self._calculate_beta(returns, daily_returns)
            
            # Correlation with market
            market_correlation = self._calculate_market_correlation(returns, daily_returns)
            
            return {
                'daily_volatility': daily_volatility,
                'annualized_volatility': annualized_volatility,
                'downside_deviation': downside_deviation,
                'annualized_downside_deviation': annualized_downside_deviation,
                'semi_deviation': semi_deviation,
                'var_95': var_95,
                'var_99': var_99,
                'cvar_95': cvar_95,
                'cvar_99': cvar_99,
                'max_daily_loss': max_daily_loss,
                'tracking_error': tracking_error,
                'beta': beta,
                'market_correlation': market_correlation
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics: {str(e)}")
            return {}
    
    def _calculate_efficiency_metrics(self, daily_returns: List, trades: List, 
                                    backtest_job) -> Dict[str, float]:
        """Calculate risk-adjusted return metrics."""
        try:
            if not daily_returns:
                return {}
            
            returns = [float(dr.daily_return_pct) / 100.0 for dr in daily_returns if dr.daily_return_pct]
            portfolio_values = [float(dr.portfolio_value) for dr in daily_returns]
            
            if not returns or len(returns) < 2:
                return {}
            
            # Calculate required metrics
            mean_return = np.mean(returns)
            annualized_return = mean_return * self.trading_days_per_year
            volatility = np.std(returns)
            annualized_volatility = volatility * np.sqrt(self.trading_days_per_year)
            
            # Downside deviation for Sortino ratio
            negative_returns = [r for r in returns if r < 0]
            downside_deviation = np.std(negative_returns) if negative_returns else volatility
            annualized_downside_deviation = downside_deviation * np.sqrt(self.trading_days_per_year)
            
            # Sharpe Ratio
            excess_return = annualized_return - self.risk_free_rate
            sharpe_ratio = excess_return / annualized_volatility if annualized_volatility > 0 else 0
            
            # Sortino Ratio (uses downside deviation instead of total volatility)
            sortino_ratio = excess_return / annualized_downside_deviation if annualized_downside_deviation > 0 else 0
            
            # Calmar Ratio (return/max drawdown)
            max_drawdown = self._calculate_max_drawdown_from_values(portfolio_values)
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Information Ratio (excess return / tracking error)
            information_ratio = 0.0
            if hasattr(daily_returns[0], 'benchmark_return') and daily_returns[0].benchmark_return:
                benchmark_returns = [float(dr.benchmark_return) / 100.0 for dr in daily_returns 
                                   if dr.benchmark_return is not None]
                if benchmark_returns and len(benchmark_returns) == len(returns):
                    excess_returns = [r - b for r, b in zip(returns, benchmark_returns)]
                    mean_excess = np.mean(excess_returns)
                    tracking_error = np.std(excess_returns)
                    information_ratio = mean_excess / tracking_error if tracking_error > 0 else 0
            
            # Treynor Ratio (excess return / beta)
            beta = self._calculate_beta(returns, daily_returns)
            treynor_ratio = excess_return / beta if beta != 0 else 0
            
            # Jensen's Alpha
            alpha = self._calculate_alpha(returns, daily_returns, beta)
            
            # Omega Ratio
            omega_ratio = self._calculate_omega_ratio(returns)
            
            # Gain-to-Pain Ratio
            gain_to_pain = self._calculate_gain_to_pain_ratio(returns)
            
            # Sterling Ratio
            sterling_ratio = self._calculate_sterling_ratio(returns, portfolio_values)
            
            # Burke Ratio
            burke_ratio = self._calculate_burke_ratio(returns, portfolio_values)
            
            return {
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'information_ratio': information_ratio,
                'treynor_ratio': treynor_ratio,
                'jensen_alpha': alpha,
                'omega_ratio': omega_ratio,
                'gain_to_pain_ratio': gain_to_pain,
                'sterling_ratio': sterling_ratio,
                'burke_ratio': burke_ratio
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate efficiency metrics: {str(e)}")
            return {}
    
    def _calculate_stability_metrics(self, daily_returns: List) -> Dict[str, float]:
        """Calculate stability and consistency metrics."""
        try:
            if not daily_returns:
                return {}
            
            returns = [float(dr.daily_return_pct) / 100.0 for dr in daily_returns if dr.daily_return_pct]
            portfolio_values = [float(dr.portfolio_value) for dr in daily_returns]
            
            if not returns or len(returns) < 10:
                return {}
            
            # Rolling window analysis
            window_size = min(30, len(returns) // 4)  # 30-day or 25% of data
            rolling_returns = []
            rolling_volatilities = []
            
            for i in range(window_size, len(returns)):
                window_returns = returns[i-window_size:i]
                rolling_returns.append(np.mean(window_returns))
                rolling_volatilities.append(np.std(window_returns))
            
            # Stability of returns
            return_stability = 1 / (1 + np.std(rolling_returns)) if rolling_returns else 0
            
            # Stability of volatility
            volatility_stability = 1 / (1 + np.std(rolling_volatilities)) if rolling_volatilities else 0
            
            # Hurst Exponent (measure of long-term memory)
            hurst_exponent = self._calculate_hurst_exponent(returns)
            
            # Persistence of performance
            positive_streaks, negative_streaks = self._calculate_streaks(returns)
            avg_positive_streak = np.mean(positive_streaks) if positive_streaks else 0
            avg_negative_streak = np.mean(negative_streaks) if negative_streaks else 0
            max_positive_streak = max(positive_streaks) if positive_streaks else 0
            max_negative_streak = max(negative_streaks) if negative_streaks else 0
            
            # Consistency Score (custom metric)
            consistency_score = self._calculate_consistency_score(returns)
            
            # R-squared of equity curve vs linear trend
            r_squared = self._calculate_equity_curve_r_squared(portfolio_values)
            
            return {
                'return_stability': return_stability,
                'volatility_stability': volatility_stability,
                'hurst_exponent': hurst_exponent,
                'avg_positive_streak': avg_positive_streak,
                'avg_negative_streak': avg_negative_streak,
                'max_positive_streak': max_positive_streak,
                'max_negative_streak': max_negative_streak,
                'consistency_score': consistency_score,
                'equity_curve_r_squared': r_squared
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate stability metrics: {str(e)}")
            return {}
    
    def _calculate_trade_metrics(self, trades: List) -> Dict[str, float]:
        """Calculate trade-specific performance metrics."""
        try:
            if not trades:
                return {}
            
            completed_trades = [t for t in trades if t.exit_date is not None and t.pnl is not None]
            
            if not completed_trades:
                return {}
            
            # Basic trade statistics
            total_trades = len(completed_trades)
            winning_trades = [t for t in completed_trades if float(t.pnl) > 0]
            losing_trades = [t for t in completed_trades if float(t.pnl) <= 0]
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            loss_rate = len(losing_trades) / total_trades if total_trades > 0 else 0
            
            # PnL analysis
            pnls = [float(t.pnl) for t in completed_trades]
            total_pnl = sum(pnls)
            avg_pnl = np.mean(pnls) if pnls else 0
            
            # Winning/losing trade analysis
            win_pnls = [float(t.pnl) for t in winning_trades]
            loss_pnls = [float(t.pnl) for t in losing_trades]
            
            avg_win = np.mean(win_pnls) if win_pnls else 0
            avg_loss = np.mean(loss_pnls) if loss_pnls else 0
            largest_win = max(win_pnls) if win_pnls else 0
            largest_loss = min(loss_pnls) if loss_pnls else 0
            
            # Risk-reward metrics
            profit_factor = abs(sum(win_pnls) / sum(loss_pnls)) if loss_pnls and sum(loss_pnls) != 0 else float('inf')
            expectancy = avg_win * win_rate + avg_loss * loss_rate
            
            # Trade duration analysis
            durations = [t.holding_period_days for t in completed_trades if t.holding_period_days is not None]
            avg_duration = np.mean(durations) if durations else 0
            median_duration = np.median(durations) if durations else 0
            
            # Win/loss streaks
            trade_results = [1 if float(t.pnl) > 0 else 0 for t in completed_trades]
            win_streaks, loss_streaks = self._calculate_trade_streaks(trade_results)
            
            max_consecutive_wins = max(win_streaks) if win_streaks else 0
            max_consecutive_losses = max(loss_streaks) if loss_streaks else 0
            avg_win_streak = np.mean(win_streaks) if win_streaks else 0
            avg_loss_streak = np.mean(loss_streaks) if loss_streaks else 0
            
            # Recovery factor
            recovery_factor = total_pnl / abs(largest_loss) if largest_loss != 0 else 0
            
            # Payoff ratio
            payoff_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            # System Quality Number (SQN)
            sqn = self._calculate_sqn(pnls)
            
            return {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'loss_rate': loss_rate,
                'total_pnl': total_pnl,
                'avg_pnl_per_trade': avg_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'largest_win': largest_win,
                'largest_loss': largest_loss,
                'profit_factor': profit_factor,
                'expectancy': expectancy,
                'avg_trade_duration': avg_duration,
                'median_trade_duration': median_duration,
                'max_consecutive_wins': max_consecutive_wins,
                'max_consecutive_losses': max_consecutive_losses,
                'avg_win_streak': avg_win_streak,
                'avg_loss_streak': avg_loss_streak,
                'recovery_factor': recovery_factor,
                'payoff_ratio': payoff_ratio,
                'system_quality_number': sqn
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate trade metrics: {str(e)}")
            return {}
    
    def _calculate_benchmark_metrics(self, daily_returns: List, backtest_job) -> Dict[str, float]:
        """Calculate benchmark comparison metrics."""
        try:
            if not daily_returns:
                return {}
            
            returns = [float(dr.daily_return_pct) / 100.0 for dr in daily_returns if dr.daily_return_pct]
            
            # Check if benchmark data is available
            benchmark_returns = []
            if hasattr(daily_returns[0], 'benchmark_return') and daily_returns[0].benchmark_return:
                benchmark_returns = [float(dr.benchmark_return) / 100.0 for dr in daily_returns 
                                   if dr.benchmark_return is not None]
            
            if not benchmark_returns or len(benchmark_returns) != len(returns):
                return {'benchmark_available': False}
            
            # Basic benchmark comparison
            portfolio_total_return = (1 + returns[0]) if returns else 1
            for r in returns[1:]:
                portfolio_total_return *= (1 + r)
            portfolio_total_return -= 1
            
            benchmark_total_return = (1 + benchmark_returns[0]) if benchmark_returns else 1
            for r in benchmark_returns[1:]:
                benchmark_total_return *= (1 + r)
            benchmark_total_return -= 1
            
            # Excess return
            excess_return = portfolio_total_return - benchmark_total_return
            
            # Annualized excess return
            days = len(returns)
            years = days / 365.25
            annualized_excess = ((1 + excess_return) ** (1/years) - 1) if years > 0 else 0
            
            # Beta and Alpha
            beta = self._calculate_beta_with_benchmark(returns, benchmark_returns)
            alpha = self._calculate_alpha_with_benchmark(returns, benchmark_returns, beta)
            
            # Correlation
            correlation = np.corrcoef(returns, benchmark_returns)[0, 1] if len(returns) > 1 else 0
            
            # Tracking error
            excess_returns = [r - b for r, b in zip(returns, benchmark_returns)]
            tracking_error = np.std(excess_returns) * np.sqrt(self.trading_days_per_year)
            
            # Information ratio
            mean_excess = np.mean(excess_returns)
            information_ratio = (mean_excess * self.trading_days_per_year) / tracking_error if tracking_error > 0 else 0
            
            # Up/down capture ratios
            up_capture, down_capture = self._calculate_capture_ratios(returns, benchmark_returns)
            
            return {
                'benchmark_available': True,
                'portfolio_total_return': portfolio_total_return,
                'benchmark_total_return': benchmark_total_return,
                'excess_return': excess_return,
                'annualized_excess_return': annualized_excess,
                'beta': beta,
                'alpha': alpha,
                'correlation': correlation,
                'tracking_error': tracking_error,
                'information_ratio': information_ratio,
                'up_capture_ratio': up_capture,
                'down_capture_ratio': down_capture
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate benchmark metrics: {str(e)}")
            return {'benchmark_available': False}
    
    def _calculate_drawdown_metrics(self, daily_returns: List) -> Dict[str, float]:
        """Calculate detailed drawdown analysis."""
        try:
            if not daily_returns:
                return {}
            
            portfolio_values = [float(dr.portfolio_value) for dr in daily_returns]
            
            if not portfolio_values:
                return {}
            
            # Calculate drawdown series
            peaks = []
            drawdowns = []
            underwater_periods = []
            
            current_peak = portfolio_values[0]
            underwater_start = None
            
            for i, value in enumerate(portfolio_values):
                if value > current_peak:
                    current_peak = value
                    if underwater_start is not None:
                        underwater_periods.append(i - underwater_start)
                        underwater_start = None
                else:
                    if underwater_start is None:
                        underwater_start = i
                
                peaks.append(current_peak)
                drawdown = (value - current_peak) / current_peak
                drawdowns.append(drawdown)
            
            # Close final underwater period if needed
            if underwater_start is not None:
                underwater_periods.append(len(portfolio_values) - underwater_start)
            
            # Maximum drawdown
            max_drawdown = min(drawdowns) if drawdowns else 0
            max_drawdown_pct = max_drawdown * 100
            
            # Maximum drawdown duration
            max_drawdown_duration = max(underwater_periods) if underwater_periods else 0
            
            # Average drawdown
            avg_drawdown = np.mean([d for d in drawdowns if d < 0]) if any(d < 0 for d in drawdowns) else 0
            
            # Average drawdown duration
            avg_drawdown_duration = np.mean(underwater_periods) if underwater_periods else 0
            
            # Recovery factor
            total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
            recovery_factor = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Drawdown frequency
            drawdown_count = len(underwater_periods)
            drawdown_frequency = drawdown_count / len(portfolio_values) if portfolio_values else 0
            
            # Pain index (average drawdown)
            pain_index = np.mean([abs(d) for d in drawdowns])
            
            # Ulcer index (RMS of drawdowns)
            ulcer_index = np.sqrt(np.mean([d**2 for d in drawdowns]))
            
            # Lake ratio (time underwater)
            time_underwater = sum(underwater_periods)
            lake_ratio = time_underwater / len(portfolio_values) if portfolio_values else 0
            
            return {
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_drawdown_pct,
                'max_drawdown_duration': max_drawdown_duration,
                'avg_drawdown': avg_drawdown,
                'avg_drawdown_duration': avg_drawdown_duration,
                'recovery_factor': recovery_factor,
                'drawdown_count': drawdown_count,
                'drawdown_frequency': drawdown_frequency,
                'pain_index': pain_index,
                'ulcer_index': ulcer_index,
                'lake_ratio': lake_ratio,
                'time_underwater': time_underwater
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate drawdown metrics: {str(e)}")
            return {}
    
    # Helper methods for complex calculations
    def _annualize_return(self, total_return: float, num_periods: int) -> float:
        """Annualize a total return."""
        if num_periods <= 0:
            return 0
        years = num_periods / self.trading_days_per_year
        return (1 + total_return) ** (1/years) - 1 if years > 0 else 0
    
    def _calculate_monthly_returns(self, daily_returns: List) -> List[float]:
        """Calculate monthly returns from daily returns."""
        monthly_returns = []
        current_month = None
        monthly_value = 1.0
        
        for dr in daily_returns:
            date_obj = dr.date
            month_key = (date_obj.year, date_obj.month)
            
            if current_month != month_key:
                if current_month is not None:
                    monthly_returns.append(monthly_value - 1.0)
                current_month = month_key
                monthly_value = 1.0
            
            daily_return = float(dr.daily_return_pct) / 100.0 if dr.daily_return_pct else 0
            monthly_value *= (1 + daily_return)
        
        # Add final month
        if current_month is not None:
            monthly_returns.append(monthly_value - 1.0)
        
        return monthly_returns
    
    def _calculate_beta(self, returns: List[float], daily_returns: List) -> float:
        """Calculate beta (systematic risk)."""
        try:
            # If benchmark data is available, use it
            if hasattr(daily_returns[0], 'benchmark_return') and daily_returns[0].benchmark_return:
                benchmark_returns = [float(dr.benchmark_return) / 100.0 for dr in daily_returns 
                                   if dr.benchmark_return is not None]
                if benchmark_returns and len(benchmark_returns) == len(returns):
                    return self._calculate_beta_with_benchmark(returns, benchmark_returns)
            
            # Otherwise, use a simplified calculation or default
            return 1.0  # Assume market beta
            
        except Exception:
            return 1.0
    
    def _calculate_beta_with_benchmark(self, returns: List[float], 
                                     benchmark_returns: List[float]) -> float:
        """Calculate beta against a specific benchmark."""
        try:
            if len(returns) != len(benchmark_returns) or len(returns) < 2:
                return 1.0
            
            covariance = np.cov(returns, benchmark_returns)[0, 1]
            benchmark_variance = np.var(benchmark_returns)
            
            return covariance / benchmark_variance if benchmark_variance > 0 else 1.0
            
        except Exception:
            return 1.0
    
    def _calculate_alpha(self, returns: List[float], daily_returns: List, beta: float) -> float:
        """Calculate Jensen's alpha."""
        try:
            portfolio_return = np.mean(returns) * self.trading_days_per_year
            
            # If benchmark data is available
            if hasattr(daily_returns[0], 'benchmark_return') and daily_returns[0].benchmark_return:
                benchmark_returns = [float(dr.benchmark_return) / 100.0 for dr in daily_returns 
                                   if dr.benchmark_return is not None]
                if benchmark_returns:
                    benchmark_return = np.mean(benchmark_returns) * self.trading_days_per_year
                    alpha = portfolio_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))
                    return alpha
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_alpha_with_benchmark(self, returns: List[float], 
                                      benchmark_returns: List[float], beta: float) -> float:
        """Calculate alpha against specific benchmark."""
        try:
            portfolio_return = np.mean(returns) * self.trading_days_per_year
            benchmark_return = np.mean(benchmark_returns) * self.trading_days_per_year
            
            alpha = portfolio_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))
            return alpha
            
        except Exception:
            return 0.0
    
    def _calculate_market_correlation(self, returns: List[float], daily_returns: List) -> float:
        """Calculate correlation with market."""
        try:
            if hasattr(daily_returns[0], 'benchmark_return') and daily_returns[0].benchmark_return:
                benchmark_returns = [float(dr.benchmark_return) / 100.0 for dr in daily_returns 
                                   if dr.benchmark_return is not None]
                if benchmark_returns and len(benchmark_returns) == len(returns):
                    return np.corrcoef(returns, benchmark_returns)[0, 1]
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_max_drawdown_from_values(self, values: List[float]) -> float:
        """Calculate maximum drawdown from portfolio values."""
        if not values:
            return 0.0
        
        peak = values[0]
        max_drawdown = 0.0
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = (value - peak) / peak
            max_drawdown = min(max_drawdown, drawdown)
        
        return max_drawdown
    
    def _calculate_omega_ratio(self, returns: List[float], threshold: float = 0.0) -> float:
        """Calculate Omega ratio."""
        try:
            gains = [max(0, r - threshold) for r in returns]
            losses = [max(0, threshold - r) for r in returns]
            
            total_gains = sum(gains)
            total_losses = sum(losses)
            
            return total_gains / total_losses if total_losses > 0 else float('inf')
            
        except Exception:
            return 0.0
    
    def _calculate_gain_to_pain_ratio(self, returns: List[float]) -> float:
        """Calculate gain-to-pain ratio."""
        try:
            gains = sum([r for r in returns if r > 0])
            losses = abs(sum([r for r in returns if r < 0]))
            
            return gains / losses if losses > 0 else float('inf')
            
        except Exception:
            return 0.0
    
    def _calculate_sterling_ratio(self, returns: List[float], values: List[float]) -> float:
        """Calculate Sterling ratio."""
        try:
            annual_return = np.mean(returns) * self.trading_days_per_year
            max_drawdown = abs(self._calculate_max_drawdown_from_values(values))
            
            return annual_return / max_drawdown if max_drawdown > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_burke_ratio(self, returns: List[float], values: List[float]) -> float:
        """Calculate Burke ratio."""
        try:
            annual_return = np.mean(returns) * self.trading_days_per_year
            
            # Calculate drawdowns
            drawdowns = []
            peak = values[0]
            for value in values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                drawdowns.append(drawdown)
            
            # Burke ratio uses square root of sum of squared drawdowns
            drawdown_squared_sum = sum([d**2 for d in drawdowns])
            burke_denominator = np.sqrt(drawdown_squared_sum)
            
            return annual_return / burke_denominator if burke_denominator > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_hurst_exponent(self, returns: List[float]) -> float:
        """Calculate Hurst exponent (measure of long-term memory)."""
        try:
            if len(returns) < 20:
                return 0.5  # Random walk default
            
            # Simple Hurst calculation using R/S analysis
            n = len(returns)
            returns_array = np.array(returns)
            
            # Calculate mean-adjusted series
            mean_return = np.mean(returns_array)
            deviations = returns_array - mean_return
            
            # Calculate cumulative deviations
            cumulative_deviations = np.cumsum(deviations)
            
            # Calculate range
            R = np.max(cumulative_deviations) - np.min(cumulative_deviations)
            
            # Calculate standard deviation
            S = np.std(returns_array)
            
            # Hurst exponent
            hurst = np.log(R/S) / np.log(n) if S > 0 and R > 0 else 0.5
            
            return max(0, min(1, hurst))  # Clamp between 0 and 1
            
        except Exception:
            return 0.5
    
    def _calculate_streaks(self, returns: List[float]) -> Tuple[List[int], List[int]]:
        """Calculate positive and negative return streaks."""
        positive_streaks = []
        negative_streaks = []
        
        current_positive_streak = 0
        current_negative_streak = 0
        
        for r in returns:
            if r > 0:
                if current_negative_streak > 0:
                    negative_streaks.append(current_negative_streak)
                    current_negative_streak = 0
                current_positive_streak += 1
            elif r < 0:
                if current_positive_streak > 0:
                    positive_streaks.append(current_positive_streak)
                    current_positive_streak = 0
                current_negative_streak += 1
            # For r == 0, we break streaks
            else:
                if current_positive_streak > 0:
                    positive_streaks.append(current_positive_streak)
                    current_positive_streak = 0
                if current_negative_streak > 0:
                    negative_streaks.append(current_negative_streak)
                    current_negative_streak = 0
        
        # Add final streaks
        if current_positive_streak > 0:
            positive_streaks.append(current_positive_streak)
        if current_negative_streak > 0:
            negative_streaks.append(current_negative_streak)
        
        return positive_streaks, negative_streaks
    
    def _calculate_trade_streaks(self, trade_results: List[int]) -> Tuple[List[int], List[int]]:
        """Calculate win/loss streaks from trade results."""
        win_streaks = []
        loss_streaks = []
        
        current_win_streak = 0
        current_loss_streak = 0
        
        for result in trade_results:
            if result == 1:  # Win
                if current_loss_streak > 0:
                    loss_streaks.append(current_loss_streak)
                    current_loss_streak = 0
                current_win_streak += 1
            else:  # Loss
                if current_win_streak > 0:
                    win_streaks.append(current_win_streak)
                    current_win_streak = 0
                current_loss_streak += 1
        
        # Add final streaks
        if current_win_streak > 0:
            win_streaks.append(current_win_streak)
        if current_loss_streak > 0:
            loss_streaks.append(current_loss_streak)
        
        return win_streaks, loss_streaks
    
    def _calculate_consistency_score(self, returns: List[float]) -> float:
        """Calculate a custom consistency score."""
        try:
            if len(returns) < 10:
                return 0.0
            
            # Percentage of positive periods
            positive_ratio = sum(1 for r in returns if r > 0) / len(returns)
            
            # Volatility penalty
            volatility = np.std(returns)
            volatility_penalty = 1 / (1 + volatility * 10)  # Scale volatility
            
            # Streak stability (prefer consistent smaller streaks over large swings)
            positive_streaks, negative_streaks = self._calculate_streaks(returns)
            all_streaks = positive_streaks + negative_streaks
            streak_stability = 1 / (1 + np.std(all_streaks)) if all_streaks else 0.5
            
            # Combined consistency score
            consistency = (positive_ratio * 0.4 + volatility_penalty * 0.3 + streak_stability * 0.3)
            
            return max(0, min(1, consistency))
            
        except Exception:
            return 0.0
    
    def _calculate_equity_curve_r_squared(self, values: List[float]) -> float:
        """Calculate R-squared of equity curve vs linear trend."""
        try:
            if len(values) < 3:
                return 0.0
            
            x = np.arange(len(values))
            y = np.array(values)
            
            # Linear regression
            correlation_matrix = np.corrcoef(x, y)
            correlation = correlation_matrix[0, 1]
            r_squared = correlation ** 2
            
            return max(0, min(1, r_squared))
            
        except Exception:
            return 0.0
    
    def _calculate_sqn(self, pnls: List[float]) -> float:
        """Calculate System Quality Number."""
        try:
            if len(pnls) < 2:
                return 0.0
            
            mean_pnl = np.mean(pnls)
            std_pnl = np.std(pnls)
            n = len(pnls)
            
            sqn = (mean_pnl / std_pnl) * np.sqrt(n) if std_pnl > 0 else 0.0
            
            return sqn
            
        except Exception:
            return 0.0
    
    def _calculate_capture_ratios(self, returns: List[float], 
                                benchmark_returns: List[float]) -> Tuple[float, float]:
        """Calculate up and down capture ratios."""
        try:
            if len(returns) != len(benchmark_returns):
                return 1.0, 1.0
            
            # Separate up and down periods
            up_periods = [(r, b) for r, b in zip(returns, benchmark_returns) if b > 0]
            down_periods = [(r, b) for r, b in zip(returns, benchmark_returns) if b < 0]
            
            # Calculate capture ratios
            up_capture = 1.0
            down_capture = 1.0
            
            if up_periods:
                portfolio_up = np.mean([r for r, b in up_periods])
                benchmark_up = np.mean([b for r, b in up_periods])
                up_capture = portfolio_up / benchmark_up if benchmark_up != 0 else 1.0
            
            if down_periods:
                portfolio_down = np.mean([r for r, b in down_periods])
                benchmark_down = np.mean([b for r, b in down_periods])
                down_capture = portfolio_down / benchmark_down if benchmark_down != 0 else 1.0
            
            return up_capture, down_capture
            
        except Exception:
            return 1.0, 1.0
    
    async def _load_backtest_data(self, backtest_job_id: UUID, 
                                db: AsyncSession) -> Dict[str, Any]:
        """Load all required data for performance calculation."""
        try:
            # Load backtest job
            job_result = await db.execute(
                select(BacktestJob).where(BacktestJob.id == backtest_job_id)
            )
            backtest_job = job_result.scalar_one_or_none()
            
            if not backtest_job:
                return {'success': False, 'error': 'Backtest job not found'}
            
            # Load daily returns
            returns_result = await db.execute(
                select(DailyReturn)
                .where(DailyReturn.backtest_job_id == backtest_job_id)
                .order_by(DailyReturn.date)
            )
            daily_returns = returns_result.scalars().all()
            
            # Load trades
            trades_result = await db.execute(
                select(BacktestTrade)
                .where(BacktestTrade.backtest_job_id == backtest_job_id)
                .order_by(BacktestTrade.entry_date)
            )
            trades = trades_result.scalars().all()
            
            return {
                'success': True,
                'backtest_job': backtest_job,
                'daily_returns': daily_returns,
                'trades': trades
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load backtest data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _store_performance_metrics(self, backtest_job_id: UUID, 
                                       results: PerformanceResults, 
                                       db: AsyncSession):
        """Store calculated metrics in the database."""
        try:
            # Combine all metrics
            all_metrics = {
                **{f"return_{k}": v for k, v in results.return_metrics.items()},
                **{f"risk_{k}": v for k, v in results.risk_metrics.items()},
                **{f"efficiency_{k}": v for k, v in results.efficiency_metrics.items()},
                **{f"stability_{k}": v for k, v in results.stability_metrics.items()},
                **{f"trade_{k}": v for k, v in results.trade_metrics.items()},
                **{f"benchmark_{k}": v for k, v in results.benchmark_metrics.items()},
                **{f"drawdown_{k}": v for k, v in results.drawdown_metrics.items()}
            }
            
            # Store each metric
            for metric_name, metric_value in all_metrics.items():
                if isinstance(metric_value, (int, float)) and not math.isnan(metric_value):
                    category = metric_name.split('_')[0]
                    
                    metric = PerformanceMetric(
                        backtest_job_id=backtest_job_id,
                        metric_category=category,
                        metric_name=metric_name,
                        metric_value=Decimal(str(metric_value)),
                        calculation_period='full_period',
                        calculation_method='standard'
                    )
                    
                    db.add(metric)
            
            await db.commit()
            self.logger.info(f"Stored {len(all_metrics)} performance metrics for backtest: {backtest_job_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to store performance metrics: {str(e)}")
            await db.rollback()
            raise