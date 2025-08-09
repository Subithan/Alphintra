"""
Model Registry Service - Manages ML model versions, artifacts, and metadata
"""

import os
import json
import hashlib
import shutil
import tarfile
import tempfile
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import asyncio
import aiofiles
from dataclasses import dataclass

import boto3
from google.cloud import storage as gcs
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
import mlflow
import mlflow.tracking
from packaging import version

from app.models.model_registry import (
    Model, ModelVersion, ModelDeployment, ModelABTest, ModelMetrics,
    ModelStatus, DeploymentStatus
)
from app.core.database import get_db_session
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ModelArtifacts:
    """Container for model artifacts"""
    model_file: str  # Path to serialized model
    code_files: List[str]  # Supporting code files
    config_file: Optional[str] = None  # Model configuration
    requirements_file: Optional[str] = None  # Dependencies
    metadata: Optional[Dict] = None  # Additional metadata


@dataclass 
class RegistrationRequest:
    """Model registration request"""
    name: str
    description: str
    category: str
    strategy_type: str
    framework: str
    model_type: str
    version: str
    artifacts: ModelArtifacts
    training_config: Dict
    performance_metrics: Dict
    business_metrics: Optional[Dict] = None
    dataset_version: Optional[str] = None
    training_job_id: Optional[str] = None
    tags: Optional[List[str]] = None


