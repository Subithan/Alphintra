"""
Advanced Testing Methodologies for Phase 5: Backtesting Engine.
Implements Walk-Forward Analysis, Monte Carlo simulation, Cross-Validation, and Robustness Testing.
"""

import logging
import asyncio
import json
import math
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import UUID, uuid4
from decimal import Decimal
import numpy as np
import pandas as pd
from dataclasses import dataclass
from scipy import stats
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.backtesting import (
    BacktestJob, BacktestTrade, DailyReturn, PortfolioSnapshot,
    BacktestStatus, BacktestMethodology
)
from app.services.backtesting_engine import BacktestingEngine
from app.services.performance_calculator import PerformanceCalculator
from app.core.config import get_settings


@dataclass
class WalkForwardResult:
    """Results from walk-forward analysis."""
    total_windows: int
    profitable_windows: int
    consistency_score: float
    avg_return_per_window: float
    std_return_per_window: float
    min_return: float
    max_return: float
    window_results: List[Dict[str, Any]]
    overall_metrics: Dict[str, float]


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""
    total_simulations: int
    confidence_intervals: Dict[str, Dict[str, float]]
    probability_metrics: Dict[str, float]
    simulation_results: List[Dict[str, Any]]
    risk_metrics: Dict[str, float]
    robustness_score: float


@dataclass
class CrossValidationResult:
    """Results from cross-validation analysis."""
    total_folds: int
    avg_performance: Dict[str, float]
    performance_stability: Dict[str, float]
    fold_results: List[Dict[str, Any]]
    out_of_sample_degradation: Dict[str, float]
    overfitting_score: float


