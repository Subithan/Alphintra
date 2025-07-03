from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    COMPILED = "compiled"
    TRAINING = "training"
    DEPLOYED = "deployed"
    FAILED = "failed"

class TrainingStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CompilationStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    VALIDATING = "validating"
    VALIDATED = "validated"
    VALIDATION_FAILED = "validation_failed"

# Node schemas
class NodeData(BaseModel):
    label: str
    parameters: Dict[str, Any] = {}
    category: Optional[str] = None
    description: Optional[str] = None

class WorkflowNode(BaseModel):
    id: str
    type: str
    position: Dict[str, float]  # {x: float, y: float}
    data: NodeData

class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    type: Optional[str] = "default"

# Workflow schemas
class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []
    parameters: Optional[Dict[str, Any]] = {}

class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[WorkflowStatus] = None

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    user_id: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    parameters: Dict[str, Any]
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            user_id=obj.user_id,
            nodes=obj.nodes if isinstance(obj.nodes, list) else [],
            edges=obj.edges if isinstance(obj.edges, list) else [],
            parameters=obj.parameters if isinstance(obj.parameters, dict) else {},
            status=obj.status,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )

# Compilation schemas
class ValidationResult(BaseModel):
    rule: str
    status: str  # "passed" | "failed" | "warning"
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class CompilationResponse(BaseModel):
    id: str
    workflow_id: str
    python_code: str
    validation_results: List[ValidationResult]
    status: CompilationStatus
    created_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        import json
        validation_results = []
        if obj.validation_results:
            try:
                validation_data = json.loads(obj.validation_results) if isinstance(obj.validation_results, str) else obj.validation_results
                if isinstance(validation_data, list):
                    validation_results = [ValidationResult(**item) for item in validation_data]
                elif isinstance(validation_data, dict):
                    # Convert dict format to list of ValidationResult
                    validation_results = [
                        ValidationResult(rule=key, status="passed", message=value)
                        for key, value in validation_data.items()
                    ]
            except:
                pass
        
        return cls(
            id=obj.id,
            workflow_id=obj.workflow_id,
            python_code=obj.python_code,
            validation_results=validation_results,
            status=obj.status,
            created_at=obj.created_at,
            error_message=getattr(obj, 'error_message', None)
        )

# Dataset schemas
class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    type: str  # "platform" | "user_uploaded" | "external"
    size: int  # number of records
    columns: List[str]
    date_range: Optional[Dict[str, str]] = None  # {"start": "2020-01-01", "end": "2023-12-31"}
    symbols: Optional[List[str]] = None
    timeframe: Optional[str] = None
    created_at: datetime
    is_public: bool = True

# Training schemas
class TrainingConfig(BaseModel):
    dataset_id: str
    train_split: float = Field(0.8, ge=0.1, le=0.9)
    validation_split: float = Field(0.1, ge=0.05, le=0.3)
    test_split: float = Field(0.1, ge=0.05, le=0.3)
    epochs: int = Field(100, ge=1, le=1000)
    batch_size: int = Field(32, ge=1, le=1024)
    learning_rate: float = Field(0.001, ge=0.0001, le=0.1)
    early_stopping: bool = True
    patience: int = Field(10, ge=1, le=100)
    compute_resources: str = Field("cpu", regex="^(cpu|gpu|tpu)$")
    parameters: Optional[Dict[str, Any]] = {}

class TrainingMetrics(BaseModel):
    epoch: int
    train_loss: float
    val_loss: float
    train_accuracy: Optional[float] = None
    val_accuracy: Optional[float] = None
    train_sharpe: Optional[float] = None
    val_sharpe: Optional[float] = None
    timestamp: datetime

