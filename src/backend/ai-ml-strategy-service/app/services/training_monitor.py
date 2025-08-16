"""
Training progress monitoring system for Phase 4: Model Training Orchestrator.
Provides real-time monitoring, alerting, and analytics for training jobs.
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import numpy as np
from collections import defaultdict, deque

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.training import (
    TrainingJob, TrainingMetric, HyperparameterTrial, 
    HyperparameterTuningJob, JobStatus
)
from app.core.config import get_settings


class MetricsCollector:
    """Collects and processes training metrics in real-time."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MetricsCollector")
        self.metric_buffer = defaultdict(deque)  # Buffer for real-time metrics
        self.anomaly_detector = MetricAnomalyDetector()
    
    async def record_metric(self, training_job_id: str, metric_data: Dict[str, Any],
                          db: AsyncSession) -> Dict[str, Any]:
        """Record a training metric."""
        try:
            # Create metric record
            metric = TrainingMetric(
                training_job_id=UUID(training_job_id),
                trial_id=UUID(metric_data.get("trial_id")) if metric_data.get("trial_id") else None,
                metric_name=metric_data["metric_name"],
                metric_value=metric_data["metric_value"],
                metric_type=metric_data.get("metric_type", "custom"),
                dataset_split=metric_data.get("dataset_split", "train"),
                epoch=metric_data.get("epoch"),
                step=metric_data.get("step"),
                timestamp=metric_data.get("timestamp", datetime.utcnow().isoformat()),
                batch_size=metric_data.get("batch_size"),
                learning_rate=metric_data.get("learning_rate")
            )
            
            db.add(metric)
            await db.commit()
            
            # Add to real-time buffer
            buffer_key = f"{training_job_id}:{metric_data['metric_name']}"
            self.metric_buffer[buffer_key].append({
                "timestamp": metric.timestamp,
                "value": metric.metric_value,
                "epoch": metric.epoch,
                "step": metric.step
            })
            
            # Keep buffer size manageable
            if len(self.metric_buffer[buffer_key]) > 1000:
                self.metric_buffer[buffer_key].popleft()
            
            # Check for anomalies
            anomaly_result = await self.anomaly_detector.check_metric_anomaly(
                buffer_key, list(self.metric_buffer[buffer_key])
            )
            
            return {
                "success": True,
                "metric_id": str(metric.id),
                "anomaly_detected": anomaly_result.get("anomaly_detected", False),
                "anomaly_score": anomaly_result.get("anomaly_score", 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to record metric: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_real_time_metrics(self, training_job_id: str, 
                                  metric_names: List[str] = None) -> Dict[str, Any]:
        """Get real-time metrics for a training job."""
        try:
            job_metrics = {}
            
            for buffer_key, metrics in self.metric_buffer.items():
                if buffer_key.startswith(f"{training_job_id}:"):
                    metric_name = buffer_key.split(":", 1)[1]
                    
                    if metric_names is None or metric_name in metric_names:
                        job_metrics[metric_name] = {
                            "latest_value": metrics[-1]["value"] if metrics else None,
                            "trend": self._calculate_trend(metrics),
                            "history": list(metrics)[-100:],  # Last 100 points
                            "statistics": self._calculate_statistics(metrics)
                        }
            
            return {
                "training_job_id": training_job_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": job_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get real-time metrics: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_trend(self, metrics: deque) -> Dict[str, Any]:
        """Calculate trend analysis for metrics."""
        if len(metrics) < 2:
            return {"direction": "insufficient_data", "slope": 0.0}
        
        # Get last 10 points for trend calculation
        recent_metrics = list(metrics)[-10:]
        values = [m["value"] for m in recent_metrics]
        
        # Simple linear regression for trend
        n = len(values)
        x = np.arange(n)
        y = np.array(values)
        
        if n > 1:
            slope = np.polyfit(x, y, 1)[0]
            
            if abs(slope) < 0.001:
                direction = "stable"
            elif slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"
            
            return {"direction": direction, "slope": float(slope)}
        
        return {"direction": "stable", "slope": 0.0}
    
    def _calculate_statistics(self, metrics: deque) -> Dict[str, Any]:
        """Calculate basic statistics for metrics."""
        if not metrics:
            return {}
        
        values = [m["value"] for m in metrics]
        
        return {
            "count": len(values),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "latest": float(values[-1]) if values else None
        }


class MetricAnomalyDetector:
    """Detects anomalies in training metrics using statistical methods."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AnomalyDetector")
        self.baseline_windows = {}  # Store baseline statistics
    
    async def check_metric_anomaly(self, metric_key: str, 
                                 metric_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if latest metric value is anomalous."""
        try:
            if len(metric_history) < 10:  # Need minimum history
                return {"anomaly_detected": False, "reason": "insufficient_history"}
            
            values = [m["value"] for m in metric_history]
            latest_value = values[-1]
            
            # Calculate baseline statistics (excluding latest value)
            baseline_values = values[:-1]
            baseline_mean = np.mean(baseline_values)
            baseline_std = np.std(baseline_values)
            
            # Z-score anomaly detection
            if baseline_std > 0:
                z_score = abs(latest_value - baseline_mean) / baseline_std
                z_threshold = 3.0  # 3-sigma rule
                
                if z_score > z_threshold:
                    return {
                        "anomaly_detected": True,
                        "anomaly_score": float(z_score),
                        "method": "z_score",
                        "threshold": z_threshold,
                        "latest_value": latest_value,
                        "baseline_mean": baseline_mean,
                        "baseline_std": baseline_std
                    }
            
            # Check for sudden spikes or drops
            if len(values) >= 5:
                recent_values = values[-5:]
                recent_mean = np.mean(recent_values[:-1])
                
                if recent_mean > 0:
                    spike_ratio = latest_value / recent_mean
                    
                    if spike_ratio > 10 or spike_ratio < 0.1:  # 10x spike or 10x drop
                        return {
                            "anomaly_detected": True,
                            "anomaly_score": float(abs(np.log10(spike_ratio))),
                            "method": "spike_detection",
                            "spike_ratio": float(spike_ratio),
                            "latest_value": latest_value,
                            "recent_mean": recent_mean
                        }
            
            return {"anomaly_detected": False, "anomaly_score": 0.0}
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {str(e)}")
            return {"anomaly_detected": False, "error": str(e)}


class TrainingProgressMonitor:
    """Main training progress monitoring service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        
        # Monitoring thresholds
        self.thresholds = {
            "stagnation_epochs": 20,  # Alert if no improvement for 20 epochs
            "loss_explosion_threshold": 1e6,
            "nan_threshold": 0.01,  # Alert if >1% of metrics are NaN
            "memory_usage_threshold": 0.9,  # Alert at 90% memory usage
            "slow_progress_threshold": 0.1  # Alert if progress < 10% expected
        }
    
    async def start_monitoring(self, training_job_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Start monitoring a training job."""
        try:
            result = await db.execute(
                select(TrainingJob)
                .where(TrainingJob.id == UUID(training_job_id))
            )
            training_job = result.scalar_one_or_none()
            
            if not training_job:
                return {"success": False, "error": "Training job not found"}
            
            # Initialize monitoring
            monitoring_config = {
                "job_id": training_job_id,
                "start_time": datetime.utcnow().isoformat(),
                "monitoring_enabled": True,
                "alert_thresholds": self.thresholds,
                "metrics_to_monitor": ["loss", "accuracy", "val_loss", "val_accuracy"],
                "alert_recipients": [str(training_job.user_id)]
            }
            
            self.logger.info(f"Started monitoring for training job {training_job_id}")
            
            return {
                "success": True,
                "monitoring_config": monitoring_config,
                "message": "Monitoring started successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def record_training_metric(self, training_job_id: str, metric_data: Dict[str, Any],
                                   db: AsyncSession) -> Dict[str, Any]:
        """Record a training metric and check for alerts."""
        try:
            # Record the metric
            result = await self.metrics_collector.record_metric(training_job_id, metric_data, db)
            
            if not result["success"]:
                return result
            
            # Check for alert conditions
            alert_checks = await self._check_alert_conditions(training_job_id, metric_data, db)
            
            # Trigger alerts if necessary
            if alert_checks.get("alerts"):
                for alert in alert_checks["alerts"]:
                    await self.alert_manager.send_alert(training_job_id, alert, db)
            
            return {
                **result,
                "alerts_triggered": alert_checks.get("alerts", []),
                "health_status": alert_checks.get("health_status", "healthy")
            }
            
        except Exception as e:
            self.logger.error(f"Failed to record training metric: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_training_progress(self, training_job_id: str, 
                                  db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive training progress information."""
        try:
            # Get training job details
            result = await db.execute(
                select(TrainingJob)
                .where(TrainingJob.id == UUID(training_job_id))
            )
            training_job = result.scalar_one_or_none()
            
            if not training_job:
                return {"error": "Training job not found"}
            
            # Get metrics from database
            result = await db.execute(
                select(TrainingMetric)
                .where(TrainingMetric.training_job_id == UUID(training_job_id))
                .order_by(TrainingMetric.timestamp.desc())
                .limit(1000)
            )
            metrics = result.scalars().all()
            
            # Get real-time metrics
            real_time_metrics = await self.metrics_collector.get_real_time_metrics(training_job_id)
            
            # Calculate progress statistics
            progress_stats = await self._calculate_progress_statistics(training_job, metrics)
            
            # Get health assessment
            health_assessment = await self._assess_training_health(training_job_id, metrics)
            
            # Estimate completion time
            completion_estimate = await self._estimate_completion_time(training_job, metrics)
            
            return {
                "training_job_id": training_job_id,
                "job_status": training_job.status.value,
                "progress_percentage": training_job.progress_percentage,
                "current_epoch": self._get_current_epoch(metrics),
                "total_epochs": training_job.training_config.get("epochs", "unknown"),
                "start_time": training_job.start_time.isoformat() if training_job.start_time else None,
                "elapsed_time": self._calculate_elapsed_time(training_job),
                "estimated_completion": completion_estimate,
                "progress_statistics": progress_stats,
                "real_time_metrics": real_time_metrics.get("metrics", {}),
                "health_assessment": health_assessment,
                "resource_usage": {
                    "cpu_hours": training_job.cpu_hours,
                    "gpu_hours": training_job.gpu_hours,
                    "memory_gb_hours": training_job.memory_gb_hours,
                    "estimated_cost": training_job.estimated_cost,
                    "actual_cost": training_job.actual_cost
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get training progress: {str(e)}")
            return {"error": str(e)}
    
    async def get_hyperparameter_tuning_progress(self, tuning_job_id: str,
                                               db: AsyncSession) -> Dict[str, Any]:
        """Get hyperparameter tuning progress."""
        try:
            result = await db.execute(
                select(HyperparameterTuningJob)
                .options(selectinload(HyperparameterTuningJob.trials))
                .where(HyperparameterTuningJob.id == UUID(tuning_job_id))
            )
            tuning_job = result.scalar_one_or_none()
            
            if not tuning_job:
                return {"error": "Tuning job not found"}
            
            trials = tuning_job.trials
            
            # Calculate trial statistics
            total_trials = len(trials)
            completed_trials = len([t for t in trials if t.status == JobStatus.COMPLETED])
            running_trials = len([t for t in trials if t.status == JobStatus.RUNNING])
            failed_trials = len([t for t in trials if t.status == JobStatus.FAILED])
            
            # Get objective values for completed trials
            objective_values = [
                t.objective_value for t in trials 
                if t.status == JobStatus.COMPLETED and t.objective_value is not None
            ]
            
            # Calculate optimization progress
            optimization_progress = self._calculate_optimization_progress(
                objective_values, tuning_job.optimization_objective
            )
            
            # Get best trial info
            best_trial_info = None
            if tuning_job.best_trial_id:
                best_trial = next((t for t in trials if t.id == tuning_job.best_trial_id), None)
                if best_trial:
                    best_trial_info = {
                        "trial_number": best_trial.trial_number,
                        "hyperparameters": best_trial.hyperparameters,
                        "objective_value": best_trial.objective_value,
                        "final_metrics": best_trial.final_metrics
                    }
            
            # Calculate convergence metrics
            convergence_analysis = self._analyze_optimization_convergence(objective_values)
            
            return {
                "tuning_job_id": tuning_job_id,
                "status": tuning_job.status.value,
                "progress_percentage": (completed_trials / tuning_job.max_trials) * 100,
                "trial_statistics": {
                    "total_trials": total_trials,
                    "completed_trials": completed_trials,
                    "running_trials": running_trials,
                    "failed_trials": failed_trials,
                    "max_trials": tuning_job.max_trials,
                    "success_rate": completed_trials / max(total_trials, 1) * 100
                },
                "optimization_progress": optimization_progress,
                "best_trial": best_trial_info,
                "convergence_analysis": convergence_analysis,
                "start_time": tuning_job.start_time.isoformat() if tuning_job.start_time else None,
                "elapsed_time": self._calculate_elapsed_time(tuning_job),
                "estimated_completion": self._estimate_tuning_completion(tuning_job, trials)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get tuning progress: {str(e)}")
            return {"error": str(e)}
    
    async def _check_alert_conditions(self, training_job_id: str, metric_data: Dict[str, Any],
                                    db: AsyncSession) -> Dict[str, Any]:
        """Check for alert conditions based on latest metric."""
        alerts = []
        health_status = "healthy"
        
        try:
            metric_name = metric_data["metric_name"]
            metric_value = metric_data["metric_value"]
            
            # Check for NaN values
            if np.isnan(metric_value) or np.isinf(metric_value):
                alerts.append({
                    "type": "invalid_metric_value",
                    "severity": "critical",
                    "message": f"Invalid {metric_name} value: {metric_value}",
                    "metric_name": metric_name,
                    "metric_value": metric_value
                })
                health_status = "critical"
            
            # Check for loss explosion
            if "loss" in metric_name.lower() and metric_value > self.thresholds["loss_explosion_threshold"]:
                alerts.append({
                    "type": "loss_explosion",
                    "severity": "critical",
                    "message": f"Loss explosion detected: {metric_value}",
                    "metric_name": metric_name,
                    "metric_value": metric_value
                })
                health_status = "critical"
            
            # Check for training stagnation (requires historical data)
            if "loss" in metric_name.lower():
                stagnation_check = await self._check_training_stagnation(training_job_id, db)
                if stagnation_check.get("stagnant"):
                    alerts.append({
                        "type": "training_stagnation",
                        "severity": "warning",
                        "message": f"Training may be stagnating: no improvement for {stagnation_check['epochs']} epochs",
                        "epochs_without_improvement": stagnation_check["epochs"]
                    })
                    if health_status == "healthy":
                        health_status = "warning"
            
            return {
                "alerts": alerts,
                "health_status": health_status
            }
            
        except Exception as e:
            self.logger.error(f"Alert condition check failed: {str(e)}")
            return {"alerts": [], "health_status": "unknown", "error": str(e)}
    
    async def _check_training_stagnation(self, training_job_id: str, 
                                       db: AsyncSession) -> Dict[str, Any]:
        """Check if training is stagnating."""
        try:
            # Get recent loss metrics
            result = await db.execute(
                select(TrainingMetric)
                .where(
                    and_(
                        TrainingMetric.training_job_id == UUID(training_job_id),
                        TrainingMetric.metric_name.ilike("%loss%"),
                        TrainingMetric.dataset_split == "validation"
                    )
                )
                .order_by(TrainingMetric.epoch.desc())
                .limit(self.thresholds["stagnation_epochs"])
            )
            
            recent_metrics = result.scalars().all()
            
            if len(recent_metrics) < self.thresholds["stagnation_epochs"]:
                return {"stagnant": False, "reason": "insufficient_data"}
            
            # Check if validation loss has improved in recent epochs
            values = [m.metric_value for m in reversed(recent_metrics)]
            best_recent = min(values)
            latest_avg = np.mean(values[-5:])  # Average of last 5 epochs
            
            # Consider stagnant if latest average is not significantly better than best recent
            improvement_threshold = 0.01  # 1% improvement threshold
            relative_improvement = (best_recent - latest_avg) / abs(best_recent) if best_recent != 0 else 0
            
            if relative_improvement < improvement_threshold:
                return {
                    "stagnant": True,
                    "epochs": len(recent_metrics),
                    "best_recent_loss": best_recent,
                    "latest_avg_loss": latest_avg,
                    "improvement": relative_improvement
                }
            
            return {"stagnant": False}
            
        except Exception as e:
            self.logger.error(f"Stagnation check failed: {str(e)}")
            return {"stagnant": False, "error": str(e)}
    
    def _calculate_progress_statistics(self, training_job: TrainingJob, 
                                     metrics: List[TrainingMetric]) -> Dict[str, Any]:
        """Calculate progress statistics from metrics."""
        if not metrics:
            return {"error": "No metrics available"}
        
        # Group metrics by name
        metric_groups = defaultdict(list)
        for metric in metrics:
            metric_groups[metric.metric_name].append(metric)
        
        statistics = {}
        
        for metric_name, metric_list in metric_groups.items():
            if not metric_list:
                continue
                
            values = [m.metric_value for m in metric_list if not np.isnan(m.metric_value)]
            epochs = [m.epoch for m in metric_list if m.epoch is not None]
            
            if values:
                statistics[metric_name] = {
                    "latest_value": values[0],  # Most recent (first in desc order)
                    "best_value": min(values) if "loss" in metric_name.lower() else max(values),
                    "mean_value": np.mean(values),
                    "std_value": np.std(values),
                    "trend": "improving" if self._is_improving(values) else "stable_or_declining",
                    "data_points": len(values),
                    "latest_epoch": max(epochs) if epochs else None
                }
        
        return statistics
    
    def _is_improving(self, values: List[float]) -> bool:
        """Check if metric values show improvement over time."""
        if len(values) < 5:
            return False
        
        # Compare first quarter with last quarter
        quarter_size = len(values) // 4
        early_values = values[-quarter_size:] if quarter_size > 0 else values[-1:]
        late_values = values[:quarter_size] if quarter_size > 0 else values[:1]
        
        early_mean = np.mean(early_values)
        late_mean = np.mean(late_values)
        
        # For loss metrics, improvement means decrease
        # For accuracy metrics, improvement means increase
        # This is a simplified heuristic
        return late_mean < early_mean  # Assuming loss-like metric
    
    def _get_current_epoch(self, metrics: List[TrainingMetric]) -> Optional[int]:
        """Get current epoch from metrics."""
        if not metrics:
            return None
        
        epochs = [m.epoch for m in metrics if m.epoch is not None]
        return max(epochs) if epochs else None
    
    def _calculate_elapsed_time(self, job) -> Optional[str]:
        """Calculate elapsed time for a job."""
        if not job.start_time:
            return None
        
        end_time = job.end_time or datetime.utcnow()
        elapsed = end_time - job.start_time
        
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        
        return f"{hours}h {minutes}m"
    
    async def _estimate_completion_time(self, training_job: TrainingJob,
                                      metrics: List[TrainingMetric]) -> Optional[str]:
        """Estimate training completion time."""
        try:
            if not training_job.start_time or training_job.progress_percentage <= 0:
                return None
            
            elapsed = datetime.utcnow() - training_job.start_time
            elapsed_seconds = elapsed.total_seconds()
            
            # Estimate based on progress percentage
            if training_job.progress_percentage > 0:
                total_estimated_seconds = elapsed_seconds * (100 / training_job.progress_percentage)
                remaining_seconds = total_estimated_seconds - elapsed_seconds
                
                if remaining_seconds > 0:
                    remaining_hours = int(remaining_seconds // 3600)
                    remaining_minutes = int((remaining_seconds % 3600) // 60)
                    
                    completion_time = datetime.utcnow() + timedelta(seconds=remaining_seconds)
                    return completion_time.isoformat()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Completion estimation failed: {str(e)}")
            return None
    
    async def _assess_training_health(self, training_job_id: str,
                                    metrics: List[TrainingMetric]) -> Dict[str, Any]:
        """Assess overall training health."""
        health = {
            "status": "healthy",
            "score": 100,
            "issues": [],
            "recommendations": []
        }
        
        try:
            if not metrics:
                health["status"] = "unknown"
                health["score"] = 0
                health["issues"].append("No metrics available")
                return health
            
            # Check for NaN values
            nan_count = sum(1 for m in metrics if np.isnan(m.metric_value))
            nan_ratio = nan_count / len(metrics)
            
            if nan_ratio > self.thresholds["nan_threshold"]:
                health["score"] -= 30
                health["issues"].append(f"High NaN ratio: {nan_ratio:.2%}")
                health["recommendations"].append("Check data preprocessing and model architecture")
            
            # Check for extreme values
            values = [m.metric_value for m in metrics if not np.isnan(m.metric_value)]
            if values:
                max_value = max(values)
                if max_value > 1e6:
                    health["score"] -= 20
                    health["issues"].append("Extreme metric values detected")
                    health["recommendations"].append("Consider gradient clipping and learning rate adjustment")
            
            # Determine overall status
            if health["score"] >= 80:
                health["status"] = "healthy"
            elif health["score"] >= 60:
                health["status"] = "warning"
            else:
                health["status"] = "critical"
            
            return health
            
        except Exception as e:
            self.logger.error(f"Health assessment failed: {str(e)}")
            return {"status": "unknown", "score": 0, "error": str(e)}
    
    def _calculate_optimization_progress(self, objective_values: List[float],
                                       optimization_objective) -> Dict[str, Any]:
        """Calculate optimization progress for hyperparameter tuning."""
        if not objective_values:
            return {"no_data": True}
        
        if len(objective_values) < 2:
            return {"insufficient_data": True, "best_value": objective_values[0]}
        
        # Sort values based on optimization objective
        if optimization_objective.value == "maximize":
            best_value = max(objective_values)
            sorted_values = sorted(objective_values, reverse=True)
        else:
            best_value = min(objective_values)
            sorted_values = sorted(objective_values)
        
        # Calculate improvement over time
        improvements = []
        current_best = objective_values[0]
        
        for value in objective_values[1:]:
            if optimization_objective.value == "maximize":
                if value > current_best:
                    improvements.append(value - current_best)
                    current_best = value
                else:
                    improvements.append(0)
            else:
                if value < current_best:
                    improvements.append(current_best - value)
                    current_best = value
                else:
                    improvements.append(0)
        
        return {
            "best_value": best_value,
            "latest_value": objective_values[-1],
            "total_improvements": sum(improvements),
            "improvement_frequency": sum(1 for imp in improvements if imp > 0) / len(improvements),
            "values_tried": len(objective_values),
            "percentile_95": np.percentile(sorted_values, 95),
            "percentile_75": np.percentile(sorted_values, 75),
            "percentile_25": np.percentile(sorted_values, 25)
        }
    
    def _analyze_optimization_convergence(self, objective_values: List[float]) -> Dict[str, Any]:
        """Analyze convergence of optimization process."""
        if len(objective_values) < 10:
            return {"status": "insufficient_data"}
        
        # Check for convergence by looking at recent improvements
        recent_window = min(20, len(objective_values) // 4)
        recent_values = objective_values[-recent_window:]
        
        # Calculate variance in recent values
        recent_variance = np.var(recent_values)
        overall_variance = np.var(objective_values)
        
        convergence_ratio = recent_variance / overall_variance if overall_variance > 0 else 0
        
        if convergence_ratio < 0.1:
            status = "converged"
        elif convergence_ratio < 0.3:
            status = "converging"
        else:
            status = "exploring"
        
        return {
            "status": status,
            "convergence_ratio": convergence_ratio,
            "recent_variance": recent_variance,
            "overall_variance": overall_variance,
            "recommendation": self._get_convergence_recommendation(status)
        }
    
    def _get_convergence_recommendation(self, status: str) -> str:
        """Get recommendation based on convergence status."""
        recommendations = {
            "converged": "Consider stopping optimization or expanding search space",
            "converging": "Optimization is making good progress",
            "exploring": "Continue optimization, good exploration happening"
        }
        return recommendations.get(status, "Continue monitoring")
    
    def _estimate_tuning_completion(self, tuning_job, trials: List) -> Optional[str]:
        """Estimate hyperparameter tuning completion time."""
        try:
            if not tuning_job.start_time:
                return None
            
            completed_trials = len([t for t in trials if t.status == JobStatus.COMPLETED])
            total_trials = tuning_job.max_trials
            
            if completed_trials == 0:
                return None
            
            elapsed = datetime.utcnow() - tuning_job.start_time
            avg_trial_duration = elapsed.total_seconds() / completed_trials
            
            remaining_trials = total_trials - len(trials)
            parallel_trials = tuning_job.max_parallel_trials
            
            remaining_time_seconds = (remaining_trials / parallel_trials) * avg_trial_duration
            completion_time = datetime.utcnow() + timedelta(seconds=remaining_time_seconds)
            
            return completion_time.isoformat()
            
        except Exception as e:
            self.logger.error(f"Tuning completion estimation failed: {str(e)}")
            return None


class AlertManager:
    """Manages alerts and notifications for training monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AlertManager")
        self.alert_history = defaultdict(list)
    
    async def send_alert(self, training_job_id: str, alert_data: Dict[str, Any],
                       db: AsyncSession):
        """Send an alert for a training job."""
        try:
            alert = {
                "timestamp": datetime.utcnow().isoformat(),
                "training_job_id": training_job_id,
                "alert_type": alert_data["type"],
                "severity": alert_data["severity"],
                "message": alert_data["message"],
                "details": alert_data
            }
            
            # Store alert in history
            self.alert_history[training_job_id].append(alert)
            
            # Keep alert history manageable
            if len(self.alert_history[training_job_id]) > 100:
                self.alert_history[training_job_id] = self.alert_history[training_job_id][-50:]
            
            # In a real implementation, this would send notifications
            # via email, Slack, webhooks, etc.
            self.logger.warning(f"ALERT [{alert['severity'].upper()}] for job {training_job_id}: {alert['message']}")
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {str(e)}")
    
    def get_alert_history(self, training_job_id: str) -> List[Dict[str, Any]]:
        """Get alert history for a training job."""
        return self.alert_history.get(training_job_id, [])