class AdvancedTestingEngine:
    """Advanced testing methodologies for strategy validation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.backtesting_engine = BacktestingEngine()
        self.performance_calculator = PerformanceCalculator()
    
    async def run_walk_forward_analysis(self, backtest_job: BacktestJob, 
                                      training_window_days: int = 252,
                                      testing_window_days: int = 63,
                                      step_size_days: int = 21,
                                      db: AsyncSession) -> WalkForwardResult:
        """
        Run walk-forward analysis to test strategy robustness over time.
        
        Args:
            training_window_days: Days for optimization/training
            testing_window_days: Days for out-of-sample testing
            step_size_days: Days to advance between windows
        """
        try:
            self.logger.info(f"Starting walk-forward analysis for backtest: {backtest_job.id}")
            
            start_date = backtest_job.start_date
            end_date = backtest_job.end_date
            total_days = (end_date - start_date).days
            
            if total_days < training_window_days + testing_window_days:
                raise ValueError("Insufficient data for walk-forward analysis")
            
            window_results = []
            current_start = start_date
            window_number = 1
            
            while current_start + timedelta(days=training_window_days + testing_window_days) <= end_date:
                # Define training and testing periods
                training_start = current_start
                training_end = current_start + timedelta(days=training_window_days)
                testing_start = training_end + timedelta(days=1)
                testing_end = testing_start + timedelta(days=testing_window_days)
                
                self.logger.info(f"Processing window {window_number}: "
                               f"Training {training_start} to {training_end}, "
                               f"Testing {testing_start} to {testing_end}")
                
                # Run training period (parameter optimization)
                training_result = await self._run_window_backtest(
                    backtest_job, training_start, training_end, 
                    f"WF_Train_{window_number}", db
                )
                
                # Run testing period (out-of-sample validation)
                testing_result = await self._run_window_backtest(
                    backtest_job, testing_start, testing_end,
                    f"WF_Test_{window_number}", db
                )
                
                # Calculate window metrics
                window_metrics = await self._calculate_window_metrics(
                    training_result, testing_result, window_number
                )
                
                window_results.append(window_metrics)
                
                # Move to next window
                current_start += timedelta(days=step_size_days)
                window_number += 1
            
            # Calculate overall walk-forward metrics
            overall_metrics = self._calculate_walk_forward_overall_metrics(window_results)
            
            # Calculate consistency score
            consistency_score = self._calculate_consistency_score(window_results)
            
            result = WalkForwardResult(
                total_windows=len(window_results),
                profitable_windows=sum(1 for w in window_results if w['testing_return'] > 0),
                consistency_score=consistency_score,
                avg_return_per_window=overall_metrics['avg_return'],
                std_return_per_window=overall_metrics['std_return'],
                min_return=overall_metrics['min_return'],
                max_return=overall_metrics['max_return'],
                window_results=window_results,
                overall_metrics=overall_metrics
            )
            
            self.logger.info(f"Walk-forward analysis completed: {len(window_results)} windows")
            return result
            
        except Exception as e:
            self.logger.error(f"Walk-forward analysis failed: {str(e)}")
            raise
    
    async def run_monte_carlo_simulation(self, backtest_job: BacktestJob,
                                       num_simulations: int = 1000,
                                       parameter_variance: float = 0.1,
                                       db: AsyncSession) -> MonteCarloResult:
        """
        Run Monte Carlo simulation to assess strategy robustness to parameter changes.
        
        Args:
            num_simulations: Number of Monte Carlo runs
            parameter_variance: Percentage variance for parameter perturbation
        """
        try:
            self.logger.info(f"Starting Monte Carlo simulation: {num_simulations} runs")
            
            simulation_results = []
            base_config = backtest_job.backtest_config.copy()
            
            for sim_num in range(num_simulations):
                if sim_num % 100 == 0:
                    self.logger.info(f"Monte Carlo progress: {sim_num}/{num_simulations}")
                
                # Perturb parameters
                perturbed_config = self._perturb_parameters(base_config, parameter_variance)
                
                # Create modified backtest job
                modified_job = await self._create_modified_backtest_job(
                    backtest_job, perturbed_config, f"MC_{sim_num}", db
                )
                
                # Run simulation
                sim_result = await self.backtesting_engine.run_backtest(modified_job, db)
                
                if sim_result['success']:
                    # Calculate performance metrics
                    performance = await self.performance_calculator.calculate_comprehensive_metrics(
                        modified_job.id, db
                    )
                    
                    simulation_results.append({
                        'simulation_number': sim_num,
                        'total_return': performance.return_metrics.get('total_return', 0),
                        'sharpe_ratio': performance.efficiency_metrics.get('sharpe_ratio', 0),
                        'max_drawdown': performance.drawdown_metrics.get('max_drawdown', 0),
                        'win_rate': performance.trade_metrics.get('win_rate', 0),
                        'parameters': perturbed_config
                    })
                else:
                    simulation_results.append({
                        'simulation_number': sim_num,
                        'total_return': -1.0,  # Failed simulation
                        'sharpe_ratio': -999,
                        'max_drawdown': 1.0,
                        'win_rate': 0,
                        'parameters': perturbed_config,
                        'failed': True
                    })
            
            # Calculate Monte Carlo statistics
            successful_sims = [s for s in simulation_results if not s.get('failed', False)]
            
            confidence_intervals = self._calculate_confidence_intervals(successful_sims)
            probability_metrics = self._calculate_probability_metrics(successful_sims)
            risk_metrics = self._calculate_monte_carlo_risk_metrics(successful_sims)
            robustness_score = self._calculate_robustness_score(successful_sims)
            
            result = MonteCarloResult(
                total_simulations=len(simulation_results),
                confidence_intervals=confidence_intervals,
                probability_metrics=probability_metrics,
                simulation_results=simulation_results,
                risk_metrics=risk_metrics,
                robustness_score=robustness_score
            )
            
            self.logger.info(f"Monte Carlo simulation completed: {len(successful_sims)} successful runs")
            return result
            
        except Exception as e:
            self.logger.error(f"Monte Carlo simulation failed: {str(e)}")
            raise
    
    async def run_cross_validation(self, backtest_job: BacktestJob,
                                 num_folds: int = 5,
                                 validation_method: str = "temporal",
                                 db: AsyncSession) -> CrossValidationResult:
        """
        Run cross-validation to assess out-of-sample performance.
        
        Args:
            num_folds: Number of cross-validation folds
            validation_method: 'temporal' or 'random'
        """
        try:
            self.logger.info(f"Starting {validation_method} cross-validation: {num_folds} folds")
            
            # Create fold divisions
            folds = self._create_cv_folds(backtest_job, num_folds, validation_method)
            
            fold_results = []
            
            for fold_num, (train_periods, test_periods) in enumerate(folds):
                self.logger.info(f"Processing fold {fold_num + 1}/{num_folds}")
                
                # Run training on all training periods
                train_result = await self._run_multi_period_backtest(
                    backtest_job, train_periods, f"CV_Train_{fold_num}", db
                )
                
                # Run testing on validation period
                test_result = await self._run_multi_period_backtest(
                    backtest_job, test_periods, f"CV_Test_{fold_num}", db
                )
                
                # Calculate fold performance
                fold_performance = await self._calculate_fold_performance(
                    train_result, test_result, fold_num
                )
                
                fold_results.append(fold_performance)
            
            # Calculate cross-validation statistics
            avg_performance = self._calculate_average_cv_performance(fold_results)
            performance_stability = self._calculate_cv_stability(fold_results)
            out_of_sample_degradation = self._calculate_oos_degradation(fold_results)
            overfitting_score = self._calculate_overfitting_score(fold_results)
            
            result = CrossValidationResult(
                total_folds=num_folds,
                avg_performance=avg_performance,
                performance_stability=performance_stability,
                fold_results=fold_results,
                out_of_sample_degradation=out_of_sample_degradation,
                overfitting_score=overfitting_score
            )
            
            self.logger.info(f"Cross-validation completed: {num_folds} folds")
            return result
            
        except Exception as e:
            self.logger.error(f"Cross-validation failed: {str(e)}")
            raise
    
    async def run_robustness_testing(self, backtest_job: BacktestJob,
                                   db: AsyncSession) -> Dict[str, Any]:
        """
        Comprehensive robustness testing combining multiple methodologies.
        """
        try:
            self.logger.info(f"Starting comprehensive robustness testing for: {backtest_job.id}")
            
            results = {}
            
            # 1. Walk-Forward Analysis
            try:
                wf_result = await self.run_walk_forward_analysis(
                    backtest_job, training_window_days=252, 
                    testing_window_days=63, step_size_days=21, db=db
                )
                results['walk_forward'] = {
                    'consistency_score': wf_result.consistency_score,
                    'profitable_windows_pct': wf_result.profitable_windows / wf_result.total_windows * 100,
                    'avg_return_per_window': wf_result.avg_return_per_window,
                    'return_stability': 1 / (1 + wf_result.std_return_per_window)
                }
            except Exception as e:
                results['walk_forward'] = {'error': str(e)}
            
            # 2. Monte Carlo Simulation
            try:
                mc_result = await self.run_monte_carlo_simulation(
                    backtest_job, num_simulations=500, parameter_variance=0.1, db=db
                )
                results['monte_carlo'] = {
                    'robustness_score': mc_result.robustness_score,
                    'success_rate': len([s for s in mc_result.simulation_results 
                                       if not s.get('failed', False)]) / len(mc_result.simulation_results) * 100,
                    'confidence_intervals': mc_result.confidence_intervals,
                    'probability_metrics': mc_result.probability_metrics
                }
            except Exception as e:
                results['monte_carlo'] = {'error': str(e)}
            
            # 3. Cross-Validation
            try:
                cv_result = await self.run_cross_validation(
                    backtest_job, num_folds=5, validation_method="temporal", db=db
                )
                results['cross_validation'] = {
                    'avg_performance': cv_result.avg_performance,
                    'performance_stability': cv_result.performance_stability,
                    'overfitting_score': cv_result.overfitting_score,
                    'out_of_sample_degradation': cv_result.out_of_sample_degradation
                }
            except Exception as e:
                results['cross_validation'] = {'error': str(e)}
            
            # 4. Overall Robustness Score
            overall_score = self._calculate_overall_robustness_score(results)
            results['overall_robustness_score'] = overall_score
            
            # 5. Recommendations
            recommendations = self._generate_robustness_recommendations(results)
            results['recommendations'] = recommendations
            
            self.logger.info(f"Robustness testing completed with score: {overall_score}")
            return results
            
        except Exception as e:
            self.logger.error(f"Robustness testing failed: {str(e)}")
            raise
    
    # Helper methods for Walk-Forward Analysis
    async def _run_window_backtest(self, base_job: BacktestJob, start_date: date, 
                                 end_date: date, name_suffix: str, 
                                 db: AsyncSession) -> Dict[str, Any]:
        """Run backtest for a specific time window."""
        try:
            # Create modified job for this window
            window_job = BacktestJob(
                user_id=base_job.user_id,
                strategy_id=base_job.strategy_id,
                dataset_id=base_job.dataset_id,
                name=f"{base_job.name}_{name_suffix}",
                description=f"Window analysis: {start_date} to {end_date}",
                methodology=base_job.methodology,
                start_date=start_date,
                end_date=end_date,
                initial_capital=base_job.initial_capital,
                commission_rate=base_job.commission_rate,
                slippage_rate=base_job.slippage_rate,
                position_sizing=base_job.position_sizing,
                position_sizing_config=base_job.position_sizing_config,
                max_position_size=base_job.max_position_size,
                stop_loss_pct=base_job.stop_loss_pct,
                take_profit_pct=base_job.take_profit_pct,
                backtest_config=base_job.backtest_config
            )
            
            db.add(window_job)
            await db.commit()
            await db.refresh(window_job)
            
            # Run backtest
            result = await self.backtesting_engine.run_backtest(window_job, db)
            
            if result['success']:
                # Calculate performance metrics
                performance = await self.performance_calculator.calculate_comprehensive_metrics(
                    window_job.id, db
                )
                return {
                    'success': True,
                    'job_id': str(window_job.id),
                    'performance': performance,
                    'final_metrics': result.get('final_metrics', {})
                }
            else:
                return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            self.logger.error(f"Window backtest failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _calculate_window_metrics(self, training_result: Dict[str, Any],
                                      testing_result: Dict[str, Any],
                                      window_number: int) -> Dict[str, Any]:
        """Calculate metrics for a walk-forward window."""
        try:
            training_return = 0.0
            testing_return = 0.0
            
            if training_result['success'] and training_result.get('performance'):
                training_return = training_result['performance'].return_metrics.get('total_return', 0)
            
            if testing_result['success'] and testing_result.get('performance'):
                testing_return = testing_result['performance'].return_metrics.get('total_return', 0)
                testing_sharpe = testing_result['performance'].efficiency_metrics.get('sharpe_ratio', 0)
                testing_drawdown = testing_result['performance'].drawdown_metrics.get('max_drawdown', 0)
            else:
                testing_sharpe = -999
                testing_drawdown = 1.0
            
            return {
                'window_number': window_number,
                'training_return': training_return,
                'testing_return': testing_return,
                'testing_sharpe': testing_sharpe,
                'testing_drawdown': testing_drawdown,
                'training_success': training_result['success'],
                'testing_success': testing_result['success'],
                'return_degradation': training_return - testing_return if training_result['success'] and testing_result['success'] else None
            }
            
        except Exception as e:
            self.logger.error(f"Window metrics calculation failed: {str(e)}")
            return {
                'window_number': window_number,
                'training_return': 0,
                'testing_return': 0,
                'testing_sharpe': -999,
                'testing_drawdown': 1.0,
                'training_success': False,
                'testing_success': False,
                'error': str(e)
            }
    
    def _calculate_walk_forward_overall_metrics(self, window_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate overall walk-forward metrics."""
        successful_windows = [w for w in window_results if w['testing_success']]
        
        if not successful_windows:
            return {'avg_return': 0, 'std_return': 0, 'min_return': 0, 'max_return': 0}
        
        testing_returns = [w['testing_return'] for w in successful_windows]
        
        return {
            'avg_return': float(np.mean(testing_returns)),
            'std_return': float(np.std(testing_returns)),
            'min_return': float(np.min(testing_returns)),
            'max_return': float(np.max(testing_returns)),
            'sharpe_ratio': float(np.mean([w['testing_sharpe'] for w in successful_windows if w['testing_sharpe'] > -900])),
            'success_rate': len(successful_windows) / len(window_results)
        }
    
    def _calculate_consistency_score(self, window_results: List[Dict[str, Any]]) -> float:
        """Calculate consistency score for walk-forward analysis."""
        successful_windows = [w for w in window_results if w['testing_success']]
        
        if len(successful_windows) < 3:
            return 0.0
        
        testing_returns = [w['testing_return'] for w in successful_windows]
        positive_ratio = sum(1 for r in testing_returns if r > 0) / len(testing_returns)
        return_stability = 1 / (1 + np.std(testing_returns))
        
        return (positive_ratio * 0.6 + return_stability * 0.4) * 100
    
    # Helper methods for Monte Carlo Simulation
    def _perturb_parameters(self, base_config: Dict[str, Any], variance: float) -> Dict[str, Any]:
        """Perturb strategy parameters for Monte Carlo simulation."""
        perturbed_config = base_config.copy()
        
        # Define parameters that can be perturbed
        perturbable_params = [
            'stop_loss_pct', 'take_profit_pct', 'max_position_size',
            'commission_rate', 'slippage_rate'
        ]
        
        for param in perturbable_params:
            if param in perturbed_config:
                original_value = perturbed_config[param]
                if isinstance(original_value, (int, float)) and original_value > 0:
                    # Apply random perturbation
                    multiplier = 1 + np.random.normal(0, variance)
                    multiplier = max(0.1, min(3.0, multiplier))  # Clamp multiplier
                    perturbed_config[param] = original_value * multiplier
        
        return perturbed_config
    
    async def _create_modified_backtest_job(self, base_job: BacktestJob, 
                                          modified_config: Dict[str, Any],
                                          name_suffix: str, 
                                          db: AsyncSession) -> BacktestJob:
        """Create a modified backtest job for Monte Carlo simulation."""
        modified_job = BacktestJob(
            user_id=base_job.user_id,
            strategy_id=base_job.strategy_id,
            dataset_id=base_job.dataset_id,
            name=f"{base_job.name}_{name_suffix}",
            description=f"Monte Carlo simulation: {name_suffix}",
            methodology=base_job.methodology,
            start_date=base_job.start_date,
            end_date=base_job.end_date,
            initial_capital=base_job.initial_capital,
            commission_rate=Decimal(str(modified_config.get('commission_rate', float(base_job.commission_rate)))),
            slippage_rate=Decimal(str(modified_config.get('slippage_rate', float(base_job.slippage_rate)))),
            position_sizing=base_job.position_sizing,
            position_sizing_config=base_job.position_sizing_config,
            max_position_size=Decimal(str(modified_config.get('max_position_size', float(base_job.max_position_size)))),
            stop_loss_pct=Decimal(str(modified_config.get('stop_loss_pct', float(base_job.stop_loss_pct)))) if base_job.stop_loss_pct else None,
            take_profit_pct=Decimal(str(modified_config.get('take_profit_pct', float(base_job.take_profit_pct)))) if base_job.take_profit_pct else None,
            backtest_config=modified_config
        )
        
        db.add(modified_job)
        await db.commit()
        await db.refresh(modified_job)
        
        return modified_job
    
    def _calculate_confidence_intervals(self, simulation_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate confidence intervals from Monte Carlo results."""
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
        confidence_intervals = {}
        
        for metric in metrics:
            values = [s[metric] for s in simulation_results if metric in s and not np.isnan(s[metric])]
            
            if values:
                confidence_intervals[metric] = {
                    '5th_percentile': float(np.percentile(values, 5)),
                    '25th_percentile': float(np.percentile(values, 25)),
                    '50th_percentile': float(np.percentile(values, 50)),
                    '75th_percentile': float(np.percentile(values, 75)),
                    '95th_percentile': float(np.percentile(values, 95)),
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values))
                }
        
        return confidence_intervals
    
    def _calculate_probability_metrics(self, simulation_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate probability-based metrics from Monte Carlo results."""
        returns = [s['total_return'] for s in simulation_results if 'total_return' in s]
        
        if not returns:
            return {}
        
        return {
            'probability_of_profit': sum(1 for r in returns if r > 0) / len(returns) * 100,
            'probability_of_loss': sum(1 for r in returns if r < 0) / len(returns) * 100,
            'probability_large_loss': sum(1 for r in returns if r < -0.2) / len(returns) * 100,
            'probability_large_gain': sum(1 for r in returns if r > 0.2) / len(returns) * 100,
            'expected_return': float(np.mean(returns)),
            'worst_case_5pct': float(np.percentile(returns, 5)),
            'best_case_95pct': float(np.percentile(returns, 95))
        }
    
    def _calculate_monte_carlo_risk_metrics(self, simulation_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate risk metrics from Monte Carlo simulation."""
        returns = [s['total_return'] for s in simulation_results if 'total_return' in s]
        drawdowns = [s['max_drawdown'] for s in simulation_results if 'max_drawdown' in s]
        
        if not returns:
            return {}
        
        return {
            'value_at_risk_95': float(np.percentile(returns, 5)) * -1,  # VaR as positive number
            'conditional_var_95': float(np.mean([r for r in returns if r <= np.percentile(returns, 5)])) * -1,
            'max_expected_drawdown': float(np.percentile(drawdowns, 95)) if drawdowns else 0,
            'return_volatility': float(np.std(returns)),
            'skewness': float(stats.skew(returns)),
            'kurtosis': float(stats.kurtosis(returns))
        }
    
    def _calculate_robustness_score(self, simulation_results: List[Dict[str, Any]]) -> float:
        """Calculate overall robustness score from Monte Carlo simulation."""
        returns = [s['total_return'] for s in simulation_results if 'total_return' in s]
        
        if not returns:
            return 0.0
        
        # Factors for robustness score
        profit_probability = sum(1 for r in returns if r > 0) / len(returns)
        return_stability = 1 / (1 + np.std(returns))
        positive_expectation = max(0, np.mean(returns))
        
        # Combined robustness score (0-100)
        robustness = (profit_probability * 0.4 + return_stability * 0.3 + positive_expectation * 0.3) * 100
        return min(100, max(0, robustness))
    
    # Helper methods for Cross-Validation
    def _create_cv_folds(self, backtest_job: BacktestJob, num_folds: int, 
                        validation_method: str) -> List[Tuple[List[Tuple[date, date]], List[Tuple[date, date]]]]:
        """Create cross-validation folds."""
        start_date = backtest_job.start_date
        end_date = backtest_job.end_date
        total_days = (end_date - start_date).days
        
        folds = []
        
        if validation_method == "temporal":
            # Time-based cross-validation
            fold_size = total_days // num_folds
            
            for i in range(num_folds):
                test_start = start_date + timedelta(days=i * fold_size)
                test_end = start_date + timedelta(days=(i + 1) * fold_size - 1)
                
                # Training periods are all other folds
                train_periods = []
                for j in range(num_folds):
                    if j != i:
                        train_start = start_date + timedelta(days=j * fold_size)
                        train_end = start_date + timedelta(days=(j + 1) * fold_size - 1)
                        train_periods.append((train_start, min(train_end, end_date)))
                
                test_periods = [(test_start, min(test_end, end_date))]
                folds.append((train_periods, test_periods))
        
        else:  # random validation
            # Random cross-validation (simplified)
            dates = [start_date + timedelta(days=x) for x in range(total_days)]
            random.shuffle(dates)
            
            fold_size = len(dates) // num_folds
            
            for i in range(num_folds):
                test_dates = dates[i * fold_size:(i + 1) * fold_size]
                train_dates = [d for d in dates if d not in test_dates]
                
                # Convert to periods (simplified)
                train_periods = [(min(train_dates), max(train_dates))] if train_dates else []
                test_periods = [(min(test_dates), max(test_dates))] if test_dates else []
                
                folds.append((train_periods, test_periods))
        
        return folds
    
    async def _run_multi_period_backtest(self, base_job: BacktestJob, 
                                       periods: List[Tuple[date, date]],
                                       name_suffix: str, db: AsyncSession) -> Dict[str, Any]:
        """Run backtest across multiple time periods."""
        try:
            if not periods:
                return {'success': False, 'error': 'No periods provided'}
            
            # For simplicity, use the first period (can be enhanced to combine periods)
            start_date, end_date = periods[0]
            
            return await self._run_window_backtest(base_job, start_date, end_date, name_suffix, db)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _calculate_fold_performance(self, train_result: Dict[str, Any],
                                        test_result: Dict[str, Any],
                                        fold_number: int) -> Dict[str, Any]:
        """Calculate performance metrics for a cross-validation fold."""
        try:
            train_return = 0.0
            test_return = 0.0
            train_sharpe = 0.0
            test_sharpe = 0.0
            
            if train_result['success'] and train_result.get('performance'):
                train_return = train_result['performance'].return_metrics.get('total_return', 0)
                train_sharpe = train_result['performance'].efficiency_metrics.get('sharpe_ratio', 0)
            
            if test_result['success'] and test_result.get('performance'):
                test_return = test_result['performance'].return_metrics.get('total_return', 0)
                test_sharpe = test_result['performance'].efficiency_metrics.get('sharpe_ratio', 0)
            
            return {
                'fold_number': fold_number,
                'train_return': train_return,
                'test_return': test_return,
                'train_sharpe': train_sharpe,
                'test_sharpe': test_sharpe,
                'return_degradation': train_return - test_return,
                'sharpe_degradation': train_sharpe - test_sharpe,
                'train_success': train_result['success'],
                'test_success': test_result['success']
            }
            
        except Exception as e:
            return {
                'fold_number': fold_number,
                'train_return': 0,
                'test_return': 0,
                'train_sharpe': 0,
                'test_sharpe': 0,
                'return_degradation': 0,
                'sharpe_degradation': 0,
                'train_success': False,
                'test_success': False,
                'error': str(e)
            }
    
    def _calculate_average_cv_performance(self, fold_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average performance across CV folds."""
        successful_folds = [f for f in fold_results if f['train_success'] and f['test_success']]
        
        if not successful_folds:
            return {}
        
        return {
            'avg_train_return': float(np.mean([f['train_return'] for f in successful_folds])),
            'avg_test_return': float(np.mean([f['test_return'] for f in successful_folds])),
            'avg_train_sharpe': float(np.mean([f['train_sharpe'] for f in successful_folds])),
            'avg_test_sharpe': float(np.mean([f['test_sharpe'] for f in successful_folds]))
        }
    
    def _calculate_cv_stability(self, fold_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate performance stability across CV folds."""
        successful_folds = [f for f in fold_results if f['train_success'] and f['test_success']]
        
        if not successful_folds:
            return {}
        
        test_returns = [f['test_return'] for f in successful_folds]
        test_sharpes = [f['test_sharpe'] for f in successful_folds]
        
        return {
            'return_std': float(np.std(test_returns)),
            'sharpe_std': float(np.std(test_sharpes)),
            'return_stability_score': 1 / (1 + np.std(test_returns)),
            'sharpe_stability_score': 1 / (1 + np.std(test_sharpes))
        }
    
    def _calculate_oos_degradation(self, fold_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate out-of-sample performance degradation."""
        successful_folds = [f for f in fold_results if f['train_success'] and f['test_success']]
        
        if not successful_folds:
            return {}
        
        return_degradations = [f['return_degradation'] for f in successful_folds]
        sharpe_degradations = [f['sharpe_degradation'] for f in successful_folds]
        
        return {
            'avg_return_degradation': float(np.mean(return_degradations)),
            'avg_sharpe_degradation': float(np.mean(sharpe_degradations)),
            'max_return_degradation': float(np.max(return_degradations)),
            'max_sharpe_degradation': float(np.max(sharpe_degradations))
        }
    
    def _calculate_overfitting_score(self, fold_results: List[Dict[str, Any]]) -> float:
        """Calculate overfitting score (0-100, higher means more overfitting)."""
        successful_folds = [f for f in fold_results if f['train_success'] and f['test_success']]
        
        if not successful_folds:
            return 100.0  # Maximum overfitting if no successful folds
        
        return_degradations = [f['return_degradation'] for f in successful_folds]
        avg_degradation = np.mean(return_degradations)
        
        # Overfitting score: higher degradation = more overfitting
        overfitting_score = min(100, max(0, avg_degradation * 200))  # Scale to 0-100
        return float(overfitting_score)
    
    # Overall robustness calculation
    def _calculate_overall_robustness_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall robustness score from all testing methods."""
        scores = []
        
        # Walk-forward consistency score
        if 'walk_forward' in results and 'consistency_score' in results['walk_forward']:
            scores.append(results['walk_forward']['consistency_score'])
        
        # Monte Carlo robustness score
        if 'monte_carlo' in results and 'robustness_score' in results['monte_carlo']:
            scores.append(results['monte_carlo']['robustness_score'])
        
        # Cross-validation score (inverse of overfitting)
        if 'cross_validation' in results and 'overfitting_score' in results['cross_validation']:
            cv_score = 100 - results['cross_validation']['overfitting_score']
            scores.append(cv_score)
        
        return float(np.mean(scores)) if scores else 0.0
    
    def _generate_robustness_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on robustness test results."""
        recommendations = []
        
        overall_score = results.get('overall_robustness_score', 0)
        
        if overall_score >= 80:
            recommendations.append("Strategy shows excellent robustness across multiple testing methodologies")
        elif overall_score >= 60:
            recommendations.append("Strategy shows good robustness but consider additional validation")
        elif overall_score >= 40:
            recommendations.append("Strategy shows moderate robustness - review parameters and consider optimization")
        else:
            recommendations.append("Strategy shows poor robustness - significant revision recommended")
        
        # Walk-forward specific recommendations
        if 'walk_forward' in results:
            wf = results['walk_forward']
            if wf.get('profitable_windows_pct', 0) < 60:
                recommendations.append("Low percentage of profitable windows in walk-forward analysis - strategy may not be consistently profitable")
            if wf.get('return_stability', 0) < 0.5:
                recommendations.append("High return volatility across walk-forward windows - consider risk management improvements")
        
        # Monte Carlo specific recommendations
        if 'monte_carlo' in results:
            mc = results['monte_carlo']
            if mc.get('success_rate', 0) < 80:
                recommendations.append("Low success rate in Monte Carlo simulation - strategy sensitive to parameter changes")
            
            prob_metrics = mc.get('probability_metrics', {})
            if prob_metrics.get('probability_of_profit', 0) < 60:
                recommendations.append("Low probability of profit in Monte Carlo analysis - review strategy logic")
        
        # Cross-validation specific recommendations
        if 'cross_validation' in results:
            cv = results['cross_validation']
            if cv.get('overfitting_score', 0) > 60:
                recommendations.append("High overfitting detected in cross-validation - simplify strategy or add regularization")
            
            oos_deg = cv.get('out_of_sample_degradation', {})
            if oos_deg.get('avg_return_degradation', 0) > 0.1:
                recommendations.append("Significant out-of-sample performance degradation - strategy may be overfit to historical data")
        
        return recommendations