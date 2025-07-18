import strawberry
from strawberry.types import Info
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from models import NoCodeWorkflow, NoCodeExecution, NoCodeComponent, NoCodeTemplate, User
from schemas_updated import WorkflowCreate, WorkflowUpdate, ExecutionCreate
from graphql_schema import (
    Workflow, Execution, Component, Template, CompilationResult, WorkflowHistory,
    WorkflowsConnection, ExecutionsConnection,
    WorkflowCreateInput, WorkflowUpdateInput, ExecutionCreateInput, WorkflowFilters, ExecutionFilters,
    convert_db_workflow_to_graphql, convert_db_execution_to_graphql, 
    convert_db_component_to_graphql, convert_db_template_to_graphql,
    convert_workflow_input_to_dict
)
from workflow_compiler_updated import WorkflowCompiler
import asyncio
import json
from contextlib import asynccontextmanager

# Get database session from context
def get_db_session(info: Info) -> Session:
    return info.context["db_session"]

# Get current user from context
def get_current_user(info: Info) -> User:
    return info.context["current_user"]

# Initialize workflow compiler
workflow_compiler = WorkflowCompiler()

@strawberry.type
class Query:
    @strawberry.field
    def workflows(
        self,
        info: Info,
        filters: Optional[WorkflowFilters] = None
    ) -> WorkflowsConnection:
        """Get workflows with filtering and pagination"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        # Build base query
        query = db.query(NoCodeWorkflow).filter(
            or_(
                NoCodeWorkflow.user_id == current_user.id,
                NoCodeWorkflow.is_public == True
            )
        )
        
        # Apply filters
        if filters:
            if filters.category:
                query = query.filter(NoCodeWorkflow.category == filters.category)
            if filters.is_public is not None:
                query = query.filter(NoCodeWorkflow.is_public == filters.is_public)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        NoCodeWorkflow.name.ilike(search_term),
                        NoCodeWorkflow.description.ilike(search_term)
                    )
                )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        if filters:
            if filters.skip:
                query = query.offset(filters.skip)
            if filters.limit:
                query = query.limit(filters.limit)
            else:
                query = query.limit(100)  # Default limit
        else:
            query = query.limit(100)
        
        # Execute query
        workflows = query.order_by(NoCodeWorkflow.updated_at.desc()).all()
        
        # Convert to GraphQL types
        graphql_workflows = [convert_db_workflow_to_graphql(w) for w in workflows]
        
        has_more = (filters.skip or 0) + len(workflows) < total
        
        return WorkflowsConnection(
            workflows=graphql_workflows,
            total=total,
            hasMore=has_more
        )
    
    @strawberry.field
    def workflow(
        self,
        info: Info,
        workflow_id: str
    ) -> Optional[Workflow]:
        """Get a specific workflow by ID"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            or_(
                NoCodeWorkflow.user_id == current_user.id,
                NoCodeWorkflow.is_public == True
            )
        ).first()
        
        if not workflow:
            return None
        
        return convert_db_workflow_to_graphql(workflow)
    
    @strawberry.field
    def executions(
        self,
        info: Info,
        workflow_id: Optional[str] = None,
        filters: Optional[ExecutionFilters] = None
    ) -> ExecutionsConnection:
        """Get executions with filtering and pagination"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        # Build base query
        query = db.query(NoCodeExecution).filter(
            NoCodeExecution.user_id == current_user.id
        )
        
        # Filter by workflow if specified
        if workflow_id:
            workflow = db.query(NoCodeWorkflow).filter(
                NoCodeWorkflow.uuid == workflow_id,
                NoCodeWorkflow.user_id == current_user.id
            ).first()
            if workflow:
                query = query.filter(NoCodeExecution.workflow_id == workflow.id)
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.filter(NoCodeExecution.status == filters.status)
            if filters.execution_type:
                query = query.filter(NoCodeExecution.execution_type == filters.execution_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        if filters:
            if filters.skip:
                query = query.offset(filters.skip)
            if filters.limit:
                query = query.limit(filters.limit)
            else:
                query = query.limit(100)  # Default limit
        else:
            query = query.limit(100)
        
        # Execute query
        executions = query.order_by(NoCodeExecution.created_at.desc()).all()
        
        # Convert to GraphQL types
        graphql_executions = [convert_db_execution_to_graphql(e) for e in executions]
        
        has_more = (filters.skip or 0) + len(executions) < total
        
        return ExecutionsConnection(
            executions=graphql_executions,
            total=total,
            hasMore=has_more
        )
    
    @strawberry.field
    def execution(
        self,
        info: Info,
        execution_id: str
    ) -> Optional[Execution]:
        """Get a specific execution by ID"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        execution = db.query(NoCodeExecution).filter(
            NoCodeExecution.uuid == execution_id,
            NoCodeExecution.user_id == current_user.id
        ).first()
        
        if not execution:
            return None
        
        return convert_db_execution_to_graphql(execution)
    
    @strawberry.field
    def components(
        self,
        info: Info,
        category: Optional[str] = None,
        is_builtin: Optional[bool] = None
    ) -> List[Component]:
        """Get available workflow components"""
        db = get_db_session(info)
        
        query = db.query(NoCodeComponent).filter(
            NoCodeComponent.is_public == True
        )
        
        if category:
            query = query.filter(NoCodeComponent.category == category)
        if is_builtin is not None:
            query = query.filter(NoCodeComponent.is_builtin == is_builtin)
        
        components = query.order_by(NoCodeComponent.category, NoCodeComponent.name).all()
        
        return [convert_db_component_to_graphql(c) for c in components]
    
    @strawberry.field
    def templates(
        self,
        info: Info,
        category: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        is_featured: Optional[bool] = None
    ) -> List[Template]:
        """Get available workflow templates"""
        db = get_db_session(info)
        
        query = db.query(NoCodeTemplate).filter(
            NoCodeTemplate.is_public == True
        )
        
        if category:
            query = query.filter(NoCodeTemplate.category == category)
        if difficulty_level:
            query = query.filter(NoCodeTemplate.difficulty_level == difficulty_level)
        if is_featured is not None:
            query = query.filter(NoCodeTemplate.is_featured == is_featured)
        
        templates = query.order_by(NoCodeTemplate.rating.desc()).all()
        
        return [convert_db_template_to_graphql(t) for t in templates]
    
    @strawberry.field
    def workflow_history(
        self,
        info: Info,
        workflow_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[WorkflowHistory]:
        """Get workflow history and activity"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        # Verify user owns workflow
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            return []
        
        # Mock history data for now - in production, this would come from an audit log table
        history = [
            WorkflowHistory(
                id="1",
                action_type="created",
                description="Model created",
                user_name=f"{current_user.first_name} {current_user.last_name}",
                version=1,
                timestamp=workflow.created_at,
                metadata={"nodes": 0, "edges": 0}
            ),
            WorkflowHistory(
                id="2",
                action_type="updated",
                description="Model updated",
                user_name=f"{current_user.first_name} {current_user.last_name}",
                version=workflow.version,
                timestamp=workflow.updated_at,
                metadata={"nodes": len(workflow.workflow_data.get("nodes", [])), "edges": len(workflow.workflow_data.get("edges", []))}
            )
        ]
        
        # Apply pagination
        if offset:
            history = history[offset:]
        if limit:
            history = history[:limit]
        
        return history

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_workflow(
        self,
        info: Info,
        input: WorkflowCreateInput
    ) -> Workflow:
        """Create a new workflow"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        # Convert input to database model
        workflow_data = {}
        if input.workflow_data:
            workflow_data = convert_workflow_input_to_dict(input.workflow_data)
        
        db_workflow = NoCodeWorkflow(
            name=input.name,
            description=input.description,
            category=input.category or 'custom',
            tags=input.tags or [],
            user_id=current_user.id,
            workflow_data=workflow_data,
            execution_mode=input.execution_mode or 'backtest'
        )
        
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        
        return convert_db_workflow_to_graphql(db_workflow)
    
    @strawberry.mutation
    def update_workflow(
        self,
        info: Info,
        workflow_id: str,
        input: WorkflowUpdateInput
    ) -> Optional[Workflow]:
        """Update an existing workflow"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            return None
        
        # Update fields
        if input.name is not None:
            workflow.name = input.name
        if input.description is not None:
            workflow.description = input.description
        if input.category is not None:
            workflow.category = input.category
        if input.tags is not None:
            workflow.tags = input.tags
        if input.workflow_data is not None:
            workflow.workflow_data = convert_workflow_input_to_dict(input.workflow_data)
        if input.execution_mode is not None:
            workflow.execution_mode = input.execution_mode
        if input.is_public is not None:
            workflow.is_public = input.is_public
        
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
        
        return convert_db_workflow_to_graphql(workflow)
    
    @strawberry.mutation
    def delete_workflow(
        self,
        info: Info,
        workflow_id: str
    ) -> bool:
        """Delete a workflow"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            return False
        
        db.delete(workflow)
        db.commit()
        
        return True
    
    @strawberry.mutation
    async def compile_workflow(
        self,
        info: Info,
        workflow_id: str
    ) -> Optional[CompilationResult]:
        """Compile a workflow to Python code"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            return None
        
        # Update compilation status
        workflow.compilation_status = 'compiling'
        db.commit()
        
        try:
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
            
            return CompilationResult(
                workflow_id=workflow_id,
                generated_code=workflow.generated_code,
                requirements=workflow.generated_requirements,
                status=workflow.compilation_status,
                errors=workflow.compilation_errors,
                created_at=datetime.utcnow()
            )
        
        except Exception as e:
            workflow.compilation_status = 'failed'
            workflow.compilation_errors = [{"error": str(e)}]
            db.commit()
            
            return CompilationResult(
                workflow_id=workflow_id,
                generated_code='',
                requirements=[],
                status='failed',
                errors=[{"error": str(e)}],
                created_at=datetime.utcnow()
            )
    
    @strawberry.mutation
    def execute_workflow(
        self,
        info: Info,
        workflow_id: str,
        input: ExecutionCreateInput
    ) -> Optional[Execution]:
        """Execute a compiled workflow"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            return None
        
        if workflow.compilation_status != 'compiled':
            raise Exception("Workflow must be compiled before execution")
        
        # Create execution record
        execution = NoCodeExecution(
            workflow_id=workflow.id,
            user_id=current_user.id,
            execution_type=input.execution_type,
            symbols=input.symbols,
            timeframe=input.timeframe,
            start_date=input.start_date,
            end_date=input.end_date,
            initial_capital=input.initial_capital,
            parameters=input.parameters or {}
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Start execution in background (this would be handled by a background task in production)
        # For now, we'll just return the execution record
        
        return convert_db_execution_to_graphql(execution)
    
    @strawberry.mutation
    def create_workflow_from_template(
        self,
        info: Info,
        template_id: str,
        workflow_name: str
    ) -> Optional[Workflow]:
        """Create a workflow from a template"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        template = db.query(NoCodeTemplate).filter(
            NoCodeTemplate.uuid == template_id,
            NoCodeTemplate.is_public == True
        ).first()
        
        if not template:
            return None
        
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
        
        return convert_db_workflow_to_graphql(workflow)

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def execution_updates(
        self,
        info: Info,
        execution_id: str
    ) -> AsyncGenerator[Execution, None]:
        """Subscribe to execution status updates"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        # Verify user owns execution
        execution = db.query(NoCodeExecution).filter(
            NoCodeExecution.uuid == execution_id,
            NoCodeExecution.user_id == current_user.id
        ).first()
        
        if not execution:
            return
        
        # In production, this would connect to Redis/WebSocket for real-time updates
        # For now, we'll simulate updates
        while execution.status in ['pending', 'running']:
            # Refresh execution from database
            db.refresh(execution)
            yield convert_db_execution_to_graphql(execution)
            await asyncio.sleep(2)  # Check every 2 seconds
        
        # Final update when completed
        db.refresh(execution)
        yield convert_db_execution_to_graphql(execution)
    
    @strawberry.subscription
    async def workflow_updates(
        self,
        info: Info,
        workflow_id: str
    ) -> AsyncGenerator[Workflow, None]:
        """Subscribe to workflow updates"""
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        # Verify user owns workflow
        workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            return
        
        # In production, this would connect to Redis/WebSocket for real-time updates
        # For now, we'll simulate updates
        last_updated = workflow.updated_at
        
        while True:
            # Check for updates
            db.refresh(workflow)
            if workflow.updated_at > last_updated:
                last_updated = workflow.updated_at
                yield convert_db_workflow_to_graphql(workflow)
            
            await asyncio.sleep(1)  # Check every second