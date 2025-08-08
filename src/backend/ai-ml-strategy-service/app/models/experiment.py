"""
Experiment tracking and ML lifecycle management models.
"""

from enum import Enum as PyEnum
from typing import Dict, Any, List

from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, Float, Enum, ForeignKey, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, UserMixin, MetadataMixin
from app.models.types import StringArray


class ExperimentStatus(PyEnum):
    """Experiment status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class RunStatus(PyEnum):
    """Experiment run status."""
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    KILLED = "killed"
    SCHEDULED = "scheduled"


class ModelStage(PyEnum):
    """Model stage in the registry."""
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    NONE = "none"


class ArtifactType(PyEnum):
    """Artifact type enumeration."""
    MODEL = "model"
    DATASET = "dataset"
    PLOT = "plot"
    REPORT = "report"
    CODE = "code"
    CONFIG = "config"
    METRICS = "metrics"


class Experiment(BaseModel, UserMixin, MetadataMixin):
    """
    MLflow experiment tracking.
    """
    __tablename__ = "experiments"
    
    # Basic information
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    status = Column(Enum(ExperimentStatus), default=ExperimentStatus.ACTIVE, nullable=False, index=True)
    
    # MLflow integration
    mlflow_experiment_id = Column(String(255), unique=True, index=True)
    mlflow_tracking_uri = Column(String(500))
    
    # Experiment metadata
    tags = Column(JSON, default=dict)
    lifecycle_stage = Column(String(50), default="active")
    artifact_location = Column(String(500))
    
    # Organization
    project_name = Column(String(255), index=True)
    team = Column(String(100))
    
    # Tracking
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    last_run_time = Column(String(30))  # ISO datetime string
    
    # Performance summary
    best_metric_value = Column(Float)
    best_metric_name = Column(String(100))
    best_run_id = Column(UUID(as_uuid=True))
    
    # Relationships
    runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentRun(BaseModel, UserMixin):
    """
    Individual experiment run tracking.
    """
    __tablename__ = "experiment_runs"
    
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id"), nullable=False, index=True)
    
    # Run identification
    run_name = Column(String(255), index=True)
    mlflow_run_id = Column(String(255), unique=True, index=True)
    run_uuid = Column(String(255), unique=True, index=True)
    
    # Run metadata
    status = Column(Enum(RunStatus), default=RunStatus.RUNNING, nullable=False, index=True)
    start_time = Column(String(30), nullable=False)  # ISO datetime string
    end_time = Column(String(30))                    # ISO datetime string
    duration_seconds = Column(Integer)
    
    # Source information
    source_type = Column(String(50))  # e.g., 'NOTEBOOK', 'JOB', 'PROJECT', 'LOCAL'
    source_name = Column(String(500))
    source_version = Column(String(100))
    entry_point_name = Column(String(255))
    
    # Git information
    git_commit = Column(String(40))
    git_branch = Column(String(255))
    git_repo_url = Column(String(500))
    
    # Parameters and metrics
    params = Column(JSON, default=dict)
    metrics = Column(JSON, default=dict)
    tags = Column(JSON, default=dict)
    
    # Artifact storage
    artifact_uri = Column(String(500))
    
    # Performance summary
    primary_metric = Column(String(100))
    primary_metric_value = Column(Float)
    
    # Resource usage
    cpu_time_seconds = Column(Float)
    memory_peak_mb = Column(Integer)
    gpu_time_seconds = Column(Float)
    
    # Error information
    error_message = Column(Text)
    stack_trace = Column(Text)
    
    # Relationships
    experiment = relationship("Experiment", back_populates="runs")
    metrics_history = relationship("RunMetricHistory", back_populates="run", cascade="all, delete-orphan")
    artifacts = relationship("RunArtifact", back_populates="run", cascade="all, delete-orphan")


class RunMetricHistory(BaseModel):
    """
    Time-series metrics for experiment runs.
    """
    __tablename__ = "run_metric_history"
    
    run_id = Column(UUID(as_uuid=True), ForeignKey("experiment_runs.id"), nullable=False, index=True)
    
    # Metric information
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(String(30), nullable=False)  # ISO datetime string
    step = Column(Integer, default=0)
    
    # Context
    epoch = Column(Integer)
    batch = Column(Integer)
    
    # Relationships
    run = relationship("ExperimentRun", back_populates="metrics_history")


class RunArtifact(BaseModel):
    """
    Artifacts associated with experiment runs.
    """
    __tablename__ = "run_artifacts"
    
    run_id = Column(UUID(as_uuid=True), ForeignKey("experiment_runs.id"), nullable=False, index=True)
    
    # Artifact information
    artifact_path = Column(String(500), nullable=False)
    artifact_type = Column(Enum(ArtifactType), nullable=False, index=True)
    file_size = Column(BigInteger)
    content_hash = Column(String(64))  # SHA-256 hash
    
    # Storage information
    storage_location = Column(String(500))
    is_directory = Column(Boolean, default=False)
    
    # Metadata
    description = Column(Text)
    tags = Column(JSON, default=dict)
    
    # Relationships
    run = relationship("ExperimentRun", back_populates="artifacts")


class ModelRegistryEntry(BaseModel, UserMixin, MetadataMixin):
    """
    Model registry for versioned model management.
    """
    __tablename__ = "model_registry_entries"
    
    # Model identification
    model_name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    
    # MLflow integration
    mlflow_model_name = Column(String(255), unique=True)
    
    # Current state
    latest_version = Column(Integer, default=0)
    current_stage = Column(Enum(ModelStage), default=ModelStage.NONE, nullable=False, index=True)
    
    # Model metadata
    model_type = Column(String(100))  # e.g., 'regression', 'classification', 'time_series'
    framework = Column(String(100))   # e.g., 'tensorflow', 'pytorch', 'sklearn'
    tags = Column(JSON, default=dict)
    
    # Performance tracking
    total_downloads = Column(BigInteger, default=0)
    total_predictions = Column(BigInteger, default=0)
    avg_inference_time_ms = Column(Float)
    
    # Relationships
    versions = relationship("ModelVersion", back_populates="model_registry", cascade="all, delete-orphan")


class ModelVersion(BaseModel, UserMixin):
    """
    Individual model version in the registry.
    """
    __tablename__ = "model_versions"
    __table_args__ = {'extend_existing': True}
    
    model_registry_id = Column(UUID(as_uuid=True), ForeignKey("model_registry_entries.id"), nullable=False, index=True)
    
    # Version information
    version = Column(Integer, nullable=False)
    description = Column(Text)
    stage = Column(Enum(ModelStage), default=ModelStage.NONE, nullable=False, index=True)
    
    # MLflow integration
    mlflow_version = Column(String(50))
    mlflow_run_id = Column(String(255), index=True)
    
    # Source information
    source_run_id = Column(UUID(as_uuid=True), ForeignKey("experiment_runs.id"))
    source_experiment_id = Column(UUID(as_uuid=True))
    
    # Model artifacts
    model_uri = Column(String(500), nullable=False)
    model_size_bytes = Column(BigInteger)
    
    # Model signature
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    signature = Column(JSON)
    
    # Performance metrics
    validation_metrics = Column(JSON, default=dict)
    training_metrics = Column(JSON, default=dict)
    test_metrics = Column(JSON, default=dict)
    
    # Deployment information
    is_deployed = Column(Boolean, default=False)
    deployment_endpoint = Column(String(500))
    deployment_config = Column(JSON, default=dict)
    
    # Approval workflow
    approved_by = Column(UUID(as_uuid=True))
    approval_timestamp = Column(String(30))
    approval_notes = Column(Text)
    
    # Usage tracking
    download_count = Column(BigInteger, default=0)
    prediction_count = Column(BigInteger, default=0)
    last_used = Column(String(30))  # ISO datetime string
    
    # Tags and metadata
    tags = Column(JSON, default=dict)
    
    # Relationships
    model_registry = relationship("ModelRegistryEntry", back_populates="versions")
    source_run = relationship("ExperimentRun")


class ModelDeployment(BaseModel, UserMixin):
    """
    Model deployment tracking and management.
    """
    __tablename__ = "model_deployments"
    
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False, index=True)
    
    # Deployment information
    deployment_name = Column(String(255), nullable=False, index=True)
    deployment_type = Column(String(100), nullable=False)  # 'batch', 'online', 'streaming'
    environment = Column(String(100), nullable=False)      # 'development', 'staging', 'production'
    
    # Endpoint information
    endpoint_url = Column(String(500))
    endpoint_type = Column(String(100))  # 'rest', 'grpc', 'websocket'
    
    # Configuration
    deployment_config = Column(JSON, default=dict)
    scaling_config = Column(JSON, default=dict)
    resource_requirements = Column(JSON, default=dict)
    
    # Status tracking
    status = Column(String(50), default="deploying", nullable=False, index=True)
    deployed_at = Column(String(30))      # ISO datetime string
    last_updated = Column(String(30))     # ISO datetime string
    health_status = Column(String(50))    # 'healthy', 'unhealthy', 'unknown'
    
    # Performance monitoring
    request_count = Column(BigInteger, default=0)
    error_count = Column(BigInteger, default=0)
    avg_response_time_ms = Column(Float)
    throughput_rps = Column(Float)        # requests per second
    
    # Resource usage
    cpu_usage_percentage = Column(Float)
    memory_usage_mb = Column(Integer)
    disk_usage_mb = Column(Integer)
    
    # Cost tracking
    estimated_cost_per_hour = Column(Float)
    total_cost = Column(Float, default=0.0)
    
    # Relationships
    model_version = relationship("ModelVersion")


class ExperimentComparison(BaseModel, UserMixin):
    """
    Comparison between multiple experiments or runs.
    """
    __tablename__ = "experiment_comparisons"
    
    # Comparison metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Items being compared
    experiment_ids = Column(StringArray())  # List of experiment UUIDs
    run_ids = Column(StringArray())         # List of run UUIDs
    
    # Comparison configuration
    comparison_metrics = Column(StringArray())  # Metrics to compare
    comparison_parameters = Column(StringArray())  # Parameters to compare
    
    # Results
    comparison_results = Column(JSON, default=dict)
    statistical_tests = Column(JSON, default=dict)
    ranking = Column(JSON, default=dict)
    
    # Visualization
    chart_configs = Column(JSON, default=dict)
    report_path = Column(String(500))
    
    # Sharing
    is_public = Column(Boolean, default=False)
    shared_with = Column(StringArray(), default=list)  # User IDs


class HyperparameterOptimization(BaseModel, UserMixin):
    """
    Hyperparameter optimization configuration and tracking.
    """
    __tablename__ = "hyperparameter_optimizations"
    
    # Basic information
    optimization_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id"), nullable=False)
    
    # Optimization configuration
    search_space = Column(JSON, nullable=False)  # Parameter search space
    objective_metric = Column(String(100), nullable=False)
    objective_direction = Column(String(10), default="maximize")  # maximize, minimize
    
    # Search algorithm
    algorithm = Column(String(100), nullable=False)  # 'random', 'grid', 'bayesian', 'tpe'
    algorithm_config = Column(JSON, default=dict)
    
    # Budget constraints
    max_trials = Column(Integer, nullable=False)
    max_duration_hours = Column(Float)
    max_parallel_trials = Column(Integer, default=1)
    
    # Progress tracking
    status = Column(String(50), default="pending", nullable=False, index=True)
    completed_trials = Column(Integer, default=0)
    successful_trials = Column(Integer, default=0)
    failed_trials = Column(Integer, default=0)
    
    # Results
    best_trial_id = Column(UUID(as_uuid=True))
    best_parameters = Column(JSON)
    best_value = Column(Float)
    
    # Resource usage
    total_compute_hours = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # Relationships
    experiment = relationship("Experiment")
    trials = relationship("OptimizationTrial", back_populates="optimization", cascade="all, delete-orphan")


class OptimizationTrial(BaseModel):
    """
    Individual trial in hyperparameter optimization.
    """
    __tablename__ = "optimization_trials"
    
    optimization_id = Column(UUID(as_uuid=True), ForeignKey("hyperparameter_optimizations.id"), nullable=False, index=True)
    
    # Trial information
    trial_number = Column(Integer, nullable=False)
    parameters = Column(JSON, nullable=False)
    
    # Execution
    status = Column(String(50), default="pending", nullable=False)
    start_time = Column(String(30))  # ISO datetime string
    end_time = Column(String(30))    # ISO datetime string
    duration_seconds = Column(Integer)
    
    # Results
    objective_value = Column(Float)
    intermediate_values = Column(JSON, default=list)  # For pruning
    final_metrics = Column(JSON, default=dict)
    
    # Associated run
    experiment_run_id = Column(UUID(as_uuid=True), ForeignKey("experiment_runs.id"))
    
    # Pruning information
    should_prune = Column(Boolean, default=False)
    pruned_at_step = Column(Integer)
    
    # Relationships
    optimization = relationship("HyperparameterOptimization", back_populates="trials")
    experiment_run = relationship("ExperimentRun")