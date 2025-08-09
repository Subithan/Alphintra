"""
Model Lifecycle Management Service - Automated model lifecycle with continuous training, validation, and deployment
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import pandas as pd
import numpy as np
from croniter import croniter

from app.models.model_registry import (
    Model, ModelVersion, ModelDeployment, ModelABTest, 
    ModelStatus, DeploymentStatus
)
from app.services.model_registry import model_registry
from app.services.k8s_deployment import k8s_deployment_service, DeploymentConfig
from app.services.model_monitor import model_monitor
from app.services.training_job_manager import training_job_manager
from app.core.database import get_db_session
from app.core.config import get_settings
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
settings = get_settings()


class LifecycleStage(str, Enum):
    """Model lifecycle stages"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    CANARY = "canary"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class LifecycleAction(str, Enum):
    """Lifecycle actions"""
    TRAIN = "train"
    VALIDATE = "validate"
    DEPLOY_STAGING = "deploy_staging"
    AB_TEST = "ab_test"
    DEPLOY_PRODUCTION = "deploy_production"
    ROLLBACK = "rollback"
    DEPRECATE = "deprecate"
    ARCHIVE = "archive"


@dataclass
class LifecycleConfig:
    """Lifecycle management configuration"""
    model_id: int
    
    # Training schedule
    retrain_schedule: str = "0 2 * * *"  # Daily at 2 AM (cron format)
    enable_auto_retrain: bool = True
    min_retrain_interval_hours: int = 24
    
    # Validation thresholds
    validation_threshold: float = 0.8
    performance_improvement_threshold: float = 0.05
    max_performance_degradation: float = 0.10
    
    # A/B testing configuration
    ab_test_duration_hours: int = 168  # 7 days
    ab_test_traffic_split: float = 0.1  # 10% to new model
    ab_test_min_samples: int = 1000
    
    # Rollout configuration
    canary_percentage: int = 10
    canary_duration_hours: int = 24
    full_rollout_threshold: float = 0.02  # 2% improvement required
    
    # Safety checks
    enable_auto_rollback: bool = True
    rollback_error_rate_threshold: float = 0.15
    rollback_latency_threshold_ms: float = 2000
    
    # Data requirements
    min_training_samples: int = 10000
    max_data_age_days: int = 30
    
    # Notifications
    enable_notifications: bool = True
    notification_channels: List[str] = field(default_factory=lambda: ["email", "slack"])


@dataclass
class LifecycleEvent:
    """Lifecycle event record"""
    model_id: int
    event_type: LifecycleAction
    timestamp: float
    stage_from: Optional[LifecycleStage] = None
    stage_to: Optional[LifecycleStage] = None
    model_version_id: Optional[int] = None
    deployment_id: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LifecycleStatus:
    """Current lifecycle status"""
    model_id: int
    current_stage: LifecycleStage
    current_version_id: Optional[int] = None
    production_version_id: Optional[int] = None
    staging_version_id: Optional[int] = None
    
    # Active processes
    training_in_progress: bool = False
    ab_test_active: bool = False
    canary_deployment_active: bool = False
    
    # Timestamps
    last_retrain: Optional[float] = None
    next_scheduled_retrain: Optional[float] = None
    last_deployment: Optional[float] = None
    
    # Health indicators
    health_score: float = 100.0
    performance_trend: str = "stable"  # improving, stable, degrading
    recommendations: List[str] = field(default_factory=list)


