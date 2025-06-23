"""
ML Model Deployment and Serving Infrastructure
Alphintra Trading Platform - Phase 4
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
import asyncio
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
import pickle
import joblib
import yaml
import docker
import kubernetes
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import hashlib
import shutil
import tempfile
import subprocess

# FastAPI and serving
from fastapi import FastAPI, HTTPException, BackgroundTasks
import uvicorn

# Async libraries
import aiofiles
import aioredis
import asyncpg

# MLflow for model management
import mlflow
import mlflow.sklearn
import mlflow.pytorch
from mlflow.tracking import MlflowClient

# Monitoring
from prometheus_client import Counter, Gauge, Histogram
import psutil

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status enumeration"""
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"
    UPDATING = "updating"


class ModelFormat(Enum):
    """Model format enumeration"""
    SKLEARN = "sklearn"
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    CUSTOM = "custom"


class DeploymentTarget(Enum):
    """Deployment target enumeration"""
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    LOCAL = "local"
    CLOUD_RUN = "cloud_run"
    LAMBDA = "lambda"


@dataclass
class ModelDeploymentConfig:
    """Model deployment configuration"""
    model_id: str
    model_name: str
    model_version: str
    model_format: ModelFormat
    deployment_target: DeploymentTarget
    
    # Resource requirements
    cpu_request: str = "100m"
    cpu_limit: str = "500m"
    memory_request: str = "128Mi"
    memory_limit: str = "512Mi"
    gpu_required: bool = False
    
    # Scaling configuration
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    
    # Serving configuration
    port: int = 8000
    health_check_path: str = "/health"
    metrics_path: str = "/metrics"
    
    # Environment variables
    environment: Dict[str, str] = None
    
    # MLflow configuration
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "model_serving"
    
    def __post_init__(self):
        if self.environment is None:
            self.environment = {}


@dataclass
class DeploymentStatus:
    """Deployment status information"""
    deployment_id: str
    model_id: str
    status: DeploymentStatus
    endpoint_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    health_status: str
    replicas: int
    error_message: Optional[str] = None
    logs: List[str] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []


class ModelPackager:
    """
    Package models for deployment
    """
    
    def __init__(self, output_dir: str = "packaged_models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    async def package_model(self, model_path: str, config: ModelDeploymentConfig) -> str:
        """Package model for deployment"""
        try:
            package_dir = self.output_dir / f"{config.model_id}_{config.model_version}"
            package_dir.mkdir(exist_ok=True)
            
            # Copy model files
            model_path = Path(model_path)
            if model_path.is_file():
                shutil.copy2(model_path, package_dir / "model.pkl")
            elif model_path.is_dir():
                shutil.copytree(model_path, package_dir / "model", dirs_exist_ok=True)
            
            # Create serving code
            await self._create_serving_code(package_dir, config)
            
            # Create requirements.txt
            await self._create_requirements_file(package_dir, config)
            
            # Create Dockerfile
            await self._create_dockerfile(package_dir, config)
            
            # Create Kubernetes manifests
            if config.deployment_target == DeploymentTarget.KUBERNETES:
                await self._create_kubernetes_manifests(package_dir, config)
            
            # Create deployment metadata
            metadata = {
                'model_id': config.model_id,
                'model_name': config.model_name,
                'model_version': config.model_version,
                'model_format': config.model_format.value,
                'created_at': datetime.now().isoformat(),
                'config': asdict(config)
            }
            
            async with aiofiles.open(package_dir / "metadata.json", 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
            
            logger.info(f"Model packaged successfully: {package_dir}")
            return str(package_dir)
            
        except Exception as e:
            logger.error(f"Error packaging model: {str(e)}")
            raise
    
    async def _create_serving_code(self, package_dir: Path, config: ModelDeploymentConfig):
        """Create serving code for the model"""
        serving_code = f'''
import asyncio
import logging
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="{config.model_name} Serving API")

class PredictionRequest(BaseModel):
    features: dict

class PredictionResponse(BaseModel):
    prediction: float
    model_id: str = "{config.model_id}"
    model_version: str = "{config.model_version}"

# Load model on startup
model = None
scaler = None

@app.on_event("startup")
async def load_model():
    global model, scaler
    try:
        # Load main model
        model_path = Path("model.pkl")
        if model_path.exists():
            with open(model_path, "rb") as f:
                model = pickle.load(f)
        
        # Load scaler if exists
        scaler_path = Path("scaler.pkl")
        if scaler_path.exists():
            with open(scaler_path, "rb") as f:
                scaler = pickle.load(f)
        
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {{str(e)}}")
        raise

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        # Convert features to array
        feature_values = list(request.features.values())
        features_array = np.array(feature_values).reshape(1, -1)
        
        # Scale features if scaler available
        if scaler is not None:
            features_array = scaler.transform(features_array)
        
        # Make prediction
        prediction = model.predict(features_array)[0]
        
        return PredictionResponse(prediction=float(prediction))
    
    except Exception as e:
        logger.error(f"Prediction error: {{str(e)}}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {{"status": "healthy", "model_loaded": model is not None}}

@app.get("/metrics")
async def get_metrics():
    # Add Prometheus metrics here
    return {{"predictions_total": 0, "errors_total": 0}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port={config.port})
'''
        
        async with aiofiles.open(package_dir / "main.py", 'w') as f:
            await f.write(serving_code)
    
    async def _create_requirements_file(self, package_dir: Path, config: ModelDeploymentConfig):
        """Create requirements.txt file"""
        requirements = [
            "fastapi>=0.68.0",
            "uvicorn>=0.15.0",
            "pydantic>=1.8.0",
            "numpy>=1.21.0",
            "pandas>=1.3.0",
            "scikit-learn>=1.0.0",
        ]
        
        if config.model_format == ModelFormat.PYTORCH:
            requirements.extend([
                "torch>=1.9.0",
                "torchvision>=0.10.0"
            ])
        elif config.model_format == ModelFormat.TENSORFLOW:
            requirements.append("tensorflow>=2.6.0")
        elif config.model_format == ModelFormat.ONNX:
            requirements.append("onnxruntime>=1.8.0")
        
        async with aiofiles.open(package_dir / "requirements.txt", 'w') as f:
            await f.write('\n'.join(requirements))
    
    async def _create_dockerfile(self, package_dir: Path, config: ModelDeploymentConfig):
        """Create Dockerfile"""
        dockerfile_content = f'''
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE {config.port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:{config.port}/health || exit 1

# Run the application
CMD ["python", "main.py"]
'''
        
        async with aiofiles.open(package_dir / "Dockerfile", 'w') as f:
            await f.write(dockerfile_content)
    
    async def _create_kubernetes_manifests(self, package_dir: Path, config: ModelDeploymentConfig):
        """Create Kubernetes deployment manifests"""
        k8s_dir = package_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)
        
        # Deployment manifest
        deployment_manifest = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': f"{config.model_name}-{config.model_version}",
                'labels': {
                    'app': config.model_name,
                    'version': config.model_version,
                    'model-id': config.model_id
                }
            },
            'spec': {
                'replicas': config.min_replicas,
                'selector': {
                    'matchLabels': {
                        'app': config.model_name,
                        'version': config.model_version
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': config.model_name,
                            'version': config.model_version
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': config.model_name,
                            'image': f"{config.model_name}:{config.model_version}",
                            'ports': [{'containerPort': config.port}],
                            'resources': {
                                'requests': {
                                    'cpu': config.cpu_request,
                                    'memory': config.memory_request
                                },
                                'limits': {
                                    'cpu': config.cpu_limit,
                                    'memory': config.memory_limit
                                }
                            },
                            'livenessProbe': {
                                'httpGet': {
                                    'path': config.health_check_path,
                                    'port': config.port
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': config.health_check_path,
                                    'port': config.port
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            },
                            'env': [
                                {'name': k, 'value': v} 
                                for k, v in config.environment.items()
                            ]
                        }]
                    }
                }
            }
        }
        
        # Service manifest
        service_manifest = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{config.model_name}-service",
                'labels': {
                    'app': config.model_name
                }
            },
            'spec': {
                'selector': {
                    'app': config.model_name
                },
                'ports': [{
                    'port': 80,
                    'targetPort': config.port,
                    'protocol': 'TCP'
                }],
                'type': 'ClusterIP'
            }
        }
        
        # HPA manifest
        hpa_manifest = {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': f"{config.model_name}-hpa"
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': f"{config.model_name}-{config.model_version}"
                },
                'minReplicas': config.min_replicas,
                'maxReplicas': config.max_replicas,
                'metrics': [{
                    'type': 'Resource',
                    'resource': {
                        'name': 'cpu',
                        'target': {
                            'type': 'Utilization',
                            'averageUtilization': config.target_cpu_utilization
                        }
                    }
                }]
            }
        }
        
        # Save manifests
        async with aiofiles.open(k8s_dir / "deployment.yaml", 'w') as f:
            await f.write(yaml.dump(deployment_manifest, default_flow_style=False))
        
        async with aiofiles.open(k8s_dir / "service.yaml", 'w') as f:
            await f.write(yaml.dump(service_manifest, default_flow_style=False))
        
        async with aiofiles.open(k8s_dir / "hpa.yaml", 'w') as f:
            await f.write(yaml.dump(hpa_manifest, default_flow_style=False))


