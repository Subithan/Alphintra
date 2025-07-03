from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
import asyncio
import os

from .models import Base, User, NoCodeWorkflow, NoCodeComponent, NoCodeExecution, NoCodeTemplate
from .schemas import *
from .workflow_compiler import WorkflowCompiler

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra_user:alphintra_password@localhost:5432/alphintra_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(
    title="Alphintra No-Code Service", 
    description="No-code visual workflow builder for trading strategies",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://alphintra.com", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify JWT token and return current user - Simplified for development"""
    # For development, create a test user if not exists
    test_user = db.query(User).filter(User.email == "test@alphintra.com").first()
    if not test_user:
        test_user = User(
            email="test@alphintra.com",
            password_hash="test_hash",
            first_name="Test",
            last_name="User",
            is_verified=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    return test_user

# Initialize services
workflow_compiler = WorkflowCompiler()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "no-code-service", "version": "2.0.0"}

# Workflow Management Endpoints
@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new no-code workflow"""
    try:
        db_workflow = NoCodeWorkflow(
            name=workflow.name,
            description=workflow.description,
            category=workflow.category or 'custom',
            tags=workflow.tags or [],
            user_id=current_user.id,
            workflow_data=workflow.workflow_data or {"nodes": [], "edges": []},
            execution_mode=workflow.execution_mode or 'backtest'
        )
        
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        
        return WorkflowResponse.from_orm(db_workflow)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@app.get("/api/workflows", response_model=List[WorkflowResponse])
async def get_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    category: Optional[str] = None,
    is_public: Optional[bool] = None
):
    """Get user's workflows with filtering"""
    try:
        query = db.query(NoCodeWorkflow).filter(
            (NoCodeWorkflow.user_id == current_user.id) | 
            (NoCodeWorkflow.is_public == True)
        )
        
        if category:
            query = query.filter(NoCodeWorkflow.category == category)
        if is_public is not None:
            query = query.filter(NoCodeWorkflow.is_public == is_public)
            
        workflows = query.offset(skip).limit(limit).order_by(NoCodeWorkflow.updated_at.desc()).all()
        return [WorkflowResponse.from_orm(w) for w in workflows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflows: {str(e)}")

@app.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific workflow"""
    try:
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            (NoCodeWorkflow.user_id == current_user.id) | (NoCodeWorkflow.is_public == True)
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
            
        return WorkflowResponse.from_orm(workflow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflow: {str(e)}")

@app.put("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_update: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a workflow"""
    try:
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        update_data = workflow_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(workflow, field):
                setattr(workflow, field, value)
        
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
        
        return WorkflowResponse.from_orm(workflow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")

@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a workflow"""
    try:
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        db.delete(workflow)
        db.commit()
        
        return {"message": "Workflow deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")

# Code Generation Endpoints
@app.post("/api/workflows/{workflow_id}/compile", response_model=CompilationResponse)
async def compile_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compile workflow to Python trading strategy code"""
    try:
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update compilation status
        workflow.compilation_status = 'compiling'
        db.commit()
        
        # Compile workflow
        compilation_result = await workflow_compiler.compile_workflow(
            workflow.workflow_data.get('nodes', []),
            workflow.workflow_data.get('edges', []),
            workflow.name
        )
        
        # Update workflow with generated code
        workflow.generated_code = compilation_result.get('code', '')
        workflow.generated_requirements = compilation_result.get('requirements', [])
        workflow.compilation_status = 'compiled' if compilation_result.get('success') else 'failed'
        workflow.compilation_errors = compilation_result.get('errors', [])
        
        db.commit()
        db.refresh(workflow)
        
        return CompilationResponse(
            workflow_id=str(workflow.uuid),
            generated_code=workflow.generated_code,
            requirements=workflow.generated_requirements,
            status=workflow.compilation_status,
            errors=workflow.compilation_errors,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Update workflow status to failed
        workflow = db.query(NoCodeWorkflow).filter(NoCodeWorkflow.uuid == workflow_id).first()
        if workflow:
            workflow.compilation_status = 'failed'
            workflow.compilation_errors = [str(e)]
            db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to compile workflow: {str(e)}")

# Execution Endpoints
@app.post("/api/workflows/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    execution_config: ExecutionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a compiled workflow (backtest, paper trade, or live trade)"""
    try:
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.compilation_status != 'compiled':
            raise HTTPException(status_code=400, detail="Workflow must be compiled before execution")
        
        # Create execution record
        execution = NoCodeExecution(
            workflow_id=workflow.id,
            user_id=current_user.id,
            execution_type=execution_config.execution_type,
            symbols=execution_config.symbols,
            timeframe=execution_config.timeframe,
            start_date=execution_config.start_date,
            end_date=execution_config.end_date,
            initial_capital=execution_config.initial_capital,
            parameters=execution_config.parameters or {}
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Start execution in background
        background_tasks.add_task(
            execute_strategy_background,
            str(execution.uuid),
            workflow.generated_code,
            execution_config.dict()
        )
        
        return ExecutionResponse.from_orm(execution)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start execution: {str(e)}")

@app.get("/api/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution status and results"""
    try:
        execution = db.query(NoCodeExecution).filter(
            NoCodeExecution.uuid == execution_id,
            NoCodeExecution.user_id == current_user.id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return ExecutionResponse.from_orm(execution)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch execution: {str(e)}")

# Component Library Endpoints
@app.get("/api/components", response_model=List[ComponentResponse])
async def get_components(
    category: Optional[str] = None,
    is_builtin: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get available workflow components"""
    try:
        query = db.query(NoCodeComponent).filter(NoCodeComponent.is_public == True)
        
        if category:
            query = query.filter(NoCodeComponent.category == category)
        if is_builtin is not None:
            query = query.filter(NoCodeComponent.is_builtin == is_builtin)
            
        components = query.order_by(NoCodeComponent.category, NoCodeComponent.name).all()
        return [ComponentResponse.from_orm(c) for c in components]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch components: {str(e)}")

# Template Library Endpoints
@app.get("/api/templates", response_model=List[TemplateResponse])
async def get_templates(
    category: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    is_featured: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get available workflow templates"""
    try:
        query = db.query(NoCodeTemplate).filter(NoCodeTemplate.is_public == True)
        
        if category:
            query = query.filter(NoCodeTemplate.category == category)
        if difficulty_level:
            query = query.filter(NoCodeTemplate.difficulty_level == difficulty_level)
        if is_featured is not None:
            query = query.filter(NoCodeTemplate.is_featured == is_featured)
            
        templates = query.order_by(NoCodeTemplate.rating.desc()).all()
        return [TemplateResponse.from_orm(t) for t in templates]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")

@app.post("/api/templates/{template_id}/use", response_model=WorkflowResponse)
async def create_workflow_from_template(
    template_id: str,
    workflow_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workflow from a template"""
    try:
        template = db.query(NoCodeTemplate).filter(
            NoCodeTemplate.uuid == template_id,
            NoCodeTemplate.is_public == True
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Create workflow from template
        workflow = NoCodeWorkflow(
            name=workflow_name,
            description=f"Created from template: {template.name}",
            category=template.category,
            user_id=current_user.id,
            workflow_data=template.template_data,
            is_template=False,
            parent_workflow_id=None
        )
        
        db.add(workflow)
        
        # Update template usage count
        template.usage_count += 1
        
        db.commit()
        db.refresh(workflow)
        
        return WorkflowResponse.from_orm(workflow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow from template: {str(e)}")

# Background Tasks
async def execute_strategy_background(execution_id: str, strategy_code: str, config: dict):
    """Background task to execute trading strategy"""
    db = SessionLocal()
    try:
        execution = db.query(NoCodeExecution).filter(NoCodeExecution.uuid == execution_id).first()
        if not execution:
            return
        
        execution.status = 'running'
        execution.current_step = 'Initializing execution environment'
        db.commit()
        
        # Simulate strategy execution
        await asyncio.sleep(2)
        execution.current_step = 'Loading market data'
        execution.progress = 25
        db.commit()
        
        await asyncio.sleep(3)
        execution.current_step = 'Running strategy logic'
        execution.progress = 50
        db.commit()
        
        await asyncio.sleep(5)
        execution.current_step = 'Calculating performance metrics'
        execution.progress = 75
        db.commit()
        
        await asyncio.sleep(2)
        
        # Simulate results
        execution.status = 'completed'
        execution.progress = 100
        execution.final_capital = float(config['initial_capital']) * 1.15  # 15% return
        execution.total_return_percent = 15.0
        execution.total_trades = 25
        execution.winning_trades = 18
        execution.performance_metrics = {
            "sharpe_ratio": 1.8,
            "max_drawdown": -5.2,
            "win_rate": 72.0,
            "profit_factor": 2.1
        }
        execution.completed_at = datetime.utcnow()
        
        db.commit()
        
    except Exception as e:
        execution.status = 'failed'
        execution.error_logs = [{"error": str(e), "timestamp": datetime.utcnow().isoformat()}]
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)  # Use port 8004 for no-code service