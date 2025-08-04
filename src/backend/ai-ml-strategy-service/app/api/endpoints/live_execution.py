"""
Live execution API endpoints.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field

from app.services.live_execution_engine import live_execution_engine, SignalData
from app.services.strategy_orchestrator import strategy_orchestrator
from app.services.deployment_manager import deployment_manager, DeploymentConfig
from app.services.signal_processor import signal_processor, SignalPriority, ProcessingMode
from app.services.broker_integration import broker_integration_service
from app.models.execution import ExecutionStatus, SignalType


router = APIRouter(prefix="/live-execution")


# Request/Response Models
class CreateExecutionRequest(BaseModel):
    strategy_id: int
    environment_id: int
    name: str
    description: Optional[str] = None
    allocated_capital: Decimal = Field(..., gt=0)
    symbols: List[str] = Field(..., min_items=1)
    timeframes: List[str] = Field(default=["1h"])
    position_sizing_method: str = Field(default="fixed_percentage")
    position_size_config: Dict[str, Any] = Field(default={"percentage": 0.05})
    risk_limits: Dict[str, Any] = Field(default={})
    execution_config: Dict[str, Any] = Field(default={})
    monitoring_config: Dict[str, Any] = Field(default={})
    auto_start: bool = Field(default=True)
    metadata: Optional[Dict[str, Any]] = None


class ExecutionResponse(BaseModel):
    execution_id: int
    status: str
    strategy_id: int
    allocated_capital: float
    current_capital: float
    symbols: List[str]
    start_time: Optional[str]
    last_signal_time: str
    active_positions: int
    pending_orders: int
    signals_processed: int
    orders_submitted: int
    orders_filled: int
    error_count: int
    last_error: Optional[str]


class SubmitSignalRequest(BaseModel):
    strategy_execution_id: int
    signal_type: str = Field(..., regex="^(entry_long|entry_short|exit_long|exit_short|position_adjust|risk_management)$")
    symbol: str
    timeframe: str
    action: str = Field(..., regex="^(buy|sell|hold)$")
    quantity: Optional[Decimal] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    stop_loss: Optional[Decimal] = Field(None, gt=0)
    take_profit: Optional[Decimal] = Field(None, gt=0)
    indicators: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    model_output: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    priority: str = Field(default="medium", regex="^(low|medium|high|critical)$")
    processing_mode: str = Field(default="real_time", regex="^(real_time|batch|stream)$")


class SignalResponse(BaseModel):
    signal_accepted: bool
    processing_latency_ms: Optional[int]
    confidence_score: Optional[float]
    risk_score: Optional[float]
    execution_recommendation: Optional[str]
    error_message: Optional[str]


class DeploymentRequest(BaseModel):
    strategy_id: int
    environment_id: int
    deployment_name: str
    deployment_type: str = Field(default="paper_trading", regex="^(paper_trading|live_trading|simulation)$")
    allocated_capital: Decimal = Field(..., gt=0)
    symbols: List[str] = Field(..., min_items=1)
    timeframes: List[str] = Field(default=["1h"])
    position_sizing_method: str = Field(default="fixed_percentage")
    position_size_config: Dict[str, Any] = Field(default={"percentage": 0.05})
    risk_limits: Dict[str, Any] = Field(default={})
    execution_config: Dict[str, Any] = Field(default={})
    monitoring_config: Dict[str, Any] = Field(default={})
    auto_start: bool = Field(default=True)
    metadata: Optional[Dict[str, Any]] = None


class DeploymentResponse(BaseModel):
    deployment_id: str
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    current_step: Optional[str]
    completed_steps: List[str]
    error_message: Optional[str]
    health_status: Optional[str]
    last_health_check: Optional[str]
    execution_status: Optional[Dict[str, Any]]


class OrchestrationResponse(BaseModel):
    orchestration_id: str
    mode: str
    environment_id: int
    status: Optional[str]
    total_strategies: int
    strategy_statuses: Dict[str, Any]
    allocations: Dict[str, Any]
    metrics: Optional[Dict[str, Any]]
    last_rebalance: Optional[str]
    next_rebalance: Optional[str]


# API Endpoints

@router.post("/deploy", response_model=DeploymentResponse)
async def deploy_strategy(request: DeploymentRequest):
    """Deploy a strategy for live execution."""
    try:
        # Create deployment configuration
        config = DeploymentConfig(
            strategy_id=request.strategy_id,
            environment_id=request.environment_id,
            deployment_name=request.deployment_name,
            deployment_type=request.deployment_type,
            allocated_capital=request.allocated_capital,
            symbols=request.symbols,
            timeframes=request.timeframes,
            position_sizing_method=request.position_sizing_method,
            position_size_config=request.position_size_config,
            risk_limits=request.risk_limits,
            execution_config=request.execution_config,
            monitoring_config=request.monitoring_config,
            auto_start=request.auto_start,
            metadata=request.metadata
        )
        
        # Deploy strategy
        deployment_id = await deployment_manager.deploy_strategy(config)
        
        # Get deployment status
        status = await deployment_manager.get_deployment_status(deployment_id)
        if not status:
            raise HTTPException(status_code=500, detail="Failed to retrieve deployment status")
        
        return DeploymentResponse(**status)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deployments", response_model=List[DeploymentResponse])
async def get_deployments():
    """Get all active deployments."""
    try:
        deployments = await deployment_manager.get_all_deployments()
        return [DeploymentResponse(**deployment) for deployment in deployments]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment_status(deployment_id: str = Path(..., description="Deployment ID")):
    """Get deployment status."""
    try:
        status = await deployment_manager.get_deployment_status(deployment_id)
        if not status:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        return DeploymentResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deployments/{deployment_id}/start")
async def start_deployment(deployment_id: str = Path(..., description="Deployment ID")):
    """Start a deployed strategy."""
    try:
        success = await deployment_manager.start_deployment(deployment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start deployment")
        
        return {"message": f"Deployment {deployment_id} started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deployments/{deployment_id}/stop")
async def stop_deployment(deployment_id: str = Path(..., description="Deployment ID")):
    """Stop a running deployment."""
    try:
        success = await deployment_manager.stop_deployment(deployment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop deployment")
        
        return {"message": f"Deployment {deployment_id} stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deployments/{deployment_id}/pause")
async def pause_deployment(deployment_id: str = Path(..., description="Deployment ID")):
    """Pause a running deployment."""
    try:
        success = await deployment_manager.pause_deployment(deployment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to pause deployment")
        
        return {"message": f"Deployment {deployment_id} paused successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deployments/{deployment_id}/resume")
async def resume_deployment(deployment_id: str = Path(..., description="Deployment ID")):
    """Resume a paused deployment."""
    try:
        success = await deployment_manager.resume_deployment(deployment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to resume deployment")
        
        return {"message": f"Deployment {deployment_id} resumed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions", response_model=List[ExecutionResponse])
async def get_executions():
    """Get all active strategy executions."""
    try:
        # This would get all active executions from the live execution engine
        # For now, return empty list as implementation would depend on internal state
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution_status(execution_id: int = Path(..., description="Execution ID")):
    """Get execution status."""
    try:
        status = await live_execution_engine.get_execution_status(execution_id)
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return ExecutionResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/start")
async def start_execution(execution_id: int = Path(..., description="Execution ID")):
    """Start a strategy execution."""
    try:
        success = await live_execution_engine.start_execution(execution_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start execution")
        
        return {"message": f"Execution {execution_id} started successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/stop")
async def stop_execution(execution_id: int = Path(..., description="Execution ID")):
    """Stop a strategy execution."""
    try:
        success = await live_execution_engine.stop_execution(execution_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop execution")
        
        return {"message": f"Execution {execution_id} stopped successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/pause")
async def pause_execution(execution_id: int = Path(..., description="Execution ID")):
    """Pause a strategy execution."""
    try:
        success = await live_execution_engine.pause_execution(execution_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to pause execution")
        
        return {"message": f"Execution {execution_id} paused successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/resume")
async def resume_execution(execution_id: int = Path(..., description="Execution ID")):
    """Resume a paused execution."""
    try:
        success = await live_execution_engine.resume_execution(execution_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to resume execution")
        
        return {"message": f"Execution {execution_id} resumed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signals/submit", response_model=SignalResponse)
async def submit_signal(request: SubmitSignalRequest):
    """Submit a trading signal for processing."""
    try:
        # Create signal data
        signal_data = SignalData(
            strategy_execution_id=request.strategy_execution_id,
            signal_type=request.signal_type,
            symbol=request.symbol,
            timeframe=request.timeframe,
            action=request.action,
            quantity=request.quantity,
            price=request.price,
            confidence=request.confidence,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            indicators=request.indicators,
            features=request.features,
            model_output=request.model_output,
            metadata=request.metadata
        )
        
        # Convert priority and processing mode
        priority = SignalPriority(request.priority)
        processing_mode = ProcessingMode(request.processing_mode)
        
        # Process signal
        processed_signal = await signal_processor.process_signal(
            signal_data=signal_data,
            priority=priority,
            processing_mode=processing_mode
        )
        
        if processed_signal:
            return SignalResponse(
                signal_accepted=True,
                processing_latency_ms=processed_signal.processing_latency_ms,
                confidence_score=processed_signal.confidence_score,
                risk_score=processed_signal.risk_score,
                execution_recommendation=processed_signal.execution_recommendation
            )
        else:
            return SignalResponse(
                signal_accepted=False,
                error_message="Signal was filtered or rejected"
            )
        
    except Exception as e:
        return SignalResponse(
            signal_accepted=False,
            error_message=str(e)
        )


@router.get("/signals/statistics")
async def get_signal_statistics(
    strategy_execution_id: Optional[int] = Query(None, description="Strategy execution ID")
):
    """Get signal processing statistics."""
    try:
        stats = await signal_processor.get_processing_statistics(strategy_execution_id)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orchestrations", response_model=List[OrchestrationResponse])
async def get_orchestrations():
    """Get all active orchestrations."""
    try:
        orchestrations = await strategy_orchestrator.get_all_orchestrations()
        return [OrchestrationResponse(**orch) for orch in orchestrations]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orchestrations/{orchestration_id}", response_model=OrchestrationResponse)
async def get_orchestration_status(orchestration_id: str = Path(..., description="Orchestration ID")):
    """Get orchestration status."""
    try:
        status = await strategy_orchestrator.get_orchestration_status(orchestration_id)
        if not status:
            raise HTTPException(status_code=404, detail="Orchestration not found")
        
        return OrchestrationResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrations/{orchestration_id}/start")
async def start_orchestration(orchestration_id: str = Path(..., description="Orchestration ID")):
    """Start an orchestration."""
    try:
        success = await strategy_orchestrator.start_orchestration(orchestration_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start orchestration")
        
        return {"message": f"Orchestration {orchestration_id} started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrations/{orchestration_id}/stop")
async def stop_orchestration(orchestration_id: str = Path(..., description="Orchestration ID")):
    """Stop an orchestration."""
    try:
        success = await strategy_orchestrator.stop_orchestration(orchestration_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop orchestration")
        
        return {"message": f"Orchestration {orchestration_id} stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrations/{orchestration_id}/rebalance")
async def trigger_rebalance(orchestration_id: str = Path(..., description="Orchestration ID")):
    """Manually trigger portfolio rebalancing."""
    try:
        success = await strategy_orchestrator.trigger_rebalance(orchestration_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to trigger rebalance")
        
        return {"message": f"Rebalance triggered for orchestration {orchestration_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environments/{environment_id}/broker/status")
async def get_broker_status(environment_id: int = Path(..., description="Environment ID")):
    """Get broker connection status."""
    try:
        status = await broker_integration_service.test_connection(environment_id)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/environments/{environment_id}/broker/connect")
async def connect_broker(environment_id: int = Path(..., description="Environment ID")):
    """Connect to broker for environment."""
    try:
        success = await broker_integration_service.initialize_environment(environment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to connect to broker")
        
        return {"message": f"Connected to broker for environment {environment_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/environments/{environment_id}/broker/disconnect")
async def disconnect_broker(environment_id: int = Path(..., description="Environment ID")):
    """Disconnect from broker for environment."""
    try:
        success = await broker_integration_service.disconnect_environment(environment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to disconnect from broker")
        
        return {"message": f"Disconnected from broker for environment {environment_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environments/{environment_id}/broker/positions")
async def get_broker_positions(environment_id: int = Path(..., description="Environment ID")):
    """Get positions from broker."""
    try:
        positions = await broker_integration_service.get_positions(environment_id)
        
        return {
            "environment_id": environment_id,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": float(pos.quantity),
                    "side": pos.side,
                    "avg_price": float(pos.avg_price),
                    "market_value": float(pos.market_value),
                    "unrealized_pnl": float(pos.unrealized_pnl),
                    "unrealized_pnl_pct": float(pos.unrealized_pnl_pct)
                }
                for pos in positions
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environments/{environment_id}/broker/account")
async def get_broker_account(environment_id: int = Path(..., description="Environment ID")):
    """Get account information from broker."""
    try:
        account = await broker_integration_service.get_account_info(environment_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account information not available")
        
        return {
            "environment_id": environment_id,
            "account_id": account.account_id,
            "account_type": account.account_type,
            "buying_power": float(account.buying_power),
            "cash_balance": float(account.cash_balance),
            "equity": float(account.equity),
            "day_trade_buying_power": float(account.day_trade_buying_power) if account.day_trade_buying_power else None,
            "maintenance_margin": float(account.maintenance_margin) if account.maintenance_margin else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "live-execution-api",
        "timestamp": datetime.utcnow().isoformat()
    }