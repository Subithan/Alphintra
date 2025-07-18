import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from models import NoCodeWorkflow, NoCodeExecution, NoCodeComponent, NoCodeTemplate, User
from schemas_updated import WorkflowCreate, WorkflowUpdate, ExecutionCreate
import json

# Create custom scalar types for JSON objects
JSON = strawberry.scalar(
    Dict[str, Any],
    serialize=lambda v: v,
    parse_value=lambda v: v,
    description="JSON object"
)

# GraphQL Types
@strawberry.type
class WorkflowNode:
    id: str
    type: str
    position: JSON
    data: JSON

@strawberry.type
class WorkflowEdge:
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

@strawberry.type
class WorkflowData:
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

@strawberry.type
class Workflow:
    id: int
    uuid: str
    name: str
    description: Optional[str]
    category: str
    tags: List[str]
    workflow_data: WorkflowData
    generated_code: Optional[str]
    generated_code_language: str
    generated_requirements: List[str]
    compilation_status: str
    compilation_errors: List[JSON]
    validation_status: str
    validation_errors: List[JSON]
    deployment_status: str
    execution_mode: str
    version: int
    parent_workflow_id: Optional[int]
    is_template: bool
    is_public: bool
    total_executions: int
    successful_executions: int
    avg_performance_score: Optional[float]
    last_execution_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

@strawberry.type
class Execution:
    id: int
    uuid: str
    workflow_id: int
    execution_type: str
    symbols: List[str]
    timeframe: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    initial_capital: float
    status: str
    progress: int
    current_step: Optional[str]
    final_capital: Optional[float]
    total_return: Optional[float]
    total_return_percent: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown_percent: Optional[float]
    total_trades: int
    winning_trades: int
    trades_data: List[JSON]
    performance_metrics: JSON
    execution_logs: List[JSON]
    error_logs: List[JSON]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime

@strawberry.type
class Component:
    id: int
    uuid: str
    name: str
    display_name: str
    description: Optional[str]
    category: str
    subcategory: Optional[str]
    component_type: str
    input_schema: JSON
    output_schema: JSON
    parameters_schema: JSON
    default_parameters: JSON
    code_template: str
    imports_required: List[str]
    dependencies: List[str]
    ui_config: JSON
    icon: Optional[str]
    is_builtin: bool
    is_public: bool
    usage_count: int
    rating: Optional[float]
    created_at: datetime
    updated_at: datetime

@strawberry.type
class Template:
    id: int
    uuid: str
    name: str
    description: Optional[str]
    category: str
    difficulty_level: str
    template_data: WorkflowData
    preview_image_url: Optional[str]
    author_id: Optional[int]
    is_featured: bool
    is_public: bool
    usage_count: int
    rating: Optional[float]
    keywords: List[str]
    estimated_time_minutes: Optional[int]
    expected_performance: JSON
    created_at: datetime
    updated_at: datetime

@strawberry.type
class CompilationResult:
    workflow_id: str
    generated_code: str
    requirements: List[str]
    status: str
    errors: List[JSON]
    created_at: datetime

@strawberry.type
class WorkflowHistory:
    id: str
    action_type: str
    description: str
    user_name: Optional[str]
    version: Optional[int]
    timestamp: datetime
    metadata: Optional[JSON]

@strawberry.type
class WorkflowsConnection:
    workflows: List[Workflow]
    total: int
    hasMore: bool

@strawberry.type
class ExecutionsConnection:
    executions: List[Execution]
    total: int
    hasMore: bool

# Input Types
@strawberry.input
class WorkflowNodeInput:
    id: str
    type: str
    position: JSON
    data: JSON

@strawberry.input
class WorkflowEdgeInput:
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

@strawberry.input
class WorkflowDataInput:
    nodes: List[WorkflowNodeInput]
    edges: List[WorkflowEdgeInput]

@strawberry.input
class WorkflowCreateInput:
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    workflow_data: Optional[WorkflowDataInput] = None
    execution_mode: Optional[str] = None

@strawberry.input
class WorkflowUpdateInput:
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    workflow_data: Optional[WorkflowDataInput] = None
    execution_mode: Optional[str] = None
    is_public: Optional[bool] = None

@strawberry.input
class ExecutionCreateInput:
    execution_type: str
    symbols: List[str]
    timeframe: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float
    parameters: Optional[JSON] = None

@strawberry.input
class WorkflowFilters:
    skip: Optional[int] = None
    limit: Optional[int] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None
    search: Optional[str] = None

@strawberry.input
class ExecutionFilters:
    skip: Optional[int] = None
    limit: Optional[int] = None
    status: Optional[str] = None
    execution_type: Optional[str] = None

# Utility functions
def convert_db_workflow_to_graphql(db_workflow: NoCodeWorkflow) -> Workflow:
    """Convert SQLAlchemy model to GraphQL type"""
    workflow_data = db_workflow.workflow_data or {"nodes": [], "edges": []}
    
    # Convert nodes
    nodes = []
    for node in workflow_data.get("nodes", []):
        nodes.append(WorkflowNode(
            id=node.get("id", ""),
            type=node.get("type", ""),
            position=node.get("position", {"x": 0, "y": 0}),
            data=node.get("data", {})
        ))
    
    # Convert edges
    edges = []
    for edge in workflow_data.get("edges", []):
        edges.append(WorkflowEdge(
            id=edge.get("id", ""),
            source=edge.get("source", ""),
            target=edge.get("target", ""),
            sourceHandle=edge.get("sourceHandle"),
            targetHandle=edge.get("targetHandle")
        ))
    
    return Workflow(
        id=db_workflow.id,
        uuid=str(db_workflow.uuid),
        name=db_workflow.name,
        description=db_workflow.description,
        category=db_workflow.category,
        tags=db_workflow.tags or [],
        workflow_data=WorkflowData(nodes=nodes, edges=edges),
        generated_code=db_workflow.generated_code,
        generated_code_language=db_workflow.generated_code_language,
        generated_requirements=db_workflow.generated_requirements or [],
        compilation_status=db_workflow.compilation_status,
        compilation_errors=db_workflow.compilation_errors or [],
        validation_status=db_workflow.validation_status,
        validation_errors=db_workflow.validation_errors or [],
        deployment_status=db_workflow.deployment_status,
        execution_mode=db_workflow.execution_mode,
        version=db_workflow.version,
        parent_workflow_id=db_workflow.parent_workflow_id,
        is_template=db_workflow.is_template,
        is_public=db_workflow.is_public,
        total_executions=db_workflow.total_executions,
        successful_executions=db_workflow.successful_executions,
        avg_performance_score=float(db_workflow.avg_performance_score) if db_workflow.avg_performance_score else None,
        last_execution_at=db_workflow.last_execution_at,
        created_at=db_workflow.created_at,
        updated_at=db_workflow.updated_at,
        published_at=db_workflow.published_at
    )

def convert_db_execution_to_graphql(db_execution: NoCodeExecution) -> Execution:
    """Convert SQLAlchemy execution model to GraphQL type"""
    return Execution(
        id=db_execution.id,
        uuid=str(db_execution.uuid),
        workflow_id=db_execution.workflow_id,
        execution_type=db_execution.execution_type,
        symbols=db_execution.symbols or [],
        timeframe=db_execution.timeframe,
        start_date=db_execution.start_date,
        end_date=db_execution.end_date,
        initial_capital=float(db_execution.initial_capital),
        status=db_execution.status,
        progress=db_execution.progress,
        current_step=db_execution.current_step,
        final_capital=float(db_execution.final_capital) if db_execution.final_capital else None,
        total_return=float(db_execution.total_return) if db_execution.total_return else None,
        total_return_percent=float(db_execution.total_return_percent) if db_execution.total_return_percent else None,
        sharpe_ratio=float(db_execution.sharpe_ratio) if db_execution.sharpe_ratio else None,
        max_drawdown_percent=float(db_execution.max_drawdown_percent) if db_execution.max_drawdown_percent else None,
        total_trades=db_execution.total_trades,
        winning_trades=db_execution.winning_trades,
        trades_data=db_execution.trades_data or [],
        performance_metrics=db_execution.performance_metrics or {},
        execution_logs=db_execution.execution_logs or [],
        error_logs=db_execution.error_logs or [],
        started_at=db_execution.started_at,
        completed_at=db_execution.completed_at,
        created_at=db_execution.created_at
    )

def convert_db_component_to_graphql(db_component: NoCodeComponent) -> Component:
    """Convert SQLAlchemy component model to GraphQL type"""
    return Component(
        id=db_component.id,
        uuid=str(db_component.uuid),
        name=db_component.name,
        display_name=db_component.display_name,
        description=db_component.description,
        category=db_component.category,
        subcategory=db_component.subcategory,
        component_type=db_component.component_type,
        input_schema=db_component.input_schema or {},
        output_schema=db_component.output_schema or {},
        parameters_schema=db_component.parameters_schema or {},
        default_parameters=db_component.default_parameters or {},
        code_template=db_component.code_template,
        imports_required=db_component.imports_required or [],
        dependencies=db_component.dependencies or [],
        ui_config=db_component.ui_config or {},
        icon=db_component.icon,
        is_builtin=db_component.is_builtin,
        is_public=db_component.is_public,
        usage_count=db_component.usage_count,
        rating=float(db_component.rating) if db_component.rating else None,
        created_at=db_component.created_at,
        updated_at=db_component.updated_at
    )

def convert_db_template_to_graphql(db_template: NoCodeTemplate) -> Template:
    """Convert SQLAlchemy template model to GraphQL type"""
    template_data = db_template.template_data or {"nodes": [], "edges": []}
    
    # Convert nodes
    nodes = []
    for node in template_data.get("nodes", []):
        nodes.append(WorkflowNode(
            id=node.get("id", ""),
            type=node.get("type", ""),
            position=node.get("position", {"x": 0, "y": 0}),
            data=node.get("data", {})
        ))
    
    # Convert edges
    edges = []
    for edge in template_data.get("edges", []):
        edges.append(WorkflowEdge(
            id=edge.get("id", ""),
            source=edge.get("source", ""),
            target=edge.get("target", ""),
            sourceHandle=edge.get("sourceHandle"),
            targetHandle=edge.get("targetHandle")
        ))
    
    return Template(
        id=db_template.id,
        uuid=str(db_template.uuid),
        name=db_template.name,
        description=db_template.description,
        category=db_template.category,
        difficulty_level=db_template.difficulty_level,
        template_data=WorkflowData(nodes=nodes, edges=edges),
        preview_image_url=db_template.preview_image_url,
        author_id=db_template.author_id,
        is_featured=db_template.is_featured,
        is_public=db_template.is_public,
        usage_count=db_template.usage_count,
        rating=float(db_template.rating) if db_template.rating else None,
        keywords=db_template.keywords or [],
        estimated_time_minutes=db_template.estimated_time_minutes,
        expected_performance=db_template.expected_performance or {},
        created_at=db_template.created_at,
        updated_at=db_template.updated_at
    )

def convert_workflow_input_to_dict(input_data: WorkflowDataInput) -> dict:
    """Convert GraphQL input to dictionary"""
    return {
        "nodes": [
            {
                "id": node.id,
                "type": node.type,
                "position": node.position,
                "data": node.data
            }
            for node in input_data.nodes
        ],
        "edges": [
            {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "sourceHandle": edge.sourceHandle,
                "targetHandle": edge.targetHandle
            }
            for edge in input_data.edges
        ]
    }