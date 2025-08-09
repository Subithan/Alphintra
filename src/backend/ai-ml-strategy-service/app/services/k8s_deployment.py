"""
Kubernetes Model Serving Service - Deploy trained models as scalable prediction services
"""

import os
import json
import yaml
import tempfile
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import asyncio
import aiofiles
import docker
from dataclasses import dataclass

from kubernetes import client, config
from kubernetes.client.rest import ApiException
import boto3
from google.cloud import storage as gcs
from jinja2 import Template

from app.models.model_registry import ModelVersion, ModelDeployment, DeploymentStatus
from app.services.model_registry import model_registry
from app.core.database import get_db_session
from app.core.config import get_settings
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DeploymentConfig:
    """Configuration for model deployment"""
    model_version_id: int
    deployment_name: str
    environment: str
    cpu_request: str = "500m"
    cpu_limit: str = "2000m"
    memory_request: str = "1Gi"
    memory_limit: str = "4Gi"
    gpu_request: int = 0
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    target_rps: Optional[int] = None
    serving_framework: str = "fastapi"
    api_version: str = "v1"
    custom_config: Optional[Dict] = None


@dataclass
class DeploymentResult:
    """Result of deployment operation"""
    success: bool
    deployment_id: Optional[int] = None
    endpoint_url: Optional[str] = None
    error_message: Optional[str] = None
    k8s_objects: Optional[List[str]] = None


