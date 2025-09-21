"""
ML model training related database models for Phase 4: Model Training Orchestrator.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Any, List

from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, Float, Enum, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, UserMixin, MetadataMixin
from app.models.types import StringArray


class JobType(PyEnum):
    """Training job type enumeration."""
    TRAINING = "training"
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"
    VALIDATION = "validation"
    INFERENCE = "inference"
    FEATURE_ENGINEERING = "feature_engineering"


class JobStatus(PyEnum):
    """Job status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class InstanceType(PyEnum):
    """Compute instance type."""
    CPU_SMALL = "cpu_small"
    CPU_MEDIUM = "cpu_medium"
    CPU_LARGE = "cpu_large"
    GPU_T4 = "gpu_t4"
    GPU_V100 = "gpu_v100"
    GPU_A100 = "gpu_a100"
    TPU_V3 = "tpu_v3"
    TPU_V4 = "tpu_v4"


class ModelFramework(PyEnum):
    """ML model framework."""
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    SKLEARN = "sklearn"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    KERAS = "keras"
    CUSTOM = "custom"


class OptimizationObjective(PyEnum):
    """Hyperparameter optimization objective."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class OptimizationAlgorithm(PyEnum):
    """Hyperparameter optimization algorithm."""
    RANDOM_SEARCH = "random_search"
    GRID_SEARCH = "grid_search"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    HYPERBAND = "hyperband"
    POPULATION_BASED = "population_based"


class TrainingPriority(PyEnum):
    """Training job priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TrainingJob(BaseModel, UserMixin, MetadataMixin):
    """
    ML model training job configuration and tracking.
    """
    __tablename__ = "training_jobs"
    
    # Basic information
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    job_name = Column(String(255), nullable=False, index=True)
    job_type = Column(Enum(JobType), nullable=False, index=True)
    
    # Compute configuration
    instance_type = Column(Enum(InstanceType), nullable=False)
    machine_type = Column(String(100))  # Specific machine configuration
    disk_size = Column(Integer, default=100)  # GB
    timeout_hours = Column(Integer, default=24)
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float)
    
    # Job execution
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    priority = Column(Enum(TrainingPriority), default=TrainingPriority.NORMAL, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    progress_percentage = Column(Integer, default=0)
    
    # Queue management
    queued_at = Column(DateTime)
    queue_position = Column(Integer)
    estimated_start_time = Column(DateTime)
    estimated_completion_time = Column(DateTime)
    
    # Configuration
    hyperparameters = Column(JSON, default=dict)
    training_config = Column(JSON, default=dict)
    model_config = Column(JSON, default=dict)
    
    # Results
    final_metrics = Column(JSON, default=dict)
    best_metrics = Column(JSON, default=dict)
    training_logs = Column(StringArray(), default=list)
    error_message = Column(Text)
    
    # Resource usage
    cpu_hours = Column(Float, default=0.0)
    gpu_hours = Column(Float, default=0.0)
    memory_gb_hours = Column(Float, default=0.0)
    
    # External references
    vertex_ai_job_id = Column(String(255))  # Vertex AI job ID
    mlflow_run_id = Column(String(255))     # MLflow run ID
    gcs_output_path = Column(String(500))   # GCS path for outputs
    
    # Relationships
    strategy = relationship("Strategy", back_populates="training_jobs")
    dataset = relationship("Dataset", back_populates="training_jobs")
    artifacts = relationship("ModelArtifact", back_populates="training_job", cascade="all, delete-orphan")
    hyperparameter_trials = relationship("HyperparameterTrial", back_populates="training_job", cascade="all, delete-orphan")


class ModelArtifact(BaseModel):
    """
    ML model artifacts and metadata.
    """
    __tablename__ = "model_artifacts"
    
    training_job_id = Column(UUID(as_uuid=True), ForeignKey("training_jobs.id"), nullable=False)
    model_name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    framework = Column(Enum(ModelFramework), nullable=False)
    
    # File information
    file_path = Column(String(500), nullable=False)  # GCS path
    file_size = Column(BigInteger, default=0)        # bytes
    content_hash = Column(String(64))                # SHA-256 hash
    
    # Model metadata
    model_type = Column(String(100))  # e.g., 'neural_network', 'random_forest'
    input_shape = Column(JSON)
    output_shape = Column(JSON)
    feature_names = Column(StringArray(), default=list)
    target_names = Column(StringArray(), default=list)
    
    # Performance metrics
    training_accuracy = Column(Float)
    validation_accuracy = Column(Float)
    test_accuracy = Column(Float)
    training_loss = Column(Float)
    validation_loss = Column(Float)
    additional_metrics = Column(JSON, default=dict)
    
    # Deployment status
    is_deployed = Column(Boolean, default=False, nullable=False)
    deployment_endpoint = Column(String(500))
    deployment_config = Column(JSON, default=dict)
    
    # Usage tracking
    inference_count = Column(BigInteger, default=0)
    last_inference = Column(String(30))  # ISO datetime string
    
    # Relationships
    training_job = relationship("TrainingJob", back_populates="artifacts")
    
    # Indexes
    __table_args__ = (
        Index('idx_artifacts_training_job', 'training_job_id'),
        Index('idx_artifacts_model_name', 'model_name'),
        Index('idx_artifacts_framework', 'framework'),
        Index('idx_artifacts_deployed', 'is_deployed'),
    )


class HyperparameterTrial(BaseModel, MetadataMixin):
    """
    Individual hyperparameter tuning trial.
    """
    __tablename__ = "hyperparameter_trials"
    
    training_job_id = Column(UUID(as_uuid=True), ForeignKey("training_jobs.id"))
    tuning_job_id = Column(UUID(as_uuid=True), ForeignKey("hyperparameter_tuning_jobs.id"))
    trial_number = Column(Integer, nullable=False)
    hyperparameters = Column(JSON, nullable=False)
    
    # Trial execution
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Results
    final_metrics = Column(JSON, default=dict)
    best_epoch = Column(Integer)
    early_stopped = Column(Boolean, default=False)
    
    # Objective value for optimization
    objective_value = Column(Float)
    objective_metric = Column(String(100))  # The metric being optimized
    
    # Resource usage
    compute_cost = Column(Float, default=0.0)
    
    # External references
    vertex_ai_trial_id = Column(String(255))
    mlflow_run_id = Column(String(255))
    
    # Relationships
    training_job = relationship("TrainingJob", back_populates="hyperparameter_trials")
    tuning_job = relationship("HyperparameterTuningJob", back_populates="trials")
    
    # Indexes
    __table_args__ = (
        Index('idx_trials_training_job', 'training_job_id'),
        Index('idx_trials_tuning_job', 'tuning_job_id'),
        Index('idx_trials_status', 'status'),
        Index('idx_trials_objective_value', 'objective_value'),
    )


class TrainingMetric(BaseModel):
    """
    Time-series training metrics for monitoring progress.
    """
    __tablename__ = "training_metrics"
    
    training_job_id = Column(UUID(as_uuid=True), ForeignKey("training_jobs.id"), nullable=False)
    trial_id = Column(UUID(as_uuid=True), ForeignKey("hyperparameter_trials.id"))
    
    # Metric information
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50))  # 'loss', 'accuracy', 'custom'
    dataset_split = Column(String(20))  # 'train', 'validation', 'test'
    
    # Time information
    epoch = Column(Integer)
    step = Column(Integer)
    timestamp = Column(String(30), nullable=False)  # ISO datetime string
    
    # Additional context
    batch_size = Column(Integer)
    learning_rate = Column(Float)
    
    # Relationships
    training_job = relationship("TrainingJob")
    trial = relationship("HyperparameterTrial")
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_training_job', 'training_job_id'),
        Index('idx_metrics_trial', 'trial_id'),
        Index('idx_metrics_name', 'metric_name'),
        Index('idx_metrics_timestamp', 'timestamp'),
    )