class ModelDeploymentManager:
    """
    Manage model deployments across different targets
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        
        self.packager = ModelPackager()
        self.deployments: Dict[str, DeploymentStatus] = {}
        
        # Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception:
            self.docker_client = None
            logger.warning("Docker client not available")
        
        # Kubernetes client
        try:
            kubernetes.config.load_incluster_config()
            self.k8s_client = kubernetes.client.ApiClient()
        except Exception:
            try:
                kubernetes.config.load_kube_config()
                self.k8s_client = kubernetes.client.ApiClient()
            except Exception:
                self.k8s_client = None
                logger.warning("Kubernetes client not available")
        
        # MLflow client
        self.mlflow_client = None
        
        # Metrics
        self.deployment_counter = Counter('model_deployments_total', 'Total deployments', ['status'])
        self.active_deployments = Gauge('active_deployments', 'Active deployments')
        self.deployment_duration = Histogram('deployment_duration_seconds', 'Deployment duration')
    
    async def initialize(self):
        """Initialize deployment manager"""
        try:
            # Initialize Redis
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Initialize MLflow
            self.mlflow_client = MlflowClient()
            
            logger.info("Model deployment manager initialized")
            
        except Exception as e:
            logger.error(f"Error initializing deployment manager: {str(e)}")
    
    async def deploy_model(self, model_path: str, config: ModelDeploymentConfig) -> str:
        """Deploy a model"""
        deployment_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting deployment {deployment_id} for model {config.model_id}")
            
            # Create deployment status
            deployment_status = DeploymentStatus(
                deployment_id=deployment_id,
                model_id=config.model_id,
                status=DeploymentStatus.PENDING,
                endpoint_url=None,
                created_at=start_time,
                updated_at=start_time,
                health_status="unknown",
                replicas=0
            )
            
            self.deployments[deployment_id] = deployment_status
            await self._update_deployment_status(deployment_status)
            
            # Package model
            deployment_status.status = DeploymentStatus.BUILDING
            await self._update_deployment_status(deployment_status)
            
            package_path = await self.packager.package_model(model_path, config)
            
            # Deploy based on target
            if config.deployment_target == DeploymentTarget.DOCKER:
                endpoint_url = await self._deploy_docker(package_path, config)
            elif config.deployment_target == DeploymentTarget.KUBERNETES:
                endpoint_url = await self._deploy_kubernetes(package_path, config)
            elif config.deployment_target == DeploymentTarget.LOCAL:
                endpoint_url = await self._deploy_local(package_path, config)
            else:
                raise ValueError(f"Unsupported deployment target: {config.deployment_target}")
            
            # Update deployment status
            deployment_status.status = DeploymentStatus.RUNNING
            deployment_status.endpoint_url = endpoint_url
            deployment_status.updated_at = datetime.now()
            await self._update_deployment_status(deployment_status)
            
            # Update metrics
            duration = (datetime.now() - start_time).total_seconds()
            self.deployment_duration.observe(duration)
            self.deployment_counter.labels(status='success').inc()
            
            logger.info(f"Deployment {deployment_id} completed successfully at {endpoint_url}")
            return deployment_id
            
        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed: {str(e)}")
            
            # Update deployment status
            deployment_status.status = DeploymentStatus.FAILED
            deployment_status.error_message = str(e)
            deployment_status.updated_at = datetime.now()
            await self._update_deployment_status(deployment_status)
            
            self.deployment_counter.labels(status='failed').inc()
            raise
    
    async def _deploy_docker(self, package_path: str, config: ModelDeploymentConfig) -> str:
        """Deploy model using Docker"""
        try:
            if not self.docker_client:
                raise RuntimeError("Docker client not available")
            
            package_dir = Path(package_path)
            image_name = f"{config.model_name}:{config.model_version}"
            
            # Build Docker image
            logger.info(f"Building Docker image: {image_name}")
            image, build_logs = self.docker_client.images.build(
                path=str(package_dir),
                tag=image_name,
                rm=True
            )
            
            # Run container
            container_name = f"{config.model_name}-{config.model_version}-{uuid.uuid4().hex[:8]}"
            
            container = self.docker_client.containers.run(
                image_name,
                name=container_name,
                ports={f'{config.port}/tcp': None},  # Random host port
                environment=config.environment,
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            # Get host port
            container.reload()
            host_port = container.ports[f'{config.port}/tcp'][0]['HostPort']
            endpoint_url = f"http://localhost:{host_port}"
            
            logger.info(f"Docker container {container_name} started at {endpoint_url}")
            return endpoint_url
            
        except Exception as e:
            logger.error(f"Docker deployment failed: {str(e)}")
            raise
    
    async def _deploy_kubernetes(self, package_path: str, config: ModelDeploymentConfig) -> str:
        """Deploy model to Kubernetes"""
        try:
            if not self.k8s_client:
                raise RuntimeError("Kubernetes client not available")
            
            package_dir = Path(package_path)
            k8s_dir = package_dir / "k8s"
            
            # Apply Kubernetes manifests
            apps_v1 = kubernetes.client.AppsV1Api(self.k8s_client)
            core_v1 = kubernetes.client.CoreV1Api(self.k8s_client)
            autoscaling_v2 = kubernetes.client.AutoscalingV2Api(self.k8s_client)
            
            # Load manifests
            with open(k8s_dir / "deployment.yaml", 'r') as f:
                deployment_manifest = yaml.safe_load(f)
            
            with open(k8s_dir / "service.yaml", 'r') as f:
                service_manifest = yaml.safe_load(f)
            
            with open(k8s_dir / "hpa.yaml", 'r') as f:
                hpa_manifest = yaml.safe_load(f)
            
            # Create deployment
            apps_v1.create_namespaced_deployment(
                namespace="default",
                body=deployment_manifest
            )
            
            # Create service
            core_v1.create_namespaced_service(
                namespace="default",
                body=service_manifest
            )
            
            # Create HPA
            autoscaling_v2.create_namespaced_horizontal_pod_autoscaler(
                namespace="default",
                body=hpa_manifest
            )
            
            # Endpoint URL (internal cluster address)
            service_name = service_manifest['metadata']['name']
            endpoint_url = f"http://{service_name}.default.svc.cluster.local"
            
            logger.info(f"Kubernetes deployment created at {endpoint_url}")
            return endpoint_url
            
        except Exception as e:
            logger.error(f"Kubernetes deployment failed: {str(e)}")
            raise
    
    async def _deploy_local(self, package_path: str, config: ModelDeploymentConfig) -> str:
        """Deploy model locally"""
        try:
            package_dir = Path(package_path)
            
            # Start the server process
            process = await asyncio.create_subprocess_exec(
                "python", "main.py",
                cwd=package_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Give it time to start
            await asyncio.sleep(2)
            
            if process.returncode is not None:
                # Process failed to start
                stdout, stderr = await process.communicate()
                raise RuntimeError(f"Failed to start local server: {stderr.decode()}")
            
            endpoint_url = f"http://localhost:{config.port}"
            logger.info(f"Local deployment started at {endpoint_url}")
            return endpoint_url
            
        except Exception as e:
            logger.error(f"Local deployment failed: {str(e)}")
            raise
    
    async def _update_deployment_status(self, deployment_status: DeploymentStatus):
        """Update deployment status in storage"""
        try:
            if self.redis_client:
                status_data = asdict(deployment_status)
                status_data['created_at'] = deployment_status.created_at.isoformat()
                status_data['updated_at'] = deployment_status.updated_at.isoformat()
                
                await self.redis_client.setex(
                    f"deployment:{deployment_status.deployment_id}",
                    86400,  # 24 hours
                    json.dumps(status_data, default=str)
                )
        except Exception as e:
            logger.error(f"Error updating deployment status: {str(e)}")
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentStatus]:
        """Get deployment status"""
        return self.deployments.get(deployment_id)
    
    async def list_deployments(self) -> List[DeploymentStatus]:
        """List all deployments"""
        return list(self.deployments.values())
    
    async def stop_deployment(self, deployment_id: str) -> bool:
        """Stop a deployment"""
        try:
            deployment = self.deployments.get(deployment_id)
            if not deployment:
                return False
            
            # Stop based on deployment target
            # This would need implementation for each target
            deployment.status = DeploymentStatus.STOPPED
            deployment.updated_at = datetime.now()
            await self._update_deployment_status(deployment)
            
            logger.info(f"Deployment {deployment_id} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping deployment {deployment_id}: {str(e)}")
            return False
    
    async def health_check_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Check deployment health"""
        try:
            deployment = self.deployments.get(deployment_id)
            if not deployment or not deployment.endpoint_url:
                return {"status": "unknown", "error": "Deployment not found"}
            
            # Make health check request
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{deployment.endpoint_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        deployment.health_status = "healthy"
                        return {"status": "healthy", "data": health_data}
                    else:
                        deployment.health_status = "unhealthy"
                        return {"status": "unhealthy", "status_code": response.status}
        
        except Exception as e:
            deployment.health_status = "error"
            return {"status": "error", "error": str(e)}
    
    def get_deployment_metrics(self) -> Dict[str, Any]:
        """Get deployment metrics"""
        active_count = len([d for d in self.deployments.values() 
                           if d.status == DeploymentStatus.RUNNING])
        
        self.active_deployments.set(active_count)
        
        return {
            'total_deployments': len(self.deployments),
            'active_deployments': active_count,
            'failed_deployments': len([d for d in self.deployments.values() 
                                     if d.status == DeploymentStatus.FAILED]),
            'deployment_targets': list(set(d.status.value for d in self.deployments.values()))
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.docker_client:
            self.docker_client.close()


# Example usage and testing
if __name__ == "__main__":
    async def test_model_deployment():
        """Test model deployment system"""
        
        # Create a simple test model
        from sklearn.linear_model import LinearRegression
        import numpy as np
        
        # Train a simple model
        X = np.random.randn(100, 5)
        y = np.sum(X, axis=1) + np.random.randn(100) * 0.1
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Save model
        model_dir = Path("test_model")
        model_dir.mkdir(exist_ok=True)
        
        with open(model_dir / "model.pkl", "wb") as f:
            pickle.dump(model, f)
        
        # Create deployment config
        config = ModelDeploymentConfig(
            model_id="test_model_001",
            model_name="test-linear-model",
            model_version="v1.0.0",
            model_format=ModelFormat.SKLEARN,
            deployment_target=DeploymentTarget.LOCAL,
            port=8001
        )
        
        # Initialize deployment manager
        manager = ModelDeploymentManager()
        await manager.initialize()
        
        try:
            # Deploy model
            print("Deploying test model...")
            deployment_id = await manager.deploy_model(str(model_dir), config)
            
            print(f"Deployment ID: {deployment_id}")
            
            # Check deployment status
            deployment_status = await manager.get_deployment_status(deployment_id)
            print(f"Deployment Status: {deployment_status.status.value}")
            print(f"Endpoint URL: {deployment_status.endpoint_url}")
            
            # Health check
            await asyncio.sleep(5)  # Wait for service to start
            health_result = await manager.health_check_deployment(deployment_id)
            print(f"Health Check: {health_result}")
            
            # Test prediction (if service is running)
            if deployment_status.endpoint_url and health_result.get("status") == "healthy":
                import aiohttp
                
                test_features = {f"feature_{i}": float(np.random.randn()) for i in range(5)}
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{deployment_status.endpoint_url}/predict",
                        json={"features": test_features}
                    ) as response:
                        if response.status == 200:
                            prediction_result = await response.json()
                            print(f"Test Prediction: {prediction_result}")
                        else:
                            print(f"Prediction failed with status: {response.status}")
            
            # Get metrics
            metrics = manager.get_deployment_metrics()
            print(f"Deployment Metrics: {metrics}")
            
            # List all deployments
            deployments = await manager.list_deployments()
            print(f"Total Deployments: {len(deployments)}")
            
        finally:
            # Cleanup
            await manager.cleanup()
            
            # Clean up test files
            shutil.rmtree(model_dir, ignore_errors=True)
            shutil.rmtree("packaged_models", ignore_errors=True)
        
        print("Model deployment test completed!")
    
    # Run the test
    asyncio.run(test_model_deployment())