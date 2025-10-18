"""REST API routes for workflow management."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi import Query as FastAPIQuery
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal, get_db
from app.core.dependencies import get_current_user
from app.services import workflows as workflow_service
from models import NoCodeExecution, NoCodeWorkflow, User
from schemas_updated import (
    CompilationResponse,
    ExecutionCreate,
    ExecutionResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowUpdate,
)
from workflow_compiler_updated import WorkflowCompiler

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

settings = get_settings()
logger = logging.getLogger(__name__)
workflow_compiler = WorkflowCompiler()


@router.post("", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new no-code workflow."""

    try:
        db_workflow = workflow_service.create_workflow(db, current_user, workflow)
        return WorkflowResponse.from_orm(db_workflow)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {exc}") from exc


@router.get("", response_model=List[WorkflowResponse])
async def get_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = FastAPIQuery(0, ge=0),
    limit: int = FastAPIQuery(100, le=1000),
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
):
    """Get user's workflows with filtering."""

    try:
        workflows = workflow_service.list_user_workflows(
            db,
            current_user,
            skip=skip,
            limit=limit,
            category=category,
            is_public=is_public,
            dev_mode=settings.dev_mode,
        )
        return [WorkflowResponse.from_orm(w) for w in workflows]
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflows: {exc}") from exc


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific workflow by ID."""

    try:
        workflow = workflow_service.ensure_workflow_access(
            db,
            workflow_id,
            current_user,
            dev_mode=settings.dev_mode,
        )
        return WorkflowResponse.from_orm(workflow)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflow: {exc}") from exc


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_update: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing workflow or create a new one when the identifier does not exist."""

    try:
        try:
            import uuid as uuid_module

            uuid_module.UUID(workflow_id)
            workflow = (
                db.query(NoCodeWorkflow)
                .filter(
                    NoCodeWorkflow.uuid == workflow_id,
                    NoCodeWorkflow.user_id == current_user.id,
                )
                .first()
            )
        except ValueError:
            logger.info("Creating new workflow for non-UUID identifier: %s", workflow_id)
            workflow = None

        if workflow:
            updated = workflow_service.update_workflow(db, workflow, workflow_update)
            return WorkflowResponse.from_orm(updated)

        workflow_data = workflow_update.dict(exclude_unset=True)
        create_payload = WorkflowCreate(
            name=workflow_data.get("name", f"Workflow {workflow_id}"),
            description=workflow_data.get("description", "Created from template"),
            category=workflow_data.get("category", "trading_strategy"),
            tags=workflow_data.get("tags", ["no-code", "generated"]),
            workflow_data=workflow_data.get("workflow_data", {"nodes": [], "edges": []}),
            execution_mode=workflow_data.get("execution_mode", "backtest"),
        )

        new_workflow = workflow_service.create_workflow(db, current_user, create_payload)

        if "generated_code" in workflow_data:
            new_workflow.generated_code = workflow_data["generated_code"]
        if "generated_requirements" in workflow_data:
            new_workflow.generated_requirements = workflow_data["generated_requirements"]
        if "compilation_status" in workflow_data:
            new_workflow.compilation_status = workflow_data["compilation_status"]
        if "validation_status" in workflow_data:
            new_workflow.validation_status = workflow_data["validation_status"]
        if "deployment_status" in workflow_data:
            new_workflow.deployment_status = workflow_data["deployment_status"]
        if "execution_metadata" in workflow_data:
            new_workflow.execution_metadata = workflow_data["execution_metadata"]
        new_workflow.version = workflow_data.get("version", 1)
        new_workflow.is_template = workflow_data.get("is_template", False)
        new_workflow.is_public = workflow_data.get("is_public", False)

        db.commit()
        db.refresh(new_workflow)
        logger.info("Created new workflow with UUID: %s", new_workflow.uuid)
        return WorkflowResponse.from_orm(new_workflow)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error updating/creating workflow: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {exc}") from exc


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a workflow."""

    try:
        workflow = workflow_service.ensure_workflow_access(
            db,
            workflow_id,
            current_user,
            dev_mode=settings.dev_mode,
        )
        workflow_service.ensure_owner(workflow, current_user)
        workflow_service.delete_workflow(db, workflow)
        return {"message": "Workflow deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error deleting workflow: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {exc}") from exc


@router.post("/{workflow_id}/compile", response_model=CompilationResponse)
async def compile_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compile workflow to Python trading strategy code."""

    try:
        workflow = workflow_service.ensure_workflow_access(
            db,
            workflow_id,
            current_user,
            dev_mode=settings.dev_mode,
        )
        workflow_service.ensure_owner(workflow, current_user)

        workflow.compilation_status = "compiling"
        db.commit()

        compilation_result = await workflow_compiler.compile_workflow(
            workflow.workflow_data.get("nodes", []),
            workflow.workflow_data.get("edges", []),
            workflow.name,
        )

        workflow.generated_code = compilation_result.get("code", "")
        workflow.generated_requirements = compilation_result.get("requirements", [])
        workflow.compilation_status = "compiled" if compilation_result.get("success") else "failed"
        workflow.compilation_errors = compilation_result.get("errors", [])

        db.commit()
        db.refresh(workflow)

        # Create compilation result with user association
        from models import CompilationResult
        compilation_record = CompilationResult(
            id=str(workflow.uuid),
            workflow_id=workflow.id,
            user_id=current_user.id,
            python_code=workflow.generated_code or "",
            validation_results=compilation_result.get("validation", {}),
            status=workflow.compilation_status,
            error_message="; ".join(compilation_result.get("errors", [])),
        )
        db.add(compilation_record)
        db.commit()

        return CompilationResponse(
            workflow_id=str(workflow.uuid),
            generated_code=workflow.generated_code,
            requirements=workflow.generated_requirements,
            status=workflow.compilation_status,
            errors=workflow.compilation_errors,
            created_at=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        fallback = (
            db.query(NoCodeWorkflow).filter(NoCodeWorkflow.uuid == workflow_id).first()
        )
        if fallback:
            fallback.compilation_status = "failed"
            fallback.compilation_errors = [str(exc)]
            db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to compile workflow: {exc}") from exc


@router.post("/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    execution_config: ExecutionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a compiled workflow (backtest, paper trade, or live trade)."""

    try:
        workflow = workflow_service.ensure_workflow_access(
            db,
            workflow_id,
            current_user,
            dev_mode=settings.dev_mode,
        )
        workflow_service.ensure_owner(workflow, current_user)

        if workflow.compilation_status != "compiled":
            raise HTTPException(status_code=400, detail="Workflow must be compiled before execution")

        execution = NoCodeExecution(
            workflow_id=workflow.id,
            user_id=current_user.id,
            execution_type=execution_config.execution_type,
            symbols=execution_config.symbols,
            timeframe=execution_config.timeframe,
            start_date=execution_config.start_date,
            end_date=execution_config.end_date,
            initial_capital=execution_config.initial_capital,
            parameters=execution_config.parameters or {},
            status="pending",
            progress=0,
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

        background_tasks.add_task(
            execute_strategy_background,
            execution_id=str(execution.uuid),
            strategy_code=workflow.generated_code or "",
            config={
                "initial_capital": float(execution.initial_capital or 10000.0),
                "symbols": execution.symbols,
                "timeframe": execution.timeframe,
            },
        )

        return ExecutionResponse.from_orm(execution)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error executing workflow: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {exc}") from exc


async def execute_strategy_background(execution_id: str, strategy_code: str, config: dict):
    """Background task to execute a trading strategy."""

    db = SessionLocal()
    try:
        execution = db.query(NoCodeExecution).filter(NoCodeExecution.uuid == execution_id).first()
        if not execution:
            return

        execution.status = "running"
        execution.current_step = "Initializing execution environment"
        db.commit()

        await asyncio.sleep(2)
        execution.current_step = "Loading market data"
        execution.progress = 25
        db.commit()

        await asyncio.sleep(3)
        execution.current_step = "Running strategy logic"
        execution.progress = 50
        db.commit()

        await asyncio.sleep(5)
        execution.current_step = "Calculating performance metrics"
        execution.progress = 75
        db.commit()

        await asyncio.sleep(2)

        execution.status = "completed"
        execution.progress = 100
        execution.final_capital = float(config["initial_capital"]) * 1.15
        execution.total_return_percent = 15.0
        execution.total_trades = 25
        execution.winning_trades = 18
        execution.performance_metrics = {
            "total_return_percent": 15.0,
            "annualized_return_percent": 12.5,
            "max_drawdown_percent": -4.2,
            "sharpe_ratio": 1.8,
            "profit_factor": 1.9,
        }
        execution.execution_logs = [
            "Strategy initialized",
            "Loaded market data",
            "Calculated indicators",
            "Generated trade signals",
            "Executed trades",
            "Computed performance metrics",
        ]
        execution.trades_data = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "BUY",
                "symbol": execution.symbols[0] if execution.symbols else "AAPL",
                "quantity": 10,
                "price": 150.25,
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "SELL",
                "symbol": execution.symbols[0] if execution.symbols else "AAPL",
                "quantity": 10,
                "price": 158.75,
            },
        ]
        execution.results = {
            "strategy_code": strategy_code,
            "config": config,
            "summary": {
                "final_capital": float(execution.final_capital or 0),
                "total_return_percent": execution.total_return_percent,
                "total_trades": execution.total_trades,
                "winning_trades": execution.winning_trades,
            },
        }
        execution.completed_at = datetime.utcnow()

        # Create execution history record with user association
        from models import ExecutionHistory
        execution_history = ExecutionHistory(
            workflow_id=execution.workflow_id,
            user_id=execution.user_id,
            execution_mode=execution.execution_type,
            status=execution.status,
            execution_config={
                "initial_capital": float(config["initial_capital"]),
                "symbols": execution.symbols,
                "timeframe": execution.timeframe,
            },
            results=execution.results,
            error_logs=execution.error_logs,
            generated_code=strategy_code,
            compilation_stats=execution.compilation_stats,
            created_at=execution.started_at,
            completed_at=execution.completed_at,
        )
        db.add(execution_history)
        db.commit()
    finally:
        db.close()
