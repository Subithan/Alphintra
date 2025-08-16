"""
Backtesting Report Generator for Phase 5: Backtesting Engine.
Generates comprehensive PDF and HTML reports with charts, tables, and analysis.
"""

import logging
import asyncio
import json
import os
import base64
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from decimal import Decimal
import numpy as np
import pandas as pd
from io import BytesIO, StringIO

# For report generation
from jinja2 import Environment, FileSystemLoader, Template
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from weasyprint import HTML, CSS
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
from app.services.advanced_testing import AdvancedTestingEngine
from app.core.config import get_settings


class BacktestReportGenerator:
    """Professional backtesting report generator."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.performance_calculator = PerformanceCalculator()
        self.advanced_testing = AdvancedTestingEngine()
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Create reports directory if it doesn't exist
        self.reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Set up Jinja2 environment for HTML templates
        self.jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates"))
        )
    
    async def generate_comprehensive_report(self, backtest_job_id: UUID, 
                                          report_format: str = "pdf",
                                          include_advanced_testing: bool = True,
                                          db: AsyncSession) -> Dict[str, Any]:
        """
        Generate a comprehensive backtesting report.
        
        Args:
            backtest_job_id: ID of the backtest job
            report_format: 'pdf', 'html', or 'both'
            include_advanced_testing: Whether to include robustness testing
        """
        try:
            self.logger.info(f"Generating comprehensive report for backtest: {backtest_job_id}")
            
            # Load backtest data
            data = await self._load_report_data(backtest_job_id, db)
            
            if not data['success']:
                raise ValueError(f"Failed to load backtest data: {data['error']}")
            
            backtest_job = data['backtest_job']
            daily_returns = data['daily_returns']
            trades = data['trades']
            
            # Calculate performance metrics
            performance_metrics = await self.performance_calculator.calculate_comprehensive_metrics(
                backtest_job_id, db
            )
            
            # Run advanced testing if requested
            advanced_testing_results = None
            if include_advanced_testing and backtest_job.status == "completed":
                try:
                    advanced_testing_results = await self.advanced_testing.run_robustness_testing(
                        backtest_job, db
                    )
                except Exception as e:
                    self.logger.warning(f"Advanced testing failed: {str(e)}")
            
            # Generate charts
            charts = await self._generate_charts(backtest_job, daily_returns, trades, performance_metrics)
            
            # Prepare report data
            report_data = {
                'backtest_job': backtest_job,
                'performance_metrics': performance_metrics,
                'advanced_testing': advanced_testing_results,
                'charts': charts,
                'daily_returns': daily_returns,
                'trades': trades,
                'generation_timestamp': datetime.utcnow(),
                'summary_stats': self._calculate_summary_stats(daily_returns, trades),
                'risk_analysis': self._generate_risk_analysis(performance_metrics),
                'trade_analysis': self._generate_trade_analysis(trades),
                'recommendations': self._generate_recommendations(performance_metrics, advanced_testing_results)
            }
            
            # Generate reports
            generated_files = []
            
            if report_format in ['html', 'both']:
                html_file = await self._generate_html_report(report_data, backtest_job_id)
                generated_files.append(html_file)
            
            if report_format in ['pdf', 'both']:
                pdf_file = await self._generate_pdf_report(report_data, backtest_job_id)
                generated_files.append(pdf_file)
            
            self.logger.info(f"Report generation completed: {len(generated_files)} files created")
            
            return {
                'success': True,
                'generated_files': generated_files,
                'report_data': {
                    'backtest_id': str(backtest_job_id),
                    'backtest_name': backtest_job.name,
                    'total_return': float(performance_metrics.return_metrics.get('total_return_pct', 0)),
                    'sharpe_ratio': float(performance_metrics.efficiency_metrics.get('sharpe_ratio', 0)),
                    'max_drawdown': float(performance_metrics.drawdown_metrics.get('max_drawdown_pct', 0)),
                    'total_trades': len(trades),
                    'win_rate': float(performance_metrics.trade_metrics.get('win_rate', 0)) * 100
                }
            }
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_comparison_report(self, comparison_id: UUID, 
                                       report_format: str = "pdf",
                                       db: AsyncSession) -> Dict[str, Any]:
        """Generate a comparison report for multiple backtests."""
        try:
            self.logger.info(f"Generating comparison report: {comparison_id}")
            
            # Load comparison data
            comparison_data = await self._load_comparison_data(comparison_id, db)
            
            if not comparison_data['success']:
                raise ValueError(f"Failed to load comparison data: {comparison_data['error']}")
            
            # Generate comparison charts
            comparison_charts = await self._generate_comparison_charts(comparison_data)
            
            # Prepare comparison report data
            report_data = {
                'comparison': comparison_data['comparison'],
                'backtests': comparison_data['backtests'],
                'comparison_charts': comparison_charts,
                'generation_timestamp': datetime.utcnow(),
                'ranking': self._calculate_backtest_ranking(comparison_data['backtests']),
                'statistical_analysis': self._perform_statistical_comparison(comparison_data['backtests'])
            }
            
            # Generate comparison report
            generated_files = []
            
            if report_format in ['html', 'both']:
                html_file = await self._generate_comparison_html_report(report_data, comparison_id)
                generated_files.append(html_file)
            
            if report_format in ['pdf', 'both']:
                pdf_file = await self._generate_comparison_pdf_report(report_data, comparison_id)
                generated_files.append(pdf_file)
            
            return {
                'success': True,
                'generated_files': generated_files,
                'comparison_summary': report_data['ranking']
            }
            
        except Exception as e:
            self.logger.error(f"Comparison report generation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Data loading methods
    async def _load_report_data(self, backtest_job_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """Load all data needed for report generation."""
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
    
    async def _load_comparison_data(self, comparison_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """Load comparison data for report generation."""
        try:
            from app.models.backtesting import BacktestComparison
            
            # Load comparison
            comp_result = await db.execute(
                select(BacktestComparison).where(BacktestComparison.id == comparison_id)
            )
            comparison = comp_result.scalar_one_or_none()
            
            if not comparison:
                return {'success': False, 'error': 'Comparison not found'}
            
            # Load all backtests in comparison
            backtests = []
            for backtest_id in comparison.backtest_ids:
                data = await self._load_report_data(UUID(backtest_id), db)
                if data['success']:
                    backtests.append(data)
            
            return {
                'success': True,
                'comparison': comparison,
                'backtests': backtests
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Chart generation methods
    async def _generate_charts(self, backtest_job, daily_returns, trades, performance_metrics) -> Dict[str, str]:
        """Generate all charts for the report."""
        charts = {}
        
        try:
            # 1. Equity Curve Chart
            charts['equity_curve'] = self._create_equity_curve_chart(daily_returns)
            
            # 2. Drawdown Chart
            charts['drawdown'] = self._create_drawdown_chart(daily_returns)
            
            # 3. Monthly Returns Heatmap
            charts['monthly_returns'] = self._create_monthly_returns_heatmap(daily_returns)
            
            # 4. Trade Analysis Charts
            if trades:
                charts['trade_pnl_distribution'] = self._create_trade_pnl_distribution(trades)
                charts['trade_duration_analysis'] = self._create_trade_duration_analysis(trades)
                charts['rolling_returns'] = self._create_rolling_returns_chart(daily_returns)
            
            # 5. Risk Metrics Radar Chart
            charts['risk_radar'] = self._create_risk_radar_chart(performance_metrics)
            
            # 6. Performance Metrics Dashboard
            charts['performance_dashboard'] = self._create_performance_dashboard(performance_metrics)
            
        except Exception as e:
            self.logger.error(f"Chart generation failed: {str(e)}")
        
        return charts
    
    def _create_equity_curve_chart(self, daily_returns) -> str:
        """Create equity curve chart."""
        try:
            if not daily_returns:
                return ""
            
            dates = [dr.date for dr in daily_returns]
            portfolio_values = [float(dr.portfolio_value) for dr in daily_returns]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=portfolio_values,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig.update_layout(
                title='Equity Curve',
                xaxis_title='Date',
                yaxis_title='Portfolio Value ($)',
                template='plotly_white',
                height=400
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="equity-curve-chart")
            
        except Exception as e:
            self.logger.error(f"Equity curve chart generation failed: {str(e)}")
            return ""
    
    def _create_drawdown_chart(self, daily_returns) -> str:
        """Create drawdown chart."""
        try:
            if not daily_returns:
                return ""
            
            dates = [dr.date for dr in daily_returns]
            drawdowns = [float(dr.drawdown) * 100 if dr.drawdown else 0 for dr in daily_returns]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=drawdowns,
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.3)',
                line=dict(color='red'),
                name='Drawdown'
            ))
            
            fig.update_layout(
                title='Drawdown Analysis',
                xaxis_title='Date',
                yaxis_title='Drawdown (%)',
                template='plotly_white',
                height=400
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="drawdown-chart")
            
        except Exception as e:
            self.logger.error(f"Drawdown chart generation failed: {str(e)}")
            return ""
    
    def _create_monthly_returns_heatmap(self, daily_returns) -> str:
        """Create monthly returns heatmap."""
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
            for year in years:
                row = []
                for month_num in range(1, 13):
                    if (year, month_num) in monthly_data:
                        row.append(monthly_data[(year, month_num)])
                    else:
                        row.append(None)
                heatmap_data.append(row)
            
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=months,
                y=years,
                colorscale='RdYlGn',
                text=[[f"{val:.1f}%" if val is not None else "" for val in row] for row in heatmap_data],
                texttemplate="%{text}",
                textfont={"size": 10},
                hoverongaps=False
            ))
            
            fig.update_layout(
                title='Monthly Returns Heatmap',
                xaxis_title='Month',
                yaxis_title='Year',
                template='plotly_white',
                height=300
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="monthly-returns-heatmap")
            
        except Exception as e:
            self.logger.error(f"Monthly returns heatmap generation failed: {str(e)}")
            return ""
    
    def _create_trade_pnl_distribution(self, trades) -> str:
        """Create trade P&L distribution chart."""
        try:
            completed_trades = [t for t in trades if t.exit_date is not None and t.pnl is not None]
            
            if not completed_trades:
                return ""
            
            pnls = [float(t.pnl) for t in completed_trades]
            
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=pnls,
                nbinsx=30,
                name='Trade P&L',
                marker_color='blue',
                opacity=0.7
            ))
            
            fig.update_layout(
                title='Trade P&L Distribution',
                xaxis_title='P&L ($)',
                yaxis_title='Frequency',
                template='plotly_white',
                height=400
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="trade-pnl-distribution")
            
        except Exception as e:
            self.logger.error(f"Trade P&L distribution chart generation failed: {str(e)}")
            return ""
    
    def _create_trade_duration_analysis(self, trades) -> str:
        """Create trade duration analysis chart."""
        try:
            completed_trades = [t for t in trades if t.exit_date is not None and t.holding_period_days is not None]
            
            if not completed_trades:
                return ""
            
            durations = [t.holding_period_days for t in completed_trades]
            pnls = [float(t.pnl) for t in completed_trades]
            
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
                    colorbar=dict(title="P&L ($)")
                ),
                text=[f"Trade {i+1}" for i in range(len(durations))],
                hovertemplate='<b>%{text}</b><br>Duration: %{x} days<br>P&L: $%{y}<extra></extra>'
            ))
            
            fig.update_layout(
                title='Trade Duration vs P&L',
                xaxis_title='Holding Period (Days)',
                yaxis_title='P&L ($)',
                template='plotly_white',
                height=400
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="trade-duration-analysis")
            
        except Exception as e:
            self.logger.error(f"Trade duration analysis chart generation failed: {str(e)}")
            return ""
    
    def _create_rolling_returns_chart(self, daily_returns) -> str:
        """Create rolling returns chart."""
        try:
            if len(daily_returns) < 30:
                return ""
            
            dates = [dr.date for dr in daily_returns]
            returns = [float(dr.daily_return_pct) if dr.daily_return_pct else 0 for dr in daily_returns]
            
            # Calculate rolling statistics
            df = pd.DataFrame({'date': dates, 'returns': returns})
            df['rolling_mean'] = df['returns'].rolling(window=30).mean()
            df['rolling_std'] = df['returns'].rolling(window=30).std()
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['rolling_mean'],
                mode='lines',
                name='30-Day Rolling Mean',
                line=dict(color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['rolling_std'],
                mode='lines',
                name='30-Day Rolling Std',
                line=dict(color='red'),
                yaxis='y2'
            ))
            
            fig.update_layout(
                title='Rolling Returns Analysis',
                xaxis_title='Date',
                yaxis_title='Rolling Mean Return (%)',
                yaxis2=dict(
                    title='Rolling Std (%)',
                    overlaying='y',
                    side='right'
                ),
                template='plotly_white',
                height=400
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="rolling-returns-chart")
            
        except Exception as e:
            self.logger.error(f"Rolling returns chart generation failed: {str(e)}")
            return ""
    
    def _create_risk_radar_chart(self, performance_metrics) -> str:
        """Create risk metrics radar chart."""
        try:
            # Define metrics for radar chart
            metrics = {
                'Sharpe Ratio': performance_metrics.efficiency_metrics.get('sharpe_ratio', 0),
                'Sortino Ratio': performance_metrics.efficiency_metrics.get('sortino_ratio', 0),
                'Calmar Ratio': performance_metrics.efficiency_metrics.get('calmar_ratio', 0),
                'Information Ratio': performance_metrics.efficiency_metrics.get('information_ratio', 0),
                'Win Rate': performance_metrics.trade_metrics.get('win_rate', 0) * 100,
                'Profit Factor': min(performance_metrics.trade_metrics.get('profit_factor', 0), 5)  # Cap at 5
            }
            
            # Normalize metrics to 0-1 scale for radar chart
            normalized_metrics = {}
            for name, value in metrics.items():
                if name == 'Win Rate':
                    normalized_metrics[name] = value / 100
                elif name == 'Profit Factor':
                    normalized_metrics[name] = min(value / 3, 1)  # Normalize to 3
                else:
                    normalized_metrics[name] = min(max(value / 2, 0), 1)  # Normalize to 2, clamp 0-1
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=list(normalized_metrics.values()),
                theta=list(normalized_metrics.keys()),
                fill='toself',
                name='Risk Metrics'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                showlegend=True,
                title="Risk-Adjusted Performance Metrics",
                template='plotly_white',
                height=400
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="risk-radar-chart")
            
        except Exception as e:
            self.logger.error(f"Risk radar chart generation failed: {str(e)}")
            return ""
    
    def _create_performance_dashboard(self, performance_metrics) -> str:
        """Create performance metrics dashboard."""
        try:
            # Create subplots for dashboard
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Return Metrics', 'Risk Metrics', 'Trade Metrics', 'Efficiency Ratios'),
                specs=[[{'type': 'bar'}, {'type': 'bar'}],
                       [{'type': 'bar'}, {'type': 'bar'}]]
            )
            
            # Return metrics
            return_metrics = {
                'Total Return': performance_metrics.return_metrics.get('total_return_pct', 0),
                'Annualized Return': performance_metrics.return_metrics.get('annualized_return_pct', 0),
                'CAGR': performance_metrics.return_metrics.get('cagr_pct', 0)
            }
            
            fig.add_trace(go.Bar(
                x=list(return_metrics.keys()),
                y=list(return_metrics.values()),
                name='Returns (%)',
                marker_color='green'
            ), row=1, col=1)
            
            # Risk metrics
            risk_metrics = {
                'Volatility': performance_metrics.risk_metrics.get('annualized_volatility', 0) * 100,
                'Max Drawdown': abs(performance_metrics.drawdown_metrics.get('max_drawdown_pct', 0)),
                'VaR 95%': abs(performance_metrics.risk_metrics.get('var_95', 0)) * 100
            }
            
            fig.add_trace(go.Bar(
                x=list(risk_metrics.keys()),
                y=list(risk_metrics.values()),
                name='Risk (%)',
                marker_color='red'
            ), row=1, col=2)
            
            # Trade metrics
            trade_metrics = {
                'Win Rate': performance_metrics.trade_metrics.get('win_rate', 0) * 100,
                'Profit Factor': min(performance_metrics.trade_metrics.get('profit_factor', 0), 10),
                'Expectancy': performance_metrics.trade_metrics.get('expectancy', 0)
            }
            
            fig.add_trace(go.Bar(
                x=list(trade_metrics.keys()),
                y=list(trade_metrics.values()),
                name='Trade Metrics',
                marker_color='blue'
            ), row=2, col=1)
            
            # Efficiency ratios
            efficiency_metrics = {
                'Sharpe': performance_metrics.efficiency_metrics.get('sharpe_ratio', 0),
                'Sortino': performance_metrics.efficiency_metrics.get('sortino_ratio', 0),
                'Calmar': performance_metrics.efficiency_metrics.get('calmar_ratio', 0)
            }
            
            fig.add_trace(go.Bar(
                x=list(efficiency_metrics.keys()),
                y=list(efficiency_metrics.values()),
                name='Efficiency Ratios',
                marker_color='purple'
            ), row=2, col=2)
            
            fig.update_layout(
                title_text="Performance Dashboard",
                showlegend=False,
                height=600,
                template='plotly_white'
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="performance-dashboard")
            
        except Exception as e:
            self.logger.error(f"Performance dashboard generation failed: {str(e)}")
            return ""
    
    # Comparison chart methods
    async def _generate_comparison_charts(self, comparison_data) -> Dict[str, str]:
        """Generate charts for backtest comparison."""
        charts = {}
        
        try:
            backtests = comparison_data['backtests']
            
            # 1. Equity Curves Comparison
            charts['equity_comparison'] = self._create_equity_comparison_chart(backtests)
            
            # 2. Performance Metrics Comparison
            charts['metrics_comparison'] = self._create_metrics_comparison_chart(backtests)
            
            # 3. Risk-Return Scatter
            charts['risk_return_scatter'] = self._create_risk_return_scatter(backtests)
            
        except Exception as e:
            self.logger.error(f"Comparison charts generation failed: {str(e)}")
        
        return charts
    
    def _create_equity_comparison_chart(self, backtests) -> str:
        """Create equity curves comparison chart."""
        try:
            fig = go.Figure()
            
            colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
            
            for i, backtest_data in enumerate(backtests):
                if not backtest_data['success']:
                    continue
                
                daily_returns = backtest_data['daily_returns']
                backtest_job = backtest_data['backtest_job']
                
                if daily_returns:
                    dates = [dr.date for dr in daily_returns]
                    # Normalize to percentage returns
                    initial_value = float(daily_returns[0].portfolio_value)
                    normalized_values = [(float(dr.portfolio_value) - initial_value) / initial_value * 100 
                                       for dr in daily_returns]
                    
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=normalized_values,
                        mode='lines',
                        name=backtest_job.name,
                        line=dict(color=colors[i % len(colors)])
                    ))
            
            fig.update_layout(
                title='Equity Curves Comparison',
                xaxis_title='Date',
                yaxis_title='Return (%)',
                template='plotly_white',
                height=500
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="equity-comparison-chart")
            
        except Exception as e:
            self.logger.error(f"Equity comparison chart generation failed: {str(e)}")
            return ""
    
    def _create_metrics_comparison_chart(self, backtests) -> str:
        """Create performance metrics comparison chart."""
        try:
            backtest_names = []
            total_returns = []
            sharpe_ratios = []
            max_drawdowns = []
            
            for backtest_data in backtests:
                if not backtest_data['success']:
                    continue
                
                backtest_job = backtest_data['backtest_job']
                backtest_names.append(backtest_job.name)
                total_returns.append(float(backtest_job.total_return_pct) if backtest_job.total_return_pct else 0)
                sharpe_ratios.append(float(backtest_job.sharpe_ratio) if backtest_job.sharpe_ratio else 0)
                max_drawdowns.append(abs(float(backtest_job.max_drawdown)) * 100 if backtest_job.max_drawdown else 0)
            
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=('Total Return (%)', 'Sharpe Ratio', 'Max Drawdown (%)'),
                specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]]
            )
            
            fig.add_trace(go.Bar(
                x=backtest_names,
                y=total_returns,
                name='Total Return',
                marker_color='green'
            ), row=1, col=1)
            
            fig.add_trace(go.Bar(
                x=backtest_names,
                y=sharpe_ratios,
                name='Sharpe Ratio',
                marker_color='blue'
            ), row=1, col=2)
            
            fig.add_trace(go.Bar(
                x=backtest_names,
                y=max_drawdowns,
                name='Max Drawdown',
                marker_color='red'
            ), row=1, col=3)
            
            fig.update_layout(
                title_text="Key Metrics Comparison",
                showlegend=False,
                height=400,
                template='plotly_white'
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="metrics-comparison-chart")
            
        except Exception as e:
            self.logger.error(f"Metrics comparison chart generation failed: {str(e)}")
            return ""
    
    def _create_risk_return_scatter(self, backtests) -> str:
        """Create risk-return scatter plot."""
        try:
            returns = []
            risks = []
            names = []
            sizes = []
            
            for backtest_data in backtests:
                if not backtest_data['success']:
                    continue
                
                backtest_job = backtest_data['backtest_job']
                names.append(backtest_job.name)
                returns.append(float(backtest_job.total_return_pct) if backtest_job.total_return_pct else 0)
                
                # Use max drawdown as risk measure
                risk = abs(float(backtest_job.max_drawdown)) * 100 if backtest_job.max_drawdown else 0
                risks.append(risk)
                
                # Size based on Sharpe ratio
                sharpe = float(backtest_job.sharpe_ratio) if backtest_job.sharpe_ratio else 0
                sizes.append(max(10, min(50, abs(sharpe) * 20)))
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=risks,
                y=returns,
                mode='markers+text',
                marker=dict(
                    size=sizes,
                    color=returns,
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Return (%)")
                ),
                text=names,
                textposition="top center",
                hovertemplate='<b>%{text}</b><br>Risk: %{x}%<br>Return: %{y}%<extra></extra>'
            ))
            
            fig.update_layout(
                title='Risk-Return Analysis',
                xaxis_title='Risk (Max Drawdown %)',
                yaxis_title='Return (%)',
                template='plotly_white',
                height=500
            )
            
            return fig.to_html(include_plotlyjs='cdn', div_id="risk-return-scatter")
            
        except Exception as e:
            self.logger.error(f"Risk-return scatter generation failed: {str(e)}")
            return ""
    
    # Analysis methods
    def _calculate_summary_stats(self, daily_returns, trades) -> Dict[str, Any]:
        """Calculate summary statistics for the report."""
        try:
            summary = {}
            
            if daily_returns:
                portfolio_values = [float(dr.portfolio_value) for dr in daily_returns]
                daily_rets = [float(dr.daily_return_pct) if dr.daily_return_pct else 0 for dr in daily_returns]
                
                summary.update({
                    'total_days': len(daily_returns),
                    'final_portfolio_value': portfolio_values[-1] if portfolio_values else 0,
                    'best_day': max(daily_rets) if daily_rets else 0,
                    'worst_day': min(daily_rets) if daily_rets else 0,
                    'positive_days': sum(1 for r in daily_rets if r > 0),
                    'negative_days': sum(1 for r in daily_rets if r < 0),
                    'avg_daily_return': np.mean(daily_rets) if daily_rets else 0
                })
            
            if trades:
                completed_trades = [t for t in trades if t.exit_date is not None]
                pnls = [float(t.pnl) for t in completed_trades if t.pnl is not None]
                
                summary.update({
                    'total_trades': len(trades),
                    'completed_trades': len(completed_trades),
                    'total_pnl': sum(pnls) if pnls else 0,
                    'avg_pnl_per_trade': np.mean(pnls) if pnls else 0,
                    'best_trade': max(pnls) if pnls else 0,
                    'worst_trade': min(pnls) if pnls else 0
                })
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Summary stats calculation failed: {str(e)}")
            return {}
    
    def _generate_risk_analysis(self, performance_metrics) -> Dict[str, Any]:
        """Generate risk analysis section."""
        try:
            risk_analysis = {}
            
            # VaR analysis
            var_95 = performance_metrics.risk_metrics.get('var_95', 0)
            if var_95:
                risk_analysis['var_interpretation'] = f"There is a 5% chance of losing more than {abs(var_95)*100:.2f}% in a single day"
            
            # Drawdown analysis
            max_dd = performance_metrics.drawdown_metrics.get('max_drawdown_pct', 0)
            if max_dd:
                risk_analysis['drawdown_interpretation'] = f"Maximum peak-to-trough decline was {abs(max_dd):.2f}%"
            
            # Volatility analysis
            volatility = performance_metrics.risk_metrics.get('annualized_volatility', 0)
            if volatility:
                risk_analysis['volatility_interpretation'] = f"Annual volatility of {volatility*100:.2f}% indicates {'high' if volatility > 0.2 else 'moderate' if volatility > 0.1 else 'low'} risk"
            
            return risk_analysis
            
        except Exception as e:
            self.logger.error(f"Risk analysis generation failed: {str(e)}")
            return {}
    
    def _generate_trade_analysis(self, trades) -> Dict[str, Any]:
        """Generate trade analysis section."""
        try:
            if not trades:
                return {}
            
            completed_trades = [t for t in trades if t.exit_date is not None and t.pnl is not None]
            
            if not completed_trades:
                return {}
            
            pnls = [float(t.pnl) for t in completed_trades]
            durations = [t.holding_period_days for t in completed_trades if t.holding_period_days is not None]
            
            analysis = {
                'completion_rate': len(completed_trades) / len(trades) * 100,
                'avg_holding_period': np.mean(durations) if durations else 0,
                'median_holding_period': np.median(durations) if durations else 0,
                'longest_trade': max(durations) if durations else 0,
                'shortest_trade': min(durations) if durations else 0,
                'pnl_distribution': {
                    'std': np.std(pnls),
                    'skewness': float(stats.skew(pnls)) if len(pnls) > 2 else 0,
                    'kurtosis': float(stats.kurtosis(pnls)) if len(pnls) > 3 else 0
                }
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Trade analysis generation failed: {str(e)}")
            return {}
    
    def _generate_recommendations(self, performance_metrics, advanced_testing_results) -> List[str]:
        """Generate recommendations based on performance analysis."""
        recommendations = []
        
        try:
            # Performance-based recommendations
            sharpe_ratio = performance_metrics.efficiency_metrics.get('sharpe_ratio', 0)
            if sharpe_ratio < 1.0:
                recommendations.append("Consider improving risk-adjusted returns (Sharpe ratio < 1.0)")
            elif sharpe_ratio > 2.0:
                recommendations.append("Excellent risk-adjusted performance (Sharpe ratio > 2.0)")
            
            # Drawdown recommendations
            max_dd = abs(performance_metrics.drawdown_metrics.get('max_drawdown_pct', 0))
            if max_dd > 20:
                recommendations.append("High maximum drawdown - consider implementing stricter risk management")
            elif max_dd < 5:
                recommendations.append("Low drawdown indicates good risk control")
            
            # Win rate recommendations
            win_rate = performance_metrics.trade_metrics.get('win_rate', 0)
            if win_rate < 0.4:
                recommendations.append("Low win rate - review strategy signals or consider trend-following approaches")
            elif win_rate > 0.7:
                recommendations.append("High win rate - ensure profit factor is also strong")
            
            # Profit factor recommendations
            profit_factor = performance_metrics.trade_metrics.get('profit_factor', 0)
            if profit_factor < 1.2:
                recommendations.append("Low profit factor - review exit strategies and position sizing")
            elif profit_factor > 2.0:
                recommendations.append("Strong profit factor indicates good trade management")
            
            # Advanced testing recommendations
            if advanced_testing_results:
                if 'recommendations' in advanced_testing_results:
                    recommendations.extend(advanced_testing_results['recommendations'])
            
            return recommendations[:10]  # Limit to top 10 recommendations
            
        except Exception as e:
            self.logger.error(f"Recommendations generation failed: {str(e)}")
            return ["Unable to generate recommendations due to data processing error"]
    
    # Report generation methods
    async def _generate_html_report(self, report_data, backtest_job_id) -> str:
        """Generate HTML report."""
        try:
            # Create HTML template
            html_template = self._create_html_template()
            
            # Render template
            html_content = html_template.render(
                report_data=report_data,
                generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Save HTML file
            filename = f"backtest_report_{backtest_job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report generated: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"HTML report generation failed: {str(e)}")
            raise
    
    async def _generate_pdf_report(self, report_data, backtest_job_id) -> str:
        """Generate PDF report."""
        try:
            # Generate HTML first
            html_template = self._create_html_template()
            html_content = html_template.render(
                report_data=report_data,
                generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Convert to PDF
            filename = f"backtest_report_{backtest_job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(self.reports_dir, filename)
            
            # CSS for PDF styling
            css_content = """
            @page {
                margin: 1in;
                @top-center {
                    content: "Backtesting Report";
                }
                @bottom-center {
                    content: counter(page);
                }
            }
            body {
                font-family: 'Arial', sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #333;
                padding-bottom: 20px;
            }
            .metric-box {
                border: 1px solid #ddd;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
            }
            .chart-container {
                page-break-inside: avoid;
                margin: 20px 0;
            }
            """
            
            HTML(string=html_content).write_pdf(
                filepath,
                stylesheets=[CSS(string=css_content)]
            )
            
            self.logger.info(f"PDF report generated: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"PDF report generation failed: {str(e)}")
            raise
    
    def _create_html_template(self) -> Template:
        """Create HTML template for reports."""
        template_str = '''
<!DOCTYPE html>
<html>
<head>
    <title>Backtesting Report</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            line-height: 1.6; 
        }
        .header { 
            text-align: center; 
            border-bottom: 2px solid #333; 
            padding-bottom: 20px; 
            margin-bottom: 30px; 
        }
        .section { 
            margin: 30px 0; 
        }
        .metric-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 15px; 
            margin: 20px 0; 
        }
        .metric-box { 
            border: 1px solid #ddd; 
            padding: 15px; 
            border-radius: 5px; 
            background: #f9f9f9; 
        }
        .chart-container { 
            margin: 20px 0; 
            text-align: center; 
        }
        .recommendation { 
            background: #e8f4fd; 
            border-left: 4px solid #1976d2; 
            padding: 10px; 
            margin: 5px 0; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin: 15px 0; 
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 8px; 
            text-align: left; 
        }
        th { 
            background-color: #f5f5f5; 
        }
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="header">
        <h1>Backtesting Report</h1>
        <h2>{{ report_data.backtest_job.name }}</h2>
        <p>Generated on: {{ generation_date }}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="metric-grid">
            <div class="metric-box">
                <h4>Total Return</h4>
                <p><strong>{{ "%.2f"|format(report_data.performance_metrics.return_metrics.get('total_return_pct', 0)) }}%</strong></p>
            </div>
            <div class="metric-box">
                <h4>Sharpe Ratio</h4>
                <p><strong>{{ "%.2f"|format(report_data.performance_metrics.efficiency_metrics.get('sharpe_ratio', 0)) }}</strong></p>
            </div>
            <div class="metric-box">
                <h4>Max Drawdown</h4>
                <p><strong>{{ "%.2f"|format(report_data.performance_metrics.drawdown_metrics.get('max_drawdown_pct', 0)|abs) }}%</strong></p>
            </div>
            <div class="metric-box">
                <h4>Win Rate</h4>
                <p><strong>{{ "%.1f"|format(report_data.performance_metrics.trade_metrics.get('win_rate', 0) * 100) }}%</strong></p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Performance Charts</h2>
        
        <div class="chart-container">
            <h3>Equity Curve</h3>
            {{ report_data.charts.equity_curve|safe }}
        </div>
        
        <div class="chart-container">
            <h3>Drawdown Analysis</h3>
            {{ report_data.charts.drawdown|safe }}
        </div>
        
        {% if report_data.charts.monthly_returns %}
        <div class="chart-container">
            <h3>Monthly Returns</h3>
            {{ report_data.charts.monthly_returns|safe }}
        </div>
        {% endif %}
    </div>

    <div class="section">
        <h2>Detailed Metrics</h2>
        
        <h3>Return Metrics</h3>
        <table>
            {% for key, value in report_data.performance_metrics.return_metrics.items() %}
            <tr>
                <td>{{ key.replace('_', ' ').title() }}</td>
                <td>{{ "%.4f"|format(value) }}{% if 'pct' in key %}%{% endif %}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h3>Risk Metrics</h3>
        <table>
            {% for key, value in report_data.performance_metrics.risk_metrics.items() %}
            <tr>
                <td>{{ key.replace('_', ' ').title() }}</td>
                <td>{{ "%.4f"|format(value) }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h3>Trade Metrics</h3>
        <table>
            {% for key, value in report_data.performance_metrics.trade_metrics.items() %}
            <tr>
                <td>{{ key.replace('_', ' ').title() }}</td>
                <td>{{ "%.4f"|format(value) }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    {% if report_data.recommendations %}
    <div class="section">
        <h2>Recommendations</h2>
        {% for recommendation in report_data.recommendations %}
        <div class="recommendation">{{ recommendation }}</div>
        {% endfor %}
    </div>
    {% endif %}

    {% if report_data.advanced_testing %}
    <div class="section">
        <h2>Robustness Analysis</h2>
        <p><strong>Overall Robustness Score:</strong> {{ "%.1f"|format(report_data.advanced_testing.get('overall_robustness_score', 0)) }}/100</p>
        
        {% if report_data.advanced_testing.walk_forward %}
        <h3>Walk-Forward Analysis</h3>
        <ul>
            <li>Consistency Score: {{ "%.1f"|format(report_data.advanced_testing.walk_forward.get('consistency_score', 0)) }}</li>
            <li>Profitable Windows: {{ "%.1f"|format(report_data.advanced_testing.walk_forward.get('profitable_windows_pct', 0)) }}%</li>
        </ul>
        {% endif %}
        
        {% if report_data.advanced_testing.monte_carlo %}
        <h3>Monte Carlo Analysis</h3>
        <ul>
            <li>Robustness Score: {{ "%.1f"|format(report_data.advanced_testing.monte_carlo.get('robustness_score', 0)) }}</li>
            <li>Success Rate: {{ "%.1f"|format(report_data.advanced_testing.monte_carlo.get('success_rate', 0)) }}%</li>
        </ul>
        {% endif %}
    </div>
    {% endif %}

</body>
</html>
        '''
        
        return Template(template_str)
    
    # Comparison report methods
    async def _generate_comparison_html_report(self, report_data, comparison_id) -> str:
        """Generate HTML comparison report."""
        # Implementation similar to _generate_html_report but for comparisons
        # Simplified for brevity
        filename = f"comparison_report_{comparison_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.reports_dir, filename)
        
        # Create basic comparison HTML (can be enhanced)
        html_content = f"""
        <html>
        <head><title>Backtest Comparison Report</title></head>
        <body>
            <h1>Backtest Comparison Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            {report_data['comparison_charts'].get('equity_comparison', '')}
            {report_data['comparison_charts'].get('metrics_comparison', '')}
        </body>
        </html>
        """
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    async def _generate_comparison_pdf_report(self, report_data, comparison_id) -> str:
        """Generate PDF comparison report."""
        # Generate HTML first then convert to PDF
        html_file = await self._generate_comparison_html_report(report_data, comparison_id)
        
        filename = f"comparison_report_{comparison_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        HTML(string=html_content).write_pdf(filepath)
        
        return filepath
    
    # Helper methods for comparison
    def _calculate_backtest_ranking(self, backtests) -> List[Dict[str, Any]]:
        """Calculate ranking of backtests based on multiple criteria."""
        ranking = []
        
        for backtest_data in backtests:
            if not backtest_data['success']:
                continue
            
            job = backtest_data['backtest_job']
            score = 0
            
            # Scoring based on multiple factors
            if job.total_return_pct:
                score += float(job.total_return_pct) * 0.3
            if job.sharpe_ratio:
                score += float(job.sharpe_ratio) * 20 * 0.4
            if job.max_drawdown:
                score -= abs(float(job.max_drawdown)) * 100 * 0.3
            
            ranking.append({
                'name': job.name,
                'score': score,
                'total_return': float(job.total_return_pct) if job.total_return_pct else 0,
                'sharpe_ratio': float(job.sharpe_ratio) if job.sharpe_ratio else 0,
                'max_drawdown': float(job.max_drawdown) if job.max_drawdown else 0
            })
        
        return sorted(ranking, key=lambda x: x['score'], reverse=True)
    
    def _perform_statistical_comparison(self, backtests) -> Dict[str, Any]:
        """Perform statistical comparison between backtests."""
        try:
            # Collect returns for statistical testing
            all_returns = []
            backtest_names = []
            
            for backtest_data in backtests:
                if not backtest_data['success']:
                    continue
                
                daily_returns = backtest_data['daily_returns']
                if daily_returns:
                    returns = [float(dr.daily_return_pct) if dr.daily_return_pct else 0 for dr in daily_returns]
                    all_returns.append(returns)
                    backtest_names.append(backtest_data['backtest_job'].name)
            
            if len(all_returns) < 2:
                return {}
            
            # Perform t-tests between pairs
            statistical_results = {}
            
            for i in range(len(all_returns)):
                for j in range(i+1, len(all_returns)):
                    try:
                        t_stat, p_value = stats.ttest_ind(all_returns[i], all_returns[j])
                        pair_name = f"{backtest_names[i]} vs {backtest_names[j]}"
                        statistical_results[pair_name] = {
                            't_statistic': float(t_stat),
                            'p_value': float(p_value),
                            'significant': p_value < 0.05
                        }
                    except Exception:
                        pass
            
            return statistical_results
            
        except Exception as e:
            self.logger.error(f"Statistical comparison failed: {str(e)}")
            return {}