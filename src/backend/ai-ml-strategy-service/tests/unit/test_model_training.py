"""Unit tests for model training and validation components."""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from app.services.hyperparameter_tuning import HyperparameterTuner
from app.services.model_validator import ModelValidator

class TestModelTraining:
    """Test suite for model training and validation."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.tuner = HyperparameterTuner()
        self.validator = ModelValidator()
        
        # Generate sample data
        np.random.seed(42)
        self.X = np.random.randn(1000, 10)  # 1000 samples, 10 features
        self.y = (np.random.rand(1000) > 0.5).astype(int)  # Binary classification
        
        # Sample hyperparameter grid
        self.param_grid = {
            'n_estimators': [50, 100],
            'max_depth': [3, 5, None],
            'min_samples_split': [2, 5]
        }
    
    @patch('app.services.hyperparameter_tuning.RandomizedSearchCV')
    def test_hyperparameter_tuning(self, mock_search):
        """Test hyperparameter tuning process."""
        # Configure mock
        mock_result = MagicMock()
        mock_result.best_params_ = {'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2}
        mock_result.best_score_ = 0.95
        mock_search.return_value = mock_result
        
        # Run tuning
        best_params, best_score = self.tuner.tune_hyperparameters(
            model_type='random_forest',
            X=self.X,
            y=self.y,
            param_distributions=self.param_grid,
            cv=3,
            n_iter=5
        )
        
        # Verify results
        assert isinstance(best_params, dict)
        assert 'n_estimators' in best_params
        assert 'max_depth' in best_params
        assert 'min_samples_split' in best_params
        assert 0 <= best_score <= 1
    
    def test_model_validation(self):
        """Test model validation metrics."""
        # Create mock model
        class MockModel:
            def predict_proba(self, X):
                return np.column_stack([1 - np.mean(X, axis=1), np.mean(X, axis=1)])
        
        model = MockModel()
        
        # Generate test data with some structure
        X_test = np.random.randn(100, 10)
        y_test = (np.mean(X_test, axis=1) > 0).astype(int)
        
        # Validate model
        metrics = self.validator.validate_model(
            model=model,
            X_test=X_test,
            y_test=y_test,
            metrics=['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
        )
        
        # Check metrics
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        assert 'roc_auc' in metrics
        
        # All metrics should be between 0 and 1
        for metric_name, value in metrics.items():
            assert 0 <= value <= 1, f"{metric_name} out of range: {value}"
    
    @patch('mlflow.start_run')
    @patch('mlflow.log_params')
    @patch('mlflow.log_metrics')
    @patch('mlflow.sklearn.log_model')
    def test_mlflow_integration(self, mock_log_model, mock_log_metrics, 
                              mock_log_params, mock_start_run):
        """Test MLflow experiment tracking integration."""
        # Mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.ones(100)
        
        # Mock metrics
        metrics = {
            'accuracy': 0.95,
            'precision': 0.94,
            'recall': 0.93,
            'f1': 0.935
        }
        
        # Log experiment
        experiment_id = self.tuner.log_experiment(
            model=mock_model,
            params={'param1': 'value1'},
            metrics=metrics,
            model_name='test_model',
            run_name='test_run',
            experiment_name='test_experiment'
        )
        
        # Verify MLflow was called correctly
        mock_start_run.assert_called_once()
        mock_log_params.assert_called_once()
        mock_log_metrics.assert_called_once()
        mock_log_model.assert_called_once()
        
        # Verify experiment ID is returned
        assert isinstance(experiment_id, str)
