"""
Dataset catalog service for organizing, searching, and discovering datasets.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload

from app.models.dataset import (
    Dataset, DatasetStatistics, AssetClass, DataSource, 
    DatasetStatus, DataFrequency
)


class DatasetSearchFilter:
    """Encapsulates dataset search and filtering logic."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def build_query(self, base_query, filters: Dict[str, Any]):
        """Build filtered query based on search criteria."""
        
        # User filter (always required for security)
        if filters.get("user_id"):
            base_query = base_query.where(Dataset.user_id == UUID(filters["user_id"]))
        
        # Status filter
        if filters.get("status"):
            if isinstance(filters["status"], list):
                status_values = [DatasetStatus(s) for s in filters["status"]]
                base_query = base_query.where(Dataset.status.in_(status_values))
            else:
                base_query = base_query.where(Dataset.status == DatasetStatus(filters["status"]))
        
        # Asset class filter
        if filters.get("asset_class"):
            if isinstance(filters["asset_class"], list):
                asset_classes = [AssetClass(ac) for ac in filters["asset_class"]]
                base_query = base_query.where(Dataset.asset_class.in_(asset_classes))
            else:
                base_query = base_query.where(Dataset.asset_class == AssetClass(filters["asset_class"]))
        
        # Data source filter
        if filters.get("source"):
            if isinstance(filters["source"], list):
                sources = [DataSource(s) for s in filters["source"]]
                base_query = base_query.where(Dataset.source.in_(sources))
            else:
                base_query = base_query.where(Dataset.source == DataSource(filters["source"]))
        
        # Frequency filter
        if filters.get("frequency"):
            if isinstance(filters["frequency"], list):
                frequencies = [DataFrequency(f) for f in filters["frequency"]]
                base_query = base_query.where(Dataset.frequency.in_(frequencies))
            else:
                base_query = base_query.where(Dataset.frequency == DataFrequency(filters["frequency"]))
        
        # Symbols filter
        if filters.get("symbols"):
            symbols = filters["symbols"]
            if isinstance(symbols, str):
                symbols = [symbols]
            
            symbols_conditions = []
            for symbol in symbols:
                symbols_conditions.append(Dataset.symbols.contains([symbol]))
            
            if len(symbols_conditions) == 1:
                base_query = base_query.where(symbols_conditions[0])
            else:
                base_query = base_query.where(or_(*symbols_conditions))
        
        # Tags filter
        if filters.get("tags"):
            tags = filters["tags"]
            if isinstance(tags, str):
                tags = [tags]
            
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(Dataset.tags.contains([tag]))
            
            if len(tag_conditions) == 1:
                base_query = base_query.where(tag_conditions[0])
            else:
                base_query = base_query.where(and_(*tag_conditions))
        
        # Category filter
        if filters.get("category"):
            base_query = base_query.where(Dataset.category == filters["category"])
        
        # Public datasets filter
        if filters.get("is_public") is not None:
            base_query = base_query.where(Dataset.is_public == filters["is_public"])
        
        # Date range filters
        if filters.get("start_date_from"):
            start_date = datetime.fromisoformat(filters["start_date_from"])
            base_query = base_query.where(Dataset.start_date >= start_date)
        
        if filters.get("start_date_to"):
            start_date = datetime.fromisoformat(filters["start_date_to"])
            base_query = base_query.where(Dataset.start_date <= start_date)
        
        if filters.get("end_date_from"):
            end_date = datetime.fromisoformat(filters["end_date_from"])
            base_query = base_query.where(Dataset.end_date >= end_date)
        
        if filters.get("end_date_to"):
            end_date = datetime.fromisoformat(filters["end_date_to"])
            base_query = base_query.where(Dataset.end_date <= end_date)
        
        # Size filters
        if filters.get("min_rows"):
            base_query = base_query.where(Dataset.row_count >= filters["min_rows"])
        
        if filters.get("max_rows"):
            base_query = base_query.where(Dataset.row_count <= filters["max_rows"])
        
        if filters.get("min_size_mb"):
            min_bytes = filters["min_size_mb"] * 1024 * 1024
            base_query = base_query.where(Dataset.file_size >= min_bytes)
        
        if filters.get("max_size_mb"):
            max_bytes = filters["max_size_mb"] * 1024 * 1024
            base_query = base_query.where(Dataset.file_size <= max_bytes)
        
        # Quality filters
        if filters.get("min_quality_score"):
            base_query = base_query.where(Dataset.quality_score >= filters["min_quality_score"])
        
        if filters.get("validated_only"):
            base_query = base_query.where(Dataset.is_validated == True)
        
        # Text search
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            search_conditions = [
                Dataset.name.ilike(search_term),
                Dataset.description.ilike(search_term),
            ]
            base_query = base_query.where(or_(*search_conditions))
        
        return base_query
    
    def apply_sorting(self, query, sort_by: str = "created_at", sort_order: str = "desc"):
        """Apply sorting to the query."""
        
        # Map sort fields
        sort_fields = {
            "name": Dataset.name,
            "created_at": Dataset.created_at,
            "updated_at": Dataset.updated_at,
            "start_date": Dataset.start_date,
            "end_date": Dataset.end_date,
            "row_count": Dataset.row_count,
            "file_size": Dataset.file_size,
            "quality_score": Dataset.quality_score,
            "download_count": Dataset.download_count,
            "last_accessed": Dataset.last_accessed
        }
        
        sort_column = sort_fields.get(sort_by, Dataset.created_at)
        
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        return query
    
    def apply_pagination(self, query, limit: int = 50, offset: int = 0):
        """Apply pagination to the query."""
        limit = min(limit, 200)  # Cap at 200 for performance
        return query.limit(limit).offset(offset)