class ModelRegistry(BaseModel, UserMixin):
    """
    Centralized model registry for version control.
    """
    __tablename__ = "model_registry"
    
    model_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    model_type = Column(String(100), nullable=False)
    framework = Column(Enum(ModelFramework), nullable=False)
    
    # Version information
    current_version = Column(String(50))
    latest_version = Column(String(50))
    
    # Model metadata
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    feature_importance = Column(JSON, default=dict)
    model_signature = Column(JSON)
    
    # Usage and performance
    total_predictions = Column(BigInteger, default=0)
    avg_prediction_time_ms = Column(Float)
    success_rate = Column(Float, default=1.0)
    
    # Tags and labels
    tags = Column(StringArray(), default=list)
    labels = Column(JSON, default=dict)
    
    # Relationships
    versions = relationship("ModelVersion", back_populates="model_registry", cascade="all, delete-orphan")


class ModelVersion(BaseModel):
    """
    Individual model version in the registry.
    """
    __tablename__ = "model_versions"
    __table_args__ = {'extend_existing': True}
    
    model_registry_id = Column(UUID(as_uuid=True), ForeignKey("model_registry.id"), nullable=False)
    version = Column(String(50), nullable=False)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("model_artifacts.id"), nullable=False)
    
    # Version metadata
    description = Column(Text)
    changelog = Column(Text)
    is_current = Column(Boolean, default=False, nullable=False)
    stage = Column(String(50), default="development")  # development, staging, production, archived
    
    # Performance comparison
    performance_metrics = Column(JSON, default=dict)
    performance_improvement = Column(Float)  # vs previous version
    
    # Approval and governance
    approved_by = Column(UUID(as_uuid=True))
    approval_date = Column(String(30))
    approval_notes = Column(Text)
    
    # Relationships
    model_registry = relationship("ModelRegistry", back_populates="versions")
    artifact = relationship("ModelArtifact")
    
    # Indexes
    __table_args__ = (
        Index('idx_model_versions_registry', 'model_registry_id'),
        Index('idx_model_versions_version', 'version'),
        Index('idx_model_versions_current', 'is_current'),
        Index('idx_model_versions_stage', 'stage'),
    )


