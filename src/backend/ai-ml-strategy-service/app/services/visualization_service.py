"""
Visualization and Comparison Tools for Phase 5: Backtesting Engine.
Interactive dashboards, charts, and comparison visualizations for backtesting results.
"""

import logging
import asyncio
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from decimal import Decimal
import numpy as np
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.backtesting import (
    BacktestJob, BacktestTrade, DailyReturn, PortfolioSnapshot,
    BacktestComparison, PerformanceMetric
)
from app.services.performance_calculator import PerformanceCalculator
from app.core.config import get_settings


class VisualizationService:
    """Interactive visualization service for backtesting results."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.performance_calculator = PerformanceCalculator()
        
        # Set Plotly theme
        pio.templates.default = "plotly_white"
        
        # Color palettes
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff9800',
            'info': '#17a2b8'
        }
        
        self.color_sequence = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
    
    async def create_interactive_dashboard(self, backtest_job_id: UUID, 
                                         db: AsyncSession) -> Dict[str, Any]:
        """
        Create a comprehensive interactive dashboard for a backtest.
        
        Returns:
            Dictionary containing all dashboard components
        """
        try:
            self.logger.info(f"Creating interactive dashboard for backtest: {backtest_job_id}")
            
            # Load data
            data = await self._load_backtest_data(backtest_job_id, db)
            
            if not data['success']:
                raise ValueError(f"Failed to load backtest data: {data['error']}")
            
            backtest_job = data['backtest_job']
            daily_returns = data['daily_returns']
            trades = data['trades']
            
            # Calculate performance metrics
            performance_metrics = await self.performance_calculator.calculate_comprehensive_metrics(
                backtest_job_id, db
            )
            
            # Create dashboard components
            dashboard = {
                'summary_cards': self._create_summary_cards(backtest_job, performance_metrics),
                'equity_curve': self._create_interactive_equity_curve(daily_returns),
                'drawdown_chart': self._create_interactive_drawdown_chart(daily_returns),
                'returns_distribution': self._create_returns_distribution(daily_returns),
                'monthly_heatmap': self._create_monthly_returns_heatmap(daily_returns),
                'rolling_metrics': self._create_rolling_metrics_chart(daily_returns),
                'trade_analysis': self._create_trade_analysis_dashboard(trades),
                'risk_dashboard': self._create_risk_dashboard(performance_metrics),
                'performance_radar': self._create_performance_radar(performance_metrics),
                'correlation_matrix': self._create_correlation_matrix(daily_returns, trades),
                'efficiency_scatter': self._create_efficiency_scatter(performance_metrics),
                'underwater_chart': self._create_underwater_chart(daily_returns)
            }
            
            # Add metadata
            dashboard['metadata'] = {
                'backtest_id': str(backtest_job_id),
                'backtest_name': backtest_job.name,
                'generated_at': datetime.utcnow().isoformat(),
                'data_range': {
                    'start_date': backtest_job.start_date.isoformat(),
                    'end_date': backtest_job.end_date.isoformat(),
                    'total_days': len(daily_returns),
                    'total_trades': len(trades)
                }
            }
            
            return {'success': True, 'dashboard': dashboard}
            
        except Exception as e:
            self.logger.error(f"Dashboard creation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_comparison_dashboard(self, backtest_ids: List[str], 
                                        db: AsyncSession) -> Dict[str, Any]:
        """Create interactive comparison dashboard for multiple backtests."""
        try:
            self.logger.info(f"Creating comparison dashboard for {len(backtest_ids)} backtests")
            
            # Load data for all backtests
            backtests_data = []
            for backtest_id in backtest_ids:
                data = await self._load_backtest_data(UUID(backtest_id), db)
                if data['success']:
                    backtests_data.append(data)
            
            if len(backtests_data) < 2:
                raise ValueError("At least 2 successful backtests required for comparison")
            
            # Create comparison dashboard
            comparison_dashboard = {
                'summary_comparison': self._create_summary_comparison(backtests_data),
                'equity_curves_comparison': self._create_equity_curves_comparison(backtests_data),
                'performance_comparison': self._create_performance_comparison_chart(backtests_data),
                'risk_return_scatter': self._create_risk_return_scatter(backtests_data),
                'drawdown_comparison': self._create_drawdown_comparison(backtests_data),
                'returns_correlation': self._create_returns_correlation_matrix(backtests_data),
                'efficiency_comparison': self._create_efficiency_comparison(backtests_data),
                'trade_metrics_comparison': self._create_trade_metrics_comparison(backtests_data),
                'monthly_performance_comparison': self._create_monthly_performance_comparison(backtests_data),
                'statistical_analysis': self._create_statistical_analysis(backtests_data)
            }
            
            # Add metadata
            comparison_dashboard['metadata'] = {
                'backtest_ids': backtest_ids,
                'backtest_names': [data['backtest_job'].name for data in backtests_data],
                'generated_at': datetime.utcnow().isoformat(),
                'comparison_count': len(backtests_data)
            }
            
            return {'success': True, 'dashboard': comparison_dashboard}
            
        except Exception as e:
            self.logger.error(f"Comparison dashboard creation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Data loading
    async def _load_backtest_data(self, backtest_job_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """Load all data needed for visualization."""
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
            return {'success': False, 'error': str(e)}
    
    # Summary and overview visualizations
    def _create_summary_cards(self, backtest_job, performance_metrics) -> Dict[str, Any]:
        """Create summary cards for key metrics."""
        try:
            return {
                'total_return': {
                    'value': float(performance_metrics.return_metrics.get('total_return_pct', 0)),
                    'format': 'percentage',
                    'color': 'success' if performance_metrics.return_metrics.get('total_return_pct', 0) > 0 else 'danger',
                    'title': 'Total Return',
                    'subtitle': f"{(backtest_job.end_date - backtest_job.start_date).days} days"
                },
                'sharpe_ratio': {
                    'value': float(performance_metrics.efficiency_metrics.get('sharpe_ratio', 0)),
                    'format': 'decimal',
                    'color': 'success' if performance_metrics.efficiency_metrics.get('sharpe_ratio', 0) > 1 else 'warning',
                    'title': 'Sharpe Ratio',
                    'subtitle': 'Risk-adjusted return'
                },
                'max_drawdown': {
                    'value': abs(float(performance_metrics.drawdown_metrics.get('max_drawdown_pct', 0))),
                    'format': 'percentage',
                    'color': 'danger' if abs(performance_metrics.drawdown_metrics.get('max_drawdown_pct', 0)) > 20 else 'warning',
                    'title': 'Max Drawdown',
                    'subtitle': 'Peak-to-trough decline'
                },
                'win_rate': {
                    'value': float(performance_metrics.trade_metrics.get('win_rate', 0)) * 100,
                    'format': 'percentage',
                    'color': 'success' if performance_metrics.trade_metrics.get('win_rate', 0) > 0.5 else 'warning',
                    'title': 'Win Rate',
                    'subtitle': f"{performance_metrics.trade_metrics.get('total_trades', 0)} trades"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Summary cards creation failed: {str(e)}")
            return {}
    
    def _create_interactive_equity_curve(self, daily_returns) -> str:
        """Create interactive equity curve with annotations."""
        try:
            if not daily_returns:
                return ""
            
            dates = [dr.date for dr in daily_returns]
            portfolio_values = [float(dr.portfolio_value) for dr in daily_returns]
            returns_pct = [float(dr.cumulative_return_pct) if dr.cumulative_return_pct else 0 for dr in daily_returns]
            
            fig = go.Figure()
            
            # Main equity curve
            fig.add_trace(go.Scatter(
                x=dates,
                y=portfolio_values,
                mode='lines',
                name='Portfolio Value',
                line=dict(color=self.colors['primary'], width=2),
                hovertemplate='<b>Date:</b> %{x}<br><b>Value:</b> $%{y:,.2f}<br><b>Return:</b> %{customdata:.2f}%<extra></extra>',
                customdata=returns_pct
            ))
            
            # Add peak markers
            peaks_indices = []
            current_peak = portfolio_values[0]
            for i, value in enumerate(portfolio_values):
                if value > current_peak:
                    current_peak = value
                    peaks_indices.append(i)
            
            if peaks_indices:
                peak_dates = [dates[i] for i in peaks_indices]
                peak_values = [portfolio_values[i] for i in peaks_indices]
                
                fig.add_trace(go.Scatter(
                    x=peak_dates,
                    y=peak_values,
                    mode='markers',
                    name='New Peaks',
                    marker=dict(color=self.colors['success'], size=8, symbol='triangle-up'),
                    hovertemplate='<b>New Peak:</b> $%{y:,.2f}<br><b>Date:</b> %{x}<extra></extra>'
                ))
            
            fig.update_layout(
                title='Interactive Equity Curve',
                xaxis_title='Date',
                yaxis_title='Portfolio Value ($)',
                hovermode='x unified',
                height=500,
                showlegend=True
            )
            
            # Add range selector
            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1M", step="month", stepmode="backward"),
                            dict(count=3, label="3M", step="month", stepmode="backward"),
                            dict(count=6, label="6M", step="month", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    rangeslider=dict(visible=True),
                    type="date"
                )
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Interactive equity curve creation failed: {str(e)}")
            return ""
    
    def _create_interactive_drawdown_chart(self, daily_returns) -> str:
        """Create interactive drawdown chart with underwater periods."""
        try:
            if not daily_returns:
                return ""
            
            dates = [dr.date for dr in daily_returns]
            drawdowns = [float(dr.drawdown) * 100 if dr.drawdown else 0 for dr in daily_returns]
            
            fig = go.Figure()
            
            # Drawdown area chart
            fig.add_trace(go.Scatter(
                x=dates,
                y=drawdowns,
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.3)',
                line=dict(color='red', width=2),
                name='Drawdown',
                hovertemplate='<b>Date:</b> %{x}<br><b>Drawdown:</b> %{y:.2f}%<extra></extra>'
            ))
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            
            # Highlight maximum drawdown
            min_drawdown = min(drawdowns) if drawdowns else 0
            if min_drawdown < 0:
                min_index = drawdowns.index(min_drawdown)
                fig.add_trace(go.Scatter(
                    x=[dates[min_index]],
                    y=[min_drawdown],
                    mode='markers',
                    name='Max Drawdown',
                    marker=dict(color='darkred', size=12, symbol='x'),
                    hovertemplate=f'<b>Max Drawdown:</b> {min_drawdown:.2f}%<br><b>Date:</b> %{{x}}<extra></extra>'
                ))
            
            fig.update_layout(
                title='Drawdown Analysis',
                xaxis_title='Date',
                yaxis_title='Drawdown (%)',
                hovermode='x unified',
                height=400
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Interactive drawdown chart creation failed: {str(e)}")
            return ""
    
    def _create_returns_distribution(self, daily_returns) -> str:
        """Create returns distribution histogram with statistics."""
        try:
            if not daily_returns:
                return ""
            
            returns = [float(dr.daily_return_pct) if dr.daily_return_pct else 0 for dr in daily_returns]
            
            if not returns:
                return ""
            
            fig = go.Figure()
            
            # Histogram
            fig.add_trace(go.Histogram(
                x=returns,
                nbinsx=50,
                name='Daily Returns',
                marker_color=self.colors['primary'],
                opacity=0.7,
                hovertemplate='<b>Return Range:</b> %{x}%<br><b>Frequency:</b> %{y}<extra></extra>'
            ))
            
            # Add normal distribution overlay
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            x_norm = np.linspace(min(returns), max(returns), 100)
            y_norm = len(returns) * (max(returns) - min(returns)) / 50 * \
                     (1 / (std_return * np.sqrt(2 * np.pi))) * \
                     np.exp(-0.5 * ((x_norm - mean_return) / std_return) ** 2)
            
            fig.add_trace(go.Scatter(
                x=x_norm,
                y=y_norm,
                mode='lines',
                name='Normal Distribution',
                line=dict(color='red', dash='dash'),
                hovertemplate='<b>Normal Dist:</b> %{y:.2f}<extra></extra>'
            ))
            
            # Add vertical lines for mean and std
            fig.add_vline(x=mean_return, line_dash="dash", line_color="green", 
                         annotation_text=f"Mean: {mean_return:.3f}%")
            fig.add_vline(x=mean_return + std_return, line_dash="dot", line_color="orange",
                         annotation_text=f"+1σ: {mean_return + std_return:.3f}%")
            fig.add_vline(x=mean_return - std_return, line_dash="dot", line_color="orange",
                         annotation_text=f"-1σ: {mean_return - std_return:.3f}%")
            
            fig.update_layout(
                title='Daily Returns Distribution',
                xaxis_title='Daily Return (%)',
                yaxis_title='Frequency',
                height=400,
                showlegend=True
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Returns distribution creation failed: {str(e)}")
            return ""
    
    def _create_monthly_returns_heatmap(self, daily_returns) -> str:
        """Create interactive monthly returns heatmap."""
        try:
            if not daily_returns:
                return ""
            
            # Calculate monthly returns
            monthly_data = {}
            current_month = None
            monthly_start_value = None
            
            for dr in daily_returns:
                month_key = (dr.date.year, dr.date.month)
                
                if current_month != month_key:
                    if current_month is not None and monthly_start_value is not None:
                        monthly_return = (float(prev_value) - monthly_start_value) / monthly_start_value * 100
                        monthly_data[current_month] = monthly_return
                    
                    current_month = month_key
                    monthly_start_value = float(dr.portfolio_value)
                
                prev_value = dr.portfolio_value
            
            # Add final month
            if current_month is not None and monthly_start_value is not None:
                monthly_return = (float(prev_value) - monthly_start_value) / monthly_start_value * 100
                monthly_data[current_month] = monthly_return
            
            if not monthly_data:
                return ""
            
            # Create heatmap data
            years = sorted(set(year for year, month in monthly_data.keys()))
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            heatmap_data = []
            heatmap_text = []
            for year in years:
                row_data = []
                row_text = []
                for month_num in range(1, 13):
                    if (year, month_num) in monthly_data:
                        value = monthly_data[(year, month_num)]
                        row_data.append(value)
                        row_text.append(f"{value:.1f}%")
                    else:
                        row_data.append(None)
                        row_text.append("")
                heatmap_data.append(row_data)
                heatmap_text.append(row_text)
            
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=months,
                y=years,
                colorscale='RdYlGn',
                text=heatmap_text,
                texttemplate="%{text}",
                textfont={"size": 10},
                hoverongaps=False,
                hovertemplate='<b>%{y} %{x}:</b> %{text}<extra></extra>',
                colorbar=dict(title="Return (%)")
            ))
            
            fig.update_layout(
                title='Monthly Returns Heatmap',
                xaxis_title='Month',
                yaxis_title='Year',
                height=300 + len(years) * 30
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Monthly returns heatmap creation failed: {str(e)}")
            return ""
    
    def _create_rolling_metrics_chart(self, daily_returns) -> str:
        """Create rolling metrics chart (Sharpe, volatility, etc.)."""
        try:
            if len(daily_returns) < 30:
                return ""
            
            dates = [dr.date for dr in daily_returns]
            returns = [float(dr.daily_return_pct) if dr.daily_return_pct else 0 for dr in daily_returns]
            
            # Calculate rolling metrics
            window = min(30, len(returns) // 4)
            df = pd.DataFrame({'date': dates, 'returns': returns})
            
            df['rolling_mean'] = df['returns'].rolling(window=window).mean() * 252  # Annualized
            df['rolling_std'] = df['returns'].rolling(window=window).std() * np.sqrt(252)  # Annualized
            df['rolling_sharpe'] = df['rolling_mean'] / df['rolling_std']
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('Rolling Return (Annualized)', 'Rolling Volatility (Annualized)', 'Rolling Sharpe Ratio'),
                vertical_spacing=0.08
            )
            
            # Rolling return
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['rolling_mean'],
                mode='lines',
                name=f'{window}-Day Rolling Return',
                line=dict(color=self.colors['primary'])
            ), row=1, col=1)
            
            # Rolling volatility
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['rolling_std'],
                mode='lines',
                name=f'{window}-Day Rolling Volatility',
                line=dict(color=self.colors['danger'])
            ), row=2, col=1)
            
            # Rolling Sharpe
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['rolling_sharpe'],
                mode='lines',
                name=f'{window}-Day Rolling Sharpe',
                line=dict(color=self.colors['success'])
            ), row=3, col=1)
            
            # Add horizontal line at Sharpe = 1
            fig.add_hline(y=1, line_dash="dash", line_color="gray", row=3, col=1)
            
            fig.update_layout(
                title=f'Rolling Performance Metrics ({window}-Day Window)',
                height=600,
                showlegend=False
            )
            
            fig.update_xaxes(title_text="Date", row=3, col=1)
            fig.update_yaxes(title_text="Return (%)", row=1, col=1)
            fig.update_yaxes(title_text="Volatility (%)", row=2, col=1)
            fig.update_yaxes(title_text="Sharpe Ratio", row=3, col=1)
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Rolling metrics chart creation failed: {str(e)}")
            return ""
    
    def _create_trade_analysis_dashboard(self, trades) -> Dict[str, str]:
        """Create comprehensive trade analysis dashboard."""
        try:
            completed_trades = [t for t in trades if t.exit_date is not None and t.pnl is not None]
            
            if not completed_trades:
                return {}
            
            dashboard = {}
            
            # Trade P&L over time
            dashboard['pnl_timeline'] = self._create_trade_pnl_timeline(completed_trades)
            
            # Trade duration vs P&L
            dashboard['duration_vs_pnl'] = self._create_trade_duration_vs_pnl(completed_trades)
            
            # P&L distribution
            dashboard['pnl_distribution'] = self._create_trade_pnl_distribution(completed_trades)
            
            # Win/Loss analysis
            dashboard['win_loss_analysis'] = self._create_win_loss_analysis(completed_trades)
            
            # MAE/MFE analysis
            dashboard['mae_mfe_analysis'] = self._create_mae_mfe_analysis(completed_trades)
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Trade analysis dashboard creation failed: {str(e)}")
            return {}
    
    def _create_trade_pnl_timeline(self, trades) -> str:
        """Create trade P&L timeline chart."""
        try:
            exit_dates = [t.exit_date for t in trades]
            pnls = [float(t.pnl) for t in trades]
            cumulative_pnl = np.cumsum(pnls)
            
            fig = go.Figure()
            
            # Individual trade markers
            colors = [self.colors['success'] if pnl > 0 else self.colors['danger'] for pnl in pnls]
            
            fig.add_trace(go.Scatter(
                x=exit_dates,
                y=pnls,
                mode='markers',
                name='Individual Trades',
                marker=dict(
                    color=colors,
                    size=8,
                    line=dict(width=1, color='white')
                ),
                hovertemplate='<b>Date:</b> %{x}<br><b>P&L:</b> $%{y:,.2f}<extra></extra>'
            ))
            
            # Cumulative P&L line
            fig.add_trace(go.Scatter(
                x=exit_dates,
                y=cumulative_pnl,
                mode='lines',
                name='Cumulative P&L',
                line=dict(color=self.colors['primary'], width=3),
                yaxis='y2',
                hovertemplate='<b>Date:</b> %{x}<br><b>Cumulative P&L:</b> $%{y:,.2f}<extra></extra>'
            ))
            
            fig.update_layout(
                title='Trade P&L Timeline',
                xaxis_title='Exit Date',
                yaxis_title='Trade P&L ($)',
                yaxis2=dict(
                    title='Cumulative P&L ($)',
                    overlaying='y',
                    side='right'
                ),
                height=400
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Trade P&L timeline creation failed: {str(e)}")
            return ""
    
    def _create_trade_duration_vs_pnl(self, trades) -> str:
        """Create trade duration vs P&L scatter plot."""
        try:
            durations = [t.holding_period_days for t in trades if t.holding_period_days is not None]
            pnls = [float(t.pnl) for t in trades if t.holding_period_days is not None]
            
            if not durations:
                return ""
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=durations,
                y=pnls,
                mode='markers',
                marker=dict(
                    size=8,
                    color=pnls,
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="P&L ($)"),
                    line=dict(width=1, color='white')
                ),
                hovertemplate='<b>Duration:</b> %{x} days<br><b>P&L:</b> $%{y:,.2f}<extra></extra>'
            ))
            
            # Add trend line
            if len(durations) > 1:
                z = np.polyfit(durations, pnls, 1)
                p = np.poly1d(z)
                trend_x = np.linspace(min(durations), max(durations), 100)
                trend_y = p(trend_x)
                
                fig.add_trace(go.Scatter(
                    x=trend_x,
                    y=trend_y,
                    mode='lines',
                    name='Trend Line',
                    line=dict(color='red', dash='dash'),
                    hoverinfo='skip'
                ))
            
            fig.update_layout(
                title='Trade Duration vs P&L',
                xaxis_title='Holding Period (Days)',
                yaxis_title='P&L ($)',
                height=400
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Trade duration vs P&L creation failed: {str(e)}")
            return ""
    
    def _create_trade_pnl_distribution(self, trades) -> str:
        """Create trade P&L distribution histogram."""
        try:
            pnls = [float(t.pnl) for t in trades]
            
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=pnls,
                nbinsx=30,
                name='Trade P&L Distribution',
                marker_color=self.colors['primary'],
                opacity=0.7
            ))
            
            # Add vertical lines for statistics
            mean_pnl = np.mean(pnls)
            median_pnl = np.median(pnls)
            
            fig.add_vline(x=mean_pnl, line_dash="dash", line_color="red",
                         annotation_text=f"Mean: ${mean_pnl:.2f}")
            fig.add_vline(x=median_pnl, line_dash="dash", line_color="green",
                         annotation_text=f"Median: ${median_pnl:.2f}")
            fig.add_vline(x=0, line_dash="solid", line_color="black", opacity=0.5)
            
            fig.update_layout(
                title='Trade P&L Distribution',
                xaxis_title='P&L ($)',
                yaxis_title='Frequency',
                height=400
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Trade P&L distribution creation failed: {str(e)}")
            return ""
    
    def _create_win_loss_analysis(self, trades) -> str:
        """Create win/loss analysis chart."""
        try:
            winning_trades = [t for t in trades if float(t.pnl) > 0]
            losing_trades = [t for t in trades if float(t.pnl) <= 0]
            
            categories = ['Winning Trades', 'Losing Trades']
            values = [len(winning_trades), len(losing_trades)]
            colors = [self.colors['success'], self.colors['danger']]
            
            avg_win = np.mean([float(t.pnl) for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([float(t.pnl) for t in losing_trades]) if losing_trades else 0
            
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Trade Count', 'Average P&L'),
                specs=[[{'type': 'pie'}, {'type': 'bar'}]]
            )
            
            # Pie chart for trade count
            fig.add_trace(go.Pie(
                labels=categories,
                values=values,
                marker_colors=colors,
                hovertemplate='<b>%{label}:</b> %{value} (%{percent})<extra></extra>'
            ), row=1, col=1)
            
            # Bar chart for average P&L
            fig.add_trace(go.Bar(
                x=categories,
                y=[avg_win, avg_loss],
                marker_color=colors,
                hovertemplate='<b>%{x}:</b> $%{y:,.2f}<extra></extra>'
            ), row=1, col=2)
            
            fig.update_layout(
                title='Win/Loss Analysis',
                height=400,
                showlegend=False
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Win/loss analysis creation failed: {str(e)}")
            return ""
    
    def _create_mae_mfe_analysis(self, trades) -> str:
        """Create MAE/MFE (Maximum Adverse/Favorable Excursion) analysis."""
        try:
            mae_values = [float(t.mae) for t in trades if t.mae is not None]
            mfe_values = [float(t.mfe) for t in trades if t.mfe is not None]
            pnls = [float(t.pnl) for t in trades if t.mae is not None and t.mfe is not None]
            
            if not mae_values or not mfe_values:
                return ""
            
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('MAE vs Final P&L', 'MFE vs Final P&L')
            )
            
            # MAE scatter plot
            fig.add_trace(go.Scatter(
                x=mae_values,
                y=pnls,
                mode='markers',
                name='MAE',
                marker=dict(color=self.colors['danger'], size=6),
                hovertemplate='<b>MAE:</b> $%{x:,.2f}<br><b>Final P&L:</b> $%{y:,.2f}<extra></extra>'
            ), row=1, col=1)
            
            # MFE scatter plot
            fig.add_trace(go.Scatter(
                x=mfe_values,
                y=pnls,
                mode='markers',
                name='MFE',
                marker=dict(color=self.colors['success'], size=6),
                hovertemplate='<b>MFE:</b> $%{x:,.2f}<br><b>Final P&L:</b> $%{y:,.2f}<extra></extra>'
            ), row=1, col=2)
            
            fig.update_layout(
                title='Maximum Adverse/Favorable Excursion Analysis',
                height=400,
                showlegend=False
            )
            
            fig.update_xaxes(title_text="MAE ($)", row=1, col=1)
            fig.update_xaxes(title_text="MFE ($)", row=1, col=2)
            fig.update_yaxes(title_text="Final P&L ($)", row=1, col=1)
            fig.update_yaxes(title_text="Final P&L ($)", row=1, col=2)
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"MAE/MFE analysis creation failed: {str(e)}")
            return ""
    
    # Risk and performance visualization methods
    def _create_risk_dashboard(self, performance_metrics) -> Dict[str, str]:
        """Create comprehensive risk dashboard."""
        try:
            dashboard = {}
            
            # Risk metrics gauge charts
            dashboard['risk_gauges'] = self._create_risk_gauges(performance_metrics)
            
            # VaR visualization
            dashboard['var_chart'] = self._create_var_chart(performance_metrics)
            
            # Risk decomposition
            dashboard['risk_decomposition'] = self._create_risk_decomposition(performance_metrics)
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Risk dashboard creation failed: {str(e)}")
            return {}
    
    def _create_risk_gauges(self, performance_metrics) -> str:
        """Create risk metrics gauge charts."""
        try:
            # Define risk metrics for gauges
            volatility = performance_metrics.risk_metrics.get('annualized_volatility', 0) * 100
            max_dd = abs(performance_metrics.drawdown_metrics.get('max_drawdown_pct', 0))
            var_95 = abs(performance_metrics.risk_metrics.get('var_95', 0)) * 100
            
            fig = make_subplots(
                rows=1, cols=3,
                specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]],
                subplot_titles=('Volatility', 'Max Drawdown', 'VaR 95%')
            )
            
            # Volatility gauge
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=volatility,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Volatility (%)"},
                gauge={
                    'axis': {'range': [None, 50]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 15], 'color': "lightgreen"},
                        {'range': [15, 25], 'color': "yellow"},
                        {'range': [25, 50], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 30
                    }
                }
            ), row=1, col=1)
            
            # Max Drawdown gauge
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=max_dd,
                title={'text': "Max Drawdown (%)"},
                gauge={
                    'axis': {'range': [None, 50]},
                    'bar': {'color': "darkred"},
                    'steps': [
                        {'range': [0, 10], 'color': "lightgreen"},
                        {'range': [10, 20], 'color': "yellow"},
                        {'range': [20, 50], 'color': "red"}
                    ]
                }
            ), row=1, col=2)
            
            # VaR gauge
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=var_95,
                title={'text': "VaR 95% (%)"},
                gauge={
                    'axis': {'range': [None, 20]},
                    'bar': {'color': "darkorange"},
                    'steps': [
                        {'range': [0, 5], 'color': "lightgreen"},
                        {'range': [5, 10], 'color': "yellow"},
                        {'range': [10, 20], 'color': "red"}
                    ]
                }
            ), row=1, col=3)
            
            fig.update_layout(
                title="Risk Metrics Dashboard",
                height=300
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Risk gauges creation failed: {str(e)}")
            return ""
    
    def _create_performance_radar(self, performance_metrics) -> str:
        """Create performance radar chart."""
        try:
            # Define metrics for radar chart
            metrics = {
                'Return': min(performance_metrics.return_metrics.get('annualized_return_pct', 0) / 20, 1),
                'Sharpe Ratio': min(performance_metrics.efficiency_metrics.get('sharpe_ratio', 0) / 3, 1),
                'Sortino Ratio': min(performance_metrics.efficiency_metrics.get('sortino_ratio', 0) / 3, 1),
                'Calmar Ratio': min(performance_metrics.efficiency_metrics.get('calmar_ratio', 0) / 2, 1),
                'Win Rate': performance_metrics.trade_metrics.get('win_rate', 0),
                'Profit Factor': min(performance_metrics.trade_metrics.get('profit_factor', 0) / 3, 1),
                'Recovery Factor': min(performance_metrics.drawdown_metrics.get('recovery_factor', 0) / 5, 1),
                'Stability': min(performance_metrics.stability_metrics.get('consistency_score', 0) / 100, 1)
            }
            
            # Normalize all values to 0-1
            normalized_values = [max(0, min(1, v)) for v in metrics.values()]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=normalized_values,
                theta=list(metrics.keys()),
                fill='toself',
                name='Performance Profile',
                fillcolor='rgba(31, 119, 180, 0.3)',
                line=dict(color=self.colors['primary'], width=2)
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1],
                        tickmode='array',
                        tickvals=[0.2, 0.4, 0.6, 0.8, 1.0],
                        ticktext=['20%', '40%', '60%', '80%', '100%']
                    )
                ),
                showlegend=True,
                title="Performance Radar Chart",
                height=500
            )
            
            return fig.to_json()
            
        except Exception as e:
            self.logger.error(f"Performance radar creation failed: {str(e)}")
            return ""
    
    # Additional helper methods would be implemented here for:
    # - Comparison visualizations
    # - Statistical analysis charts
    # - Correlation matrices
    # - Efficiency scatter plots
    # - Underwater charts
    # etc.
    
    # For brevity, I'll include method signatures for the remaining methods
    
    def _create_correlation_matrix(self, daily_returns, trades) -> str:
        """Create correlation matrix of various metrics."""
        # Implementation would create correlation analysis
        return ""
    
    def _create_efficiency_scatter(self, performance_metrics) -> str:
        """Create efficiency scatter plot."""
        # Implementation would create risk vs return scatter
        return ""
    
    def _create_underwater_chart(self, daily_returns) -> str:
        """Create underwater equity chart."""
        # Implementation would show time underwater
        return ""
    
    # Comparison methods
    def _create_summary_comparison(self, backtests_data) -> Dict[str, Any]:
        """Create summary comparison table."""
        # Implementation would compare key metrics
        return {}
    
    def _create_equity_curves_comparison(self, backtests_data) -> str:
        """Create overlaid equity curves comparison."""
        # Implementation would overlay multiple equity curves
        return ""
    
    def _create_performance_comparison_chart(self, backtests_data) -> str:
        """Create performance metrics comparison chart."""
        # Implementation would create comparison bar charts
        return ""
    
    def _create_risk_return_scatter(self, backtests_data) -> str:
        """Create risk-return scatter plot for comparison."""
        # Implementation would create scatter plot
        return ""
    
    def _create_drawdown_comparison(self, backtests_data) -> str:
        """Create drawdown comparison chart."""
        # Implementation would overlay drawdown charts
        return ""
    
    def _create_returns_correlation_matrix(self, backtests_data) -> str:
        """Create returns correlation matrix."""
        # Implementation would show correlation between strategies
        return ""
    
    def _create_efficiency_comparison(self, backtests_data) -> str:
        """Create efficiency metrics comparison."""
        # Implementation would compare efficiency ratios
        return ""
    
    def _create_trade_metrics_comparison(self, backtests_data) -> str:
        """Create trade metrics comparison."""
        # Implementation would compare trade statistics
        return ""
    
    def _create_monthly_performance_comparison(self, backtests_data) -> str:
        """Create monthly performance comparison."""
        # Implementation would compare monthly returns
        return ""
    
    def _create_statistical_analysis(self, backtests_data) -> Dict[str, Any]:
        """Create statistical analysis of comparisons."""
        # Implementation would perform statistical tests
        return {}
    
    def _create_var_chart(self, performance_metrics) -> str:
        """Create Value at Risk visualization."""
        # Implementation would show VaR analysis
        return ""
    
    def _create_risk_decomposition(self, performance_metrics) -> str:
        """Create risk decomposition chart."""
        # Implementation would break down risk components
        return ""