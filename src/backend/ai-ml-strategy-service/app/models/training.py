"""
ML model training related database models.
"""

from enum import Enum as PyEnum
from typing import Dict, Any, List

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, Enum, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, UserMixin, MetadataMixin


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
    CUSTOM = "custom"


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
    start_time = Column(String(30))  # ISO datetime string
    end_time = Column(String(30))    # ISO datetime string
    duration_seconds = Column(Integer)
    progress_percentage = Column(Integer, default=0)
    
    # Configuration
    hyperparameters = Column(JSON, default=dict)
    training_config = Column(JSON, default=dict)
    model_config = Column(JSON, default=dict)
    
    # Results
    final_metrics = Column(JSON, default=dict)
    best_metrics = Column(JSON, default=dict)
    training_logs = Column(ARRAY(String), default=list)
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
    feature_names = Column(ARRAY(String), default=list)
    target_names = Column(ARRAY(String), default=list)
    
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


class HyperparameterTrial(BaseModel):
    """
    Individual hyperparameter tuning trial.
    """
    __tablename__ = "hyperparameter_trials"
    
    training_job_id = Column(UUID(as_uuid=True), ForeignKey("training_jobs.id"), nullable=False)
    trial_number = Column(Integer, nullable=False)
    hyperparameters = Column(JSON, nullable=False)
    
    # Trial execution
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    start_time = Column(String(30))
    end_time = Column(String(30))
    duration_seconds = Column(Integer)
    
    # Results
    final_metrics = Column(JSON, default=dict)
    best_epoch = Column(Integer)
    early_stopped = Column(Boolean, default=False)
    
    # Objective value for optimization
    objective_value = Column(Float)
    objective_metric = Column(String(100))  # The metric being optimized
    
    # Relationships
    training_job = relationship("TrainingJob", back_populates="hyperparameter_trials")


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
    tags = Column(ARRAY(String), default=list)
    labels = Column(JSON, default=dict)
    
    # Relationships
    versions = relationship("ModelVersion", back_populates="model_registry", cascade="all, delete-orphan")


class ModelVersion(BaseModel):
    """
    Individual model version in the registry.
    """
    __tablename__ = "model_versions"
    
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
    benchmark_date = Column(String(30))