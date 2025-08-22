"""
Comprehensive dataset validation service with quality checks.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID
import pandas as pd
import numpy as np
from scipy import stats

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.dataset import (
    Dataset, DatasetValidationReport, DataQualityRule, 
    AssetClass, DataFrequency, DatasetStatus
)


class ValidationRule:
    """Base class for validation rules."""
    
    def __init__(self, name: str, description: str, severity: str = "warning"):
        self.name = name
        self.description = description
        self.severity = severity  # error, warning, info
    
    def validate(self, df: pd.DataFrame, dataset: Dataset) -> Dict[str, Any]:
        """Validate the dataset."""
        raise NotImplementedError("Subclasses must implement validate method")


class SchemaValidationRule(ValidationRule):
    """Validate dataset schema and structure."""
    
    def __init__(self):
        super().__init__(
            "schema_validation",
            "Validates dataset schema and column structure",
            "error"
        )
    
    def validate(self, df: pd.DataFrame, dataset: Dataset) -> Dict[str, Any]:
        """Validate dataset schema."""
        errors = []
        warnings = []
        suggestions = []
        metrics = {}
        
        # Check if DataFrame is empty
        if df.empty:
            errors.append({
                "type": "empty_dataset",
                "message": "Dataset is empty",
                "column": None
            })
            return {
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions,
                "metrics": metrics
            }
        
        # Required columns for market data
        required_columns = self._get_required_columns(dataset.asset_class)
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append({
                "type": "missing_columns",
                "message": f"Missing required columns: {missing_columns}",
                "columns": missing_columns
            })
        
        # Check for duplicate columns
        duplicate_columns = df.columns[df.columns.duplicated()].tolist()
        if duplicate_columns:
            errors.append({
                "type": "duplicate_columns",
                "message": f"Duplicate columns found: {duplicate_columns}",
                "columns": duplicate_columns
            })
        
        # Validate column data types
        type_issues = self._validate_column_types(df, dataset.asset_class)
        warnings.extend(type_issues)
        
        # Check for recommended columns
        recommended_columns = self._get_recommended_columns(dataset.asset_class)
        missing_recommended = [col for col in recommended_columns if col not in df.columns]
        
        if missing_recommended:
            suggestions.append({
                "type": "missing_recommended_columns",
                "message": f"Consider adding recommended columns: {missing_recommended}",
                "columns": missing_recommended
            })
        
        # Schema metrics
        metrics.update({
            "total_columns": len(df.columns),
            "required_columns_present": len(required_columns) - len(missing_columns),
            "recommended_columns_present": len(recommended_columns) - len(missing_recommended),
            "duplicate_columns_count": len(duplicate_columns)
        })
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "metrics": metrics
        }
    
    def _get_required_columns(self, asset_class: AssetClass) -> List[str]:
        """Get required columns for asset class."""
        base_columns = ["timestamp"]
        
        if asset_class in [AssetClass.CRYPTO, AssetClass.STOCKS, AssetClass.FOREX]:
            base_columns.extend(["open", "high", "low", "close", "volume"])
        elif asset_class == AssetClass.OPTIONS:
            base_columns.extend(["strike", "expiry", "option_type", "premium"])
        
        return base_columns
    
    def _get_recommended_columns(self, asset_class: AssetClass) -> List[str]:
        """Get recommended columns for asset class."""
        recommended = ["symbol"]
        
        if asset_class in [AssetClass.CRYPTO, AssetClass.STOCKS]:
            recommended.extend(["trades", "vwap"])
        
        return recommended
    
    def _validate_column_types(self, df: pd.DataFrame, asset_class: AssetClass) -> List[Dict[str, Any]]:
        """Validate column data types."""
        warnings = []
        
        # Expected types for common columns
        expected_types = {
            "timestamp": ["datetime64", "object"],
            "open": ["float64", "int64"],
            "high": ["float64", "int64"],
            "low": ["float64", "int64"],
            "close": ["float64", "int64"],
            "volume": ["float64", "int64"],
            "symbol": ["object"]
        }
        
        for col, expected in expected_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if not any(exp in actual_type for exp in expected):
                    warnings.append({
                        "type": "unexpected_column_type",
                        "message": f"Column '{col}' has type '{actual_type}', expected one of {expected}",
                        "column": col,
                        "actual_type": actual_type,
                        "expected_types": expected
                    })
        
        return warnings


class DataQualityValidationRule(ValidationRule):
    """Validate data quality metrics."""
    
    def __init__(self):
        super().__init__(
            "data_quality_validation",
            "Validates data quality and completeness",
            "warning"
        )
    
    def validate(self, df: pd.DataFrame, dataset: Dataset) -> Dict[str, Any]:
        """Validate data quality."""
        errors = []
        warnings = []
        suggestions = []
        metrics = {}
        
        # Check for missing values
        missing_stats = self._analyze_missing_values(df)
        metrics.update(missing_stats["metrics"])
        
        if missing_stats["high_missing_columns"]:
            warnings.append({
                "type": "high_missing_values",
                "message": f"Columns with >20% missing values: {missing_stats['high_missing_columns']}",
                "columns": missing_stats["high_missing_columns"]
            })
        
        # Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        metrics["duplicate_rows"] = int(duplicate_count)
        
        if duplicate_count > 0:
            duplicate_pct = (duplicate_count / len(df)) * 100
            if duplicate_pct > 5:
                warnings.append({
                    "type": "high_duplicate_rows",
                    "message": f"High percentage of duplicate rows: {duplicate_pct:.1f}%",
                    "duplicate_count": int(duplicate_count),
                    "duplicate_percentage": round(duplicate_pct, 2)
                })
            else:
                suggestions.append({
                    "type": "duplicate_rows",
                    "message": f"Found {duplicate_count} duplicate rows ({duplicate_pct:.1f}%)",
                    "duplicate_count": int(duplicate_count)
                })
        
        # Validate numeric columns
        numeric_issues = self._validate_numeric_columns(df)
        warnings.extend(numeric_issues["warnings"])
        suggestions.extend(numeric_issues["suggestions"])
        metrics.update(numeric_issues["metrics"])
        
        # Validate timestamp column
        timestamp_issues = self._validate_timestamp_column(df, dataset)
        warnings.extend(timestamp_issues["warnings"])
        suggestions.extend(timestamp_issues["suggestions"])
        metrics.update(timestamp_issues["metrics"])
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(metrics, len(df))
        metrics["quality_score"] = quality_score
        
        if quality_score < 0.7:
            warnings.append({
                "type": "low_quality_score",
                "message": f"Low data quality score: {quality_score:.2f}",
                "quality_score": quality_score
            })
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "metrics": metrics
        }
    
    def _analyze_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze missing values in the dataset."""
        missing_counts = df.isnull().sum()
        missing_percentages = (missing_counts / len(df)) * 100
        
        high_missing_columns = []
        for col in df.columns:
            if missing_percentages[col] > 20:
                high_missing_columns.append(col)
        
        return {
            "metrics": {
                "total_missing_values": int(missing_counts.sum()),
                "missing_value_percentage": round((missing_counts.sum() / df.size) * 100, 2),
                "columns_with_missing": int((missing_counts > 0).sum()),
                "missing_by_column": {col: int(count) for col, count in missing_counts.items()}
            },
            "high_missing_columns": high_missing_columns
        }
    
    def _validate_numeric_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate numeric columns."""
        warnings = []
        suggestions = []
        metrics = {}
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue
            
            # Check for infinite values
            inf_count = np.isinf(col_data).sum()
            if inf_count > 0:
                warnings.append({
                    "type": "infinite_values",
                    "message": f"Column '{col}' contains {inf_count} infinite values",
                    "column": col,
                    "infinite_count": int(inf_count)
                })
            
            # Check for negative values in price/volume columns
            if col.lower() in ['open', 'high', 'low', 'close', 'volume', 'price']:
                negative_count = (col_data < 0).sum()
                if negative_count > 0:
                    warnings.append({
                        "type": "negative_values",
                        "message": f"Column '{col}' contains {negative_count} negative values",
                        "column": col,
                        "negative_count": int(negative_count)
                    })
            
            # Detect outliers
            outlier_stats = self._detect_outliers(col_data, col)
            if outlier_stats["outlier_count"] > 0:
                outlier_pct = (outlier_stats["outlier_count"] / len(col_data)) * 100
                if outlier_pct > 5:
                    warnings.append({
                        "type": "high_outliers",
                        "message": f"Column '{col}' has {outlier_pct:.1f}% outliers",
                        "column": col,
                        "outlier_count": outlier_stats["outlier_count"],
                        "outlier_percentage": round(outlier_pct, 2)
                    })
                else:
                    suggestions.append({
                        "type": "outliers_detected",
                        "message": f"Column '{col}' has {outlier_stats['outlier_count']} potential outliers",
                        "column": col,
                        "outlier_count": outlier_stats["outlier_count"]
                    })
        
        metrics["numeric_columns_count"] = len(numeric_columns)
        return {"warnings": warnings, "suggestions": suggestions, "metrics": metrics}
    
    def _detect_outliers(self, data: pd.Series, column: str) -> Dict[str, Any]:
        """Detect outliers using IQR method."""
        try:
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = data[(data < lower_bound) | (data > upper_bound)]
            
            return {
                "outlier_count": len(outliers),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "outlier_indices": outliers.index.tolist()
            }
        except Exception:
            return {"outlier_count": 0}
    
    def _validate_timestamp_column(self, df: pd.DataFrame, dataset: Dataset) -> Dict[str, Any]:
        """Validate timestamp column."""
        warnings = []
        suggestions = []
        metrics = {}
        
        if "timestamp" not in df.columns:
            return {"warnings": warnings, "suggestions": suggestions, "metrics": metrics}
        
        # Convert to datetime if not already
        try:
            timestamps = pd.to_datetime(df["timestamp"])
        except Exception as e:
            warnings.append({
                "type": "timestamp_conversion_failed",
                "message": f"Failed to convert timestamp column: {str(e)}",
                "column": "timestamp"
            })
            return {"warnings": warnings, "suggestions": suggestions, "metrics": metrics}
        
        # Check for duplicates
        duplicate_timestamps = timestamps.duplicated().sum()
        if duplicate_timestamps > 0:
            warnings.append({
                "type": "duplicate_timestamps",
                "message": f"Found {duplicate_timestamps} duplicate timestamps",
                "duplicate_count": int(duplicate_timestamps)
            })
        
        # Check time range
        min_time = timestamps.min()
        max_time = timestamps.max()
        time_range = max_time - min_time
        
        metrics.update({
            "timestamp_range_days": time_range.days,
            "min_timestamp": min_time.isoformat(),
            "max_timestamp": max_time.isoformat(),
            "duplicate_timestamps": int(duplicate_timestamps)
        })
        
        # Check for gaps in time series
        if dataset.frequency:
            gaps = self._detect_time_gaps(timestamps, dataset.frequency)
            if gaps["gap_count"] > 0:
                gap_pct = (gaps["gap_count"] / len(timestamps)) * 100
                if gap_pct > 5:
                    warnings.append({
                        "type": "significant_time_gaps",
                        "message": f"Significant time gaps detected: {gaps['gap_count']} gaps ({gap_pct:.1f}%)",
                        "gap_count": gaps["gap_count"],
                        "gap_percentage": round(gap_pct, 2)
                    })
                else:
                    suggestions.append({
                        "type": "time_gaps",
                        "message": f"Minor time gaps detected: {gaps['gap_count']} gaps",
                        "gap_count": gaps["gap_count"]
                    })
            
            metrics.update(gaps)
        
        return {"warnings": warnings, "suggestions": suggestions, "metrics": metrics}
    
    def _detect_time_gaps(self, timestamps: pd.Series, frequency: DataFrequency) -> Dict[str, Any]:
        """Detect gaps in time series data."""
        try:
            # Map frequency to expected time delta
            freq_map = {
                DataFrequency.MINUTE_1: timedelta(minutes=1),
                DataFrequency.MINUTE_5: timedelta(minutes=5),
                DataFrequency.MINUTE_15: timedelta(minutes=15),
                DataFrequency.MINUTE_30: timedelta(minutes=30),
                DataFrequency.HOUR_1: timedelta(hours=1),
                DataFrequency.HOUR_4: timedelta(hours=4),
                DataFrequency.DAY_1: timedelta(days=1),
                DataFrequency.WEEK_1: timedelta(weeks=1),
                DataFrequency.MONTH_1: timedelta(days=30)  # Approximate
            }
            
            expected_delta = freq_map.get(frequency)
            if not expected_delta:
                return {"gap_count": 0}
            
            sorted_timestamps = timestamps.sort_values()
            time_diffs = sorted_timestamps.diff()[1:]  # Skip first NaT
            
            # Allow some tolerance (e.g., 10% of expected delta)
            tolerance = expected_delta * 0.1
            expected_min = expected_delta - tolerance
            expected_max = expected_delta + tolerance
            
            # Find gaps (time differences significantly larger than expected)
            gaps = time_diffs[time_diffs > expected_max * 2]  # 2x expected is considered a gap
            
            return {
                "gap_count": len(gaps),
                "max_gap_duration": str(gaps.max()) if len(gaps) > 0 else None,
                "avg_gap_duration": str(gaps.mean()) if len(gaps) > 0 else None
            }
            
        except Exception:
            return {"gap_count": 0}
    
    def _calculate_quality_score(self, metrics: Dict[str, Any], total_rows: int) -> float:
        """Calculate overall data quality score (0-1)."""
        try:
            score = 1.0
            
            # Penalize missing values
            missing_pct = metrics.get("missing_value_percentage", 0) / 100
            score -= missing_pct * 0.3
            
            # Penalize duplicate rows
            duplicate_pct = (metrics.get("duplicate_rows", 0) / total_rows) * 100
            score -= (duplicate_pct / 100) * 0.2
            
            # Penalize time gaps
            gap_count = metrics.get("gap_count", 0)
            if gap_count > 0:
                gap_penalty = min(gap_count / total_rows, 0.2)
                score -= gap_penalty
            
            return max(0.0, min(1.0, score))
            
        except Exception:
            return 0.5  # Default neutral score


class BusinessLogicValidationRule(ValidationRule):
    """Validate business logic and domain-specific rules."""
    
    def __init__(self):
        super().__init__(
            "business_logic_validation",
            "Validates business logic and domain rules",
            "warning"
        )
    
    def validate(self, df: pd.DataFrame, dataset: Dataset) -> Dict[str, Any]:
        """Validate business logic."""
        errors = []
        warnings = []
        suggestions = []
        metrics = {}
        
        # OHLC validation for market data
        if all(col in df.columns for col in ["open", "high", "low", "close"]):
            ohlc_issues = self._validate_ohlc_logic(df)
            warnings.extend(ohlc_issues["warnings"])
            metrics.update(ohlc_issues["metrics"])
        
        # Volume validation
        if "volume" in df.columns:
            volume_issues = self._validate_volume(df)
            warnings.extend(volume_issues["warnings"])
            suggestions.extend(volume_issues["suggestions"])
            metrics.update(volume_issues["metrics"])
        
        # Symbol validation
        if "symbol" in df.columns:
            symbol_issues = self._validate_symbols(df, dataset.asset_class)
            warnings.extend(symbol_issues["warnings"])
            metrics.update(symbol_issues["metrics"])
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "metrics": metrics
        }
    
    def _validate_ohlc_logic(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate OHLC (Open, High, Low, Close) logic."""
        warnings = []
        metrics = {}
        
        ohlc_df = df[["open", "high", "low", "close"]].dropna()
        
        # Check: High >= max(Open, Close) and Low <= min(Open, Close)
        invalid_high = (ohlc_df["high"] < ohlc_df[["open", "close"]].max(axis=1)).sum()
        invalid_low = (ohlc_df["low"] > ohlc_df[["open", "close"]].min(axis=1)).sum()
        
        # Check: High >= Low
        invalid_range = (ohlc_df["high"] < ohlc_df["low"]).sum()
        
        total_violations = invalid_high + invalid_low + invalid_range
        
        if total_violations > 0:
            violation_pct = (total_violations / len(ohlc_df)) * 100
            warnings.append({
                "type": "ohlc_logic_violations",
                "message": f"OHLC logic violations: {total_violations} rows ({violation_pct:.1f}%)",
                "invalid_high": int(invalid_high),
                "invalid_low": int(invalid_low),
                "invalid_range": int(invalid_range),
                "total_violations": int(total_violations)
            })
        
        metrics.update({
            "ohlc_violations": int(total_violations),
            "ohlc_violation_percentage": round((total_violations / len(ohlc_df)) * 100, 2) if len(ohlc_df) > 0 else 0
        })
        
        return {"warnings": warnings, "metrics": metrics}
    
    def _validate_volume(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate volume data."""
        warnings = []
        suggestions = []
        metrics = {}
        
        volume_data = df["volume"].dropna()
        
        if len(volume_data) == 0:
            return {"warnings": warnings, "suggestions": suggestions, "metrics": metrics}
        
        # Check for zero volume
        zero_volume = (volume_data == 0).sum()
        if zero_volume > 0:
            zero_pct = (zero_volume / len(volume_data)) * 100
            if zero_pct > 10:
                warnings.append({
                    "type": "high_zero_volume",
                    "message": f"High percentage of zero volume: {zero_pct:.1f}%",
                    "zero_volume_count": int(zero_volume)
                })
            else:
                suggestions.append({
                    "type": "zero_volume",
                    "message": f"Found {zero_volume} records with zero volume",
                    "zero_volume_count": int(zero_volume)
                })
        
        # Check for suspiciously low volume
        median_volume = volume_data.median()
        low_volume_threshold = median_volume * 0.01  # 1% of median
        low_volume = (volume_data < low_volume_threshold).sum()
        
        if low_volume > 0:
            suggestions.append({
                "type": "low_volume",
                "message": f"Found {low_volume} records with suspiciously low volume",
                "low_volume_count": int(low_volume),
                "threshold": float(low_volume_threshold)
            })
        
        metrics.update({
            "zero_volume_count": int(zero_volume),
            "low_volume_count": int(low_volume),
            "median_volume": float(median_volume),
            "min_volume": float(volume_data.min()),
            "max_volume": float(volume_data.max())
        })
        
        return {"warnings": warnings, "suggestions": suggestions, "metrics": metrics}
    
    def _validate_symbols(self, df: pd.DataFrame, asset_class: AssetClass) -> Dict[str, Any]:
        """Validate symbol format and consistency."""
        warnings = []
        metrics = {}
        
        symbols = df["symbol"].dropna()
        unique_symbols = symbols.unique()
        
        # Check symbol format based on asset class
        invalid_symbols = []
        
        if asset_class == AssetClass.CRYPTO:
            # Crypto symbols usually end with USDT, BUSD, etc.
            pattern = r'^[A-Z]+USDT?$|^[A-Z]+BUSD$|^[A-Z]+BTC$|^[A-Z]+ETH$'
            for symbol in unique_symbols:
                if not re.match(pattern, str(symbol)):
                    invalid_symbols.append(symbol)
        
        elif asset_class == AssetClass.STOCKS:
            # Stock symbols are usually 1-5 uppercase letters
            pattern = r'^[A-Z]{1,5}$'
            for symbol in unique_symbols:
                if not re.match(pattern, str(symbol)):
                    invalid_symbols.append(symbol)
        
        if invalid_symbols:
            warnings.append({
                "type": "invalid_symbol_format",
                "message": f"Symbols with invalid format: {invalid_symbols}",
                "invalid_symbols": invalid_symbols,
                "asset_class": asset_class.value
            })
        
        metrics.update({
            "unique_symbols": len(unique_symbols),
            "invalid_symbols_count": len(invalid_symbols),
            "symbol_list": unique_symbols.tolist()
        })
        
        return {"warnings": warnings, "metrics": metrics}


class DatasetValidator:
    """Main dataset validation service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize validation rules
        self.rules = [
            SchemaValidationRule(),
            DataQualityValidationRule(),
            BusinessLogicValidationRule()
        ]
    
    async def validate_dataset(self, dataset_id: str, user_id: str, 
                             db: AsyncSession) -> Dict[str, Any]:
        """Validate a dataset and create validation report."""
        try:
            # Get dataset
            result = await db.execute(
                select(Dataset).where(
                    Dataset.id == UUID(dataset_id),
                    Dataset.user_id == UUID(user_id)
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {"success": False, "error": "Dataset not found"}
            
            # Load dataset
            df = await self._load_dataset(dataset)
            if df is None:
                return {"success": False, "error": "Failed to load dataset"}
            
            # Run validation rules
            validation_start = datetime.utcnow()
            all_errors = []
            all_warnings = []
            all_suggestions = []
            all_metrics = {}
            
            for rule in self.rules:
                self.logger.info(f"Running validation rule: {rule.name}")
                
                try:
                    rule_result = rule.validate(df, dataset)
                    
                    # Collect results
                    all_errors.extend(rule_result.get("errors", []))
                    all_warnings.extend(rule_result.get("warnings", []))
                    all_suggestions.extend(rule_result.get("suggestions", []))
                    
                    # Merge metrics
                    rule_metrics = rule_result.get("metrics", {})
                    all_metrics.update(rule_metrics)
                    
                except Exception as e:
                    self.logger.error(f"Validation rule {rule.name} failed: {str(e)}")
                    all_errors.append({
                        "type": "validation_rule_error",
                        "message": f"Validation rule '{rule.name}' failed: {str(e)}",
                        "rule": rule.name
                    })
            
            validation_duration = (datetime.utcnow() - validation_start).total_seconds()
            
            # Determine validation status
            is_valid = len(all_errors) == 0
            
            # Create validation report
            report = DatasetValidationReport(
                dataset_id=UUID(dataset_id),
                is_valid=is_valid,
                validation_type="comprehensive",
                errors=all_errors,
                warnings=all_warnings,
                suggestions=all_suggestions,
                metrics=all_metrics,
                validation_duration=validation_duration,
                validator_version="1.0.0"
            )
            
            db.add(report)
            
            # Update dataset status
            if is_valid:
                dataset.status = DatasetStatus.VALIDATED
                dataset.is_validated = True
                dataset.validation_errors = []
                dataset.validation_warnings = [w.get("message", str(w)) for w in all_warnings]
                
                # Update quality metrics
                dataset.completeness_score = all_metrics.get("missing_value_percentage", 0)
                dataset.quality_score = all_metrics.get("quality_score", 0.5)
            else:
                dataset.status = DatasetStatus.FAILED
                dataset.is_validated = False
                dataset.validation_errors = [e.get("message", str(e)) for e in all_errors]
                dataset.validation_warnings = [w.get("message", str(w)) for w in all_warnings]
            
            await db.commit()
            
            self.logger.info(f"Validation completed for dataset {dataset_id}: {'VALID' if is_valid else 'INVALID'}")
            
            return {
                "success": True,
                "is_valid": is_valid,
                "report_id": str(report.id),
                "errors": all_errors,
                "warnings": all_warnings,
                "suggestions": all_suggestions,
                "metrics": all_metrics,
                "validation_duration": validation_duration
            }
            
        except Exception as e:
            self.logger.error(f"Dataset validation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _load_dataset(self, dataset: Dataset) -> Optional[pd.DataFrame]:
        """Load dataset from storage."""
        try:
            if not dataset.file_path or not dataset.file_path.exists():
                self.logger.error(f"Dataset file not found: {dataset.file_path}")
                return None
            
            # Load based on format
            if dataset.data_format == "parquet":
                df = pd.read_parquet(dataset.file_path)
            elif dataset.data_format == "csv":
                df = pd.read_csv(dataset.file_path)
            elif dataset.data_format == "json":
                df = pd.read_json(dataset.file_path)
            else:
                self.logger.error(f"Unsupported data format: {dataset.data_format}")
                return None
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load dataset: {str(e)}")
            return None
    
    async def get_validation_report(self, dataset_id: str, user_id: str, 
                                  db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get the latest validation report for a dataset."""
        try:
            # Get latest validation report
            result = await db.execute(
                select(DatasetValidationReport)
                .join(Dataset)
                .where(
                    Dataset.id == UUID(dataset_id),
                    Dataset.user_id == UUID(user_id)
                )
                .order_by(DatasetValidationReport.created_at.desc())
                .limit(1)
            )
            
            report = result.scalar_one_or_none()
            
            if not report:
                return None
            
            return {
                "id": str(report.id),
                "dataset_id": str(report.dataset_id),
                "is_valid": report.is_valid,
                "validation_type": report.validation_type,
                "errors": report.errors,
                "warnings": report.warnings,
                "suggestions": report.suggestions,
                "metrics": report.metrics,
                "validation_duration": report.validation_duration,
                "validator_version": report.validator_version,
                "created_at": report.created_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get validation report: {str(e)}")
            return None
    
    async def validate_uploaded_file(self, file_path: str, 
                                   asset_class: AssetClass) -> Dict[str, Any]:
        """Quick validation of uploaded file before creating dataset."""
        try:
            # Try to load the file
            if file_path.endswith('.parquet'):
                df = pd.read_parquet(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                df = pd.read_json(file_path)
            else:
                return {
                    "valid": False,
                    "error": "Unsupported file format"
                }
            
            # Basic validation
            if df.empty:
                return {
                    "valid": False,
                    "error": "File is empty"
                }
            
            # Check for minimum required columns
            schema_rule = SchemaValidationRule()
            mock_dataset = type('Dataset', (), {
                'asset_class': asset_class
            })()
            
            schema_result = schema_rule.validate(df, mock_dataset)
            
            has_errors = len(schema_result.get("errors", [])) > 0
            
            return {
                "valid": not has_errors,
                "errors": schema_result.get("errors", []),
                "warnings": schema_result.get("warnings", []),
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns.tolist(),
                "file_size": os.path.getsize(file_path)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to validate file: {str(e)}"
            }