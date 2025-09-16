"""
Paper trading API endpoints.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from pydantic import BaseModel, Field

from app.services.paper_trading_engine import paper_trading_engine, OrderRequest
from app.services.order_management import order_manager
from app.services.portfolio_tracker import portfolio_tracker
from app.services.market_data_service import market_data_service
from app.services.risk_manager import risk_manager
from app.models.paper_trading import OrderStatus, OrderType, OrderSide, PaperTradingSession
from app.core.auth import get_current_user_id


router = APIRouter(prefix="/paper-trading")


# Request/Response Models
class WorkflowPaperTradingRequest(BaseModel):
    workflow_definition: Dict[str, Any] = Field(..., description="The workflow definition from the no-code UI")
    config: Dict[str, Any] = Field(..., description="Paper trading configuration")

class CreateSessionRequest(BaseModel):
    strategy_id: int
    name: str
    description: Optional[str] = None
    initial_capital: Decimal = Field(default=Decimal("100000.00"), gt=0)
    commission_rate: Decimal = Field(default=Decimal("0.001"), ge=0)
    slippage_rate: Decimal = Field(default=Decimal("0.0001"), ge=0)


class SessionResponse(BaseModel):
    session_id: int
    strategy_id: int
    name: str
    description: Optional[str]
    is_active: bool
    initial_capital: float
    current_capital: float
    cash_balance: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    open_positions: List[Dict[str, Any]]
    num_orders: int
    last_update: str


class SubmitOrderRequest(BaseModel):
    symbol: str
    side: str = Field(..., pattern="^(buy|sell)$")
    order_type: str = Field(..., pattern="^(market|limit|stop|stop_limit)$")
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    stop_price: Optional[Decimal] = Field(None, gt=0)
    time_in_force: str = Field(default="DAY", pattern="^(DAY|GTC|IOC|FOK)$")
    client_order_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OrderResponse(BaseModel):
    order_id: str
    client_order_id: Optional[str]
    symbol: str
    side: str
    order_type: str
    quantity: float
    filled_quantity: float
    remaining_quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    avg_fill_price: Optional[float]
    status: str
    commission: float
    slippage: float
    time_in_force: str
    created_at: str
    filled_at: Optional[str]
    reject_reason: Optional[str]


class PortfolioResponse(BaseModel):
    session_id: int
    total_value: float
    cash_balance: float
    positions_value: float
    total_pnl: float
    total_pnl_pct: float
    day_pnl: float
    day_pnl_pct: float
    realized_pnl: float
    unrealized_pnl: float
    num_positions: int
    leverage: float
    positions: List[Dict[str, Any]]


class RiskSummaryResponse(BaseModel):
    session_id: int
    overall_risk_score: float
    overall_risk_level: str
    risk_metrics: List[Dict[str, Any]]
    recent_alerts: int
    critical_alerts: int
    last_updated: str


class PositionSizingRequest(BaseModel):
    symbol: str
    side: str = Field(..., pattern="^(buy|sell)$")
    risk_percentage: Decimal = Field(default=Decimal("0.01"), gt=0, le=1)
    stop_loss_pct: Optional[Decimal] = Field(None, gt=0, lt=1)


class PositionSizingResponse(BaseModel):
    symbol: str
    recommended_quantity: float
    max_quantity: float
    risk_percentage: float
    stop_loss_price: Optional[float]
    position_value: Optional[float]
    rationale: str


class MarketDataResponse(BaseModel):
    symbol: str
    timestamp: str
    bid: float
    ask: float
    last_price: float
    spread: float
    volume: float


# API Endpoints

@router.post("/from-workflow", status_code=status.HTTP_202_ACCEPTED)
async def create_paper_session_from_workflow(
    request: WorkflowPaperTradingRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Create a paper trading session from a workflow."""
    # Placeholder logic
    import logging
    logging.info(f"Received paper trading request from workflow for user {user_id}")

    strategy_id = 1 # dummy
    session = await paper_trading_engine.create_session(
        strategy_id=strategy_id,
        name=f"Workflow Paper Trading - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        initial_capital=request.config.get("paper_initial_capital", 50000)
    )
    return {"session_id": session.id, "status": "created"}


