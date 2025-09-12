#!/usr/bin/env python3
"""
Backtest Microservice

A dedicated microservice for running backtests on generated trading strategies.
This service receives strategy code from the no-code-service and executes
comprehensive backtests with performance analysis.
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime
import logging
import uvicorn
import os

# Import our backtest engine
from backtest_engine import BacktestEngine, BacktestConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Backtest Service",
    description="Microservice for backtesting generated trading strategies",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class BacktestRequest(BaseModel):
    """Request model for backtest execution."""
    workflow_id: str
    strategy_code: str
    config: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}

class BacktestResponse(BaseModel):
    """Response model for backtest results."""
    success: bool
    execution_id: str
    workflow_id: str
    message: str
    performance_metrics: Optional[Dict[str, Any]] = None
    trade_summary: Optional[Dict[str, Any]] = None
    market_data_stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    timestamp: str
    version: str

# Initialize backtest engine
backtest_engine = BacktestEngine()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="backtest-service",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )

@app.post("/api/backtest/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest = Body(...)):
    """
    Execute backtest for a given strategy code.
    
    This endpoint receives strategy code from the no-code-service
    and runs a comprehensive backtest with performance analysis.
    """
    try:
        logger.info(f"Starting backtest for workflow {request.workflow_id}")
        
        # Validate request
        if not request.strategy_code.strip():
            raise HTTPException(
                status_code=400,
                detail="Strategy code cannot be empty"
            )
        
        # Parse backtest configuration
        config = BacktestConfig(
            start_date=request.config.get('start_date', '2023-01-01'),
            end_date=request.config.get('end_date', '2023-12-31'),
            initial_capital=float(request.config.get('initial_capital', 10000.0)),
            commission=float(request.config.get('commission', 0.001)),
            symbols=request.config.get('symbols', ['AAPL']),
            timeframe=request.config.get('timeframe', '1h'),
            slippage=float(request.config.get('slippage', 0.0001)),
            max_positions=int(request.config.get('max_positions', 1))
        )
        
        # Run backtest
        result = backtest_engine.run_backtest_from_code(
            strategy_code=request.strategy_code,
            config=config,
            workflow_id=request.workflow_id,
            metadata=request.metadata
        )
        
        if result['success']:
            logger.info(f"Backtest completed successfully for workflow {request.workflow_id}")
            
            return BacktestResponse(
                success=True,
                execution_id=result['execution_id'],
                workflow_id=request.workflow_id,
                message="Backtest completed successfully",
                performance_metrics=result['performance_metrics'],
                trade_summary=result['trade_summary'],
                market_data_stats=result['market_data_stats']
            )
        else:
            logger.error(f"Backtest failed for workflow {request.workflow_id}: {result.get('error')}")
            
            return BacktestResponse(
                success=False,
                execution_id=result.get('execution_id', str(uuid.uuid4())),
                workflow_id=request.workflow_id,
                message="Backtest failed",
                error=result.get('error', 'Unknown error')
            )
            
    except Exception as e:
        logger.error(f"Backtest service error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/backtest/status/{execution_id}")
async def get_backtest_status(execution_id: str):
    """Get status of a running backtest."""
    try:
        # In a real implementation, this would check the status
        # from a database or job queue
        return {
            "execution_id": execution_id,
            "status": "completed",  # For demo purposes
            "progress": 100,
            "message": "Backtest completed"
        }
    except Exception as e:
        logger.error(f"Error getting backtest status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backtest/results/{execution_id}")
async def get_backtest_results(execution_id: str):
    """Get detailed results of a completed backtest."""
    try:
        # In a real implementation, this would retrieve results
        # from a database or storage system
        return {
            "execution_id": execution_id,
            "status": "completed",
            "message": "Use the run endpoint response for immediate results"
        }
    except Exception as e:
        logger.error(f"Error getting backtest results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backtest/market-data/symbols")
async def get_available_symbols():
    """Get list of available symbols for backtesting."""
    return {
        "symbols": [
            {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ"},
            {"symbol": "BTCUSD", "name": "Bitcoin", "exchange": "CRYPTO"},
            {"symbol": "ETHUSD", "name": "Ethereum", "exchange": "CRYPTO"}
        ],
        "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
        "date_range": {
            "earliest": "2020-01-01",
            "latest": datetime.utcnow().strftime("%Y-%m-%d")
        }
    }

@app.get("/api/backtest/performance-metrics/definitions")
async def get_performance_metrics_definitions():
    """Get definitions of all performance metrics."""
    return {
        "metrics": {
            "total_return": "Total profit/loss in absolute terms",
            "total_return_percent": "Total profit/loss as percentage of initial capital",
            "sharpe_ratio": "Risk-adjusted return metric (higher is better)",
            "max_drawdown": "Maximum peak-to-trough decline in absolute terms",
            "max_drawdown_percent": "Maximum peak-to-trough decline as percentage",
            "total_trades": "Total number of trades executed",
            "winning_trades": "Number of profitable trades",
            "losing_trades": "Number of unprofitable trades",
            "win_rate": "Percentage of winning trades",
            "avg_win": "Average profit per winning trade",
            "avg_loss": "Average loss per losing trade",
            "profit_factor": "Ratio of gross profit to gross loss",
            "calmar_ratio": "Annual return divided by maximum drawdown",
            "sortino_ratio": "Risk-adjusted return using downside deviation",
            "final_capital": "Capital at end of backtest period"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8007))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )