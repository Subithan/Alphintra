from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflows = relationship("Workflow", back_populates="user")

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    nodes = Column(JSON, default=list)  # Stores workflow nodes as JSON
    edges = Column(JSON, default=list)  # Stores workflow edges as JSON
    parameters = Column(JSON, default=dict)  # Workflow configuration parameters
    status = Column(String, default="draft")  # draft, compiled, training, deployed, failed
    version = Column(Integer, default=1)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="workflows")
    compilations = relationship("CompilationResult", back_populates="workflow")
    training_jobs = relationship("TrainingJob", back_populates="workflow")

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
    metadata = Column(JSON, default=dict)  # Dataset metadata (columns, size, etc.)
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