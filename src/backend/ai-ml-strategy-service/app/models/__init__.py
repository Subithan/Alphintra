"""
Database models for the AI/ML Strategy Service.
"""

from app.models.base import BaseModel, UUIDMixin, TimestampMixin, UserMixin, MetadataMixin

# Import User model
from app.models.user import User

# Import all model classes to ensure they're registered with SQLAlchemy
from app.models.strategy import (
    Strategy,
    StrategyTemplate,
    DebugSession,
    StrategyVersion,
    StrategyPerformanceMetrics,
    StrategyStatus,
    DifficultyLevel,
    DebugStatus
)

from app.models.dataset import (
    Dataset,
    DatasetPreview,
    DataPreprocessingJob,
    DatasetTag,
    DatasetTagAssociation,
    MarketDataStream,
    DataValidationRule,
    DataSource,
    DatasetStatus,
    DataFormat
)

from app.models.training import (
    TrainingJob,
    ModelArtifact,
    HyperparameterTrial,
    TrainingMetric,
    ModelRegistry,
    ModelVersion,
    ComputeResource,
    JobType,
    JobStatus,
    InstanceType,
    ModelFramework
)

from app.models.backtesting import (
    BacktestJob,
    BacktestResult,
    Trade,
    EquityCurvePoint,
    BacktestComparison,
    BacktestTemplate,
    WalkForwardAnalysis,
    BacktestMethodology,
    TradeSide,
    OrderType,
    ExitReason
)

from app.models.paper_trading import (
    PaperAccount,
    Position,
    PaperTrade,
    PaperOrder,
    StrategyDeployment,
    AccountPerformanceSnapshot,
    PaperTradingSettings,
    AccountStatus,
    PositionSide,
    OrderStatus,
    StrategyDeploymentStatus
)

from app.models.experiment import (
    Experiment,
    ExperimentRun,
    RunMetricHistory,
    RunArtifact,
    ModelRegistryEntry,
    ModelVersion,
    ModelDeployment,
    ExperimentComparison,
    HyperparameterOptimization,
    OptimizationTrial,
    ExperimentStatus,
    RunStatus,
    ModelStage,
    ArtifactType
)

from app.models.file_management import (
    Project,
    ProjectFile,
    ProjectTemplate,
    FileSession,
    FileVersion
)

__all__ = [
    # Base classes
    "BaseModel",
    "UUIDMixin",
    "TimestampMixin",
    "UserMixin",
    "MetadataMixin",
    
    # User model
    "User",
    
    # Strategy models
    "Strategy",
    "StrategyTemplate",
    "DebugSession",
    "StrategyVersion",
    "StrategyPerformanceMetrics",
    "StrategyStatus",
    "DifficultyLevel",
    "DebugStatus",
    
    # Dataset models
    "Dataset",
    "DatasetPreview",
    "DataPreprocessingJob",
    "DatasetTag",
    "DatasetTagAssociation",
    "MarketDataStream",
    "DataValidationRule",
    "DataSource",
    "DatasetStatus",
    "DataFormat",
    
    # Training models
    "TrainingJob",
    "ModelArtifact",
    "HyperparameterTrial",
    "TrainingMetric",
    "ModelRegistry",
    "ModelVersion",
    "ComputeResource",
    "JobType",
    "JobStatus",
    "InstanceType",
    "ModelFramework",
    
    # Backtesting models
    "BacktestJob",
    "BacktestResult",
    "Trade",
    "EquityCurvePoint",
    "BacktestComparison",
    "BacktestTemplate",
    "WalkForwardAnalysis",
    "BacktestMethodology",
    "TradeSide",
    "OrderType",
    "ExitReason",
    
    # Paper trading models
    "PaperAccount",
    "Position",
    "PaperTrade",
    "PaperOrder",
    "StrategyDeployment",
    "AccountPerformanceSnapshot",
    "PaperTradingSettings",
    "AccountStatus",
    "PositionSide",
    "OrderStatus",
    "StrategyDeploymentStatus",
    
    # Experiment models
    "Experiment",
    "ExperimentRun",
    "RunMetricHistory",
    "RunArtifact",
    "ModelRegistryEntry",
    "ModelVersion",
    "ModelDeployment",
    "ExperimentComparison",
    "HyperparameterOptimization",
    "OptimizationTrial",
    "ExperimentStatus",
    "RunStatus",
    "ModelStage",
    "ArtifactType",
    
    # File management models
    "Project",
    "ProjectFile",
    "ProjectTemplate",
    "FileSession",
    "FileVersion",
]