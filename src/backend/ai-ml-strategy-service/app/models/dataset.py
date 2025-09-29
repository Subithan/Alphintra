"""
Dataset-related database models for Phase 3: Dataset Management.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Any, List

from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, Float, Enum, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, UserMixin, MetadataMixin
from app.models.types import StringArray


class DataSource(PyEnum):
    """Data source enumeration."""
    PLATFORM = "platform"
    USER_UPLOAD = "user_upload"
    EXTERNAL = "external"
    GENERATED = "generated"
    SYNTHETIC = "synthetic"


class DatasetStatus(PyEnum):
    """Dataset processing status."""
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    VALIDATED = "validated"
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
    HDF5 = "hdf5"


class DataFrequency(PyEnum):
    """Data frequency/timeframe."""
    TICK = "tick"
    SECOND_1 = "1s"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class AssetClass(PyEnum):
    """Asset class categories."""
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FOREX = "forex"
    COMMODITIES = "commodities"
    BONDS = "bonds"
    OPTIONS = "options"
    FUTURES = "futures"


class Dataset(BaseModel, UserMixin, MetadataMixin):
    """
    Enhanced dataset model for comprehensive data management.
    """
    __tablename__ = "datasets"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    source = Column(Enum(DataSource), nullable=False, index=True)
    asset_class = Column(Enum(AssetClass), nullable=False, index=True)
    symbols = Column(StringArray(), default=list)
    frequency = Column(Enum(DataFrequency))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    columns = Column(StringArray(), default=list)
    row_count = Column(BigInteger, default=0)
    file_size = Column(BigInteger, default=0)  # in bytes
    data_format = Column(Enum(DataFormat), nullable=False)
    status = Column(Enum(DatasetStatus), default=DatasetStatus.UPLOADED, nullable=False, index=True)
    
    # Validation
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_errors = Column(JSON, default=list)
    validation_warnings = Column(JSON, default=list)
    
    # File storage
    file_path = Column(String(500))  # Path in cloud storage
    original_filename = Column(String(255))
    content_hash = Column(String(64))  # SHA-256 hash
    storage_backend = Column(String(50), default="local")  # local, gcs, s3
    compression = Column(String(20))  # gzip, parquet, etc.
    
    # Data characteristics
    missing_values_count = Column(JSON, default=dict)  # {column: count}
    data_types = Column(JSON, default=dict)  # {column: type}
    duplicate_rows = Column(Integer, default=0)
    
    # Quality metrics
    completeness_score = Column(Float)  # Percentage of non-null values
    quality_score = Column(Float)  # Overall quality score (0-1)
    
    # Processing metadata
    processing_config = Column(JSON)  # Configuration for processing
    feature_columns = Column(JSON)  # Engineered feature columns
    target_columns = Column(JSON)  # Target/label columns
    
    # Usage tracking
    download_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    # Tags and categorization
    tags = Column(StringArray(), default=list)
    category = Column(String(100))
    is_public = Column(Boolean, default=False)
    
    # Relationships
    training_jobs = relationship("TrainingJob", back_populates="dataset")
    backtest_jobs = relationship("BacktestJob", back_populates="dataset")
    debug_sessions = relationship("DebugSession", back_populates="dataset")
    preprocessing_jobs = relationship("DataPreprocessingJob", foreign_keys="DataPreprocessingJob.dataset_id", back_populates="dataset")
    validation_reports = relationship("DatasetValidationReport", back_populates="dataset", cascade="all, delete-orphan")
    statistics = relationship("DatasetStatistics", back_populates="dataset", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_datasets_user_id', 'user_id'),
        Index('idx_datasets_asset_class', 'asset_class'),
        Index('idx_datasets_source', 'source'),
        Index('idx_datasets_status', 'status'),
        Index('idx_datasets_symbols', 'symbols', postgresql_using='gin'),
        Index('idx_datasets_tags', 'tags', postgresql_using='gin'),
    )


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
    symbols = Column(StringArray(), nullable=False)
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


class DatasetValidationReport(BaseModel, MetadataMixin):
    """
    Detailed validation report for datasets.
    """
    __tablename__ = "dataset_validation_reports"
    
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    
    # Validation results
    is_valid = Column(Boolean, nullable=False)
    validation_type = Column(String(50), nullable=False)  # schema, data_quality, completeness
    
    # Detailed results
    errors = Column(JSON, default=list)  # List of error details
    warnings = Column(JSON, default=list)  # List of warning details
    suggestions = Column(JSON, default=list)  # List of improvement suggestions
    
    # Metrics
    metrics = Column(JSON, default=dict)  # Validation metrics
    
    # Processing info
    validation_duration = Column(Float)  # Duration in seconds
    validator_version = Column(String(20))
    
    # Relationship
    dataset = relationship("Dataset", back_populates="validation_reports")


class DatasetStatistics(BaseModel, MetadataMixin):
    """
    Statistical information about datasets.
    """
    __tablename__ = "dataset_statistics"
    
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False, unique=True)
    
    # Basic statistics
    total_rows = Column(BigInteger, nullable=False)
    total_columns = Column(Integer, nullable=False)
    null_count = Column(BigInteger, default=0)
    duplicate_count = Column(BigInteger, default=0)
    
    # Column-wise statistics
    column_stats = Column(JSON, default=dict)  # Statistics for each column
    correlation_matrix = Column(JSON, default=dict)  # Correlation between numeric columns
    
    # Data distribution
    date_range = Column(JSON, default=dict)  # Min/max dates
    symbol_distribution = Column(JSON, default=dict)  # Count per symbol
    frequency_stats = Column(JSON, default=dict)  # Data frequency analysis
    
    # Quality metrics
    completeness_by_column = Column(JSON, default=dict)  # Completeness per column
    outlier_stats = Column(JSON, default=dict)  # Outlier detection results
    missing_data_patterns = Column(JSON, default=dict)  # Missing data analysis
    
    # Time series specific
    gaps_detected = Column(JSON, default=dict)  # Time gaps in data
    seasonality_stats = Column(JSON, default=dict)  # Seasonality analysis
    trend_analysis = Column(JSON, default=dict)  # Trend analysis results
    
    # Update tracking
    last_computed = Column(DateTime, nullable=False, default=datetime.utcnow)
    computation_duration = Column(Float)  # Time to compute stats
    
    # Relationship
    dataset = relationship("Dataset", back_populates="statistics")


class DataIngestionJob(BaseModel, UserMixin, MetadataMixin):
    """
    Data ingestion job for automated data collection.
    """
    __tablename__ = "data_ingestion_jobs"
    
    # Job configuration
    job_name = Column(String(255), nullable=False)
    data_source = Column(String(100), nullable=False)  # binance, coinbase, yahoo_finance, etc.
    symbols = Column(StringArray(), nullable=False)  # List of symbols to collect
    frequency = Column(Enum(DataFrequency), nullable=False)
    
    # Date range
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Status and scheduling
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, running, completed, failed
    is_recurring = Column(Boolean, default=False)
    schedule_cron = Column(String(100))  # Cron expression for recurring jobs
    next_run = Column(DateTime, index=True)
    
    # Execution tracking
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float)  # Duration in seconds
    
    # Results
    created_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    records_collected = Column(BigInteger, default=0)
    bytes_processed = Column(BigInteger, default=0)
    
    # Error handling
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)
    logs = Column(JSON, default=list)  # Execution logs
    
    # Configuration
    ingestion_config = Column(JSON, default=dict)  # Source-specific configuration
    quality_checks = Column(JSON, default=list)  # Quality checks to perform
    
    # Relationships
    created_dataset = relationship("Dataset", foreign_keys=[created_dataset_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_ingestion_jobs_user_id', 'user_id'),
        Index('idx_ingestion_jobs_status', 'status'),
        Index('idx_ingestion_jobs_next_run', 'next_run'),
        Index('idx_ingestion_jobs_data_source', 'data_source'),
    )


class DataQualityRule(BaseModel, MetadataMixin):
    """
    Data quality rules for validation.
    """
    __tablename__ = "data_quality_rules"
    
    # Rule definition
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    rule_type = Column(String(50), nullable=False)  # completeness, range, format, uniqueness
    
    # Rule configuration
    conditions = Column(JSON, nullable=False)  # Rule conditions
    severity = Column(String(20), default="warning")  # error, warning, info
    
    # Applicability
    asset_classes = Column(JSON, default=list)  # Which asset classes this applies to
    columns = Column(JSON, default=list)  # Which columns this applies to
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Indexes
    __table_args__ = (
        Index('idx_quality_rules_type', 'rule_type'),
        Index('idx_quality_rules_active', 'is_active'),
    )


class DataProcessingJob(BaseModel, UserMixin):
    """
    Data processing job for transforming and cleaning datasets.
    """
    __tablename__ = "data_processing_jobs"
    
    # Job identification
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    job_type = Column(String(50), nullable=False)  # cleaning, transformation, feature_engineering
    
    # Job configuration
    input_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    output_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    processing_config = Column(JSON, default=dict)
    
    # Status and execution
    status = Column(String(50), default="pending", nullable=False, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    records_processed = Column(BigInteger, default=0)
    
    # Relationships
    input_dataset = relationship("Dataset", foreign_keys=[input_dataset_id])
    output_dataset = relationship("Dataset", foreign_keys=[output_dataset_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_processing_jobs_status', 'status'),
        Index('idx_processing_jobs_user_id', 'user_id'),
        Index('idx_processing_jobs_type', 'job_type'),
    )