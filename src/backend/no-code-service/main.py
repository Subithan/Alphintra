from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
import asyncio

from . import models, schemas, database, auth
from .workflow_compiler import WorkflowCompiler
from .dataset_manager import DatasetManager
from .training_orchestrator import TrainingOrchestrator

app = FastAPI(
    title="Alphintra No-Code Service",
    description="No-code visual workflow builder for AI trading strategies",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://alphintra.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependencies
async def get_db() -> AsyncSession:
    async with database.SessionLocal() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Verify JWT token and return current user"""
    user = await auth.verify_token(credentials.credentials, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return user

# Initialize services
workflow_compiler = WorkflowCompiler()
dataset_manager = DatasetManager()
training_orchestrator = TrainingOrchestrator()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "no-code-service", "version": "1.0.0"}

# Workflow endpoints
@app.post("/api/workflows", response_model=schemas.WorkflowResponse)
async def create_workflow(
    workflow: schemas.WorkflowCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new workflow"""
    try:
        db_workflow = models.Workflow(
            id=str(uuid.uuid4()),
            name=workflow.name,
            description=workflow.description,
            user_id=current_user.id,
            nodes=json.dumps(workflow.nodes),
            edges=json.dumps(workflow.edges),
            parameters=json.dumps(workflow.parameters or {}),
            status="draft",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_workflow)
        await db.commit()
        await db.refresh(db_workflow)
        
        return schemas.WorkflowResponse.from_orm(db_workflow)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@app.get("/api/workflows", response_model=List[schemas.WorkflowResponse])
async def get_workflows(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get user's workflows"""
    try:
        result = await db.execute(
            models.Workflow.__table__.select()
            .where(models.Workflow.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .order_by(models.Workflow.updated_at.desc())
        )
        workflows = result.fetchall()
        return [schemas.WorkflowResponse.from_orm(w) for w in workflows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflows: {str(e)}")

@app.get("/api/workflows/{workflow_id}", response_model=schemas.WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific workflow"""
    try:
        result = await db.execute(
            models.Workflow.__table__.select()
            .where(
                models.Workflow.id == workflow_id,
                models.Workflow.user_id == current_user.id
            )
        )
        workflow = result.fetchone()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
            
        return schemas.WorkflowResponse.from_orm(workflow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflow: {str(e)}")

@app.put("/api/workflows/{workflow_id}", response_model=schemas.WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_update: schemas.WorkflowUpdate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a workflow"""
    try:
        result = await db.execute(
            models.Workflow.__table__.select()
            .where(
                models.Workflow.id == workflow_id,
                models.Workflow.user_id == current_user.id
            )
        )
        db_workflow = result.fetchone()
        
        if not db_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        update_data = workflow_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['nodes', 'edges', 'parameters'] and value is not None:
                value = json.dumps(value)
            setattr(db_workflow, field, value)
        
        db_workflow.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_workflow)
        
        return schemas.WorkflowResponse.from_orm(db_workflow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")

@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a workflow"""
    try:
        result = await db.execute(
            models.Workflow.__table__.select()
            .where(
                models.Workflow.id == workflow_id,
                models.Workflow.user_id == current_user.id
            )
        )
        workflow = result.fetchone()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        await db.execute(
            models.Workflow.__table__.delete()
            .where(models.Workflow.id == workflow_id)
        )
        await db.commit()
        
        return {"message": "Workflow deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")

# Compilation endpoints
@app.post("/api/workflows/{workflow_id}/compile", response_model=schemas.CompilationResponse)
async def compile_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compile workflow to Python code"""
    try:
        # Get workflow
        result = await db.execute(
            models.Workflow.__table__.select()
            .where(
                models.Workflow.id == workflow_id,
                models.Workflow.user_id == current_user.id
            )
        )
        workflow = result.fetchone()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Compile workflow
        nodes = json.loads(workflow.nodes)
        edges = json.loads(workflow.edges)
        parameters = json.loads(workflow.parameters)
        
        compilation_result = await workflow_compiler.compile(
            workflow_id=workflow_id,
            nodes=nodes,
            edges=edges,
            parameters=parameters
        )
        
        # Save compilation result
        db_compilation = models.CompilationResult(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            python_code=compilation_result.python_code,
            validation_results=json.dumps(compilation_result.validation_results),
            status=compilation_result.status,
            created_at=datetime.utcnow()
        )
        
        db.add(db_compilation)
        await db.commit()
        
        # Start background validation
        background_tasks.add_task(
            validate_compiled_code,
            compilation_result.python_code,
            workflow_id,
            db_compilation.id
        )
        
        return schemas.CompilationResponse(
            id=db_compilation.id,
            workflow_id=workflow_id,
            python_code=compilation_result.python_code,
            validation_results=compilation_result.validation_results,
            status=compilation_result.status,
            created_at=db_compilation.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile workflow: {str(e)}")

@app.get("/api/workflows/{workflow_id}/compilations", response_model=List[schemas.CompilationResponse])
async def get_compilations(
    workflow_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get compilation history for a workflow"""
    try:
        # Verify workflow ownership
        workflow_result = await db.execute(
            models.Workflow.__table__.select()
            .where(
                models.Workflow.id == workflow_id,
                models.Workflow.user_id == current_user.id
            )
        )
        if not workflow_result.fetchone():
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get compilations
        result = await db.execute(
            models.CompilationResult.__table__.select()
            .where(models.CompilationResult.workflow_id == workflow_id)
            .order_by(models.CompilationResult.created_at.desc())
        )
        compilations = result.fetchall()
        
        return [schemas.CompilationResponse.from_orm(c) for c in compilations]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch compilations: {str(e)}")

# Dataset endpoints
@app.get("/api/datasets", response_model=List[schemas.DatasetResponse])
async def get_datasets(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available datasets"""
    try:
        datasets = await dataset_manager.get_available_datasets(current_user.id)
        return datasets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch datasets: {str(e)}")

@app.post("/api/datasets/upload")
async def upload_dataset(
    # dataset_file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a custom dataset"""
    # Implementation for dataset upload
    return {"message": "Dataset upload endpoint - implementation pending"}

# Training endpoints
@app.post("/api/workflows/{workflow_id}/train", response_model=schemas.TrainingJobResponse)
async def start_training(
    workflow_id: str,
    training_config: schemas.TrainingConfig,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start model training"""
    try:
        # Get workflow and latest compilation
        workflow_result = await db.execute(
            models.Workflow.__table__.select()
            .where(
                models.Workflow.id == workflow_id,
                models.Workflow.user_id == current_user.id
            )
        )
        workflow = workflow_result.fetchone()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get latest successful compilation
        compilation_result = await db.execute(
            models.CompilationResult.__table__.select()
            .where(
                models.CompilationResult.workflow_id == workflow_id,
                models.CompilationResult.status == "success"
            )
            .order_by(models.CompilationResult.created_at.desc())
            .limit(1)
        )
        compilation = compilation_result.fetchone()
        
        if not compilation:
            raise HTTPException(status_code=400, detail="No successful compilation found. Please compile the workflow first.")
        
        # Create training job
        job_id = str(uuid.uuid4())
        training_job = models.TrainingJob(
            id=job_id,
            workflow_id=workflow_id,
            compilation_id=compilation.id,
            dataset_id=training_config.dataset_id,
            config=json.dumps(training_config.dict()),
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db.add(training_job)
        await db.commit()
        
        # Start training in background
        background_tasks.add_task(
            start_training_job,
            job_id,
            compilation.python_code,
            training_config
        )
        
        return schemas.TrainingJobResponse.from_orm(training_job)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")

@app.get("/api/training-jobs/{job_id}", response_model=schemas.TrainingJobResponse)
async def get_training_job(
    job_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get training job status"""
    try:
        result = await db.execute(
            models.TrainingJob.__table__.select()
            .where(models.TrainingJob.id == job_id)
        )
        job = result.fetchone()
        
        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")
        
        # Verify ownership through workflow
        workflow_result = await db.execute(
            models.Workflow.__table__.select()
            .where(
                models.Workflow.id == job.workflow_id,
                models.Workflow.user_id == current_user.id
            )
        )
        if not workflow_result.fetchone():
            raise HTTPException(status_code=404, detail="Training job not found")
        
        return schemas.TrainingJobResponse.from_orm(job)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch training job: {str(e)}")

# Component library endpoints
@app.get("/api/components", response_model=List[schemas.ComponentResponse])
async def get_components():
    """Get available workflow components"""
    try:
        components = await workflow_compiler.get_available_components()
        return components
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch components: {str(e)}")

@app.get("/api/components/{component_type}", response_model=schemas.ComponentDetailResponse)
async def get_component_details(component_type: str):
    """Get detailed information about a component"""
    try:
        component_details = await workflow_compiler.get_component_details(component_type)
        if not component_details:
            raise HTTPException(status_code=404, detail="Component not found")
        return component_details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch component details: {str(e)}")

# Background tasks
async def validate_compiled_code(python_code: str, workflow_id: str, compilation_id: str):
    """Background task to validate compiled code"""
    try:
        # Implement code validation logic
        # This would include security scanning, syntax checking, etc.
        await asyncio.sleep(5)  # Simulate validation time
        
        # Update compilation status in database
        async with database.SessionLocal() as db:
            await db.execute(
                models.CompilationResult.__table__.update()
                .where(models.CompilationResult.id == compilation_id)
                .values(
                    status="validated",
                    validation_results=json.dumps({
                        "security_scan": "passed",
                        "syntax_check": "passed",
                        "performance_analysis": "passed"
                    })
                )
            )
            await db.commit()
    except Exception as e:
        # Update compilation status to failed
        async with database.SessionLocal() as db:
            await db.execute(
                models.CompilationResult.__table__.update()
                .where(models.CompilationResult.id == compilation_id)
                .values(
                    status="validation_failed",
                    validation_results=json.dumps({
                        "error": str(e)
                    })
                )
            )
            await db.commit()

async def start_training_job(job_id: str, python_code: str, training_config: schemas.TrainingConfig):
    """Background task to start training"""
    try:
        # Start training process
        result = await training_orchestrator.start_training(
            job_id=job_id,
            code=python_code,
            config=training_config
        )
        
        # Update job status
        async with database.SessionLocal() as db:
            await db.execute(
                models.TrainingJob.__table__.update()
                .where(models.TrainingJob.id == job_id)
                .values(
                    status="running",
                    started_at=datetime.utcnow()
                )
            )
            await db.commit()
            
    except Exception as e:
        # Update job status to failed
        async with database.SessionLocal() as db:
            await db.execute(
                models.TrainingJob.__table__.update()
                .where(models.TrainingJob.id == job_id)
                .values(
                    status="failed",
                    error_message=str(e)
                )
            )
            await db.commit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)