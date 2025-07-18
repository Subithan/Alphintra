from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

# Base schemas
class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = 'custom'
    tags: Optional[List[str]] = []
    workflow_data: Optional[Dict[str, Any]] = {"nodes": [], "edges": []}
    execution_mode: Optional[str] = 'backtest'

class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    workflow_data: Optional[Dict[str, Any]] = None
    execution_mode: Optional[str] = None
    is_public: Optional[bool] = None

class WorkflowResponse(BaseModel):
    id: int
    uuid: str
    name: str
    description: Optional[str]
    category: str
    tags: List[str]
    workflow_data: Dict[str, Any]
    generated_code: Optional[str]
    generated_code_language: str
    generated_requirements: List[str]
    compilation_status: str
    compilation_errors: List[Any]
    validation_status: str
    validation_errors: List[Any]
    deployment_status: str
    execution_mode: str
    version: int
    is_template: bool
    is_public: bool
    total_executions: int
    successful_executions: int
    avg_performance_score: Optional[Decimal]
    last_execution_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            uuid=str(obj.uuid),  # Convert UUID to string
            name=obj.name,
            description=obj.description,
            category=obj.category,
            tags=obj.tags or [],
            workflow_data=obj.workflow_data or {"nodes": [], "edges": []},
            generated_code=obj.generated_code,
            generated_code_language=obj.generated_code_language or 'python',
            generated_requirements=obj.generated_requirements or [],
            compilation_status=obj.compilation_status or 'pending',
            compilation_errors=obj.compilation_errors or [],
            validation_status=obj.validation_status or 'pending',
            validation_errors=obj.validation_errors or [],
            deployment_status=obj.deployment_status or 'not_deployed',
            execution_mode=obj.execution_mode or 'backtest',
            version=obj.version or 1,
            is_template=obj.is_template or False,
            is_public=obj.is_public or False,
            total_executions=obj.total_executions or 0,
            successful_executions=obj.successful_executions or 0,
            avg_performance_score=obj.avg_performance_score,
            last_execution_at=obj.last_execution_at,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            published_at=obj.published_at
        )

# Component schemas
class ComponentResponse(BaseModel):
    id: int
    uuid: str
    name: str
    display_name: str
    description: Optional[str]
    category: str
    subcategory: Optional[str]
    component_type: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    parameters_schema: Dict[str, Any]
    default_parameters: Dict[str, Any]
    code_template: str
    imports_required: List[str]
    dependencies: List[str]
    ui_config: Dict[str, Any]
    icon: Optional[str]
    is_builtin: bool
    is_public: bool
    usage_count: int
    rating: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Execution schemas
class ExecutionCreate(BaseModel):
    execution_type: str = Field(..., pattern="^(backtest|paper_trade|live_trade)$")
    symbols: List[str] = Field(..., min_items=1)
    timeframe: str = Field(..., pattern="^(1m|5m|15m|30m|1h|4h|1d)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: Decimal = Field(default=10000.0, gt=0)
    parameters: Optional[Dict[str, Any]] = {}

    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v

class ExecutionResponse(BaseModel):
    id: int
    uuid: str
    workflow_id: int
    execution_type: str
    symbols: List[str]
    timeframe: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    initial_capital: Decimal
    status: str
    progress: int
    current_step: Optional[str]
    final_capital: Optional[Decimal]
    total_return: Optional[Decimal]
    total_return_percent: Optional[Decimal]
    sharpe_ratio: Optional[Decimal]
    max_drawdown_percent: Optional[Decimal]
    total_trades: int
    winning_trades: int
    trades_data: List[Any]
    performance_metrics: Dict[str, Any]
    execution_logs: List[Any]
    error_logs: List[Any]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

# Template schemas
class TemplateResponse(BaseModel):
    id: int
    uuid: str
    name: str
    description: Optional[str]
    category: str
    difficulty_level: str
    template_data: Dict[str, Any]
    preview_image_url: Optional[str]
    author_id: Optional[int]
    is_featured: bool
    is_public: bool
    usage_count: int
    rating: Optional[Decimal]
    keywords: List[str]
    estimated_time_minutes: Optional[int]
    expected_performance: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Compilation schemas
class CompilationResponse(BaseModel):
    workflow_id: str
    generated_code: str
    requirements: List[str]
    status: str
    errors: List[Any]
    created_at: datetime

# Analytics schemas
class WorkflowAnalytics(BaseModel):
    total_workflows: int
    public_workflows: int
    total_executions: int
    successful_executions: int
    avg_success_rate: float
    popular_categories: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]

# User activity tracking
class ActivityLog(BaseModel):
    event_type: str
    workflow_id: Optional[str]
    timestamp: datetime
    details: Dict[str, Any]

# Market data schemas for execution
class MarketDataConfig(BaseModel):
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    source: Optional[str] = 'default'

# Risk management schemas
class RiskConfig(BaseModel):
    max_position_size: Optional[float] = None
    max_drawdown: Optional[float] = None
    stop_loss_percent: Optional[float] = None
    take_profit_percent: Optional[float] = None
    max_trades_per_day: Optional[int] = None

# Performance metrics
class PerformanceMetrics(BaseModel):
    total_return: float
    total_return_percent: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    calmar_ratio: float

# Workflow validation
class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    complexity_score: int
    estimated_execution_time: Optional[str]

# File upload schemas
class DatasetUpload(BaseModel):
    name: str
    description: Optional[str]
    file_type: str
    file_size: int
    columns: List[str]
    sample_data: List[Dict[str, Any]]

# Strategy backtesting
class BacktestConfig(BaseModel):
    workflow_id: str
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.001

class BacktestResult(BaseModel):
    execution_id: str
    config: BacktestConfig
    performance: PerformanceMetrics
    trades: List[Dict[str, Any]]
    equity_curve: List[Dict[str, float]]
    drawdown_curve: List[Dict[str, float]]
    monthly_returns: List[Dict[str, float]]
    execution_time: float
    created_at: datetime

# Component creation (for advanced users)
class ComponentCreate(BaseModel):
    name: str
    display_name: str
    description: str
    category: str
    subcategory: Optional[str]
    component_type: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    parameters_schema: Dict[str, Any]
    default_parameters: Dict[str, Any]
    code_template: str
    imports_required: List[str] = []
    dependencies: List[str] = []
    ui_config: Dict[str, Any] = {"width": 200, "height": 100, "color": "#1f2937"}
    icon: Optional[str] = None

# Workflow sharing
class WorkflowShare(BaseModel):
    workflow_id: str
    shared_with_email: str
    permission_level: str = "view"  # view, edit, execute
    expires_at: Optional[datetime] = None
    message: Optional[str] = None

# System statistics
class SystemStats(BaseModel):
    total_users: int
    total_workflows: int
    total_executions: int
    total_components: int
    total_templates: int
    avg_executions_per_day: float
    most_popular_components: List[str]
    most_used_templates: List[str]
    system_uptime: str
    last_updated: datetime