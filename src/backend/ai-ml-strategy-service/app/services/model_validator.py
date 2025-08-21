"""
Model validation and testing framework for Phase 4: Model Training Orchestrator.
Provides comprehensive model validation, testing, and quality assessment.
"""

import logging
import asyncio
import json
import pickle
import tempfile
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import UUID, uuid4
import numpy as np
import pandas as pd
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.training import (
    TrainingJob, ModelArtifact, ModelFramework, JobStatus
)
from app.models.dataset import Dataset
from app.core.config import get_settings


class ModelValidator:
    """Comprehensive model validation and testing framework."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # Validation thresholds
        self.quality_thresholds = {
            "min_accuracy": 0.6,
            "max_overfitting_ratio": 2.0,  # validation_loss / training_loss
            "min_samples_per_class": 10,
            "max_prediction_time_ms": 1000,
            "min_feature_importance_coverage": 0.8
        }
    
    async def validate_model(self, model_artifact: ModelArtifact, 
                           validation_config: Dict[str, Any],
                           db: AsyncSession) -> Dict[str, Any]:
        """Comprehensive model validation."""
        try:
            validation_report = {
                "model_id": str(model_artifact.id),
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_score": 0.0,
                "passed": False,
                "validation_results": {},
                "recommendations": [],
                "warnings": [],
                "errors": []
            }
            
            # Load model and prepare data
            model_info = await self._load_model_info(model_artifact)
            if not model_info["success"]:
                validation_report["errors"].append(model_info["error"])
                return validation_report
            
            # Get validation dataset
            validation_data = await self._prepare_validation_data(
                model_artifact, validation_config, db
            )
            
            if not validation_data["success"]:
                validation_report["errors"].append(validation_data["error"])
                return validation_report
            
            # Run validation tests
            validation_tests = [
                self._validate_model_structure,
                self._validate_performance_metrics,
                self._validate_prediction_consistency,
                self._validate_feature_importance,
                self._validate_prediction_speed,
                self._validate_memory_usage,
                self._validate_data_drift_robustness,
                self._validate_edge_cases
            ]
            
            total_score = 0.0
            max_score = len(validation_tests)
            
            for test_func in validation_tests:
                try:
                    test_result = await test_func(
                        model_info["model"], 
                        validation_data["data"], 
                        validation_config
                    )
                    
                    test_name = test_func.__name__.replace("_validate_", "")
                    validation_report["validation_results"][test_name] = test_result
                    
                    if test_result["passed"]:
                        total_score += test_result.get("score", 1.0)
                    
                    if test_result.get("warnings"):
                        validation_report["warnings"].extend(test_result["warnings"])
                    
                    if test_result.get("recommendations"):
                        validation_report["recommendations"].extend(test_result["recommendations"])
                        
                except Exception as e:
                    self.logger.error(f"Validation test {test_func.__name__} failed: {str(e)}")
                    validation_report["errors"].append(f"Test {test_func.__name__} failed: {str(e)}")
            
            # Calculate overall score
            validation_report["overall_score"] = (total_score / max_score) * 100
            validation_report["passed"] = validation_report["overall_score"] >= 70  # 70% threshold
            
            # Generate summary recommendations
            validation_report["summary"] = self._generate_validation_summary(validation_report)
            
            self.logger.info(f"Model validation completed for {model_artifact.id}: "
                           f"Score {validation_report['overall_score']:.1f}%, "
                           f"Passed: {validation_report['passed']}")
            
            return validation_report
            
        except Exception as e:
            self.logger.error(f"Model validation failed: {str(e)}")
            return {
                "model_id": str(model_artifact.id),
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_score": 0.0,
                "passed": False,
                "errors": [str(e)]
            }
    
    async def _load_model_info(self, model_artifact: ModelArtifact) -> Dict[str, Any]:
        """Load model and extract metadata."""
        try:
            # In a real implementation, this would load the actual model
            # For now, we'll simulate model loading and return metadata
            
            model_metadata = {
                "framework": model_artifact.framework.value,
                "model_type": model_artifact.model_type,
                "input_shape": model_artifact.input_shape,
                "output_shape": model_artifact.output_shape,
                "feature_names": model_artifact.feature_names,
                "target_names": model_artifact.target_names,
                "file_size": model_artifact.file_size,
                "training_accuracy": model_artifact.training_accuracy,
                "validation_accuracy": model_artifact.validation_accuracy
            }
            
            # Simulate model object
            mock_model = {
                "metadata": model_metadata,
                "framework": model_artifact.framework,
                "predict": self._mock_predict,
                "predict_proba": self._mock_predict_proba if model_artifact.model_type == "classification" else None
            }
            
            return {
                "success": True,
                "model": mock_model,
                "metadata": model_metadata
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _prepare_validation_data(self, model_artifact: ModelArtifact,
                                     validation_config: Dict[str, Any],
                                     db: AsyncSession) -> Dict[str, Any]:
        """Prepare validation dataset."""
        try:
            # Get the training job to find the dataset
            result = await db.execute(
                select(TrainingJob)
                .options(selectinload(TrainingJob.dataset))
                .where(TrainingJob.id == model_artifact.training_job_id)
            )
            training_job = result.scalar_one_or_none()
            
            if not training_job or not training_job.dataset:
                return {"success": False, "error": "Training dataset not found"}
            
            # Generate mock validation data based on dataset info
            dataset = training_job.dataset
            
            # Create synthetic validation data based on dataset characteristics
            n_samples = validation_config.get("validation_samples", 1000)
            n_features = len(dataset.columns) - 1  # Assume last column is target
            
            # Generate mock features
            X_val = np.random.randn(n_samples, n_features)
            
            # Generate mock targets based on model type
            if model_artifact.model_type == "classification":
                n_classes = validation_config.get("n_classes", 2)
                y_val = np.random.randint(0, n_classes, n_samples)
            else:
                y_val = np.random.randn(n_samples)
            
            validation_data = {
                "X": X_val,
                "y": y_val,
                "feature_names": model_artifact.feature_names,
                "target_names": model_artifact.target_names,
                "dataset_info": {
                    "name": dataset.name,
                    "size": n_samples,
                    "features": n_features
                }
            }
            
            return {
                "success": True,
                "data": validation_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _validate_model_structure(self, model: Dict[str, Any], 
                                      validation_data: Dict[str, Any],
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model structure and architecture."""
        result = {
            "passed": True,
            "score": 1.0,
            "details": {},
            "warnings": [],
            "recommendations": []
        }
        
        try:
            metadata = model["metadata"]
            
            # Check input/output shapes
            expected_features = validation_data["X"].shape[1]
            model_input_features = metadata.get("input_shape", [expected_features])
            
            if isinstance(model_input_features, list) and len(model_input_features) > 0:
                if model_input_features[-1] != expected_features:
                    result["passed"] = False
                    result["score"] = 0.0
                    result["warnings"].append(
                        f"Input shape mismatch: expected {expected_features}, got {model_input_features[-1]}"
                    )
            
            # Check feature names consistency
            if metadata.get("feature_names"):
                if len(metadata["feature_names"]) != expected_features:
                    result["warnings"].append("Feature names count doesn't match input dimensions")
            
            # Check model size
            model_size_mb = metadata.get("file_size", 0) / (1024 * 1024)
            if model_size_mb > 500:  # 500MB threshold
                result["warnings"].append(f"Large model size: {model_size_mb:.1f}MB")
                result["recommendations"].append("Consider model compression or pruning")
            
            result["details"] = {
                "input_features": expected_features,
                "model_input_shape": model_input_features,
                "model_size_mb": round(model_size_mb, 2),
                "framework": metadata.get("framework")
            }
            
        except Exception as e:
            result["passed"] = False
            result["score"] = 0.0
            result["warnings"].append(f"Structure validation failed: {str(e)}")
        
        return result
    
    async def _validate_performance_metrics(self, model: Dict[str, Any],
                                          validation_data: Dict[str, Any],
                                          config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model performance metrics."""
        result = {
            "passed": True,
            "score": 1.0,
            "details": {},
            "warnings": [],
            "recommendations": []
        }
        
        try:
            metadata = model["metadata"]
            
            # Get training metrics
            train_acc = metadata.get("training_accuracy", 0)
            val_acc = metadata.get("validation_accuracy", 0)
            
            # Calculate current performance on validation data
            X_val = validation_data["X"]
            y_true = validation_data["y"]
            y_pred = await model["predict"](X_val)
            
            # Calculate accuracy
            if model["metadata"].get("model_type") == "classification":
                current_acc = np.mean(y_pred == y_true)
            else:
                # For regression, use R² score approximation
                ss_res = np.sum((y_true - y_pred) ** 2)
                ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
                current_acc = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # Check minimum accuracy threshold
            min_accuracy = config.get("min_accuracy", self.quality_thresholds["min_accuracy"])
            if current_acc < min_accuracy:
                result["passed"] = False
                result["score"] = current_acc / min_accuracy
                result["warnings"].append(f"Low accuracy: {current_acc:.3f} < {min_accuracy}")
            
            # Check for overfitting
            if train_acc and val_acc:
                overfitting_ratio = train_acc / val_acc if val_acc > 0 else float('inf')
                max_overfitting = self.quality_thresholds["max_overfitting_ratio"]
                
                if overfitting_ratio > max_overfitting:
                    result["warnings"].append(f"Potential overfitting detected: {overfitting_ratio:.2f}")
                    result["recommendations"].append("Consider regularization or more training data")
            
            result["details"] = {
                "current_accuracy": round(current_acc, 4),
                "training_accuracy": train_acc,
                "validation_accuracy": val_acc,
                "overfitting_ratio": round(train_acc / val_acc, 3) if val_acc > 0 else None
            }
            
        except Exception as e:
            result["passed"] = False
            result["score"] = 0.0
            result["warnings"].append(f"Performance validation failed: {str(e)}")
        
        return result
    
    async def _validate_prediction_consistency(self, model: Dict[str, Any],
                                             validation_data: Dict[str, Any],
                                             config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate prediction consistency and stability."""
        result = {
            "passed": True,
            "score": 1.0,
            "details": {},
            "warnings": [],
            "recommendations": []
        }
        
        try:
            X_val = validation_data["X"][:100]  # Use subset for consistency check
            
            # Test prediction consistency (same input should give same output)
            pred1 = await model["predict"](X_val)
            pred2 = await model["predict"](X_val)
            
            consistency_score = np.mean(pred1 == pred2) if len(pred1) > 0 else 0
            
            if consistency_score < 0.99:  # 99% consistency threshold
                result["passed"] = False
                result["score"] = consistency_score
                result["warnings"].append(f"Inconsistent predictions: {consistency_score:.3f}")
            
            # Test prediction stability with small perturbations
            noise_scale = 0.01
            X_noisy = X_val + np.random.normal(0, noise_scale, X_val.shape)
            pred_noisy = await model["predict"](X_noisy)
            
            if model["metadata"].get("model_type") == "classification":
                stability_score = np.mean(pred1 == pred_noisy)
            else:
                # For regression, check if predictions are within reasonable range
                pred_diff = np.abs(pred1 - pred_noisy)
                stability_score = np.mean(pred_diff < np.std(pred1) * 0.1)
            
            if stability_score < 0.8:  # 80% stability threshold
                result["warnings"].append(f"Low prediction stability: {stability_score:.3f}")
                result["recommendations"].append("Model may be sensitive to input noise")
            
            result["details"] = {
                "consistency_score": round(consistency_score, 4),
                "stability_score": round(stability_score, 4),
                "samples_tested": len(X_val)
            }
            
        except Exception as e:
            result["passed"] = False
            result["score"] = 0.0
            result["warnings"].append(f"Consistency validation failed: {str(e)}")
        
        return result
    
    async def _validate_feature_importance(self, model: Dict[str, Any],
                                         validation_data: Dict[str, Any],
                                         config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate feature importance and interpretability."""
        result = {
            "passed": True,
            "score": 1.0,
            "details": {},
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Simulate feature importance calculation
            n_features = validation_data["X"].shape[1]
            feature_names = validation_data.get("feature_names", [f"feature_{i}" for i in range(n_features)])
            
            # Generate mock feature importance (would use actual model feature importance)
            importance_scores = np.random.exponential(1, n_features)
            importance_scores = importance_scores / np.sum(importance_scores)
            
            # Sort features by importance
            importance_ranking = sorted(
                zip(feature_names, importance_scores),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Check if top features cover sufficient importance
            top_features_coverage = sum(score for _, score in importance_ranking[:10])
            min_coverage = self.quality_thresholds["min_feature_importance_coverage"]
            
            if top_features_coverage < min_coverage:
                result["warnings"].append(
                    f"Low feature importance coverage: {top_features_coverage:.3f} < {min_coverage}"
                )
                result["recommendations"].append("Consider feature selection or engineering")
            
            # Check for feature dominance (one feature too important)
            max_single_importance = max(importance_scores)
            if max_single_importance > 0.5:
                result["warnings"].append(f"Feature dominance detected: {max_single_importance:.3f}")
                result["recommendations"].append("Check for data leakage or consider feature regularization")
            
            result["details"] = {
                "top_10_features": importance_ranking[:10],
                "feature_importance_coverage": round(top_features_coverage, 4),
                "max_single_importance": round(max_single_importance, 4),
                "total_features": n_features
            }
            
        except Exception as e:
            result["passed"] = False
            result["score"] = 0.0
            result["warnings"].append(f"Feature importance validation failed: {str(e)}")
        
        return result
    
    async def _validate_prediction_speed(self, model: Dict[str, Any],
                                       validation_data: Dict[str, Any],
                                       config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model prediction speed and latency."""
        result = {
            "passed": True,
            "score": 1.0,
            "details": {},
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Test prediction speed with different batch sizes
            test_samples = [1, 10, 100, 1000]
            speed_results = []
            
            for batch_size in test_samples:
                if batch_size <= len(validation_data["X"]):
                    X_batch = validation_data["X"][:batch_size]
                    
                    # Measure prediction time
                    start_time = datetime.utcnow()
                    await model["predict"](X_batch)
                    end_time = datetime.utcnow()
                    
                    duration_ms = (end_time - start_time).total_seconds() * 1000
                    time_per_sample = duration_ms / batch_size
                    
                    speed_results.append({
                        "batch_size": batch_size,
                        "total_time_ms": round(duration_ms, 2),
                        "time_per_sample_ms": round(time_per_sample, 2)
                    })
            
            # Check if single prediction time is within threshold
            single_prediction_time = speed_results[0]["time_per_sample_ms"] if speed_results else float('inf')
            max_prediction_time = config.get("max_prediction_time_ms", 
                                            self.quality_thresholds["max_prediction_time_ms"])
            
            if single_prediction_time > max_prediction_time:
                result["passed"] = False
                result["score"] = max_prediction_time / single_prediction_time
                result["warnings"].append(f"Slow prediction: {single_prediction_time:.2f}ms > {max_prediction_time}ms")
                result["recommendations"].append("Consider model optimization or quantization")
            
            # Calculate throughput
            if len(speed_results) > 1:
                batch_100_time = next((r for r in speed_results if r["batch_size"] == 100), None)
                if batch_100_time:
                    throughput = 100 / (batch_100_time["total_time_ms"] / 1000)  # samples per second
                    result["details"]["throughput_samples_per_sec"] = round(throughput, 2)
            
            result["details"]["speed_benchmark"] = speed_results
            
        except Exception as e:
            result["passed"] = False
            result["score"] = 0.0
            result["warnings"].append(f"Speed validation failed: {str(e)}")
        
        return result
    
    async def _validate_memory_usage(self, model: Dict[str, Any],
                                   validation_data: Dict[str, Any],
                                   config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model memory usage and efficiency."""
        result = {
            "passed": True,
            "score": 1.0,
            "details": {},
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Simulate memory usage calculation
            model_size_mb = model["metadata"].get("file_size", 0) / (1024 * 1024)
            
            # Estimate runtime memory usage (simplified)
            n_features = validation_data["X"].shape[1]
            estimated_runtime_mb = model_size_mb * 1.5 + (n_features * 0.001)  # Rough estimate
            
            # Check memory thresholds
            max_model_size = config.get("max_model_size_mb", 1000)  # 1GB default
            max_runtime_memory = config.get("max_runtime_memory_mb", 2000)  # 2GB default
            
            if model_size_mb > max_model_size:
                result["warnings"].append(f"Large model size: {model_size_mb:.1f}MB")
                result["recommendations"].append("Consider model compression")
            
            if estimated_runtime_mb > max_runtime_memory:
                result["warnings"].append(f"High runtime memory: {estimated_runtime_mb:.1f}MB")
                result["recommendations"].append("Consider model optimization")
            
            # Memory efficiency score
            memory_efficiency = 1.0 / (1.0 + estimated_runtime_mb / 1000)  # Normalize
            
            result["details"] = {
                "model_size_mb": round(model_size_mb, 2),
                "estimated_runtime_mb": round(estimated_runtime_mb, 2),
                "memory_efficiency_score": round(memory_efficiency, 4)
            }
            
        except Exception as e:
            result["passed"] = False
            result["score"] = 0.0
            result["warnings"].append(f"Memory validation failed: {str(e)}")
        
        return result
    
    async def _validate_data_drift_robustness(self, model: Dict[str, Any],
                                            validation_data: Dict[str, Any],
                                            config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model robustness to data drift."""
        result = {
            "passed": True,
            "score": 1.0,
            "details": {},
            "warnings": [],
            "recommendations": []
        }
        
        try:
            X_val = validation_data["X"][:500]  # Use subset for drift testing
            
            # Test with different types of data drift
            drift_tests = []
            
            # 1. Feature scaling drift
            X_scaled = X_val * np.random.uniform(0.8, 1.2, X_val.shape[1])
            pred_original = await model["predict"](X_val)
            pred_scaled = await model["predict"](X_scaled)
            
            if model["metadata"].get("model_type") == "classification":
                scaling_robustness = np.mean(pred_original == pred_scaled)
            else:
                correlation = np.corrcoef(pred_original, pred_scaled)[0, 1]
                scaling_robustness = max(0, correlation)
            
            drift_tests.append({
                "test": "feature_scaling",
                "robustness_score": round(scaling_robustness, 4)
            })
            
            # 2. Feature shift drift
            X_shifted = X_val + np.random.normal(0, 0.1, X_val.shape)
            pred_shifted = await model["predict"](X_shifted)
            
            if model["metadata"].get("model_type") == "classification":
                shift_robustness = np.mean(pred_original == pred_shifted)
            else:
                correlation = np.corrcoef(pred_original, pred_shifted)[0, 1]
                shift_robustness = max(0, correlation)
            
            drift_tests.append({
                "test": "feature_shift",
                "robustness_score": round(shift_robustness, 4)
            })
            
            # Calculate overall robustness
            avg_robustness = np.mean([test["robustness_score"] for test in drift_tests])
            
            if avg_robustness < 0.8:  # 80% threshold
                result["warnings"].append(f"Low drift robustness: {avg_robustness:.3f}")
                result["recommendations"].append("Consider robust training techniques or feature normalization")
            
            result["details"] = {
                "drift_tests": drift_tests,
                "average_robustness": round(avg_robustness, 4)
            }
            
        except Exception as e:
            result["passed"] = False
            result["score"] = 0.0
            result["warnings"].append(f"Drift robustness validation failed: {str(e)}")
        
        return result
    
    async def _validate_edge_cases(self, model: Dict[str, Any],
                                 validation_data: Dict[str, Any],
                                 config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model behavior on edge cases."""
        result = {
            "passed": True,
            "score": 1.0,
            "details": {},
            "warnings": [],
            "recommendations": []
        }
        
        try:
            X_val = validation_data["X"]
            edge_case_tests = []
            
            # Test with extreme values
            X_extreme = np.copy(X_val[:10])
            X_extreme[0] = np.full(X_extreme.shape[1], 1e6)   # Very large values
            X_extreme[1] = np.full(X_extreme.shape[1], -1e6)  # Very small values
            X_extreme[2] = np.zeros(X_extreme.shape[1])       # All zeros
            
            try:
                pred_extreme = await model["predict"](X_extreme)
                extreme_test_passed = True
                extreme_error = None
            except Exception as e:
                extreme_test_passed = False
                extreme_error = str(e)
            
            edge_case_tests.append({
                "test": "extreme_values",
                "passed": extreme_test_passed,
                "error": extreme_error
            })
            
            # Test with missing-like values (NaN simulation with large negative values)
            X_missing = np.copy(X_val[:10])
            X_missing[3] = np.full(X_missing.shape[1], -999999)  # Simulate missing values
            
            try:
                pred_missing = await model["predict"](X_missing)
                missing_test_passed = True
                missing_error = None
            except Exception as e:
                missing_test_passed = False
                missing_error = str(e)
            
            edge_case_tests.append({
                "test": "missing_like_values",
                "passed": missing_test_passed,
                "error": missing_error
            })
            
            # Calculate edge case robustness
            passed_tests = sum(1 for test in edge_case_tests if test["passed"])
            edge_case_score = passed_tests / len(edge_case_tests)
            
            if edge_case_score < 1.0:
                result["warnings"].append("Model failed some edge case tests")
                result["recommendations"].append("Add input validation and error handling")
            
            result["details"] = {
                "edge_case_tests": edge_case_tests,
                "edge_case_score": round(edge_case_score, 4)
            }
            
        except Exception as e:
            result["passed"] = False
            result["score"] = 0.0
            result["warnings"].append(f"Edge case validation failed: {str(e)}")
        
        return result
    
    def _generate_validation_summary(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation summary and recommendations."""
        summary = {
            "overall_assessment": "",
            "key_strengths": [],
            "critical_issues": [],
            "improvement_recommendations": [],
            "deployment_readiness": ""
        }
        
        score = validation_report["overall_score"]
        
        # Overall assessment
        if score >= 90:
            summary["overall_assessment"] = "Excellent model quality"
            summary["deployment_readiness"] = "Ready for production deployment"
        elif score >= 80:
            summary["overall_assessment"] = "Good model quality with minor issues"
            summary["deployment_readiness"] = "Ready for deployment with monitoring"
        elif score >= 70:
            summary["overall_assessment"] = "Acceptable model quality"
            summary["deployment_readiness"] = "Consider improvements before production"
        else:
            summary["overall_assessment"] = "Model quality needs improvement"
            summary["deployment_readiness"] = "Not recommended for production"
        
        # Analyze validation results for strengths and issues
        for test_name, test_result in validation_report["validation_results"].items():
            if test_result.get("passed", False) and test_result.get("score", 0) > 0.9:
                summary["key_strengths"].append(f"Strong {test_name.replace('_', ' ')}")
            elif not test_result.get("passed", True):
                summary["critical_issues"].append(f"Failed {test_name.replace('_', ' ')}")
        
        # Collect unique recommendations
        all_recommendations = validation_report.get("recommendations", [])
        summary["improvement_recommendations"] = list(set(all_recommendations))[:5]  # Top 5 unique
        
        return summary
    
    async def _mock_predict(self, X: np.ndarray) -> np.ndarray:
        """Mock prediction function for testing."""
        # Simulate prediction delay
        await asyncio.sleep(0.001)  # 1ms delay
        
        # Generate mock predictions
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        # Simple linear combination for consistent predictions
        predictions = np.sum(X * 0.1, axis=1) + np.random.normal(0, 0.01, X.shape[0])
        
        return predictions
    
    async def _mock_predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Mock prediction probability function for classification."""
        await asyncio.sleep(0.001)
        
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        # Generate mock probabilities
        n_classes = 2
        raw_scores = np.random.randn(X.shape[0], n_classes)
        
        # Softmax to get probabilities
        exp_scores = np.exp(raw_scores - np.max(raw_scores, axis=1, keepdims=True))
        probabilities = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
        
        return probabilities