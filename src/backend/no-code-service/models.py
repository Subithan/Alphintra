from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, JSON, ForeignKey, DECIMAL, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    workflows = relationship("NoCodeWorkflow", back_populates="user")

class NoCodeWorkflow(Base):
    __tablename__ = "nocode_workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), default='custom')
    tags = Column(ARRAY(String), default=[])
    
    # Workflow definition
    workflow_data = Column(JSON, nullable=False, default={"nodes": [], "edges": []})
    
    # Generated code
    generated_code = Column(Text)
    generated_code_language = Column(String(20), default='python')
    generated_requirements = Column(ARRAY(String), default=[])
    
    # Status fields
    compilation_status = Column(String(20), default='pending')
    compilation_errors = Column(JSON, default=[])
    validation_status = Column(String(20), default='pending')
    validation_errors = Column(JSON, default=[])
    deployment_status = Column(String(20), default='draft')
    execution_mode = Column(String(20), default='backtest')
    
    # Versioning
    version = Column(Integer, default=1)
    parent_workflow_id = Column(Integer, ForeignKey("nocode_workflows.id"))
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    # Performance metrics
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    avg_performance_score = Column(DECIMAL(5,2), default=0.0)
    last_execution_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="workflows")
    executions = relationship("NoCodeExecution", back_populates="workflow")
    parent_workflow = relationship("NoCodeWorkflow", remote_side=[id])

class NoCodeComponent(Base):
    __tablename__ = "nocode_components"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50))
    
    # Component definition
    component_type = Column(String(50), nullable=False)
    input_schema = Column(JSON, nullable=False, default={})
    output_schema = Column(JSON, nullable=False, default={})
    parameters_schema = Column(JSON, nullable=False, default={})
    default_parameters = Column(JSON, default={})
    
    # Code templates
    code_template = Column(Text, nullable=False)
    imports_required = Column(ARRAY(String), default=[])
    dependencies = Column(ARRAY(String), default=[])
    
    # UI configuration
    ui_config = Column(JSON, default={"width": 200, "height": 100, "color": "#1f2937"})
    icon = Column(String(100))
    
    # Metadata
    author_id = Column(Integer, ForeignKey("users.id"))
    is_builtin = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    rating = Column(DECIMAL(2,1), default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class NoCodeExecution(Base):
    __tablename__ = "nocode_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    workflow_id = Column(Integer, ForeignKey("nocode_workflows.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Execution configuration
    execution_type = Column(String(20), nullable=False)
    parameters = Column(JSON, default={})
    
    # Market data configuration
    symbols = Column(ARRAY(String), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_capital = Column(DECIMAL(20,8), default=10000.0)
    
    # Execution status
    status = Column(String(20), default='pending', index=True)
    progress = Column(Integer, default=0)
    current_step = Column(String(255))
    
    # Results
    final_capital = Column(DECIMAL(20,8))
    total_return = Column(DECIMAL(10,4))
    total_return_percent = Column(DECIMAL(6,2))
    sharpe_ratio = Column(DECIMAL(6,3))
    max_drawdown_percent = Column(DECIMAL(6,2))
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    
    # Execution data
    trades_data = Column(JSON, default=[])
    performance_metrics = Column(JSON, default={})
    execution_logs = Column(JSON, default=[])
    error_logs = Column(JSON, default=[])
    
    # Timestamps
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    workflow = relationship("NoCodeWorkflow", back_populates="executions")

class NoCodeTemplate(Base):
    __tablename__ = "nocode_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)
    difficulty_level = Column(String(20), default='beginner')
    
    # Template data
    template_data = Column(JSON, nullable=False)
    preview_image_url = Column(String(500))
    
    # Metadata
    author_id = Column(Integer, ForeignKey("users.id"))
    is_featured = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    rating = Column(DECIMAL(2,1), default=0.0)
    
    # SEO and discovery
    keywords = Column(ARRAY(String), default=[])
    estimated_time_minutes = Column(Integer)
    expected_performance = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class CompilationResult(Base):
    __tablename__ = "compilation_results"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    python_code = Column(Text, nullable=False)  # Generated Python code
    validation_results = Column(JSON, default=dict)  # Validation and security scan results
    status = Column(String, default="pending")  # pending, success, failed, validating, validated, validation_failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="compilations")
    training_jobs = relationship("TrainingJob", back_populates="compilation")

class TrainingJob(Base):
    __tablename__ = "training_jobs"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    compilation_id = Column(String, ForeignKey("compilation_results.id"), nullable=False)
    dataset_id = Column(String, nullable=False)
    config = Column(JSON, nullable=False)  # Training configuration
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    current_epoch = Column(Integer)
    total_epochs = Column(Integer)
    metrics = Column(JSON, default=list)  # Training metrics history
    model_artifacts = Column(JSON)  # URLs/paths to trained model files
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="training_jobs")
    compilation = relationship("CompilationResult", back_populates="training_jobs")

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, nullable=False)  # platform, user_uploaded, external
    owner_id = Column(String, ForeignKey("users.id"))
    file_path = Column(String)  # Path to dataset file
    dataset_metadata = Column(JSON, default=dict)  # Dataset metadata (columns, size, etc.)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ComponentLibrary(Base):
    __tablename__ = "component_library"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # technicalIndicator, condition, action, etc.
    category = Column(String, nullable=False)
    description = Column(Text)
    icon = Column(String)
    tags = Column(JSON, default=list)
    parameters_schema = Column(JSON, default=dict)  # JSON schema for parameters
    inputs_schema = Column(JSON, default=list)  # Input port definitions
    outputs_schema = Column(JSON, default=list)  # Output port definitions
    implementation = Column(Text)  # Python code template
    documentation = Column(Text)
    examples = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TestingResult(Base):
    __tablename__ = "testing_results"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    compilation_id = Column(String, ForeignKey("compilation_results.id"), nullable=False)
    test_type = Column(String, nullable=False)  # security, performance, accuracy
    status = Column(String, default="pending")  # pending, running, completed, failed
    results = Column(JSON, default=dict)  # Test results
    score = Column(Float)  # Overall score/rating
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)

class MarketplaceStrategy(Base):
    __tablename__ = "marketplace_strategies"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)
    tags = Column(JSON, default=list)
    price = Column(Float, default=0.0)  # 0 for free
    workflow_template = Column(JSON, nullable=False)  # Workflow definition
    performance_metrics = Column(JSON, default=dict)
    rating = Column(Float, default=0.0)
    downloads = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class StrategyRating(Base):
    __tablename__ = "strategy_ratings"
    
    id = Column(String, primary_key=True)
    strategy_id = Column(String, ForeignKey("marketplace_strategies.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review = Column(Text)
    created_at = Column(DateTime, default=func.now())

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    training_job_id = Column(String, ForeignKey("training_jobs.id"))
    execution_type = Column(String, nullable=False)  # backtest, live, paper
    status = Column(String, default="pending")  # pending, running, completed, failed
    results = Column(JSON, default=dict)  # Execution results
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String, nullable=False)  # create, update, delete, compile, train, etc.
    resource_type = Column(String, nullable=False)  # workflow, training_job, etc.
    resource_id = Column(String, nullable=False)
    details = Column(JSON, default=dict)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=func.now())