class DatasetCatalogService:
    """Service for dataset catalog operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.search_filter = DatasetSearchFilter()
    
    async def search_datasets(self, filters: Dict[str, Any], 
                            db: AsyncSession) -> Dict[str, Any]:
        """Search datasets with advanced filtering."""
        try:
            # Build base query
            base_query = select(Dataset).options(
                selectinload(Dataset.statistics)
            )
            
            # Apply filters
            filtered_query = self.search_filter.build_query(base_query, filters)
            
            # Get total count before pagination
            count_query = select(func.count()).select_from(
                self.search_filter.build_query(
                    select(Dataset), filters
                ).subquery()
            )
            count_result = await db.execute(count_query)
            total_count = count_result.scalar()
            
            # Apply sorting
            sort_by = filters.get("sort_by", "created_at")
            sort_order = filters.get("sort_order", "desc")
            sorted_query = self.search_filter.apply_sorting(filtered_query, sort_by, sort_order)
            
            # Apply pagination
            limit = filters.get("limit", 50)
            offset = filters.get("offset", 0)
            paginated_query = self.search_filter.apply_pagination(sorted_query, limit, offset)
            
            # Execute query
            result = await db.execute(paginated_query)
            datasets = result.scalars().all()
            
            # Convert to dictionaries
            dataset_list = []
            for dataset in datasets:
                dataset_dict = await self._dataset_to_dict(dataset)
                dataset_list.append(dataset_dict)
            
            # Calculate pagination info
            has_next = offset + limit < total_count
            has_prev = offset > 0
            total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
            current_page = (offset // limit) + 1 if limit > 0 else 1
            
            return {
                "datasets": dataset_list,
                "pagination": {
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "current_page": current_page,
                    "limit": limit,
                    "offset": offset,
                    "has_next": has_next,
                    "has_prev": has_prev
                },
                "filters": filters
            }
            
        except Exception as e:
            self.logger.error(f"Dataset search failed: {str(e)}")
            return {
                "datasets": [],
                "pagination": {
                    "total_count": 0,
                    "total_pages": 0,
                    "current_page": 1,
                    "limit": limit,
                    "offset": offset,
                    "has_next": False,
                    "has_prev": False
                },
                "error": str(e)
            }
    
    async def get_dataset_details(self, dataset_id: str, user_id: str, 
                                db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get detailed information about a dataset."""
        try:
            # Get dataset with all related data
            result = await db.execute(
                select(Dataset)
                .options(
                    selectinload(Dataset.statistics),
                    selectinload(Dataset.validation_reports)
                )
                .where(
                    Dataset.id == UUID(dataset_id),
                    or_(
                        Dataset.user_id == UUID(user_id),
                        Dataset.is_public == True
                    )
                )
            )
            
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return None
            
            # Update last accessed if owned by user
            if str(dataset.user_id) == user_id:
                dataset.last_accessed = datetime.utcnow()
                await db.commit()
            
            # Convert to detailed dictionary
            dataset_dict = await self._dataset_to_dict(dataset, include_details=True)
            
            return dataset_dict
            
        except Exception as e:
            self.logger.error(f"Failed to get dataset details: {str(e)}")
            return None
    
    async def get_dataset_statistics(self, dataset_id: str, user_id: str, 
                                   db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get comprehensive statistics for a dataset."""
        try:
            # Get dataset and statistics
            result = await db.execute(
                select(Dataset)
                .options(selectinload(Dataset.statistics))
                .where(
                    Dataset.id == UUID(dataset_id),
                    or_(
                        Dataset.user_id == UUID(user_id),
                        Dataset.is_public == True
                    )
                )
            )
            
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return None
            
            if not dataset.statistics:
                # Generate statistics if not available
                stats = await self._generate_dataset_statistics(dataset, db)
                return stats
            
            stats = dataset.statistics
            return {
                "dataset_id": str(dataset.id),
                "total_rows": stats.total_rows,
                "total_columns": stats.total_columns,
                "null_count": stats.null_count,
                "duplicate_count": stats.duplicate_count,
                "column_stats": stats.column_stats,
                "correlation_matrix": stats.correlation_matrix,
                "date_range": stats.date_range,
                "symbol_distribution": stats.symbol_distribution,
                "frequency_stats": stats.frequency_stats,
                "completeness_by_column": stats.completeness_by_column,
                "outlier_stats": stats.outlier_stats,
                "missing_data_patterns": stats.missing_data_patterns,
                "gaps_detected": stats.gaps_detected,
                "seasonality_stats": stats.seasonality_stats,
                "trend_analysis": stats.trend_analysis,
                "last_computed": stats.last_computed.isoformat(),
                "computation_duration": stats.computation_duration
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get dataset statistics: {str(e)}")
            return None
    
    async def get_catalog_summary(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get summary statistics for the user's dataset catalog."""
        try:
            # Total datasets by user
            total_result = await db.execute(
                select(func.count()).select_from(Dataset)
                .where(Dataset.user_id == UUID(user_id))
            )
            total_datasets = total_result.scalar()
            
            # Datasets by status
            status_result = await db.execute(
                select(Dataset.status, func.count())
                .where(Dataset.user_id == UUID(user_id))
                .group_by(Dataset.status)
            )
            status_distribution = {
                status.value: count for status, count in status_result.all()
            }
            
            # Datasets by asset class
            asset_result = await db.execute(
                select(Dataset.asset_class, func.count())
                .where(Dataset.user_id == UUID(user_id))
                .group_by(Dataset.asset_class)
            )
            asset_distribution = {
                asset_class.value: count for asset_class, count in asset_result.all()
            }
            
            # Datasets by source
            source_result = await db.execute(
                select(Dataset.source, func.count())
                .where(Dataset.user_id == UUID(user_id))
                .group_by(Dataset.source)
            )
            source_distribution = {
                source.value: count for source, count in source_result.all()
            }
            
            # Storage usage
            storage_result = await db.execute(
                select(func.sum(Dataset.file_size))
                .where(Dataset.user_id == UUID(user_id))
            )
            total_storage_bytes = storage_result.scalar() or 0
            total_storage_mb = round(total_storage_bytes / (1024 * 1024), 2)
            
            # Recent datasets
            recent_result = await db.execute(
                select(Dataset.name, Dataset.created_at, Dataset.status)
                .where(Dataset.user_id == UUID(user_id))
                .order_by(desc(Dataset.created_at))
                .limit(5)
            )
            recent_datasets = [
                {
                    "name": name,
                    "created_at": created_at.isoformat(),
                    "status": status.value
                }
                for name, created_at, status in recent_result.all()
            ]
            
            # Most used datasets
            popular_result = await db.execute(
                select(Dataset.name, Dataset.download_count)
                .where(Dataset.user_id == UUID(user_id))
                .order_by(desc(Dataset.download_count))
                .limit(5)
            )
            popular_datasets = [
                {
                    "name": name,
                    "download_count": download_count
                }
                for name, download_count in popular_result.all()
            ]
            
            return {
                "total_datasets": total_datasets,
                "status_distribution": status_distribution,
                "asset_class_distribution": asset_distribution,
                "source_distribution": source_distribution,
                "total_storage_mb": total_storage_mb,
                "recent_datasets": recent_datasets,
                "popular_datasets": popular_datasets
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get catalog summary: {str(e)}")
            return {}
    
    async def get_public_datasets(self, filters: Dict[str, Any], 
                                db: AsyncSession) -> Dict[str, Any]:
        """Get public datasets available to all users."""
        try:
            # Add public filter
            filters = filters.copy()
            filters["is_public"] = True
            
            # Remove user_id filter for public datasets
            if "user_id" in filters:
                del filters["user_id"]
            
            return await self.search_datasets(filters, db)
            
        except Exception as e:
            self.logger.error(f"Failed to get public datasets: {str(e)}")
            return {
                "datasets": [],
                "pagination": {
                    "total_count": 0,
                    "total_pages": 0,
                    "current_page": 1,
                    "limit": filters.get("limit", 50),
                    "offset": filters.get("offset", 0),
                    "has_next": False,
                    "has_prev": False
                },
                "error": str(e)
            }
    
    async def get_recommended_datasets(self, user_id: str, limit: int, 
                                     db: AsyncSession) -> List[Dict[str, Any]]:
        """Get recommended datasets based on user's usage patterns."""
        try:
            # Simple recommendation based on:
            # 1. Similar asset classes user has worked with
            # 2. High quality scores
            # 3. Popular public datasets
            
            # Get user's preferred asset classes
            user_assets_result = await db.execute(
                select(Dataset.asset_class, func.count())
                .where(Dataset.user_id == UUID(user_id))
                .group_by(Dataset.asset_class)
                .order_by(desc(func.count()))
                .limit(3)
            )
            preferred_assets = [asset for asset, _ in user_assets_result.all()]
            
            # Build recommendation query
            query = select(Dataset).where(
                and_(
                    Dataset.is_public == True,
                    Dataset.user_id != UUID(user_id),  # Exclude user's own datasets
                    Dataset.status == DatasetStatus.READY,
                    Dataset.quality_score > 0.7
                )
            )
            
            # Prefer datasets with similar asset classes
            if preferred_assets:
                query = query.where(Dataset.asset_class.in_(preferred_assets))
            
            # Order by quality score and popularity
            query = query.order_by(
                desc(Dataset.quality_score),
                desc(Dataset.download_count)
            ).limit(limit)
            
            result = await db.execute(query)
            datasets = result.scalars().all()
            
            # Convert to dictionaries
            recommended = []
            for dataset in datasets:
                dataset_dict = await self._dataset_to_dict(dataset)
                dataset_dict["recommendation_reason"] = "Similar to your datasets"
                recommended.append(dataset_dict)
            
            return recommended
            
        except Exception as e:
            self.logger.error(f"Failed to get recommended datasets: {str(e)}")
            return []
    
    async def get_dataset_tags(self, db: AsyncSession) -> List[str]:
        """Get all unique tags used in datasets."""
        try:
            # Use raw SQL to unnest array and get distinct values
            result = await db.execute(
                text("SELECT DISTINCT unnest(tags) as tag FROM datasets WHERE tags IS NOT NULL ORDER BY tag")
            )
            
            tags = [row[0] for row in result.all() if row[0]]
            return tags
            
        except Exception as e:
            self.logger.error(f"Failed to get dataset tags: {str(e)}")
            return []
    
    async def get_dataset_categories(self, db: AsyncSession) -> List[str]:
        """Get all unique categories used in datasets."""
        try:
            result = await db.execute(
                select(Dataset.category)
                .distinct()
                .where(Dataset.category.isnot(None))
                .order_by(Dataset.category)
            )
            
            categories = [row[0] for row in result.all() if row[0]]
            return categories
            
        except Exception as e:
            self.logger.error(f"Failed to get dataset categories: {str(e)}")
            return []
    
    async def _dataset_to_dict(self, dataset: Dataset, include_details: bool = False) -> Dict[str, Any]:
        """Convert dataset model to dictionary."""
        try:
            dataset_dict = {
                "id": str(dataset.id),
                "name": dataset.name,
                "description": dataset.description,
                "source": dataset.source.value,
                "asset_class": dataset.asset_class.value,
                "symbols": dataset.symbols,
                "frequency": dataset.frequency.value if dataset.frequency else None,
                "start_date": dataset.start_date.isoformat(),
                "end_date": dataset.end_date.isoformat(),
                "row_count": dataset.row_count,
                "file_size": dataset.file_size,
                "file_size_mb": round(dataset.file_size / (1024 * 1024), 2),
                "data_format": dataset.data_format.value,
                "status": dataset.status.value,
                "is_validated": dataset.is_validated,
                "quality_score": dataset.quality_score,
                "completeness_score": dataset.completeness_score,
                "tags": dataset.tags,
                "category": dataset.category,
                "is_public": dataset.is_public,
                "download_count": dataset.download_count,
                "created_at": dataset.created_at.isoformat(),
                "updated_at": dataset.updated_at.isoformat(),
                "last_accessed": dataset.last_accessed.isoformat() if dataset.last_accessed else None
            }
            
            if include_details:
                dataset_dict.update({
                    "columns": dataset.columns,
                    "data_types": dataset.data_types,
                    "validation_errors": dataset.validation_errors,
                    "validation_warnings": dataset.validation_warnings,
                    "storage_backend": dataset.storage_backend,
                    "compression": dataset.compression,
                    "content_hash": dataset.content_hash,
                    "processing_config": dataset.processing_config,
                    "feature_columns": dataset.feature_columns,
                    "target_columns": dataset.target_columns
                })
                
                # Include validation reports
                if hasattr(dataset, 'validation_reports') and dataset.validation_reports:
                    latest_report = max(dataset.validation_reports, 
                                      key=lambda r: r.created_at)
                    dataset_dict["latest_validation"] = {
                        "is_valid": latest_report.is_valid,
                        "validation_type": latest_report.validation_type,
                        "created_at": latest_report.created_at.isoformat()
                    }
            
            return dataset_dict
            
        except Exception as e:
            self.logger.error(f"Failed to convert dataset to dict: {str(e)}")
            return {"error": "Failed to serialize dataset"}
    
    async def _generate_dataset_statistics(self, dataset: Dataset, 
                                         db: AsyncSession) -> Dict[str, Any]:
        """Generate basic statistics for a dataset that doesn't have them."""
        try:
            # Return basic info from dataset record
            return {
                "dataset_id": str(dataset.id),
                "total_rows": dataset.row_count,
                "total_columns": len(dataset.columns) if dataset.columns else 0,
                "null_count": 0,  # Would need to analyze actual data
                "duplicate_count": 0,  # Would need to analyze actual data
                "column_stats": {},
                "correlation_matrix": {},
                "date_range": {
                    "start": dataset.start_date.isoformat(),
                    "end": dataset.end_date.isoformat()
                },
                "symbol_distribution": {},
                "frequency_stats": {},
                "completeness_by_column": {},
                "outlier_stats": {},
                "missing_data_patterns": {},
                "gaps_detected": {},
                "seasonality_stats": {},
                "trend_analysis": {},
                "last_computed": datetime.utcnow().isoformat(),
                "computation_duration": 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate dataset statistics: {str(e)}")
            return {}