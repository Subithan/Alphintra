"""
Storage manager for efficient data handling across different storage backends.
"""

import logging
import os
import shutil
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, BinaryIO, Union
from pathlib import Path
import asyncio
import aiofiles
import pandas as pd
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.models.dataset import Dataset, DataFormat
from app.core.config import get_settings


class StorageBackend:
    """Base class for storage backends."""
    
    def __init__(self, backend_name: str):
        self.backend_name = backend_name
        self.logger = logging.getLogger(f"{__name__}.{backend_name}")
    
    async def store_file(self, file_path: str, content: Union[bytes, BinaryIO], 
                        metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Store a file and return storage information."""
        raise NotImplementedError("Subclasses must implement store_file")
    
    async def retrieve_file(self, file_path: str, destination: str = None) -> Optional[str]:
        """Retrieve a file and return local path."""
        raise NotImplementedError("Subclasses must implement retrieve_file")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage."""
        raise NotImplementedError("Subclasses must implement delete_file")
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        raise NotImplementedError("Subclasses must implement file_exists")
    
    async def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata."""
        raise NotImplementedError("Subclasses must implement get_file_metadata")
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files with optional prefix filter."""
        raise NotImplementedError("Subclasses must implement list_files")


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, base_path: str):
        super().__init__("local")
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def store_file(self, file_path: str, content: Union[bytes, BinaryIO], 
                        metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Store file to local filesystem."""
        try:
            full_path = self.base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            if isinstance(content, bytes):
                async with aiofiles.open(full_path, 'wb') as f:
                    await f.write(content)
            else:
                # Assume BinaryIO
                content.seek(0)
                async with aiofiles.open(full_path, 'wb') as f:
                    await f.write(content.read())
            
            # Get file info
            file_size = full_path.stat().st_size
            
            # Calculate hash
            hash_md5 = hashlib.md5()
            async with aiofiles.open(full_path, 'rb') as f:
                async for chunk in f:
                    hash_md5.update(chunk)
            
            return {
                "file_path": str(full_path),
                "relative_path": file_path,
                "file_size": file_size,
                "content_hash": hash_md5.hexdigest(),
                "mime_type": mimetypes.guess_type(str(full_path))[0],
                "created_at": datetime.fromtimestamp(full_path.stat().st_ctime),
                "modified_at": datetime.fromtimestamp(full_path.stat().st_mtime)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to store file {file_path}: {str(e)}")
            raise
    
    async def retrieve_file(self, file_path: str, destination: str = None) -> Optional[str]:
        """Retrieve file from local storage."""
        try:
            if file_path.startswith(str(self.base_path)):
                # Absolute path provided
                full_path = Path(file_path)
            else:
                # Relative path provided
                full_path = self.base_path / file_path
            
            if not full_path.exists():
                return None
            
            if destination:
                # Copy to destination
                dest_path = Path(destination)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(full_path, dest_path)
                return str(dest_path)
            else:
                # Return original path
                return str(full_path)
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve file {file_path}: {str(e)}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage."""
        try:
            if file_path.startswith(str(self.base_path)):
                full_path = Path(file_path)
            else:
                full_path = self.base_path / file_path
            
            if full_path.exists():
                full_path.unlink()
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        try:
            if file_path.startswith(str(self.base_path)):
                full_path = Path(file_path)
            else:
                full_path = self.base_path / file_path
            
            return full_path.exists()
            
        except Exception as e:
            self.logger.error(f"Failed to check file existence {file_path}: {str(e)}")
            return False
    
    async def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata."""
        try:
            if file_path.startswith(str(self.base_path)):
                full_path = Path(file_path)
            else:
                full_path = self.base_path / file_path
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            
            return {
                "file_path": str(full_path),
                "file_size": stat.st_size,
                "mime_type": mimetypes.guess_type(str(full_path))[0],
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "is_file": full_path.is_file(),
                "is_directory": full_path.is_dir()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get file metadata {file_path}: {str(e)}")
            return None
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files with prefix filter."""
        try:
            files = []
            search_path = self.base_path / prefix if prefix else self.base_path
            
            if search_path.is_dir():
                for file_path in search_path.rglob("*"):
                    if file_path.is_file() and len(files) < limit:
                        metadata = await self.get_file_metadata(str(file_path))
                        if metadata:
                            files.append(metadata)
            
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list files with prefix {prefix}: {str(e)}")
            return []


class CloudStorageBackend(StorageBackend):
    """Base class for cloud storage backends (GCS, S3, Azure)."""
    
    def __init__(self, backend_name: str, config: Dict[str, Any]):
        super().__init__(backend_name)
        self.config = config
    
    # Cloud storage implementations would go here
    # For now, this is a placeholder


class DataCompressionManager:
    """Manager for data compression and decompression."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def compress_dataframe(self, df: pd.DataFrame, file_path: str, 
                                compression_type: str = "parquet") -> Dict[str, Any]:
        """Compress dataframe to specified format."""
        try:
            if compression_type == "parquet":
                df.to_parquet(file_path, compression="snappy", index=False)
            elif compression_type == "feather":
                df.to_feather(file_path, compression="lz4")
            elif compression_type == "hdf5":
                df.to_hdf(file_path, key="data", mode="w", complevel=9, complib="blosc")
            elif compression_type == "csv_gzip":
                df.to_csv(file_path + ".gz", compression="gzip", index=False)
                file_path = file_path + ".gz"
            else:
                raise ValueError(f"Unsupported compression type: {compression_type}")
            
            # Get file info
            file_size = os.path.getsize(file_path)
            
            return {
                "file_path": file_path,
                "file_size": file_size,
                "compression_type": compression_type,
                "original_rows": len(df),
                "original_columns": len(df.columns)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to compress dataframe: {str(e)}")
            raise
    
    async def decompress_dataframe(self, file_path: str, 
                                  compression_type: str = "parquet") -> pd.DataFrame:
        """Decompress dataframe from file."""
        try:
            if compression_type == "parquet":
                return pd.read_parquet(file_path)
            elif compression_type == "feather":
                return pd.read_feather(file_path)
            elif compression_type == "hdf5":
                return pd.read_hdf(file_path, key="data")
            elif compression_type == "csv_gzip":
                return pd.read_csv(file_path, compression="gzip")
            else:
                raise ValueError(f"Unsupported compression type: {compression_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to decompress dataframe: {str(e)}")
            raise


class StorageManager:
    """Main storage manager coordinating different backends and operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # Initialize backends
        self.backends = {}
        
        # Local storage backend
        local_path = getattr(self.settings, 'DATA_STORAGE_PATH', '/tmp/ai_ml_data')
        self.backends["local"] = LocalStorageBackend(local_path)
        
        # Cloud backends would be initialized here based on configuration
        # self.backends["gcs"] = GCSStorageBackend(config)
        # self.backends["s3"] = S3StorageBackend(config)
        
        # Set default backend
        self.default_backend = "local"
        
        # Initialize compression manager
        self.compression_manager = DataCompressionManager()
    
    async def store_dataset(self, df: pd.DataFrame, dataset_metadata: Dict[str, Any], 
                           backend: str = None) -> Dict[str, Any]:
        """Store a dataset with optimal compression and storage."""
        try:
            backend = backend or self.default_backend
            
            if backend not in self.backends:
                raise ValueError(f"Unknown storage backend: {backend}")
            
            storage_backend = self.backends[backend]
            
            # Generate file path
            dataset_id = dataset_metadata.get("id", str(uuid4()))
            file_name = f"dataset_{dataset_id}"
            
            # Determine optimal format based on data characteristics
            optimal_format = self._determine_optimal_format(df, dataset_metadata)
            
            # Create temporary file for compression
            temp_dir = Path("/tmp/ai_ml_temp")
            temp_dir.mkdir(exist_ok=True)
            temp_file_path = temp_dir / f"{file_name}.{optimal_format}"
            
            # Compress dataframe
            compression_info = await self.compression_manager.compress_dataframe(
                df, str(temp_file_path), optimal_format
            )
            
            # Store in backend
            storage_path = f"datasets/{dataset_id[:2]}/{dataset_id}/{file_name}.{optimal_format}"
            
            with open(temp_file_path, 'rb') as f:
                storage_info = await storage_backend.store_file(
                    storage_path, 
                    f.read(),
                    metadata=dataset_metadata
                )
            
            # Clean up temp file
            temp_file_path.unlink()
            
            # Combine information
            result = {
                "dataset_id": dataset_id,
                "storage_backend": backend,
                "storage_path": storage_path,
                "data_format": optimal_format,
                **storage_info,
                **compression_info
            }
            
            self.logger.info(f"Stored dataset {dataset_id} using {optimal_format} format ({storage_info['file_size']} bytes)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to store dataset: {str(e)}")
            raise
    
    async def retrieve_dataset(self, dataset: Dataset, 
                              destination: str = None) -> Optional[pd.DataFrame]:
        """Retrieve and load a dataset."""
        try:
            backend_name = dataset.storage_backend or self.default_backend
            
            if backend_name not in self.backends:
                self.logger.error(f"Unknown storage backend: {backend_name}")
                return None
            
            storage_backend = self.backends[backend_name]
            
            # Retrieve file
            local_path = await storage_backend.retrieve_file(dataset.file_path, destination)
            
            if not local_path:
                self.logger.error(f"Failed to retrieve dataset file: {dataset.file_path}")
                return None
            
            # Decompress and load dataframe
            compression_type = dataset.data_format.value if hasattr(dataset.data_format, 'value') else str(dataset.data_format)
            
            df = await self.compression_manager.decompress_dataframe(
                local_path, compression_type
            )
            
            # Update last accessed time
            dataset.last_accessed = datetime.utcnow()
            
            self.logger.info(f"Retrieved dataset {dataset.id} with {len(df)} rows")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve dataset: {str(e)}")
            return None
    
    async def delete_dataset(self, dataset: Dataset) -> bool:
        """Delete a dataset from storage."""
        try:
            backend_name = dataset.storage_backend or self.default_backend
            
            if backend_name not in self.backends:
                self.logger.error(f"Unknown storage backend: {backend_name}")
                return False
            
            storage_backend = self.backends[backend_name]
            
            # Delete file
            success = await storage_backend.delete_file(dataset.file_path)
            
            if success:
                self.logger.info(f"Deleted dataset {dataset.id} from storage")
            else:
                self.logger.warning(f"Failed to delete dataset {dataset.id} from storage")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete dataset: {str(e)}")
            return False
    
    async def migrate_dataset(self, dataset: Dataset, target_backend: str, 
                             db: AsyncSession) -> bool:
        """Migrate dataset between storage backends."""
        try:
            if target_backend not in self.backends:
                raise ValueError(f"Unknown target backend: {target_backend}")
            
            # Retrieve dataset from current backend
            df = await self.retrieve_dataset(dataset)
            if df is None:
                return False
            
            # Store in target backend
            dataset_metadata = {
                "id": str(dataset.id),
                "name": dataset.name,
                "asset_class": dataset.asset_class.value,
                "row_count": len(df)
            }
            
            storage_info = await self.store_dataset(df, dataset_metadata, target_backend)
            
            # Update dataset record
            old_file_path = dataset.file_path
            old_backend = dataset.storage_backend
            
            dataset.file_path = storage_info["storage_path"]
            dataset.storage_backend = target_backend
            dataset.file_size = storage_info["file_size"]
            dataset.content_hash = storage_info["content_hash"]
            dataset.updated_at = datetime.utcnow()
            
            await db.commit()
            
            # Delete from old backend
            old_backend_obj = self.backends[old_backend]
            await old_backend_obj.delete_file(old_file_path)
            
            self.logger.info(f"Migrated dataset {dataset.id} from {old_backend} to {target_backend}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to migrate dataset: {str(e)}")
            return False
    
    async def optimize_storage(self, dataset: Dataset, db: AsyncSession) -> Dict[str, Any]:
        """Optimize storage for a dataset (recompress, reformat)."""
        try:
            # Retrieve current dataset
            df = await self.retrieve_dataset(dataset)
            if df is None:
                return {"success": False, "error": "Failed to retrieve dataset"}
            
            # Analyze current vs optimal format
            current_format = dataset.data_format.value if hasattr(dataset.data_format, 'value') else str(dataset.data_format)
            optimal_format = self._determine_optimal_format(df, {})
            
            optimization_info = {
                "original_size": dataset.file_size,
                "original_format": current_format,
                "optimal_format": optimal_format,
                "optimized": False
            }
            
            # Only optimize if different format would be better
            if optimal_format != current_format:
                # Store with optimal format
                dataset_metadata = {
                    "id": str(dataset.id),
                    "name": dataset.name,
                    "asset_class": dataset.asset_class.value,
                    "row_count": len(df)
                }
                
                storage_info = await self.store_dataset(df, dataset_metadata, dataset.storage_backend)
                
                # Delete old file
                old_file_path = dataset.file_path
                backend = self.backends[dataset.storage_backend]
                await backend.delete_file(old_file_path)
                
                # Update dataset record
                dataset.file_path = storage_info["storage_path"]
                dataset.data_format = DataFormat(optimal_format)
                dataset.file_size = storage_info["file_size"]
                dataset.content_hash = storage_info["content_hash"]
                dataset.updated_at = datetime.utcnow()
                
                await db.commit()
                
                optimization_info.update({
                    "optimized": True,
                    "new_size": storage_info["file_size"],
                    "size_reduction": dataset.file_size - storage_info["file_size"],
                    "compression_ratio": storage_info["file_size"] / dataset.file_size
                })
                
                self.logger.info(f"Optimized dataset {dataset.id}: {current_format} -> {optimal_format} "
                               f"({optimization_info['size_reduction']} bytes saved)")
            
            return {"success": True, "optimization": optimization_info}
            
        except Exception as e:
            self.logger.error(f"Failed to optimize dataset storage: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_storage_statistics(self, backend: str = None, 
                                   db: AsyncSession = None) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            stats = {}
            
            if backend:
                backends_to_check = [backend]
            else:
                backends_to_check = list(self.backends.keys())
            
            for backend_name in backends_to_check:
                backend_obj = self.backends[backend_name]
                
                # Get basic file listing
                files = await backend_obj.list_files(limit=1000)
                
                total_size = sum(f.get("file_size", 0) for f in files)
                total_files = len(files)
                
                stats[backend_name] = {
                    "total_files": total_files,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2)
                }
            
            # Add database statistics if available
            if db:
                from sqlalchemy import func
                
                # Dataset count by backend
                result = await db.execute(
                    select(Dataset.storage_backend, func.count(), func.sum(Dataset.file_size))
                    .group_by(Dataset.storage_backend)
                )
                
                db_stats = {}
                for backend_name, count, total_size in result.all():
                    db_stats[backend_name] = {
                        "dataset_count": count,
                        "total_size_bytes": total_size or 0,
                        "total_size_mb": round((total_size or 0) / (1024 * 1024), 2)
                    }
                
                stats["database_view"] = db_stats
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get storage statistics: {str(e)}")
            return {}
    
    def _determine_optimal_format(self, df: pd.DataFrame, 
                                 metadata: Dict[str, Any]) -> str:
        """Determine optimal storage format based on data characteristics."""
        try:
            row_count = len(df)
            column_count = len(df.columns)
            
            # Get data types
            numeric_cols = len(df.select_dtypes(include=['number']).columns)
            string_cols = len(df.select_dtypes(include=['object']).columns)
            datetime_cols = len(df.select_dtypes(include=['datetime']).columns)
            
            # Decision logic based on data characteristics
            
            # Large datasets with mostly numeric data -> Parquet
            if row_count > 100000 and numeric_cols / column_count > 0.7:
                return "parquet"
            
            # Time series data with many columns -> Parquet
            if datetime_cols > 0 and column_count > 10:
                return "parquet"
            
            # Small datasets -> Feather (fast read/write)
            if row_count < 10000:
                return "feather"
            
            # Many string columns -> Parquet (good compression)
            if string_cols / column_count > 0.5:
                return "parquet"
            
            # Default to Parquet for good balance of compression and speed
            return "parquet"
            
        except Exception as e:
            self.logger.warning(f"Failed to determine optimal format, using default: {str(e)}")
            return "parquet"
    
    async def cleanup_temp_files(self, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours."""
        try:
            temp_dir = Path("/tmp/ai_ml_temp")
            if not temp_dir.exists():
                return
            
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            cleaned_count = 0
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} temporary files")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp files: {str(e)}")
    
    def get_supported_backends(self) -> List[str]:
        """Get list of supported storage backends."""
        return list(self.backends.keys())
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported data formats."""
        return ["parquet", "feather", "hdf5", "csv_gzip"]