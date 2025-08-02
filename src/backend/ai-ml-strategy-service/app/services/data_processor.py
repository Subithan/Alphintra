"""
Data processing service for cleaning, transformation, and feature engineering.
"""

import logging
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.dataset import (
    Dataset, DataProcessingJob, DatasetStatus, DataFormat, AssetClass
)
from app.core.config import get_settings


class DataProcessor:
    """Base class for data processing operations."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def process(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Process the dataframe."""
        raise NotImplementedError("Subclasses must implement process method")
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this processor."""
        raise NotImplementedError("Subclasses must implement get_config_schema method")


class MissingValueProcessor(DataProcessor):
    """Handle missing values in datasets."""
    
    def __init__(self):
        super().__init__(
            "missing_value_handler",
            "Handle missing values through various imputation strategies"
        )
    
    def process(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Process missing values."""
        try:
            strategy = config.get("strategy", "drop")
            columns = config.get("columns", df.columns.tolist())
            
            # Filter to specified columns
            target_columns = [col for col in columns if col in df.columns]
            
            if strategy == "drop_rows":
                # Drop rows with any missing values in target columns
                df_processed = df.dropna(subset=target_columns)
                
            elif strategy == "drop_columns":
                # Drop columns with missing values above threshold
                threshold = config.get("threshold", 0.5)
                missing_ratios = df[target_columns].isnull().sum() / len(df)
                columns_to_drop = missing_ratios[missing_ratios > threshold].index.tolist()
                df_processed = df.drop(columns=columns_to_drop)
                
            elif strategy == "forward_fill":
                # Forward fill missing values
                df_processed = df.copy()
                df_processed[target_columns] = df_processed[target_columns].fillna(method='ffill')
                
            elif strategy == "backward_fill":
                # Backward fill missing values
                df_processed = df.copy()
                df_processed[target_columns] = df_processed[target_columns].fillna(method='bfill')
                
            elif strategy == "interpolate":
                # Interpolate missing values
                method = config.get("interpolation_method", "linear")
                df_processed = df.copy()
                
                for col in target_columns:
                    if df_processed[col].dtype in ['float64', 'int64']:
                        df_processed[col] = df_processed[col].interpolate(method=method)
                
            elif strategy == "mean_impute":
                # Mean imputation for numeric columns
                df_processed = df.copy()
                numeric_columns = df_processed[target_columns].select_dtypes(include=[np.number]).columns
                
                imputer = SimpleImputer(strategy='mean')
                df_processed[numeric_columns] = imputer.fit_transform(df_processed[numeric_columns])
                
            elif strategy == "median_impute":
                # Median imputation for numeric columns
                df_processed = df.copy()
                numeric_columns = df_processed[target_columns].select_dtypes(include=[np.number]).columns
                
                imputer = SimpleImputer(strategy='median')
                df_processed[numeric_columns] = imputer.fit_transform(df_processed[numeric_columns])
                
            elif strategy == "mode_impute":
                # Mode imputation for categorical columns
                df_processed = df.copy()
                categorical_columns = df_processed[target_columns].select_dtypes(include=['object']).columns
                
                imputer = SimpleImputer(strategy='most_frequent')
                df_processed[categorical_columns] = imputer.fit_transform(df_processed[categorical_columns])
                
            elif strategy == "knn_impute":
                # KNN imputation
                n_neighbors = config.get("n_neighbors", 5)
                df_processed = df.copy()
                numeric_columns = df_processed[target_columns].select_dtypes(include=[np.number]).columns
                
                imputer = KNNImputer(n_neighbors=n_neighbors)
                df_processed[numeric_columns] = imputer.fit_transform(df_processed[numeric_columns])
                
            else:
                raise ValueError(f"Unknown missing value strategy: {strategy}")
            
            self.logger.info(f"Processed missing values using {strategy} strategy")
            return df_processed
            
        except Exception as e:
            self.logger.error(f"Missing value processing failed: {str(e)}")
            raise
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "strategy": {
                "type": "string",
                "enum": ["drop_rows", "drop_columns", "forward_fill", "backward_fill", 
                        "interpolate", "mean_impute", "median_impute", "mode_impute", "knn_impute"],
                "default": "drop_rows",
                "description": "Strategy for handling missing values"
            },
            "columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Columns to process (default: all columns)"
            },
            "threshold": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "default": 0.5,
                "description": "Threshold for drop_columns strategy"
            },
            "interpolation_method": {
                "type": "string",
                "enum": ["linear", "polynomial", "spline"],
                "default": "linear",
                "description": "Interpolation method"
            },
            "n_neighbors": {
                "type": "integer",
                "minimum": 1,
                "default": 5,
                "description": "Number of neighbors for KNN imputation"
            }
        }


class OutlierProcessor(DataProcessor):
    """Handle outliers in datasets."""
    
    def __init__(self):
        super().__init__(
            "outlier_handler",
            "Detect and handle outliers using various methods"
        )
    
    def process(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Process outliers."""
        try:
            method = config.get("method", "iqr")
            action = config.get("action", "remove")
            columns = config.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
            
            df_processed = df.copy()
            
            for col in columns:
                if col not in df_processed.columns:
                    continue
                
                # Detect outliers
                outlier_mask = self._detect_outliers(df_processed[col], method, config)
                
                if action == "remove":
                    # Remove outlier rows
                    df_processed = df_processed[~outlier_mask]
                    
                elif action == "cap":
                    # Cap outliers to threshold values
                    if method == "iqr":
                        Q1 = df_processed[col].quantile(0.25)
                        Q3 = df_processed[col].quantile(0.75)
                        IQR = Q3 - Q1
                        multiplier = config.get("multiplier", 1.5)
                        
                        lower_bound = Q1 - multiplier * IQR
                        upper_bound = Q3 + multiplier * IQR
                        
                        df_processed[col] = df_processed[col].clip(lower_bound, upper_bound)
                        
                    elif method == "zscore":
                        threshold = config.get("threshold", 3)
                        mean = df_processed[col].mean()
                        std = df_processed[col].std()
                        
                        lower_bound = mean - threshold * std
                        upper_bound = mean + threshold * std
                        
                        df_processed[col] = df_processed[col].clip(lower_bound, upper_bound)
                
                elif action == "transform":
                    # Transform outliers (e.g., log transformation)
                    transform_method = config.get("transform_method", "log")
                    
                    if transform_method == "log":
                        # Apply log transformation (add small constant to handle zeros)
                        df_processed[col] = np.log1p(df_processed[col])
                    elif transform_method == "sqrt":
                        # Apply square root transformation
                        df_processed[col] = np.sqrt(np.abs(df_processed[col]))
                    elif transform_method == "box_cox":
                        # Box-Cox transformation
                        df_processed[col], _ = stats.boxcox(df_processed[col] + 1)  # Add 1 to handle zeros
            
            self.logger.info(f"Processed outliers using {method} method with {action} action")
            return df_processed
            
        except Exception as e:
            self.logger.error(f"Outlier processing failed: {str(e)}")
            raise
    
    def _detect_outliers(self, series: pd.Series, method: str, config: Dict[str, Any]) -> pd.Series:
        """Detect outliers in a series."""
        if method == "iqr":
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            multiplier = config.get("multiplier", 1.5)
            
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            
            return (series < lower_bound) | (series > upper_bound)
            
        elif method == "zscore":
            threshold = config.get("threshold", 3)
            z_scores = np.abs(stats.zscore(series.dropna()))
            return pd.Series(z_scores > threshold, index=series.index)
            
        elif method == "modified_zscore":
            threshold = config.get("threshold", 3.5)
            median = series.median()
            mad = np.median(np.abs(series - median))
            modified_z_scores = 0.6745 * (series - median) / mad
            return np.abs(modified_z_scores) > threshold
            
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "method": {
                "type": "string",
                "enum": ["iqr", "zscore", "modified_zscore"],
                "default": "iqr",
                "description": "Outlier detection method"
            },
            "action": {
                "type": "string",
                "enum": ["remove", "cap", "transform"],
                "default": "remove",
                "description": "Action to take on outliers"
            },
            "columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Columns to process (default: all numeric columns)"
            },
            "multiplier": {
                "type": "number",
                "default": 1.5,
                "description": "IQR multiplier for outlier detection"
            },
            "threshold": {
                "type": "number",
                "default": 3,
                "description": "Z-score threshold for outlier detection"
            },
            "transform_method": {
                "type": "string",
                "enum": ["log", "sqrt", "box_cox"],
                "default": "log",
                "description": "Transformation method for outliers"
            }
        }


class ScalingProcessor(DataProcessor):
    """Scale/normalize numeric features."""
    
    def __init__(self):
        super().__init__(
            "scaler",
            "Scale and normalize numeric features"
        )
    
    def process(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Scale numeric features."""
        try:
            method = config.get("method", "standard")
            columns = config.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
            
            # Filter to existing columns
            target_columns = [col for col in columns if col in df.columns]
            
            if not target_columns:
                self.logger.warning("No numeric columns found for scaling")
                return df.copy()
            
            df_processed = df.copy()
            
            # Choose scaler
            if method == "standard":
                scaler = StandardScaler()
            elif method == "minmax":
                feature_range = config.get("feature_range", (0, 1))
                scaler = MinMaxScaler(feature_range=feature_range)
            elif method == "robust":
                scaler = RobustScaler()
            else:
                raise ValueError(f"Unknown scaling method: {method}")
            
            # Apply scaling
            df_processed[target_columns] = scaler.fit_transform(df_processed[target_columns])
            
            self.logger.info(f"Applied {method} scaling to {len(target_columns)} columns")
            return df_processed
            
        except Exception as e:
            self.logger.error(f"Scaling failed: {str(e)}")
            raise
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "method": {
                "type": "string",
                "enum": ["standard", "minmax", "robust"],
                "default": "standard",
                "description": "Scaling method"
            },
            "columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Columns to scale (default: all numeric columns)"
            },
            "feature_range": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 2,
                "maxItems": 2,
                "default": [0, 1],
                "description": "Feature range for MinMax scaling"
            }
        }


