"""
Model Performance Monitoring Service - Track model performance, data drift, and business metrics
"""

import asyncio
import json
import logging
import time
import statistics
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, precision_recall_fscore_support
import redis.asyncio as redis

from app.models.model_registry import ModelDeployment, ModelMetrics, DeploymentStatus
from app.services import prediction_service as prediction_service_module
from app.services.prediction_service import ModelMetrics as PredictionMetrics
from app.core.database import get_db_session
from app.core.config import get_settings
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
settings = get_settings()


async def _send_email_notification(subject: str, body: str):
    logger.info(f"--- EMAIL NOTIFICATION ---")
    logger.info(f"To: on-call-team@example.com")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body: {body}")
    logger.info(f"--------------------------")

async def _send_slack_notification(channel: str, message: str):
    logger.info(f"--- SLACK NOTIFICATION ---")
    logger.info(f"Channel: {channel}")
    logger.info(f"Message: {message}")
    logger.info(f"--------------------------")


@dataclass
class ConceptDriftAlert:
    """Concept drift detection alert"""
    deployment_id: int
    drift_score: float
    p_value: float
    threshold: float = 0.05
    timestamp: float = field(default_factory=time.time)
    severity: str # "low", "medium", "high"
    description: str


@dataclass
class DataDriftAlert:
    """Data drift detection alert"""
    deployment_id: int
    feature_name: str
    drift_score: float
    threshold: float
    detection_method: str
    timestamp: float
    severity: str  # "low", "medium", "high"
    description: str


@dataclass
class PredictionLog:
    """Log of a single prediction"""
    deployment_id: int
    request_id: str
    features: Dict[str, Any]
    prediction: Union[float, int, List[float], Dict[str, Any]]
    ground_truth: Optional[Union[float, int, str]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceDegradationAlert:
    """Performance degradation alert"""
    deployment_id: int
    metric_name: str
    current_value: float
    expected_value: float
    degradation_percentage: float
    threshold: float
    timestamp: float
    severity: str
    description: str


@dataclass
class ModelHealthStatus:
    """Overall model health status"""
    deployment_id: int
    health_score: float  # 0-100
    status: str  # "healthy", "warning", "critical"
    performance_metrics: Dict[str, float]
    accuracy_metrics: Dict[str, float]
    drift_metrics: Dict[str, float]
    business_metrics: Dict[str, float]
    alerts: List[Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]]
    last_updated: float
    recommendations: List[str] = field(default_factory=list)


@dataclass
class MonitoringConfig:
    """Monitoring configuration for a model"""
    deployment_id: int
    performance_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "accuracy_drop_threshold": 0.05,
        "latency_increase_threshold": 2.0,
        "error_rate_threshold": 0.10
    })
    drift_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "psi_threshold": 0.2,
        "ks_threshold": 0.1,
        "chi2_threshold": 0.05
    })
    alert_settings: Dict[str, Any] = field(default_factory=lambda: {
        "enable_alerts": True,
        "alert_cooldown_minutes": 30,
        "min_samples_for_drift": 1000,
        "notification_channels": ["log"] # "log", "email", "slack"
    })
    business_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "sharpe_ratio_threshold": -0.5,
        "max_drawdown_threshold": 0.20,
        "win_rate_threshold": -0.10
    })


