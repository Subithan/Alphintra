#!/usr/bin/env python3
"""
Production server for no-code service with PostgreSQL database connection
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
import os
import sys

# Import models and schemas
from models import Base, User, NoCodeWorkflow, NoCodeComponent, NoCodeExecution, NoCodeTemplate
from schemas_updated import WorkflowResponse, WorkflowCreate, WorkflowUpdate

# Database configuration for k3d PostgreSQL with connection pooling
# Using Kubernetes service directly instead of port forwarding
DATABASE_URL = "postgresql://alphintra:alphintra@10.43.22.175:5432/alphintra"
engine = create_engine(
    DATABASE_URL, 
    echo=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Alphintra No-Code Service (Production)", 
    description="Production no-code service with PostgreSQL database",
    version="2.0.0-production"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """Get or create test user for development"""
    try:
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
    except Exception as e:
        print(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

# Initialize database tables
def init_database():
    """Initialize database tables"""
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        
        # Create test data
        db = SessionLocal()
        try:
            # Create test user if not exists
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
                print("✅ Test user created")
            
            # Create test components if not exist
            if db.query(NoCodeComponent).count() == 0:
                test_components = [
                    NoCodeComponent(
                        name="RSI Indicator",
                        display_name="RSI Indicator",
                        description="Relative Strength Index technical indicator",
                        category="indicators",
                        component_type="indicator",
                        input_schema={"price": "number"},
                        output_schema={"rsi": "number"},
                        parameters_schema={"period": "number"},
                        default_parameters={"period": 14},
                        code_template="# RSI calculation code",
                        imports_required=["pandas", "numpy"]
                    ),
                    NoCodeComponent(
                        name="Moving Average",
                        display_name="Moving Average",
                        description="Simple Moving Average indicator",
                        category="indicators",
                        component_type="indicator",
                        input_schema={"price": "number"},
                        output_schema={"ma": "number"},
                        parameters_schema={"period": "number"},
                        default_parameters={"period": 20},
                        code_template="# MA calculation code",
                        imports_required=["pandas", "numpy"]
                    )
                ]
                for component in test_components:
                    db.add(component)
                db.commit()
                print("✅ Test components created")
            
            # Create test templates if not exist
            if db.query(NoCodeTemplate).count() == 0:
                test_template = NoCodeTemplate(
                    name="Basic RSI Strategy",
                    description="A template for RSI-based trading strategies",
                    category="momentum",
                    template_data={"nodes": [], "edges": []},
                    author_id=test_user.id,
                    is_public=True
                )
                db.add(test_template)
                db.commit()
                print("✅ Test template created")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
        finally:
            db.close()
            
        return {
            "status": "healthy",
            "service": "no-code-service-production",
            "version": "2.0.0-production",
            "database": db_status
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "no-code-service-production",
            "error": str(e)
        }

# Workflow Management Endpoints
@app.post("/api/workflows")
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
        
        return {
            "id": db_workflow.id,
            "uuid": str(db_workflow.uuid),
            "name": db_workflow.name,
            "description": db_workflow.description,
            "category": db_workflow.category,
            "workflow_data": db_workflow.workflow_data,
            "created_at": db_workflow.created_at.isoformat() if db_workflow.created_at else None,
            "updated_at": db_workflow.updated_at.isoformat() if db_workflow.updated_at else None
        }
    except Exception as e:
        print(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@app.get("/api/workflows")
async def get_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    category: Optional[str] = None
):
    """Get user's workflows with filtering"""
    try:
        query = db.query(NoCodeWorkflow).filter(
            (NoCodeWorkflow.user_id == current_user.id) | 
            (NoCodeWorkflow.is_public == True)
        )
        
        if category:
            query = query.filter(NoCodeWorkflow.category == category)
            
        workflows = query.order_by(NoCodeWorkflow.updated_at.desc()).offset(skip).limit(limit).all()
        
        return [
            {
                "id": w.id,
                "uuid": str(w.uuid),
                "name": w.name,
                "description": w.description,
                "category": w.category,
                "workflow_data": w.workflow_data,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None
            }
            for w in workflows
        ]
    except Exception as e:
        print(f"Error fetching workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflows: {str(e)}")

@app.get("/api/workflows/{workflow_id}")
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
            
        return {
            "id": workflow.id,
            "uuid": str(workflow.uuid),
            "name": workflow.name,
            "description": workflow.description,
            "category": workflow.category,
            "workflow_data": workflow.workflow_data,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflow: {str(e)}")

@app.put("/api/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    workflow_data: dict,
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
        
        # Update fields
        if "name" in workflow_data:
            workflow.name = workflow_data["name"]
        if "description" in workflow_data:
            workflow.description = workflow_data["description"]
        if "category" in workflow_data:
            workflow.category = workflow_data["category"]
        if "workflow_data" in workflow_data:
            workflow.workflow_data = workflow_data["workflow_data"]
        
        workflow.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(workflow)
        
        return {
            "id": workflow.id,
            "uuid": str(workflow.uuid),
            "name": workflow.name,
            "description": workflow.description,
            "category": workflow.category,
            "workflow_data": workflow.workflow_data,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")

@app.get("/api/components")
async def get_components(
    db: Session = Depends(get_db),
    category: Optional[str] = None
):
    """Get available components"""
    try:
        query = db.query(NoCodeComponent)
        
        if category:
            query = query.filter(NoCodeComponent.category == category)
            
        components = query.all()
        
        return [
            {
                "id": c.id,
                "uuid": str(c.uuid),
                "name": c.name,
                "display_name": c.display_name,
                "description": c.description,
                "category": c.category,
                "component_type": c.component_type,
                "input_schema": c.input_schema,
                "output_schema": c.output_schema,
                "parameters_schema": c.parameters_schema,
                "default_parameters": c.default_parameters
            }
            for c in components
        ]
    except Exception as e:
        print(f"Error fetching components: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch components: {str(e)}")

@app.get("/api/templates")
async def get_templates(
    db: Session = Depends(get_db),
    category: Optional[str] = None
):
    """Get available templates"""
    try:
        query = db.query(NoCodeTemplate).filter(NoCodeTemplate.is_public == True)
        
        if category:
            query = query.filter(NoCodeTemplate.category == category)
            
        templates = query.all()
        
        return [
            {
                "id": t.id,
                "uuid": str(t.uuid),
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "template_data": t.template_data
            }
            for t in templates
        ]
    except Exception as e:
        print(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Alphintra No-Code Service Production Server",
        "version": "2.0.0-production",
        "database": "PostgreSQL",
        "endpoints": {
            "health": "/health",
            "workflows": "/api/workflows",
            "components": "/api/components",
            "templates": "/api/templates"
        }
    }

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Check for port argument
    port = 8006
    if len(sys.argv) > 1 and sys.argv[1] == "--port" and len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            port = 8006
    
    print(f"🚀 Starting Production Server on port {port}...")
    print(f"📊 Database: {DATABASE_URL}")
    uvicorn.run(app, host="0.0.0.0", port=port)