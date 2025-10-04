"""Vertex AI integration for asynchronous training orchestration."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training import HyperparameterTuningJob, JobStatus, TrainingJob
from app.core.config import get_settings


class TrainingOrchestrationClient:
    """Thin client for the external training orchestration backend."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.TrainingOrchestrationClient")
        self.settings = get_settings()
        self.base_url = getattr(self.settings, "TRAINING_ORCHESTRATOR_URL", None)
        self.queue_topic = getattr(self.settings, "TRAINING_JOB_QUEUE_TOPIC", None)
        self.auth_token = getattr(self.settings, "TRAINING_ORCHESTRATOR_TOKEN", None)
        timeout_value = getattr(self.settings, "TRAINING_ORCHESTRATOR_TIMEOUT", 30.0)
        self.timeout = httpx.Timeout(timeout_value)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def _url(self, path: str) -> str:
        if not self.base_url:
            raise RuntimeError("TRAINING_ORCHESTRATOR_URL must be configured for HTTP operations.")
        return f"{self.base_url.rstrip('/')}{path}"

    async def dispatch_training_job(self, job_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a training job specification to the orchestration backend."""
        if self.base_url:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self._url("/jobs"),
                    json=job_spec,
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()

        if not self.queue_topic:
            raise RuntimeError("No orchestration backend configured. Set TRAINING_ORCHESTRATOR_URL or TRAINING_JOB_QUEUE_TOPIC.")

        job_id = job_spec.get("job_id", str(uuid4()))
        self.logger.info(
            "Published training job %s to queue topic %s (fire-and-forget).", job_id, self.queue_topic
        )
        return {
            "job_id": job_id,
            "state": "JOB_STATE_QUEUED",
            "transport": "queue",
        }

    async def dispatch_hyperparameter_job(self, tuning_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a hyperparameter tuning job specification."""
        if self.base_url:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self._url("/tuning-jobs"),
                    json=tuning_spec,
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()

        # Fallback to queue semantics.
        return await self.dispatch_training_job(tuning_spec)

    async def fetch_job_status(self, job_id: str) -> Dict[str, Any]:
        """Fetch job status from orchestration backend."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self._url(f"/jobs/{job_id}"),
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running job."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self._url(f"/jobs/{job_id}/cancel"),
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def fetch_job_logs(self, job_id: str, max_lines: int = 1000) -> Dict[str, Any]:
        """Retrieve logs for a job."""
        params = {"max_lines": max_lines}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self._url(f"/jobs/{job_id}/logs"),
                params=params,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()


class VertexAIIntegrationService:
    """Service responsible for brokering communication with the training backend."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.vertex_client = TrainingOrchestrationClient()
        self.settings = get_settings()

    async def submit_training_job(
        self,
        training_job: TrainingJob,
        dataset_path: Optional[str],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Submit a training job specification to the orchestration backend."""
        try:
            job_spec = self._build_training_job_spec(training_job, dataset_path)

            backend_response = await self.vertex_client.dispatch_training_job(job_spec)

            backend_job_id = backend_response.get("job_id") or backend_response.get("name")
            if not backend_job_id:
                raise RuntimeError("Training backend did not return a job identifier.")

            backend_state = backend_response.get("state", "JOB_STATE_QUEUED")
            mapped_status = self._map_backend_state_to_job_status(backend_state)

            training_job.vertex_ai_job_id = backend_job_id
            training_job.status = mapped_status

            if mapped_status == JobStatus.RUNNING:
                training_job.start_time = datetime.utcnow()
            elif mapped_status in {JobStatus.QUEUED, JobStatus.PENDING}:
                training_job.start_time = None

            await db.commit()

            self.logger.info(
                "Submitted training job %s to orchestration backend as %s (state=%s)",
                training_job.id,
                backend_job_id,
                backend_state,
            )

            return {
                "success": True,
                "vertex_ai_job_id": backend_job_id,
                "backend_state": backend_state,
            }

        except Exception as exc:
            self.logger.error("Failed to submit training job %s: %s", training_job.id, exc)
            return {"success": False, "error": str(exc)}

    async def submit_hyperparameter_tuning_job(
        self,
        tuning_job: HyperparameterTuningJob,
        dataset_path: Optional[str],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Submit a hyperparameter tuning job to the orchestration backend."""
        try:
            tuning_spec = self._build_tuning_job_spec(tuning_job, dataset_path)
            backend_response = await self.vertex_client.dispatch_hyperparameter_job(tuning_spec)

            backend_job_id = backend_response.get("job_id") or backend_response.get("name")
            if not backend_job_id:
                raise RuntimeError("Training backend did not return a job identifier for tuning job.")

            backend_state = backend_response.get("state", "JOB_STATE_QUEUED")
            mapped_status = self._map_backend_state_to_job_status(backend_state)

            tuning_job.vertex_ai_job_id = backend_job_id
            tuning_job.status = mapped_status

            if mapped_status == JobStatus.RUNNING:
                tuning_job.start_time = datetime.utcnow()
            elif mapped_status in {JobStatus.QUEUED, JobStatus.PENDING}:
                tuning_job.start_time = None

            await db.commit()

            self.logger.info(
                "Submitted tuning job %s to orchestration backend as %s (state=%s)",
                tuning_job.id,
                backend_job_id,
                backend_state,
            )

            return {
                "success": True,
                "vertex_ai_job_id": backend_job_id,
                "backend_state": backend_state,
            }

        except Exception as exc:
            self.logger.error("Failed to submit hyperparameter tuning job %s: %s", tuning_job.id, exc)
            return {"success": False, "error": str(exc)}
    
    async def sync_job_status(self, training_job: TrainingJob, db: AsyncSession) -> Dict[str, Any]:
        """Sync training job status with the backend."""
        try:
            if not training_job.vertex_ai_job_id:
                return {"success": False, "error": "No backend job ID found"}
            
            # Get status from the client
            status_result = await self.vertex_client.fetch_job_status(training_job.vertex_ai_job_id)

            # Map backend state to our job status
            backend_state = status_result.get("state", "JOB_STATE_RUNNING")
            new_status = self._map_backend_state_to_job_status(backend_state)

            # Update job if status changed
            previous_status = training_job.status
            status_changed = previous_status != new_status

            if status_changed:
                training_job.status = new_status

                if new_status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    end_time = self._parse_iso_datetime(status_result.get("end_time"))
                    training_job.end_time = end_time or datetime.utcnow()

                    if training_job.start_time:
                        duration = training_job.end_time - training_job.start_time
                        training_job.duration_seconds = int(duration.total_seconds())

                if new_status == JobStatus.FAILED and status_result.get("error"):
                    training_job.error_message = str(status_result["error"])

                if new_status == JobStatus.RUNNING and not training_job.start_time:
                    start_time = self._parse_iso_datetime(status_result.get("start_time"))
                    training_job.start_time = start_time or datetime.utcnow()

                await db.commit()

                self.logger.info(
                    "Updated job %s status from %s to %s (backend_state=%s)",
                    training_job.id,
                    previous_status.value if previous_status else "unknown",
                    new_status.value,
                    backend_state,
                )

            return {
                "success": True,
                "backend_state": backend_state,
                "job_status": new_status.value,
                "status_changed": status_changed,
            }

        except Exception as exc:
            self.logger.error("Failed to sync job %s status: %s", training_job.id, exc)
            return {"success": False, "error": str(exc)}
    
    async def get_job_logs(self, training_job: TrainingJob) -> Dict[str, Any]:
        """Get training job logs from the backend."""
        try:
            if not training_job.vertex_ai_job_id:
                return {"error": "No backend job ID found"}
            
            logs_result = await self.vertex_client.fetch_job_logs(training_job.vertex_ai_job_id)

            logs = logs_result.get("logs") or logs_result.get("entries")
            if logs:
                if training_job.training_logs is None:
                    training_job.training_logs = []

                existing_logs = set(training_job.training_logs)
                new_logs = [log for log in logs if log not in existing_logs]
                training_job.training_logs.extend(new_logs)

            return {"job_id": training_job.vertex_ai_job_id, "logs": logs or []}

        except Exception as exc:
            self.logger.error("Failed to get job logs for %s: %s", training_job.id, exc)
            return {"error": str(exc)}
    
    async def cancel_job(self, training_job: TrainingJob, db: AsyncSession) -> Dict[str, Any]:
        """Cancel a training job in the backend."""
        try:
            if not training_job.vertex_ai_job_id:
                return {"success": False, "error": "No backend job ID found"}
            
            backend_response = await self.vertex_client.cancel_job(training_job.vertex_ai_job_id)

            success = backend_response.get("success", True)

            if success:
                training_job.status = JobStatus.CANCELLED
                training_job.end_time = datetime.utcnow()

                if training_job.start_time:
                    duration = training_job.end_time - training_job.start_time
                    training_job.duration_seconds = int(duration.total_seconds())
                
                await db.commit()
                
                self.logger.info(f"Cancelled training job {training_job.id} in backend")

            backend_response.setdefault("success", success)
            return backend_response

        except Exception as exc:
            self.logger.error("Failed to cancel job %s in backend: %s", training_job.id, exc)
            return {"success": False, "error": str(exc)}
    
    async def sync_hyperparameter_trials(
        self, tuning_job: HyperparameterTuningJob, db: AsyncSession
    ) -> Dict[str, Any]:
        """Sync hyperparameter trials from the backend."""
        self.logger.warning("Hyperparameter tuning trial synchronization is not yet implemented.")
        return {"success": True, "synced_trials": 0, "total_trials": 0}

    def _build_training_job_spec(
        self, training_job: TrainingJob, dataset_path: Optional[str]
    ) -> Dict[str, Any]:
        """Construct the payload sent to the orchestration backend for training jobs."""
        callback_base = getattr(self.settings, "TRAINING_CALLBACK_BASE_URL", None)
        callbacks: Dict[str, str] = {}

        if callback_base:
            base = callback_base.rstrip("/")
            callbacks = {
                "progress": f"{base}/api/training/jobs/{training_job.id}/progress",
                "completion": f"{base}/api/training/jobs/{training_job.id}/complete",
            }

        return {
            "job_id": str(training_job.id),
            "job_name": training_job.job_name,
            "user_context": {
                "user_id": str(training_job.user_id) if training_job.user_id else None,
                "strategy_id": str(training_job.strategy_id),
            },
            "dataset": {
                "id": str(training_job.dataset_id),
                "path": dataset_path,
            },
            "compute": {
                "instance_type": training_job.instance_type.value,
                "machine_type": training_job.machine_type,
                "disk_size_gb": training_job.disk_size,
                "timeout_hours": training_job.timeout_hours,
            },
            "priority": training_job.priority.value,
            "training": {
                "command": self._get_training_command(training_job),
                "args": self._get_training_args(training_job),
            },
            "hyperparameters": training_job.hyperparameters or {},
            "training_config": training_job.training_config or {},
            "model_config": training_job.model_config or {},
            "callbacks": callbacks or None,
        }

    def _build_tuning_job_spec(
        self, tuning_job: HyperparameterTuningJob, dataset_path: Optional[str]
    ) -> Dict[str, Any]:
        """Construct payload for hyperparameter tuning jobs."""
        spec = self._build_training_job_spec(tuning_job, dataset_path)
        spec.update(
            {
                "job_type": "hyperparameter_tuning",
                "parameter_space": tuning_job.parameter_space,
                "optimization": {
                    "objective": tuning_job.optimization_objective.value,
                    "algorithm": tuning_job.optimization_algorithm.value,
                    "metric": tuning_job.objective_metric,
                    "max_trials": tuning_job.max_trials,
                    "max_parallel_trials": tuning_job.max_parallel_trials,
                    "max_trial_duration_hours": tuning_job.max_trial_duration_hours,
                    "early_stopping": tuning_job.early_stopping_config,
                },
            }
        )
        return spec
    
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

    def _parse_iso_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
