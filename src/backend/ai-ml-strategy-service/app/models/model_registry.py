"""
Database models for ML model registry, versioning, and deployment tracking.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.base import Base


class ModelStatus(str, Enum):
    """Model status enumeration"""
    TRAINING = "training"
    TRAINED = "trained" 
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class DeploymentStatus(str, Enum):
    """Deployment status enumeration"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    UPDATING = "updating"
    SCALING = "scaling"
    STOPPING = "stopping"
    STOPPED = "stopped"


class Model(Base):
    """
    Core model registry table - represents a logical model (e.g., "EURUSD_Predictor")
    """
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(100), nullable=False)  # e.g., "prediction", "signal", "risk"
    strategy_type = Column(String(100))  # e.g., "momentum", "mean_reversion", "arbitrage"
    
    # Model metadata
    framework = Column(String(50))  # "scikit-learn", "tensorflow", "pytorch", "xgboost"
    model_type = Column(String(100))  # "random_forest", "neural_network", "svm", etc.
    input_features = Column(JSONB)  # List of feature names and types
    output_schema = Column(JSONB)  # Expected output format
    
    # Business metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    team = Column(String(100))
    project = Column(String(100))
    tags = Column(JSONB)  # Array of tags for organization
    
    # Status and lifecycle
    status = Column(String(20), default=ModelStatus.TRAINING)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
    deployments = relationship("ModelDeployment", back_populates="model", cascade="all, delete-orphan")
    training_jobs = relationship("TrainingJob", back_populates="model")
    
    # Indexes
    __table_args__ = (
        Index('ix_models_name', 'name'),
        Index('ix_models_category', 'category'),
        Index('ix_models_status', 'status'),
        Index('ix_models_created_by', 'created_by'),
        Index('ix_models_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'uuid': str(self.uuid),
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'strategy_type': self.strategy_type,
            'framework': self.framework,
            'model_type': self.model_type,
            'input_features': self.input_features,
            'output_schema': self.output_schema,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': self.tags,
            'version_count': len(self.versions) if self.versions else 0,
            'latest_version': self.get_latest_version()
        }
    
    def get_latest_version(self) -> Optional[str]:
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.created_at).version


class ModelVersion(Base):
    """
    Model version registry - tracks individual model versions
    """
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    version = Column(String(50), nullable=False)  # e.g., "1.0.0", "2.1.3"
    
    # Artifact storage
    artifacts_path = Column(String(500), nullable=False)  # S3/GCS path to model files
    model_file_size = Column(Integer)  # Size in bytes
    code_version = Column(String(100))  # Git commit hash or code version
    
    # Training metadata
    training_config = Column(JSONB)  # Hyperparameters, training settings
    dataset_version = Column(String(100))  # Dataset version used for training
    training_duration = Column(Integer)  # Training time in seconds
    training_job_id = Column(String(100))  # Reference to training job
    
    # Model lineage
    parent_version_id = Column(Integer, ForeignKey("model_versions.id"))  # For model evolution tracking
    experiment_id = Column(String(100))  # MLflow experiment ID
    run_id = Column(String(100))  # MLflow run ID
    
    # Performance metrics
    performance_metrics = Column(JSONB)  # Validation metrics (accuracy, precision, recall, etc.)
    business_metrics = Column(JSONB)  # Trading-specific metrics (sharpe, drawdown, etc.)
    benchmark_results = Column(JSONB)  # Comparison with baseline models
    
    # Validation and testing
    validation_status = Column(String(20), default="pending")  # pending, passed, failed
    test_results = Column(JSONB)  # Unit test, integration test results
    model_signature = Column(String(500))  # Model input/output signature hash
    
    # Deployment readiness
    deployment_ready = Column(Boolean, default=False)
    deployment_requirements = Column(JSONB)  # CPU, memory, GPU requirements
    compatibility_check = Column(JSONB)  # Compatibility with serving infrastructure
    
    # Metadata
    description = Column(Text)
    changelog = Column(Text)  # Changes from previous version
    release_notes = Column(Text)
    
    # Status
    status = Column(String(20), default=ModelStatus.TRAINING)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    model = relationship("Model", back_populates="versions")
    parent_version = relationship("ModelVersion", remote_side=[id])
    deployments = relationship("ModelDeployment", back_populates="model_version")
    
    # Indexes
    __table_args__ = (
        Index('ix_model_versions_model_version', 'model_id', 'version', unique=True),
        Index('ix_model_versions_status', 'status'),
        Index('ix_model_versions_created_at', 'created_at'),
        Index('ix_model_versions_deployment_ready', 'deployment_ready'),
        {'extend_existing': True}
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'uuid': str(self.uuid),
            'model_id': self.model_id,
            'version': self.version,
            'artifacts_path': self.artifacts_path,
            'model_file_size': self.model_file_size,
            'code_version': self.code_version,
            'training_config': self.training_config,
            'dataset_version': self.dataset_version,
            'training_duration': self.training_duration,
            'performance_metrics': self.performance_metrics,
            'business_metrics': self.business_metrics,
            'validation_status': self.validation_status,
            'deployment_ready': self.deployment_ready,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'description': self.description,
            'changelog': self.changelog
        }


