"""Minimal SQLAlchemy models required for the no-code service."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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

    workflows = relationship("NoCodeWorkflow", back_populates="user")


class NoCodeWorkflow(Base):
    __tablename__ = "nocode_workflows"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), default="custom")
    tags = Column(ARRAY(String), default=list)

    workflow_data = Column(JSON, nullable=False, default=lambda: {"nodes": [], "edges": []})

    generated_code = Column(Text)
    generated_code_language = Column(String(20), default="python")
    generated_requirements = Column(ARRAY(String), default=list)
    generated_code_size = Column(Integer, default=0)
    generated_code_lines = Column(Integer, default=0)
    compiler_version = Column(String(50), default="Enhanced v2.0")

    compilation_status = Column(String(20), default="pending")
    compilation_errors = Column(JSON, default=list)
    validation_status = Column(String(20), default="pending")
    validation_errors = Column(JSON, default=list)
    deployment_status = Column(String(20), default="draft")
    execution_mode = Column(String(20), default="backtest")

    execution_metadata = Column(JSON, default=dict)
    aiml_training_job_id = Column(String, nullable=True)

    version = Column(Integer, default=1)
    parent_workflow_id = Column(Integer, ForeignKey("nocode_workflows.id"))
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)

    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    avg_performance_score = Column(DECIMAL(5, 2), default=0.0)
    last_execution_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime)

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

    component_type = Column(String(50), nullable=False)
    input_schema = Column(JSON, nullable=False, default=dict)
    output_schema = Column(JSON, nullable=False, default=dict)
    parameters_schema = Column(JSON, nullable=False, default=dict)
    default_parameters = Column(JSON, default=dict)

    code_template = Column(Text, nullable=False)
    imports_required = Column(ARRAY(String), default=list)
    dependencies = Column(ARRAY(String), default=list)

    ui_config = Column(JSON, default=lambda: {"width": 200, "height": 100, "color": "#1f2937"})
    icon = Column(String(100))

    author_id = Column(Integer, ForeignKey("users.id"))
    is_builtin = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    rating = Column(DECIMAL(2, 1), default=0.0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NoCodeExecution(Base):
    __tablename__ = "nocode_executions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    workflow_id = Column(Integer, ForeignKey("nocode_workflows.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    execution_type = Column(String(20), nullable=False)
    parameters = Column(JSON, default=dict)
    symbols = Column(ARRAY(String), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_capital = Column(DECIMAL(20, 8), default=10000.0)

    status = Column(String(20), default="pending", index=True)
    progress = Column(Integer, default=0)
    current_step = Column(String(255))

    final_capital = Column(DECIMAL(20, 8))
    total_return = Column(DECIMAL(10, 4))
    total_return_percent = Column(DECIMAL(6, 2))
    sharpe_ratio = Column(DECIMAL(6, 3))
    max_drawdown_percent = Column(DECIMAL(6, 2))
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)

    trades_data = Column(JSON, default=list)
    performance_metrics = Column(JSON, default=dict)
    execution_logs = Column(JSON, default=list)
    error_logs = Column(JSON, default=list)

    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    workflow = relationship("NoCodeWorkflow", back_populates="executions")


class NoCodeTemplate(Base):
    __tablename__ = "nocode_templates"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)
    difficulty_level = Column(String(20), default="beginner")

    template_data = Column(JSON, nullable=False)
    preview_image_url = Column(String(500))

    author_id = Column(Integer, ForeignKey("users.id"))
    is_featured = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    rating = Column(DECIMAL(2, 1), default=0.0)

    keywords = Column(ARRAY(String), default=list)
    estimated_time_minutes = Column(Integer)
    expected_performance = Column(JSON, default=dict)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CompilationResult(Base):
    __tablename__ = "compilation_results"

    id = Column(String, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("nocode_workflows.id"), nullable=False)
    python_code = Column(Text, nullable=False)
    validation_results = Column(JSON, default=dict)
    status = Column(String, default="pending")
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())

    workflow = relationship("NoCodeWorkflow")


class ExecutionHistory(Base):
    __tablename__ = "execution_history"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    workflow_id = Column(Integer, ForeignKey("nocode_workflows.id"), nullable=False, index=True)
    execution_mode = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    execution_config = Column(JSON, default=dict)
    results = Column(JSON, default=dict)
    error_logs = Column(JSON, default=list)
    generated_code = Column(Text)
    generated_requirements = Column(ARRAY(String), default=list)
    compilation_stats = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    workflow = relationship("NoCodeWorkflow")
