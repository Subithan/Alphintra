"""
ML Model Training Framework
Alphintra Trading Platform - Phase 4
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
import asyncio
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import joblib
from pathlib import Path
import json
from datetime import datetime, timedelta
import warnings

# ML Libraries
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.svm import SVR, SVC
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, precision_score, recall_score, f1_score
from sklearn.base import BaseEstimator, RegressorMixin, ClassifierMixin

# Deep Learning
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    warnings.warn("PyTorch not available. Deep learning models will be disabled.")

# XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    warnings.warn("XGBoost not available. XGBoost models will be disabled.")

# LightGBM
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    warnings.warn("LightGBM not available. LightGBM models will be disabled.")

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Enumeration of supported model types"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting" 
    LINEAR_REGRESSION = "linear_regression"
    RIDGE_REGRESSION = "ridge_regression"
    LASSO_REGRESSION = "lasso_regression"
    LOGISTIC_REGRESSION = "logistic_regression"
    SVM = "svm"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    LSTM = "lstm"
    TRANSFORMER = "transformer"


class TaskType(Enum):
    """Enumeration of ML task types"""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    TIME_SERIES = "time_series"


@dataclass
class ModelConfig:
    """Configuration for ML model training"""
    model_type: ModelType
    task_type: TaskType
    target_column: str
    feature_columns: List[str]
    hyperparameters: Dict[str, Any]
    validation_split: float = 0.2
    test_split: float = 0.1
    random_state: int = 42
    cross_validation_folds: int = 5
    early_stopping: bool = True
    early_stopping_rounds: int = 50
    scaling_method: str = "standard"  # standard, minmax, robust
    feature_selection: bool = True
    feature_selection_k: int = 50


@dataclass
class TrainingResults:
    """Results from model training"""
    model_id: str
    model_type: ModelType
    task_type: TaskType
    training_score: float
    validation_score: float
    test_score: float
    feature_importance: Dict[str, float]
    hyperparameters: Dict[str, Any]
    training_time: float
    model_path: str
    scaler_path: Optional[str]
    metrics: Dict[str, float]
    cross_validation_scores: List[float]


class ModelTrainer:
    """
    Comprehensive ML model training framework for trading strategies
    Supports multiple algorithms, hyperparameter optimization, and validation
    """
    
    def __init__(self, models_dir: str = "models", experiments_dir: str = "experiments"):
        self.models_dir = Path(models_dir)
        self.experiments_dir = Path(experiments_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.experiments_dir.mkdir(exist_ok=True)
        
        self.scalers = {
            "standard": StandardScaler(),
            "minmax": MinMaxScaler(),
            "robust": RobustScaler()
        }
        
        self.trained_models = {}
        self.training_history = []
        
    async def train_model(self, 
                         data: pd.DataFrame,
                         config: ModelConfig,
                         optimize_hyperparameters: bool = True) -> TrainingResults:
        """
        Train a machine learning model with the given configuration
        
        Args:
            data: DataFrame with features and target
            config: Model configuration
            optimize_hyperparameters: Whether to perform hyperparameter optimization
            
        Returns:
            Training results with model performance metrics
        """
        try:
            start_time = datetime.now()
            model_id = f"{config.model_type.value}_{int(start_time.timestamp())}"
            
            logger.info(f"Starting training for model {model_id}")
            
            # Prepare data
            X, y = self._prepare_data(data, config)
            
            # Split data
            X_train, X_val, X_test, y_train, y_val, y_test = self._split_data(X, y, config)
            
            # Scale features
            scaler = self._fit_scaler(X_train, config.scaling_method)
            X_train_scaled = scaler.transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            X_test_scaled = scaler.transform(X_test)
            
            # Feature selection
            if config.feature_selection:
                feature_selector = self._fit_feature_selector(X_train_scaled, y_train, config)
                X_train_scaled = feature_selector.transform(X_train_scaled)
                X_val_scaled = feature_selector.transform(X_val_scaled)
                X_test_scaled = feature_selector.transform(X_test_scaled)
            
            # Initialize model
            model = self._initialize_model(config)
            
            # Hyperparameter optimization
            if optimize_hyperparameters:
                model = await self._optimize_hyperparameters(
                    model, X_train_scaled, y_train, config
                )
            
            # Train model
            if config.model_type in [ModelType.LSTM, ModelType.TRANSFORMER]:
                model = await self._train_deep_learning_model(
                    model, X_train_scaled, y_train, X_val_scaled, y_val, config
                )
            else:
                model = self._train_sklearn_model(
                    model, X_train_scaled, y_train, config
                )
            
            # Evaluate model
            train_score = self._evaluate_model(model, X_train_scaled, y_train, config.task_type)
            val_score = self._evaluate_model(model, X_val_scaled, y_val, config.task_type)
            test_score = self._evaluate_model(model, X_test_scaled, y_test, config.task_type)
            
            # Cross-validation
            cv_scores = self._cross_validate_model(model, X_train_scaled, y_train, config)
            
            # Feature importance
            feature_importance = self._get_feature_importance(model, config.feature_columns)
            
            # Calculate detailed metrics
            metrics = self._calculate_metrics(model, X_test_scaled, y_test, config.task_type)
            
            # Save model and scaler
            model_path = self._save_model(model, model_id)
            scaler_path = self._save_scaler(scaler, model_id)
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Create results
            results = TrainingResults(
                model_id=model_id,
                model_type=config.model_type,
                task_type=config.task_type,
                training_score=train_score,
                validation_score=val_score,
                test_score=test_score,
                feature_importance=feature_importance,
                hyperparameters=config.hyperparameters,
                training_time=training_time,
                model_path=model_path,
                scaler_path=scaler_path,
                metrics=metrics,
                cross_validation_scores=cv_scores
            )
            
            # Store results
            self.trained_models[model_id] = results
            self.training_history.append(results)
            self._save_training_results(results)
            
            logger.info(f"Model {model_id} training completed. Test score: {test_score:.4f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
    
    def _prepare_data(self, data: pd.DataFrame, config: ModelConfig) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target from raw data"""
        # Ensure all required columns exist
        missing_cols = [col for col in config.feature_columns if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing feature columns: {missing_cols}")
        
        if config.target_column not in data.columns:
            raise ValueError(f"Missing target column: {config.target_column}")
        
        # Extract features and target
        X = data[config.feature_columns].copy()
        y = data[config.target_column].copy()
        
        # Handle missing values
        X = X.fillna(method='ffill').fillna(method='bfill')
        y = y.fillna(method='ffill').fillna(method='bfill')
        
        # Remove any remaining NaN rows
        valid_idx = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_idx]
        y = y[valid_idx]
        
        logger.info(f"Prepared data: {len(X)} samples, {len(config.feature_columns)} features")
        
        return X, y
    
    def _split_data(self, X: pd.DataFrame, y: pd.Series, config: ModelConfig) -> Tuple:
        """Split data into train/validation/test sets"""
        n_samples = len(X)
        
        # Calculate split indices
        test_size = int(n_samples * config.test_split)
        val_size = int(n_samples * config.validation_split)
        train_size = n_samples - test_size - val_size
        
        # Time-series aware splitting (no shuffling)
        X_train = X.iloc[:train_size]
        X_val = X.iloc[train_size:train_size + val_size]
        X_test = X.iloc[train_size + val_size:]
        
        y_train = y.iloc[:train_size]
        y_val = y.iloc[train_size:train_size + val_size]
        y_test = y.iloc[train_size + val_size:]
        
        logger.info(f"Data split - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def _fit_scaler(self, X_train: pd.DataFrame, scaling_method: str):
        """Fit and return data scaler"""
        if scaling_method not in self.scalers:
            raise ValueError(f"Unknown scaling method: {scaling_method}")
        
        scaler = self.scalers[scaling_method].__class__()
        scaler.fit(X_train)
        return scaler
    
    def _fit_feature_selector(self, X_train: np.ndarray, y_train: pd.Series, config: ModelConfig):
        """Fit feature selector for dimensionality reduction"""
        from sklearn.feature_selection import SelectKBest, f_regression, f_classif
        
        if config.task_type == TaskType.REGRESSION:
            selector = SelectKBest(score_func=f_regression, k=min(config.feature_selection_k, X_train.shape[1]))
        else:
            selector = SelectKBest(score_func=f_classif, k=min(config.feature_selection_k, X_train.shape[1]))
        
        selector.fit(X_train, y_train)
        return selector
    
    def _initialize_model(self, config: ModelConfig):
        """Initialize ML model based on configuration"""
        model_type = config.model_type
        task_type = config.task_type
        params = config.hyperparameters
        
        if model_type == ModelType.RANDOM_FOREST:
            if task_type == TaskType.REGRESSION:
                return RandomForestRegressor(random_state=config.random_state, **params)
            else:
                return RandomForestClassifier(random_state=config.random_state, **params)
                
        elif model_type == ModelType.GRADIENT_BOOSTING:
            if task_type == TaskType.REGRESSION:
                return GradientBoostingRegressor(random_state=config.random_state, **params)
            else:
                return GradientBoostingClassifier(random_state=config.random_state, **params)
                
        elif model_type == ModelType.LINEAR_REGRESSION:
            return LinearRegression(**params)
            
        elif model_type == ModelType.RIDGE_REGRESSION:
            return Ridge(random_state=config.random_state, **params)
            
        elif model_type == ModelType.LASSO_REGRESSION:
            return Lasso(random_state=config.random_state, **params)
            
        elif model_type == ModelType.LOGISTIC_REGRESSION:
            return LogisticRegression(random_state=config.random_state, **params)
            
        elif model_type == ModelType.SVM:
            if task_type == TaskType.REGRESSION:
                return SVR(**params)
            else:
                return SVC(random_state=config.random_state, **params)
                
        elif model_type == ModelType.XGBOOST:
            if not XGBOOST_AVAILABLE:
                raise ImportError("XGBoost not available")
            if task_type == TaskType.REGRESSION:
                return xgb.XGBRegressor(random_state=config.random_state, **params)
            else:
                return xgb.XGBClassifier(random_state=config.random_state, **params)
                
        elif model_type == ModelType.LIGHTGBM:
            if not LIGHTGBM_AVAILABLE:
                raise ImportError("LightGBM not available")
            if task_type == TaskType.REGRESSION:
                return lgb.LGBMRegressor(random_state=config.random_state, **params)
            else:
                return lgb.LGBMClassifier(random_state=config.random_state, **params)
                
        elif model_type in [ModelType.LSTM, ModelType.TRANSFORMER]:
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch not available for deep learning models")
            return self._initialize_deep_learning_model(config)
            
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def _initialize_deep_learning_model(self, config: ModelConfig):
        """Initialize deep learning model"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")
        
        input_size = len(config.feature_columns)
        
        if config.model_type == ModelType.LSTM:
            return LSTMModel(
                input_size=input_size,
                hidden_size=config.hyperparameters.get('hidden_size', 64),
                num_layers=config.hyperparameters.get('num_layers', 2),
                output_size=1,
                dropout=config.hyperparameters.get('dropout', 0.2)
            )
        elif config.model_type == ModelType.TRANSFORMER:
            return TransformerModel(
                input_size=input_size,
                d_model=config.hyperparameters.get('d_model', 64),
                nhead=config.hyperparameters.get('nhead', 8),
                num_layers=config.hyperparameters.get('num_layers', 2),
                output_size=1,
                dropout=config.hyperparameters.get('dropout', 0.1)
            )
    
    async def _optimize_hyperparameters(self, model, X_train, y_train, config: ModelConfig):
        """Optimize model hyperparameters using grid/random search"""
        try:
            param_grid = self._get_hyperparameter_grid(config.model_type)
            
            if not param_grid:
                logger.info("No hyperparameter optimization for this model type")
                return model
            
            # Use time series cross-validation
            tscv = TimeSeriesSplit(n_splits=config.cross_validation_folds)
            
            # Use RandomizedSearchCV for efficiency
            search = RandomizedSearchCV(
                model,
                param_grid,
                cv=tscv,
                n_iter=20,  # Limit iterations for speed
                scoring=self._get_scoring_metric(config.task_type),
                random_state=config.random_state,
                n_jobs=-1
            )
            
            search.fit(X_train, y_train)
            
            logger.info(f"Best hyperparameters: {search.best_params_}")
            logger.info(f"Best CV score: {search.best_score_:.4f}")
            
            return search.best_estimator_
            
        except Exception as e:
            logger.warning(f"Hyperparameter optimization failed: {str(e)}")
            return model
    
    def _get_hyperparameter_grid(self, model_type: ModelType) -> Dict:
        """Get hyperparameter grid for optimization"""
        grids = {
            ModelType.RANDOM_FOREST: {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            },
            ModelType.GRADIENT_BOOSTING: {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 0.9, 1.0]
            },
            ModelType.RIDGE_REGRESSION: {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            },
            ModelType.LASSO_REGRESSION: {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            },
            ModelType.SVM: {
                'C': [0.1, 1.0, 10.0],
                'gamma': ['scale', 'auto', 0.1, 1.0]
            }
        }
        
        if XGBOOST_AVAILABLE:
            grids[ModelType.XGBOOST] = {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0]
            }
        
        if LIGHTGBM_AVAILABLE:
            grids[ModelType.LIGHTGBM] = {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [-1, 5, 10],
                'num_leaves': [31, 50, 100],
                'subsample': [0.8, 0.9, 1.0]
            }
        
        return grids.get(model_type, {})
    
    def _get_scoring_metric(self, task_type: TaskType) -> str:
        """Get appropriate scoring metric for task type"""
        if task_type == TaskType.REGRESSION:
            return 'neg_mean_squared_error'
        else:
            return 'accuracy'
    
    def _train_sklearn_model(self, model, X_train, y_train, config: ModelConfig):
        """Train scikit-learn model"""
        model.fit(X_train, y_train)
        return model
    
    async def _train_deep_learning_model(self, model, X_train, y_train, X_val, y_val, config: ModelConfig):
        """Train deep learning model with PyTorch"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        
        # Convert data to tensors
        X_train_tensor = torch.FloatTensor(X_train).to(device)
        y_train_tensor = torch.FloatTensor(y_train.values).to(device)
        X_val_tensor = torch.FloatTensor(X_val).to(device)
        y_val_tensor = torch.FloatTensor(y_val.values).to(device)
        
        # Create data loaders
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        
        # Loss function and optimizer
        if config.task_type == TaskType.REGRESSION:
            criterion = nn.MSELoss()
        else:
            criterion = nn.CrossEntropyLoss()
        
        optimizer = optim.Adam(model.parameters(), lr=config.hyperparameters.get('learning_rate', 0.001))
        
        # Training loop
        epochs = config.hyperparameters.get('epochs', 100)
        best_val_loss = float('inf')
        patience = config.early_stopping_rounds
        patience_counter = 0
        
        for epoch in range(epochs):
            model.train()
            train_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs.squeeze(), batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            # Validation
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val_tensor)
                val_loss = criterion(val_outputs.squeeze(), y_val_tensor).item()
            
            # Early stopping
            if config.early_stopping:
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logger.info(f"Early stopping at epoch {epoch}")
                        break
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Train Loss: {train_loss/len(train_loader):.4f}, Val Loss: {val_loss:.4f}")
        
        return model
    
    def _evaluate_model(self, model, X, y, task_type: TaskType) -> float:
        """Evaluate model performance"""
        if hasattr(model, 'predict'):
            y_pred = model.predict(X)
        else:  # PyTorch model
            model.eval()
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X)
                y_pred = model(X_tensor).squeeze().numpy()
        
        if task_type == TaskType.REGRESSION:
            return -mean_squared_error(y, y_pred)  # Negative for consistency with sklearn scoring
        else:
            return accuracy_score(y, y_pred)
    
    def _cross_validate_model(self, model, X, y, config: ModelConfig) -> List[float]:
        """Perform cross-validation"""
        try:
            from sklearn.model_selection import cross_val_score
            
            tscv = TimeSeriesSplit(n_splits=config.cross_validation_folds)
            scoring = self._get_scoring_metric(config.task_type)
            
            scores = cross_val_score(model, X, y, cv=tscv, scoring=scoring)
            return scores.tolist()
            
        except Exception as e:
            logger.warning(f"Cross-validation failed: {str(e)}")
            return []
    
    def _get_feature_importance(self, model, feature_names: List[str]) -> Dict[str, float]:
        """Extract feature importance from model"""
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importances = np.abs(model.coef_).flatten()
            else:
                return {}
            
            # Ensure we have the right number of features
            if len(importances) != len(feature_names):
                logger.warning(f"Feature importance length mismatch: {len(importances)} vs {len(feature_names)}")
                return {}
            
            importance_dict = dict(zip(feature_names, importances))
            
            # Normalize to sum to 1
            total_importance = sum(importance_dict.values())
            if total_importance > 0:
                importance_dict = {k: v / total_importance for k, v in importance_dict.items()}
            
            return importance_dict
            
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {str(e)}")
            return {}
    
    def _calculate_metrics(self, model, X_test, y_test, task_type: TaskType) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        try:
            if hasattr(model, 'predict'):
                y_pred = model.predict(X_test)
            else:  # PyTorch model
                model.eval()
                with torch.no_grad():
                    X_tensor = torch.FloatTensor(X_test)
                    y_pred = model(X_tensor).squeeze().numpy()
            
            metrics = {}
            
            if task_type == TaskType.REGRESSION:
                metrics['mse'] = mean_squared_error(y_test, y_pred)
                metrics['rmse'] = np.sqrt(metrics['mse'])
                metrics['mae'] = mean_absolute_error(y_test, y_pred)
                
                # R-squared
                ss_res = np.sum((y_test - y_pred) ** 2)
                ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
                metrics['r2'] = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                
            else:
                y_pred_binary = (y_pred > 0.5).astype(int) if len(np.unique(y_test)) == 2 else y_pred
                
                metrics['accuracy'] = accuracy_score(y_test, y_pred_binary)
                metrics['precision'] = precision_score(y_test, y_pred_binary, average='weighted')
                metrics['recall'] = recall_score(y_test, y_pred_binary, average='weighted')
                metrics['f1'] = f1_score(y_test, y_pred_binary, average='weighted')
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {}
    
    def _save_model(self, model, model_id: str) -> str:
        """Save trained model to disk"""
        model_path = self.models_dir / f"{model_id}_model.pkl"
        
        try:
            if hasattr(model, 'state_dict'):  # PyTorch model
                torch.save(model.state_dict(), model_path)
            else:  # Scikit-learn model
                joblib.dump(model, model_path)
            
            logger.info(f"Model saved to {model_path}")
            return str(model_path)
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def _save_scaler(self, scaler, model_id: str) -> str:
        """Save data scaler to disk"""
        scaler_path = self.models_dir / f"{model_id}_scaler.pkl"
        
        try:
            joblib.dump(scaler, scaler_path)
            logger.info(f"Scaler saved to {scaler_path}")
            return str(scaler_path)
            
        except Exception as e:
            logger.error(f"Error saving scaler: {str(e)}")
            raise
    
    def _save_training_results(self, results: TrainingResults):
        """Save training results to experiment tracking"""
        results_path = self.experiments_dir / f"{results.model_id}_results.json"
        
        try:
            results_dict = asdict(results)
            results_dict['timestamp'] = datetime.now().isoformat()
            
            with open(results_path, 'w') as f:
                json.dump(results_dict, f, indent=2, default=str)
            
            logger.info(f"Training results saved to {results_path}")
            
        except Exception as e:
            logger.error(f"Error saving training results: {str(e)}")
    
    def load_model(self, model_id: str) -> Tuple[Any, Any]:
        """Load trained model and scaler"""
        model_path = self.models_dir / f"{model_id}_model.pkl"
        scaler_path = self.models_dir / f"{model_id}_scaler.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            # Load model
            if model_path.suffix == '.pth':  # PyTorch model
                # Note: Would need model architecture to load PyTorch model properly
                raise NotImplementedError("PyTorch model loading not implemented in this example")
            else:
                model = joblib.load(model_path)
            
            # Load scaler if exists
            scaler = None
            if scaler_path.exists():
                scaler = joblib.load(scaler_path)
            
            logger.info(f"Model {model_id} loaded successfully")
            return model, scaler
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def get_model_summary(self) -> pd.DataFrame:
        """Get summary of all trained models"""
        if not self.training_history:
            return pd.DataFrame()
        
        summary_data = []
        for result in self.training_history:
            summary_data.append({
                'model_id': result.model_id,
                'model_type': result.model_type.value,
                'task_type': result.task_type.value,
                'test_score': result.test_score,
                'validation_score': result.validation_score,
                'training_time': result.training_time,
                'cv_mean': np.mean(result.cross_validation_scores) if result.cross_validation_scores else None,
                'cv_std': np.std(result.cross_validation_scores) if result.cross_validation_scores else None
            })
        
        return pd.DataFrame(summary_data)


