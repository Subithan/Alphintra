"""
Dataset management API endpoints for Phase 3.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
import tempfile

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user_id, require_permission, create_rate_limit_dependency
from app.services.data_ingestion_service import DataIngestionService
from app.services.dataset_validator import DatasetValidator
from app.services.data_processor import DataProcessingService
from app.services.dataset_catalog import DatasetCatalogService
from app.services.storage_manager import StorageManager
from app.models.dataset import AssetClass, DataSource, DataFrequency, DataFormat

router = APIRouter(prefix="/datasets")

# Dependency instances
data_ingestion_service = DataIngestionService()
dataset_validator = DatasetValidator()
data_processor = DataProcessingService()
catalog_service = DatasetCatalogService()
storage_manager = StorageManager()

# Rate limiting
rate_limit = create_rate_limit_dependency(requests_per_minute=60)


# Request/Response Models
class DatasetUploadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    asset_class: AssetClass
    symbols: Optional[List[str]] = Field(default_factory=list)
    frequency: Optional[DataFrequency] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    category: Optional[str] = Field(None, max_length=100)
    is_public: bool = Field(default=False)


class DatasetUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=100)
    is_public: Optional[bool] = None


class IngestionJobRequest(BaseModel):
    job_name: str = Field(..., min_length=1, max_length=255)
    data_source: str = Field(..., min_length=1)
    symbols: List[str] = Field(..., min_items=1)
    frequency: DataFrequency
    start_date: str = Field(..., description="ISO format date string")
    end_date: str = Field(..., description="ISO format date string")
    is_recurring: bool = Field(default=False)
    schedule_cron: Optional[str] = None
    ingestion_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    quality_checks: Optional[List[str]] = Field(default_factory=list)


class ProcessingJobRequest(BaseModel):
    dataset_id: str
    job_name: str = Field(..., min_length=1, max_length=255)
    job_type: str = Field(default="cleaning")
    processing_steps: List[Dict[str, Any]] = Field(..., min_items=1)
    input_columns: Optional[List[str]] = Field(default_factory=list)
    output_columns: Optional[List[str]] = Field(default_factory=list)


class ValidationRequest(BaseModel):
    dataset_id: str


class DatasetSearchRequest(BaseModel):
    search: Optional[str] = None
    asset_class: Optional[Union[AssetClass, List[AssetClass]]] = None
    source: Optional[Union[DataSource, List[DataSource]]] = None
    frequency: Optional[Union[DataFrequency, List[DataFrequency]]] = None
    symbols: Optional[Union[str, List[str]]] = None
    tags: Optional[Union[str, List[str]]] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None
    status: Optional[Union[str, List[str]]] = None
    start_date_from: Optional[str] = None
    start_date_to: Optional[str] = None
    end_date_from: Optional[str] = None
    end_date_to: Optional[str] = None
    min_rows: Optional[int] = Field(None, ge=0)
    max_rows: Optional[int] = Field(None, ge=0)
    min_size_mb: Optional[float] = Field(None, ge=0)
    max_size_mb: Optional[float] = Field(None, ge=0)
    min_quality_score: Optional[float] = Field(None, ge=0, le=1)
    validated_only: Optional[bool] = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")
    limit: int = Field(default=50, le=200)
    offset: int = Field(default=0, ge=0)


# Dataset CRUD Endpoints
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    metadata: str = None,  # JSON string of DatasetUploadRequest
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Upload a new dataset file."""
    try:
        # Parse metadata
        import json
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset metadata is required"
            )
        
        try:
            metadata_dict = json.loads(metadata)
            upload_request = DatasetUploadRequest(**metadata_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metadata format: {str(e)}"
            )
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Check file extension
        allowed_extensions = {'.csv', '.json', '.parquet', '.xlsx', '.feather'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Quick validation of uploaded file
            validation_result = await dataset_validator.validate_uploaded_file(
                temp_file_path, upload_request.asset_class
            )
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "File validation failed",
                    "validation_errors": validation_result.get("errors", [])
                }
            
            # Store dataset using storage manager
            import pandas as pd
            
            # Load dataframe
            if file_extension == '.csv':
                df = pd.read_csv(temp_file_path)
            elif file_extension == '.json':
                df = pd.read_json(temp_file_path)
            elif file_extension == '.parquet':
                df = pd.read_parquet(temp_file_path)
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(temp_file_path)
            elif file_extension == '.feather':
                df = pd.read_feather(temp_file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Prepare dataset metadata
            dataset_metadata = {
                "id": str(UUID(user_id)),  # Will be replaced with actual dataset ID
                "name": upload_request.name,
                "description": upload_request.description,
                "asset_class": upload_request.asset_class.value,
                "symbols": upload_request.symbols,
                "row_count": len(df)
            }
            
            # Store dataset
            storage_info = await storage_manager.store_dataset(df, dataset_metadata)
            
            # Create dataset record
            from app.models.dataset import Dataset, DatasetStatus
            
            # Determine data format
            format_map = {
                '.csv': DataFormat.CSV,
                '.json': DataFormat.JSON,
                '.parquet': DataFormat.PARQUET,
                '.xlsx': DataFormat.EXCEL,
                '.xls': DataFormat.EXCEL,
                '.feather': DataFormat.FEATHER
            }
            
            data_format = format_map.get(file_extension, DataFormat.CSV)
            
            # Infer date range from data if timestamp column exists
            start_date = datetime.utcnow()
            end_date = datetime.utcnow()
            
            if 'timestamp' in df.columns:
                try:
                    timestamps = pd.to_datetime(df['timestamp'])
                    start_date = timestamps.min().to_pydatetime()
                    end_date = timestamps.max().to_pydatetime()
                except:
                    pass
            
            dataset = Dataset(
                id=UUID(storage_info["dataset_id"]),
                user_id=user_id,
                name=upload_request.name,
                description=upload_request.description,
                source=DataSource.USER_UPLOAD,
                asset_class=upload_request.asset_class,
                symbols=upload_request.symbols or [],
                frequency=upload_request.frequency,
                start_date=start_date,
                end_date=end_date,
                columns=df.columns.tolist(),
                row_count=len(df),
                file_size=storage_info["file_size"],
                data_format=data_format,
                status=DatasetStatus.UPLOADED,
                is_validated=False,
                file_path=storage_info["storage_path"],
                original_filename=file.filename,
                content_hash=storage_info["content_hash"],
                storage_backend=storage_info["storage_backend"],
                data_types={str(col): str(df[col].dtype) for col in df.columns},
                tags=upload_request.tags or [],
                category=upload_request.category,
                is_public=upload_request.is_public
            )
            
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            
            return {
                "success": True,
                "dataset_id": str(dataset.id),
                "message": "Dataset uploaded successfully",
                "validation_warnings": validation_result.get("warnings", [])
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/search")
async def search_datasets(
    search: Optional[str] = None,
    asset_class: Optional[str] = None,
    source: Optional[str] = None,
    frequency: Optional[str] = None,
    symbols: Optional[str] = None,
    tags: Optional[str] = None,
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    status_filter: Optional[str] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    end_date_from: Optional[str] = None,
    end_date_to: Optional[str] = None,
    min_rows: Optional[int] = None,
    max_rows: Optional[int] = None,
    min_size_mb: Optional[float] = None,
    max_size_mb: Optional[float] = None,    
    min_quality_score: Optional[float] = None,
    validated_only: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Search datasets with advanced filtering."""
    try:
        # Build filters dict
        filters = {
            "user_id": str(user_id),
            "search": search,
            "asset_class": asset_class,
            "source": source,
            "frequency": frequency,
            "symbols": symbols.split(",") if symbols else None,
            "tags": tags.split(",") if tags else None,
            "category": category,
            "is_public": is_public,
            "status": status_filter,
            "start_date_from": start_date_from,
            "start_date_to": start_date_to,
            "end_date_from": end_date_from,
            "end_date_to": end_date_to,
            "min_rows": min_rows,
            "max_rows": max_rows,
            "min_size_mb": min_size_mb,
            "max_size_mb": max_size_mb,
            "min_quality_score": min_quality_score,
            "validated_only": validated_only,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        result = await catalog_service.search_datasets(filters, db)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/public")
async def get_public_datasets(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    asset_class: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get public datasets available to all users."""
    try:
        filters = {
            "limit": limit,
            "offset": offset,
            "asset_class": asset_class,
            "category": category
        }
        
        result = await catalog_service.get_public_datasets(filters, db)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/recommended")
async def get_recommended_datasets(
    limit: int = Query(default=10, le=50),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get recommended datasets for the user."""
    try:
        recommended = await catalog_service.get_recommended_datasets(str(user_id), limit, db)
        return {"recommended_datasets": recommended}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/summary")
async def get_catalog_summary(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's dataset catalog summary."""
    try:
        summary = await catalog_service.get_catalog_summary(str(user_id), db)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a dataset."""
    try:
        dataset = await catalog_service.get_dataset_details(dataset_id, str(user_id), db)
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{dataset_id}")
async def update_dataset(
    dataset_id: str,
    request: DatasetUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Update dataset metadata."""
    try:
        from sqlalchemy import select, update
        from app.models.dataset import Dataset
        
        # Get dataset
        result = await db.execute(
            select(Dataset).where(
                Dataset.id == UUID(dataset_id),
                Dataset.user_id == user_id
            )
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        
        if update_data:
            for field, value in update_data.items():
                setattr(dataset, field, value)
            
            dataset.updated_at = datetime.utcnow()
            await db.commit()
        
        return {"message": "Dataset updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("delete_dataset"))
):
    """Delete a dataset."""
    try:
        from sqlalchemy import select
        from app.models.dataset import Dataset
        
        # Get dataset
        result = await db.execute(
            select(Dataset).where(
                Dataset.id == UUID(dataset_id),
                Dataset.user_id == user_id
            )
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Delete from storage
        await storage_manager.delete_dataset(dataset)
        
        # Delete from database
        await db.delete(dataset)
        await db.commit()
        
        return {"message": "Dataset deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{dataset_id}/download")
async def download_dataset(
    dataset_id: str,
    format: Optional[str] = Query(default=None, description="Download format: csv, json, parquet"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Download a dataset file."""
    try:
        from sqlalchemy import select
        from app.models.dataset import Dataset
        
        # Get dataset
        result = await db.execute(
            select(Dataset).where(
                Dataset.id == UUID(dataset_id),
                Dataset.user_id == user_id
            )
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Update download count
        dataset.download_count += 1
        dataset.last_accessed = datetime.utcnow()
        await db.commit()
        
        # Get file path
        file_path = await storage_manager.backends[dataset.storage_backend].retrieve_file(dataset.file_path)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset file not found"
            )
        
        # Convert format if requested
        if format and format != dataset.data_format.value:
            # Load and convert
            df = await storage_manager.retrieve_dataset(dataset)
            if df is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to load dataset"
                )
            
            # Create temporary file in requested format
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as temp_file:
                if format == "csv":
                    df.to_csv(temp_file.name, index=False)
                elif format == "json":
                    df.to_json(temp_file.name, orient="records")
                elif format == "parquet":
                    df.to_parquet(temp_file.name, index=False)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported format: {format}"
                    )
                
                converted_file_path = temp_file.name
            
            return FileResponse(
                path=converted_file_path,
                filename=f"{dataset.name}.{format}",
                media_type="application/octet-stream"
            )
        else:
            # Return original file
            return FileResponse(
                path=file_path,
                filename=f"{dataset.name}.{dataset.data_format.value}",
                media_type="application/octet-stream"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Data Ingestion Endpoints
@router.post("/ingestion/jobs", status_code=status.HTTP_201_CREATED)
async def create_ingestion_job(
    request: IngestionJobRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Create a new data ingestion job."""
    try:
        result = await data_ingestion_service.create_ingestion_job(
            job_data=request.dict(),
            user_id=str(user_id),
            db=db
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ingestion/jobs/{job_id}/execute")
async def execute_ingestion_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("execute_ingestion"))
):
    """Execute a data ingestion job."""
    try:
        # Execute in background
        background_tasks.add_task(
            data_ingestion_service.execute_ingestion_job,
            job_id,
            db
        )
        
        return {"message": "Ingestion job started", "job_id": job_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/ingestion/jobs")
async def list_ingestion_jobs(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[str] = None,
    data_source: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List ingestion jobs."""
    try:
        filters = {
            "user_id": str(user_id),
            "limit": limit,
            "offset": offset,
            "status": status_filter,
            "data_source": data_source
        }
        
        jobs = await data_ingestion_service.list_ingestion_jobs(filters, db)
        return {"jobs": jobs}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/ingestion/sources")
async def get_ingestion_sources():
    """Get supported data ingestion sources."""
    try:
        sources = data_ingestion_service.get_supported_sources()
        return {"sources": sources}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Validation Endpoints
@router.post("/{dataset_id}/validate")
async def validate_dataset(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Validate a dataset."""
    try:
        # Execute validation in background
        background_tasks.add_task(
            dataset_validator.validate_dataset,
            dataset_id,
            str(user_id),
            db
        )
        
        return {"message": "Dataset validation started", "dataset_id": dataset_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{dataset_id}/validation-report")
async def get_validation_report(
    dataset_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get validation report for a dataset."""
    try:
        report = await dataset_validator.get_validation_report(dataset_id, str(user_id), db)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation report not found"
            )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Processing Endpoints
@router.post("/processing/jobs", status_code=status.HTTP_201_CREATED)
async def create_processing_job(
    request: ProcessingJobRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(rate_limit)
):
    """Create a data processing job."""
    try:
        result = await data_processor.create_processing_job(
            job_data=request.dict(),
            user_id=str(user_id),
            db=db
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/processing/jobs/{job_id}/execute")
async def execute_processing_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("execute_processing"))
):
    """Execute a data processing job."""
    try:
        # Execute in background
        background_tasks.add_task(
            data_processor.execute_processing_job,
            job_id,
            db
        )
        
        return {"message": "Processing job started", "job_id": job_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/processing/processors")
async def get_available_processors():
    """Get available data processors."""
    try:
        processors = data_processor.get_available_processors()
        return {"processors": processors}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{dataset_id}/statistics")
async def get_dataset_statistics(
    dataset_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dataset statistics."""
    try:
        stats = await catalog_service.get_dataset_statistics(dataset_id, str(user_id), db)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or statistics not available"
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Utility Endpoints
@router.get("/tags")
async def get_dataset_tags(db: AsyncSession = Depends(get_db)):
    """Get all available dataset tags."""
    try:
        tags = await catalog_service.get_dataset_tags(db)
        return {"tags": tags}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/categories")
async def get_dataset_categories(db: AsyncSession = Depends(get_db)):
    """Get all available dataset categories."""
    try:
        categories = await catalog_service.get_dataset_categories(db)
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/storage/stats")
async def get_storage_statistics(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get storage usage statistics."""
    try:
        stats = await storage_manager.get_storage_statistics(db=db)
        return {"storage_stats": stats}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )