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
import subprocess
import shutil
import venv

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
            
            # For local development, we use the LocalTrainingClient
            self.logger.info("Using LocalTrainingClient for development.")
            self._client = LocalTrainingClient()
            self._initialized = True
            
            self.logger.info(f"Initialized Local Training Client")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize training client: {str(e)}")
            return False
    
    async def create_training_job(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom training job."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # In a real scenario, this would be a more complex mapping.
            # For local training, we pass a simplified config.
            local_job_config = {
                "display_name": job_config["job_name"],
                "command": job_config.get("command", ["python", "train.py"]),
                "args": job_config.get("args", [])
            }

            # Submit job to the local client
            local_job = await self._client.create_custom_job(local_job_config)
            
            return {
                "success": True,
                "vertex_ai_job_id": local_job["name"],
                "job_state": local_job["state"],
                "create_time": local_job["createTime"],
                "training_config": job_config # Return original config for reference
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create local training job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_hyperparameter_tuning_job(self, tuning_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a hyperparameter tuning job."""
        self.logger.warning("Hyperparameter tuning is not fully implemented for local training. Submitting a single training job instead.")
        # Simplify by submitting a single trial job
        trial_job_spec = tuning_config.get("trial_job_spec", {})
        return await self.create_training_job(trial_job_spec)

    async def get_job_status(self, vertex_ai_job_id: str) -> Dict[str, Any]:
        """Get the status of a job."""
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
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get job status: {str(e)}")
            return {"error": str(e)}
    
    async def cancel_job(self, vertex_ai_job_id: str) -> Dict[str, Any]:
        """Cancel a job."""
        try:
            result = await self._client.cancel_job(vertex_ai_job_id)
            
            return {
                "success": True,
                "message": "Job cancellation requested",
                "job_id": vertex_ai_job_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to cancel job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_job_logs(self, vertex_ai_job_id: str, max_lines: int = 1000) -> Dict[str, Any]:
        """Get logs for a job."""
        try:
            logs = await self._client.get_job_logs(vertex_ai_job_id, max_lines)
            
            return {
                "job_id": vertex_ai_job_id,
                "logs": logs,
                "log_count": len(logs)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get job logs: {str(e)}")
            return {"error": str(e)}
    
    async def get_hyperparameter_trials(self, vertex_ai_job_id: str) -> Dict[str, Any]:
        """Get hyperparameter trials for a tuning job."""
        self.logger.warning("Hyperparameter tuning is not implemented for local training.")
        return {"job_id": vertex_ai_job_id, "trials": [], "trial_count": 0}
    

class LocalTrainingClient:
    """
    A client that simulates Vertex AI by running training jobs as local subprocesses
    in isolated virtual environments.
    """
    
    def __init__(self):
        self.jobs = {}
        self.job_counter = 0
        self.logger = logging.getLogger(f"{__name__}.LocalTrainingClient")
        self.workspace_dir = "/tmp/local_training_runs"
        self.template_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "local_training_workspace", "sample_strategy")
        )
        os.makedirs(self.workspace_dir, exist_ok=True)
    
    async def create_custom_job(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Creates and runs a local training job in a dedicated venv."""
        self.job_counter += 1
        job_id = f"local-job-{self.job_counter}"
        job_dir = os.path.join(self.workspace_dir, job_id)
        
        try:
            # 1. Setup job directory from template
            self.logger.info(f"[{job_id}] Setting up job directory at {job_dir}")
            shutil.copytree(self.template_dir, job_dir)

            # 2. Create virtual environment
            self.logger.info(f"[{job_id}] Creating virtual environment...")
            venv_dir = os.path.join(job_dir, "venv")
            venv.create(venv_dir, with_pip=True)

            # 3. Install dependencies
            self.logger.info(f"[{job_id}] Installing dependencies from requirements.txt...")
            pip_executable = os.path.join(venv_dir, "bin", "pip")
            requirements_path = os.path.join(job_dir, "requirements.txt")
            install_process = subprocess.run(
                [pip_executable, "install", "-r", requirements_path],
                capture_output=True, text=True
            )
            if install_process.returncode != 0:
                self.logger.error(f"[{job_id}] Failed to install dependencies: {install_process.stderr}")
                raise Exception("Dependency installation failed.")
            self.logger.info(f"[{job_id}] Dependencies installed.")

            # 4. Start the training script
            self.logger.info(f"[{job_id}] Starting training script...")
            python_executable = os.path.join(venv_dir, "bin", "python")
            command = [python_executable] + config["command"] + config["args"]
            log_path = os.path.join(job_dir, "training.log")
            
            process = subprocess.Popen(
                command,
                stdout=open(log_path, 'w'),
                stderr=subprocess.STDOUT,
                cwd=job_dir # Run from the job's directory
            )

            job = {
                "name": job_id,
                "displayName": config["display_name"],
                "state": "JOB_STATE_RUNNING",
                "createTime": datetime.utcnow().isoformat() + "Z",
                "startTime": datetime.utcnow().isoformat() + "Z",
                "updateTime": datetime.utcnow().isoformat() + "Z",
                "process": process,
                "log_path": log_path,
                "job_dir": job_dir,
                "error": None
            }
            
            self.jobs[job_id] = job
            self.logger.info(f"[{job_id}] Local training job started with PID {process.pid}")
            return job

        except Exception as e:
            self.logger.error(f"[{job_id}] Failed to create job: {e}")
            # Clean up failed job directory
            if os.path.exists(job_dir):
                shutil.rmtree(job_dir)
            raise

    async def get_job(self, job_id: str) -> Dict[str, Any]:
        """Gets the status of a local job by checking its subprocess."""
        if job_id not in self.jobs:
            raise Exception(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        process = job["process"]
        
        if process.poll() is None:
            job["state"] = "JOB_STATE_RUNNING"
        else:
            if job["state"] not in ["JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]:
                if process.returncode == 0:
                    job["state"] = "JOB_STATE_SUCCEEDED"
                else:
                    job["state"] = "JOB_STATE_FAILED"
                    job["error"] = "Process exited with non-zero code."
                job["endTime"] = datetime.fromtimestamp(os.path.getmtime(job["log_path"])).isoformat() + "Z"
            
        job["updateTime"] = datetime.utcnow().isoformat() + "Z"
        return job

    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancels a local job by terminating its subprocess."""
        if job_id not in self.jobs:
            raise Exception(f"Job {job_id} not found")
            
        job = self.jobs[job_id]
        process = job["process"]

        if process.poll() is None:
            self.logger.info(f"[{job_id}] Terminating process with PID {process.pid}")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.logger.warning(f"[{job_id}] Process did not terminate gracefully, killing.")
                process.kill()

        job["state"] = "JOB_STATE_CANCELLED"
        job["endTime"] = datetime.utcnow().isoformat() + "Z"
        self.logger.info(f"[{job_id}] Job cancelled.")
        return {"success": True}

    async def get_job_logs(self, job_id: str, max_lines: int = 1000) -> List[str]:
        """Reads logs from the local log file for a job."""
        if job_id not in self.jobs:
            raise Exception(f"Job {job_id} not found")
            
        log_path = self.jobs[job_id]["log_path"]
        
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
            return [line.strip() for line in lines[-max_lines:]]
        except FileNotFoundError:
            return [f"Log file not found at {log_path}"]
        except Exception as e:
            self.logger.error(f"Error reading log file for job {job_id}: {e}")
            return [f"Error reading logs: {e}"]


class VertexAIIntegrationService:
    """Main service for integrating with Vertex AI."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vertex_client = VertexAIClient()
        self.settings = get_settings()
    
    async def submit_training_job(self, training_job: TrainingJob, 
                                dataset_path: str, db: AsyncSession) -> Dict[str, Any]:
        """Submit a training job."""
        try:
            # Prepare job configuration
            job_config = {
                "job_id": str(training_job.id),
                "job_name": f"training-{training_job.job_name}-{training_job.id}",
                "command": self._get_training_command(training_job),
                "args": self._get_training_args(training_job)
            }
            
            # Submit to the client (local or cloud)
            result = await self.vertex_client.create_training_job(job_config)
            
            if result.get("success"):
                # Update training job with job details
                training_job.vertex_ai_job_id = result["vertex_ai_job_id"]
                training_job.status = JobStatus.RUNNING
                training_job.start_time = datetime.utcnow()
                
                await db.commit()
                
                self.logger.info(f"Submitted training job {training_job.id} with backend job ID {result['vertex_ai_job_id']}")
                
                return {
                    "success": True,
                    "vertex_ai_job_id": result["vertex_ai_job_id"],
                    "message": "Training job submitted successfully"
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to submit training job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def submit_hyperparameter_tuning_job(self, tuning_job: HyperparameterTuningJob,
                                             dataset_path: str, db: AsyncSession) -> Dict[str, Any]:
        """Submit a hyperparameter tuning job."""
        try:
            # Prepare tuning configuration
            tuning_config = {
                "job_id": str(tuning_job.id),
                "job_name": f"hp-tuning-{tuning_job.job_name}-{tuning_job.id}",
                "trial_job_spec": {
                     "command": self._get_tuning_command(tuning_job),
                     "args": self._get_tuning_args(tuning_job)
                }
            }
            
            # Submit to the client
            result = await self.vertex_client.create_hyperparameter_tuning_job(tuning_config)
            
            if result.get("success"):
                # Update tuning job with job details
                tuning_job.vertex_ai_job_id = result["vertex_ai_job_id"]
                tuning_job.status = JobStatus.RUNNING
                tuning_job.start_time = datetime.utcnow()
                
                await db.commit()
                
                self.logger.info(f"Submitted hyperparameter tuning job {tuning_job.id} with backend job ID {result['vertex_ai_job_id']}")
                
                return {
                    "success": True,
                    "vertex_ai_job_id": result["vertex_ai_job_id"],
                    "message": "Hyperparameter tuning job submitted successfully"
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to submit hyperparameter tuning job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def sync_job_status(self, training_job: TrainingJob, db: AsyncSession) -> Dict[str, Any]:
        """Sync training job status with the backend."""
        try:
            if not training_job.vertex_ai_job_id:
                return {"success": False, "error": "No backend job ID found"}
            
            # Get status from the client
            status_result = await self.vertex_client.get_job_status(training_job.vertex_ai_job_id)
            
            if "error" in status_result:
                return {"success": False, "error": status_result["error"]}
            
            # Map backend state to our job status
            backend_state = status_result["state"]
            new_status = self._map_backend_state_to_job_status(backend_state)
            
            # Update job if status changed
            if training_job.status != new_status:
                training_job.status = new_status
                
                if new_status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    if status_result.get("end_time"):
                        training_job.end_time = datetime.fromisoformat(
                            status_result["end_time"].replace("Z", "+00:00")
                        )
                    else:
                        training_job.end_time = datetime.utcnow()
                    
                    if training_job.start_time:
                        duration = training_job.end_time - training_job.start_time
                        training_job.duration_seconds = int(duration.total_seconds())
                
                if new_status == JobStatus.FAILED and status_result.get("error"):
                    training_job.error_message = str(status_result["error"])
                
                await db.commit()
                
                self.logger.info(f"Updated job {training_job.id} status to {new_status.value}")
            
            return {
                "success": True,
                "backend_state": backend_state,
                "job_status": new_status.value,
                "status_changed": training_job.status != new_status
            }
            
        except Exception as e:
            self.logger.error(f"Failed to sync job status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_job_logs(self, training_job: TrainingJob) -> Dict[str, Any]:
        """Get training job logs from the backend."""
        try:
            if not training_job.vertex_ai_job_id:
                return {"error": "No backend job ID found"}
            
            logs_result = await self.vertex_client.get_job_logs(training_job.vertex_ai_job_id)
            
            if "error" in logs_result:
                return logs_result
            
            if logs_result.get("logs"):
                if training_job.training_logs is None:
                    training_job.training_logs = []
                
                existing_logs = set(training_job.training_logs)
                new_logs = [log for log in logs_result["logs"] if log not in existing_logs]
                training_job.training_logs.extend(new_logs)
            
            return logs_result
            
        except Exception as e:
            self.logger.error(f"Failed to get job logs: {str(e)}")
            return {"error": str(e)}
    
    async def cancel_job(self, training_job: TrainingJob, db: AsyncSession) -> Dict[str, Any]:
        """Cancel a training job in the backend."""
        try:
            if not training_job.vertex_ai_job_id:
                return {"success": False, "error": "No backend job ID found"}
            
            result = await self.vertex_client.cancel_job(training_job.vertex_ai_job_id)
            
            if result["success"]:
                training_job.status = JobStatus.CANCELLED
                training_job.end_time = datetime.utcnow()
                
                if training_job.start_time:
                    duration = training_job.end_time - training_job.start_time
                    training_job.duration_seconds = int(duration.total_seconds())
                
                await db.commit()
                
                self.logger.info(f"Cancelled training job {training_job.id} in backend")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to cancel job in backend: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def sync_hyperparameter_trials(self, tuning_job: HyperparameterTuningJob,
                                       db: AsyncSession) -> Dict[str, Any]:
        """Sync hyperparameter trials from the backend."""
        self.logger.warning("Hyperparameter tuning is not fully implemented for local training.")
        return {"success": True, "synced_trials": 0, "total_trials": 0}
    
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
        
        for key, value in training_job.hyperparameters.items():
            args.extend([f"--{key}", str(value)])
        
        return args
    
    def _get_tuning_command(self, tuning_job: HyperparameterTuningJob) -> List[str]:
        """Get hyperparameter tuning command."""
        return ["python", "train.py"] # Fallback to train.py for now
    
    def _get_tuning_args(self, tuning_job: HyperparameterTuningJob) -> List[str]:
        """Get hyperparameter tuning arguments."""
        return [
            "--job-id", str(tuning_job.id),
            "--strategy-id", str(tuning_job.strategy_id),
            "--dataset-id", str(tuning_job.dataset_id),
        ]
    
    def _map_backend_state_to_job_status(self, backend_state: str) -> JobStatus:
        """Map backend job state to our job status."""
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
        return mapping.get(backend_state, JobStatus.RUNNING)
    
    def _convert_vertex_parameters(self, vertex_parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert Vertex AI parameters to our format."""
        parameters = {}
        for param in vertex_parameters:
            param_id = param["parameter_id"]
            value = param.get("value", param.get("double_value", param.get("int_value", param.get("string_value"))))
            parameters[param_id] = value
        return parameters