class FeatureEngineeringProcessor(DataProcessor):
    """Create derived features from existing data."""
    
    def __init__(self):
        super().__init__(
            "feature_engineer",
            "Create derived features and technical indicators"
        )
    
    def process(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Create engineered features."""
        try:
            features = config.get("features", [])
            df_processed = df.copy()
            
            for feature_config in features:
                feature_type = feature_config.get("type")
                
                if feature_type == "sma":
                    df_processed = self._add_sma(df_processed, feature_config)
                elif feature_type == "ema":
                    df_processed = self._add_ema(df_processed, feature_config)
                elif feature_type == "rsi":
                    df_processed = self._add_rsi(df_processed, feature_config)
                elif feature_type == "bollinger_bands":
                    df_processed = self._add_bollinger_bands(df_processed, feature_config)
                elif feature_type == "macd":
                    df_processed = self._add_macd(df_processed, feature_config)
                elif feature_type == "returns":
                    df_processed = self._add_returns(df_processed, feature_config)
                elif feature_type == "volatility":
                    df_processed = self._add_volatility(df_processed, feature_config)
                elif feature_type == "lag_features":
                    df_processed = self._add_lag_features(df_processed, feature_config)
                elif feature_type == "rolling_stats":
                    df_processed = self._add_rolling_stats(df_processed, feature_config)
                else:
                    self.logger.warning(f"Unknown feature type: {feature_type}")
            
            self.logger.info(f"Created {len(features)} engineered features")
            return df_processed
            
        except Exception as e:
            self.logger.error(f"Feature engineering failed: {str(e)}")
            raise
    
    def _add_sma(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Add Simple Moving Average."""
        column = config.get("column", "close")
        period = config.get("period", 20)
        name = config.get("name", f"sma_{period}")
        
        if column in df.columns:
            df[name] = df[column].rolling(window=period).mean()
        
        return df
    
    def _add_ema(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Add Exponential Moving Average."""
        column = config.get("column", "close")
        period = config.get("period", 20)
        name = config.get("name", f"ema_{period}")
        
        if column in df.columns:
            df[name] = df[column].ewm(span=period).mean()
        
        return df
    
    def _add_rsi(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Add Relative Strength Index."""
        column = config.get("column", "close")
        period = config.get("period", 14)
        name = config.get("name", "rsi")
        
        if column in df.columns:
            delta = df[column].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[name] = 100 - (100 / (1 + rs))
        
        return df
    
    def _add_bollinger_bands(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Add Bollinger Bands."""
        column = config.get("column", "close")
        period = config.get("period", 20)
        std_dev = config.get("std_dev", 2)
        
        if column in df.columns:
            sma = df[column].rolling(window=period).mean()
            std = df[column].rolling(window=period).std()
            
            df[f"bb_middle"] = sma
            df[f"bb_upper"] = sma + (std * std_dev)
            df[f"bb_lower"] = sma - (std * std_dev)
            df[f"bb_width"] = df[f"bb_upper"] - df[f"bb_lower"]
        
        return df
    
    def _add_macd(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Add MACD indicator."""
        column = config.get("column", "close")
        fast_period = config.get("fast_period", 12)
        slow_period = config.get("slow_period", 26)
        signal_period = config.get("signal_period", 9)
        
        if column in df.columns:
            ema_fast = df[column].ewm(span=fast_period).mean()
            ema_slow = df[column].ewm(span=slow_period).mean()
            
            df["macd"] = ema_fast - ema_slow
            df["macd_signal"] = df["macd"].ewm(span=signal_period).mean()
            df["macd_histogram"] = df["macd"] - df["macd_signal"]
        
        return df
    
    def _add_returns(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Add price returns."""
        column = config.get("column", "close")
        periods = config.get("periods", [1])
        
        if column in df.columns:
            for period in periods:
                df[f"return_{period}"] = df[column].pct_change(periods=period)
        
        return df
    
    def _add_volatility(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Add volatility measures."""
        column = config.get("column", "close")
        window = config.get("window", 20)
        name = config.get("name", f"volatility_{window}")
        
        if column in df.columns:
            returns = df[column].pct_change()
            df[name] = returns.rolling(window=window).std()
        
        return df
    
    def _add_lag_features(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Add lagged features."""
        column = config.get("column", "close")
        lags = config.get("lags", [1, 2, 3])
        
        if column in df.columns:
            for lag in lags:
                df[f"{column}_lag_{lag}"] = df[column].shift(lag)
        
        return df
    
    def _add_rolling_stats(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Add rolling statistics."""
        column = config.get("column", "close")
        window = config.get("window", 20)
        stats_list = config.get("stats", ["mean", "std", "min", "max"])
        
        if column in df.columns:
            rolling = df[column].rolling(window=window)
            
            for stat in stats_list:
                if stat == "mean":
                    df[f"{column}_rolling_mean_{window}"] = rolling.mean()
                elif stat == "std":
                    df[f"{column}_rolling_std_{window}"] = rolling.std()
                elif stat == "min":
                    df[f"{column}_rolling_min_{window}"] = rolling.min()
                elif stat == "max":
                    df[f"{column}_rolling_max_{window}"] = rolling.max()
                elif stat == "median":
                    df[f"{column}_rolling_median_{window}"] = rolling.median()
        
        return df
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "features": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["sma", "ema", "rsi", "bollinger_bands", "macd", 
                                   "returns", "volatility", "lag_features", "rolling_stats"]
                        },
                        "column": {"type": "string"},
                        "period": {"type": "integer"},
                        "name": {"type": "string"}
                    },
                    "required": ["type"]
                },
                "description": "List of features to engineer"
            }
        }


