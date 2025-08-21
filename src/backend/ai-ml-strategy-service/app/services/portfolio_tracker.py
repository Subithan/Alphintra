"""
Portfolio tracking and P&L calculation service for paper trading.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.paper_trading import (
    PaperTradingSession,
    PaperPosition,
    PaperTransaction,
    PaperPortfolioSnapshot
)
from app.services.market_data_service import market_data_service
from app.database.connection import get_db_session


@dataclass
class PositionSummary:
    """Position summary data."""
    symbol: str
    quantity: Decimal
    side: str
    avg_price: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    day_pnl: Decimal
    day_pnl_pct: Decimal


@dataclass
class PortfolioSummary:
    """Portfolio summary data."""
    session_id: int
    total_value: Decimal
    cash_balance: Decimal
    positions_value: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    day_pnl: Decimal
    day_pnl_pct: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    num_positions: int
    leverage: Decimal
    positions: List[PositionSummary]


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics."""
    total_return: Decimal
    total_return_pct: Decimal
    annualized_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    max_drawdown_pct: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    largest_win: Decimal
    largest_loss: Decimal


class PortfolioTracker:
    """Portfolio tracking and P&L calculation service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.position_cache: Dict[int, Dict[str, PositionSummary]] = {}
        self.portfolio_cache: Dict[int, PortfolioSummary] = {}
        self.tracking_active = False
        
        # Performance calculation settings
        self.risk_free_rate = Decimal("0.02")  # 2% annual risk-free rate
        self.trading_days_per_year = 252
        
    async def initialize(self) -> None:
        """Initialize the portfolio tracker."""
        
        # Load active sessions
        await self._load_active_sessions()
        
        # Start real-time tracking
        if not self.tracking_active:
            self.tracking_active = True
            asyncio.create_task(self._portfolio_tracking_loop())
        
        self.logger.info("Portfolio tracker initialized")
    
    async def _load_active_sessions(self) -> None:
        """Load active trading sessions."""
        
        try:
            with get_db_session() as db:
                active_sessions = db.query(PaperTradingSession).filter(
                    PaperTradingSession.is_active == True
                ).all()
                
                for session in active_sessions:
                    await self._load_session_positions(session.id)
                
            self.logger.info(f"Loaded {len(active_sessions)} active sessions")
            
        except Exception as e:
            self.logger.error(f"Error loading active sessions: {e}")
    
    async def _load_session_positions(self, session_id: int) -> None:
        """Load positions for a trading session."""
        
        try:
            with get_db_session() as db:
                positions = db.query(PaperPosition).filter(
                    and_(
                        PaperPosition.session_id == session_id,
                        PaperPosition.is_open == True
                    )
                ).all()
                
                session_positions = {}
                for position in positions:
                    # Update position with current market data
                    await self._update_position_value(position)
                    
                    position_summary = PositionSummary(
                        symbol=position.symbol,
                        quantity=position.quantity,
                        side=position.side,
                        avg_price=position.avg_price,
                        current_price=position.current_price,
                        market_value=position.market_value,
                        cost_basis=position.total_cost,
                        unrealized_pnl=position.unrealized_pnl,
                        unrealized_pnl_pct=position.unrealized_pnl_pct,
                        day_pnl=Decimal("0"),  # Will be calculated
                        day_pnl_pct=Decimal("0")
                    )
                    
                    session_positions[position.symbol] = position_summary
                
                self.position_cache[session_id] = session_positions
                
        except Exception as e:
            self.logger.error(f"Error loading positions for session {session_id}: {e}")
    
    async def _portfolio_tracking_loop(self) -> None:
        """Main portfolio tracking loop."""
        
        while self.tracking_active:
            try:
                # Update all cached portfolios
                for session_id in list(self.position_cache.keys()):
                    await self._update_portfolio_values(session_id)
                
                # Create periodic snapshots
                await self._create_portfolio_snapshots()
                
                await asyncio.sleep(5.0)  # Update every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in portfolio tracking loop: {e}")
                await asyncio.sleep(10.0)
    
    async def _update_portfolio_values(self, session_id: int) -> None:
        """Update portfolio values for a session."""
        
        try:
            # Update all position values
            if session_id in self.position_cache:
                for symbol, position in self.position_cache[session_id].items():
                    await self._update_position_market_value(position)
            
            # Calculate portfolio summary
            portfolio_summary = await self._calculate_portfolio_summary(session_id)
            self.portfolio_cache[session_id] = portfolio_summary
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio values for session {session_id}: {e}")
    
    async def _update_position_value(self, position: PaperPosition) -> None:
        """Update position value with current market data."""
        
        try:
            current_price = await market_data_service.get_current_price(position.symbol)
            if current_price:
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                
                # Calculate unrealized P&L
                if position.side == "long":
                    position.unrealized_pnl = position.market_value - position.total_cost
                else:
                    position.unrealized_pnl = position.total_cost - position.market_value
                
                if position.total_cost > 0:
                    position.unrealized_pnl_pct = (position.unrealized_pnl / position.total_cost) * 100
                else:
                    position.unrealized_pnl_pct = Decimal("0")
        
        except Exception as e:
            self.logger.error(f"Error updating position value for {position.symbol}: {e}")
    
    async def _update_position_market_value(self, position: PositionSummary) -> None:
        """Update position market value."""
        
        try:
            current_price = await market_data_service.get_current_price(position.symbol)
            if current_price:
                old_market_value = position.market_value
                
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                
                # Calculate unrealized P&L
                if position.side == "long":
                    position.unrealized_pnl = position.market_value - position.cost_basis
                else:
                    position.unrealized_pnl = position.cost_basis - position.market_value
                
                if position.cost_basis > 0:
                    position.unrealized_pnl_pct = (position.unrealized_pnl / position.cost_basis) * 100
                else:
                    position.unrealized_pnl_pct = Decimal("0")
                
                # Calculate day P&L (change since last update)
                position.day_pnl = position.market_value - old_market_value
                if old_market_value > 0:
                    position.day_pnl_pct = (position.day_pnl / old_market_value) * 100
                else:
                    position.day_pnl_pct = Decimal("0")
        
        except Exception as e:
            self.logger.error(f"Error updating market value for {position.symbol}: {e}")
    
    async def _calculate_portfolio_summary(self, session_id: int) -> PortfolioSummary:
        """Calculate portfolio summary."""
        
        try:
            # Get session data
            with get_db_session() as db:
                session = db.query(PaperTradingSession).filter(
                    PaperTradingSession.id == session_id
                ).first()
                
                if not session:
                    raise ValueError(f"Session {session_id} not found")
            
            # Calculate position values
            positions = list(self.position_cache.get(session_id, {}).values())
            positions_value = sum(pos.market_value for pos in positions)
            unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
            day_pnl = sum(pos.day_pnl for pos in positions)
            
            # Get cash balance (need to calculate from transactions)
            cash_balance = await self._calculate_cash_balance(session_id)
            
            # Calculate total portfolio value
            total_value = cash_balance + positions_value
            
            # Calculate total P&L
            total_pnl = total_value - session.initial_capital
            total_pnl_pct = (total_pnl / session.initial_capital) * 100 if session.initial_capital > 0 else Decimal("0")
            
            # Calculate day P&L percentage
            previous_value = total_value - day_pnl
            day_pnl_pct = (day_pnl / previous_value) * 100 if previous_value > 0 else Decimal("0")
            
            # Get realized P&L from closed positions
            realized_pnl = await self._calculate_realized_pnl(session_id)
            
            # Calculate leverage
            leverage = positions_value / total_value if total_value > 0 else Decimal("0")
            
            return PortfolioSummary(
                session_id=session_id,
                total_value=total_value,
                cash_balance=cash_balance,
                positions_value=positions_value,
                total_pnl=total_pnl,
                total_pnl_pct=total_pnl_pct,
                day_pnl=day_pnl,
                day_pnl_pct=day_pnl_pct,
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl,
                num_positions=len(positions),
                leverage=leverage,
                positions=positions
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio summary for session {session_id}: {e}")
            return PortfolioSummary(
                session_id=session_id,
                total_value=Decimal("0"),
                cash_balance=Decimal("0"),
                positions_value=Decimal("0"),
                total_pnl=Decimal("0"),
                total_pnl_pct=Decimal("0"),
                day_pnl=Decimal("0"),
                day_pnl_pct=Decimal("0"),
                realized_pnl=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                num_positions=0,
                leverage=Decimal("0"),
                positions=[]
            )
    
    async def _calculate_cash_balance(self, session_id: int) -> Decimal:
        """Calculate current cash balance from transactions."""
        
        try:
            with get_db_session() as db:
                # Get initial capital
                session = db.query(PaperTradingSession).filter(
                    PaperTradingSession.id == session_id
                ).first()
                
                if not session:
                    return Decimal("0")
                
                # Calculate net cash flow from all transactions
                cash_flows = db.query(func.sum(PaperTransaction.cash_flow)).filter(
                    PaperTransaction.session_id == session_id
                ).scalar()
                
                total_cash_flow = cash_flows or Decimal("0")
                return session.initial_capital + total_cash_flow
                
        except Exception as e:
            self.logger.error(f"Error calculating cash balance for session {session_id}: {e}")
            return Decimal("0")
    
    async def _calculate_realized_pnl(self, session_id: int) -> Decimal:
        """Calculate realized P&L from closed positions."""
        
        try:
            with get_db_session() as db:
                realized_pnl = db.query(func.sum(PaperPosition.realized_pnl)).filter(
                    and_(
                        PaperPosition.session_id == session_id,
                        PaperPosition.is_open == False
                    )
                ).scalar()
                
                return realized_pnl or Decimal("0")
                
        except Exception as e:
            self.logger.error(f"Error calculating realized P&L for session {session_id}: {e}")
            return Decimal("0")
    
    async def _create_portfolio_snapshots(self) -> None:
        """Create periodic portfolio snapshots."""
        
        try:
            current_time = datetime.utcnow()
            
            # Create snapshots every minute
            for session_id, portfolio in self.portfolio_cache.items():
                # Check if we need to create a snapshot
                with get_db_session() as db:
                    last_snapshot = db.query(PaperPortfolioSnapshot).filter(
                        PaperPortfolioSnapshot.session_id == session_id
                    ).order_by(desc(PaperPortfolioSnapshot.timestamp)).first()
                    
                    # Create snapshot if none exists or last one is older than 1 minute
                    should_create = True
                    if last_snapshot:
                        time_diff = current_time - last_snapshot.timestamp
                        should_create = time_diff.total_seconds() >= 60
                    
                    if should_create:
                        # Calculate additional metrics
                        performance_metrics = await self._calculate_performance_metrics(session_id)
                        
                        snapshot = PaperPortfolioSnapshot(
                            session_id=session_id,
                            timestamp=current_time,
                            cash_balance=portfolio.cash_balance,
                            market_value=portfolio.positions_value,
                            total_value=portfolio.total_value,
                            total_return=portfolio.total_pnl,
                            total_return_pct=portfolio.total_pnl_pct,
                            daily_return=portfolio.day_pnl,
                            daily_return_pct=portfolio.day_pnl_pct,
                            drawdown=performance_metrics.max_drawdown if performance_metrics else None,
                            drawdown_pct=performance_metrics.max_drawdown_pct if performance_metrics else None,
                            volatility=performance_metrics.volatility if performance_metrics else None,
                            sharpe_ratio=performance_metrics.sharpe_ratio if performance_metrics else None,
                            num_positions=portfolio.num_positions,
                            leverage=portfolio.leverage
                        )
                        
                        db.add(snapshot)
                        db.commit()
                        
        except Exception as e:
            self.logger.error(f"Error creating portfolio snapshots: {e}")
    
    async def _calculate_performance_metrics(self, session_id: int) -> Optional[PerformanceMetrics]:
        """Calculate comprehensive performance metrics."""
        
        try:
            with get_db_session() as db:
                # Get session
                session = db.query(PaperTradingSession).filter(
                    PaperTradingSession.id == session_id
                ).first()
                
                if not session:
                    return None
                
                # Get portfolio snapshots for calculations
                snapshots = db.query(PaperPortfolioSnapshot).filter(
                    PaperPortfolioSnapshot.session_id == session_id
                ).order_by(PaperPortfolioSnapshot.timestamp).all()
                
                if len(snapshots) < 2:
                    return None
                
                # Calculate returns series
                returns = []
                portfolio_values = [float(snapshot.total_value) for snapshot in snapshots]
                
                for i in range(1, len(portfolio_values)):
                    if portfolio_values[i-1] > 0:
                        daily_return = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                        returns.append(daily_return)
                
                if not returns:
                    return None
                
                # Calculate basic metrics
                total_return = portfolio_values[-1] - float(session.initial_capital)
                total_return_pct = (total_return / float(session.initial_capital)) * 100
                
                # Calculate annualized return
                days_elapsed = (snapshots[-1].timestamp - snapshots[0].timestamp).days
                if days_elapsed > 0:
                    annualized_return = ((portfolio_values[-1] / portfolio_values[0]) ** (365.0 / days_elapsed) - 1) * 100
                else:
                    annualized_return = 0.0
                
                # Calculate volatility (annualized)
                if len(returns) > 1:
                    import statistics
                    import math
                    daily_vol = statistics.stdev(returns)
                    volatility = daily_vol * math.sqrt(self.trading_days_per_year) * 100
                else:
                    volatility = 0.0
                
                # Calculate Sharpe ratio
                if volatility > 0:
                    excess_return = annualized_return - float(self.risk_free_rate) * 100
                    sharpe_ratio = excess_return / volatility
                else:
                    sharpe_ratio = 0.0
                
                # Calculate maximum drawdown
                peak = portfolio_values[0]
                max_drawdown = 0.0
                max_drawdown_pct = 0.0
                
                for value in portfolio_values:
                    if value > peak:
                        peak = value
                    drawdown = peak - value
                    drawdown_pct = (drawdown / peak) * 100 if peak > 0 else 0.0
                    
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                        max_drawdown_pct = drawdown_pct
                
                # Calculate trade statistics
                closed_positions = db.query(PaperPosition).filter(
                    and_(
                        PaperPosition.session_id == session_id,
                        PaperPosition.is_open == False
                    )
                ).all()
                
                winning_trades = [pos for pos in closed_positions if pos.realized_pnl > 0]
                losing_trades = [pos for pos in closed_positions if pos.realized_pnl < 0]
                
                win_rate = (len(winning_trades) / len(closed_positions)) * 100 if closed_positions else 0.0
                
                avg_win = sum(float(pos.realized_pnl) for pos in winning_trades) / len(winning_trades) if winning_trades else 0.0
                avg_loss = sum(float(pos.realized_pnl) for pos in losing_trades) / len(losing_trades) if losing_trades else 0.0
                
                largest_win = max((float(pos.realized_pnl) for pos in winning_trades), default=0.0)
                largest_loss = min((float(pos.realized_pnl) for pos in losing_trades), default=0.0)
                
                # Calculate profit factor
                total_wins = sum(float(pos.realized_pnl) for pos in winning_trades)
                total_losses = abs(sum(float(pos.realized_pnl) for pos in losing_trades))
                profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
                
                return PerformanceMetrics(
                    total_return=Decimal(str(total_return)),
                    total_return_pct=Decimal(str(total_return_pct)),
                    annualized_return=Decimal(str(annualized_return)),
                    volatility=Decimal(str(volatility)),
                    sharpe_ratio=Decimal(str(sharpe_ratio)),
                    max_drawdown=Decimal(str(max_drawdown)),
                    max_drawdown_pct=Decimal(str(max_drawdown_pct)),
                    win_rate=Decimal(str(win_rate)),
                    profit_factor=Decimal(str(profit_factor)),
                    avg_win=Decimal(str(avg_win)),
                    avg_loss=Decimal(str(avg_loss)),
                    largest_win=Decimal(str(largest_win)),
                    largest_loss=Decimal(str(largest_loss))
                )
                
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics for session {session_id}: {e}")
            return None
    
    async def get_portfolio_summary(self, session_id: int) -> Optional[PortfolioSummary]:
        """Get current portfolio summary."""
        
        if session_id in self.portfolio_cache:
            return self.portfolio_cache[session_id]
        
        # Load and calculate if not cached
        await self._load_session_positions(session_id)
        await self._update_portfolio_values(session_id)
        
        return self.portfolio_cache.get(session_id)
    
    async def get_position_details(self, session_id: int, symbol: str) -> Optional[PositionSummary]:
        """Get detailed position information."""
        
        if session_id in self.position_cache:
            return self.position_cache[session_id].get(symbol)
        
        return None
    
    async def get_performance_metrics(self, session_id: int) -> Optional[PerformanceMetrics]:
        """Get comprehensive performance metrics."""
        
        return await self._calculate_performance_metrics(session_id)
    
    async def get_portfolio_history(
        self,
        session_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get portfolio history snapshots."""
        
        try:
            with get_db_session() as db:
                query = db.query(PaperPortfolioSnapshot).filter(
                    PaperPortfolioSnapshot.session_id == session_id
                )
                
                if start_date:
                    query = query.filter(PaperPortfolioSnapshot.timestamp >= start_date)
                if end_date:
                    query = query.filter(PaperPortfolioSnapshot.timestamp <= end_date)
                
                snapshots = query.order_by(PaperPortfolioSnapshot.timestamp).all()
                
                return [
                    {
                        "timestamp": snapshot.timestamp.isoformat(),
                        "total_value": float(snapshot.total_value),
                        "cash_balance": float(snapshot.cash_balance),
                        "positions_value": float(snapshot.market_value),
                        "total_return": float(snapshot.total_return),
                        "total_return_pct": float(snapshot.total_return_pct),
                        "daily_return": float(snapshot.daily_return) if snapshot.daily_return else 0.0,
                        "daily_return_pct": float(snapshot.daily_return_pct) if snapshot.daily_return_pct else 0.0,
                        "drawdown": float(snapshot.drawdown) if snapshot.drawdown else 0.0,
                        "drawdown_pct": float(snapshot.drawdown_pct) if snapshot.drawdown_pct else 0.0,
                        "sharpe_ratio": float(snapshot.sharpe_ratio) if snapshot.sharpe_ratio else 0.0,
                        "num_positions": snapshot.num_positions,
                        "leverage": float(snapshot.leverage)
                    }
                    for snapshot in snapshots
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting portfolio history for session {session_id}: {e}")
            return []
    
    async def cleanup(self) -> None:
        """Cleanup portfolio tracker."""
        
        self.tracking_active = False
        self.logger.info("Portfolio tracker cleaned up")


# Global portfolio tracker instance
portfolio_tracker = PortfolioTracker()