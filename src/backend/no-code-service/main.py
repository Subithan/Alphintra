"""
No-Code Service - Microservice for Visual Workflow Builder
Handles workflow creation, execution, and management for trading strategies
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Body
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
import logging
from prometheus_fastapi_instrumentator import Instrumentator
import redis
import httpx
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from graphql_resolvers import Query, Mutation, Subscription
from fastapi import Query as FastAPIQuery
from pydantic import BaseModel

# Import models and schemas
from models import Base, NoCodeWorkflow, NoCodeComponent, NoCodeExecution, NoCodeTemplate, User, ExecutionHistory
from schemas_updated import *
from workflow_compiler_updated import WorkflowCompiler
from code_generator import CodeGenerator
from workflow_converter import WorkflowConverter
from clients.aiml_client import AIMLClient, AIMLServiceError, AIMLServiceUnavailable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration with K3D internal networking
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://nocode_service_user:nocode_service_pass@postgresql-primary.alphintra.svc.cluster.local:5432/alphintra_nocode"
)

# Redis configuration
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/2"
)

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service.alphintra.svc.cluster.local:8080")
AIML_SERVICE_URL = os.getenv("AIML_SERVICE_URL", "http://ai-ml-strategy-service.alphintra.svc.cluster.local:8000")

# Development mode flag
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"

# Initialize database
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize Redis
try:
    redis_client = redis.from_url(REDIS_URL)
except Exception as e:
    logger.warning(f"Redis connection failed, using fallback: {e}")
    redis_client = None

# HTTP client for service communication
http_client = httpx.AsyncClient(timeout=30.0)

# Initialize FastAPI app
app = FastAPI(
    title="Alphintra No-Code Service",
    description="Microservice for visual workflow builder and trading strategy management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for microservices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Security
security = HTTPBearer(auto_error=False)  # Don't auto-error for missing auth in dev mode

# Initialize services
workflow_compiler = WorkflowCompiler()
code_generator = CodeGenerator()
workflow_converter = WorkflowConverter()

# Request models
class CodeGenerationRequest(BaseModel):
    language: str = "python"
    framework: str = "backtesting.py"
    includeComments: bool = True

class ExecutionModeRequest(BaseModel):
    mode: str = Field(..., regex="^(strategy|model)$", description="Execution mode: 'strategy' or 'model'")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters for execution mode")

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)  # Add db dependency
):
    """Validate JWT token with Auth Service or return mock user in dev mode"""
    if DEV_MODE:
        # In development mode, create/get test user
        logger.info("Development mode: using test user")
        test_user = db.query(User).filter(User.email == "dev@alphintra.com").first()
        if not test_user:
            test_user = User(
                email="dev@alphintra.com",
                password_hash="dev_hash",
                first_name="Development",
                last_name="User",
                is_verified=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        return test_user
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = await http_client.get(f"{AUTH_SERVICE_URL}/api/v1/auth/validate", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        raise HTTPException(status_code=401, detail="Authentication service unavailable")

# Health checks
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Check database connection
        db = next(get_db())
        db.execute(text("SELECT 1"))
        
        # Check Redis connection if available
        if redis_client:
            redis_client.ping()
        
        return {
            "status": "healthy",
            "service": "no-code-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    return {
        "status": "ready",
        "service": "no-code-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "no-code-service",
        "version": "2.0.0",
        "status": "running",
        "dev_mode": DEV_MODE,
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "graphql": "/graphql",
            "workflows": "/api/workflows",
            "templates": "/api/templates",
            "executions": "/api/executions",
            "generate_code": "/api/workflows/{workflow_id}/generate-code",
            "get_generated_code": "/api/workflows/{workflow_id}/generated-code",
            "execution_mode": "/api/workflows/{workflow_id}/execution-mode",
            "create_sample_workflow": "/api/workflows/create-sample",
            "list_workflows": "/api/workflows/debug/list"
        }
    }

# Initialize services
workflow_compiler = WorkflowCompiler()

# GraphQL Schema
schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)

# GraphQL context function
async def get_graphql_context(request: Request, db: Session = Depends(get_db)):
    """Create GraphQL context with database session and user authentication"""
    current_user = None
    
    if DEV_MODE:
        # Development mode: create/get test user
        test_user = db.query(User).filter(User.email == "dev@alphintra.com").first()
        if not test_user:
            test_user = User(
                email="dev@alphintra.com",
                password_hash="dev_hash",
                first_name="Development",
                last_name="User",
                is_verified=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        current_user = test_user
    else:
        # Production mode: get user from authorization header
        authorization = request.headers.get("Authorization")
        if authorization:
            try:
                # Extract token from Authorization header
                token = authorization.replace("Bearer ", "")
                # In production, validate token with auth service
                # For now, create test user for development
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
                current_user = test_user
            except Exception:
                # Default to test user for development
                current_user = db.query(User).filter(User.email == "test@alphintra.com").first()
    
    return {
        "db_session": db,
        "current_user": current_user,
        "request": request
    }

# GraphQL Router
graphql_router = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL]
)

# Add GraphQL router to the app
app.include_router(graphql_router, prefix="/graphql")

# --- Specific routes first (must be before parameterized routes) ---

@app.post("/api/workflows/create-sample")
async def create_sample_workflow(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a sample workflow for testing"""
    try:
        sample_workflow_data = {
            "nodes": [
                {
                    "id": "data_source_1",
                    "type": "data_source",
                    "position": {"x": 100, "y": 100},
                    "data": {"symbol": "AAPL", "timeframe": "1d"}
                },
                {
                    "id": "indicator_1",
                    "type": "indicator",
                    "position": {"x": 300, "y": 100},
                    "data": {"indicator_type": "sma", "period": 20}
                },
                {
                    "id": "condition_1",
                    "type": "condition",
                    "position": {"x": 500, "y": 100},
                    "data": {"condition_type": "greater_than", "value": 150}
                },
                {
                    "id": "signal_1",
                    "type": "signal",
                    "position": {"x": 700, "y": 100},
                    "data": {"signal_type": "buy"}
                }
            ],
            "edges": [
                {"id": "edge_1", "source": "data_source_1", "target": "indicator_1"},
                {"id": "edge_2", "source": "indicator_1", "target": "condition_1"},
                {"id": "edge_3", "source": "condition_1", "target": "signal_1"}
            ]
        }
        
        workflow = NoCodeWorkflow(
            name="Sample Trading Strategy",
            description="A sample workflow for testing code generation",
            category="sample",
            tags=["sample", "test"],
            user_id=current_user.id,
            workflow_data=sample_workflow_data,
            execution_mode="backtest"
        )
        
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        
        return {
            "message": "Sample workflow created successfully",
            "workflow_id": str(workflow.uuid),
            "workflow_data": workflow.workflow_data
        }
        
    except Exception as e:
        logger.error(f"Error creating sample workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create sample workflow: {str(e)}")