class ModelDeployment(Base):
    """
    Model deployment registry - tracks deployed model instances
    """
    __tablename__ = "model_deployments"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=False)
    
    # Deployment configuration
    deployment_name = Column(String(255), nullable=False, unique=True)
    environment = Column(String(50), nullable=False)  # dev, staging, prod
    deployment_config = Column(JSONB)  # Serving configuration
    
    # Kubernetes configuration
    k8s_namespace = Column(String(100))
    k8s_deployment_name = Column(String(100))
    k8s_service_name = Column(String(100))
    k8s_config = Column(JSONB)  # Full K8s deployment spec
    
    # Serving configuration
    endpoint_url = Column(String(500))
    api_version = Column(String(20), default="v1")
    serving_framework = Column(String(50))  # "fastapi", "flask", "torchserve", etc.
    
    # Resource allocation
    cpu_request = Column(String(20))  # e.g., "500m"
    cpu_limit = Column(String(20))    # e.g., "2000m"
    memory_request = Column(String(20))  # e.g., "1Gi"
    memory_limit = Column(String(20))    # e.g., "4Gi"
    gpu_request = Column(Integer, default=0)
    
    # Scaling configuration
    min_replicas = Column(Integer, default=1)
    max_replicas = Column(Integer, default=10)
    target_cpu_utilization = Column(Integer, default=70)
    target_rps = Column(Integer)  # Target requests per second for scaling
    
    # Health and monitoring
    health_check_path = Column(String(200), default="/health")
    metrics_path = Column(String(200), default="/metrics")
    health_metrics = Column(JSONB)  # Current health status
    
    # Traffic routing
    traffic_percentage = Column(Integer, default=100)  # For canary/blue-green deployments
    load_balancer_config = Column(JSONB)
    
    # Status and lifecycle
    status = Column(String(20), default=DeploymentStatus.PENDING)
    deployment_status_message = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    deployed_at = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    model = relationship("Model", back_populates="deployments")
    model_version = relationship("ModelVersion", back_populates="deployments")
    
    # Indexes
    __table_args__ = (
        Index('ix_deployments_model_id', 'model_id'),
        Index('ix_deployments_status', 'status'),
        Index('ix_deployments_environment', 'environment'),
        Index('ix_deployments_created_at', 'created_at'),
        {'extend_existing': True}
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'uuid': str(self.uuid),
            'model_id': self.model_id,
            'model_version_id': self.model_version_id,
            'deployment_name': self.deployment_name,
            'environment': self.environment,
            'endpoint_url': self.endpoint_url,
            'api_version': self.api_version,
            'serving_framework': self.serving_framework,
            'cpu_request': self.cpu_request,
            'cpu_limit': self.cpu_limit,
            'memory_request': self.memory_request,
            'memory_limit': self.memory_limit,
            'gpu_request': self.gpu_request,
            'min_replicas': self.min_replicas,
            'max_replicas': self.max_replicas,
            'target_cpu_utilization': self.target_cpu_utilization,
            'status': self.status,
            'deployment_status_message': self.deployment_status_message,
            'is_active': self.is_active,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'health_metrics': self.health_metrics,
            'traffic_percentage': self.traffic_percentage
        }


class ModelABTest(Base):
    """
    A/B testing configuration for model comparison
    """
    __tablename__ = "model_ab_tests"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Test configuration
    control_model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=False)
    treatment_model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=False)
    traffic_split = Column(Float, default=0.5)  # Fraction of traffic to treatment (0.0-1.0)
    
    # Test parameters
    test_duration_days = Column(Integer, default=7)
    success_criteria = Column(JSONB)  # Statistical significance requirements
    business_metrics = Column(JSONB)  # Metrics to track (return, sharpe, etc.)
    
    # Test results
    statistical_results = Column(JSONB)  # p-values, confidence intervals, etc.
    business_results = Column(JSONB)    # Performance comparison
    conclusion = Column(Text)  # Test conclusion and recommendations
    
    # Status
    status = Column(String(20), default="planning")  # planning, running, completed, stopped
    is_active = Column(Boolean, default=False)
    
    # Timestamps
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    control_version = relationship("ModelVersion", foreign_keys=[control_model_version_id])
    treatment_version = relationship("ModelVersion", foreign_keys=[treatment_model_version_id])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'uuid': str(self.uuid),
            'name': self.name,
            'description': self.description,
            'control_model_version_id': self.control_model_version_id,
            'treatment_model_version_id': self.treatment_model_version_id,
            'traffic_split': self.traffic_split,
            'test_duration_days': self.test_duration_days,
            'success_criteria': self.success_criteria,
            'statistical_results': self.statistical_results,
            'business_results': self.business_results,
            'conclusion': self.conclusion,
            'status': self.status,
            'is_active': self.is_active,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ModelMetrics(Base):
    """
    Time-series metrics for model performance tracking
    """
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True)
    model_deployment_id = Column(Integer, ForeignKey("model_deployments.id"), nullable=False)
    
    # Metric metadata
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    metric_type = Column(String(50))  # "performance", "business", "technical"
    
    # Context
    environment = Column(String(50))
    data_window_start = Column(DateTime)
    data_window_end = Column(DateTime)
    sample_size = Column(Integer)
    
    # Metadata
    tags = Column(JSONB)  # Additional metadata
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    deployment = relationship("ModelDeployment")
    
    # Indexes
    __table_args__ = (
        Index('ix_model_metrics_deployment_metric', 'model_deployment_id', 'metric_name'),
        Index('ix_model_metrics_recorded_at', 'recorded_at'),
        Index('ix_model_metrics_metric_type', 'metric_type'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'model_deployment_id': self.model_deployment_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'metric_type': self.metric_type,
            'environment': self.environment,
            'data_window_start': self.data_window_start.isoformat() if self.data_window_start else None,
            'data_window_end': self.data_window_end.isoformat() if self.data_window_end else None,
            'sample_size': self.sample_size,
            'tags': self.tags,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }