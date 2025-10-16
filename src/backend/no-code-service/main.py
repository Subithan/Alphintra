"""
No-Code Service - Microservice for Visual Workflow Builder
Handles workflow creation, execution, and management for trading strategies
"""

from fastapi import HTTPException, Depends, Request, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import uuid
from datetime import datetime
import logging
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from graphql_resolvers import Query, Mutation, Subscription
from pydantic import BaseModel

from app import create_app
from app.api import register_routes
from app.core.config import get_settings
from app.core.db import get_db, SessionLocal
from app.core.dependencies import get_current_user
from app.core.redis import get_redis_client

# Import models and schemas
from models import NoCodeWorkflow, User, ExecutionHistory
from schemas_updated import *
from workflow_compiler_updated import WorkflowCompiler
from database_strategy_handler import execute_database_strategy_mode
from workflow_converter import WorkflowConverter
from clients.aiml_client import AIMLClient, AIMLServiceError, AIMLServiceUnavailable
from clients.backtest_client import BacktestClient, BacktestServiceError, BacktestServiceUnavailable

settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize dependencies
redis_client = get_redis_client()

# Initialize FastAPI app
app = create_app()
register_routes(app)

# Initialize services
workflow_compiler = WorkflowCompiler()
workflow_converter = WorkflowConverter()
backtest_client = BacktestClient()

# Request models
class CodeGenerationRequest(BaseModel):
    language: str = "python"
    framework: str = "backtesting.py"
    includeComments: bool = True

class ExecutionModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(strategy|model|hybrid|backtesting|paper_trading|research)$", description="Execution mode")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters for execution mode")

