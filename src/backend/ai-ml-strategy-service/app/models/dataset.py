"""
Dataset-related database models.
"""

from enum import Enum as PyEnum
from typing import Dict, Any, List

from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, UserMixin, MetadataMixin


class DataSource(PyEnum):
    """Data source enumeration."""
    PLATFORM = "platform"
    USER_UPLOAD = "user_upload"
    EXTERNAL = "external"
    GENERATED = "generated"


class DatasetStatus(PyEnum):
    """Dataset processing status."""
    UPLOADING = "uploading"
    VALIDATING = "validating"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class DataFormat(PyEnum):
    """Supported data formats."""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    EXCEL = "excel"
    FEATHER = "feather"


class Dataset(BaseModel, UserMixin, MetadataMixin):
    """
    Dataset model for storing market data and custom datasets.
    """
    __tablename__ = "datasets"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    source = Column(Enum(DataSource), nullable=False, index=True)
    asset_class = Column(String(50), nullable=False, index=True)  # CRYPTO, STOCKS, FOREX, etc.
    symbols = Column(ARRAY(String), default=list)
    timeframe = Column(String(20))  # 1m, 5m, 1h, 1d, etc.
    start_date = Column(String(20))  # ISO date string
    end_date = Column(String(20))    # ISO date string
    columns = Column(ARRAY(String), default=list)
    row_count = Column(BigInteger, default=0)
    file_size = Column(BigInteger, default=0)  # in bytes
    data_format = Column(Enum(DataFormat), nullable=False)
    status = Column(Enum(DatasetStatus), default=DatasetStatus.UPLOADING, nullable=False, index=True)
    
    # Validation
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_errors = Column(ARRAY(String), default=list)
    validation_warnings = Column(ARRAY(String), default=list)
    
    # File storage
    file_path = Column(String(500))  # Path in cloud storage
    original_filename = Column(String(255))
    content_hash = Column(String(64))  # SHA-256 hash
    
    # Data quality metrics
    missing_values_count = Column(JSON, default=dict)  # {column: count}
    data_types = Column(JSON, default=dict)  # {column: type}
    duplicate_rows = Column(Integer, default=0)
    
    # Usage tracking
    download_count = Column(Integer, default=0)
    last_accessed = Column(String(30))  # ISO datetime string
    
    # Relationships
    training_jobs = relationship("TrainingJob", back_populates="dataset")
    backtest_jobs = relationship("BacktestJob", back_populates="dataset")
    debug_sessions = relationship("DebugSession", back_populates="dataset")
    preprocessing_jobs = relationship("DataPreprocessingJob", back_populates="dataset")


class DatasetPreview(BaseModel):
    """
    Dataset preview with sample data and statistics.
    """
    __tablename__ = "dataset_previews"
    
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False, unique=True)
    sample_data = Column(JSON, nullable=False)  # First N rows as JSON
    statistics = Column(JSON, default=dict)     # Basic statistics
    missing_values = Column(JSON, default=dict) # Missing value counts
    data_types = Column(JSON, default=dict)     # Column data types
    chart_data = Column(JSON, default=dict)     # Data for visualization
    correlation_matrix = Column(JSON, default=dict)
    
    # Relationships
    dataset = relationship("Dataset")


class DataPreprocessingJob(BaseModel, UserMixin):
    """
    Data preprocessing and cleaning job.
    """
    __tablename__ = "data_preprocessing_jobs"
    
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    job_name = Column(String(255), nullable=False)
    preprocessing_steps = Column(JSON, nullable=False)  # List of preprocessing operations
    output_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    status = Column(String(50), default="pending", nullable=False, index=True)
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Processing statistics
    rows_processed = Column(BigInteger, default=0)
    rows_removed = Column(BigInteger, default=0)
    columns_added = Column(Integer, default=0)
    columns_removed = Column(Integer, default=0)
    
    # Relationships
    dataset = relationship("Dataset", foreign_keys=[dataset_id], back_populates="preprocessing_jobs")
    output_dataset = relationship("Dataset", foreign_keys=[output_dataset_id])


class DatasetTag(BaseModel):
    """
    Tags for categorizing datasets.
    """
    __tablename__ = "dataset_tags"
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    color = Column(String(7))  # Hex color code
    usage_count = Column(Integer, default=0)


class DatasetTagAssociation(BaseModel):
    """
    Many-to-many association between datasets and tags.
    """
    __tablename__ = "dataset_tag_associations"
    
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("dataset_tags.id"), nullable=False)
    
    # Relationships
    dataset = relationship("Dataset")
    tag = relationship("DatasetTag")


class MarketDataStream(BaseModel):
    """
    Real-time market data stream configuration.
    """
    __tablename__ = "market_data_streams"
    
    name = Column(String(255), nullable=False, index=True)
    symbols = Column(ARRAY(String), nullable=False)
    data_source = Column(String(100), nullable=False)  # e.g., 'binance', 'polygon', 'alpaca'
    timeframe = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_update = Column(String(30))  # ISO datetime string
    
    # Stream configuration
    api_key_id = Column(UUID(as_uuid=True))  # Reference to encrypted API key
    endpoint_url = Column(String(500))
    rate_limit = Column(Integer, default=100)  # requests per minute
    
    # Quality metrics
    messages_received = Column(BigInteger, default=0)
    messages_processed = Column(BigInteger, default=0)
    last_message_timestamp = Column(String(30))
    connection_uptime = Column(Float, default=0.0)  # percentage


class DataValidationRule(BaseModel):
    """
    Custom data validation rules for datasets.
    """
    __tablename__ = "data_validation_rules"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    rule_type = Column(String(50), nullable=False)  # 'range', 'format', 'custom', etc.
    rule_config = Column(JSON, nullable=False)      # Rule-specific configuration
    is_active = Column(Boolean, default=True, nullable=False)
    severity = Column(String(20), default="error")  # 'error', 'warning', 'info'
    
    # Usage tracking
    applied_count = Column(Integer, default=0)
    violations_count = Column(Integer, default=0)