class TrainingJobResponse(BaseModel):
    id: str
    workflow_id: str
    compilation_id: str
    dataset_id: str
    config: TrainingConfig
    status: TrainingStatus
    progress: float = 0.0  # 0.0 to 1.0
    current_epoch: Optional[int] = None
    total_epochs: Optional[int] = None
    metrics: List[TrainingMetrics] = []
    model_artifacts: Optional[Dict[str, str]] = None  # URLs to model files
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        import json
        config_data = {}
        metrics_data = []
        artifacts_data = None
        
        try:
            if obj.config:
                config_data = json.loads(obj.config) if isinstance(obj.config, str) else obj.config
                config_data = TrainingConfig(**config_data)
        except:
            config_data = TrainingConfig(dataset_id="unknown")
            
        try:
            if obj.metrics:
                metrics_list = json.loads(obj.metrics) if isinstance(obj.metrics, str) else obj.metrics
                metrics_data = [TrainingMetrics(**item) for item in metrics_list]
        except:
            pass
            
        try:
            if obj.model_artifacts:
                artifacts_data = json.loads(obj.model_artifacts) if isinstance(obj.model_artifacts, str) else obj.model_artifacts
        except:
            pass
        
        return cls(
            id=obj.id,
            workflow_id=obj.workflow_id,
            compilation_id=obj.compilation_id,
            dataset_id=obj.dataset_id,
            config=config_data,
            status=obj.status,
            progress=getattr(obj, 'progress', 0.0),
            current_epoch=getattr(obj, 'current_epoch', None),
            total_epochs=getattr(obj, 'total_epochs', None),
            metrics=metrics_data,
            model_artifacts=artifacts_data,
            error_message=getattr(obj, 'error_message', None),
            created_at=obj.created_at,
            started_at=getattr(obj, 'started_at', None),
            completed_at=getattr(obj, 'completed_at', None)
        )

# Component schemas
class ComponentParameter(BaseModel):
    name: str
    type: str  # "number", "string", "boolean", "select", "range"
    label: str
    description: Optional[str] = None
    default: Any = None
    required: bool = False
    options: Optional[List[Dict[str, Any]]] = None  # For select type
    min_value: Optional[float] = None  # For number/range type
    max_value: Optional[float] = None  # For number/range type
    step: Optional[float] = None  # For number/range type

class ComponentIOPort(BaseModel):
    name: str
    type: str  # "data", "signal", "value"
    description: Optional[str] = None
    required: bool = True

class ComponentResponse(BaseModel):
    id: str
    name: str
    type: str
    category: str
    description: str
    icon: Optional[str] = None
    tags: List[str] = []
    inputs: List[ComponentIOPort] = []
    outputs: List[ComponentIOPort] = []
    parameters: List[ComponentParameter] = []

class ComponentDetailResponse(ComponentResponse):
    documentation: Optional[str] = None
    examples: List[Dict[str, Any]] = []
    implementation: Optional[str] = None  # Python code template

# Testing schemas
class SecurityTestResult(BaseModel):
    test_name: str
    status: str  # "passed", "failed", "warning"
    severity: str  # "low", "medium", "high", "critical"
    message: str
    details: Optional[Dict[str, Any]] = None

class PerformanceTestResult(BaseModel):
    metric_name: str
    value: float
    unit: str
    benchmark: Optional[float] = None
    status: str  # "passed", "failed", "warning"

class TestingResponse(BaseModel):
    id: str
    workflow_id: str
    compilation_id: str
    test_type: str  # "security", "performance", "accuracy"
    status: str  # "pending", "running", "completed", "failed"
    security_results: List[SecurityTestResult] = []
    performance_results: List[PerformanceTestResult] = []
    accuracy_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# Marketplace schemas
class MarketplaceStrategy(BaseModel):
    id: str
    name: str
    description: str
    author: str
    category: str
    tags: List[str]
    price: float  # 0 for free
    rating: float
    downloads: int
    workflow_template: Dict[str, Any]  # Workflow nodes and edges
    performance_metrics: Dict[str, float]
    created_at: datetime
    updated_at: datetime