class KubernetesModelDeployment:
    """
    Service for deploying ML models to Kubernetes clusters with auto-scaling and monitoring
    """
    
    def __init__(self):
        # Initialize Kubernetes client
        try:
            if settings.KUBERNETES_CONFIG_PATH:
                config.load_kube_config(config_file=settings.KUBERNETES_CONFIG_PATH)
            else:
                config.load_incluster_config()  # For running inside cluster
        except Exception as e:
            logger.warning(f"Could not load Kubernetes config: {e}")
            
        self.k8s_apps = client.AppsV1Api()
        self.k8s_core = client.CoreV1Api() 
        self.k8s_networking = client.NetworkingV1Api()
        self.k8s_autoscaling = client.AutoscalingV2Api()
        
        # Initialize container registry
        self.container_registry = settings.CONTAINER_REGISTRY or "gcr.io/alphintra"
        self.registry_prefix = f"{self.container_registry}/model-serving"
        
        # Initialize Docker client for image building
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Could not initialize Docker client: {e}")
            self.docker_client = None
        
        # Default namespace for model deployments
        self.namespace = settings.MODEL_SERVING_NAMESPACE or "alphintra-models"
        
        # Templates directory
        self.templates_dir = Path(__file__).parent.parent / "templates" / "k8s"

    async def deploy_model(
        self,
        config: DeploymentConfig,
        user_id: int,
        db_session: Session = None
    ) -> DeploymentResult:
        """
        Deploy a model version to Kubernetes cluster
        """
        if not db_session:
            db_session = next(get_db_session())
            
        try:
            logger.info(f"Starting deployment for model version {config.model_version_id}")
            
            # Get model version
            model_version = db_session.query(ModelVersion).get(config.model_version_id)
            if not model_version:
                return DeploymentResult(
                    success=False,
                    error_message=f"Model version {config.model_version_id} not found"
                )
            
            # Check if model is deployment ready
            if not model_version.deployment_ready:
                return DeploymentResult(
                    success=False,
                    error_message=f"Model version {config.model_version_id} is not deployment ready"
                )
            
            # Create deployment record
            deployment = ModelDeployment(
                model_id=model_version.model_id,
                model_version_id=config.model_version_id,
                deployment_name=config.deployment_name,
                environment=config.environment,
                serving_framework=config.serving_framework,
                api_version=config.api_version,
                cpu_request=config.cpu_request,
                cpu_limit=config.cpu_limit,
                memory_request=config.memory_request,
                memory_limit=config.memory_limit,
                gpu_request=config.gpu_request,
                min_replicas=config.min_replicas,
                max_replicas=config.max_replicas,
                target_cpu_utilization=config.target_cpu_utilization,
                target_rps=config.target_rps,
                k8s_namespace=self.namespace,
                k8s_deployment_name=f"{config.deployment_name}-deployment",
                k8s_service_name=f"{config.deployment_name}-service",
                status=DeploymentStatus.PENDING
            )
            
            db_session.add(deployment)
            db_session.flush()
            
            # Build and push container image
            image_tag = await self._build_model_image(model_version, deployment)
            if not image_tag:
                deployment.status = DeploymentStatus.FAILED
                deployment.deployment_status_message = "Failed to build container image"
                db_session.commit()
                return DeploymentResult(
                    success=False,
                    error_message="Failed to build container image"
                )
            
            # Deploy to Kubernetes
            k8s_objects = await self._deploy_to_k8s(deployment, image_tag, config)
            if not k8s_objects:
                deployment.status = DeploymentStatus.FAILED
                deployment.deployment_status_message = "Failed to create Kubernetes resources"
                db_session.commit()
                return DeploymentResult(
                    success=False,
                    error_message="Failed to create Kubernetes resources"
                )
            
            # Wait for deployment to be ready
            deployment_ready = await self._wait_for_deployment(deployment.k8s_deployment_name)
            if not deployment_ready:
                deployment.status = DeploymentStatus.FAILED
                deployment.deployment_status_message = "Deployment failed to become ready"
                db_session.commit()
                return DeploymentResult(
                    success=False,
                    error_message="Deployment failed to become ready"
                )
            
            # Get service endpoint
            endpoint_url = await self._get_service_endpoint(deployment.k8s_service_name)
            
            # Update deployment record
            deployment.status = DeploymentStatus.DEPLOYED
            deployment.endpoint_url = endpoint_url
            deployment.deployed_at = datetime.utcnow()
            deployment.k8s_config = {"objects": k8s_objects}
            deployment.deployment_status_message = "Successfully deployed"
            
            db_session.commit()
            
            logger.info(f"Successfully deployed model {config.deployment_name} at {endpoint_url}")
            
            return DeploymentResult(
                success=True,
                deployment_id=deployment.id,
                endpoint_url=endpoint_url,
                k8s_objects=k8s_objects
            )
            
        except Exception as e:
            logger.error(f"Failed to deploy model: {str(e)}")
            if 'deployment' in locals():
                deployment.status = DeploymentStatus.FAILED
                deployment.deployment_status_message = f"Deployment error: {str(e)}"
                db_session.commit()
            
            return DeploymentResult(
                success=False,
                error_message=f"Deployment error: {str(e)}"
            )

    async def scale_deployment(
        self,
        deployment_id: int,
        min_replicas: int,
        max_replicas: int,
        db_session: Session = None
    ) -> bool:
        """Scale existing deployment"""
        if not db_session:
            db_session = next(get_db_session())
            
        try:
            deployment = db_session.query(ModelDeployment).get(deployment_id)
            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")
            
            # Update HPA
            hpa_name = f"{deployment.deployment_name}-hpa"
            try:
                hpa = self.k8s_autoscaling.read_namespaced_horizontal_pod_autoscaler(
                    name=hpa_name,
                    namespace=self.namespace
                )
                hpa.spec.min_replicas = min_replicas
                hpa.spec.max_replicas = max_replicas
                
                self.k8s_autoscaling.patch_namespaced_horizontal_pod_autoscaler(
                    name=hpa_name,
                    namespace=self.namespace,
                    body=hpa
                )
                
                # Update database
                deployment.min_replicas = min_replicas
                deployment.max_replicas = max_replicas
                db_session.commit()
                
                logger.info(f"Scaled deployment {deployment_id} to {min_replicas}-{max_replicas} replicas")
                return True
                
            except ApiException as e:
                logger.error(f"Failed to scale deployment: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error scaling deployment: {str(e)}")
            return False

    async def update_deployment(
        self,
        deployment_id: int,
        new_model_version_id: int,
        strategy: str = "rolling",
        db_session: Session = None
    ) -> bool:
        """Update deployment with new model version"""
        if not db_session:
            db_session = next(get_db_session())
            
        try:
            deployment = db_session.query(ModelDeployment).get(deployment_id)
            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")
            
            new_model_version = db_session.query(ModelVersion).get(new_model_version_id)
            if not new_model_version or not new_model_version.deployment_ready:
                raise ValueError(f"Model version {new_model_version_id} not ready for deployment")
            
            deployment.status = DeploymentStatus.UPDATING
            db_session.commit()
            
            # Build new image
            new_image_tag = await self._build_model_image(new_model_version, deployment)
            if not new_image_tag:
                deployment.status = DeploymentStatus.FAILED
                deployment.deployment_status_message = "Failed to build new image"
                db_session.commit()
                return False
            
            # Update Kubernetes deployment
            try:
                k8s_deployment = self.k8s_apps.read_namespaced_deployment(
                    name=deployment.k8s_deployment_name,
                    namespace=self.namespace
                )
                
                # Update image
                k8s_deployment.spec.template.spec.containers[0].image = new_image_tag
                
                # Update deployment
                self.k8s_apps.patch_namespaced_deployment(
                    name=deployment.k8s_deployment_name,
                    namespace=self.namespace,
                    body=k8s_deployment
                )
                
                # Wait for rollout to complete
                rollout_success = await self._wait_for_rollout(deployment.k8s_deployment_name)
                
                if rollout_success:
                    deployment.model_version_id = new_model_version_id
                    deployment.status = DeploymentStatus.DEPLOYED
                    deployment.deployment_status_message = "Successfully updated"
                    deployment.last_updated = datetime.utcnow()
                else:
                    deployment.status = DeploymentStatus.FAILED
                    deployment.deployment_status_message = "Update rollout failed"
                
                db_session.commit()
                return rollout_success
                
            except ApiException as e:
                logger.error(f"Failed to update deployment: {e}")
                deployment.status = DeploymentStatus.FAILED
                deployment.deployment_status_message = f"K8s update error: {str(e)}"
                db_session.commit()
                return False
                
        except Exception as e:
            logger.error(f"Error updating deployment: {str(e)}")
            return False

    async def delete_deployment(
        self,
        deployment_id: int,
        db_session: Session = None
    ) -> bool:
        """Delete deployment and cleanup Kubernetes resources"""
        if not db_session:
            db_session = next(get_db_session())
            
        try:
            deployment = db_session.query(ModelDeployment).get(deployment_id)
            if not deployment:
                return False
            
            deployment.status = DeploymentStatus.STOPPING
            db_session.commit()
            
            # Delete Kubernetes resources
            resources_deleted = await self._cleanup_k8s_resources(deployment)
            
            if resources_deleted:
                deployment.status = DeploymentStatus.STOPPED
                deployment.is_active = False
                deployment.deployment_status_message = "Successfully deleted"
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.deployment_status_message = "Failed to cleanup resources"
            
            db_session.commit()
            return resources_deleted
            
        except Exception as e:
            logger.error(f"Error deleting deployment: {str(e)}")
            return False

    async def get_deployment_status(
        self,
        deployment_id: int,
        db_session: Session = None
    ) -> Dict[str, Any]:
        """Get detailed deployment status"""
        if not db_session:
            db_session = next(get_db_session())
            
        deployment = db_session.query(ModelDeployment).get(deployment_id)
        if not deployment:
            return {"error": "Deployment not found"}
        
        try:
            # Get Kubernetes deployment status
            k8s_deployment = self.k8s_apps.read_namespaced_deployment(
                name=deployment.k8s_deployment_name,
                namespace=self.namespace
            )
            
            # Get pods status
            pods = self.k8s_core.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"app={deployment.deployment_name}"
            )
            
            # Get service status
            service = self.k8s_core.read_namespaced_service(
                name=deployment.k8s_service_name,
                namespace=self.namespace
            )
            
            return {
                "deployment_id": deployment_id,
                "status": deployment.status,
                "endpoint_url": deployment.endpoint_url,
                "replicas": {
                    "desired": k8s_deployment.spec.replicas,
                    "available": k8s_deployment.status.available_replicas or 0,
                    "ready": k8s_deployment.status.ready_replicas or 0,
                    "updated": k8s_deployment.status.updated_replicas or 0
                },
                "pods": [
                    {
                        "name": pod.metadata.name,
                        "status": pod.status.phase,
                        "ready": all(c.status for c in pod.status.conditions if c.type == "Ready")
                    }
                    for pod in pods.items
                ],
                "service": {
                    "cluster_ip": service.spec.cluster_ip,
                    "ports": [
                        {"port": port.port, "target_port": port.target_port}
                        for port in service.spec.ports
                    ]
                },
                "last_updated": deployment.last_updated.isoformat() if deployment.last_updated else None
            }
            
        except Exception as e:
            logger.error(f"Error getting deployment status: {str(e)}")
            return {
                "deployment_id": deployment_id,
                "status": deployment.status,
                "error": str(e)
            }

    # Private helper methods
    
    async def _build_model_image(
        self,
        model_version: ModelVersion,
        deployment: ModelDeployment
    ) -> Optional[str]:
        """Build Docker image for model serving"""
        try:
            if not self.docker_client:
                logger.error("Docker client not available")
                return None
            
            # Download model artifacts
            local_artifacts_path = await model_registry.download_model_artifacts(model_version)
            
            # Create temporary directory for build context
            with tempfile.TemporaryDirectory() as build_context:
                build_context_path = Path(build_context)
                
                # Copy model artifacts
                artifacts_dir = build_context_path / "artifacts"
                artifacts_dir.mkdir()
                
                # Extract artifacts
                import tarfile
                with tarfile.open(local_artifacts_path, "r:gz") as tar:
                    tar.extractall(artifacts_dir)
                
                # Generate serving code
                serving_code = await self._generate_serving_code(
                    model_version, deployment.serving_framework
                )
                
                # Write serving code
                (build_context_path / "main.py").write_text(serving_code)
                
                # Generate Dockerfile
                dockerfile = await self._generate_dockerfile(
                    model_version, deployment.serving_framework
                )
                (build_context_path / "Dockerfile").write_text(dockerfile)
                
                # Generate requirements.txt
                requirements = await self._generate_requirements(
                    model_version, deployment.serving_framework
                )
                (build_context_path / "requirements.txt").write_text(requirements)
                
                # Build image
                image_tag = f"{self.registry_prefix}:{model_version.model.name}-{model_version.version}"
                
                logger.info(f"Building Docker image: {image_tag}")
                image, build_logs = self.docker_client.images.build(
                    path=str(build_context_path),
                    tag=image_tag,
                    dockerfile="Dockerfile",
                    rm=True
                )
                
                # Push image to registry
                push_logs = self.docker_client.images.push(image_tag)
                logger.info(f"Pushed image to registry: {image_tag}")
                
                return image_tag
                
        except Exception as e:
            logger.error(f"Failed to build model image: {str(e)}")
            return None

    async def _deploy_to_k8s(
        self,
        deployment: ModelDeployment,
        image_tag: str,
        config: DeploymentConfig
    ) -> Optional[List[str]]:
        """Deploy model to Kubernetes"""
        try:
            k8s_objects = []
            
            # Create namespace if it doesn't exist
            try:
                self.k8s_core.read_namespace(self.namespace)
            except ApiException as e:
                if e.status == 404:
                    namespace_manifest = client.V1Namespace(
                        metadata=client.V1ObjectMeta(name=self.namespace)
                    )
                    self.k8s_core.create_namespace(namespace_manifest)
                    k8s_objects.append(f"namespace/{self.namespace}")
            
            # Create deployment
            deployment_manifest = await self._generate_deployment_manifest(
                deployment, image_tag, config
            )
            self.k8s_apps.create_namespaced_deployment(
                namespace=self.namespace,
                body=deployment_manifest
            )
            k8s_objects.append(f"deployment/{deployment.k8s_deployment_name}")
            
            # Create service
            service_manifest = await self._generate_service_manifest(deployment, config)
            self.k8s_core.create_namespaced_service(
                namespace=self.namespace,
                body=service_manifest
            )
            k8s_objects.append(f"service/{deployment.k8s_service_name}")
            
            # Create HPA (Horizontal Pod Autoscaler)
            hpa_manifest = await self._generate_hpa_manifest(deployment, config)
            self.k8s_autoscaling.create_namespaced_horizontal_pod_autoscaler(
                namespace=self.namespace,
                body=hpa_manifest
            )
            k8s_objects.append(f"hpa/{deployment.deployment_name}-hpa")
            
            # Create ingress (optional)
            if settings.CREATE_INGRESS_FOR_MODELS:
                ingress_manifest = await self._generate_ingress_manifest(deployment, config)
                self.k8s_networking.create_namespaced_ingress(
                    namespace=self.namespace,
                    body=ingress_manifest
                )
                k8s_objects.append(f"ingress/{deployment.deployment_name}-ingress")
            
            return k8s_objects
            
        except Exception as e:
            logger.error(f"Failed to deploy to Kubernetes: {str(e)}")
            return None

    async def _wait_for_deployment(self, deployment_name: str, timeout: int = 300) -> bool:
        """Wait for deployment to be ready"""
        import asyncio
        
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).seconds < timeout:
            try:
                deployment = self.k8s_apps.read_namespaced_deployment(
                    name=deployment_name,
                    namespace=self.namespace
                )
                
                if deployment.status.ready_replicas and \
                   deployment.status.ready_replicas >= deployment.spec.replicas:
                    return True
                    
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.warning(f"Error checking deployment status: {e}")
                await asyncio.sleep(5)
        
        return False

    async def _wait_for_rollout(self, deployment_name: str, timeout: int = 300) -> bool:
        """Wait for deployment rollout to complete"""
        import asyncio
        
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).seconds < timeout:
            try:
                deployment = self.k8s_apps.read_namespaced_deployment(
                    name=deployment_name,
                    namespace=self.namespace
                )
                
                # Check if rollout is complete
                if deployment.status.updated_replicas == deployment.spec.replicas and \
                   deployment.status.replicas == deployment.spec.replicas and \
                   deployment.status.available_replicas == deployment.spec.replicas:
                    return True
                    
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.warning(f"Error checking rollout status: {e}")
                await asyncio.sleep(5)
        
        return False

    async def _get_service_endpoint(self, service_name: str) -> Optional[str]:
        """Get service endpoint URL"""
        try:
            service = self.k8s_core.read_namespaced_service(
                name=service_name,
                namespace=self.namespace
            )
            
            if service.spec.type == "LoadBalancer":
                if service.status.load_balancer.ingress:
                    ip = service.status.load_balancer.ingress[0].ip
                    port = service.spec.ports[0].port
                    return f"http://{ip}:{port}"
            
            # For ClusterIP or NodePort, return internal cluster URL
            cluster_ip = service.spec.cluster_ip
            port = service.spec.ports[0].port
            return f"http://{cluster_ip}:{port}"
            
        except Exception as e:
            logger.error(f"Failed to get service endpoint: {e}")
            return None

    async def _cleanup_k8s_resources(self, deployment: ModelDeployment) -> bool:
        """Cleanup all Kubernetes resources for deployment"""
        try:
            success = True
            
            # Delete HPA
            try:
                self.k8s_autoscaling.delete_namespaced_horizontal_pod_autoscaler(
                    name=f"{deployment.deployment_name}-hpa",
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:  # Ignore not found errors
                    logger.warning(f"Failed to delete HPA: {e}")
                    success = False
            
            # Delete ingress
            try:
                self.k8s_networking.delete_namespaced_ingress(
                    name=f"{deployment.deployment_name}-ingress",
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:
                    logger.warning(f"Failed to delete ingress: {e}")
            
            # Delete service
            try:
                self.k8s_core.delete_namespaced_service(
                    name=deployment.k8s_service_name,
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:
                    logger.warning(f"Failed to delete service: {e}")
                    success = False
            
            # Delete deployment
            try:
                self.k8s_apps.delete_namespaced_deployment(
                    name=deployment.k8s_deployment_name,
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:
                    logger.warning(f"Failed to delete deployment: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error cleaning up resources: {str(e)}")
            return False

    async def _generate_serving_code(self, model_version: ModelVersion, framework: str) -> str:
        """Generate serving application code"""
        if framework == "fastapi":
            return f'''
import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

app = FastAPI(title="{model_version.model.name} Prediction Service")

# Load model on startup
model = None

@app.on_event("startup")
async def load_model():
    global model
    model_path = "/app/artifacts/model.pkl"
    if os.path.exists(model_path):
        model = joblib.load(model_path)
    else:
        raise RuntimeError("Model file not found")

class PredictionRequest(BaseModel):
    features: Dict[str, Any]

class PredictionResponse(BaseModel):
    prediction: float
    probability: float = None
    confidence: float = None

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Convert features to DataFrame
        df = pd.DataFrame([request.features])
        
        # Make prediction
        prediction = model.predict(df)[0]
        
        # Get probability if available
        probability = None
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(df)[0]
            probability = float(max(proba))
        
        return PredictionResponse(
            prediction=float(prediction),
            probability=probability
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {{str(e)}}")

@app.get("/health")
async def health_check():
    return {{"status": "healthy", "model_loaded": model is not None}}

@app.get("/info")
async def model_info():
    return {{
        "model_name": "{model_version.model.name}",
        "model_version": "{model_version.version}",
        "framework": "{model_version.model.framework}",
        "model_type": "{model_version.model.model_type}"
    }}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        else:
            return "# Unsupported serving framework"

    async def _generate_dockerfile(self, model_version: ModelVersion, framework: str) -> str:
        """Generate Dockerfile for model serving"""
        if framework == "fastapi":
            return f'''
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and model artifacts
COPY main.py .
COPY artifacts/ artifacts/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "main.py"]
'''
        else:
            return "# Unsupported framework"

    async def _generate_requirements(self, model_version: ModelVersion, framework: str) -> str:
        """Generate requirements.txt for model serving"""
        base_requirements = [
            "pandas>=1.3.0",
            "numpy>=1.21.0",
            "scikit-learn>=1.0.0",
        ]
        
        if framework == "fastapi":
            base_requirements.extend([
                "fastapi>=0.70.0",
                "uvicorn[standard]>=0.15.0",
                "pydantic>=1.8.0"
            ])
        
        # Add framework-specific requirements
        if model_version.model.framework == "tensorflow":
            base_requirements.append("tensorflow>=2.8.0")
        elif model_version.model.framework == "pytorch":
            base_requirements.append("torch>=1.11.0")
        elif model_version.model.framework == "xgboost":
            base_requirements.append("xgboost>=1.5.0")
        
        base_requirements.append("joblib>=1.1.0")
        
        return "\\n".join(base_requirements)

    async def _generate_deployment_manifest(
        self,
        deployment: ModelDeployment,
        image_tag: str,
        config: DeploymentConfig
    ) -> client.V1Deployment:
        """Generate Kubernetes deployment manifest"""
        
        # Container spec
        container = client.V1Container(
            name="model-server",
            image=image_tag,
            ports=[client.V1ContainerPort(container_port=8000)],
            resources=client.V1ResourceRequirements(
                requests={
                    "cpu": config.cpu_request,
                    "memory": config.memory_request
                },
                limits={
                    "cpu": config.cpu_limit,
                    "memory": config.memory_limit
                }
            ),
            liveness_probe=client.V1Probe(
                http_get=client.V1HTTPGetAction(path="/health", port=8000),
                initial_delay_seconds=30,
                period_seconds=10
            ),
            readiness_probe=client.V1Probe(
                http_get=client.V1HTTPGetAction(path="/health", port=8000),
                initial_delay_seconds=5,
                period_seconds=5
            )
        )
        
        # Add GPU resources if requested
        if config.gpu_request > 0:
            if container.resources.requests is None:
                container.resources.requests = {}
            if container.resources.limits is None:
                container.resources.limits = {}
            
            container.resources.requests["nvidia.com/gpu"] = str(config.gpu_request)
            container.resources.limits["nvidia.com/gpu"] = str(config.gpu_request)
        
        # Pod template
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={"app": deployment.deployment_name}
            ),
            spec=client.V1PodSpec(containers=[container])
        )
        
        # Deployment spec
        spec = client.V1DeploymentSpec(
            replicas=config.min_replicas,
            selector=client.V1LabelSelector(
                match_labels={"app": deployment.deployment_name}
            ),
            template=template
        )
        
        # Deployment
        return client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=deployment.k8s_deployment_name,
                labels={"app": deployment.deployment_name}
            ),
            spec=spec
        )

    async def _generate_service_manifest(
        self,
        deployment: ModelDeployment,
        config: DeploymentConfig
    ) -> client.V1Service:
        """Generate Kubernetes service manifest"""
        
        return client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=deployment.k8s_service_name,
                labels={"app": deployment.deployment_name}
            ),
            spec=client.V1ServiceSpec(
                selector={"app": deployment.deployment_name},
                ports=[
                    client.V1ServicePort(
                        port=80,
                        target_port=8000,
                        protocol="TCP"
                    )
                ],
                type="ClusterIP"
            )
        )

    async def _generate_hpa_manifest(
        self,
        deployment: ModelDeployment,
        config: DeploymentConfig
    ) -> client.V2HorizontalPodAutoscaler:
        """Generate Horizontal Pod Autoscaler manifest"""
        
        metrics = [
            client.V2MetricSpec(
                type="Resource",
                resource=client.V2ResourceMetricSource(
                    name="cpu",
                    target=client.V2MetricTarget(
                        type="Utilization",
                        average_utilization=config.target_cpu_utilization
                    )
                )
            )
        ]
        
        # Add RPS metric if specified
        if config.target_rps:
            metrics.append(
                client.V2MetricSpec(
                    type="Pods",
                    pods=client.V2PodsMetricSource(
                        metric=client.V2MetricIdentifier(
                            name="requests_per_second"
                        ),
                        target=client.V2MetricTarget(
                            type="AverageValue",
                            average_value=str(config.target_rps)
                        )
                    )
                )
            )
        
        return client.V2HorizontalPodAutoscaler(
            api_version="autoscaling/v2",
            kind="HorizontalPodAutoscaler",
            metadata=client.V1ObjectMeta(
                name=f"{deployment.deployment_name}-hpa"
            ),
            spec=client.V2HorizontalPodAutoscalerSpec(
                scale_target_ref=client.V2CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=deployment.k8s_deployment_name
                ),
                min_replicas=config.min_replicas,
                max_replicas=config.max_replicas,
                metrics=metrics
            )
        )

    async def _generate_ingress_manifest(
        self,
        deployment: ModelDeployment,
        config: DeploymentConfig
    ) -> client.V1Ingress:
        """Generate Ingress manifest for external access"""
        
        return client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=f"{deployment.deployment_name}-ingress",
                annotations={
                    "nginx.ingress.kubernetes.io/rewrite-target": "/",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod"
                }
            ),
            spec=client.V1IngressSpec(
                tls=[
                    client.V1IngressTLS(
                        hosts=[f"{deployment.deployment_name}.{settings.INGRESS_DOMAIN}"],
                        secret_name=f"{deployment.deployment_name}-tls"
                    )
                ],
                rules=[
                    client.V1IngressRule(
                        host=f"{deployment.deployment_name}.{settings.INGRESS_DOMAIN}",
                        http=client.V1HTTPIngressRuleValue(
                            paths=[
                                client.V1HTTPIngressPath(
                                    path="/",
                                    path_type="Prefix",
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            name=deployment.k8s_service_name,
                                            port=client.V1ServiceBackendPort(number=80)
                                        )
                                    )
                                )
                            ]
                        )
                    )
                ]
            )
        )


# Global instance
k8s_deployment_service = KubernetesModelDeployment()