class ModelLifecycleService:
    """
    Automated model lifecycle management service
    """
    
    def __init__(self):
        self.lifecycle_configs: Dict[int, LifecycleConfig] = {}
        self.lifecycle_statuses: Dict[int, LifecycleStatus] = {}
        self.lifecycle_events: Dict[int, List[LifecycleEvent]] = {}
        
        # Background task management
        self._background_tasks = []
        self._lifecycle_active = False
        
        # Scheduling
        self._scheduled_tasks: Dict[int, asyncio.Task] = {}

    async def initialize(self):
        """Initialize lifecycle management service"""
        try:
            # Load existing configurations
            await self._load_lifecycle_configs()
            
            # Start background lifecycle management
            await self._start_background_lifecycle_management()
            
            self._lifecycle_active = True
            logger.info("Model lifecycle management service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize lifecycle management service: {e}")
            raise

    async def cleanup(self):
        """Cleanup lifecycle management service"""
        try:
            self._lifecycle_active = False
            
            # Cancel background tasks
            for task in self._background_tasks:
                task.cancel()
            
            # Cancel scheduled tasks
            for task in self._scheduled_tasks.values():
                task.cancel()
            
            logger.info("Model lifecycle management service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during lifecycle cleanup: {e}")

    async def setup_lifecycle(
        self,
        model_id: int,
        config: Optional[LifecycleConfig] = None
    ) -> bool:
        """Setup lifecycle management for a model"""
        try:
            logger.info(f"Setting up lifecycle management for model {model_id}")
            
            # Use default config if not provided
            if not config:
                config = LifecycleConfig(model_id=model_id)
            
            # Store configuration
            self.lifecycle_configs[model_id] = config
            
            # Initialize status
            db = next(get_db_session())
            model = db.query(Model).get(model_id)
            if not model:
                raise ValueError(f"Model {model_id} not found")
            
            # Determine current stage based on deployments
            current_stage = await self._determine_current_stage(model_id, db)
            
            self.lifecycle_statuses[model_id] = LifecycleStatus(
                model_id=model_id,
                current_stage=current_stage
            )
            
            # Initialize event history
            self.lifecycle_events[model_id] = []
            
            # Schedule automated tasks
            await self._schedule_lifecycle_tasks(model_id, config)
            
            db.close()
            
            logger.info(f"Lifecycle management setup completed for model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup lifecycle for model {model_id}: {e}")
            return False

    async def trigger_retrain(
        self,
        model_id: int,
        training_data: Optional[pd.DataFrame] = None,
        force: bool = False
    ) -> bool:
        """Trigger model retraining"""
        try:
            config = self.lifecycle_configs.get(model_id)
            if not config:
                raise ValueError(f"No lifecycle config for model {model_id}")
            
            status = self.lifecycle_statuses[model_id]
            
            # Check if retraining is allowed
            if not force and status.training_in_progress:
                logger.info(f"Training already in progress for model {model_id}")
                return False
            
            # Check minimum interval
            if not force and status.last_retrain:
                time_since_last = time.time() - status.last_retrain
                min_interval_seconds = config.min_retrain_interval_hours * 3600
                if time_since_last < min_interval_seconds:
                    logger.info(f"Too soon to retrain model {model_id}")
                    return False
            
            logger.info(f"Starting retraining for model {model_id}")
            
            # Update status
            status.training_in_progress = True
            
            # Record event
            await self._record_event(LifecycleEvent(
                model_id=model_id,
                event_type=LifecycleAction.TRAIN,
                timestamp=time.time(),
                stage_from=status.current_stage,
                metadata={"trigger": "scheduled" if not force else "manual"}
            ))
            
            # Get model info
            db = next(get_db_session())
            model = db.query(Model).get(model_id)
            if not model:
                raise ValueError(f"Model {model_id} not found")
            
            # Prepare training configuration
            latest_version = max(model.versions, key=lambda v: v.created_at) if model.versions else None
            
            training_config = {
                "model_type": model.model_type,
                "framework": model.framework,
                "strategy_type": model.strategy_type,
                "hyperparameters": latest_version.training_config if latest_version else {},
                "auto_retrain": True,
                "parent_version_id": latest_version.id if latest_version else None
            }
            
            # Create training job
            job = await training_job_manager.create_training_job(
                user_id=1,  # System user
                training_config=training_config,
                dataset_config={
                    "data_sources": ["market_data"],
                    "lookback_days": config.max_data_age_days,
                    "min_samples": config.min_training_samples
                }
            )
            
            if not job:
                raise RuntimeError("Failed to create training job")
            
            # Start training in background
            asyncio.create_task(self._monitor_training_job(model_id, job.id))
            
            db.close()
            
            logger.info(f"Retraining started for model {model_id}, job ID: {job.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger retrain for model {model_id}: {e}")
            
            # Update status on failure
            if model_id in self.lifecycle_statuses:
                self.lifecycle_statuses[model_id].training_in_progress = False
            
            await self._record_event(LifecycleEvent(
                model_id=model_id,
                event_type=LifecycleAction.TRAIN,
                timestamp=time.time(),
                success=False,
                error_message=str(e)
            ))
            
            return False

    async def validate_model_version(
        self,
        model_version_id: int,
        validation_data: Optional[pd.DataFrame] = None
    ) -> Tuple[bool, Dict[str, float]]:
        """Validate a model version against performance thresholds"""
        try:
            db = next(get_db_session())
            model_version = db.query(ModelVersion).get(model_version_id)
            if not model_version:
                raise ValueError(f"Model version {model_version_id} not found")
            
            model_id = model_version.model_id
            config = self.lifecycle_configs.get(model_id)
            if not config:
                raise ValueError(f"No lifecycle config for model {model_id}")
            
            logger.info(f"Validating model version {model_version_id}")
            
            # Record event
            await self._record_event(LifecycleEvent(
                model_id=model_id,
                event_type=LifecycleAction.VALIDATE,
                timestamp=time.time(),
                model_version_id=model_version_id
            ))
            
            # Get performance metrics from model version
            performance_metrics = model_version.performance_metrics or {}
            
            # Validation checks
            validation_results = {
                "accuracy": performance_metrics.get("accuracy", 0.0),
                "precision": performance_metrics.get("precision", 0.0),
                "recall": performance_metrics.get("recall", 0.0),
                "f1_score": performance_metrics.get("f1_score", 0.0),
                "sharpe_ratio": performance_metrics.get("sharpe_ratio", 0.0)
            }
            
            # Check against thresholds
            validation_passed = True
            
            # Basic performance threshold
            if validation_results["accuracy"] < config.validation_threshold:
                validation_passed = False
                logger.warning(f"Model version {model_version_id} failed accuracy threshold: {validation_results['accuracy']} < {config.validation_threshold}")
            
            # Check improvement against current production model
            production_version = await self._get_production_model_version(model_id, db)
            if production_version:
                improvement = self._calculate_improvement(
                    validation_results,
                    production_version.performance_metrics or {}
                )
                
                if improvement < config.performance_improvement_threshold:
                    validation_passed = False
                    logger.warning(f"Model version {model_version_id} failed improvement threshold: {improvement} < {config.performance_improvement_threshold}")
                
                validation_results["improvement_over_production"] = improvement
            
            # Update model version status
            if validation_passed:
                model_version.validation_status = "passed"
                model_version.deployment_ready = True
                model_version.status = ModelStatus.VALIDATED
            else:
                model_version.validation_status = "failed"
                model_version.deployment_ready = False
            
            db.commit()
            db.close()
            
            logger.info(f"Validation {'passed' if validation_passed else 'failed'} for model version {model_version_id}")
            
            return validation_passed, validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate model version {model_version_id}: {e}")
            return False, {}

    async def deploy_to_staging(
        self,
        model_version_id: int,
        deployment_config: Optional[DeploymentConfig] = None
    ) -> Optional[int]:
        """Deploy model version to staging environment"""
        try:
            db = next(get_db_session())
            model_version = db.query(ModelVersion).get(model_version_id)
            if not model_version:
                raise ValueError(f"Model version {model_version_id} not found")
            
            model_id = model_version.model_id
            
            logger.info(f"Deploying model version {model_version_id} to staging")
            
            # Default staging deployment config
            if not deployment_config:
                deployment_config = DeploymentConfig(
                    model_version_id=model_version_id,
                    deployment_name=f"{model_version.model.name}-staging-v{model_version.version}",
                    environment="staging",
                    cpu_request="250m",
                    cpu_limit="1000m",
                    memory_request="512Mi",
                    memory_limit="2Gi",
                    min_replicas=1,
                    max_replicas=3
                )
            
            # Record event
            await self._record_event(LifecycleEvent(
                model_id=model_id,
                event_type=LifecycleAction.DEPLOY_STAGING,
                timestamp=time.time(),
                stage_from=self.lifecycle_statuses[model_id].current_stage,
                stage_to=LifecycleStage.STAGING,
                model_version_id=model_version_id
            ))
            
            # Deploy to Kubernetes
            result = await k8s_deployment_service.deploy_model(
                deployment_config,
                user_id=1,  # System user
                db_session=db
            )
            
            if not result.success:
                raise RuntimeError(f"Deployment failed: {result.error_message}")
            
            # Update lifecycle status
            status = self.lifecycle_statuses[model_id]
            status.current_stage = LifecycleStage.STAGING
            status.staging_version_id = model_version_id
            status.last_deployment = time.time()
            
            db.close()
            
            logger.info(f"Model version {model_version_id} successfully deployed to staging, deployment ID: {result.deployment_id}")
            
            return result.deployment_id
            
        except Exception as e:
            logger.error(f"Failed to deploy to staging: {e}")
            
            await self._record_event(LifecycleEvent(
                model_id=model_version.model_id,
                event_type=LifecycleAction.DEPLOY_STAGING,
                timestamp=time.time(),
                model_version_id=model_version_id,
                success=False,
                error_message=str(e)
            ))
            
            return None

    async def start_ab_test(
        self,
        control_version_id: int,
        treatment_version_id: int,
        traffic_split: Optional[float] = None
    ) -> Optional[int]:
        """Start A/B test between two model versions"""
        try:
            db = next(get_db_session())
            
            control_version = db.query(ModelVersion).get(control_version_id)
            treatment_version = db.query(ModelVersion).get(treatment_version_id)
            
            if not control_version or not treatment_version:
                raise ValueError("Control or treatment version not found")
            
            if control_version.model_id != treatment_version.model_id:
                raise ValueError("Versions must belong to the same model")
            
            model_id = control_version.model_id
            config = self.lifecycle_configs.get(model_id)
            if not config:
                raise ValueError(f"No lifecycle config for model {model_id}")
            
            # Use config traffic split if not provided
            if traffic_split is None:
                traffic_split = config.ab_test_traffic_split
            
            logger.info(f"Starting A/B test for model {model_id}: control={control_version_id}, treatment={treatment_version_id}")
            
            # Create A/B test
            ab_test = await model_registry.create_ab_test(
                name=f"Model {model_id} A/B Test - v{control_version.version} vs v{treatment_version.version}",
                description=f"Automated A/B test comparing model versions",
                control_version_id=control_version_id,
                treatment_version_id=treatment_version_id,
                traffic_split=traffic_split,
                duration_days=config.ab_test_duration_hours // 24,
                success_criteria={
                    "significance_level": 0.05,
                    "minimum_sample_size": config.ab_test_min_samples,
                    "primary_metric": "sharpe_ratio",
                    "minimum_effect_size": config.performance_improvement_threshold
                },
                db_session=db
            )
            
            # Update lifecycle status
            status = self.lifecycle_statuses[model_id]
            status.ab_test_active = True
            status.current_stage = LifecycleStage.CANARY
            
            # Record event
            await self._record_event(LifecycleEvent(
                model_id=model_id,
                event_type=LifecycleAction.AB_TEST,
                timestamp=time.time(),
                stage_to=LifecycleStage.CANARY,
                metadata={
                    "ab_test_id": ab_test.id,
                    "control_version_id": control_version_id,
                    "treatment_version_id": treatment_version_id,
                    "traffic_split": traffic_split
                }
            ))
            
            # Schedule A/B test monitoring
            asyncio.create_task(self._monitor_ab_test(model_id, ab_test.id))
            
            db.close()
            
            logger.info(f"A/B test started for model {model_id}, test ID: {ab_test.id}")
            
            return ab_test.id
            
        except Exception as e:
            logger.error(f"Failed to start A/B test: {e}")
            return None

    async def rollback_deployment(
        self,
        deployment_id: int,
        reason: str = "Manual rollback"
    ) -> bool:
        """Rollback a deployment to previous version"""
        try:
            db = next(get_db_session())
            
            deployment = db.query(ModelDeployment).get(deployment_id)
            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")
            
            model_id = deployment.model_id
            
            logger.info(f"Rolling back deployment {deployment_id} for model {model_id}")
            
            # Find previous production version
            previous_version = await self._get_previous_production_version(model_id, db)
            if not previous_version:
                raise ValueError("No previous version available for rollback")
            
            # Record event
            await self._record_event(LifecycleEvent(
                model_id=model_id,
                event_type=LifecycleAction.ROLLBACK,
                timestamp=time.time(),
                deployment_id=deployment_id,
                metadata={
                    "reason": reason,
                    "rollback_to_version": previous_version.id
                }
            ))
            
            # Update deployment with previous version
            success = await k8s_deployment_service.update_deployment(
                deployment_id,
                previous_version.id,
                strategy="rolling",
                db_session=db
            )
            
            if success:
                # Update lifecycle status
                status = self.lifecycle_statuses[model_id]
                status.production_version_id = previous_version.id
                
                logger.info(f"Successfully rolled back deployment {deployment_id} to version {previous_version.id}")
            
            db.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rollback deployment {deployment_id}: {e}")
            return False

    async def get_lifecycle_status(self, model_id: int) -> Optional[LifecycleStatus]:
        """Get current lifecycle status"""
        return self.lifecycle_statuses.get(model_id)

    async def get_lifecycle_events(
        self,
        model_id: int,
        limit: int = 50
    ) -> List[LifecycleEvent]:
        """Get lifecycle event history"""
        events = self.lifecycle_events.get(model_id, [])
        return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]

    # Private helper methods
    
    async def _load_lifecycle_configs(self):
        """Load lifecycle configurations"""
        try:
            # Load from database - get all active models
            db = next(get_db_session())
            models = db.query(Model).filter(Model.is_active == True).all()
            
            for model in models:
                # Create default config for each model
                self.lifecycle_configs[model.id] = LifecycleConfig(model_id=model.id)
                
                # Initialize status
                current_stage = await self._determine_current_stage(model.id, db)
                self.lifecycle_statuses[model.id] = LifecycleStatus(
                    model_id=model.id,
                    current_stage=current_stage
                )
                
                # Initialize event history
                self.lifecycle_events[model.id] = []
            
            db.close()
            logger.info(f"Loaded lifecycle configs for {len(self.lifecycle_configs)} models")
            
        except Exception as e:
            logger.error(f"Error loading lifecycle configs: {e}")

    async def _determine_current_stage(self, model_id: int, db: Session) -> LifecycleStage:
        """Determine current lifecycle stage based on deployments"""
        try:
            # Check for production deployments
            prod_deployment = db.query(ModelDeployment).filter(
                ModelDeployment.model_id == model_id,
                ModelDeployment.environment == "prod",
                ModelDeployment.is_active == True,
                ModelDeployment.status == DeploymentStatus.DEPLOYED
            ).first()
            
            if prod_deployment:
                return LifecycleStage.PRODUCTION
            
            # Check for staging deployments
            staging_deployment = db.query(ModelDeployment).filter(
                ModelDeployment.model_id == model_id,
                ModelDeployment.environment == "staging",
                ModelDeployment.is_active == True,
                ModelDeployment.status == DeploymentStatus.DEPLOYED
            ).first()
            
            if staging_deployment:
                return LifecycleStage.STAGING
            
            # Check for any validated versions
            validated_version = db.query(ModelVersion).filter(
                ModelVersion.model_id == model_id,
                ModelVersion.status == ModelStatus.VALIDATED
            ).first()
            
            if validated_version:
                return LifecycleStage.TESTING
            
            return LifecycleStage.DEVELOPMENT
            
        except Exception as e:
            logger.error(f"Error determining current stage for model {model_id}: {e}")
            return LifecycleStage.DEVELOPMENT

    async def _start_background_lifecycle_management(self):
        """Start background lifecycle management tasks"""
        # Schedule monitoring task
        schedule_task = asyncio.create_task(self._lifecycle_scheduler_loop())
        self._background_tasks.append(schedule_task)
        
        # Health monitoring task
        health_task = asyncio.create_task(self._health_monitoring_loop())
        self._background_tasks.append(health_task)
        
        # Rollback monitoring task
        rollback_task = asyncio.create_task(self._rollback_monitoring_loop())
        self._background_tasks.append(rollback_task)

    async def _lifecycle_scheduler_loop(self):
        """Background task for scheduled lifecycle actions"""
        while self._lifecycle_active:
            try:
                current_time = datetime.now()
                
                for model_id, config in self.lifecycle_configs.items():
                    if not config.enable_auto_retrain:
                        continue
                    
                    # Check if retraining is scheduled
                    cron = croniter(config.retrain_schedule, current_time)
                    next_run = cron.get_next(datetime)
                    
                    # If next run is within the next minute, trigger retraining
                    if (next_run - current_time).total_seconds() < 60:
                        logger.info(f"Triggering scheduled retrain for model {model_id}")
                        asyncio.create_task(self.trigger_retrain(model_id))
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in lifecycle scheduler loop: {e}")
                await asyncio.sleep(300)

    async def _health_monitoring_loop(self):
        """Background task for health monitoring and automated actions"""
        while self._lifecycle_active:
            try:
                for model_id in self.lifecycle_configs.keys():
                    # Get model health from monitoring service
                    health_status = await model_monitor.get_health_status(model_id)
                    if not health_status:
                        continue
                    
                    # Update lifecycle status
                    status = self.lifecycle_statuses.get(model_id)
                    if status:
                        status.health_score = health_status.health_score
                        
                        # Determine performance trend
                        if health_status.health_score >= 80:
                            status.performance_trend = "stable"
                        elif health_status.health_score >= 60:
                            status.performance_trend = "degrading"
                        else:
                            status.performance_trend = "critical"
                        
                        # Generate recommendations
                        status.recommendations = health_status.recommendations.copy()
                        
                        # Trigger actions based on health
                        if health_status.health_score < 50:
                            logger.warning(f"Critical health for model {model_id}, considering rollback")
                            # Could trigger automatic rollback here
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(300)

    async def _rollback_monitoring_loop(self):
        """Background task for rollback monitoring"""
        while self._lifecycle_active:
            try:
                for model_id, config in self.lifecycle_configs.items():
                    if not config.enable_auto_rollback:
                        continue
                    
                    # Get production deployments for this model
                    db = next(get_db_session())
                    deployments = db.query(ModelDeployment).filter(
                        ModelDeployment.model_id == model_id,
                        ModelDeployment.environment == "prod",
                        ModelDeployment.is_active == True,
                        ModelDeployment.status == DeploymentStatus.DEPLOYED
                    ).all()
                    
                    for deployment in deployments:
                        # Get prediction metrics
                        from app.services.prediction_service import prediction_service
                        metrics = await prediction_service.get_model_metrics(deployment.id)
                        
                        if metrics:
                            # Check rollback conditions
                            should_rollback = False
                            reason = ""
                            
                            if metrics.error_rate > config.rollback_error_rate_threshold:
                                should_rollback = True
                                reason = f"Error rate {metrics.error_rate:.1%} exceeds threshold {config.rollback_error_rate_threshold:.1%}"
                            
                            elif metrics.avg_latency_ms > config.rollback_latency_threshold_ms:
                                should_rollback = True
                                reason = f"Latency {metrics.avg_latency_ms:.0f}ms exceeds threshold {config.rollback_latency_threshold_ms:.0f}ms"
                            
                            if should_rollback:
                                logger.warning(f"Auto-rollback triggered for deployment {deployment.id}: {reason}")
                                await self.rollback_deployment(deployment.id, reason)
                    
                    db.close()
                
                await asyncio.sleep(180)  # Check every 3 minutes
                
            except Exception as e:
                logger.error(f"Error in rollback monitoring loop: {e}")
                await asyncio.sleep(180)

    async def _schedule_lifecycle_tasks(self, model_id: int, config: LifecycleConfig):
        """Schedule automated lifecycle tasks for a model"""
        # This would set up cron-like scheduling for retraining
        # For now, we rely on the scheduler loop
        pass

    async def _monitor_training_job(self, model_id: int, job_id: int):
        """Monitor training job and continue lifecycle when complete"""
        try:
            logger.info(f"Monitoring training job {job_id} for model {model_id}")
            
            # Poll training job status
            while True:
                job_status = await training_job_manager.get_job_status(job_id)
                if not job_status:
                    break
                
                if job_status["status"] == "completed":
                    logger.info(f"Training job {job_id} completed for model {model_id}")
                    
                    # Get the new model version
                    model_version_id = job_status.get("model_version_id")
                    if model_version_id:
                        # Validate the new version
                        validation_passed, metrics = await self.validate_model_version(model_version_id)
                        
                        if validation_passed:
                            # Deploy to staging
                            staging_deployment_id = await self.deploy_to_staging(model_version_id)
                            
                            if staging_deployment_id:
                                # Could start A/B test here
                                logger.info(f"New model version {model_version_id} deployed to staging")
                    
                    # Update status
                    status = self.lifecycle_statuses[model_id]
                    status.training_in_progress = False
                    status.last_retrain = time.time()
                    
                    break
                    
                elif job_status["status"] in ["failed", "cancelled"]:
                    logger.error(f"Training job {job_id} failed for model {model_id}")
                    
                    # Update status
                    status = self.lifecycle_statuses[model_id]
                    status.training_in_progress = False
                    
                    break
                
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Error monitoring training job {job_id}: {e}")

    async def _monitor_ab_test(self, model_id: int, ab_test_id: int):
        """Monitor A/B test and promote winner when complete"""
        try:
            logger.info(f"Monitoring A/B test {ab_test_id} for model {model_id}")
            
            config = self.lifecycle_configs[model_id]
            
            # Wait for test duration
            await asyncio.sleep(config.ab_test_duration_hours * 3600)
            
            # Analyze A/B test results (placeholder)
            # In real implementation, this would collect metrics and determine winner
            logger.info(f"A/B test {ab_test_id} completed for model {model_id}")
            
            # Update status
            status = self.lifecycle_statuses[model_id]
            status.ab_test_active = False
            
            # Could automatically promote winner to production here
            
        except Exception as e:
            logger.error(f"Error monitoring A/B test {ab_test_id}: {e}")

    async def _record_event(self, event: LifecycleEvent):
        """Record lifecycle event"""
        if event.model_id not in self.lifecycle_events:
            self.lifecycle_events[event.model_id] = []
        
        self.lifecycle_events[event.model_id].append(event)
        
        # Limit event history
        max_events = 1000
        if len(self.lifecycle_events[event.model_id]) > max_events:
            self.lifecycle_events[event.model_id] = self.lifecycle_events[event.model_id][-max_events:]
        
        logger.info(f"Lifecycle event recorded for model {event.model_id}: {event.event_type}")

    async def _get_production_model_version(self, model_id: int, db: Session) -> Optional[ModelVersion]:
        """Get current production model version"""
        deployment = db.query(ModelDeployment).filter(
            ModelDeployment.model_id == model_id,
            ModelDeployment.environment == "prod",
            ModelDeployment.is_active == True,
            ModelDeployment.status == DeploymentStatus.DEPLOYED
        ).first()
        
        return deployment.model_version if deployment else None

    async def _get_previous_production_version(self, model_id: int, db: Session) -> Optional[ModelVersion]:
        """Get previous production model version for rollback"""
        # This would implement logic to find the previous stable version
        # For now, just return the second most recent validated version
        versions = db.query(ModelVersion).filter(
            ModelVersion.model_id == model_id,
            ModelVersion.status == ModelStatus.VALIDATED
        ).order_by(ModelVersion.created_at.desc()).limit(2).all()
        
        return versions[1] if len(versions) > 1 else None

    def _calculate_improvement(
        self,
        new_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float]
    ) -> float:
        """Calculate improvement percentage"""
        if not baseline_metrics:
            return 0.0
        
        # Use primary metric (accuracy) for improvement calculation
        new_value = new_metrics.get("accuracy", 0.0)
        baseline_value = baseline_metrics.get("accuracy", 0.0)
        
        if baseline_value == 0:
            return 0.0
        
        return (new_value - baseline_value) / baseline_value


# Global instance
model_lifecycle = ModelLifecycleService()