"""
Resource allocator for Phase 4: Model Training Orchestrator.
Manages compute resources, pricing, quotas, and cost optimization for ML training jobs.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
from decimal import Decimal
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.training import (
    ComputeResource, ResourceQuota, TrainingJob, JobStatus, 
    InstanceType, TrainingPriority
)
from app.core.config import get_settings


class CostCalculator:
    """Calculate and optimize costs for training jobs."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CostCalculator")
        
        # Base pricing per hour (in USD)
        self.base_pricing = {
            InstanceType.CPU_SMALL: 0.05,
            InstanceType.CPU_MEDIUM: 0.10,
            InstanceType.CPU_LARGE: 0.20,
            InstanceType.GPU_T4: 0.35,
            InstanceType.GPU_V100: 2.50,
            InstanceType.GPU_A100: 4.00,
            InstanceType.TPU_V3: 8.00,
            InstanceType.TPU_V4: 12.00
        }
        
        # Pricing multipliers for different factors
        self.region_multipliers = {
            "us-central1": 1.0,
            "us-east1": 1.0,
            "us-west1": 1.05,
            "europe-west1": 1.1,
            "asia-east1": 1.15
        }
        
        self.time_multipliers = {
            "peak": 1.2,     # Business hours
            "standard": 1.0,  # Regular hours
            "off_peak": 0.8   # Night/weekend
        }
        
        # Preemptible pricing (60-80% discount)
        self.preemptible_discount = 0.3  # 70% discount
    
    def calculate_job_cost(self, instance_type: InstanceType, duration_hours: float,
                          region: str = "us-central1", is_preemptible: bool = False,
                          time_period: str = "standard") -> Dict[str, Any]:
        """Calculate the cost for a training job."""
        try:
            base_cost = self.base_pricing.get(instance_type, 1.0)
            
            # Apply multipliers
            region_multiplier = self.region_multipliers.get(region, 1.0)
            time_multiplier = self.time_multipliers.get(time_period, 1.0)
            
            hourly_rate = base_cost * region_multiplier * time_multiplier
            
            # Apply preemptible discount
            if is_preemptible:
                hourly_rate *= self.preemptible_discount
            
            total_cost = hourly_rate * duration_hours
            
            return {
                "base_hourly_rate": base_cost,
                "adjusted_hourly_rate": hourly_rate,
                "duration_hours": duration_hours,
                "total_cost": round(total_cost, 4),
                "currency": "USD",
                "is_preemptible": is_preemptible,
                "region": region,
                "time_period": time_period,
                "breakdown": {
                    "base_cost": base_cost * duration_hours,
                    "region_adjustment": (base_cost * region_multiplier - base_cost) * duration_hours,
                    "time_adjustment": (base_cost * time_multiplier - base_cost) * duration_hours,
                    "preemptible_discount": -base_cost * duration_hours * (1 - self.preemptible_discount) if is_preemptible else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate job cost: {str(e)}")
            return {"error": str(e)}
    
    def recommend_cost_optimization(self, job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend cost optimization strategies for a job."""
        try:
            recommendations = []
            
            instance_type = InstanceType(job_requirements.get("instance_type"))
            duration_hours = job_requirements.get("duration_hours", 4)
            priority = job_requirements.get("priority", TrainingPriority.NORMAL.value)
            
            # Current cost
            current_cost = self.calculate_job_cost(instance_type, duration_hours)
            
            # Recommendation 1: Use preemptible instances
            if not job_requirements.get("is_preemptible", False):
                preemptible_cost = self.calculate_job_cost(
                    instance_type, duration_hours, is_preemptible=True
                )
                savings = current_cost["total_cost"] - preemptible_cost["total_cost"]
                
                if savings > 0:
                    recommendations.append({
                        "type": "preemptible_instance",
                        "description": "Use preemptible instances for significant cost savings",
                        "savings_usd": round(savings, 2),
                        "savings_percentage": round((savings / current_cost["total_cost"]) * 100, 1),
                        "risk": "Job may be interrupted, requiring checkpointing",
                        "suitable_for": ["non-urgent jobs", "fault-tolerant workloads"]
                    })
            
            # Recommendation 2: Alternative instance types
            for alt_instance in InstanceType:
                if alt_instance != instance_type:
                    alt_cost = self.calculate_job_cost(alt_instance, duration_hours)
                    
                    if alt_cost["total_cost"] < current_cost["total_cost"]:
                        savings = current_cost["total_cost"] - alt_cost["total_cost"]
                        recommendations.append({
                            "type": "alternative_instance",
                            "description": f"Consider using {alt_instance.value} instead",
                            "alternative_instance": alt_instance.value,
                            "savings_usd": round(savings, 2),
                            "savings_percentage": round((savings / current_cost["total_cost"]) * 100, 1),
                            "performance_impact": self._assess_performance_impact(instance_type, alt_instance)
                        })
            
            # Recommendation 3: Off-peak scheduling
            if priority in [TrainingPriority.LOW.value, TrainingPriority.NORMAL.value]:
                off_peak_cost = self.calculate_job_cost(
                    instance_type, duration_hours, time_period="off_peak"
                )
                savings = current_cost["total_cost"] - off_peak_cost["total_cost"]
                
                if savings > 0:
                    recommendations.append({
                        "type": "off_peak_scheduling",
                        "description": "Schedule job during off-peak hours for lower rates",
                        "savings_usd": round(savings, 2),
                        "savings_percentage": round((savings / current_cost["total_cost"]) * 100, 1),
                        "suggested_times": ["10 PM - 6 AM local time", "weekends"]
                    })
            
            # Recommendation 4: Spot instances with checkpointing
            if duration_hours > 2:
                recommendations.append({
                    "type": "spot_with_checkpointing",
                    "description": "Use spot instances with automated checkpointing",
                    "estimated_savings": "50-70%",
                    "requirements": ["Implement checkpointing", "Fault-tolerant code"],
                    "best_for": ["Long-running jobs", "Iterative training"]
                })
            
            # Sort recommendations by savings
            recommendations.sort(key=lambda x: x.get("savings_usd", 0), reverse=True)
            
            return {
                "current_cost": current_cost,
                "recommendations": recommendations[:5],  # Top 5 recommendations
                "total_potential_savings": sum(r.get("savings_usd", 0) for r in recommendations[:3])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate cost recommendations: {str(e)}")
            return {"error": str(e)}
    
    def _assess_performance_impact(self, current: InstanceType, alternative: InstanceType) -> str:
        """Assess performance impact of switching instance types."""
        # Simple heuristic based on compute power
        compute_power = {
            InstanceType.CPU_SMALL: 1,
            InstanceType.CPU_MEDIUM: 2,
            InstanceType.CPU_LARGE: 4,
            InstanceType.GPU_T4: 6,
            InstanceType.GPU_V100: 10,
            InstanceType.GPU_A100: 15,
            InstanceType.TPU_V3: 20,
            InstanceType.TPU_V4: 30
        }
        
        current_power = compute_power.get(current, 5)
        alt_power = compute_power.get(alternative, 5)
        
        ratio = alt_power / current_power
        
        if ratio > 1.5:
            return "Significant performance improvement expected"
        elif ratio > 1.1:
            return "Moderate performance improvement expected"
        elif ratio > 0.9:
            return "Similar performance expected"
        elif ratio > 0.7:
            return "Moderate performance decrease expected"
        else:
            return "Significant performance decrease expected"


class QuotaManager:
    """Manage user resource quotas and usage tracking."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.QuotaManager")
    
    async def create_user_quota(self, user_id: str, quota_config: Dict[str, Any], 
                              db: AsyncSession) -> Dict[str, Any]:
        """Create resource quota for a user."""
        try:
            # Check if quota already exists
            result = await db.execute(
                select(ResourceQuota)
                .where(ResourceQuota.user_id == UUID(user_id))
            )
            existing_quota = result.scalar_one_or_none()
            
            if existing_quota:
                return {"success": False, "error": "Quota already exists for user"}
            
            # Create new quota
            quota = ResourceQuota(
                id=uuid4(),
                user_id=UUID(user_id),
                max_cpu_hours=quota_config.get("max_cpu_hours", 100.0),
                max_gpu_hours=quota_config.get("max_gpu_hours", 10.0),
                max_memory_gb_hours=quota_config.get("max_memory_gb_hours", 1000.0),
                max_storage_gb=quota_config.get("max_storage_gb", 100.0),
                max_concurrent_jobs=quota_config.get("max_concurrent_jobs", 5),
                max_monthly_cost=quota_config.get("max_monthly_cost", 1000.0),
                quota_period_start=datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                quota_period_end=self._get_next_month_start(datetime.utcnow()),
                cpu_alert_threshold=quota_config.get("cpu_alert_threshold", 0.8),
                gpu_alert_threshold=quota_config.get("gpu_alert_threshold", 0.8),
                cost_alert_threshold=quota_config.get("cost_alert_threshold", 0.8),
                alert_enabled=quota_config.get("alert_enabled", True)
            )
            
            db.add(quota)
            await db.commit()
            await db.refresh(quota)
            
            self.logger.info(f"Created quota for user {user_id}")
            
            return {
                "success": True,
                "quota_id": str(quota.id),
                "message": "User quota created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create user quota: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def check_quota_availability(self, user_id: str, resource_request: Dict[str, Any],
                                     db: AsyncSession) -> Dict[str, Any]:
        """Check if user has sufficient quota for a resource request."""
        try:
            # Get user quota
            result = await db.execute(
                select(ResourceQuota)
                .where(ResourceQuota.user_id == UUID(user_id))
            )
            quota = result.scalar_one_or_none()
            
            if not quota:
                return {
                    "available": False,
                    "reason": "No quota found for user",
                    "action_required": "Contact administrator to set up quota"
                }
            
            # Check if quota period needs reset
            if datetime.utcnow() >= quota.quota_period_end:
                await self._reset_quota_period(quota, db)
            
            # Validate concurrent jobs
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
                    "available": False,
                    "reason": f"Concurrent jobs limit exceeded ({current_jobs}/{quota.max_concurrent_jobs})",
                    "action_required": "Wait for running jobs to complete or cancel some jobs"
                }
            
            # Estimate resource usage for the request
            estimated_usage = self._estimate_resource_usage(resource_request)
            
            # Check each resource limit
            checks = [
                ("CPU hours", quota.used_cpu_hours + estimated_usage["cpu_hours"], quota.max_cpu_hours),
                ("GPU hours", quota.used_gpu_hours + estimated_usage["gpu_hours"], quota.max_gpu_hours),
                ("Memory GB-hours", quota.used_memory_gb_hours + estimated_usage["memory_gb_hours"], quota.max_memory_gb_hours),
                ("Monthly cost", quota.current_monthly_cost + estimated_usage["cost"], quota.max_monthly_cost)
            ]
            
            violations = []
            warnings = []
            
            for resource_name, projected_usage, limit in checks:
                if projected_usage > limit:
                    violations.append({
                        "resource": resource_name,
                        "projected_usage": projected_usage,
                        "limit": limit,
                        "excess": projected_usage - limit
                    })
                elif projected_usage > limit * 0.9:  # 90% threshold warning
                    warnings.append({
                        "resource": resource_name,
                        "projected_usage": projected_usage,
                        "limit": limit,
                        "usage_percentage": (projected_usage / limit) * 100
                    })
            
            if violations:
                return {
                    "available": False,
                    "reason": f"Resource quota would be exceeded",
                    "violations": violations,
                    "action_required": "Reduce resource requirements or request quota increase"
                }
            
            # Check alert thresholds
            alerts = []
            if quota.alert_enabled:
                if (quota.used_cpu_hours + estimated_usage["cpu_hours"]) / quota.max_cpu_hours > quota.cpu_alert_threshold:
                    alerts.append("CPU hours approaching limit")
                
                if (quota.used_gpu_hours + estimated_usage["gpu_hours"]) / quota.max_gpu_hours > quota.gpu_alert_threshold:
                    alerts.append("GPU hours approaching limit")
                
                if (quota.current_monthly_cost + estimated_usage["cost"]) / quota.max_monthly_cost > quota.cost_alert_threshold:
                    alerts.append("Monthly cost approaching limit")
            
            return {
                "available": True,
                "estimated_usage": estimated_usage,
                "remaining_quota": {
                    "cpu_hours": quota.max_cpu_hours - quota.used_cpu_hours,
                    "gpu_hours": quota.max_gpu_hours - quota.used_gpu_hours,
                    "memory_gb_hours": quota.max_memory_gb_hours - quota.used_memory_gb_hours,
                    "concurrent_jobs": quota.max_concurrent_jobs - current_jobs,
                    "monthly_cost": quota.max_monthly_cost - quota.current_monthly_cost
                },
                "warnings": warnings,
                "alerts": alerts
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check quota availability: {str(e)}")
            return {"available": False, "error": str(e)}
    
    async def consume_quota(self, user_id: str, resource_usage: Dict[str, Any],
                          db: AsyncSession) -> Dict[str, Any]:
        """Consume quota based on actual resource usage."""
        try:
            result = await db.execute(
                select(ResourceQuota)
                .where(ResourceQuota.user_id == UUID(user_id))
            )
            quota = result.scalar_one_or_none()
            
            if not quota:
                return {"success": False, "error": "No quota found for user"}
            
            # Update usage
            quota.used_cpu_hours += resource_usage.get("cpu_hours", 0)
            quota.used_gpu_hours += resource_usage.get("gpu_hours", 0)
            quota.used_memory_gb_hours += resource_usage.get("memory_gb_hours", 0)
            quota.current_monthly_cost += resource_usage.get("cost", 0)
            
            await db.commit()
            
            self.logger.info(f"Consumed quota for user {user_id}: {resource_usage}")
            
            return {"success": True, "message": "Quota consumed successfully"}
            
        except Exception as e:
            self.logger.error(f"Failed to consume quota: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_quota_status(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get current quota status for a user."""
        try:
            result = await db.execute(
                select(ResourceQuota)
                .where(ResourceQuota.user_id == UUID(user_id))
            )
            quota = result.scalar_one_or_none()
            
            if not quota:
                return {"error": "No quota found for user"}
            
            # Get current active jobs
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
            
            # Calculate usage percentages
            usage_percentages = {
                "cpu_hours": (quota.used_cpu_hours / quota.max_cpu_hours) * 100,
                "gpu_hours": (quota.used_gpu_hours / quota.max_gpu_hours) * 100,
                "memory_gb_hours": (quota.used_memory_gb_hours / quota.max_memory_gb_hours) * 100,
                "monthly_cost": (quota.current_monthly_cost / quota.max_monthly_cost) * 100,
                "concurrent_jobs": (current_jobs / quota.max_concurrent_jobs) * 100
            }
            
            # Check for alerts
            alerts = []
            if quota.alert_enabled:
                if usage_percentages["cpu_hours"] > quota.cpu_alert_threshold * 100:
                    alerts.append("CPU hours usage high")
                if usage_percentages["gpu_hours"] > quota.gpu_alert_threshold * 100:
                    alerts.append("GPU hours usage high")
                if usage_percentages["monthly_cost"] > quota.cost_alert_threshold * 100:
                    alerts.append("Monthly cost usage high")
            
            return {
                "quota_limits": {
                    "max_cpu_hours": quota.max_cpu_hours,
                    "max_gpu_hours": quota.max_gpu_hours,
                    "max_memory_gb_hours": quota.max_memory_gb_hours,
                    "max_storage_gb": quota.max_storage_gb,
                    "max_concurrent_jobs": quota.max_concurrent_jobs,
                    "max_monthly_cost": quota.max_monthly_cost
                },
                "current_usage": {
                    "used_cpu_hours": quota.used_cpu_hours,
                    "used_gpu_hours": quota.used_gpu_hours,
                    "used_memory_gb_hours": quota.used_memory_gb_hours,
                    "used_storage_gb": quota.used_storage_gb,
                    "current_concurrent_jobs": current_jobs,
                    "current_monthly_cost": quota.current_monthly_cost
                },
                "usage_percentages": usage_percentages,
                "remaining_quota": {
                    "cpu_hours": quota.max_cpu_hours - quota.used_cpu_hours,
                    "gpu_hours": quota.max_gpu_hours - quota.used_gpu_hours,
                    "memory_gb_hours": quota.max_memory_gb_hours - quota.used_memory_gb_hours,
                    "concurrent_jobs": quota.max_concurrent_jobs - current_jobs,
                    "monthly_cost": quota.max_monthly_cost - quota.current_monthly_cost
                },
                "quota_period": {
                    "start": quota.quota_period_start.isoformat(),
                    "end": quota.quota_period_end.isoformat(),
                    "days_remaining": (quota.quota_period_end - datetime.utcnow()).days
                },
                "alerts": alerts,
                "alert_thresholds": {
                    "cpu_alert_threshold": quota.cpu_alert_threshold,
                    "gpu_alert_threshold": quota.gpu_alert_threshold,
                    "cost_alert_threshold": quota.cost_alert_threshold
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get quota status: {str(e)}")
            return {"error": str(e)}
    
    def _estimate_resource_usage(self, resource_request: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate resource usage for a request."""
        instance_type = InstanceType(resource_request.get("instance_type"))
        duration_hours = resource_request.get("duration_hours", 4)
        
        # Base resource usage estimates
        usage_profiles = {
            InstanceType.CPU_SMALL: {"cpu": 2, "memory_gb": 4, "gpu": 0},
            InstanceType.CPU_MEDIUM: {"cpu": 4, "memory_gb": 8, "gpu": 0},
            InstanceType.CPU_LARGE: {"cpu": 8, "memory_gb": 16, "gpu": 0},
            InstanceType.GPU_T4: {"cpu": 4, "memory_gb": 16, "gpu": 1},
            InstanceType.GPU_V100: {"cpu": 8, "memory_gb": 32, "gpu": 1},
            InstanceType.GPU_A100: {"cpu": 12, "memory_gb": 64, "gpu": 1},
            InstanceType.TPU_V3: {"cpu": 16, "memory_gb": 128, "gpu": 0},
            InstanceType.TPU_V4: {"cpu": 32, "memory_gb": 256, "gpu": 0}
        }
        
        profile = usage_profiles.get(instance_type, {"cpu": 4, "memory_gb": 8, "gpu": 0})
        
        # Calculate cost
        cost_calculator = CostCalculator()
        cost_info = cost_calculator.calculate_job_cost(instance_type, duration_hours)
        
        return {
            "cpu_hours": profile["cpu"] * duration_hours,
            "gpu_hours": profile["gpu"] * duration_hours,
            "memory_gb_hours": profile["memory_gb"] * duration_hours,
            "cost": cost_info.get("total_cost", 0)
        }
    
    async def _reset_quota_period(self, quota: ResourceQuota, db: AsyncSession):
        """Reset quota usage for a new period."""
        try:
            # Reset usage counters
            quota.used_cpu_hours = 0.0
            quota.used_gpu_hours = 0.0
            quota.used_memory_gb_hours = 0.0
            quota.used_storage_gb = 0.0
            quota.current_monthly_cost = 0.0
            
            # Update period
            quota.quota_period_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            quota.quota_period_end = self._get_next_month_start(datetime.utcnow())
            quota.last_reset = datetime.utcnow()
            
            await db.commit()
            
            self.logger.info(f"Reset quota period for user {quota.user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to reset quota period: {str(e)}")
    
    def _get_next_month_start(self, current_date: datetime) -> datetime:
        """Get the start of the next month."""
        if current_date.month == 12:
            return current_date.replace(year=current_date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return current_date.replace(month=current_date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


class ResourceAllocator:
    """Main resource allocator coordinating compute resources and cost optimization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.cost_calculator = CostCalculator()
        self.quota_manager = QuotaManager()
    
    async def get_available_resources(self, filters: Dict[str, Any] = None, 
                                    db: AsyncSession = None) -> Dict[str, Any]:
        """Get available compute resources with filtering."""
        try:
            query = select(ComputeResource).where(ComputeResource.is_available == True)
            
            if filters:
                if "instance_type" in filters:
                    if isinstance(filters["instance_type"], list):
                        query = query.where(ComputeResource.resource_type.in_(filters["instance_type"]))
                    else:
                        query = query.where(ComputeResource.resource_type == InstanceType(filters["instance_type"]))
                
                if "provider" in filters:
                    query = query.where(ComputeResource.provider == filters["provider"])
                
                if "region" in filters:
                    query = query.where(ComputeResource.region == filters["region"])
                
                if "max_cost_per_hour" in filters:
                    query = query.where(ComputeResource.cost_per_hour <= filters["max_cost_per_hour"])
            
            # Order by availability and cost
            query = query.order_by(
                ComputeResource.current_usage.asc(),
                ComputeResource.cost_per_hour.asc()
            )
            
            result = await db.execute(query)
            resources = result.scalars().all()
            
            resource_list = []
            for resource in resources:
                availability_percentage = (1 - (resource.current_usage / resource.max_concurrent_jobs)) * 100
                
                resource_info = {
                    "id": str(resource.id),
                    "resource_name": resource.resource_name,
                    "resource_type": resource.resource_type.value,
                    "provider": resource.provider,
                    "region": resource.region,
                    "cpu_cores": resource.cpu_cores,
                    "memory_gb": resource.memory_gb,
                    "gpu_count": resource.gpu_count,
                    "gpu_type": resource.gpu_type,
                    "disk_gb": resource.disk_gb,
                    "network_bandwidth_gbps": resource.network_bandwidth_gbps,
                    "cost_per_hour": resource.cost_per_hour,
                    "preemptible_cost_per_hour": resource.preemptible_cost_per_hour,
                    "max_concurrent_jobs": resource.max_concurrent_jobs,
                    "current_usage": resource.current_usage,
                    "availability_percentage": round(availability_percentage, 1),
                    "benchmark_score": resource.benchmark_score,
                    "benchmark_date": resource.benchmark_date.isoformat() if resource.benchmark_date else None
                }
                
                resource_list.append(resource_info)
            
            return {
                "resources": resource_list,
                "total_count": len(resource_list),
                "providers": list(set(r["provider"] for r in resource_list)),
                "regions": list(set(r["region"] for r in resource_list)),
                "instance_types": list(set(r["resource_type"] for r in resource_list))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get available resources: {str(e)}")
            return {"error": str(e)}
    
    async def recommend_optimal_resource(self, job_requirements: Dict[str, Any],
                                       user_preferences: Dict[str, Any] = None,
                                       db: AsyncSession = None) -> Dict[str, Any]:
        """Recommend optimal resource configuration for a job."""
        try:
            # Get user quota status
            user_id = job_requirements.get("user_id")
            quota_status = await self.quota_manager.get_quota_status(user_id, db) if user_id else {}
            
            # Get available resources
            resources_info = await self.get_available_resources(db=db)
            resources = resources_info.get("resources", [])
            
            if not resources:
                return {"error": "No resources available"}
            
            # Job requirements analysis
            job_type = job_requirements.get("job_type", "training")
            dataset_size_mb = job_requirements.get("dataset_size_mb", 100)
            model_complexity = job_requirements.get("model_complexity", "medium")  # low, medium, high
            priority = job_requirements.get("priority", TrainingPriority.NORMAL.value)
            max_budget = user_preferences.get("max_budget", float('inf')) if user_preferences else float('inf')
            
            # Score resources based on suitability
            scored_resources = []
            
            for resource in resources:
                score = self._calculate_resource_score(
                    resource, job_type, dataset_size_mb, model_complexity, 
                    priority, max_budget, quota_status
                )
                
                if score > 0:  # Only include suitable resources
                    scored_resources.append({
                        "resource": resource,
                        "suitability_score": score,
                        "estimated_cost": self.cost_calculator.calculate_job_cost(
                            InstanceType(resource["resource_type"]),
                            job_requirements.get("estimated_duration_hours", 4)
                        ),
                        "recommendation_reasons": self._get_recommendation_reasons(
                            resource, job_type, model_complexity, priority
                        )
                    })
            
            # Sort by suitability score
            scored_resources.sort(key=lambda x: x["suitability_score"], reverse=True)
            
            # Generate recommendations
            recommendations = []
            for i, item in enumerate(scored_resources[:5]):  # Top 5 recommendations
                recommendation = {
                    "rank": i + 1,
                    "resource": item["resource"],
                    "suitability_score": round(item["suitability_score"], 2),
                    "estimated_cost": item["estimated_cost"],
                    "reasons": item["recommendation_reasons"],
                    "pros": self._get_resource_pros(item["resource"], job_requirements),
                    "cons": self._get_resource_cons(item["resource"], job_requirements)
                }
                
                # Add cost optimization suggestions
                if i == 0:  # For top recommendation
                    cost_optimization = self.cost_calculator.recommend_cost_optimization(
                        {**job_requirements, "instance_type": item["resource"]["resource_type"]}
                    )
                    recommendation["cost_optimization"] = cost_optimization
                
                recommendations.append(recommendation)
            
            # Summary
            summary = {
                "total_resources_evaluated": len(resources),
                "suitable_resources_found": len(scored_resources),
                "best_recommendation": recommendations[0] if recommendations else None,
                "cost_range": {
                    "min": min(r["estimated_cost"]["total_cost"] for r in scored_resources) if scored_resources else 0,
                    "max": max(r["estimated_cost"]["total_cost"] for r in scored_resources) if scored_resources else 0
                },
                "quota_constraints": self._summarize_quota_constraints(quota_status)
            }
            
            return {
                "recommendations": recommendations,
                "summary": summary,
                "quota_status": quota_status.get("remaining_quota", {})
            }
            
        except Exception as e:
            self.logger.error(f"Failed to recommend optimal resource: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_resource_score(self, resource: Dict[str, Any], job_type: str,
                                dataset_size_mb: float, model_complexity: str,
                                priority: str, max_budget: float, quota_status: Dict[str, Any]) -> float:
        """Calculate suitability score for a resource."""
        score = 0.0
        
        # Base score from resource specifications
        instance_type = resource["resource_type"]
        
        # GPU/TPU preference for ML workloads
        if "gpu" in instance_type.lower() or "tpu" in instance_type.lower():
            score += 20
        
        # CPU cores scoring
        cpu_cores = resource.get("cpu_cores", 1)
        if cpu_cores >= 8:
            score += 15
        elif cpu_cores >= 4:
            score += 10
        else:
            score += 5
        
        # Memory scoring based on dataset size
        memory_gb = resource.get("memory_gb", 1)
        required_memory = max(4, dataset_size_mb / 250)  # Rough estimate
        
        if memory_gb >= required_memory * 2:
            score += 15
        elif memory_gb >= required_memory:
            score += 10
        else:
            score -= 5
        
        # Model complexity scoring
        complexity_multipliers = {"low": 0.8, "medium": 1.0, "high": 1.3}
        score *= complexity_multipliers.get(model_complexity, 1.0)
        
        # Cost efficiency
        cost_per_hour = resource.get("cost_per_hour", 1.0)
        if cost_per_hour <= max_budget:
            score += 10 - min(10, cost_per_hour)  # Lower cost = higher score
        else:
            score -= 20  # Penalty for exceeding budget
        
        # Availability scoring
        availability = resource.get("availability_percentage", 0)
        score += availability / 10  # 100% availability adds 10 points
        
        # Priority-based adjustments
        if priority == TrainingPriority.URGENT.value:
            # Prefer immediately available resources
            if availability == 100:
                score += 20
        elif priority == TrainingPriority.LOW.value:
            # Prefer cost-effective resources
            if cost_per_hour < 1.0:
                score += 15
        
        # Quota constraints
        remaining_quota = quota_status.get("remaining_quota", {})
        if remaining_quota.get("monthly_cost", 0) < cost_per_hour * 4:  # Assume 4h job
            score -= 30  # Heavy penalty for quota violation
        
        return max(0, score)  # Ensure non-negative score
    
    def _get_recommendation_reasons(self, resource: Dict[str, Any], job_type: str,
                                  model_complexity: str, priority: str) -> List[str]:
        """Get human-readable reasons for recommendation."""
        reasons = []
        
        instance_type = resource["resource_type"]
        
        if "gpu" in instance_type.lower():
            reasons.append("GPU acceleration for faster training")
        
        if "tpu" in instance_type.lower():
            reasons.append("TPU optimization for TensorFlow workloads")
        
        if resource.get("availability_percentage", 0) == 100:
            reasons.append("Immediately available")
        
        if resource.get("cost_per_hour", 1.0) < 1.0:
            reasons.append("Cost-effective pricing")
        
        if resource.get("benchmark_score", 0) > 1000:
            reasons.append("High performance benchmark scores")
        
        if model_complexity == "high" and resource.get("memory_gb", 0) > 32:
            reasons.append("Sufficient memory for complex models")
        
        return reasons
    
    def _get_resource_pros(self, resource: Dict[str, Any], job_requirements: Dict[str, Any]) -> List[str]:
        """Get pros for a resource recommendation."""
        pros = []
        
        if resource.get("gpu_count", 0) > 0:
            pros.append(f"Includes {resource['gpu_count']} {resource.get('gpu_type', 'GPU')}(s)")
        
        if resource.get("cost_per_hour", 1.0) < 2.0:
            pros.append("Affordable hourly rate")
        
        if resource.get("availability_percentage", 0) > 80:
            pros.append("High availability")
        
        if resource.get("network_bandwidth_gbps", 0) > 10:
            pros.append("High-speed networking")
        
        return pros
    
    def _get_resource_cons(self, resource: Dict[str, Any], job_requirements: Dict[str, Any]) -> List[str]:
        """Get cons for a resource recommendation."""
        cons = []
        
        if resource.get("current_usage", 0) > resource.get("max_concurrent_jobs", 1) * 0.8:
            cons.append("High current usage, may have queue wait time")
        
        if resource.get("cost_per_hour", 0) > 5.0:
            cons.append("Higher cost per hour")
        
        if resource.get("gpu_count", 0) == 0 and job_requirements.get("model_complexity") == "high":
            cons.append("No GPU acceleration for complex models")
        
        return cons
    
    def _summarize_quota_constraints(self, quota_status: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize quota constraints affecting recommendations."""
        constraints = {}
        
        remaining_quota = quota_status.get("remaining_quota", {})
        usage_percentages = quota_status.get("usage_percentages", {})
        
        if remaining_quota.get("concurrent_jobs", 1) <= 0:
            constraints["concurrent_jobs"] = "No concurrent job slots available"
        
        if remaining_quota.get("monthly_cost", 100) < 10:
            constraints["budget"] = "Low remaining monthly budget"
        
        if usage_percentages.get("gpu_hours", 0) > 90:
            constraints["gpu_hours"] = "GPU hours quota nearly exhausted"
        
        return constraints
    
    async def allocate_resource_for_job(self, job_id: str, resource_preferences: Dict[str, Any],
                                       db: AsyncSession) -> Dict[str, Any]:
        """Allocate a specific resource for a training job."""
        try:
            # This would integrate with the actual resource allocation system
            # For now, we'll simulate the allocation
            
            resource_id = resource_preferences.get("resource_id")
            if not resource_id:
                return {"success": False, "error": "Resource ID required"}
            
            # Get resource details
            result = await db.execute(
                select(ComputeResource)
                .where(ComputeResource.id == UUID(resource_id))
            )
            resource = result.scalar_one_or_none()
            
            if not resource:
                return {"success": False, "error": "Resource not found"}
            
            if not resource.is_available:
                return {"success": False, "error": "Resource not available"}
            
            if resource.current_usage >= resource.max_concurrent_jobs:
                return {"success": False, "error": "Resource at capacity"}
            
            # Update resource usage
            resource.current_usage += 1
            await db.commit()
            
            self.logger.info(f"Allocated resource {resource_id} for job {job_id}")
            
            return {
                "success": True,
                "resource_id": resource_id,
                "allocation_time": datetime.utcnow().isoformat(),
                "estimated_cost_per_hour": resource.cost_per_hour
            }
            
        except Exception as e:
            self.logger.error(f"Failed to allocate resource: {str(e)}")
            return {"success": False, "error": str(e)}