# Deep Learning Models (if PyTorch is available)
if TORCH_AVAILABLE:
    class LSTMModel(nn.Module):
        """LSTM model for time series prediction"""
        
        def __init__(self, input_size: int, hidden_size: int, num_layers: int, 
                     output_size: int, dropout: float = 0.2):
            super(LSTMModel, self).__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                               batch_first=True, dropout=dropout)
            self.fc = nn.Linear(hidden_size, output_size)
            self.dropout = nn.Dropout(dropout)
            
        def forward(self, x):
            # Initialize hidden state
            h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
            c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
            
            # LSTM forward pass
            out, _ = self.lstm(x.unsqueeze(1), (h0, c0))
            out = self.dropout(out[:, -1, :])  # Take last output
            out = self.fc(out)
            
            return out
    
    
    class TransformerModel(nn.Module):
        """Transformer model for sequence prediction"""
        
        def __init__(self, input_size: int, d_model: int, nhead: int, 
                     num_layers: int, output_size: int, dropout: float = 0.1):
            super(TransformerModel, self).__init__()
            self.input_projection = nn.Linear(input_size, d_model)
            self.positional_encoding = nn.Parameter(torch.randn(1000, d_model))
            
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model, 
                nhead=nhead, 
                dropout=dropout,
                batch_first=True
            )
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
            self.fc = nn.Linear(d_model, output_size)
            self.dropout = nn.Dropout(dropout)
            
        def forward(self, x):
            # Project input to d_model dimensions
            x = self.input_projection(x.unsqueeze(1))
            
            # Add positional encoding
            seq_len = x.size(1)
            x += self.positional_encoding[:seq_len, :].unsqueeze(0)
            
            # Transformer forward pass
            x = self.transformer(x)
            x = self.dropout(x[:, -1, :])  # Take last output
            x = self.fc(x)
            
            return x


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_model_training():
        """Test the model training framework"""
        
        # Generate sample data
        np.random.seed(42)
        n_samples = 1000
        n_features = 20
        
        # Create synthetic financial data
        dates = pd.date_range(start='2023-01-01', periods=n_samples, freq='1min')
        
        # Generate correlated features (simulating technical indicators)
        features = np.random.randn(n_samples, n_features)
        for i in range(1, n_features):
            features[:, i] = 0.7 * features[:, i-1] + 0.3 * features[:, i]
        
        # Create target (next period return)
        target = np.roll(features[:, 0], -1) + 0.1 * np.random.randn(n_samples)
        target[-1] = target[-2]  # Fill last value
        
        # Create DataFrame
        feature_columns = [f'feature_{i}' for i in range(n_features)]
        data = pd.DataFrame(features, columns=feature_columns, index=dates)
        data['target'] = target
        
        # Initialize trainer
        trainer = ModelTrainer()
        
        # Test different model configurations
        model_configs = [
            ModelConfig(
                model_type=ModelType.RANDOM_FOREST,
                task_type=TaskType.REGRESSION,
                target_column='target',
                feature_columns=feature_columns,
                hyperparameters={'n_estimators': 100, 'max_depth': 10}
            ),
            ModelConfig(
                model_type=ModelType.LINEAR_REGRESSION,
                task_type=TaskType.REGRESSION,
                target_column='target',
                feature_columns=feature_columns,
                hyperparameters={}
            )
        ]
        
        if XGBOOST_AVAILABLE:
            model_configs.append(
                ModelConfig(
                    model_type=ModelType.XGBOOST,
                    task_type=TaskType.REGRESSION,
                    target_column='target',
                    feature_columns=feature_columns,
                    hyperparameters={'n_estimators': 100, 'max_depth': 6}
                )
            )
        
        # Train models
        results = []
        for config in model_configs:
            print(f"\nTraining {config.model_type.value} model...")
            result = await trainer.train_model(data, config, optimize_hyperparameters=True)
            results.append(result)
            
            print(f"Model ID: {result.model_id}")
            print(f"Test Score: {result.test_score:.4f}")
            print(f"Training Time: {result.training_time:.2f}s")
            print(f"Top 5 Features:")
            
            # Sort features by importance
            sorted_features = sorted(result.feature_importance.items(), 
                                   key=lambda x: x[1], reverse=True)
            for name, importance in sorted_features[:5]:
                print(f"  {name}: {importance:.4f}")
        
        # Get model summary
        summary = trainer.get_model_summary()
        print("\nModel Summary:")
        print(summary.to_string(index=False))
        
        print(f"\nTraining completed. {len(results)} models trained.")
    
    # Run the test
    asyncio.run(test_model_training())