@app.get("/api/workflows/debug/list")
async def list_all_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to list all workflows"""
    try:
        workflows = db.query(NoCodeWorkflow).all()
        return {
            "total_workflows": len(workflows),
            "workflows": [
                {
                    "id": w.id,
                    "uuid": str(w.uuid),
                    "name": w.name,
                    "user_id": w.user_id,
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                    "has_workflow_data": bool(w.workflow_data)
                }
                for w in workflows
            ]
        }
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

# Code Generation Endpoints (must be before general workflow/{workflow_id} routes)
@app.post("/api/workflows/{workflow_id}/generate-code")
async def generate_code(
    workflow_id: str,
    request: CodeGenerationRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate Python code from workflow data"""
    try:
        # Debug: Log the request
        logger.info(f"Generate code request for workflow_id: {workflow_id}")
        logger.info(f"Current user: {current_user}")
        logger.info(f"Generation options: {request.dict()}")
        
        # Check if workflow exists (with more detailed logging)
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id
        ).first()
        
        if not workflow:
            all_workflows = db.query(NoCodeWorkflow).all()
            logger.error(f"Workflow not found with ID: {workflow_id}")
            logger.info(f"Available workflows: {[str(w.uuid) for w in all_workflows]}")
            return {
                "workflow_id": workflow_id,
                "generated_code": "",
                "requirements": [],
                "success": False,
                "errors": [f"Workflow not found with ID: {workflow_id}"],
                "message": "Workflow not found"
            }
        
        # Generate code using the code generator
        generation_result = code_generator.generate_strategy_code(
            workflow.workflow_data or {"nodes": [], "edges": []},
            workflow.name
        )
        
        if generation_result['success']:
            # Update workflow with generated code
            workflow.generated_code = generation_result['code']
            workflow.generated_requirements = generation_result['requirements']
            workflow.compilation_status = 'generated'
            workflow.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(workflow)
            
            return {
                "workflow_id": str(workflow.uuid),
                "generated_code": generation_result['code'],
                "requirements": generation_result['requirements'],
                "metadata": generation_result['metadata'],
                "success": True,
                "message": "Code generated successfully"
            }
        else:
            # Update workflow with error status
            workflow.compilation_status = 'generation_failed'
            workflow.compilation_errors = generation_result['errors']
            workflow.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {
                "workflow_id": str(workflow.uuid),
                "generated_code": "",
                "requirements": [],
                "success": False,
                "errors": generation_result['errors'],
                "message": "Code generation failed"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate code: {str(e)}")

@app.get("/api/workflows/{workflow_id}/generated-code")
async def get_generated_code(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the generated code for a workflow"""
    try:
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "workflow_id": str(workflow.uuid),
            "workflow_name": workflow.name,
            "generated_code": workflow.generated_code or "",
            "requirements": workflow.generated_requirements or [],
            "compilation_status": workflow.compilation_status,
            "compilation_errors": workflow.compilation_errors or [],
            "last_updated": workflow.updated_at.isoformat() if workflow.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving generated code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve generated code: {str(e)}")

# --- Execution mode endpoint (new) ---

@app.post("/api/workflows/{workflow_id}/execution-mode")
async def set_execution_mode(
    workflow_id: str,
    request: ExecutionModeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set execution mode and route to appropriate handler"""
    try:
        # Validate workflow exists and user owns it
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
        # Update workflow with execution mode
        workflow.execution_mode = request.mode
        workflow.execution_metadata = request.config
        workflow.updated_at = datetime.utcnow()
        
        execution_id = str(uuid.uuid4())
        
        if request.mode == "strategy":
            # Strategy mode: Use existing code generator
            logger.info(f"Processing workflow {workflow_id} in strategy mode")
            
            generation_result = code_generator.generate_strategy_code(
                workflow.workflow_data or {"nodes": [], "edges": []},
                workflow.name
            )
            
            if generation_result['success']:
                workflow.generated_code = generation_result['code']
                workflow.generated_requirements = generation_result['requirements']
                workflow.compilation_status = 'generated'
                
                db.commit()
                
                return {
                    "execution_id": execution_id,
                    "mode": "strategy",
                    "status": "completed",
                    "next_action": f"/api/workflows/{workflow_id}/generated-code",
                    "generated_code": generation_result['code'],
                    "requirements": generation_result['requirements']
                }
            else:
                workflow.compilation_status = 'generation_failed'
                workflow.compilation_errors = generation_result['errors']
                db.commit()
                
                return {
                    "execution_id": execution_id,
                    "mode": "strategy", 
                    "status": "failed",
                    "next_action": None,
                    "errors": generation_result['errors']
                }
                
        elif request.mode == "model":
            # Model mode: Convert workflow and forward to AI-ML service
            logger.info(f"Processing workflow {workflow_id} in model mode")
            
            try:
                # Convert workflow to training configuration
                training_config = workflow_converter.convert_to_training_config(
                    workflow.workflow_data or {"nodes": [], "edges": []}
                )
                
                # Create AI-ML client and submit training job
                async with AIMLClient(AIML_SERVICE_URL) as aiml_client:
                    training_job_response = await aiml_client.create_training_job_from_workflow(
                        workflow_definition=workflow.workflow_data,
                        workflow_name=workflow.name,
                        user_id=str(current_user.id),
                        config=request.config
                    )
                
                # Update workflow status
                workflow.compilation_status = 'training_submitted'
                training_job_id = training_job_response.get('training_job_id')
                workflow.aiml_training_job_id = training_job_id
                
                db.commit()
                
                return {
                    "execution_id": execution_id,
                    "mode": "model",
                    "status": "training_submitted",
                    "next_action": f"/api/training/jobs/{training_job_id}/status",
                    "training_job_id": training_job_id,
                    "estimated_duration": training_job_response.get('estimated_duration'),
                    "message": "Training job successfully submitted to AI-ML service"
                }
                
            except (AIMLServiceUnavailable, AIMLServiceError) as e:
                # Handle AI-ML service errors gracefully
                logger.error(f"AI-ML service error for workflow {workflow_id}: {str(e)}")
                workflow.compilation_status = 'training_failed'
                workflow.compilation_errors = [str(e)]
                db.commit()
                
                return {
                    "execution_id": execution_id,
                    "mode": "model",
                    "status": "failed",
                    "next_action": None,
                    "errors": [str(e)],
                    "message": "Failed to submit training job to AI-ML service"
                }
            except Exception as e:
                # Handle workflow conversion errors
                logger.error(f"Workflow conversion error for {workflow_id}: {str(e)}")
                workflow.compilation_status = 'conversion_failed'  
                workflow.compilation_errors = [str(e)]
                db.commit()
                
                return {
                    "execution_id": execution_id,
                    "mode": "model",
                    "status": "failed", 
                    "next_action": None,
                    "errors": [str(e)],
                    "message": "Failed to convert workflow to training configuration"
                }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting execution mode for workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set execution mode: {str(e)}")

# --- General workflow routes (after specific routes) ---

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
    skip: int = FastAPIQuery(0, ge=0),
    limit: int = FastAPIQuery(100, le=1000),
    category: Optional[str] = None,
    is_public: Optional[bool] = None
):
    """Get user's workflows with filtering"""
    try:
        # In dev mode, use user_id=2 for testing
        user_id_to_use = 2 if DEV_MODE else current_user.id
        
        query = db.query(NoCodeWorkflow).filter(
            (NoCodeWorkflow.user_id == user_id_to_use) | 
            (NoCodeWorkflow.is_public == True)
        )
        
        if category:
            query = query.filter(NoCodeWorkflow.category == category)
        if is_public is not None:
            query = query.filter(NoCodeWorkflow.is_public == is_public)
            
        workflows = query.order_by(NoCodeWorkflow.updated_at.desc()).offset(skip).limit(limit).all()
        return [WorkflowResponse.from_orm(w) for w in workflows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflows: {str(e)}")

@app.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific workflow by ID"""
    try:
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            (NoCodeWorkflow.user_id == current_user.id) | 
            (NoCodeWorkflow.is_public == True)
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
    """Update an existing workflow"""
    try:
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update fields that are provided
        update_data = workflow_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
        
        return WorkflowResponse.from_orm(workflow)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow: {str(e)}")
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
        logger.error(f"Error deleting workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")

# Existing Code Generation Endpoints
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
    uvicorn.run(app, host="0.0.0.0", port=8006)  # Use port 8006 for no-code service