class ComputeResource(BaseModel):
    """
    Available compute resources for training.
    """
    __tablename__ = "compute_resources"
    
    resource_name = Column(String(255), nullable=False, unique=True, index=True)
    resource_type = Column(Enum(InstanceType), nullable=False)
    provider = Column(String(100), nullable=False)  # 'gcp', 'aws', 'azure'
    region = Column(String(100), nullable=False)
    
    # Resource specifications
    cpu_cores = Column(Integer)
    memory_gb = Column(Integer)
    gpu_count = Column(Integer, default=0)
    gpu_type = Column(String(100))
    disk_gb = Column(Integer)
    network_bandwidth_gbps = Column(Float)
    
    # Pricing
    cost_per_hour = Column(Float, nullable=False)
    preemptible_cost_per_hour = Column(Float)
    
    # Availability
    is_available = Column(Boolean, default=True, nullable=False)
    max_concurrent_jobs = Column(Integer, default=1)
    current_usage = Column(Integer, default=0)
    
    # Performance benchmarks
    benchmark_score = Column(Float)
    benchmark_date = Column(DateTime)
    
    # Relationships
    training_jobs = relationship("TrainingJob")
    
    # Indexes
    __table_args__ = (
        Index('idx_compute_resources_name', 'resource_name'),
        Index('idx_compute_resources_type', 'resource_type'),
        Index('idx_compute_resources_provider', 'provider'),
        Index('idx_compute_resources_available', 'is_available'),
    )


