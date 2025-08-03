"""
Training job manager for Phase 4: Model Training Orchestrator.
Manages ML model training jobs with queue management, resource allocation, and progress tracking.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.training import (
    TrainingJob, JobType, JobStatus, InstanceType, ModelFramework, 
    TrainingPriority, OptimizationObjective, OptimizationAlgorithm,
    HyperparameterTuningJob, HyperparameterTrial, ModelArtifact,
    TrainingMetric, ComputeResource, ResourceQuota, TrainingTemplate
)
from app.models.dataset import Dataset
from app.models.strategy import Strategy
from app.core.config import get_settings


class TrainingJobQueue:
    """Queue manager for training jobs with priority handling."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.Queue")
    
    async def enqueue_job(self, job: TrainingJob, db: AsyncSession) -> Dict[str, Any]:
        """Add a job to the training queue."""
        try:
            # Calculate queue position based on priority and submission time
            priority_order = {
                TrainingPriority.URGENT: 1,
                TrainingPriority.HIGH: 2,
                TrainingPriority.NORMAL: 3,
                TrainingPriority.LOW: 4
            }
            
            # Get current queue position for same priority level
            result = await db.execute(
                select(func.count(TrainingJob.id))
                .where(
                    and_(
                        TrainingJob.status == JobStatus.QUEUED,
                        TrainingJob.priority == job.priority
                    )
                )
            )
            same_priority_count = result.scalar() or 0
            
            # Get higher priority jobs count
            higher_priority_jobs = 0
            for priority, order in priority_order.items():
                if order < priority_order[job.priority]:
                    result = await db.execute(
                        select(func.count(TrainingJob.id))
                        .where(
                            and_(
                                TrainingJob.status == JobStatus.QUEUED,
                                TrainingJob.priority == priority
                            )
                        )
                    )
                    higher_priority_jobs += result.scalar() or 0
            
            # Set queue position
            queue_position = higher_priority_jobs + same_priority_count + 1
            
            # Update job status and queue info
            job.status = JobStatus.QUEUED
            job.queued_at = datetime.utcnow()
            job.queue_position = queue_position
            
            # Estimate start time based on queue position and average job duration
            avg_duration_hours = await self._get_average_job_duration(job.job_type, db)
            estimated_start = datetime.utcnow() + timedelta(hours=avg_duration_hours * (queue_position - 1))
            job.estimated_start_time = estimated_start
            job.estimated_completion_time = estimated_start + timedelta(hours=avg_duration_hours)
            
            await db.commit()
            
            self.logger.info(f"Enqueued job {job.id} at position {queue_position}")
            
            return {
                "success": True,
                "queue_position": queue_position,
                "estimated_start_time": estimated_start.isoformat(),
                "estimated_completion_time": job.estimated_completion_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to enqueue job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def dequeue_next_job(self, db: AsyncSession) -> Optional[TrainingJob]:
        """Get the next job from the queue."""
        try:
            # Get highest priority job that's queued
            result = await db.execute(
                select(TrainingJob)
                .where(TrainingJob.status == JobStatus.QUEUED)
                .order_by(
                    TrainingJob.priority.asc(),  # Higher priority first (URGENT=1, LOW=4)
                    TrainingJob.queued_at.asc()  # Earlier submissions first
                )
                .limit(1)
            )
            
            job = result.scalar_one_or_none()
            
            if job:
                self.logger.info(f"Dequeued job {job.id} from queue")
                
                # Update queue positions for remaining jobs
                await self._update_queue_positions(db)
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to dequeue job: {str(e)}")
            return None
    
    async def get_queue_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get current queue status."""
        try:
            # Count jobs by status
            status_counts = {}
            for status in JobStatus:
                result = await db.execute(
                    select(func.count(TrainingJob.id))
                    .where(TrainingJob.status == status)
                )
                status_counts[status.value] = result.scalar() or 0
            
            # Get queue details for queued jobs
            result = await db.execute(
                select(TrainingJob)
                .where(TrainingJob.status == JobStatus.QUEUED)
                .order_by(TrainingJob.queue_position.asc())
                .limit(20)
            )
            queued_jobs = result.scalars().all()
            
            queue_details = []
            for job in queued_jobs:
                queue_details.append({
                    "job_id": str(job.id),
                    "job_name": job.job_name,
                    "priority": job.priority.value,
                    "queue_position": job.queue_position,
                    "estimated_start_time": job.estimated_start_time.isoformat() if job.estimated_start_time else None,
                    "user_id": str(job.user_id)
                })
            
            return {
                "status_counts": status_counts,
                "queue_details": queue_details,
                "total_queued": len(queued_jobs),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get queue status: {str(e)}")
            return {"error": str(e)}
    
    async def _get_average_job_duration(self, job_type: JobType, db: AsyncSession) -> float:
        """Calculate average job duration for estimation."""
        try:
            result = await db.execute(
                select(func.avg(TrainingJob.duration_seconds))
                .where(
                    and_(
                        TrainingJob.job_type == job_type,
                        TrainingJob.status == JobStatus.COMPLETED,
                        TrainingJob.duration_seconds.isnot(None)
                    )
                )
            )
            
            avg_seconds = result.scalar()
            if avg_seconds:
                return avg_seconds / 3600  # Convert to hours
            else:
                # Default estimates by job type
                defaults = {
                    JobType.TRAINING: 2.0,
                    JobType.HYPERPARAMETER_TUNING: 4.0,
                    JobType.VALIDATION: 0.5,
                    JobType.INFERENCE: 0.1,
                    JobType.FEATURE_ENGINEERING: 1.0
                }
                return defaults.get(job_type, 2.0)
                
        except Exception as e:
            self.logger.error(f"Failed to calculate average duration: {str(e)}")
            return 2.0  # Default 2 hours
    
    async def _update_queue_positions(self, db: AsyncSession):
        """Update queue positions after job dequeue."""
        try:
            # Get all queued jobs ordered by priority and time
            result = await db.execute(
                select(TrainingJob)
                .where(TrainingJob.status == JobStatus.QUEUED)
                .order_by(
                    TrainingJob.priority.asc(),
                    TrainingJob.queued_at.asc()
                )
            )
            
            queued_jobs = result.scalars().all()
            
            # Update positions
            for index, job in enumerate(queued_jobs, 1):
                if job.queue_position != index:
                    job.queue_position = index
            
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to update queue positions: {str(e)}")


class ResourceManager:
    """Resource allocation and monitoring for training jobs."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ResourceManager")
    
    async def check_resource_availability(self, instance_type: InstanceType, 
                                        db: AsyncSession) -> Dict[str, Any]:
        """Check if resources are available for the requested instance type."""
        try:
            result = await db.execute(
                select(ComputeResource)
                .where(
                    and_(
                        ComputeResource.resource_type == instance_type,
                        ComputeResource.is_available == True,
                        ComputeResource.current_usage < ComputeResource.max_concurrent_jobs
                    )
                )
            )
            
            available_resources = result.scalars().all()
            
            if available_resources:
                # Select best resource (lowest current usage)
                best_resource = min(available_resources, key=lambda r: r.current_usage)
                
                return {
                    "available": True,
                    "resource_id": str(best_resource.id),
                    "resource_name": best_resource.resource_name,
                    "cost_per_hour": best_resource.cost_per_hour,
                    "current_usage": best_resource.current_usage,
                    "max_concurrent": best_resource.max_concurrent_jobs
                }
            else:
                return {
                    "available": False,
                    "reason": f"No available {instance_type.value} resources"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to check resource availability: {str(e)}")
            return {"available": False, "error": str(e)}
    
    async def allocate_resource(self, resource_id: str, job: TrainingJob, 
                              db: AsyncSession) -> bool:
        """Allocate a resource to a training job."""
        try:
            result = await db.execute(
                select(ComputeResource)
                .where(ComputeResource.id == UUID(resource_id))
            )
            resource = result.scalar_one_or_none()
            
            if not resource:
                return False
            
            if resource.current_usage >= resource.max_concurrent_jobs:
                return False
            
            # Increment usage
            resource.current_usage += 1
            
            # Update job with resource info
            job.machine_type = resource.resource_name
            
            await db.commit()
            
            self.logger.info(f"Allocated resource {resource_id} to job {job.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to allocate resource: {str(e)}")
            return False
    
    async def release_resource(self, resource_id: str, db: AsyncSession) -> bool:
        """Release a resource from a completed job."""
        try:
            result = await db.execute(
                select(ComputeResource)
                .where(ComputeResource.id == UUID(resource_id))
            )
            resource = result.scalar_one_or_none()
            
            if resource and resource.current_usage > 0:
                resource.current_usage -= 1
                await db.commit()
                
                self.logger.info(f"Released resource {resource_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to release resource: {str(e)}")
            return False
    
    async def check_user_quota(self, user_id: str, job: TrainingJob, 
                             db: AsyncSession) -> Dict[str, Any]:
        """Check if user has sufficient quota for the job."""
        try:
            # Get user's resource quota
            result = await db.execute(
                select(ResourceQuota)
                .where(ResourceQuota.user_id == UUID(user_id))
            )
            quota = result.scalar_one_or_none()
            
            if not quota:
                return {"within_quota": False, "reason": "No quota found for user"}
            
            # Check concurrent jobs limit
            result = await db.execute(
                select(func.count(TrainingJob.id))
                .where(
                    and_(
                        TrainingJob.user_id == UUID(user_id),
                        TrainingJob.status.in_([JobStatus.RUNNING, JobStatus.QUEUED])
                    )
                )
            )
            current_jobs = result.scalar() or 0
            
            if current_jobs >= quota.max_concurrent_jobs:
                return {
                    "within_quota": False,
                    "reason": f"Concurrent jobs limit exceeded ({current_jobs}/{quota.max_concurrent_jobs})"
                }
            
            # Estimate job cost
            estimated_cost = self._estimate_job_cost(job)
            
            # Check monthly cost limit
            if quota.current_monthly_cost + estimated_cost > quota.max_monthly_cost:
                return {
                    "within_quota": False,
                    "reason": f"Monthly cost limit would be exceeded ({quota.current_monthly_cost + estimated_cost:.2f}/{quota.max_monthly_cost:.2f})"
                }
            
            return {
                "within_quota": True,
                "estimated_cost": estimated_cost,
                "remaining_jobs": quota.max_concurrent_jobs - current_jobs,
                "remaining_budget": quota.max_monthly_cost - quota.current_monthly_cost
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check user quota: {str(e)}")
            return {"within_quota": False, "error": str(e)}
    
    def _estimate_job_cost(self, job: TrainingJob) -> float:
        """Estimate the cost of a training job."""
        try:
            # Default hourly rates by instance type
            base_rates = {
                InstanceType.CPU_SMALL: 0.05,
                InstanceType.CPU_MEDIUM: 0.10,
                InstanceType.CPU_LARGE: 0.20,
                InstanceType.GPU_T4: 0.35,
                InstanceType.GPU_V100: 2.50,
                InstanceType.GPU_A100: 4.00,
                InstanceType.TPU_V3: 8.00,
                InstanceType.TPU_V4: 12.00
            }
            
            hourly_rate = base_rates.get(job.instance_type, 1.0)
            estimated_hours = job.timeout_hours or 4  # Default 4 hours
            
            return hourly_rate * estimated_hours
            
        except Exception as e:
            self.logger.error(f"Failed to estimate job cost: {str(e)}")
            return 10.0  # Default estimate


class TrainingJobManager:
    """Main training job manager orchestrating job lifecycle."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.queue = TrainingJobQueue()
        self.resource_manager = ResourceManager()
    
    async def create_training_job(self, job_data: Dict[str, Any], user_id: str, 
                                db: AsyncSession) -> Dict[str, Any]:
        """Create a new training job."""
        try:
            # Validate required fields
            required_fields = ["strategy_id", "dataset_id", "job_name", "job_type", "instance_type"]
            for field in required_fields:
                if field not in job_data:
                    return {"success": False, "error": f"Missing required field: {field}"}
            
            # Validate strategy exists and belongs to user
            result = await db.execute(
                select(Strategy)
                .where(
                    and_(
                        Strategy.id == UUID(job_data["strategy_id"]),
                        Strategy.user_id == UUID(user_id)
                    )
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return {"success": False, "error": "Strategy not found or access denied"}
            
            # Validate dataset exists and user has access
            result = await db.execute(
                select(Dataset)
                .where(
                    or_(
                        and_(
                            Dataset.id == UUID(job_data["dataset_id"]),
                            Dataset.user_id == UUID(user_id)
                        ),
                        and_(
                            Dataset.id == UUID(job_data["dataset_id"]),
                            Dataset.is_public == True
                        )
                    )
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {"success": False, "error": "Dataset not found or access denied"}
            
            # Create training job
            job = TrainingJob(
                id=uuid4(),
                user_id=UUID(user_id),
                strategy_id=UUID(job_data["strategy_id"]),
                dataset_id=UUID(job_data["dataset_id"]),
                job_name=job_data["job_name"],
                job_type=JobType(job_data["job_type"]),
                instance_type=InstanceType(job_data["instance_type"]),
                machine_type=job_data.get("machine_type"),
                disk_size=job_data.get("disk_size", 100),
                timeout_hours=job_data.get("timeout_hours", 24),
                priority=TrainingPriority(job_data.get("priority", TrainingPriority.NORMAL.value)),
                hyperparameters=job_data.get("hyperparameters", {}),
                training_config=job_data.get("training_config", {}),
                model_config=job_data.get("model_config", {}),
                status=JobStatus.PENDING
            )
            
            # Estimate cost
            job.estimated_cost = self.resource_manager._estimate_job_cost(job)
            
            # Check user quota
            quota_check = await self.resource_manager.check_user_quota(user_id, job, db)
            if not quota_check["within_quota"]:
                return {"success": False, "error": quota_check["reason"]}
            
            # Save job
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            # Add to queue
            queue_result = await self.queue.enqueue_job(job, db)
            
            if queue_result["success"]:
                self.logger.info(f"Created training job {job.id} for user {user_id}")
                
                return {
                    "success": True,
                    "job_id": str(job.id),
                    "queue_info": queue_result,
                    "estimated_cost": job.estimated_cost
                }
            else:
                return {"success": False, "error": queue_result["error"]}
                
        except Exception as e:
            self.logger.error(f"Failed to create training job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def start_next_job(self, db: AsyncSession) -> Dict[str, Any]:
        """Start the next job in the queue."""
        try:
            # Get next job from queue
            job = await self.queue.dequeue_next_job(db)
            
            if not job:
                return {"success": False, "message": "No jobs in queue"}
            
            # Check resource availability
            resource_check = await self.resource_manager.check_resource_availability(
                job.instance_type, db
            )
            
            if not resource_check["available"]:
                # Put job back in queue
                await self.queue.enqueue_job(job, db)
                return {"success": False, "error": resource_check.get("reason", "No resources available")}
            
            # Allocate resource
            allocated = await self.resource_manager.allocate_resource(
                resource_check["resource_id"], job, db
            )
            
            if not allocated:
                return {"success": False, "error": "Failed to allocate resource"}
            
            # Update job status
            job.status = JobStatus.RUNNING
            job.start_time = datetime.utcnow()
            job.progress_percentage = 0
            
            await db.commit()
            
            # Here you would integrate with actual training infrastructure
            # For now, we'll simulate the training process
            
            self.logger.info(f"Started training job {job.id}")
            
            return {
                "success": True,
                "job_id": str(job.id),
                "resource_info": resource_check
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start next job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_job_progress(self, job_id: str, progress_data: Dict[str, Any], 
                                db: AsyncSession) -> Dict[str, Any]:
        """Update training job progress."""
        try:
            result = await db.execute(
                select(TrainingJob)
                .where(TrainingJob.id == UUID(job_id))
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return {"success": False, "error": "Job not found"}
            
            # Update progress
            if "progress_percentage" in progress_data:
                job.progress_percentage = min(100, max(0, progress_data["progress_percentage"]))
            
            # Add training logs
            if "logs" in progress_data:
                if job.training_logs is None:
                    job.training_logs = []
                job.training_logs.extend(progress_data["logs"])
            
            # Update metrics
            if "metrics" in progress_data:
                if job.final_metrics is None:
                    job.final_metrics = {}
                job.final_metrics.update(progress_data["metrics"])
            
            await db.commit()
            
            return {"success": True, "message": "Progress updated"}
            
        except Exception as e:
            self.logger.error(f"Failed to update job progress: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def complete_job(self, job_id: str, completion_data: Dict[str, Any], 
                          db: AsyncSession) -> Dict[str, Any]:
        """Mark a training job as completed."""
        try:
            result = await db.execute(
                select(TrainingJob)
                .where(TrainingJob.id == UUID(job_id))
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return {"success": False, "error": "Job not found"}
            
            # Update job completion info
            job.status = JobStatus.COMPLETED
            job.end_time = datetime.utcnow()
            job.progress_percentage = 100
            
            if job.start_time:
                job.duration_seconds = int((job.end_time - job.start_time).total_seconds())
            
            # Update final metrics
            if "final_metrics" in completion_data:
                job.final_metrics = completion_data["final_metrics"]
            
            # Update resource usage and costs
            if "resource_usage" in completion_data:
                usage = completion_data["resource_usage"]
                job.cpu_hours = usage.get("cpu_hours", 0)
                job.gpu_hours = usage.get("gpu_hours", 0)
                job.memory_gb_hours = usage.get("memory_gb_hours", 0)
                job.actual_cost = usage.get("actual_cost", 0)
            
            # Release resource (if we have resource tracking)
            # This would need to be implemented based on resource allocation
            
            await db.commit()
            
            self.logger.info(f"Completed training job {job.id}")
            
            return {"success": True, "message": "Job completed successfully"}
            
        except Exception as e:
            self.logger.error(f"Failed to complete job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def cancel_job(self, job_id: str, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Cancel a training job."""
        try:
            result = await db.execute(
                select(TrainingJob)
                .where(
                    and_(
                        TrainingJob.id == UUID(job_id),
                        TrainingJob.user_id == UUID(user_id)
                    )
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return {"success": False, "error": "Job not found or access denied"}
            
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return {"success": False, "error": f"Cannot cancel job with status {job.status.value}"}
            
            # Update job status
            job.status = JobStatus.CANCELLED
            job.end_time = datetime.utcnow()
            
            if job.start_time:
                job.duration_seconds = int((job.end_time - job.start_time).total_seconds())
            
            await db.commit()
            
            # Release any allocated resources
            # This would need resource tracking implementation
            
            self.logger.info(f"Cancelled training job {job.id}")
            
            return {"success": True, "message": "Job cancelled successfully"}
            
        except Exception as e:
            self.logger.error(f"Failed to cancel job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def list_user_jobs(self, user_id: str, filters: Dict[str, Any], 
                           db: AsyncSession) -> Dict[str, Any]:
        """List training jobs for a user with filtering."""
        try:
            query = select(TrainingJob).where(TrainingJob.user_id == UUID(user_id))
            
            # Apply filters
            if "status" in filters:
                if isinstance(filters["status"], list):
                    query = query.where(TrainingJob.status.in_([JobStatus(s) for s in filters["status"]]))
                else:
                    query = query.where(TrainingJob.status == JobStatus(filters["status"]))
            
            if "job_type" in filters:
                query = query.where(TrainingJob.job_type == JobType(filters["job_type"]))
            
            if "strategy_id" in filters:
                query = query.where(TrainingJob.strategy_id == UUID(filters["strategy_id"]))
            
            if "start_date_from" in filters:
                start_date = datetime.fromisoformat(filters["start_date_from"])
                query = query.where(TrainingJob.created_at >= start_date)
            
            if "start_date_to" in filters:
                end_date = datetime.fromisoformat(filters["start_date_to"])
                query = query.where(TrainingJob.created_at <= end_date)
            
            # Sorting
            sort_by = filters.get("sort_by", "created_at")
            sort_order = filters.get("sort_order", "desc")
            
            if hasattr(TrainingJob, sort_by):
                sort_column = getattr(TrainingJob, sort_by)
                if sort_order == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            
            # Pagination
            limit = filters.get("limit", 50)
            offset = filters.get("offset", 0)
            
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = await db.execute(query)
            jobs = result.scalars().all()
            
            # Get total count for pagination
            count_query = select(func.count(TrainingJob.id)).where(TrainingJob.user_id == UUID(user_id))
            count_result = await db.execute(count_query)
            total_count = count_result.scalar()
            
            # Format response
            job_list = []
            for job in jobs:
                job_list.append({
                    "id": str(job.id),
                    "job_name": job.job_name,
                    "job_type": job.job_type.value,
                    "status": job.status.value,
                    "priority": job.priority.value,
                    "instance_type": job.instance_type.value,
                    "progress_percentage": job.progress_percentage,
                    "estimated_cost": job.estimated_cost,
                    "actual_cost": job.actual_cost,
                    "created_at": job.created_at.isoformat(),
                    "start_time": job.start_time.isoformat() if job.start_time else None,
                    "end_time": job.end_time.isoformat() if job.end_time else None,
                    "duration_seconds": job.duration_seconds,
                    "strategy_id": str(job.strategy_id),
                    "dataset_id": str(job.dataset_id)
                })
            
            return {
                "jobs": job_list,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            self.logger.error(f"Failed to list user jobs: {str(e)}")
            return {"error": str(e)}
    
    async def get_job_details(self, job_id: str, user_id: str, 
                            db: AsyncSession) -> Dict[str, Any]:
        """Get detailed information about a training job."""
        try:
            result = await db.execute(
                select(TrainingJob)
                .options(
                    selectinload(TrainingJob.strategy),
                    selectinload(TrainingJob.dataset),
                    selectinload(TrainingJob.artifacts),
                    selectinload(TrainingJob.hyperparameter_trials)
                )
                .where(
                    and_(
                        TrainingJob.id == UUID(job_id),
                        TrainingJob.user_id == UUID(user_id)
                    )
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return {"error": "Job not found or access denied"}
            
            # Format detailed response
            job_details = {
                "id": str(job.id),
                "job_name": job.job_name,
                "job_type": job.job_type.value,
                "status": job.status.value,
                "priority": job.priority.value,
                "instance_type": job.instance_type.value,
                "machine_type": job.machine_type,
                "disk_size": job.disk_size,
                "timeout_hours": job.timeout_hours,
                "progress_percentage": job.progress_percentage,
                "estimated_cost": job.estimated_cost,
                "actual_cost": job.actual_cost,
                "hyperparameters": job.hyperparameters,
                "training_config": job.training_config,
                "model_config": job.model_config,
                "final_metrics": job.final_metrics,
                "best_metrics": job.best_metrics,
                "training_logs": job.training_logs,
                "error_message": job.error_message,
                "cpu_hours": job.cpu_hours,
                "gpu_hours": job.gpu_hours,
                "memory_gb_hours": job.memory_gb_hours,
                "vertex_ai_job_id": job.vertex_ai_job_id,
                "mlflow_run_id": job.mlflow_run_id,
                "gcs_output_path": job.gcs_output_path,
                "created_at": job.created_at.isoformat(),
                "start_time": job.start_time.isoformat() if job.start_time else None,
                "end_time": job.end_time.isoformat() if job.end_time else None,
                "duration_seconds": job.duration_seconds,
                "queue_position": job.queue_position,
                "estimated_start_time": job.estimated_start_time.isoformat() if job.estimated_start_time else None,
                "estimated_completion_time": job.estimated_completion_time.isoformat() if job.estimated_completion_time else None,
                
                # Related entities
                "strategy": {
                    "id": str(job.strategy.id),
                    "name": job.strategy.name
                } if job.strategy else None,
                
                "dataset": {
                    "id": str(job.dataset.id),
                    "name": job.dataset.name,
                    "asset_class": job.dataset.asset_class.value
                } if job.dataset else None,
                
                # Artifacts
                "artifacts": [
                    {
                        "id": str(artifact.id),
                        "model_name": artifact.model_name,
                        "version": artifact.version,
                        "framework": artifact.framework.value,
                        "file_size": artifact.file_size,
                        "is_deployed": artifact.is_deployed
                    }
                    for artifact in job.artifacts
                ],
                
                # Hyperparameter trials
                "hyperparameter_trials": [
                    {
                        "id": str(trial.id),
                        "trial_number": trial.trial_number,
                        "status": trial.status.value,
                        "objective_value": trial.objective_value,
                        "hyperparameters": trial.hyperparameters
                    }
                    for trial in job.hyperparameter_trials
                ]
            }
            
            return job_details
            
        except Exception as e:
            self.logger.error(f"Failed to get job details: {str(e)}")
            return {"error": str(e)}
    
    async def get_queue_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get current training queue status."""
        return await self.queue.get_queue_status(db)