"""
Vertex AI integration service for Phase 4: Model Training Orchestrator.
Manages ML model training jobs using Google Cloud Vertex AI platform.
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
import base64
import tempfile
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.training import (
    TrainingJob, JobStatus, InstanceType, ModelFramework,
    HyperparameterTuningJob, HyperparameterTrial, ModelArtifact
)
from app.core.config import get_settings


class VertexAIClient:
    """Client wrapper for Google Cloud Vertex AI APIs."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.VertexAIClient")
        self.settings = get_settings()
        
        # Configuration
        self.project_id = getattr(self.settings, 'VERTEX_AI_PROJECT_ID', 'alphintra-ml')
        self.region = getattr(self.settings, 'VERTEX_AI_REGION', 'us-central1')
        self.service_account = getattr(self.settings, 'VERTEX_AI_SERVICE_ACCOUNT', None)
        
        # Initialize client (would use actual Vertex AI SDK in production)
        self._initialized = False
        self._client = None
    
    async def initialize(self):
        """Initialize Vertex AI client."""
        try:
            if self._initialized:
                return True
            
            # In production, this would initialize the actual Vertex AI client
            # from google.cloud import aiplatform
            # aiplatform.init(
            #     project=self.project_id,
            #     location=self.region,
            #     service_account=self.service_account
            # )
            # self._client = aiplatform
            
            # For now, simulate initialization
            self._client = MockVertexAIClient()
            self._initialized = True
            
            self.logger.info(f"Initialized Vertex AI client for project {self.project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Vertex AI client: {str(e)}")
            return False
    
    async def create_training_job(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom training job in Vertex AI."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Prepare training job configuration
            training_config = {
                "display_name": job_config["job_name"],
                "training_task_definition": "gs://alphintra-ml/training-tasks/custom-training.yaml",
                "training_task_inputs": {
                    "args": job_config.get("args", []),
                    "command": job_config.get("command", ["python", "train.py"]),
                    "environment": {
                        "imageUri": job_config.get("container_image", "gcr.io/alphintra/ml-training:latest"),
                        "env": [
                            {"name": "JOB_ID", "value": job_config["job_id"]},
                            {"name": "DATASET_PATH", "value": job_config.get("dataset_path", "")},
                            {"name": "MODEL_CONFIG", "value": json.dumps(job_config.get("model_config", {}))},
                            {"name": "HYPERPARAMETERS", "value": json.dumps(job_config.get("hyperparameters", {}))}
                        ]
                    }
                },
                "worker_pool_specs": [
                    {
                        "machine_spec": {
                            "machine_type": self._get_vertex_machine_type(job_config["instance_type"]),
                            "accelerator_type": self._get_accelerator_type(job_config["instance_type"]),
                            "accelerator_count": self._get_accelerator_count(job_config["instance_type"])
                        },
                        "replica_count": job_config.get("replica_count", 1),
                        "disk_spec": {
                            "boot_disk_type": "pd-ssd",
                            "boot_disk_size_gb": job_config.get("disk_size", 100)
                        }
                    }
                ],
                "service_account": self.service_account,
                "network": f"projects/{self.project_id}/global/networks/default",
                "timeout": f"{job_config.get('timeout_hours', 24)}h",
                "restart_job_on_worker_restart": False,
                "tensorboard": f"projects/{self.project_id}/locations/{self.region}/tensorboards/default"
            }
            
            # Submit job to Vertex AI
            vertex_job = await self._client.create_custom_job(training_config)
            
            return {
                "success": True,
                "vertex_ai_job_id": vertex_job["name"],
                "job_state": vertex_job["state"],
                "create_time": vertex_job["createTime"],
                "training_config": training_config
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create Vertex AI training job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_hyperparameter_tuning_job(self, tuning_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a hyperparameter tuning job in Vertex AI."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Prepare hyperparameter tuning configuration
            hp_config = {
                "display_name": tuning_config["job_name"],
                "study_spec": {
                    "metrics": [
                        {
                            "metric_id": tuning_config["objective_metric"],
                            "goal": tuning_config["optimization_objective"].upper()
                        }
                    ],
                    "parameters": self._convert_parameter_space(tuning_config["parameter_space"]),
                    "algorithm": self._get_tuning_algorithm(tuning_config["optimization_algorithm"]),
                    "measurement_selection_type": "BEST_MEASUREMENT"
                },
                "max_trial_count": tuning_config.get("max_trials", 100),
                "parallel_trial_count": tuning_config.get("max_parallel_trials", 4),
                "max_failed_trial_count": tuning_config.get("max_failed_trials", 10),
                "trial_job_spec": {
                    "worker_pool_specs": [
                        {
                            "machine_spec": {
                                "machine_type": self._get_vertex_machine_type(tuning_config["instance_type"]),
                                "accelerator_type": self._get_accelerator_type(tuning_config["instance_type"]),
                                "accelerator_count": self._get_accelerator_count(tuning_config["instance_type"])
                            },
                            "replica_count": 1,
                            "container_spec": {
                                "image_uri": tuning_config.get("container_image", "gcr.io/alphintra/ml-training:latest"),
                                "command": tuning_config.get("command", ["python", "train.py"]),
                                "args": tuning_config.get("args", []),
                                "env": [
                                    {"name": "JOB_ID", "value": tuning_config["job_id"]},
                                    {"name": "DATASET_PATH", "value": tuning_config.get("dataset_path", "")},
                                    {"name": "AIP_MODEL_DIR", "value": f"gs://alphintra-ml/models/{tuning_config['job_id']}"}
                                ]
                            },
                            "disk_spec": {
                                "boot_disk_type": "pd-ssd",
                                "boot_disk_size_gb": tuning_config.get("disk_size", 100)
                            }
                        }
                    ],
                    "service_account": self.service_account,
                    "network": f"projects/{self.project_id}/global/networks/default",
                    "timeout": f"{tuning_config.get('max_trial_duration_hours', 4)}h"
                }
            }
            
            # Early stopping configuration
            if tuning_config.get("early_stopping_config"):
                hp_config["study_spec"]["study_stopping_config"] = {
                    "should_stop_asap": False,
                    "minimum_runtime_constraint": {"min_runtime": "300s"},
                    "max_duration_no_progress": "1800s"
                }
            
            # Submit hyperparameter tuning job
            vertex_job = await self._client.create_hyperparameter_tuning_job(hp_config)
            
            return {
                "success": True,
                "vertex_ai_job_id": vertex_job["name"],
                "job_state": vertex_job["state"],
                "create_time": vertex_job["createTime"],
                "tuning_config": hp_config
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create Vertex AI hyperparameter tuning job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_job_status(self, vertex_ai_job_id: str) -> Dict[str, Any]:
        """Get the status of a Vertex AI job."""
        try:
            job_details = await self._client.get_job(vertex_ai_job_id)
            
            return {
                "job_id": vertex_ai_job_id,
                "state": job_details["state"],
                "create_time": job_details["createTime"],
                "start_time": job_details.get("startTime"),
                "end_time": job_details.get("endTime"),
                "update_time": job_details["updateTime"],
                "error": job_details.get("error"),
                "labels": job_details.get("labels", {}),
                "training_task_metadata": job_details.get("trainingTaskMetadata", {})
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Vertex AI job status: {str(e)}")
            return {"error": str(e)}
    
    async def cancel_job(self, vertex_ai_job_id: str) -> Dict[str, Any]:
        """Cancel a Vertex AI job."""
        try:
            result = await self._client.cancel_job(vertex_ai_job_id)
            
            return {
                "success": True,
                "message": "Job cancellation requested",
                "job_id": vertex_ai_job_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to cancel Vertex AI job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_job_logs(self, vertex_ai_job_id: str, max_lines: int = 1000) -> Dict[str, Any]:
        """Get logs for a Vertex AI job."""
        try:
            logs = await self._client.get_job_logs(vertex_ai_job_id, max_lines)
            
            return {
                "job_id": vertex_ai_job_id,
                "logs": logs,
                "log_count": len(logs)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Vertex AI job logs: {str(e)}")
            return {"error": str(e)}
    
    async def get_hyperparameter_trials(self, vertex_ai_job_id: str) -> Dict[str, Any]:
        """Get hyperparameter trials for a tuning job."""
        try:
            trials = await self._client.get_hyperparameter_trials(vertex_ai_job_id)
            
            return {
                "job_id": vertex_ai_job_id,
                "trials": trials,
                "trial_count": len(trials)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get hyperparameter trials: {str(e)}")
            return {"error": str(e)}
    
    def _get_vertex_machine_type(self, instance_type: InstanceType) -> str:
        """Convert internal instance type to Vertex AI machine type."""
        mapping = {
            InstanceType.CPU_SMALL: "n1-standard-4",
            InstanceType.CPU_MEDIUM: "n1-standard-8",
            InstanceType.CPU_LARGE: "n1-standard-16",
            InstanceType.GPU_T4: "n1-standard-8",
            InstanceType.GPU_V100: "n1-standard-16",
            InstanceType.GPU_A100: "a2-highgpu-1g",
            InstanceType.TPU_V3: "cloud-tpu",
            InstanceType.TPU_V4: "cloud-tpu"
        }
        return mapping.get(instance_type, "n1-standard-4")
    
    def _get_accelerator_type(self, instance_type: InstanceType) -> Optional[str]:
        """Get accelerator type for instance."""
        mapping = {
            InstanceType.GPU_T4: "NVIDIA_TESLA_T4",
            InstanceType.GPU_V100: "NVIDIA_TESLA_V100",
            InstanceType.GPU_A100: "NVIDIA_TESLA_A100",
            InstanceType.TPU_V3: "TPU_V3",
            InstanceType.TPU_V4: "TPU_V4"
        }
        return mapping.get(instance_type)
    
    def _get_accelerator_count(self, instance_type: InstanceType) -> int:
        """Get accelerator count for instance."""
        gpu_types = [InstanceType.GPU_T4, InstanceType.GPU_V100, InstanceType.GPU_A100]
        tpu_types = [InstanceType.TPU_V3, InstanceType.TPU_V4]
        
        if instance_type in gpu_types:
            return 1
        elif instance_type in tpu_types:
            return 8  # TPU v3/v4 typically have 8 cores
        else:
            return 0
    
    def _convert_parameter_space(self, parameter_space: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert parameter space to Vertex AI format."""
        parameters = []
        
        for param_name, param_config in parameter_space.items():
            param_type = param_config.get("type", "double")
            
            if param_type == "double":
                parameters.append({
                    "parameter_id": param_name,
                    "double_value_spec": {
                        "min_value": param_config["min"],
                        "max_value": param_config["max"]
                    },
                    "scale_type": param_config.get("scale", "UNIT_LINEAR_SCALE").upper()
                })
            elif param_type == "integer":
                parameters.append({
                    "parameter_id": param_name,
                    "integer_value_spec": {
                        "min_value": param_config["min"],
                        "max_value": param_config["max"]
                    },
                    "scale_type": param_config.get("scale", "UNIT_LINEAR_SCALE").upper()
                })
            elif param_type == "categorical":
                parameters.append({
                    "parameter_id": param_name,
                    "categorical_value_spec": {
                        "values": param_config["values"]
                    }
                })
            elif param_type == "discrete":
                parameters.append({
                    "parameter_id": param_name,
                    "discrete_value_spec": {
                        "values": [float(v) for v in param_config["values"]]
                    }
                })
        
        return parameters
    
    def _get_tuning_algorithm(self, algorithm: str) -> str:
        """Convert optimization algorithm to Vertex AI format."""
        mapping = {
            "random_search": "RANDOM_SEARCH",
            "grid_search": "GRID_SEARCH",
            "bayesian_optimization": "GAUSSIAN_PROCESS_BANDIT",
            "hyperband": "RANDOM_SEARCH",  # Vertex AI doesn't have direct Hyperband
            "population_based": "RANDOM_SEARCH"
        }
        return mapping.get(algorithm, "RANDOM_SEARCH")


class MockVertexAIClient:
    """Mock Vertex AI client for development/testing."""
    
    def __init__(self):
        self.jobs = {}
        self.job_counter = 0
    
    async def create_custom_job(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock custom job creation."""
        self.job_counter += 1
        job_id = f"projects/alphintra-ml/locations/us-central1/customJobs/job-{self.job_counter}"
        
        job = {
            "name": job_id,
            "displayName": config["display_name"],
            "state": "JOB_STATE_RUNNING",
            "createTime": datetime.utcnow().isoformat() + "Z",
            "startTime": datetime.utcnow().isoformat() + "Z",
            "updateTime": datetime.utcnow().isoformat() + "Z",
            "jobSpec": config,
            "labels": {"created_by": "alphintra_ai_service"}
        }
        
        self.jobs[job_id] = job
        return job
    
    async def create_hyperparameter_tuning_job(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock hyperparameter tuning job creation."""
        self.job_counter += 1
        job_id = f"projects/alphintra-ml/locations/us-central1/hyperparameterTuningJobs/hp-job-{self.job_counter}"
        
        job = {
            "name": job_id,
            "displayName": config["display_name"],
            "state": "JOB_STATE_RUNNING",
            "createTime": datetime.utcnow().isoformat() + "Z",
            "startTime": datetime.utcnow().isoformat() + "Z",
            "updateTime": datetime.utcnow().isoformat() + "Z",
            "studySpec": config["study_spec"],
            "maxTrialCount": config["max_trial_count"],
            "parallelTrialCount": config["parallel_trial_count"],
            "labels": {"created_by": "alphintra_ai_service"}
        }
        
        self.jobs[job_id] = job
        return job
    
    async def get_job(self, job_id: str) -> Dict[str, Any]:
        """Mock get job status."""
        if job_id in self.jobs:
            return self.jobs[job_id]
        else:
            raise Exception(f"Job {job_id} not found")
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Mock job cancellation."""
        if job_id in self.jobs:
            self.jobs[job_id]["state"] = "JOB_STATE_CANCELLED"
            self.jobs[job_id]["endTime"] = datetime.utcnow().isoformat() + "Z"
            return {"success": True}
        else:
            raise Exception(f"Job {job_id} not found")
    
    async def get_job_logs(self, job_id: str, max_lines: int = 1000) -> List[str]:
        """Mock job logs."""
        return [
            f"[{datetime.utcnow().isoformat()}] Training started for job {job_id}",
            f"[{datetime.utcnow().isoformat()}] Loading dataset...",
            f"[{datetime.utcnow().isoformat()}] Model initialization complete",
            f"[{datetime.utcnow().isoformat()}] Epoch 1/10 - loss: 0.8743, accuracy: 0.6251",
            f"[{datetime.utcnow().isoformat()}] Epoch 2/10 - loss: 0.7854, accuracy: 0.7102"
        ]
    
    async def get_hyperparameter_trials(self, job_id: str) -> List[Dict[str, Any]]:
        """Mock hyperparameter trials."""
        return [
            {
                "id": "1",
                "state": "COMPLETED",
                "parameters": [
                    {"parameter_id": "learning_rate", "value": 0.001},
                    {"parameter_id": "batch_size", "value": 32}
                ],
                "final_measurement": {
                    "metrics": [
                        {"metric_id": "accuracy", "value": 0.85}
                    ]
                }
            },
            {
                "id": "2", 
                "state": "COMPLETED",
                "parameters": [
                    {"parameter_id": "learning_rate", "value": 0.01},
                    {"parameter_id": "batch_size", "value": 64}
                ],
                "final_measurement": {
                    "metrics": [
                        {"metric_id": "accuracy", "value": 0.82}
                    ]
                }
            }
        ]


class VertexAIIntegrationService:
    """Main service for integrating with Vertex AI."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vertex_client = VertexAIClient()
        self.settings = get_settings()
    
    async def submit_training_job(self, training_job: TrainingJob, 
                                dataset_path: str, db: AsyncSession) -> Dict[str, Any]:
        """Submit a training job to Vertex AI."""
        try:
            # Prepare job configuration
            job_config = {
                "job_id": str(training_job.id),
                "job_name": f"training-{training_job.job_name}-{training_job.id}",
                "instance_type": training_job.instance_type,
                "dataset_path": dataset_path,
                "model_config": training_job.model_config,
                "hyperparameters": training_job.hyperparameters,
                "training_config": training_job.training_config,
                "disk_size": training_job.disk_size,
                "timeout_hours": training_job.timeout_hours,
                "container_image": self._get_container_image(training_job),
                "command": self._get_training_command(training_job),
                "args": self._get_training_args(training_job)
            }
            
            # Submit to Vertex AI
            result = await self.vertex_client.create_training_job(job_config)
            
            if result["success"]:
                # Update training job with Vertex AI details
                training_job.vertex_ai_job_id = result["vertex_ai_job_id"]
                training_job.status = JobStatus.RUNNING
                training_job.start_time = datetime.utcnow()
                
                await db.commit()
                
                self.logger.info(f"Submitted training job {training_job.id} to Vertex AI")
                
                return {
                    "success": True,
                    "vertex_ai_job_id": result["vertex_ai_job_id"],
                    "message": "Training job submitted to Vertex AI"
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to submit training job to Vertex AI: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def submit_hyperparameter_tuning_job(self, tuning_job: HyperparameterTuningJob,
                                             dataset_path: str, db: AsyncSession) -> Dict[str, Any]:
        """Submit a hyperparameter tuning job to Vertex AI."""
        try:
            # Prepare tuning configuration
            tuning_config = {
                "job_id": str(tuning_job.id),
                "job_name": f"hp-tuning-{tuning_job.job_name}-{tuning_job.id}",
                "instance_type": tuning_job.instance_type,
                "dataset_path": dataset_path,
                "parameter_space": tuning_job.parameter_space,
                "optimization_algorithm": tuning_job.optimization_algorithm.value,
                "optimization_objective": tuning_job.optimization_objective.value,
                "objective_metric": tuning_job.objective_metric,
                "max_trials": tuning_job.max_trials,
                "max_parallel_trials": tuning_job.max_parallel_trials,
                "max_trial_duration_hours": tuning_job.max_trial_duration_hours,
                "early_stopping_config": tuning_job.early_stopping_config,
                "container_image": self._get_container_image_for_tuning(tuning_job),
                "command": self._get_tuning_command(tuning_job),
                "args": self._get_tuning_args(tuning_job)
            }
            
            # Submit to Vertex AI
            result = await self.vertex_client.create_hyperparameter_tuning_job(tuning_config)
            
            if result["success"]:
                # Update tuning job with Vertex AI details
                tuning_job.vertex_ai_job_id = result["vertex_ai_job_id"]
                tuning_job.status = JobStatus.RUNNING
                tuning_job.start_time = datetime.utcnow()
                
                await db.commit()
                
                self.logger.info(f"Submitted hyperparameter tuning job {tuning_job.id} to Vertex AI")
                
                return {
                    "success": True,
                    "vertex_ai_job_id": result["vertex_ai_job_id"],
                    "message": "Hyperparameter tuning job submitted to Vertex AI"
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to submit hyperparameter tuning job to Vertex AI: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def sync_job_status(self, training_job: TrainingJob, db: AsyncSession) -> Dict[str, Any]:
        """Sync training job status with Vertex AI."""
        try:
            if not training_job.vertex_ai_job_id:
                return {"success": False, "error": "No Vertex AI job ID found"}
            
            # Get status from Vertex AI
            status_result = await self.vertex_client.get_job_status(training_job.vertex_ai_job_id)
            
            if "error" in status_result:
                return {"success": False, "error": status_result["error"]}
            
            # Map Vertex AI state to our job status
            vertex_state = status_result["state"]
            new_status = self._map_vertex_state_to_job_status(vertex_state)
            
            # Update job if status changed
            if training_job.status != new_status:
                training_job.status = new_status
                
                # Set end time if job completed
                if new_status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    if status_result.get("end_time"):
                        training_job.end_time = datetime.fromisoformat(
                            status_result["end_time"].replace("Z", "+00:00")
                        )
                    else:
                        training_job.end_time = datetime.utcnow()
                    
                    # Calculate duration
                    if training_job.start_time:
                        duration = training_job.end_time - training_job.start_time
                        training_job.duration_seconds = int(duration.total_seconds())
                
                # Handle errors
                if new_status == JobStatus.FAILED and status_result.get("error"):
                    training_job.error_message = str(status_result["error"])
                
                await db.commit()
                
                self.logger.info(f"Updated job {training_job.id} status to {new_status.value}")
            
            return {
                "success": True,
                "vertex_state": vertex_state,
                "job_status": new_status.value,
                "status_changed": training_job.status != new_status
            }
            
        except Exception as e:
            self.logger.error(f"Failed to sync job status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_job_logs(self, training_job: TrainingJob) -> Dict[str, Any]:
        """Get training job logs from Vertex AI."""
        try:
            if not training_job.vertex_ai_job_id:
                return {"error": "No Vertex AI job ID found"}
            
            logs_result = await self.vertex_client.get_job_logs(training_job.vertex_ai_job_id)
            
            if "error" in logs_result:
                return logs_result
            
            # Update training logs in job record
            if logs_result.get("logs"):
                if training_job.training_logs is None:
                    training_job.training_logs = []
                
                # Add new logs (avoid duplicates)
                existing_logs = set(training_job.training_logs)
                new_logs = [log for log in logs_result["logs"] if log not in existing_logs]
                training_job.training_logs.extend(new_logs)
            
            return logs_result
            
        except Exception as e:
            self.logger.error(f"Failed to get job logs: {str(e)}")
            return {"error": str(e)}
    
    async def cancel_job(self, training_job: TrainingJob, db: AsyncSession) -> Dict[str, Any]:
        """Cancel a training job in Vertex AI."""
        try:
            if not training_job.vertex_ai_job_id:
                return {"success": False, "error": "No Vertex AI job ID found"}
            
            # Cancel in Vertex AI
            result = await self.vertex_client.cancel_job(training_job.vertex_ai_job_id)
            
            if result["success"]:
                # Update job status
                training_job.status = JobStatus.CANCELLED
                training_job.end_time = datetime.utcnow()
                
                if training_job.start_time:
                    duration = training_job.end_time - training_job.start_time
                    training_job.duration_seconds = int(duration.total_seconds())
                
                await db.commit()
                
                self.logger.info(f"Cancelled training job {training_job.id} in Vertex AI")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to cancel job in Vertex AI: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def sync_hyperparameter_trials(self, tuning_job: HyperparameterTuningJob,
                                       db: AsyncSession) -> Dict[str, Any]:
        """Sync hyperparameter trials from Vertex AI."""
        try:
            if not tuning_job.vertex_ai_job_id:
                return {"success": False, "error": "No Vertex AI job ID found"}
            
            # Get trials from Vertex AI
            trials_result = await self.vertex_client.get_hyperparameter_trials(tuning_job.vertex_ai_job_id)
            
            if "error" in trials_result:
                return trials_result
            
            # Process trials
            synced_trials = 0
            for trial_data in trials_result.get("trials", []):
                trial_id = trial_data["id"]
                
                # Check if trial already exists
                result = await db.execute(
                    select(HyperparameterTrial)
                    .where(
                        and_(
                            HyperparameterTrial.tuning_job_id == tuning_job.id,
                            HyperparameterTrial.vertex_ai_trial_id == trial_id
                        )
                    )
                )
                existing_trial = result.scalar_one_or_none()
                
                if not existing_trial:
                    # Create new trial
                    trial = HyperparameterTrial(
                        id=uuid4(),
                        tuning_job_id=tuning_job.id,
                        vertex_ai_trial_id=trial_id,
                        trial_number=int(trial_id),
                        hyperparameters=self._convert_vertex_parameters(trial_data.get("parameters", [])),
                        status=self._map_vertex_state_to_job_status(trial_data["state"]),
                        start_time=datetime.utcnow(),  # Would parse from trial_data if available
                        end_time=datetime.utcnow() if trial_data["state"] in ["COMPLETED", "FAILED"] else None
                    )
                    
                    # Extract objective value
                    if trial_data.get("final_measurement"):
                        metrics = trial_data["final_measurement"].get("metrics", [])
                        for metric in metrics:
                            if metric["metric_id"] == tuning_job.objective_metric:
                                trial.objective_value = metric["value"]
                                trial.objective_metric = metric["metric_id"]
                                break
                    
                    db.add(trial)
                    synced_trials += 1
                else:
                    # Update existing trial
                    existing_trial.status = self._map_vertex_state_to_job_status(trial_data["state"])
                    if trial_data.get("final_measurement"):
                        metrics = trial_data["final_measurement"].get("metrics", [])
                        for metric in metrics:
                            if metric["metric_id"] == tuning_job.objective_metric:
                                existing_trial.objective_value = metric["value"]
                                existing_trial.objective_metric = metric["metric_id"]
                                break
            
            await db.commit()
            
            # Update tuning job completed trials count
            tuning_job.completed_trials = len([t for t in trials_result.get("trials", []) 
                                             if t["state"] == "COMPLETED"])
            await db.commit()
            
            return {
                "success": True,
                "synced_trials": synced_trials,
                "total_trials": len(trials_result.get("trials", []))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to sync hyperparameter trials: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_container_image(self, training_job: TrainingJob) -> str:
        """Get appropriate container image for training job."""
        # Framework-specific containers
        framework_images = {
            ModelFramework.TENSORFLOW: "gcr.io/alphintra/tensorflow-training:latest",
            ModelFramework.PYTORCH: "gcr.io/alphintra/pytorch-training:latest",
            ModelFramework.SKLEARN: "gcr.io/alphintra/sklearn-training:latest",
            ModelFramework.XGBOOST: "gcr.io/alphintra/xgboost-training:latest",
            ModelFramework.LIGHTGBM: "gcr.io/alphintra/lightgbm-training:latest",
            ModelFramework.CATBOOST: "gcr.io/alphintra/catboost-training:latest",
            ModelFramework.KERAS: "gcr.io/alphintra/tensorflow-training:latest",
            ModelFramework.CUSTOM: "gcr.io/alphintra/custom-training:latest"
        }
        
        # Extract framework from model config or use default
        framework = training_job.model_config.get("framework", ModelFramework.TENSORFLOW)
        if isinstance(framework, str):
            framework = ModelFramework(framework)
        
        return framework_images.get(framework, "gcr.io/alphintra/ml-training:latest")
    
    def _get_container_image_for_tuning(self, tuning_job: HyperparameterTuningJob) -> str:
        """Get container image for hyperparameter tuning."""
        return "gcr.io/alphintra/hp-tuning:latest"
    
    def _get_training_command(self, training_job: TrainingJob) -> List[str]:
        """Get training command based on job configuration."""
        return ["python", "train.py"]
    
    def _get_training_args(self, training_job: TrainingJob) -> List[str]:
        """Get training arguments."""
        args = [
            "--job-id", str(training_job.id),
            "--strategy-id", str(training_job.strategy_id),
            "--dataset-id", str(training_job.dataset_id)
        ]
        
        # Add hyperparameters as arguments
        for key, value in training_job.hyperparameters.items():
            args.extend([f"--{key}", str(value)])
        
        return args
    
    def _get_tuning_command(self, tuning_job: HyperparameterTuningJob) -> List[str]:
        """Get hyperparameter tuning command."""
        return ["python", "tune.py"]
    
    def _get_tuning_args(self, tuning_job: HyperparameterTuningJob) -> List[str]:
        """Get hyperparameter tuning arguments."""
        return [
            "--tuning-job-id", str(tuning_job.id),
            "--strategy-id", str(tuning_job.strategy_id),
            "--dataset-id", str(tuning_job.dataset_id),
            "--objective-metric", tuning_job.objective_metric
        ]
    
    def _map_vertex_state_to_job_status(self, vertex_state: str) -> JobStatus:
        """Map Vertex AI job state to our job status."""
        mapping = {
            "JOB_STATE_QUEUED": JobStatus.QUEUED,
            "JOB_STATE_PENDING": JobStatus.PENDING,
            "JOB_STATE_RUNNING": JobStatus.RUNNING,
            "JOB_STATE_SUCCEEDED": JobStatus.COMPLETED,
            "JOB_STATE_FAILED": JobStatus.FAILED,
            "JOB_STATE_CANCELLING": JobStatus.RUNNING,
            "JOB_STATE_CANCELLED": JobStatus.CANCELLED,
            "JOB_STATE_PAUSED": JobStatus.PENDING,
            "JOB_STATE_EXPIRED": JobStatus.TIMEOUT
        }
        return mapping.get(vertex_state, JobStatus.RUNNING)
    
    def _convert_vertex_parameters(self, vertex_parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert Vertex AI parameters to our format."""
        parameters = {}
        for param in vertex_parameters:
            param_id = param["parameter_id"]
            value = param.get("value", param.get("double_value", param.get("int_value", param.get("string_value"))))
            parameters[param_id] = value
        return parameters