"""
Backtesting Engine for Phase 5: Backtesting Engine.
Core backtesting functionality with trade simulation and execution.
"""

import logging
import asyncio
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import UUID, uuid4
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.backtesting import (
    BacktestJob, BacktestTrade, DailyReturn, PortfolioSnapshot,
    BacktestStatus, BacktestMethodology, TradeSide, OrderType, 
    ExitReason, PositionSizing
)
from app.models.strategy import Strategy
from app.models.dataset import Dataset
from app.core.config import get_settings


@dataclass
class Position:
    """Represents an open position in the portfolio."""
    symbol: str
    quantity: Decimal
    entry_price: Decimal
    entry_date: datetime
    entry_value: Decimal
    current_price: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    side: str
    strategy_context: Dict[str, Any]


@dataclass
class Signal:
    """Trading signal from strategy."""
    symbol: str
    side: str  # 'buy' or 'sell'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    target_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    context: Dict[str, Any] = None


@dataclass
class Order:
    """Order to be executed."""
    order_id: str
    symbol: str
    side: str
    quantity: Decimal
    order_type: str
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = "GTC"


class Portfolio:
    """Portfolio management for backtesting."""
    
    def __init__(self, initial_capital: Decimal, commission_rate: Decimal, 
                 slippage_rate: Decimal):
        self.initial_capital = initial_capital
        self.cash_balance = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.positions: Dict[str, Position] = {}
        self.total_value = initial_capital
        self.invested_amount = Decimal('0.0')
        self.total_commission = Decimal('0.0')
        self.total_slippage = Decimal('0.0')
        
    def get_portfolio_value(self, current_prices: Dict[str, Decimal]) -> Decimal:
        """Calculate current portfolio value."""
        position_value = Decimal('0.0')
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.current_price = current_prices[symbol]
                position.current_value = position.quantity * position.current_price
                position.unrealized_pnl = position.current_value - position.entry_value
                position_value += position.current_value
        
        self.invested_amount = position_value
        self.total_value = self.cash_balance + position_value
        return self.total_value
    
    def get_exposure_pct(self) -> Decimal:
        """Get current portfolio exposure percentage."""
        if self.total_value <= 0:
            return Decimal('0.0')
        return (self.invested_amount / self.total_value) * Decimal('100.0')
    
    def get_position_weight(self, symbol: str) -> Decimal:
        """Get position weight as percentage of portfolio."""
        if symbol not in self.positions or self.total_value <= 0:
            return Decimal('0.0')
        return (self.positions[symbol].current_value / self.total_value) * Decimal('100.0')


class PositionSizer:
    """Position sizing algorithms."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PositionSizer")
    
    def calculate_position_size(self, signal: Signal, portfolio: Portfolio, 
                              current_price: Decimal, sizing_method: str) -> Decimal:
        """Calculate position size based on sizing method."""
        try:
            if sizing_method == PositionSizing.FIXED_AMOUNT.value:
                return self._fixed_amount_sizing(signal, portfolio, current_price)
            elif sizing_method == PositionSizing.FIXED_PERCENTAGE.value:
                return self._fixed_percentage_sizing(signal, portfolio, current_price)
            elif sizing_method == PositionSizing.KELLY_CRITERION.value:
                return self._kelly_criterion_sizing(signal, portfolio, current_price)
            elif sizing_method == PositionSizing.RISK_PARITY.value:
                return self._risk_parity_sizing(signal, portfolio, current_price)
            elif sizing_method == PositionSizing.VOLATILITY_ADJUSTED.value:
                return self._volatility_adjusted_sizing(signal, portfolio, current_price)
            elif sizing_method == PositionSizing.OPTIMAL_F.value:
                return self._optimal_f_sizing(signal, portfolio, current_price)
            else:
                return self._fixed_percentage_sizing(signal, portfolio, current_price)
                
        except Exception as e:
            self.logger.error(f"Position sizing failed: {str(e)}")
            return Decimal('0.0')
    
    def _fixed_amount_sizing(self, signal: Signal, portfolio: Portfolio, 
                           current_price: Decimal) -> Decimal:
        """Fixed dollar amount per position."""
        fixed_amount = Decimal(str(self.config.get('fixed_amount', 1000.0)))
        if portfolio.cash_balance < fixed_amount:
            fixed_amount = portfolio.cash_balance * Decimal('0.95')  # Leave 5% cash
        return fixed_amount / current_price
    
    def _fixed_percentage_sizing(self, signal: Signal, portfolio: Portfolio, 
                               current_price: Decimal) -> Decimal:
        """Fixed percentage of portfolio per position."""
        percentage = Decimal(str(self.config.get('percentage', 0.1)))  # 10% default
        position_value = portfolio.total_value * percentage
        
        # Apply signal strength adjustment
        position_value *= Decimal(str(signal.strength))
        
        if position_value > portfolio.cash_balance:
            position_value = portfolio.cash_balance * Decimal('0.95')
            
        return position_value / current_price
    
    def _kelly_criterion_sizing(self, signal: Signal, portfolio: Portfolio, 
                              current_price: Decimal) -> Decimal:
        """Kelly Criterion position sizing."""
        # Simplified Kelly: f = (bp - q) / b
        # Where b = odds, p = win probability, q = loss probability
        win_prob = Decimal(str(signal.confidence))
        loss_prob = Decimal('1.0') - win_prob
        
        # Estimate odds from historical data or use signal strength
        odds = Decimal(str(self.config.get('expected_odds', 2.0)))
        
        kelly_fraction = (odds * win_prob - loss_prob) / odds
        kelly_fraction = max(Decimal('0.0'), min(kelly_fraction, Decimal('0.25')))  # Cap at 25%
        
        position_value = portfolio.total_value * kelly_fraction
        if position_value > portfolio.cash_balance:
            position_value = portfolio.cash_balance * Decimal('0.95')
            
        return position_value / current_price
    
    def _risk_parity_sizing(self, signal: Signal, portfolio: Portfolio, 
                          current_price: Decimal) -> Decimal:
        """Risk parity position sizing."""
        # Simplified risk parity based on volatility
        symbol_volatility = Decimal(str(self.config.get('symbol_volatility', {}).get(signal.symbol, 0.2)))
        target_risk = Decimal(str(self.config.get('target_risk_per_position', 0.02)))  # 2%
        
        # Position size = (Target Risk * Portfolio Value) / (Price * Volatility)
        risk_amount = portfolio.total_value * target_risk
        position_value = risk_amount / symbol_volatility
        
        if position_value > portfolio.cash_balance:
            position_value = portfolio.cash_balance * Decimal('0.95')
            
        return position_value / current_price
    
    def _volatility_adjusted_sizing(self, signal: Signal, portfolio: Portfolio, 
                                  current_price: Decimal) -> Decimal:
        """Volatility-adjusted position sizing."""
        base_percentage = Decimal(str(self.config.get('base_percentage', 0.1)))
        symbol_volatility = Decimal(str(self.config.get('symbol_volatility', {}).get(signal.symbol, 0.2)))
        target_volatility = Decimal(str(self.config.get('target_volatility', 0.15)))
        
        # Adjust position size inversely to volatility
        vol_adjustment = target_volatility / symbol_volatility
        adjusted_percentage = base_percentage * vol_adjustment
        adjusted_percentage = min(adjusted_percentage, Decimal('0.3'))  # Cap at 30%
        
        position_value = portfolio.total_value * adjusted_percentage
        if position_value > portfolio.cash_balance:
            position_value = portfolio.cash_balance * Decimal('0.95')
            
        return position_value / current_price
    
    def _optimal_f_sizing(self, signal: Signal, portfolio: Portfolio, 
                        current_price: Decimal) -> Decimal:
        """Optimal F position sizing."""
        # Simplified Optimal F calculation
        historical_returns = self.config.get('historical_returns', [])
        if not historical_returns:
            return self._fixed_percentage_sizing(signal, portfolio, current_price)
        
        # Calculate Optimal F fraction
        max_loss = min(historical_returns) if historical_returns else -0.1
        optimal_f = Decimal('0.1')  # Simplified calculation
        
        position_value = portfolio.total_value * optimal_f
        if position_value > portfolio.cash_balance:
            position_value = portfolio.cash_balance * Decimal('0.95')
            
        return position_value / current_price


class ExecutionEngine:
    """Trade execution simulation engine."""
    
    def __init__(self, commission_rate: Decimal, slippage_rate: Decimal, 
                 execution_delay_ms: int, price_improvement_pct: Decimal,
                 partial_fill_probability: Decimal):
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.execution_delay_ms = execution_delay_ms
        self.price_improvement_pct = price_improvement_pct
        self.partial_fill_probability = partial_fill_probability
        self.logger = logging.getLogger(f"{__name__}.ExecutionEngine")
    
    def execute_order(self, order: Order, current_price: Decimal, 
                     market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate order execution."""
        try:
            # Simulate execution delay
            fill_time_ms = self.execution_delay_ms + np.random.randint(-20, 21)
            
            # Determine if order gets partial fill
            partial_fill = np.random.random() < float(self.partial_fill_probability)
            fill_ratio = Decimal(str(np.random.uniform(0.7, 1.0))) if partial_fill else Decimal('1.0')
            
            # Calculate execution price with slippage
            execution_price = self._calculate_execution_price(
                order, current_price, market_data
            )
            
            # Calculate quantities and costs
            filled_quantity = order.quantity * fill_ratio
            trade_value = filled_quantity * execution_price
            commission = trade_value * self.commission_rate
            slippage_cost = self._calculate_slippage_cost(
                order, current_price, execution_price, filled_quantity
            )
            
            return {
                'success': True,
                'filled_quantity': filled_quantity,
                'execution_price': execution_price,
                'trade_value': trade_value,
                'commission': commission,
                'slippage': slippage_cost,
                'fill_time_ms': fill_time_ms,
                'partial_fill': partial_fill,
                'fill_ratio': fill_ratio
            }
            
        except Exception as e:
            self.logger.error(f"Order execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'rejected': True,
                'rejection_reason': f"Execution error: {str(e)}"
            }
    
    def _calculate_execution_price(self, order: Order, current_price: Decimal, 
                                 market_data: Dict[str, Any]) -> Decimal:
        """Calculate execution price with slippage and price improvement."""
        base_price = current_price
        
        # Apply slippage based on order side
        if order.side == TradeSide.BUY.value:
            slippage_adjustment = base_price * self.slippage_rate
        else:
            slippage_adjustment = -base_price * self.slippage_rate
        
        # Apply price improvement (sometimes market moves in our favor)
        price_improvement = Decimal('0.0')
        if np.random.random() < 0.3:  # 30% chance of price improvement
            improvement_factor = np.random.uniform(0, float(self.price_improvement_pct))
            if order.side == TradeSide.BUY.value:
                price_improvement = -base_price * Decimal(str(improvement_factor))
            else:
                price_improvement = base_price * Decimal(str(improvement_factor))
        
        execution_price = base_price + slippage_adjustment + price_improvement
        
        # Ensure price is positive
        return max(execution_price, Decimal('0.01'))
    
    def _calculate_slippage_cost(self, order: Order, expected_price: Decimal, 
                               execution_price: Decimal, quantity: Decimal) -> Decimal:
        """Calculate slippage cost."""
        price_diff = abs(execution_price - expected_price)
        return price_diff * quantity


class BacktestingEngine:
    """Main backtesting engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
    
    async def run_backtest(self, backtest_job: BacktestJob, db: AsyncSession) -> Dict[str, Any]:
        """Run a complete backtest."""
        try:
            self.logger.info(f"Starting backtest: {backtest_job.id}")
            
            # Update status to running
            await self._update_backtest_status(backtest_job.id, BacktestStatus.RUNNING, db)
            
            # Initialize backtest components
            portfolio = Portfolio(
                backtest_job.initial_capital,
                backtest_job.commission_rate,
                backtest_job.slippage_rate
            )
            
            position_sizer = PositionSizer(backtest_job.position_sizing_config)
            
            execution_engine = ExecutionEngine(
                backtest_job.commission_rate,
                backtest_job.slippage_rate,
                backtest_job.execution_delay_ms,
                backtest_job.price_improvement_pct,
                backtest_job.partial_fill_probability
            )
            
            # Load strategy and data
            strategy_data = await self._load_strategy_data(backtest_job, db)
            market_data = await self._load_market_data(backtest_job, db)
            
            if not strategy_data['success'] or not market_data['success']:
                await self._handle_backtest_error(
                    backtest_job.id, 
                    "Failed to load strategy or market data", 
                    db
                )
                return {'success': False, 'error': 'Data loading failed'}
            
            # Run backtest simulation
            simulation_result = await self._run_simulation(
                backtest_job, portfolio, position_sizer, execution_engine,
                strategy_data['data'], market_data['data'], db
            )
            
            if simulation_result['success']:
                # Calculate final metrics
                final_metrics = await self._calculate_final_metrics(
                    backtest_job.id, portfolio, db
                )
                
                # Update backtest job with results
                await self._update_backtest_results(
                    backtest_job.id, final_metrics, db
                )
                
                # Mark as completed
                await self._update_backtest_status(
                    backtest_job.id, BacktestStatus.COMPLETED, db
                )
                
                self.logger.info(f"Backtest completed successfully: {backtest_job.id}")
                return {
                    'success': True,
                    'backtest_id': str(backtest_job.id),
                    'final_metrics': final_metrics
                }
            else:
                await self._handle_backtest_error(
                    backtest_job.id, 
                    simulation_result.get('error', 'Simulation failed'), 
                    db
                )
                return simulation_result
                
        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}")
            await self._handle_backtest_error(backtest_job.id, str(e), db)
            return {'success': False, 'error': str(e)}
    
    async def _run_simulation(self, backtest_job: BacktestJob, portfolio: Portfolio,
                            position_sizer: PositionSizer, execution_engine: ExecutionEngine,
                            strategy_data: Dict[str, Any], market_data: Dict[str, Any],
                            db: AsyncSession) -> Dict[str, Any]:
        """Run the main backtest simulation loop."""
        try:
            trades_executed = 0
            current_date = backtest_job.start_date
            end_date = backtest_job.end_date
            
            # Track daily progress
            total_days = (end_date - current_date).days
            days_processed = 0
            
            while current_date <= end_date:
                # Get market data for current date
                daily_market_data = self._get_daily_market_data(market_data, current_date)
                
                if daily_market_data:
                    # Update portfolio value
                    current_prices = {symbol: Decimal(str(data['close'])) 
                                    for symbol, data in daily_market_data.items()}
                    portfolio.get_portfolio_value(current_prices)
                    
                    # Generate trading signals
                    signals = await self._generate_trading_signals(
                        strategy_data, daily_market_data, current_date
                    )
                    
                    # Process signals and execute trades
                    for signal in signals:
                        if signal.symbol in current_prices:
                            trade_result = await self._process_signal(
                                signal, portfolio, position_sizer, execution_engine,
                                current_prices[signal.symbol], backtest_job, 
                                current_date, db
                            )
                            
                            if trade_result['executed']:
                                trades_executed += 1
                    
                    # Check exit conditions for existing positions
                    await self._check_exit_conditions(
                        portfolio, execution_engine, current_prices,
                        backtest_job, current_date, db
                    )
                    
                    # Record daily performance
                    await self._record_daily_performance(
                        backtest_job.id, current_date, portfolio,
                        current_prices, db
                    )
                    
                    # Update progress
                    days_processed += 1
                    progress = int((days_processed / total_days) * 100)
                    if progress != backtest_job.progress_percentage:
                        await self._update_progress(backtest_job.id, progress, db)
                
                current_date += timedelta(days=1)
            
            return {
                'success': True,
                'trades_executed': trades_executed,
                'final_portfolio_value': portfolio.total_value
            }
            
        except Exception as e:
            self.logger.error(f"Simulation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _process_signal(self, signal: Signal, portfolio: Portfolio,
                            position_sizer: PositionSizer, execution_engine: ExecutionEngine,
                            current_price: Decimal, backtest_job: BacktestJob,
                            current_date: date, db: AsyncSession) -> Dict[str, Any]:
        """Process a trading signal and execute if appropriate."""
        try:
            # Calculate position size
            position_size = position_sizer.calculate_position_size(
                signal, portfolio, current_price, backtest_job.position_sizing
            )
            
            if position_size <= 0:
                return {'executed': False, 'reason': 'Zero position size'}
            
            # Create order
            order = Order(
                order_id=str(uuid4()),
                symbol=signal.symbol,
                side=signal.side,
                quantity=position_size,
                order_type=OrderType.MARKET.value
            )
            
            # Execute order
            execution_result = execution_engine.execute_order(
                order, current_price, {}
            )
            
            if execution_result['success']:
                # Record trade
                await self._record_trade(
                    backtest_job.id, signal, order, execution_result,
                    portfolio, current_date, db
                )
                
                # Update portfolio
                if signal.side == TradeSide.BUY.value:
                    await self._add_position(portfolio, signal, execution_result, current_date)
                else:
                    await self._close_position(portfolio, signal, execution_result)
                
                return {'executed': True, 'trade_id': order.order_id}
            else:
                return {'executed': False, 'reason': execution_result.get('error')}
                
        except Exception as e:
            self.logger.error(f"Signal processing failed: {str(e)}")
            return {'executed': False, 'reason': str(e)}
    
    async def _add_position(self, portfolio: Portfolio, signal: Signal,
                          execution_result: Dict[str, Any], entry_date: date):
        """Add new position to portfolio."""
        position = Position(
            symbol=signal.symbol,
            quantity=execution_result['filled_quantity'],
            entry_price=execution_result['execution_price'],
            entry_date=entry_date,
            entry_value=execution_result['trade_value'],
            current_price=execution_result['execution_price'],
            current_value=execution_result['trade_value'],
            unrealized_pnl=Decimal('0.0'),
            side=signal.side,
            strategy_context=signal.context or {}
        )
        
        portfolio.positions[signal.symbol] = position
        portfolio.cash_balance -= execution_result['trade_value']
        portfolio.cash_balance -= execution_result['commission']
        portfolio.total_commission += execution_result['commission']
        portfolio.total_slippage += execution_result['slippage']
    
    async def _close_position(self, portfolio: Portfolio, signal: Signal,
                            execution_result: Dict[str, Any]):
        """Close existing position."""
        if signal.symbol in portfolio.positions:
            position = portfolio.positions[signal.symbol]
            
            # Calculate PnL
            proceeds = execution_result['trade_value']
            commission = execution_result['commission']
            net_proceeds = proceeds - commission
            
            # Add proceeds to cash
            portfolio.cash_balance += net_proceeds
            portfolio.total_commission += commission
            portfolio.total_slippage += execution_result['slippage']
            
            # Remove position
            del portfolio.positions[signal.symbol]
    
    # Additional helper methods would continue here...
    # For brevity, I'll include the key method signatures and a few implementations
    
    async def _generate_trading_signals(self, strategy_data: Dict[str, Any],
                                      market_data: Dict[str, Any], 
                                      current_date: date) -> List[Signal]:
        """Generate trading signals from strategy."""
        # Placeholder implementation - would integrate with actual strategy logic
        signals = []
        
        # Simple example: random signals for demonstration
        symbols = list(market_data.keys())
        if symbols and np.random.random() < 0.1:  # 10% chance of signal
            symbol = np.random.choice(symbols)
            side = np.random.choice([TradeSide.BUY.value, TradeSide.SELL.value])
            
            signal = Signal(
                symbol=symbol,
                side=side,
                strength=np.random.uniform(0.5, 1.0),
                confidence=np.random.uniform(0.6, 0.9),
                context={'date': current_date.isoformat()}
            )
            signals.append(signal)
        
        return signals
    
    async def _check_exit_conditions(self, portfolio: Portfolio, 
                                   execution_engine: ExecutionEngine,
                                   current_prices: Dict[str, Decimal],
                                   backtest_job: BacktestJob, current_date: date,
                                   db: AsyncSession):
        """Check exit conditions for open positions."""
        positions_to_close = []
        
        for symbol, position in portfolio.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position.current_price = current_price
                position.current_value = position.quantity * current_price
                position.unrealized_pnl = position.current_value - position.entry_value
                
                # Check stop loss
                if backtest_job.stop_loss_pct:
                    loss_pct = (position.unrealized_pnl / position.entry_value) * Decimal('100.0')
                    if loss_pct <= -backtest_job.stop_loss_pct:
                        positions_to_close.append((symbol, ExitReason.STOP_LOSS.value))
                
                # Check take profit
                if backtest_job.take_profit_pct:
                    profit_pct = (position.unrealized_pnl / position.entry_value) * Decimal('100.0')
                    if profit_pct >= backtest_job.take_profit_pct:
                        positions_to_close.append((symbol, ExitReason.TAKE_PROFIT.value))
        
        # Execute exit orders
        for symbol, exit_reason in positions_to_close:
            await self._exit_position(
                portfolio, symbol, exit_reason, execution_engine,
                current_prices[symbol], backtest_job, current_date, db
            )
    
    async def _exit_position(self, portfolio: Portfolio, symbol: str, 
                           exit_reason: str, execution_engine: ExecutionEngine,
                           current_price: Decimal, backtest_job: BacktestJob,
                           current_date: date, db: AsyncSession):
        """Exit a position."""
        if symbol not in portfolio.positions:
            return
        
        position = portfolio.positions[symbol]
        
        # Create exit order
        order = Order(
            order_id=str(uuid4()),
            symbol=symbol,
            side=TradeSide.SELL.value if position.side == TradeSide.BUY.value else TradeSide.BUY.value,
            quantity=position.quantity,
            order_type=OrderType.MARKET.value
        )
        
        # Execute exit order
        execution_result = execution_engine.execute_order(order, current_price, {})
        
        if execution_result['success']:
            # Record exit trade
            await self._record_exit_trade(
                backtest_job.id, position, order, execution_result,
                exit_reason, current_date, db
            )
            
            # Update portfolio
            await self._close_position(portfolio, 
                Signal(symbol=symbol, side=order.side, strength=1.0, confidence=1.0),
                execution_result
            )
    
    async def _load_strategy_data(self, backtest_job: BacktestJob, 
                                db: AsyncSession) -> Dict[str, Any]:
        """Load strategy data for backtesting."""
        try:
            result = await db.execute(
                select(Strategy).where(Strategy.id == backtest_job.strategy_id)
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return {'success': False, 'error': 'Strategy not found'}
            
            return {
                'success': True,
                'data': {
                    'strategy_id': str(strategy.id),
                    'name': strategy.name,
                    'config': strategy.strategy_config,
                    'parameters': strategy.parameters
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load strategy data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _load_market_data(self, backtest_job: BacktestJob, 
                              db: AsyncSession) -> Dict[str, Any]:
        """Load market data for backtesting."""
        try:
            result = await db.execute(
                select(Dataset).where(Dataset.id == backtest_job.dataset_id)
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {'success': False, 'error': 'Dataset not found'}
            
            # Simulate market data loading
            # In real implementation, this would load actual market data
            data = self._generate_sample_market_data(
                backtest_job.start_date, backtest_job.end_date
            )
            
            return {'success': True, 'data': data}
            
        except Exception as e:
            self.logger.error(f"Failed to load market data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_sample_market_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate sample market data for testing."""
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
        data = {}
        
        current_date = start_date
        base_prices = {'AAPL': 150.0, 'GOOGL': 2500.0, 'MSFT': 300.0, 'AMZN': 3000.0, 'TSLA': 800.0}
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            data[date_str] = {}
            
            for symbol in symbols:
                # Generate random price movement
                price_change = np.random.normal(0, 0.02)  # 2% daily volatility
                base_prices[symbol] *= (1 + price_change)
                
                data[date_str][symbol] = {
                    'open': base_prices[symbol] * (1 + np.random.normal(0, 0.005)),
                    'high': base_prices[symbol] * (1 + abs(np.random.normal(0, 0.01))),
                    'low': base_prices[symbol] * (1 - abs(np.random.normal(0, 0.01))),
                    'close': base_prices[symbol],
                    'volume': np.random.randint(1000000, 10000000)
                }
            
            current_date += timedelta(days=1)
        
        return data
    
    def _get_daily_market_data(self, market_data: Dict[str, Any], 
                             current_date: date) -> Dict[str, Any]:
        """Get market data for a specific date."""
        date_str = current_date.isoformat()
        return market_data.get(date_str, {})
    
    async def _record_trade(self, backtest_job_id: UUID, signal: Signal, 
                          order: Order, execution_result: Dict[str, Any],
                          portfolio: Portfolio, trade_date: date, 
                          db: AsyncSession):
        """Record a trade in the database."""
        try:
            trade = BacktestTrade(
                backtest_job_id=backtest_job_id,
                trade_id=order.order_id,
                symbol=signal.symbol,
                side=signal.side,
                entry_date=datetime.combine(trade_date, datetime.min.time()),
                entry_price=execution_result['execution_price'],
                entry_quantity=execution_result['filled_quantity'],
                entry_value=execution_result['trade_value'],
                entry_commission=execution_result['commission'],
                entry_slippage=execution_result['slippage'],
                entry_order_type=order.order_type,
                portfolio_value_at_entry=portfolio.total_value,
                position_size_pct=(execution_result['trade_value'] / portfolio.total_value) * Decimal('100.0'),
                signal_strength=Decimal(str(signal.strength)),
                confidence_score=Decimal(str(signal.confidence)),
                strategy_context=signal.context or {},
                fill_time_ms=execution_result['fill_time_ms'],
                partial_fill=execution_result['partial_fill']
            )
            
            db.add(trade)
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to record trade: {str(e)}")
            await db.rollback()
    
    async def _record_exit_trade(self, backtest_job_id: UUID, position: Position,
                               order: Order, execution_result: Dict[str, Any],
                               exit_reason: str, exit_date: date, db: AsyncSession):
        """Record trade exit details."""
        try:
            # Find the entry trade
            result = await db.execute(
                select(BacktestTrade).where(
                    and_(
                        BacktestTrade.backtest_job_id == backtest_job_id,
                        BacktestTrade.symbol == position.symbol,
                        BacktestTrade.exit_date.is_(None)
                    )
                )
            )
            trade = result.scalar_one_or_none()
            
            if trade:
                # Update with exit details
                trade.exit_date = datetime.combine(exit_date, datetime.min.time())
                trade.exit_price = execution_result['execution_price']
                trade.exit_quantity = execution_result['filled_quantity']
                trade.exit_value = execution_result['trade_value']
                trade.exit_commission = execution_result['commission']
                trade.exit_slippage = execution_result['slippage']
                trade.exit_order_type = order.order_type
                trade.exit_reason = exit_reason
                
                # Calculate PnL
                gross_pnl = trade.exit_value - trade.entry_value
                total_commission = trade.entry_commission + trade.exit_commission
                trade.pnl = gross_pnl - total_commission
                trade.pnl_pct = (trade.pnl / trade.entry_value) * Decimal('100.0')
                
                # Calculate holding period
                holding_period = (trade.exit_date - trade.entry_date).days
                trade.holding_period_days = holding_period
                
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to record trade exit: {str(e)}")
            await db.rollback()
    
    async def _record_daily_performance(self, backtest_job_id: UUID, 
                                      current_date: date, portfolio: Portfolio,
                                      current_prices: Dict[str, Decimal], 
                                      db: AsyncSession):
        """Record daily portfolio performance."""
        try:
            # Calculate returns
            portfolio_value = portfolio.get_portfolio_value(current_prices)
            
            # Get previous day's value for return calculation
            previous_result = await db.execute(
                select(DailyReturn).where(
                    DailyReturn.backtest_job_id == backtest_job_id
                ).order_by(DailyReturn.date.desc()).limit(1)
            )
            previous_daily = previous_result.scalar_one_or_none()
            
            daily_return = Decimal('0.0')
            daily_return_pct = Decimal('0.0')
            cumulative_return = portfolio_value - portfolio.initial_capital
            cumulative_return_pct = (cumulative_return / portfolio.initial_capital) * Decimal('100.0')
            
            if previous_daily:
                daily_return = portfolio_value - previous_daily.portfolio_value
                daily_return_pct = (daily_return / previous_daily.portfolio_value) * Decimal('100.0')
            
            daily_record = DailyReturn(
                backtest_job_id=backtest_job_id,
                date=current_date,
                portfolio_value=portfolio_value,
                cash_balance=portfolio.cash_balance,
                invested_amount=portfolio.invested_amount,
                daily_return=daily_return,
                daily_return_pct=daily_return_pct,
                cumulative_return=cumulative_return,
                cumulative_return_pct=cumulative_return_pct,
                positions_count=len(portfolio.positions),
                exposure_pct=portfolio.get_exposure_pct(),
                commission_paid=portfolio.total_commission
            )
            
            db.add(daily_record)
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to record daily performance: {str(e)}")
            await db.rollback()
    
    async def _calculate_final_metrics(self, backtest_job_id: UUID, 
                                     portfolio: Portfolio, db: AsyncSession) -> Dict[str, Any]:
        """Calculate final backtest performance metrics."""
        try:
            # Get all daily returns
            result = await db.execute(
                select(DailyReturn).where(
                    DailyReturn.backtest_job_id == backtest_job_id
                ).order_by(DailyReturn.date)
            )
            daily_returns = result.scalars().all()
            
            # Get all trades
            trades_result = await db.execute(
                select(BacktestTrade).where(
                    BacktestTrade.backtest_job_id == backtest_job_id
                )
            )
            trades = trades_result.scalars().all()
            
            if not daily_returns:
                return {}
            
            # Calculate key metrics
            returns = [float(dr.daily_return_pct) for dr in daily_returns if dr.daily_return_pct]
            
            total_return = portfolio.total_value - portfolio.initial_capital
            total_return_pct = (total_return / portfolio.initial_capital) * Decimal('100.0')
            
            # Calculate Sharpe ratio (simplified)
            returns_array = np.array(returns) if returns else np.array([0])
            sharpe_ratio = np.mean(returns_array) / np.std(returns_array) * np.sqrt(252) if np.std(returns_array) > 0 else 0
            
            # Calculate max drawdown
            portfolio_values = [float(dr.portfolio_value) for dr in daily_returns]
            peak = portfolio_values[0]
            max_drawdown = 0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            # Trade statistics
            completed_trades = [t for t in trades if t.exit_date is not None]
            winning_trades = [t for t in completed_trades if t.pnl > 0]
            losing_trades = [t for t in completed_trades if t.pnl <= 0]
            
            win_rate = len(winning_trades) / len(completed_trades) if completed_trades else 0
            
            return {
                'total_return': float(total_return),
                'total_return_pct': float(total_return_pct),
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': len(completed_trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'final_portfolio_value': float(portfolio.total_value)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate final metrics: {str(e)}")
            return {}
    
    # Status and error handling methods
    async def _update_backtest_status(self, backtest_job_id: UUID, 
                                    status: BacktestStatus, db: AsyncSession):
        """Update backtest status."""
        try:
            await db.execute(
                update(BacktestJob)
                .where(BacktestJob.id == backtest_job_id)
                .values(status=status.value, updated_at=func.now())
            )
            await db.commit()
        except Exception as e:
            self.logger.error(f"Failed to update backtest status: {str(e)}")
            await db.rollback()
    
    async def _update_progress(self, backtest_job_id: UUID, progress: int, 
                             db: AsyncSession):
        """Update backtest progress."""
        try:
            await db.execute(
                update(BacktestJob)
                .where(BacktestJob.id == backtest_job_id)
                .values(progress_percentage=progress, updated_at=func.now())
            )
            await db.commit()
        except Exception as e:
            self.logger.error(f"Failed to update progress: {str(e)}")
            await db.rollback()
    
    async def _update_backtest_results(self, backtest_job_id: UUID, 
                                     metrics: Dict[str, Any], db: AsyncSession):
        """Update backtest with final results."""
        try:
            await db.execute(
                update(BacktestJob)
                .where(BacktestJob.id == backtest_job_id)
                .values(
                    total_trades=metrics.get('total_trades', 0),
                    winning_trades=metrics.get('winning_trades', 0),
                    losing_trades=metrics.get('losing_trades', 0),
                    total_return=Decimal(str(metrics.get('total_return', 0))),
                    total_return_pct=Decimal(str(metrics.get('total_return_pct', 0))),
                    sharpe_ratio=Decimal(str(metrics.get('sharpe_ratio', 0))),
                    max_drawdown=Decimal(str(metrics.get('max_drawdown', 0))),
                    win_rate=Decimal(str(metrics.get('win_rate', 0))),
                    end_time=func.now(),
                    updated_at=func.now()
                )
            )
            await db.commit()
        except Exception as e:
            self.logger.error(f"Failed to update backtest results: {str(e)}")
            await db.rollback()
    
    async def _handle_backtest_error(self, backtest_job_id: UUID, error_message: str, 
                                   db: AsyncSession):
        """Handle backtest errors."""
        try:
            await db.execute(
                update(BacktestJob)
                .where(BacktestJob.id == backtest_job_id)
                .values(
                    status=BacktestStatus.FAILED.value,
                    error_details=error_message,
                    end_time=func.now(),
                    updated_at=func.now()
                )
            )
            await db.commit()
        except Exception as e:
            self.logger.error(f"Failed to handle backtest error: {str(e)}")
            await db.rollback()