# AI/ML Strategy Service - Core Components Documentation

## Table of Contents

1. [Core Architecture](#core-architecture)
2. [Configuration Management](#configuration-management)
3. [Database Layer](#database-layer)
4. [Service Layer](#service-layer)
5. [ML Models and Training](#ml-models-and-training)
6. [Utility Functions](#utility-functions)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Error Handling and Validation](#error-handling-and-validation)

## Core Architecture

### Application Structure

```
app/
├── api/                    # API layer (FastAPI routes)
│   ├── endpoints/         # Individual endpoint modules
│   └── routes.py         # Main router configuration
├── core/                  # Core application components
│   ├── config.py         # Configuration management
│   ├── database.py       # Database connection and session management
│   ├── auth.py           # Authentication and authorization
│   └── monitoring.py     # Metrics and monitoring setup
├── models/               # Database models (SQLAlchemy)
│   ├── base.py          # Base model classes
│   ├── strategy.py      # Strategy-related models
│   ├── dataset.py       # Dataset models
│   ├── training.py      # Training job models
│   └── backtesting.py   # Backtesting models
├── services/            # Business logic layer
│   ├── strategy_service.py      # Strategy management
│   ├── backtesting_engine.py    # Backtesting execution
│   ├── training_job_manager.py  # ML training orchestration
│   └── data_processor.py       # Data processing
├── sdk/                 # Python SDK for strategy development
│   ├── strategy.py      # Base strategy class
│   ├── data.py          # Market data interfaces
│   ├── portfolio.py     # Portfolio management
│   └── indicators.py    # Technical indicators
├── ml_models/           # ML model implementations
│   ├── base.py          # Base ML model interface
│   └── xgboost_model.py # Specific model implementations
└── utils/               # Utility functions
    └── workflow_analyzer.py
```

### Design Principles

1. **Separation of Concerns**: Clear separation between API, business logic, and data layers
2. **Dependency Injection**: Services are injected as dependencies for testability
3. **Async/Await**: Full async support for high-performance operations
4. **Type Safety**: Comprehensive type hints using Pydantic models
5. **Configuration-Driven**: Environment-based configuration management
6. **Observability**: Built-in metrics, logging, and monitoring

## Configuration Management

### Settings Class

The `Settings` class in `app/core/config.py` manages all application configuration:

```python
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    APP_NAME: str = "AI/ML Strategy Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    PORT: int = Field(default=8002)
    DEBUG: bool = Field(default=True)
    
    # Security settings
    SECRET_KEY: str = Field(..., description="Secret key for JWT token generation")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # Database settings
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    TIMESCALE_DATABASE_URL: Optional[str] = Field(default=None)
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=30)
    
    # External service URLs
    AUTH_SERVICE_URL: str = Field(default="http://auth-service:8080")
    TRADING_ENGINE_URL: str = Field(default="http://trading-engine:8080")
    MARKET_DATA_SERVICE_URL: str = Field(default="http://market-data-service:8080")
```

### Configuration Usage

```python
from app.core.config import settings

# Access configuration values
database_url = settings.DATABASE_URL
is_development = settings.is_development
max_training_time = settings.MAX_TRAINING_TIME_HOURS

# Environment-specific behavior
if settings.ENVIRONMENT == "production":
    # Production-specific logic
    pass
```

### Environment Variables

Key environment variables that must be set:

```bash
# Required
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/aiml_strategy_service
GCP_PROJECT_ID=your-gcp-project
MLFLOW_TRACKING_URI=http://mlflow:5000
GCS_BUCKET_NAME=your-storage-bucket

# Optional with defaults
ENVIRONMENT=development
PORT=8002
DEBUG=true
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

## Database Layer

### Database Connection Management

The database layer provides async PostgreSQL connections with connection pooling:

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### Base Model Classes

All database models inherit from base classes that provide common functionality:

```python
# app/models/base.py
from sqlalchemy import Column, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserMixin:
    """Mixin for models that belong to users."""
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

class MetadataMixin:
    """Mixin for models with metadata."""
    metadata = Column(JSON, default=dict)
    tags = Column(StringArray(), default=list)
```

### Model Examples

```python
# Strategy model with relationships
class Strategy(BaseModel, UserMixin, MetadataMixin):
    __tablename__ = "strategies"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    code = Column(Text, nullable=False)
    language = Column(String(50), default="python", nullable=False)
    sdk_version = Column(String(50), nullable=False)
    parameters = Column(JSON, default=dict)
    status = Column(Enum(StrategyStatus), default=StrategyStatus.DRAFT)
    
    # Performance metrics
    total_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    win_rate = Column(Float)
    
    # Relationships
    backtest_jobs = relationship("BacktestJob", back_populates="strategy")
    training_jobs = relationship("TrainingJob", back_populates="strategy")
```

### Database Migrations

The service uses Alembic for database schema migrations:

```bash
# Generate new migration
alembic revision --autogenerate -m "Add new strategy fields"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Service Layer

### Strategy Service

Manages strategy lifecycle and operations:

```python
class StrategyService:
    """Service for managing strategies and their lifecycle."""
    
    def __init__(self, execution_engine: ExecutionEngine):
        self.execution_engine = execution_engine
        self.logger = logging.getLogger(__name__)
    
    async def create_strategy(self, strategy_data: Dict[str, Any], 
                            user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Create a new strategy with validation."""
        try:
            # Validate strategy code
            validation_result = self.execution_engine.validate_strategy_code(
                strategy_data["code"]
            )
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Strategy code validation failed",
                    "validation_errors": validation_result["errors"]
                }
            
            # Create strategy
            strategy = Strategy(
                name=strategy_data["name"],
                description=strategy_data.get("description"),
                code=strategy_data["code"],
                sdk_version="1.0.0",
                parameters=strategy_data.get("parameters", {}),
                status=StrategyStatus.DRAFT,
                user_id=UUID(user_id),
                tags=strategy_data.get("tags", [])
            )
            
            db.add(strategy)
            await db.commit()
            await db.refresh(strategy)
            
            return {
                "success": True,
                "strategy_id": str(strategy.id),
                "validation_warnings": validation_result.get("warnings", [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create strategy: {str(e)}")
            return {"success": False, "error": str(e)}
```

### Backtesting Engine

Comprehensive backtesting with multiple methodologies:

```python
class BacktestingEngine:
    """Advanced backtesting engine with multiple methodologies."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.performance_calculator = PerformanceCalculator()
    
    async def run_backtest(self, backtest_job: BacktestJob) -> Dict[str, Any]:
        """Execute a backtest job."""
        try:
            # Load strategy and dataset
            strategy = await self._load_strategy(backtest_job.strategy_id)
            dataset = await self._load_dataset(backtest_job.dataset_id)
            
            # Initialize backtest environment
            portfolio = Portfolio(
                initial_capital=backtest_job.initial_capital,
                commission_rate=backtest_job.commission_rate,
                slippage_rate=backtest_job.slippage_rate
            )
            
            # Execute backtest based on methodology
            if backtest_job.methodology == BacktestMethodology.WALK_FORWARD:
                results = await self._run_walk_forward_backtest(
                    strategy, dataset, portfolio, backtest_job
                )
            elif backtest_job.methodology == BacktestMethodology.MONTE_CARLO:
                results = await self._run_monte_carlo_backtest(
                    strategy, dataset, portfolio, backtest_job
                )
            else:
                results = await self._run_standard_backtest(
                    strategy, dataset, portfolio, backtest_job
                )
            
            # Calculate performance metrics
            performance_metrics = self.performance_calculator.calculate_metrics(
                results["trades"], 
                results["equity_curve"],
                backtest_job.initial_capital
            )
            
            return {
                "success": True,
                "results": results,
                "performance_metrics": performance_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}")
            return {"success": False, "error": str(e)}
```

### Training Job Manager

Orchestrates ML model training on cloud infrastructure:

```python
class TrainingJobManager:
    """Manages ML training jobs with cloud resource allocation."""
    
    def __init__(self):
        self.vertex_ai = VertexAIIntegrationService()
        self.resource_allocator = ResourceAllocator()
        self.logger = logging.getLogger(__name__)
    
    async def create_training_job(self, job_request: TrainingJobRequest, 
                                user_id: str) -> Dict[str, Any]:
        """Create and queue a new training job."""
        try:
            # Allocate cloud resources
            resource_allocation = await self.resource_allocator.allocate_resources(
                instance_type=job_request.instance_type,
                disk_size=job_request.disk_size,
                timeout_hours=job_request.timeout_hours,
                priority=job_request.priority
            )
            
            # Create training job in Vertex AI
            vertex_job = await self.vertex_ai.create_training_job(
                job_name=job_request.job_name,
                strategy_id=job_request.strategy_id,
                dataset_id=job_request.dataset_id,
                hyperparameters=job_request.hyperparameters,
                training_config=job_request.training_config,
                resource_allocation=resource_allocation
            )
            
            # Store job in database
            training_job = TrainingJob(
                strategy_id=UUID(job_request.strategy_id),
                dataset_id=UUID(job_request.dataset_id),
                job_name=job_request.job_name,
                job_type=job_request.job_type,
                instance_type=job_request.instance_type,
                hyperparameters=job_request.hyperparameters,
                training_config=job_request.training_config,
                status=JobStatus.QUEUED,
                user_id=UUID(user_id),
                vertex_job_id=vertex_job["job_id"]
            )
            
            return {
                "success": True,
                "job_id": str(training_job.id),
                "vertex_job_id": vertex_job["job_id"],
                "estimated_start_time": vertex_job["estimated_start_time"],
                "resource_allocation": resource_allocation
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create training job: {str(e)}")
            return {"success": False, "error": str(e)}
```

### Data Processing Service

Handles data ingestion, validation, and preprocessing:

```python
class DataProcessingService:
    """Service for processing and validating datasets."""
    
    def __init__(self):
        self.storage_manager = StorageManager()
        self.validator = DatasetValidator()
        self.logger = logging.getLogger(__name__)
    
    async def process_uploaded_dataset(self, file_path: str, 
                                     metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process an uploaded dataset file."""
        try:
            # Load and validate data
            df = pd.read_csv(file_path)
            validation_results = await self.validator.validate_dataset(df, metadata)
            
            if not validation_results["is_valid"]:
                return {
                    "success": False,
                    "error": "Dataset validation failed",
                    "validation_errors": validation_results["errors"]
                }
            
            # Clean and preprocess data
            cleaned_df = await self._clean_dataset(df, metadata)
            
            # Generate statistics
            statistics = self._generate_dataset_statistics(cleaned_df)
            
            # Upload to cloud storage
            storage_path = await self.storage_manager.upload_dataset(
                cleaned_df, metadata["name"]
            )
            
            return {
                "success": True,
                "storage_path": storage_path,
                "statistics": statistics,
                "validation_results": validation_results,
                "record_count": len(cleaned_df)
            }
            
        except Exception as e:
            self.logger.error(f"Dataset processing failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _clean_dataset(self, df: pd.DataFrame, 
                           metadata: Dict[str, Any]) -> pd.DataFrame:
        """Clean and preprocess dataset."""
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        if metadata.get("fill_missing", True):
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].fillna(method='ffill')
        
        # Validate data types
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Sort by timestamp if present
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp")
        
        return df
```

## ML Models and Training

### Base ML Model Interface

All ML models implement a common interface:

```python
# app/ml_models/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class BaseMLModel(ABC):
    """Base class for all ML models."""
    
    def __init__(self, model_config: Dict[str, Any]):
        self.model_config = model_config
        self.model = None
        self.is_trained = False
        self.feature_columns = []
        self.target_column = None
    
    @abstractmethod
    async def train(self, training_data: pd.DataFrame, 
                   validation_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Train the model on provided data."""
        pass
    
    @abstractmethod
    async def predict(self, input_data: pd.DataFrame) -> pd.DataFrame:
        """Make predictions on input data."""
        pass
    
    @abstractmethod
    def save_model(self, path: str) -> None:
        """Save trained model to disk."""
        pass
    
    @abstractmethod
    def load_model(self, path: str) -> None:
        """Load trained model from disk."""
        pass
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance if supported by the model."""
        return None
    
    def validate_input(self, data: pd.DataFrame) -> bool:
        """Validate input data format."""
        required_columns = set(self.feature_columns)
        available_columns = set(data.columns)
        return required_columns.issubset(available_columns)
```

### XGBoost Model Implementation

```python
# app/ml_models/xgboost_model.py
import xgboost as xgb
from app.ml_models.base import BaseMLModel

class XGBoostModel(BaseMLModel):
    """XGBoost model implementation for price prediction."""
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.model_params = {
            "objective": "reg:squarederror",
            "n_estimators": model_config.get("n_estimators", 100),
            "max_depth": model_config.get("max_depth", 6),
            "learning_rate": model_config.get("learning_rate", 0.1),
            "random_state": 42
        }
    
    async def train(self, training_data: pd.DataFrame, 
                   validation_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Train XGBoost model."""
        try:
            # Prepare features and target
            self.feature_columns = [col for col in training_data.columns 
                                  if col != self.model_config["target_column"]]
            self.target_column = self.model_config["target_column"]
            
            X_train = training_data[self.feature_columns]
            y_train = training_data[self.target_column]
            
            # Initialize and train model
            self.model = xgb.XGBRegressor(**self.model_params)
            
            if validation_data is not None:
                X_val = validation_data[self.feature_columns]
                y_val = validation_data[self.target_column]
                
                self.model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=10,
                    verbose=False
                )
            else:
                self.model.fit(X_train, y_train)
            
            self.is_trained = True
            
            # Calculate training metrics
            train_predictions = self.model.predict(X_train)
            train_mse = mean_squared_error(y_train, train_predictions)
            train_r2 = r2_score(y_train, train_predictions)
            
            metrics = {
                "train_mse": train_mse,
                "train_r2": train_r2
            }
            
            if validation_data is not None:
                val_predictions = self.model.predict(X_val)
                val_mse = mean_squared_error(y_val, val_predictions)
                val_r2 = r2_score(y_val, val_predictions)
                metrics.update({
                    "val_mse": val_mse,
                    "val_r2": val_r2
                })
            
            return {"success": True, "metrics": metrics}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def predict(self, input_data: pd.DataFrame) -> pd.DataFrame:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        if not self.validate_input(input_data):
            raise ValueError("Input data missing required features")
        
        X = input_data[self.feature_columns]
        predictions = self.model.predict(X)
        
        result_df = input_data.copy()
        result_df["prediction"] = predictions
        return result_df
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get XGBoost feature importance."""
        if not self.is_trained:
            return None
        
        importance_scores = self.model.feature_importances_
        return dict(zip(self.feature_columns, importance_scores))
```

## Utility Functions

### Workflow Analyzer

Analyzes no-code workflows for optimization and validation:

```python
# app/utils/workflow_analyzer.py
from typing import Dict, List, Any, Tuple

class WorkflowAnalyzer:
    """Analyzes no-code workflow definitions for optimization."""
    
    def analyze_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workflow for performance and correctness."""
        nodes = workflow_definition.get("nodes", [])
        edges = workflow_definition.get("edges", [])
        
        analysis = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "complexity_score": self._calculate_complexity(nodes, edges),
            "optimization_suggestions": [],
            "potential_issues": [],
            "estimated_execution_time": self._estimate_execution_time(nodes)
        }
        
        # Check for common issues
        issues = self._detect_issues(nodes, edges)
        analysis["potential_issues"] = issues
        
        # Generate optimization suggestions
        suggestions = self._generate_optimizations(nodes, edges)
        analysis["optimization_suggestions"] = suggestions
        
        return analysis
    
    def _calculate_complexity(self, nodes: List[Dict], edges: List[Dict]) -> float:
        """Calculate workflow complexity score."""
        base_complexity = len(nodes) * 0.1
        edge_complexity = len(edges) * 0.05
        
        # Add complexity for specific node types
        for node in nodes:
            node_type = node.get("type", "")
            if node_type in ["ml_model", "optimization"]:
                base_complexity += 1.0
            elif node_type in ["technical_indicator", "condition"]:
                base_complexity += 0.3
        
        return min(base_complexity + edge_complexity, 10.0)
    
    def _detect_issues(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """Detect potential issues in workflow."""
        issues = []
        
        # Check for disconnected nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.get("source"))
            connected_nodes.add(edge.get("target"))
        
        all_nodes = {node.get("id") for node in nodes}
        disconnected = all_nodes - connected_nodes
        
        if disconnected:
            issues.append({
                "type": "disconnected_nodes",
                "severity": "warning",
                "message": f"Found {len(disconnected)} disconnected nodes",
                "nodes": list(disconnected)
            })
        
        # Check for cycles
        if self._has_cycles(edges):
            issues.append({
                "type": "circular_dependency",
                "severity": "error",
                "message": "Workflow contains circular dependencies"
            })
        
        return issues
    
    def _generate_optimizations(self, nodes: List[Dict], 
                              edges: List[Dict]) -> List[Dict]:
        """Generate optimization suggestions."""
        suggestions = []
        
        # Suggest parallel execution opportunities
        parallel_groups = self._find_parallel_groups(nodes, edges)
        if len(parallel_groups) > 1:
            suggestions.append({
                "type": "parallelization",
                "description": f"Found {len(parallel_groups)} groups that can run in parallel",
                "potential_speedup": f"{len(parallel_groups)}x"
            })
        
        # Suggest caching opportunities
        cacheable_nodes = [n for n in nodes if n.get("type") in ["data_source", "technical_indicator"]]
        if len(cacheable_nodes) > 2:
            suggestions.append({
                "type": "caching",
                "description": f"Consider caching results from {len(cacheable_nodes)} nodes",
                "estimated_savings": "20-40% execution time"
            })
        
        return suggestions
```

## Monitoring and Observability

### Metrics Collection

The service collects comprehensive metrics using Prometheus:

```python
# app/core/monitoring.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# Metrics definitions
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_STRATEGIES = Gauge(
    'active_strategies_total',
    'Number of active strategies'
)

TRAINING_JOBS_RUNNING = Gauge(
    'training_jobs_running',
    'Number of running training jobs'
)

BACKTEST_DURATION = Histogram(
    'backtest_duration_seconds',
    'Backtest execution duration'
)

def setup_metrics():
    """Setup Prometheus metrics server."""
    start_http_server(settings.PROMETHEUS_PORT)

def track_request_metrics(func):
    """Decorator to track request metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(
                method="POST",  # This would be extracted from request
                endpoint=func.__name__,
                status_code=200
            ).inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(
                method="POST",
                endpoint=func.__name__,
                status_code=500
            ).inc()
            raise
        finally:
            REQUEST_DURATION.labels(
                method="POST",
                endpoint=func.__name__
            ).observe(time.time() - start_time)
    
    return wrapper
```

### Structured Logging

The service uses structured logging with contextual information:

```python
import structlog
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def get_logger(name: str):
    """Get a structured logger with context."""
    logger = structlog.get_logger(name)
    return logger.bind(
        request_id=request_id_var.get(),
        user_id=user_id_var.get()
    )

# Usage in services
class StrategyService:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def create_strategy(self, strategy_data: Dict[str, Any]):
        self.logger.info(
            "Creating strategy",
            strategy_name=strategy_data["name"],
            code_length=len(strategy_data["code"])
        )
```

## Error Handling and Validation

### Custom Exception Classes

```python
# app/core/exceptions.py
class AIMLStrategyServiceException(Exception):
    """Base exception for AI/ML Strategy Service."""
    pass

class StrategyValidationError(AIMLStrategyServiceException):
    """Raised when strategy code validation fails."""
    def __init__(self, message: str, errors: List[Dict[str, Any]]):
        super().__init__(message)
        self.errors = errors

class DatasetValidationError(AIMLStrategyServiceException):
    """Raised when dataset validation fails."""
    def __init__(self, message: str, issues: List[Dict[str, Any]]):
        super().__init__(message)
        self.issues = issues

class TrainingJobError(AIMLStrategyServiceException):
    """Raised when training job fails."""
    def __init__(self, message: str, job_id: str):
        super().__init__(message)
        self.job_id = job_id

class BacktestError(AIMLStrategyServiceException):
    """Raised when backtest execution fails."""
    def __init__(self, message: str, backtest_id: str):
        super().__init__(message)
        self.backtest_id = backtest_id
```

### Global Exception Handler

```python
# In main.py
@app.exception_handler(StrategyValidationError)
async def strategy_validation_error_handler(request: Request, exc: StrategyValidationError):
    """Handle strategy validation errors."""
    logger.warning(
        "Strategy validation failed",
        path=request.url.path,
        errors=exc.errors
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": str(exc),
            "error_code": "STRATEGY_VALIDATION_ERROR",
            "validation_errors": exc.errors
        }
    )

@app.exception_handler(DatasetValidationError)
async def dataset_validation_error_handler(request: Request, exc: DatasetValidationError):
    """Handle dataset validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": str(exc),
            "error_code": "DATASET_VALIDATION_ERROR",
            "validation_issues": exc.issues
        }
    )
```

### Input Validation

Using Pydantic for comprehensive input validation:

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any

class StrategyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    code: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Strategy name cannot be empty')
        return v.strip()
    
    @validator('code')
    def validate_code(cls, v):
        if 'import os' in v or 'import sys' in v:
            raise ValueError('Restricted imports not allowed in strategy code')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    class Config:
        schema_extra = {
            "example": {
                "name": "RSI Mean Reversion",
                "description": "Strategy using RSI for mean reversion signals",
                "code": "from alphintra import BaseStrategy\n\nclass RSIStrategy(BaseStrategy):\n    pass",
                "parameters": {"rsi_period": 14},
                "tags": ["rsi", "mean-reversion"]
            }
        }
```

This comprehensive documentation covers the core components and internal architecture of the AI/ML Strategy Service, providing developers with detailed information about the service's implementation, design patterns, and extensibility points.