class DataProcessingService:
    """Main service for coordinating data processing operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # Initialize processors
        self.processors = {
            "missing_values": MissingValueProcessor(),
            "outliers": OutlierProcessor(),
            "scaling": ScalingProcessor(),
            "feature_engineering": FeatureEngineeringProcessor()
        }
    
    async def create_processing_job(self, job_data: Dict[str, Any], 
                                  user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Create a new data processing job."""
        try:
            # Validate dataset exists
            dataset_id = job_data.get("dataset_id")
            result = await db.execute(
                select(Dataset).where(
                    Dataset.id == UUID(dataset_id),
                    Dataset.user_id == UUID(user_id)
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {"success": False, "error": "Dataset not found"}
            
            # Validate processing steps
            processing_steps = job_data.get("processing_steps", [])
            if not processing_steps:
                return {"success": False, "error": "No processing steps provided"}
            
            # Validate step configurations
            validation_errors = []
            for step in processing_steps:
                processor_type = step.get("processor")
                if processor_type not in self.processors:
                    validation_errors.append(f"Unknown processor: {processor_type}")
            
            if validation_errors:
                return {
                    "success": False,
                    "error": "Invalid processing configuration",
                    "validation_errors": validation_errors
                }
            
            # Create processing job
            job = DataProcessingJob(
                dataset_id=UUID(dataset_id),
                user_id=UUID(user_id),
                job_name=job_data["job_name"],
                job_type=job_data.get("job_type", "cleaning"),
                processing_config={"steps": processing_steps},
                input_columns=job_data.get("input_columns", []),
                output_columns=job_data.get("output_columns", [])
            )
            
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            self.logger.info(f"Created processing job {job.id} for dataset {dataset_id}")
            
            return {
                "success": True,
                "job_id": str(job.id)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create processing job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def execute_processing_job(self, job_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Execute a data processing job."""
        try:
            # Get job and dataset
            result = await db.execute(
                select(DataProcessingJob).where(DataProcessingJob.id == UUID(job_id))
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return {"success": False, "error": "Job not found"}
            
            if job.status == "running":
                return {"success": False, "error": "Job is already running"}
            
            # Update job status
            job.status = "running"
            job.start_time = datetime.utcnow()
            job.progress = 0.0
            await db.commit()
            
            try:
                # Load input dataset
                result = await db.execute(
                    select(Dataset).where(Dataset.id == job.dataset_id)
                )
                dataset = result.scalar_one_or_none()
                
                if not dataset:
                    raise ValueError("Dataset not found")
                
                df = await self._load_dataset(dataset)
                if df is None:
                    raise ValueError("Failed to load dataset")
                
                original_shape = df.shape
                self.logger.info(f"Loaded dataset with shape {original_shape}")
                
                # Execute processing steps
                processing_steps = job.processing_config.get("steps", [])
                total_steps = len(processing_steps)
                
                job.logs = []
                
                for i, step in enumerate(processing_steps):
                    processor_type = step.get("processor")
                    processor_config = step.get("config", {})
                    
                    self.logger.info(f"Executing step {i+1}/{total_steps}: {processor_type}")
                    
                    # Update progress
                    job.progress = (i / total_steps) * 100
                    await db.commit()
                    
                    # Execute processing step
                    processor = self.processors[processor_type]
                    df = processor.process(df, processor_config)
                    
                    # Log step completion
                    job.logs.append({
                        "step": i + 1,
                        "processor": processor_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        "shape_before": original_shape,
                        "shape_after": df.shape,
                        "message": f"Completed {processor_type} processing"
                    })
                    
                    original_shape = df.shape
                
                # Save processed dataset
                output_dataset_id = await self._save_processed_dataset(
                    df, job, dataset, db
                )
                
                # Update job with results
                job.status = "completed"
                job.end_time = datetime.utcnow()
                job.duration = (job.end_time - job.start_time).total_seconds()
                job.progress = 100.0
                job.processed_rows = len(df)
                job.output_dataset_id = UUID(output_dataset_id)
                job.output_columns = df.columns.tolist()
                
                job.logs.append({
                    "step": "final",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Processing completed successfully. Output dataset: {output_dataset_id}"
                })
                
                await db.commit()
                
                self.logger.info(f"Completed processing job {job_id}, created dataset {output_dataset_id}")
                
                return {
                    "success": True,
                    "output_dataset_id": output_dataset_id,
                    "processed_rows": len(df),
                    "processing_time": job.duration
                }
                
            except Exception as e:
                # Update job with error
                job.status = "failed"
                job.end_time = datetime.utcnow()
                job.duration = (job.end_time - job.start_time).total_seconds() if job.start_time else 0
                job.error_message = str(e)
                
                if not job.logs:
                    job.logs = []
                job.logs.append({
                    "step": "error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Processing failed: {str(e)}"
                })
                
                await db.commit()
                raise
                
        except Exception as e:
            self.logger.error(f"Failed to execute processing job {job_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _load_dataset(self, dataset: Dataset) -> Optional[pd.DataFrame]:
        """Load dataset from storage."""
        try:
            if not dataset.file_path or not os.path.exists(dataset.file_path):
                self.logger.error(f"Dataset file not found: {dataset.file_path}")
                return None
            
            # Load based on format
            if dataset.data_format == DataFormat.PARQUET:
                df = pd.read_parquet(dataset.file_path)
            elif dataset.data_format == DataFormat.CSV:
                df = pd.read_csv(dataset.file_path)
            elif dataset.data_format == DataFormat.JSON:
                df = pd.read_json(dataset.file_path)
            else:
                self.logger.error(f"Unsupported data format: {dataset.data_format}")
                return None
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load dataset: {str(e)}")
            return None
    
    async def _save_processed_dataset(self, df: pd.DataFrame, job: DataProcessingJob, 
                                    original_dataset: Dataset, db: AsyncSession) -> str:
        """Save processed data as a new dataset."""
        try:
            # Generate file path
            dataset_id = str(uuid4())
            filename = f"processed_data_{dataset_id}.parquet"
            storage_dir = os.path.join(self.settings.DATA_STORAGE_PATH, "processed")
            os.makedirs(storage_dir, exist_ok=True)
            file_path = os.path.join(storage_dir, filename)
            
            # Save data to parquet
            df.to_parquet(file_path, index=False)
            file_size = os.path.getsize(file_path)
            
            # Calculate content hash
            with open(file_path, 'rb') as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Create dataset record
            dataset = Dataset(
                id=UUID(dataset_id),
                user_id=job.user_id,
                name=f"{job.job_name} - Processed Data",
                description=f"Processed version of '{original_dataset.name}' using {job.job_type} pipeline",
                source=original_dataset.source,
                asset_class=original_dataset.asset_class,
                symbols=original_dataset.symbols,
                frequency=original_dataset.frequency,
                start_date=original_dataset.start_date,
                end_date=original_dataset.end_date,
                columns=df.columns.tolist(),
                row_count=len(df),
                file_size=file_size,
                data_format=DataFormat.PARQUET,
                status=DatasetStatus.READY,
                is_validated=False,
                file_path=file_path,
                original_filename=filename,
                content_hash=content_hash,
                storage_backend="local",
                compression="snappy",
                data_types={str(col): str(df[col].dtype) for col in df.columns},
                tags=original_dataset.tags + ["processed", job.job_type],
                category=original_dataset.category,
                processing_config={
                    "source_dataset_id": str(original_dataset.id),
                    "processing_job_id": str(job.id),
                    "processing_steps": job.processing_config.get("steps", [])
                }
            )
            
            db.add(dataset)
            await db.commit()
            
            return dataset_id
            
        except Exception as e:
            self.logger.error(f"Failed to save processed dataset: {str(e)}")
            raise
    
    def get_available_processors(self) -> Dict[str, Any]:
        """Get information about available processors."""
        processors_info = {}
        
        for name, processor in self.processors.items():
            processors_info[name] = {
                "name": processor.name,
                "description": processor.description,
                "config_schema": processor.get_config_schema()
            }
        
        return processors_info