# Health checks
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Check database connection
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))

        # Check Redis connection if available
        if redis_client:
            redis_client.ping()

        return {
            "status": "healthy",
            "service": "no-code-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.version,
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
        "version": settings.version,
        "status": "running",
        "dev_mode": settings.dev_mode,
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
            "list_workflows": "/api/workflows/debug/list",
            "list_strategies": "/api/workflows/strategies/list",
            "strategy_details": "/api/workflows/{workflow_id}/strategy-details",
            "strategy_database_overview": "/api/workflows/strategies/database-overview"
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

    if settings.dev_mode:
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

        # Generate code using database strategy handler
        generation_result = execute_database_strategy_mode(
            workflow=workflow,
            execution_config={"optimization_level": 2},
            db=db
        )

        if generation_result['success']:
            return {
                "workflow_id": str(workflow.uuid),
                "generated_code": workflow.generated_code,
                "requirements": workflow.generated_requirements or [],
                "metadata": generation_result.get('strategy_details', {}),
                "success": True,
                "message": "Code generated successfully"
            }
        else:
            return {
                "workflow_id": str(workflow.uuid),
                "generated_code": "",
                "requirements": [],
                "success": False,
                "errors": [generation_result.get('error', 'Unknown error')],
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
        # Find workflow with flexible UUID handling (same as update_workflow)
        workflow = None

        # Check if workflow_id is a valid UUID format
        try:
            import uuid as uuid_module
            uuid_module.UUID(workflow_id)  # This will raise ValueError if not a valid UUID

            # It's a valid UUID, try to find the workflow
            workflow = db.query(NoCodeWorkflow).filter(
                NoCodeWorkflow.uuid == workflow_id,
                NoCodeWorkflow.user_id == current_user.id
            ).first()
        except ValueError:
            # Not a valid UUID, this might be a template ID or custom identifier
            # For execution mode, we need to create a workflow if it doesn't exist
            logger.info(f"Looking for workflow with non-UUID identifier for execution: {workflow_id}")
            workflow = None

        if not workflow:
            # Create a basic workflow for execution if none exists
            # This handles template-based workflows from the frontend
            workflow = NoCodeWorkflow(
                name=f"Template Workflow {workflow_id}",
                description="Auto-created for execution",
                category="trading_strategy",
                tags=["template", "auto-created"],
                user_id=current_user.id,
                workflow_data={"nodes": [], "edges": []},
                execution_mode=request.mode,
                execution_metadata=request.config,
                version=1,
                is_template=False,
                is_public=False
            )
            db.add(workflow)
            db.commit()
            db.refresh(workflow)
            logger.info(f"Created new workflow for execution with UUID: {workflow.uuid}")

        # Update workflow with execution mode
        workflow.execution_mode = request.mode
        workflow.execution_metadata = request.config
        workflow.updated_at = datetime.utcnow()

        execution_id = str(uuid.uuid4())

        if request.mode == "strategy":
            # Enhanced Strategy mode: Use Enhanced Compiler with organized file storage
            logger.info(f"Processing workflow {workflow_id} in enhanced strategy mode")

            try:
                # Use Database Strategy Handler (no file storage)
                strategy_result = execute_database_strategy_mode(
                    workflow=workflow,
                    execution_config=request.config,
                    db=db
                )

                if strategy_result['success']:
                    # Strategy generated and saved successfully to database
                    logger.info(f"Database strategy generated successfully for workflow {workflow_id}")
                    
                    response = {
                        "execution_id": strategy_result['execution_id'],
                        "mode": "strategy", 
                        "status": "completed",
                        "message": strategy_result['message'],
                        "next_action": f"/api/workflows/{workflow_id}/generated-code",
                        "strategy_details": {
                            "workflow_id": strategy_result['strategy_details']['workflow_id'],
                            "workflow_uuid": strategy_result['strategy_details']['workflow_uuid'],
                            "code_lines": strategy_result['strategy_details']['code_lines'],
                            "code_size_bytes": strategy_result['strategy_details']['code_size_bytes'],
                            "requirements": strategy_result['strategy_details']['requirements'],
                            "compilation_stats": strategy_result['strategy_details']['compilation_stats'],
                            "storage": strategy_result['strategy_details']['storage'],
                            "compiler_version": strategy_result['strategy_details']['compiler_version']
                        },
                        "database_storage": strategy_result['database_storage'],
                        "execution_record_id": strategy_result['execution_record_id']
                    }
                    
                    # Include auto-backtest results if available
                    if 'auto_backtest' in strategy_result:
                        response['auto_backtest'] = strategy_result['auto_backtest']
                        
                        # Update message if backtest was successful
                        if strategy_result['auto_backtest'].get('success'):
                            response['message'] = f"{strategy_result['message']} + Auto-backtest completed successfully"
                            response['backtest_performance'] = strategy_result['auto_backtest']['performance_metrics']
                            response['next_actions'] = {
                                "view_code": f"/api/workflows/{workflow_id}/generated-code",
                                "view_backtest_results": f"/api/executions/{strategy_result['auto_backtest']['execution_id']}/details",
                                "manual_backtest": f"/api/workflows/{workflow_id}/backtest"
                            }
                        else:
                            response['message'] = f"{strategy_result['message']} (Auto-backtest: {strategy_result['auto_backtest'].get('error', 'Failed')})"
                    
                    return response
                else:
                    # Strategy generation failed
                    logger.error(f"Enhanced strategy generation failed: {strategy_result.get('error', 'Unknown error')}")
                    
                    return {
                        "execution_id": strategy_result['execution_id'],
                        "mode": "strategy",
                        "status": "failed", 
                        "error": strategy_result.get('error', 'Strategy generation failed'),
                        "details": strategy_result.get('details', {}),
                        "next_action": None
                    }
                    
            except Exception as e:
                logger.error(f"Exception in enhanced strategy mode: {str(e)}")
                workflow.compilation_status = 'generation_failed'
                workflow.compilation_errors = [{"type": "exception", "message": str(e)}]
                db.commit()
                
                return {
                    "execution_id": str(uuid.uuid4()),
                    "mode": "strategy",
                    "status": "failed",
                    "error": f"Strategy execution failed: {str(e)}",
                    "next_action": None
                }

        elif request.mode == "model":
            # Model mode: Convert workflow and forward to AI-ML service
            logger.info(f"Processing workflow {workflow_id} in model mode")

            try:
                # Create AI-ML client and submit training job
                async with AIMLClient(settings.aiml_service_url) as aiml_client:
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
                logger.error(f"AI-ML service error for workflow {workflow_id}: {str(e)}")
                raise HTTPException(status_code=503, detail=f"AI-ML service unavailable: {e}")
            except Exception as e:
                logger.error(f"Error in model mode for {workflow_id}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        else:
            # Handle other modes by forwarding to AI-ML service
            logger.info(f"Processing workflow {workflow_id} in {request.mode} mode")
            try:
                async with AIMLClient(settings.aiml_service_url) as aiml_client:
                    if request.mode == "hybrid":
                        response = await aiml_client.start_hybrid_execution(workflow.workflow_data, request.config)
                    elif request.mode == "backtesting":
                        response = await aiml_client.start_backtest(workflow.workflow_data, request.config)
                    elif request.mode == "paper_trading":
                        response = await aiml_client.start_paper_trading(workflow.workflow_data, request.config)
                    elif request.mode == "research":
                        response = await aiml_client.start_research_session(workflow.workflow_data, request.config)
                    else:
                        raise HTTPException(status_code=400, detail=f"Unsupported mode: {request.mode}")

                db.commit() # Commit changes to execution_mode and metadata
                return response

            except (AIMLServiceUnavailable, AIMLServiceError) as e:
                logger.error(f"AI-ML service error for workflow {workflow_id} in {request.mode} mode: {str(e)}")
                raise HTTPException(status_code=503, detail=f"AI-ML service unavailable: {e}")
            except Exception as e:
                logger.error(f"Error in {request.mode} mode for {workflow_id}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting execution mode for workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set execution mode: {str(e)}")

# --- Enhanced Strategy Management Routes ---
@app.get("/api/workflows/strategies/list")
async def list_user_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all generated strategies for the current user (from database)"""
    from database_strategy_handler import DatabaseStrategyHandler
    
    try:
        handler = DatabaseStrategyHandler()
        strategies = handler.list_user_strategies(current_user.id, db)
        
        if strategies['success']:
            return {
                "success": True,
                "strategies": strategies['strategies'],
                "total_count": strategies['total_count'],
                "storage_info": strategies['storage_info']
            }
        else:
            raise HTTPException(status_code=500, detail=strategies['error'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing user strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


@app.get("/api/workflows/{workflow_id}/strategy-details")
async def get_strategy_details(
    workflow_id: str,
    include_code: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a generated strategy from database"""
    from database_strategy_handler import get_strategy_from_database
    
    try:
        # Convert workflow_id to int if it's numeric, otherwise find by UUID
        try:
            workflow_id_int = int(workflow_id)
        except ValueError:
            # If it's a UUID, find the workflow first
            workflow = db.query(NoCodeWorkflow).filter(
                NoCodeWorkflow.uuid == workflow_id
            ).first()
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            workflow_id_int = workflow.id
        
        details = get_strategy_from_database(workflow_id_int, db, include_code)
        
        if not details['success']:
            raise HTTPException(status_code=404, detail=details['error'])
            
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategy details: {str(e)}")


@app.get("/api/workflows/strategies/database-overview")  
async def get_strategy_database_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overview of generated strategies in database"""
    from database_strategy_handler import DatabaseStrategyHandler
    
    try:
        handler = DatabaseStrategyHandler()
        strategies = handler.list_user_strategies(current_user.id, db)
        
        if strategies['success']:
            return {
                "success": True,
                "database_overview": {
                    "total_strategies": strategies['total_count'],
                    "storage_type": "database",
                    "storage_info": strategies['storage_info'],
                    "recent_strategies": strategies['strategies'][:5]  # Show 5 most recent
                }
            }
        else:
            raise HTTPException(status_code=500, detail=strategies['error'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy database overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get database overview: {str(e)}")

# Backtest Endpoints (calls backtest microservice)
@app.post("/api/workflows/{workflow_id}/backtest")
async def run_workflow_backtest(
    workflow_id: str,
    backtest_config: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run backtest for a workflow's generated strategy using backtest microservice.
    
    Expected backtest_config:
    {
        "start_date": "2023-01-01",
        "end_date": "2023-12-31", 
        "initial_capital": 10000,
        "commission": 0.001,
        "symbols": ["AAPL"],
        "timeframe": "1h"
    }
    """
    try:
        # Find workflow
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        if not workflow.generated_code:
            raise HTTPException(
                status_code=400, 
                detail="No generated code found. Please generate strategy code first using execution-mode endpoint."
            )

        # Validate backtest configuration
        required_fields = ['start_date', 'end_date']
        for field in required_fields:
            if field not in backtest_config:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # Set defaults for optional fields
        backtest_config.setdefault('initial_capital', 10000.0)
        backtest_config.setdefault('commission', 0.001)
        backtest_config.setdefault('symbols', ['AAPL'])
        backtest_config.setdefault('timeframe', '1h')

        # Call backtest microservice
        logger.info(f"Calling backtest service for workflow {workflow_id}")
        
        try:
            result = await backtest_client.run_backtest(
                workflow_id=workflow_id,
                strategy_code=workflow.generated_code,
                config=backtest_config,
                metadata={
                    'workflow_name': workflow.name,
                    'compilation_status': workflow.compilation_status,
                    'compiler_version': getattr(workflow, 'compiler_version', 'Enhanced v2.0'),
                    'generated_code_lines': getattr(workflow, 'generated_code_lines', 0),
                    'generated_code_size': getattr(workflow, 'generated_code_size', 0)
                }
            )
            
            if result.get('success'):
                # Save backtest record to execution history
                try:
                    execution_record = ExecutionHistory(
                        uuid=result['execution_id'],
                        workflow_id=workflow.id,
                        execution_mode='backtest',
                        status='completed',
                        execution_config=backtest_config,
                        results=result,
                        generated_code=workflow.generated_code,
                        generated_requirements=workflow.generated_requirements or [],
                        compilation_stats={
                            'backtest_service_execution': True,
                            'execution_time': datetime.utcnow().isoformat(),
                            'service_url': backtest_client.base_url
                        },
                        created_at=datetime.utcnow(),
                        completed_at=datetime.utcnow()
                    )
                    
                    db.add(execution_record)
                    db.commit()
                    
                    # Update workflow stats
                    workflow.total_executions = (workflow.total_executions or 0) + 1
                    if result.get('performance_metrics', {}).get('total_return_percent', 0) > 0:
                        workflow.successful_executions = (workflow.successful_executions or 0) + 1
                    workflow.last_execution_at = datetime.utcnow()
                    db.commit()
                    
                except Exception as db_error:
                    logger.warning(f"Failed to save execution history: {db_error}")
                    # Continue anyway - backtest succeeded
                
                logger.info(f"Backtest completed successfully for workflow {workflow_id}")
                return {
                    "message": "Backtest completed successfully",
                    "workflow_id": workflow_id,
                    "execution_id": result['execution_id'],
                    "performance_metrics": result['performance_metrics'],
                    "trade_summary": result['trade_summary'],
                    "market_data_stats": result['market_data_stats'],
                    "backtest_config": result['execution_config'],
                    "service_info": {
                        "backtest_service_url": backtest_client.base_url,
                        "execution_method": "microservice"
                    }
                }
            else:
                logger.error(f"Backtest failed for workflow {workflow_id}: {result.get('error')}")
                return {
                    "message": "Backtest failed",
                    "workflow_id": workflow_id,
                    "error": result.get('error', 'Unknown error'),
                    "success": False
                }
                
        except BacktestServiceUnavailable as e:
            logger.error(f"Backtest service unavailable: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Backtest service is currently unavailable. Please try again later."
            )
        
        except BacktestServiceError as e:
            logger.error(f"Backtest service error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Backtest failed: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/backtest/symbols")
async def get_backtest_symbols():
    """Get available symbols for backtesting from backtest service."""
    try:
        symbols = await backtest_client.get_available_symbols()
        return symbols
    except BacktestServiceUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Backtest service is currently unavailable"
        )
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backtest/health")
async def check_backtest_service_health():
    """Check health of backtest service."""
    try:
        is_healthy = await backtest_client.health_check()
        return {
            "backtest_service": "healthy" if is_healthy else "unhealthy",
            "service_url": backtest_client.base_url,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "backtest_service": "error",
            "error": str(e),
            "service_url": backtest_client.base_url,
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)  # Use port 8006 for no-code service