class ModelMonitoringService:
    """
    Comprehensive model monitoring service for performance tracking, drift detection, and alerting
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.monitoring_configs: Dict[int, MonitoringConfig] = {}
        self.health_statuses: Dict[int, ModelHealthStatus] = {}
        self.alert_history: Dict[int, List[Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]]] = {}
        self.reference_data: Dict[int, pd.DataFrame] = {}  # Training data distributions
        self.performance_baselines: Dict[int, Dict[str, float]] = {}
        self.prediction_logs: Dict[int, deque[PredictionLog]] = {}
        self.prediction_log_map: Dict[str, PredictionLog] = {}
        
        # Background task management
        self._background_tasks = []
        self._monitoring_active = False
        
        # Cache settings
        self.cache_prefix = "model_monitor:"
        self.cache_ttl = 3600  # 1 hour

    async def initialize(self):
        """Initialize monitoring service"""
        try:
            # Initialize Redis connection
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    retry_on_timeout=True
                )
                await self.redis_client.ping()
                logger.info("Model monitoring service connected to Redis")
            
            # Load existing monitoring configurations
            await self._load_monitoring_configs()
            
            # Start background monitoring tasks
            await self._start_background_monitoring()
            
            self._monitoring_active = True
            logger.info("Model monitoring service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize model monitoring service: {e}")
            raise

    async def cleanup(self):
        """Cleanup monitoring service"""
        try:
            self._monitoring_active = False
            
            # Cancel background tasks
            for task in self._background_tasks:
                task.cancel()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Model monitoring service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during monitoring cleanup: {e}")

    async def setup_monitoring(
        self,
        deployment_id: int,
        reference_data: pd.DataFrame,
        performance_baseline: Dict[str, float],
        config: Optional[MonitoringConfig] = None
    ) -> bool:
        """Setup monitoring for a model deployment"""
        try:
            logger.info(f"Setting up monitoring for deployment {deployment_id}")
            
            # Use default config if not provided
            if not config:
                config = MonitoringConfig(deployment_id=deployment_id)
            
            # Store configuration
            self.monitoring_configs[deployment_id] = config
            
            # Store reference data
            self.reference_data[deployment_id] = reference_data.copy()
            
            # Store performance baseline
            self.performance_baselines[deployment_id] = performance_baseline.copy()
            
            # Initialize health status
            self.health_statuses[deployment_id] = ModelHealthStatus(
                deployment_id=deployment_id,
                health_score=100.0,
                status="healthy",
                performance_metrics={},
                drift_metrics={},
                business_metrics={},
                alerts=[],
                last_updated=time.time()
            )
            
            # Initialize alert history
            self.alert_history[deployment_id] = []
            
            # Save to cache
            if self.redis_client:
                await self._save_config_to_cache(deployment_id, config)
            
            logger.info(f"Monitoring setup completed for deployment {deployment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup monitoring for deployment {deployment_id}: {e}")
            return False

    async def check_data_drift(
        self,
        deployment_id: int,
        current_data: pd.DataFrame,
        feature_columns: List[str]
    ) -> List[DataDriftAlert]:
        """Detect data drift using multiple statistical tests"""
        if deployment_id not in self.reference_data:
            logger.warning(f"No reference data for deployment {deployment_id}")
            return []
        
        try:
            reference_data = self.reference_data[deployment_id]
            config = self.monitoring_configs.get(deployment_id, MonitoringConfig(deployment_id))
            alerts = []
            
            for feature in feature_columns:
                if feature not in reference_data.columns or feature not in current_data.columns:
                    continue
                
                # Get feature data
                ref_values = reference_data[feature].dropna()
                curr_values = current_data[feature].dropna()
                
                if len(curr_values) < config.alert_settings["min_samples_for_drift"]:
                    continue
                
                # Population Stability Index (PSI)
                psi_score = await self._calculate_psi(ref_values, curr_values)
                if psi_score > config.drift_thresholds["psi_threshold"]:
                    alerts.append(DataDriftAlert(
                        deployment_id=deployment_id,
                        feature_name=feature,
                        drift_score=psi_score,
                        threshold=config.drift_thresholds["psi_threshold"],
                        detection_method="PSI",
                        timestamp=time.time(),
                        severity=self._get_drift_severity(psi_score, config.drift_thresholds["psi_threshold"]),
                        description=f"PSI drift detected: {psi_score:.3f} > {config.drift_thresholds['psi_threshold']}"
                    ))
                
                # Kolmogorov-Smirnov Test
                ks_stat, ks_p_value = stats.ks_2samp(ref_values, curr_values)
                if ks_stat > config.drift_thresholds["ks_threshold"]:
                    alerts.append(DataDriftAlert(
                        deployment_id=deployment_id,
                        feature_name=feature,
                        drift_score=ks_stat,
                        threshold=config.drift_thresholds["ks_threshold"],
                        detection_method="KS",
                        timestamp=time.time(),
                        severity=self._get_drift_severity(ks_stat, config.drift_thresholds["ks_threshold"]),
                        description=f"KS drift detected: {ks_stat:.3f} > {config.drift_thresholds['ks_threshold']}"
                    ))
                
                # Chi-square test for categorical features
                if self._is_categorical(ref_values):
                    chi2_score = await self._calculate_chi2_drift(ref_values, curr_values)
                    if chi2_score > config.drift_thresholds["chi2_threshold"]:
                        alerts.append(DataDriftAlert(
                            deployment_id=deployment_id,
                            feature_name=feature,
                            drift_score=chi2_score,
                            threshold=config.drift_thresholds["chi2_threshold"],
                            detection_method="Chi2",
                            timestamp=time.time(),
                            severity=self._get_drift_severity(chi2_score, config.drift_thresholds["chi2_threshold"]),
                            description=f"Chi-square drift detected: {chi2_score:.3f} > {config.drift_thresholds['chi2_threshold']}"
                        ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking data drift for deployment {deployment_id}: {e}")
            return []

    async def check_performance_degradation(
        self,
        deployment_id: int,
        current_metrics: Dict[str, float]
    ) -> List[PerformanceDegradationAlert]:
        """Check for performance degradation against baseline"""
        if deployment_id not in self.performance_baselines:
            logger.warning(f"No performance baseline for deployment {deployment_id}")
            return []
        
        try:
            baseline = self.performance_baselines[deployment_id]
            config = self.monitoring_configs.get(deployment_id, MonitoringConfig(deployment_id))
            alerts = []
            
            for metric_name, current_value in current_metrics.items():
                if metric_name not in baseline:
                    continue
                
                expected_value = baseline[metric_name]
                
                # Calculate degradation percentage
                if expected_value != 0:
                    degradation_pct = abs((current_value - expected_value) / expected_value)
                else:
                    degradation_pct = abs(current_value - expected_value)
                
                # Check against thresholds
                threshold = config.performance_thresholds.get(f"{metric_name}_threshold", 0.1)
                
                if degradation_pct > threshold:
                    severity = "high" if degradation_pct > threshold * 2 else "medium"
                    
                    alerts.append(PerformanceDegradationAlert(
                        deployment_id=deployment_id,
                        metric_name=metric_name,
                        current_value=current_value,
                        expected_value=expected_value,
                        degradation_percentage=degradation_pct,
                        threshold=threshold,
                        timestamp=time.time(),
                        severity=severity,
                        description=f"{metric_name} degraded by {degradation_pct:.1%}: {current_value:.3f} vs {expected_value:.3f}"
                    ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking performance degradation for deployment {deployment_id}: {e}")
            return []

    async def update_health_status(self, deployment_id: int) -> ModelHealthStatus:
        """Update and return overall health status"""
        try:
            # Get prediction service metrics
            pred_metrics = await prediction_service_module.prediction_service.get_model_metrics(deployment_id)
            
            # Get recent alerts
            recent_alerts = self._get_recent_alerts(deployment_id, hours=24)
            
            # Calculate health score
            health_score = await self._calculate_health_score(deployment_id, pred_metrics, recent_alerts)
            
            # Determine status
            if health_score >= 80:
                status = "healthy"
            elif health_score >= 60:
                status = "warning"
            else:
                status = "critical"
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(deployment_id, health_score, recent_alerts)
            
            # Update health status
            accuracy_metrics = await self.calculate_accuracy_metrics(deployment_id)

            health_status = ModelHealthStatus(
                deployment_id=deployment_id,
                health_score=health_score,
                status=status,
                performance_metrics=self._extract_performance_metrics(pred_metrics),
                accuracy_metrics=accuracy_metrics,
                drift_metrics=await self._get_drift_metrics(deployment_id),
                business_metrics=await self._get_business_metrics(deployment_id),
                alerts=recent_alerts,
                last_updated=time.time(),
                recommendations=recommendations
            )
            
            self.health_statuses[deployment_id] = health_status
            
            # Cache the health status
            if self.redis_client:
                await self._cache_health_status(deployment_id, health_status)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error updating health status for deployment {deployment_id}: {e}")
            return ModelHealthStatus(
                deployment_id=deployment_id,
                health_score=0.0,
                status="unknown",
                performance_metrics={},
                accuracy_metrics={},
                drift_metrics={},
                business_metrics={},
                alerts=[],
                last_updated=time.time(),
                recommendations=["Unable to assess model health due to monitoring error"]
            )

    async def get_health_status(self, deployment_id: int) -> Optional[ModelHealthStatus]:
        """Get current health status"""
        # Try cache first
        if self.redis_client:
            cached_status = await self._get_cached_health_status(deployment_id)
            if cached_status:
                return cached_status
        
        # Return in-memory status
        return self.health_statuses.get(deployment_id)

    async def get_all_health_statuses(self) -> List[ModelHealthStatus]:
        """Get all health statuses"""
        return list(self.health_statuses.values())

    async def get_alert_history(
        self,
        deployment_id: int,
        hours: int = 24,
        alert_type: Optional[str] = None
    ) -> List[Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]]:
        """Get alert history for a deployment"""
        if deployment_id not in self.alert_history:
            return []
        
        cutoff_time = time.time() - (hours * 3600)
        alerts = [
            alert for alert in self.alert_history[deployment_id]
            if alert.timestamp >= cutoff_time
        ]
        
        if alert_type:
            if alert_type == "drift":
                alerts = [a for a in alerts if isinstance(a, DataDriftAlert)]
            elif alert_type == "performance":
                alerts = [a for a in alerts if isinstance(a, PerformanceDegradationAlert)]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    async def add_alert(self, alert: Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]):
        """Add alert to history and trigger notifications"""
        deployment_id = alert.deployment_id
        
        if deployment_id not in self.alert_history:
            self.alert_history[deployment_id] = []
        
        # Check cooldown
        config = self.monitoring_configs.get(deployment_id, MonitoringConfig(deployment_id))
        cooldown_seconds = config.alert_settings["alert_cooldown_minutes"] * 60
        
        # Check if similar alert exists within cooldown period
        recent_similar_alerts = [
            a for a in self.alert_history[deployment_id]
            if (time.time() - a.timestamp) < cooldown_seconds and
               type(a) == type(alert) and
               getattr(a, 'feature_name', None) == getattr(alert, 'feature_name', None) and
               getattr(a, 'metric_name', None) == getattr(alert, 'metric_name', None)
        ]
        
        if recent_similar_alerts:
            logger.debug(f"Skipping alert due to cooldown: {alert}")
            return
        
        # Add alert
        self.alert_history[deployment_id].append(alert)
        
        # Limit history size
        max_history = 1000
        if len(self.alert_history[deployment_id]) > max_history:
            self.alert_history[deployment_id] = self.alert_history[deployment_id][-max_history:]
        
        # Trigger notification
        await self._send_alert_notification(alert)
        
        # Trigger remediation for severe alerts
        if alert.severity == "high":
            await self.trigger_remediation(alert)

        logger.warning(f"New alert for deployment {deployment_id}: {alert.description}")

    async def log_prediction(self, log: PredictionLog):
        """Log a prediction for monitoring"""
        deployment_id = log.deployment_id
        if deployment_id not in self.prediction_logs:
            self.prediction_logs[deployment_id] = deque(maxlen=10000)

        if len(self.prediction_logs[deployment_id]) == self.prediction_logs[deployment_id].maxlen:
            # The oldest item is about to be evicted.
            oldest_log = self.prediction_logs[deployment_id][0]
            if oldest_log.request_id in self.prediction_log_map:
                del self.prediction_log_map[oldest_log.request_id]

        self.prediction_logs[deployment_id].append(log)
        self.prediction_log_map[log.request_id] = log

        logger.debug(f"Logged prediction {log.request_id} for deployment {deployment_id}")

    async def log_ground_truth(self, deployment_id: int, request_id: str, ground_truth: Union[float, int, str]):
        """Log ground truth for a past prediction."""
        if request_id in self.prediction_log_map:
            log = self.prediction_log_map[request_id]
            if log.deployment_id == deployment_id:
                log.ground_truth = ground_truth
                logger.info(f"Logged ground truth for request {request_id}")
                return
        logger.warning(f"Could not find prediction with request_id {request_id} for deployment {deployment_id} to log ground truth.")

    async def check_concept_drift(self, deployment_id: int, current_predictions: pd.Series) -> Optional[ConceptDriftAlert]:
        """Detect concept drift by comparing prediction distributions."""
        if deployment_id not in self.reference_data or 'prediction' not in self.reference_data[deployment_id].columns:
            return None

        reference_predictions = self.reference_data[deployment_id]['prediction'].dropna()
        current_predictions = current_predictions.dropna()

        if len(reference_predictions) == 0 or len(current_predictions) == 0:
            return None

        ks_stat, p_value = stats.ks_2samp(reference_predictions, current_predictions)

        threshold = 0.05  # p-value threshold
        if p_value < threshold:
            return ConceptDriftAlert(
                deployment_id=deployment_id,
                drift_score=ks_stat,
                p_value=p_value,
                description=f"Concept drift detected (KS test on predictions). p-value: {p_value:.4f}",
                severity="medium"
            )
        return None

    async def calculate_accuracy_metrics(self, deployment_id: int, time_window_hours: int = 24) -> Dict[str, float]:
        """Calculate accuracy metrics over a time window."""
        if deployment_id not in self.prediction_logs:
            return {}

        cutoff_time = time.time() - (time_window_hours * 3600)

        predictions = []
        ground_truths = []

        for log in self.prediction_logs[deployment_id]:
            if log.timestamp >= cutoff_time and log.ground_truth is not None:
                predictions.append(log.prediction)
                ground_truths.append(log.ground_truth)

        if not predictions:
            return {}

        try:
            accuracy = accuracy_score(ground_truths, predictions)
            precision, recall, f1, _ = precision_recall_fscore_support(ground_truths, predictions, average='weighted', zero_division=0)

            return {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "samples_with_ground_truth": float(len(ground_truths))
            }
        except Exception as e:
            logger.error(f"Error calculating accuracy metrics for deployment {deployment_id}: {e}")
            return {}

    async def trigger_remediation(self, alert: Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]):
        """Trigger automated remediation actions."""
        logger.info(f"Triggering remediation for high-severity alert on deployment {alert.deployment_id}")

        # Example remediation: flag for retraining
        await self._flag_for_retraining(alert.deployment_id, alert)

    async def _flag_for_retraining(self, deployment_id: int, alert: Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]):
        """Set a flag in the model deployment's health_metrics to indicate need for retraining."""
        try:
            db = next(get_db_session())
            deployment = db.query(ModelDeployment).filter(ModelDeployment.id == deployment_id).first()
            if deployment:
                if not deployment.health_metrics:
                    deployment.health_metrics = {}

                new_health_metrics = deployment.health_metrics.copy()
                new_health_metrics["retraining_needed"] = True
                new_health_metrics["retraining_reason"] = f"High-severity alert: {type(alert).__name__}"
                new_health_metrics["retraining_flagged_at"] = datetime.utcnow().isoformat()
                deployment.health_metrics = new_health_metrics

                db.commit()
                logger.info(f"Deployment {deployment_id} flagged for retraining.")
            else:
                logger.warning(f"Could not find deployment {deployment_id} to flag for retraining.")
        except Exception as e:
            logger.error(f"Error flagging deployment {deployment_id} for retraining: {e}")
            db.rollback()
        finally:
            if 'db' in locals() and db.is_active:
                db.close()

    # Private helper methods
    
    async def _load_monitoring_configs(self):
        """Load monitoring configurations from database/cache"""
        try:
            # Load from database
            db = next(get_db_session())
            deployments = db.query(ModelDeployment).filter(
                ModelDeployment.is_active == True,
                ModelDeployment.status == DeploymentStatus.DEPLOYED
            ).all()
            
            for deployment in deployments:
                # Try to load config from cache first
                if self.redis_client:
                    config = await self._load_config_from_cache(deployment.id)
                    if config:
                        self.monitoring_configs[deployment.id] = config
                        continue
                
                # Create default config
                self.monitoring_configs[deployment.id] = MonitoringConfig(deployment_id=deployment.id)
            
            db.close()
            logger.info(f"Loaded monitoring configs for {len(self.monitoring_configs)} deployments")
            
        except Exception as e:
            logger.error(f"Error loading monitoring configs: {e}")

    async def _start_background_monitoring(self):
        """Start background monitoring tasks"""
        # Health check task
        health_task = asyncio.create_task(self._health_check_loop())
        self._background_tasks.append(health_task)
        
        # Data drift monitoring task  
        drift_task = asyncio.create_task(self._drift_monitoring_loop())
        self._background_tasks.append(drift_task)
        
        # Performance monitoring task
        perf_task = asyncio.create_task(self._performance_monitoring_loop())
        self._background_tasks.append(perf_task)

    async def _health_check_loop(self):
        """Background task for health status updates"""
        while self._monitoring_active:
            try:
                for deployment_id in self.monitoring_configs.keys():
                    await self.update_health_status(deployment_id)
                    await asyncio.sleep(1)  # Prevent overwhelming
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(60)

    async def _drift_monitoring_loop(self):
        """Background task for drift monitoring"""
        while self._monitoring_active:
            try:
                for deployment_id, config in self.monitoring_configs.items():
                    if deployment_id not in self.prediction_logs:
                        continue

                    # Get recent prediction logs for drift check
                    cutoff_time = time.time() - 3600  # Last hour of data
                    recent_logs = [
                        log for log in self.prediction_logs[deployment_id]
                        if log.timestamp >= cutoff_time
                    ]

                    if len(recent_logs) < config.alert_settings.get("min_samples_for_drift", 100):
                        continue

                    # Create DataFrame from logs for data drift
                    current_features = pd.DataFrame([log.features for log in recent_logs])

                    if deployment_id in self.reference_data:
                        feature_columns = list(self.reference_data[deployment_id].columns)

                        # Data drift check
                        data_drift_alerts = await self.check_data_drift(
                            deployment_id,
                            current_features,
                            feature_columns
                        )
                        for alert in data_drift_alerts:
                            await self.add_alert(alert)

                        # Concept drift check
                        current_predictions = pd.Series([log.prediction for log in recent_logs])
                        concept_drift_alert = await self.check_concept_drift(
                            deployment_id,
                            current_predictions
                        )
                        if concept_drift_alert:
                            await self.add_alert(concept_drift_alert)

                await asyncio.sleep(600)  # Run every 10 minutes
                
            except Exception as e:
                logger.error(f"Error in drift monitoring loop: {e}")
                await asyncio.sleep(300)

    async def _performance_monitoring_loop(self):
        """Background task for performance monitoring"""
        while self._monitoring_active:
            try:
                for deployment_id in self.monitoring_configs.keys():
                    # Get current metrics from prediction service
                    pred_metrics = await prediction_service_module.prediction_service.get_model_metrics(deployment_id)
                    if pred_metrics:
                        current_metrics = {
                            "error_rate": pred_metrics.error_rate,
                            "avg_latency_ms": pred_metrics.avg_latency_ms,
                            "p95_latency_ms": pred_metrics.p95_latency_ms
                        }
                        
                        # Check for performance degradation
                        alerts = await self.check_performance_degradation(deployment_id, current_metrics)
                        for alert in alerts:
                            await self.add_alert(alert)
                
                await asyncio.sleep(180)  # Run every 3 minutes
                
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(180)

    async def _calculate_psi(self, reference_data: pd.Series, current_data: pd.Series, buckets: int = 10) -> float:
        """Calculate Population Stability Index"""
        try:
            # Create bins based on reference data
            _, bin_edges = pd.cut(reference_data, bins=buckets, retbins=True)
            
            # Calculate distributions
            ref_counts = pd.cut(reference_data, bins=bin_edges).value_counts().sort_index()
            curr_counts = pd.cut(current_data, bins=bin_edges).value_counts().sort_index()
            
            # Convert to percentages
            ref_pct = ref_counts / len(reference_data)
            curr_pct = curr_counts / len(current_data)
            
            # Calculate PSI
            psi = 0
            for i in range(len(ref_pct)):
                if ref_pct.iloc[i] > 0 and curr_pct.iloc[i] > 0:
                    psi += (curr_pct.iloc[i] - ref_pct.iloc[i]) * np.log(curr_pct.iloc[i] / ref_pct.iloc[i])
            
            return psi
            
        except Exception as e:
            logger.error(f"Error calculating PSI: {e}")
            return 0.0

    async def _calculate_chi2_drift(self, reference_data: pd.Series, current_data: pd.Series) -> float:
        """Calculate chi-square drift score for categorical data"""
        try:
            # Get value counts
            ref_counts = reference_data.value_counts()
            curr_counts = current_data.value_counts()
            
            # Align the series
            all_categories = set(ref_counts.index) | set(curr_counts.index)
            ref_aligned = pd.Series(0, index=all_categories)
            curr_aligned = pd.Series(0, index=all_categories)
            
            ref_aligned.update(ref_counts)
            curr_aligned.update(curr_counts)
            
            # Perform chi-square test
            chi2_stat, p_value = stats.chisquare(curr_aligned, ref_aligned)
            return p_value  # Return p-value (lower means more drift)
            
        except Exception as e:
            logger.error(f"Error calculating chi-square drift: {e}")
            return 1.0

    def _is_categorical(self, data: pd.Series) -> bool:
        """Check if data is categorical"""
        return data.dtype == 'object' or data.nunique() < 20

    def _get_drift_severity(self, score: float, threshold: float) -> str:
        """Determine drift severity level"""
        if score > threshold * 3:
            return "high"
        elif score > threshold * 1.5:
            return "medium"
        else:
            return "low"

    def _get_recent_alerts(
        self,
        deployment_id: int,
        hours: int = 24
    ) -> List[Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]]:
        """Get recent alerts for health calculation"""
        if deployment_id not in self.alert_history:
            return []
        
        cutoff_time = time.time() - (hours * 3600)
        return [
            alert for alert in self.alert_history[deployment_id]
            if alert.timestamp >= cutoff_time
        ]

    async def _calculate_health_score(
        self,
        deployment_id: int,
        pred_metrics: Optional[PredictionMetrics],
        recent_alerts: List[Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]]
    ) -> float:
        """Calculate overall health score (0-100)"""
        score = 100.0
        
        # Deduct for prediction service issues
        if pred_metrics:
            if pred_metrics.error_rate > 0.1:
                score -= min(50, pred_metrics.error_rate * 500)
            
            if pred_metrics.avg_latency_ms > 1000:
                score -= min(20, (pred_metrics.avg_latency_ms - 1000) / 100)
        
        # Deduct for alerts
        for alert in recent_alerts:
            if alert.severity == "high":
                score -= 15
            elif alert.severity == "medium":
                score -= 10
            else:
                score -= 5
        
        return max(0.0, score)

    def _extract_performance_metrics(self, pred_metrics: Optional[PredictionMetrics]) -> Dict[str, float]:
        """Extract performance metrics for health status"""
        if not pred_metrics:
            return {}
        
        return {
            "total_requests": float(pred_metrics.total_requests),
            "error_rate": pred_metrics.error_rate,
            "avg_latency_ms": pred_metrics.avg_latency_ms,
            "p50_latency_ms": pred_metrics.p50_latency_ms,
            "p90_latency_ms": pred_metrics.p90_latency_ms,
            "p95_latency_ms": pred_metrics.p95_latency_ms,
            "p99_latency_ms": pred_metrics.p99_latency_ms
        }

    async def _get_drift_metrics(self, deployment_id: int) -> Dict[str, float]:
        """Get drift metrics for health status"""
        # Placeholder - would calculate from recent drift checks
        return {
            "features_with_drift": 0,
            "max_drift_score": 0.0,
            "avg_drift_score": 0.0
        }

    async def _get_business_metrics(self, deployment_id: int) -> Dict[str, float]:
        """Get business metrics for health status"""
        # Placeholder - would integrate with trading performance tracking
        return {
            "prediction_accuracy": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        }

    async def _generate_recommendations(
        self,
        deployment_id: int,
        health_score: float,
        recent_alerts: List[Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]]
    ) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        
        if health_score < 60:
            recommendations.append("Model health is critical - consider immediate investigation")
        
        # Check for specific alert patterns
        drift_alerts = [a for a in recent_alerts if isinstance(a, DataDriftAlert)]
        perf_alerts = [a for a in recent_alerts if isinstance(a, PerformanceDegradationAlert)]
        
        if len(drift_alerts) > 3:
            recommendations.append("Multiple drift alerts detected - retrain model with recent data")
        
        if len(perf_alerts) > 2:
            recommendations.append("Performance degradation detected - review model deployment")
        
        if not recommendations and health_score < 80:
            recommendations.append("Monitor model closely for potential issues")
        
        return recommendations

    async def _send_alert_notification(self, alert: Union[DataDriftAlert, PerformanceDegradationAlert, ConceptDriftAlert]):
        """Send alert notification (placeholder)"""
        config = self.monitoring_configs.get(alert.deployment_id)
        if not config or not config.alert_settings.get("enable_alerts"):
            return

        channels = config.alert_settings.get("notification_channels", ["log"])

        subject = f"Model Alert for Deployment {alert.deployment_id}: {type(alert).__name__}"
        body = f"Alert: {alert.description}\nSeverity: {alert.severity}\nTimestamp: {datetime.fromtimestamp(alert.timestamp)}"

        if "log" in channels:
            logger.warning(f"Alert for deployment {alert.deployment_id}: {alert.description}")

        if "email" in channels:
            await _send_email_notification(subject, body)

        if "slack" in channels:
            await _send_slack_notification("#monitoring-alerts", body)

    async def _save_config_to_cache(self, deployment_id: int, config: MonitoringConfig):
        """Save monitoring config to cache"""
        if not self.redis_client:
            return
        
        try:
            key = f"{self.cache_prefix}config:{deployment_id}"
            config_data = {
                "deployment_id": config.deployment_id,
                "performance_thresholds": config.performance_thresholds,
                "drift_thresholds": config.drift_thresholds,
                "alert_settings": config.alert_settings,
                "business_thresholds": config.business_thresholds
            }
            await self.redis_client.setex(key, self.cache_ttl, json.dumps(config_data))
        except Exception as e:
            logger.error(f"Error saving config to cache: {e}")

    async def _load_config_from_cache(self, deployment_id: int) -> Optional[MonitoringConfig]:
        """Load monitoring config from cache"""
        if not self.redis_client:
            return None
        
        try:
            key = f"{self.cache_prefix}config:{deployment_id}"
            config_data = await self.redis_client.get(key)
            if config_data:
                data = json.loads(config_data)
                return MonitoringConfig(**data)
        except Exception as e:
            logger.error(f"Error loading config from cache: {e}")
        
        return None

    async def _cache_health_status(self, deployment_id: int, health_status: ModelHealthStatus):
        """Cache health status"""
        if not self.redis_client:
            return
        
        try:
            key = f"{self.cache_prefix}health:{deployment_id}"
            # Convert to dict for JSON serialization
            health_data = {
                "deployment_id": health_status.deployment_id,
                "health_score": health_status.health_score,
                "status": health_status.status,
                "performance_metrics": health_status.performance_metrics,
                "accuracy_metrics": health_status.accuracy_metrics,
                "drift_metrics": health_status.drift_metrics,
                "business_metrics": health_status.business_metrics,
                "alerts": [alert.__dict__ for alert in health_status.alerts],
                "last_updated": health_status.last_updated,
                "recommendations": health_status.recommendations
            }
            await self.redis_client.setex(key, 300, json.dumps(health_data))  # 5 minutes TTL
        except Exception as e:
            logger.error(f"Error caching health status: {e}")

    async def _get_cached_health_status(self, deployment_id: int) -> Optional[ModelHealthStatus]:
        """Get cached health status"""
        if not self.redis_client:
            return None
        
        try:
            key = f"{self.cache_prefix}health:{deployment_id}"
            health_data = await self.redis_client.get(key)
            if health_data:
                data = json.loads(health_data)
                if 'accuracy_metrics' not in data:
                    data['accuracy_metrics'] = {}
                # Convert alert dicts back to objects (simplified)
                alerts = []
                for alert_data in data.get("alerts", []):
                    if "p_value" in alert_data:
                        alerts.append(ConceptDriftAlert(**alert_data))
                    elif "feature_name" in alert_data:
                        alerts.append(DataDriftAlert(**alert_data))
                    else:
                        alerts.append(PerformanceDegradationAlert(**alert_data))
                
                data["alerts"] = alerts
                return ModelHealthStatus(**data)
        except Exception as e:
            logger.error(f"Error getting cached health status: {e}")
        
        return None


# Global instance
model_monitor = ModelMonitoringService()