class ModelRegistry:
    """
    Central service for managing ML model registry, versioning, and artifacts
    """
    
    def __init__(self):
        self.storage_backend = settings.MODEL_STORAGE_BACKEND  # 's3', 'gcs', 'local'
        self.storage_bucket = settings.MODEL_STORAGE_BUCKET
        self.local_storage_path = settings.LOCAL_MODEL_STORAGE_PATH or "/tmp/models"
        
        # Initialize storage clients
        if self.storage_backend == 's3':
            self.s3_client = boto3.client('s3')
        elif self.storage_backend == 'gcs':
            self.gcs_client = gcs.Client()
            self.gcs_bucket = self.gcs_client.bucket(self.storage_bucket)
        
        # Initialize MLflow
        if settings.MLFLOW_TRACKING_URI:
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)

    async def register_model(
        self, 
        request: RegistrationRequest,
        created_by: int,
        db_session: Session = None
    ) -> ModelVersion:
        """
        Register a new model version with artifacts and metadata
        """
        if not db_session:
            db_session = next(get_db_session())
        
        try:
            logger.info(f"Registering model {request.name} version {request.version}")
            
            # Get or create base model
            model = self._get_or_create_model(request, created_by, db_session)
            
            # Validate version format and uniqueness
            await self._validate_version(model.id, request.version, db_session)
            
            # Upload and store artifacts
            artifacts_path = await self._store_artifacts(
                model.name, request.version, request.artifacts
            )
            
            # Calculate model signature
            model_signature = await self._calculate_model_signature(request.artifacts)
            
            # Create model version record
            model_version = ModelVersion(
                model_id=model.id,
                version=request.version,
                artifacts_path=artifacts_path,
                training_config=request.training_config,
                dataset_version=request.dataset_version,
                training_job_id=request.training_job_id,
                performance_metrics=request.performance_metrics,
                business_metrics=request.business_metrics,
                model_signature=model_signature,
                description=request.description,
                status=ModelStatus.TRAINED
            )
            
            # Add file size information
            model_version.model_file_size = await self._get_file_size(request.artifacts.model_file)
            
            db_session.add(model_version)
            db_session.flush()
            
            # Run validation checks
            validation_results = await self._validate_model_version(model_version, request.artifacts)
            model_version.validation_status = "passed" if validation_results['valid'] else "failed"
            model_version.test_results = validation_results
            model_version.deployment_ready = validation_results['valid']
            
            # Update model status
            model.status = ModelStatus.TRAINED
            model.updated_at = datetime.utcnow()
            
            db_session.commit()
            
            logger.info(f"Successfully registered model version {model_version.uuid}")
            return model_version
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to register model: {str(e)}")
            raise

    async def list_models(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        db_session: Session = None
    ) -> List[Model]:
        """List models with filtering options"""
        if not db_session:
            db_session = next(get_db_session())
            
        query = db_session.query(Model).filter(Model.is_active == True)
        
        if category:
            query = query.filter(Model.category == category)
        if status:
            query = query.filter(Model.status == status)
        if created_by:
            query = query.filter(Model.created_by == created_by)
        if tags:
            # Filter by tags (PostgreSQL JSONB contains check)
            for tag in tags:
                query = query.filter(Model.tags.contains([tag]))
        
        return query.order_by(desc(Model.updated_at)).offset(offset).limit(limit).all()

    async def get_model_versions(
        self,
        model_id: int,
        limit: int = 20,
        db_session: Session = None
    ) -> List[ModelVersion]:
        """Get all versions for a model"""
        if not db_session:
            db_session = next(get_db_session())
            
        return (
            db_session.query(ModelVersion)
            .filter(ModelVersion.model_id == model_id, ModelVersion.is_active == True)
            .order_by(desc(ModelVersion.created_at))
            .limit(limit)
            .all()
        )

    async def get_model_version(
        self,
        model_id: int,
        version: str,
        db_session: Session = None
    ) -> Optional[ModelVersion]:
        """Get specific model version"""
        if not db_session:
            db_session = next(get_db_session())
            
        return (
            db_session.query(ModelVersion)
            .filter(
                ModelVersion.model_id == model_id,
                ModelVersion.version == version,
                ModelVersion.is_active == True
            )
            .first()
        )

    async def download_model_artifacts(
        self, 
        model_version: ModelVersion,
        local_path: Optional[str] = None
    ) -> str:
        """Download model artifacts to local filesystem"""
        if not local_path:
            local_path = tempfile.mkdtemp()
        
        logger.info(f"Downloading artifacts for model version {model_version.uuid}")
        
        try:
            if self.storage_backend == 's3':
                await self._download_from_s3(model_version.artifacts_path, local_path)
            elif self.storage_backend == 'gcs':
                await self._download_from_gcs(model_version.artifacts_path, local_path)
            else:
                await self._download_from_local(model_version.artifacts_path, local_path)
            
            logger.info(f"Downloaded artifacts to {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download artifacts: {str(e)}")
            raise

    async def promote_version(
        self,
        model_version_id: int,
        target_status: ModelStatus,
        db_session: Session = None
    ) -> ModelVersion:
        """Promote model version to new status"""
        if not db_session:
            db_session = next(get_db_session())
        
        try:
            model_version = db_session.query(ModelVersion).get(model_version_id)
            if not model_version:
                raise ValueError(f"Model version {model_version_id} not found")
            
            # Validate promotion path
            valid_promotions = {
                ModelStatus.TRAINING: [ModelStatus.TRAINED],
                ModelStatus.TRAINED: [ModelStatus.VALIDATED, ModelStatus.DEPLOYED],
                ModelStatus.VALIDATED: [ModelStatus.DEPLOYED],
                ModelStatus.DEPLOYED: [ModelStatus.DEPRECATED]
            }
            
            current_status = ModelStatus(model_version.status)
            if target_status not in valid_promotions.get(current_status, []):
                raise ValueError(f"Cannot promote from {current_status} to {target_status}")
            
            # Update status
            model_version.status = target_status.value
            model_version.updated_at = datetime.utcnow()
            
            # Update parent model status if needed
            if target_status == ModelStatus.DEPLOYED:
                model_version.model.status = ModelStatus.DEPLOYED.value
            
            db_session.commit()
            logger.info(f"Promoted model version {model_version.uuid} to {target_status}")
            
            return model_version
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to promote model version: {str(e)}")
            raise

    async def compare_versions(
        self,
        version_1_id: int,
        version_2_id: int,
        metrics: List[str] = None,
        db_session: Session = None
    ) -> Dict[str, Any]:
        """Compare performance metrics between two model versions"""
        if not db_session:
            db_session = next(get_db_session())
        
        v1 = db_session.query(ModelVersion).get(version_1_id)
        v2 = db_session.query(ModelVersion).get(version_2_id)
        
        if not v1 or not v2:
            raise ValueError("One or both model versions not found")
        
        # Default metrics to compare
        if not metrics:
            metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'sharpe_ratio', 'max_drawdown']
        
        comparison = {
            'version_1': {
                'id': v1.id,
                'version': v1.version,
                'created_at': v1.created_at.isoformat(),
                'metrics': {}
            },
            'version_2': {
                'id': v2.id,
                'version': v2.version,
                'created_at': v2.created_at.isoformat(),
                'metrics': {}
            },
            'comparison': {},
            'winner': None
        }
        
        # Compare metrics
        v1_score = 0
        v2_score = 0
        
        for metric in metrics:
            v1_value = v1.performance_metrics.get(metric) if v1.performance_metrics else None
            v2_value = v2.performance_metrics.get(metric) if v2.performance_metrics else None
            
            comparison['version_1']['metrics'][metric] = v1_value
            comparison['version_2']['metrics'][metric] = v2_value
            
            if v1_value is not None and v2_value is not None:
                # Determine which is better based on metric type
                if metric in ['accuracy', 'precision', 'recall', 'f1_score', 'sharpe_ratio']:
                    # Higher is better
                    if v1_value > v2_value:
                        v1_score += 1
                        comparison['comparison'][metric] = 'v1_better'
                    elif v2_value > v1_value:
                        v2_score += 1
                        comparison['comparison'][metric] = 'v2_better'
                    else:
                        comparison['comparison'][metric] = 'tie'
                elif metric in ['max_drawdown', 'mse', 'mae']:
                    # Lower is better
                    if v1_value < v2_value:
                        v1_score += 1
                        comparison['comparison'][metric] = 'v1_better'
                    elif v2_value < v1_value:
                        v2_score += 1
                        comparison['comparison'][metric] = 'v2_better'
                    else:
                        comparison['comparison'][metric] = 'tie'
                        
                comparison['comparison'][f'{metric}_diff'] = v2_value - v1_value
        
        # Determine overall winner
        if v1_score > v2_score:
            comparison['winner'] = 'version_1'
        elif v2_score > v1_score:
            comparison['winner'] = 'version_2'
        else:
            comparison['winner'] = 'tie'
        
        comparison['score'] = {'version_1': v1_score, 'version_2': v2_score}
        
        return comparison

    async def create_ab_test(
        self,
        name: str,
        description: str,
        control_version_id: int,
        treatment_version_id: int,
        traffic_split: float = 0.5,
        duration_days: int = 7,
        success_criteria: Dict = None,
        db_session: Session = None
    ) -> ModelABTest:
        """Create A/B test configuration"""
        if not db_session:
            db_session = next(get_db_session())
        
        # Validate inputs
        if not (0 < traffic_split < 1):
            raise ValueError("Traffic split must be between 0 and 1")
        
        # Check that versions exist and belong to same model
        control = db_session.query(ModelVersion).get(control_version_id)
        treatment = db_session.query(ModelVersion).get(treatment_version_id)
        
        if not control or not treatment:
            raise ValueError("One or both model versions not found")
        
        if control.model_id != treatment.model_id:
            raise ValueError("A/B test versions must belong to the same model")
        
        # Default success criteria
        if not success_criteria:
            success_criteria = {
                'significance_level': 0.05,
                'minimum_sample_size': 1000,
                'primary_metric': 'sharpe_ratio',
                'minimum_effect_size': 0.1
            }
        
        # Create A/B test
        ab_test = ModelABTest(
            name=name,
            description=description,
            control_model_version_id=control_version_id,
            treatment_model_version_id=treatment_version_id,
            traffic_split=traffic_split,
            test_duration_days=duration_days,
            success_criteria=success_criteria,
            status="planning"
        )
        
        db_session.add(ab_test)
        db_session.commit()
        
        logger.info(f"Created A/B test {ab_test.uuid}")
        return ab_test

    async def get_model_lineage(
        self, 
        model_version_id: int,
        depth: int = 5,
        db_session: Session = None
    ) -> Dict[str, Any]:
        """Get model lineage (ancestry and descendants)"""
        if not db_session:
            db_session = next(get_db_session())
        
        root_version = db_session.query(ModelVersion).get(model_version_id)
        if not root_version:
            raise ValueError(f"Model version {model_version_id} not found")
        
        lineage = {
            'root': root_version.to_dict(),
            'ancestors': [],
            'descendants': []
        }
        
        # Trace ancestors
        current = root_version
        ancestor_depth = 0
        while current.parent_version_id and ancestor_depth < depth:
            parent = db_session.query(ModelVersion).get(current.parent_version_id)
            if parent:
                lineage['ancestors'].append(parent.to_dict())
                current = parent
                ancestor_depth += 1
            else:
                break
        
        # Find descendants
        descendants = []
        queue = [(root_version, 0)]
        
        while queue:
            version, level = queue.pop(0)
            if level >= depth:
                continue
                
            children = (
                db_session.query(ModelVersion)
                .filter(ModelVersion.parent_version_id == version.id)
                .all()
            )
            
            for child in children:
                child_dict = child.to_dict()
                child_dict['level'] = level + 1
                descendants.append(child_dict)
                queue.append((child, level + 1))
        
        lineage['descendants'] = descendants
        return lineage

    # Private helper methods
    
    def _get_or_create_model(
        self, 
        request: RegistrationRequest, 
        created_by: int, 
        db_session: Session
    ) -> Model:
        """Get existing model or create new one"""
        model = db_session.query(Model).filter(Model.name == request.name).first()
        
        if not model:
            model = Model(
                name=request.name,
                description=request.description,
                category=request.category,
                strategy_type=request.strategy_type,
                framework=request.framework,
                model_type=request.model_type,
                created_by=created_by,
                tags=request.tags or [],
                status=ModelStatus.TRAINING
            )
            db_session.add(model)
            db_session.flush()
        
        return model

    async def _validate_version(self, model_id: int, version_str: str, db_session: Session):
        """Validate version format and uniqueness"""
        # Check version format (semantic versioning)
        try:
            version.Version(version_str)
        except:
            raise ValueError(f"Invalid version format: {version_str}")
        
        # Check uniqueness
        existing = (
            db_session.query(ModelVersion)
            .filter(ModelVersion.model_id == model_id, ModelVersion.version == version_str)
            .first()
        )
        
        if existing:
            raise ValueError(f"Version {version_str} already exists for this model")

    async def _store_artifacts(
        self, 
        model_name: str, 
        version: str, 
        artifacts: ModelArtifacts
    ) -> str:
        """Store model artifacts in configured storage backend"""
        # Create artifact package
        with tempfile.TemporaryDirectory() as temp_dir:
            package_path = Path(temp_dir) / f"{model_name}_{version}.tar.gz"
            
            with tarfile.open(package_path, "w:gz") as tar:
                # Add model file
                tar.add(artifacts.model_file, arcname="model.pkl")
                
                # Add code files
                for i, code_file in enumerate(artifacts.code_files):
                    tar.add(code_file, arcname=f"code_{i}.py")
                
                # Add config and requirements if provided
                if artifacts.config_file:
                    tar.add(artifacts.config_file, arcname="config.json")
                if artifacts.requirements_file:
                    tar.add(artifacts.requirements_file, arcname="requirements.txt")
            
            # Upload to storage backend
            storage_path = f"models/{model_name}/{version}/artifacts.tar.gz"
            
            if self.storage_backend == 's3':
                self.s3_client.upload_file(str(package_path), self.storage_bucket, storage_path)
            elif self.storage_backend == 'gcs':
                blob = self.gcs_bucket.blob(storage_path)
                blob.upload_from_filename(str(package_path))
            else:
                # Local storage
                local_dir = Path(self.local_storage_path) / model_name / version
                local_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(package_path, local_dir / "artifacts.tar.gz")
                storage_path = str(local_dir / "artifacts.tar.gz")
            
            return storage_path

    async def _calculate_model_signature(self, artifacts: ModelArtifacts) -> str:
        """Calculate model signature hash"""
        hasher = hashlib.sha256()
        
        # Hash the model file
        async with aiofiles.open(artifacts.model_file, 'rb') as f:
            while chunk := await f.read(8192):
                hasher.update(chunk)
        
        return hasher.hexdigest()

    async def _validate_model_version(
        self, 
        model_version: ModelVersion, 
        artifacts: ModelArtifacts
    ) -> Dict[str, Any]:
        """Run validation checks on model version"""
        results = {
            'valid': True,
            'checks': {},
            'errors': []
        }
        
        try:
            # Check if model file exists and can be loaded
            if not os.path.exists(artifacts.model_file):
                results['checks']['file_exists'] = False
                results['errors'].append("Model file does not exist")
                results['valid'] = False
            else:
                results['checks']['file_exists'] = True
                
                # Try to load model (basic check)
                file_size = os.path.getsize(artifacts.model_file)
                results['checks']['file_size'] = file_size
                
                if file_size == 0:
                    results['errors'].append("Model file is empty")
                    results['valid'] = False
            
            # Check performance metrics
            if not model_version.performance_metrics:
                results['errors'].append("No performance metrics provided")
                results['valid'] = False
            else:
                results['checks']['has_metrics'] = True
                
                # Check for required metrics
                required_metrics = ['accuracy', 'precision', 'recall']
                for metric in required_metrics:
                    if metric not in model_version.performance_metrics:
                        results['errors'].append(f"Missing required metric: {metric}")
                        results['valid'] = False
            
            # Check training configuration
            if not model_version.training_config:
                results['errors'].append("No training configuration provided")
                results['valid'] = False
            else:
                results['checks']['has_training_config'] = True
            
            return results
            
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Validation error: {str(e)}")
            return results

    async def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    async def _download_from_s3(self, storage_path: str, local_path: str):
        """Download artifacts from S3"""
        self.s3_client.download_file(self.storage_bucket, storage_path, local_path)

    async def _download_from_gcs(self, storage_path: str, local_path: str):
        """Download artifacts from Google Cloud Storage"""
        blob = self.gcs_bucket.blob(storage_path)
        blob.download_to_filename(local_path)

    async def _download_from_local(self, storage_path: str, local_path: str):
        """Copy artifacts from local storage"""
        shutil.copy2(storage_path, local_path)


# Global instance
model_registry = ModelRegistry()