@router.post("/sessions", response_model=SessionResponse)
async def create_paper_trading_session(request: CreateSessionRequest):
    """Create a new paper trading session."""
    try:
        session = await paper_trading_engine.create_session(
            strategy_id=request.strategy_id,
            name=request.name,
            description=request.description,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate,
            slippage_rate=request.slippage_rate
        )
        
        # Get session status
        status = await paper_trading_engine.get_session_status(session.id)
        
        return SessionResponse(**status)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_status(session_id: int = Path(..., description="Paper trading session ID")):
    """Get paper trading session status."""
    try:
        status = await paper_trading_engine.get_session_status(session_id)
        return SessionResponse(**status)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/stop")
async def stop_session(session_id: int = Path(..., description="Paper trading session ID")):
    """Stop a paper trading session."""
    try:
        await paper_trading_engine.stop_session(session_id)
        return {"message": f"Session {session_id} stopped successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/orders", response_model=OrderResponse)
async def submit_order(
    session_id: int,
    request: SubmitOrderRequest
):
    """Submit a trading order."""
    try:
        # Validate order with risk manager
        is_valid, validation_errors = await risk_manager.validate_order_risk(
            session_id=session_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Order validation failed: {', '.join(validation_errors)}")
        
        # Submit order
        order = await order_manager.submit_order(
            session_id=session_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            time_in_force=request.time_in_force,
            client_order_id=request.client_order_id,
            metadata=request.metadata
        )
        
        # Get order status
        order_status = await order_manager.get_order_status(order.id)
        if not order_status:
            raise HTTPException(status_code=500, detail="Failed to retrieve order status")
        
        return OrderResponse(**order_status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/orders", response_model=List[OrderResponse])
async def get_orders(session_id: int = Path(..., description="Paper trading session ID")):
    """Get all orders for a session."""
    try:
        orders = await order_manager.get_orders_for_session(session_id)
        return [OrderResponse(**order) for order in orders]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_status(order_id: int = Path(..., description="Order ID")):
    """Get order status."""
    try:
        order_status = await order_manager.get_order_status(order_id)
        if not order_status:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return OrderResponse(**order_status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: int = Path(..., description="Order ID")):
    """Cancel a pending order."""
    try:
        success = await order_manager.cancel_order(order_id)
        if not success:
            raise HTTPException(status_code=404, detail="Order not found or cannot be cancelled")
        
        return {"message": f"Order {order_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/portfolio", response_model=PortfolioResponse)
async def get_portfolio(session_id: int = Path(..., description="Paper trading session ID")):
    """Get portfolio summary."""
    try:
        portfolio = await portfolio_tracker.get_portfolio_summary(session_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Convert to response format
        response_data = {
            "session_id": portfolio.session_id,
            "total_value": float(portfolio.total_value),
            "cash_balance": float(portfolio.cash_balance),
            "positions_value": float(portfolio.positions_value),
            "total_pnl": float(portfolio.total_pnl),
            "total_pnl_pct": float(portfolio.total_pnl_pct),
            "day_pnl": float(portfolio.day_pnl),
            "day_pnl_pct": float(portfolio.day_pnl_pct),
            "realized_pnl": float(portfolio.realized_pnl),
            "unrealized_pnl": float(portfolio.unrealized_pnl),
            "num_positions": portfolio.num_positions,
            "leverage": float(portfolio.leverage),
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": float(pos.quantity),
                    "side": pos.side,
                    "avg_price": float(pos.avg_price),
                    "current_price": float(pos.current_price),
                    "market_value": float(pos.market_value),
                    "cost_basis": float(pos.cost_basis),
                    "unrealized_pnl": float(pos.unrealized_pnl),
                    "unrealized_pnl_pct": float(pos.unrealized_pnl_pct),
                    "day_pnl": float(pos.day_pnl),
                    "day_pnl_pct": float(pos.day_pnl_pct)
                }
                for pos in portfolio.positions
            ]
        }
        
        return PortfolioResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/portfolio/history")
async def get_portfolio_history(
    session_id: int = Path(..., description="Paper trading session ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date")
):
    """Get portfolio history."""
    try:
        history = await portfolio_tracker.get_portfolio_history(
            session_id=session_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {"session_id": session_id, "history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/performance")
async def get_performance_metrics(session_id: int = Path(..., description="Paper trading session ID")):
    """Get comprehensive performance metrics."""
    try:
        metrics = await portfolio_tracker.get_performance_metrics(session_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Performance metrics not available")
        
        return {
            "session_id": session_id,
            "total_return": float(metrics.total_return),
            "total_return_pct": float(metrics.total_return_pct),
            "annualized_return": float(metrics.annualized_return),
            "volatility": float(metrics.volatility),
            "sharpe_ratio": float(metrics.sharpe_ratio),
            "max_drawdown": float(metrics.max_drawdown),
            "max_drawdown_pct": float(metrics.max_drawdown_pct),
            "win_rate": float(metrics.win_rate),
            "profit_factor": float(metrics.profit_factor),
            "avg_win": float(metrics.avg_win),
            "avg_loss": float(metrics.avg_loss),
            "largest_win": float(metrics.largest_win),
            "largest_loss": float(metrics.largest_loss)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/risk", response_model=RiskSummaryResponse)
async def get_risk_summary(session_id: int = Path(..., description="Paper trading session ID")):
    """Get risk summary."""
    try:
        risk_summary = await risk_manager.get_risk_summary(session_id)
        return RiskSummaryResponse(**risk_summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/risk/alerts")
async def get_risk_alerts(session_id: int = Path(..., description="Paper trading session ID")):
    """Get risk alerts."""
    try:
        alerts = await risk_manager.get_risk_alerts(session_id)
        return {"session_id": session_id, "alerts": alerts}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/position-sizing", response_model=PositionSizingResponse)
async def calculate_position_sizing(
    session_id: int,
    request: PositionSizingRequest
):
    """Calculate optimal position sizing."""
    try:
        sizing = await risk_manager.calculate_position_size(
            session_id=session_id,
            symbol=request.symbol,
            side=request.side,
            risk_percentage=request.risk_percentage,
            stop_loss_pct=request.stop_loss_pct
        )
        
        return PositionSizingResponse(
            symbol=sizing.symbol,
            recommended_quantity=float(sizing.recommended_quantity),
            max_quantity=float(sizing.max_quantity),
            risk_percentage=float(sizing.risk_percentage),
            stop_loss_price=float(sizing.stop_loss_price) if sizing.stop_loss_price else None,
            position_value=float(sizing.position_value) if sizing.position_value else None,
            rationale=sizing.rationale
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data(symbol: str = Path(..., description="Trading symbol")):
    """Get current market data for a symbol."""
    try:
        quote = await market_data_service.get_current_quote(symbol)
        if not quote:
            raise HTTPException(status_code=404, detail=f"Market data not available for {symbol}")
        
        return MarketDataResponse(
            symbol=quote.symbol,
            timestamp=quote.timestamp.isoformat(),
            bid=float(quote.bid),
            ask=float(quote.ask),
            last_price=float((quote.bid + quote.ask) / 2),
            spread=float(quote.spread),
            volume=float(quote.bid_size + quote.ask_size)  # Simplified volume
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-data/{symbol}/history")
async def get_historical_data(
    symbol: str = Path(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe (e.g., 1m, 5m, 1h, 1d)"),
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of bars")
):
    """Get historical market data."""
    try:
        bars = await market_data_service.get_historical_bars(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "bars": [
                {
                    "timestamp": bar.timestamp.isoformat(),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": float(bar.volume)
                }
                for bar in bars
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "paper-trading-api",
        "timestamp": datetime.utcnow().isoformat()
    }