class HyperparameterTuningJob(BaseModel, UserMixin, MetadataMixin):
    """
    Hyperparameter tuning job configuration and tracking.
    """
    __tablename__ = "hyperparameter_tuning_jobs"
    
    # Basic information
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    job_name = Column(String(255), nullable=False, index=True)
    
    # Optimization configuration
    optimization_algorithm = Column(Enum(OptimizationAlgorithm), nullable=False)
    optimization_objective = Column(Enum(OptimizationObjective), nullable=False)
    objective_metric = Column(String(100), nullable=False)  # The metric to optimize
    max_trials = Column(Integer, default=100)
    max_parallel_trials = Column(Integer, default=4)
    max_trial_duration_hours = Column(Integer, default=4)
    
    # Search space
    parameter_space = Column(JSON, nullable=False)  # Hyperparameter search space
    early_stopping_config = Column(JSON, default=dict)
    
    # Job execution
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    priority = Column(Enum(TrainingPriority), default=TrainingPriority.NORMAL, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    progress_percentage = Column(Integer, default=0)
    
    # Compute configuration
    instance_type = Column(Enum(InstanceType), nullable=False)
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float)
    
    # Results
    best_trial_id = Column(UUID(as_uuid=True), ForeignKey("hyperparameter_trials.id"))
    best_hyperparameters = Column(JSON, default=dict)
    best_objective_value = Column(Float)
    completed_trials = Column(Integer, default=0)
    failed_trials = Column(Integer, default=0)
    
    # External references
    vertex_ai_job_id = Column(String(255))
    mlflow_experiment_id = Column(String(255))
    
    # Relationships
    strategy = relationship("Strategy")
    dataset = relationship("Dataset")
    trials = relationship("HyperparameterTrial", back_populates="tuning_job", cascade="all, delete-orphan")
    best_trial = relationship("HyperparameterTrial", foreign_keys=[best_trial_id], post_update=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_tuning_jobs_user_id', 'user_id'),
        Index('idx_tuning_jobs_status', 'status'),
        Index('idx_tuning_jobs_strategy_id', 'strategy_id'),
        Index('idx_tuning_jobs_dataset_id', 'dataset_id'),
    )


class ResourceQuota(BaseModel, UserMixin, MetadataMixin):
    """
    User resource quotas and usage tracking.
    """
    __tablename__ = "resource_quotas"
    
    # Quota limits (per month)
    max_cpu_hours = Column(Float, default=100.0)
    max_gpu_hours = Column(Float, default=10.0)
    max_memory_gb_hours = Column(Float, default=1000.0)
    max_storage_gb = Column(Float, default=100.0)
    max_concurrent_jobs = Column(Integer, default=5)
    max_monthly_cost = Column(Float, default=1000.0)
    
    # Current usage (this month)
    used_cpu_hours = Column(Float, default=0.0)
    used_gpu_hours = Column(Float, default=0.0)
    used_memory_gb_hours = Column(Float, default=0.0)
    used_storage_gb = Column(Float, default=0.0)
    current_concurrent_jobs = Column(Integer, default=0)
    current_monthly_cost = Column(Float, default=0.0)
    
    # Reset tracking
    quota_period_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    quota_period_end = Column(DateTime, nullable=False)
    last_reset = Column(DateTime)
    
    # Alerts and notifications
    cpu_alert_threshold = Column(Float, default=0.8)  # Alert at 80% usage
    gpu_alert_threshold = Column(Float, default=0.8)
    cost_alert_threshold = Column(Float, default=0.8)
    alert_enabled = Column(Boolean, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_resource_quotas_user_id', 'user_id'),
        Index('idx_resource_quotas_period', 'quota_period_start', 'quota_period_end'),
    )


class TrainingTemplate(BaseModel, UserMixin, MetadataMixin):
    """
    Reusable training configuration templates.
    """
    __tablename__ = "training_templates"
    
    # Basic information
    template_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), nullable=False)  # 'deep_learning', 'classical_ml', 'time_series'
    
    # Template configuration
    model_framework = Column(Enum(ModelFramework), nullable=False)
    default_hyperparameters = Column(JSON, default=dict)
    training_config = Column(JSON, default=dict)
    model_config = Column(JSON, default=dict)
    
    # Compute recommendations
    recommended_instance_type = Column(Enum(InstanceType))
    min_memory_gb = Column(Integer)
    estimated_training_time_hours = Column(Float)
    
    # Usage and validation
    is_public = Column(Boolean, default=False)
    is_validated = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_performance_score = Column(Float)
    
    # Versioning
    version = Column(String(50), default="1.0.0")
    parent_template_id = Column(UUID(as_uuid=True), ForeignKey("training_templates.id"))
    
    # Tags and metadata
    tags = Column(StringArray(), default=list)
    documentation = Column(Text)
    example_code = Column(Text)
    
    # Relationships
    parent_template = relationship("TrainingTemplate", remote_side="TrainingTemplate.id")
    child_templates = relationship("TrainingTemplate", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_training_templates_category', 'category'),
        Index('idx_training_templates_framework', 'model_framework'),
        Index('idx_training_templates_public', 'is_public'),
        Index('idx_training_templates_usage', 'usage_count'),
    )