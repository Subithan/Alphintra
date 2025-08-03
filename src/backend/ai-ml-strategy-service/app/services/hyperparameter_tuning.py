"""
Hyperparameter tuning automation service for Phase 4: Model Training Orchestrator.
Provides intelligent hyperparameter optimization using various algorithms and strategies.
"""

import logging
import asyncio
import json
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import UUID, uuid4
import numpy as np
from scipy.stats import uniform, randint, loguniform
from scipy.optimize import minimize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.training import (
    HyperparameterTuningJob, HyperparameterTrial, TrainingJob,
    OptimizationObjective, OptimizationAlgorithm, JobStatus,
    InstanceType, ModelFramework
)
from app.models.strategy import Strategy
from app.models.dataset import Dataset
from app.core.config import get_settings


class ParameterSpace:
    """Represents a hyperparameter search space."""
    
    def __init__(self, space_definition: Dict[str, Any]):
        self.space_definition = space_definition
        self.parameters = {}
        self._parse_space_definition()
    
    def _parse_space_definition(self):
        """Parse space definition into parameter objects."""
        for param_name, config in self.space_definition.items():
            param_type = config.get("type", "float")
            
            if param_type == "float":
                self.parameters[param_name] = FloatParameter(
                    name=param_name,
                    min_value=config["min"],
                    max_value=config["max"],
                    log_scale=config.get("log_scale", False)
                )
            elif param_type == "int":
                self.parameters[param_name] = IntParameter(
                    name=param_name,
                    min_value=config["min"],
                    max_value=config["max"]
                )
            elif param_type == "categorical":
                self.parameters[param_name] = CategoricalParameter(
                    name=param_name,
                    choices=config["choices"]
                )
            elif param_type == "bool":
                self.parameters[param_name] = BooleanParameter(name=param_name)
    
    def sample_random(self) -> Dict[str, Any]:
        """Sample random values from the parameter space."""
        sample = {}
        for param_name, param in self.parameters.items():
            sample[param_name] = param.sample_random()
        return sample
    
    def get_bounds(self) -> List[Tuple[float, float]]:
        """Get parameter bounds for optimization algorithms."""
        bounds = []
        for param in self.parameters.values():
            bounds.append(param.get_bounds())
        return bounds
    
    def denormalize_vector(self, normalized_vector: List[float]) -> Dict[str, Any]:
        """Convert normalized vector back to parameter values."""
        result = {}
        for i, (param_name, param) in enumerate(self.parameters.items()):
            result[param_name] = param.denormalize(normalized_vector[i])
        return result
    
    def normalize_dict(self, param_dict: Dict[str, Any]) -> List[float]:
        """Convert parameter dictionary to normalized vector."""
        vector = []
        for param_name, param in self.parameters.items():
            vector.append(param.normalize(param_dict.get(param_name)))
        return vector


class Parameter:
    """Base class for hyperparameters."""
    
    def __init__(self, name: str):
        self.name = name
    
    def sample_random(self) -> Any:
        raise NotImplementedError
    
    def get_bounds(self) -> Tuple[float, float]:
        raise NotImplementedError
    
    def normalize(self, value: Any) -> float:
        raise NotImplementedError
    
    def denormalize(self, normalized_value: float) -> Any:
        raise NotImplementedError


class FloatParameter(Parameter):
    """Continuous floating-point parameter."""
    
    def __init__(self, name: str, min_value: float, max_value: float, log_scale: bool = False):
        super().__init__(name)
        self.min_value = min_value
        self.max_value = max_value
        self.log_scale = log_scale
    
    def sample_random(self) -> float:
        if self.log_scale:
            return loguniform.rvs(self.min_value, self.max_value)
        else:
            return uniform.rvs(self.min_value, self.max_value - self.min_value)
    
    def get_bounds(self) -> Tuple[float, float]:
        return (0.0, 1.0)  # Normalized bounds
    
    def normalize(self, value: float) -> float:
        if self.log_scale:
            log_min = math.log(self.min_value)
            log_max = math.log(self.max_value)
            log_val = math.log(max(value, self.min_value))
            return (log_val - log_min) / (log_max - log_min)
        else:
            return (value - self.min_value) / (self.max_value - self.min_value)
    
    def denormalize(self, normalized_value: float) -> float:
        normalized_value = max(0.0, min(1.0, normalized_value))
        if self.log_scale:
            log_min = math.log(self.min_value)
            log_max = math.log(self.max_value)
            log_val = log_min + normalized_value * (log_max - log_min)
            return math.exp(log_val)
        else:
            return self.min_value + normalized_value * (self.max_value - self.min_value)


class IntParameter(Parameter):
    """Integer parameter."""
    
    def __init__(self, name: str, min_value: int, max_value: int):
        super().__init__(name)
        self.min_value = min_value
        self.max_value = max_value
    
    def sample_random(self) -> int:
        return randint.rvs(self.min_value, self.max_value + 1)
    
    def get_bounds(self) -> Tuple[float, float]:
        return (0.0, 1.0)
    
    def normalize(self, value: int) -> float:
        return (value - self.min_value) / (self.max_value - self.min_value)
    
    def denormalize(self, normalized_value: float) -> int:
        normalized_value = max(0.0, min(1.0, normalized_value))
        return round(self.min_value + normalized_value * (self.max_value - self.min_value))


class CategoricalParameter(Parameter):
    """Categorical parameter."""
    
    def __init__(self, name: str, choices: List[Any]):
        super().__init__(name)
        self.choices = choices
    
    def sample_random(self) -> Any:
        return random.choice(self.choices)
    
    def get_bounds(self) -> Tuple[float, float]:
        return (0.0, 1.0)
    
    def normalize(self, value: Any) -> float:
        try:
            index = self.choices.index(value)
            return index / (len(self.choices) - 1) if len(self.choices) > 1 else 0.0
        except ValueError:
            return 0.0
    
    def denormalize(self, normalized_value: float) -> Any:
        normalized_value = max(0.0, min(1.0, normalized_value))
        index = round(normalized_value * (len(self.choices) - 1))
        return self.choices[index]


class BooleanParameter(Parameter):
    """Boolean parameter."""
    
    def __init__(self, name: str):
        super().__init__(name)
    
    def sample_random(self) -> bool:
        return random.choice([True, False])
    
    def get_bounds(self) -> Tuple[float, float]:
        return (0.0, 1.0)
    
    def normalize(self, value: bool) -> float:
        return 1.0 if value else 0.0
    
    def denormalize(self, normalized_value: float) -> bool:
        return normalized_value > 0.5


class RandomSearchOptimizer:
    """Random search optimization algorithm."""
    
    def __init__(self, parameter_space: ParameterSpace, random_seed: int = None):
        self.parameter_space = parameter_space
        self.random_seed = random_seed
        if random_seed:
            random.seed(random_seed)
            np.random.seed(random_seed)
    
    def suggest_parameters(self, trial_number: int, 
                         previous_trials: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Suggest parameters for the next trial."""
        return self.parameter_space.sample_random()


class GridSearchOptimizer:
    """Grid search optimization algorithm."""
    
    def __init__(self, parameter_space: ParameterSpace, grid_resolution: int = 5):
        self.parameter_space = parameter_space
        self.grid_resolution = grid_resolution
        self.grid_points = self._generate_grid_points()
        self.current_index = 0
    
    def _generate_grid_points(self) -> List[Dict[str, Any]]:
        """Generate all grid points."""
        # Simplified grid generation for demonstration
        points = []
        
        # For each parameter, create discrete values
        param_grids = {}
        for param_name, param in self.parameter_space.parameters.items():
            if isinstance(param, FloatParameter):
                if param.log_scale:
                    log_min = math.log(param.min_value)
                    log_max = math.log(param.max_value)
                    log_values = np.linspace(log_min, log_max, self.grid_resolution)
                    param_grids[param_name] = [math.exp(v) for v in log_values]
                else:
                    param_grids[param_name] = np.linspace(
                        param.min_value, param.max_value, self.grid_resolution
                    ).tolist()
            elif isinstance(param, IntParameter):
                param_grids[param_name] = list(range(
                    param.min_value, 
                    min(param.max_value + 1, param.min_value + self.grid_resolution)
                ))
            elif isinstance(param, CategoricalParameter):
                param_grids[param_name] = param.choices
            elif isinstance(param, BooleanParameter):
                param_grids[param_name] = [True, False]
        
        # Generate all combinations
        import itertools
        
        param_names = list(param_grids.keys())
        param_values = [param_grids[name] for name in param_names]
        
        for combination in itertools.product(*param_values):
            point = dict(zip(param_names, combination))
            points.append(point)
        
        return points
    
    def suggest_parameters(self, trial_number: int,
                         previous_trials: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Suggest parameters for the next trial."""
        if self.current_index >= len(self.grid_points):
            # Grid exhausted, fall back to random
            return self.parameter_space.sample_random()
        
        point = self.grid_points[self.current_index]
        self.current_index += 1
        return point


class BayesianOptimizer:
    """Bayesian optimization using Gaussian Process."""
    
    def __init__(self, parameter_space: ParameterSpace, acquisition_function: str = "ei"):
        self.parameter_space = parameter_space
        self.acquisition_function = acquisition_function
        self.gp_model = None
        self.X_observed = []
        self.y_observed = []
    
    def suggest_parameters(self, trial_number: int,
                         previous_trials: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Suggest parameters using Bayesian optimization."""
        if not previous_trials or len(previous_trials) < 2:
            # Not enough data for GP, use random sampling
            return self.parameter_space.sample_random()
        
        # Prepare training data
        X = []
        y = []
        for trial in previous_trials:
            if trial.get("objective_value") is not None:
                param_vector = self.parameter_space.normalize_dict(trial["hyperparameters"])
                X.append(param_vector)
                y.append(trial["objective_value"])
        
        if len(X) < 2:
            return self.parameter_space.sample_random()
        
        X = np.array(X)
        y = np.array(y)
        
        # Fit Gaussian Process
        kernel = Matern(length_scale=1.0, nu=2.5)
        self.gp_model = GaussianProcessRegressor(kernel=kernel, alpha=1e-6, normalize_y=True)
        self.gp_model.fit(X, y)
        
        # Optimize acquisition function
        bounds = self.parameter_space.get_bounds()
        
        # Multiple random starts for acquisition optimization
        best_x = None
        best_acq = float('-inf')
        
        for _ in range(10):  # 10 random starts
            x0 = [random.uniform(b[0], b[1]) for b in bounds]
            
            try:
                result = minimize(
                    fun=lambda x: -self._acquisition_function(x, X, y),
                    x0=x0,
                    bounds=bounds,
                    method='L-BFGS-B'
                )
                
                if result.success and -result.fun > best_acq:
                    best_acq = -result.fun
                    best_x = result.x
            except:
                continue
        
        if best_x is not None:
            return self.parameter_space.denormalize_vector(best_x.tolist())
        else:
            return self.parameter_space.sample_random()
    
    def _acquisition_function(self, x: np.ndarray, X_observed: np.ndarray, 
                            y_observed: np.ndarray) -> float:
        """Calculate acquisition function value."""
        x = x.reshape(1, -1)
        
        if self.acquisition_function == "ei":  # Expected Improvement
            return self._expected_improvement(x, X_observed, y_observed)
        elif self.acquisition_function == "ucb":  # Upper Confidence Bound
            return self._upper_confidence_bound(x, X_observed, y_observed)
        else:
            return self._expected_improvement(x, X_observed, y_observed)
    
    def _expected_improvement(self, x: np.ndarray, X_observed: np.ndarray, 
                            y_observed: np.ndarray) -> float:
        """Expected Improvement acquisition function."""
        mu, sigma = self.gp_model.predict(x, return_std=True)
        mu = mu[0]
        sigma = sigma[0]
        
        if sigma == 0:
            return 0
        
        f_best = np.max(y_observed)
        z = (mu - f_best) / sigma
        
        from scipy.stats import norm
        ei = (mu - f_best) * norm.cdf(z) + sigma * norm.pdf(z)
        return ei
    
    def _upper_confidence_bound(self, x: np.ndarray, X_observed: np.ndarray,
                               y_observed: np.ndarray, kappa: float = 2.0) -> float:
        """Upper Confidence Bound acquisition function."""
        mu, sigma = self.gp_model.predict(x, return_std=True)
        return mu[0] + kappa * sigma[0]


class HyperparameterTuningService:
    """Main service for hyperparameter tuning automation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
    
    async def create_tuning_job(self, job_data: Dict[str, Any], user_id: str,
                              db: AsyncSession) -> Dict[str, Any]:
        """Create a new hyperparameter tuning job."""
        try:
            # Validate required fields
            required_fields = ["strategy_id", "dataset_id", "job_name", "parameter_space", 
                             "objective_metric", "optimization_objective"]
            for field in required_fields:
                if field not in job_data:
                    return {"success": False, "error": f"Missing required field: {field}"}
            
            # Validate strategy exists and belongs to user
            result = await db.execute(
                select(Strategy)
                .where(
                    and_(
                        Strategy.id == UUID(job_data["strategy_id"]),
                        Strategy.user_id == UUID(user_id)
                    )
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return {"success": False, "error": "Strategy not found or access denied"}
            
            # Validate dataset exists and user has access
            result = await db.execute(
                select(Dataset)
                .where(
                    or_(
                        and_(
                            Dataset.id == UUID(job_data["dataset_id"]),
                            Dataset.user_id == UUID(user_id)
                        ),
                        and_(
                            Dataset.id == UUID(job_data["dataset_id"]),
                            Dataset.is_public == True
                        )
                    )
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {"success": False, "error": "Dataset not found or access denied"}
            
            # Validate parameter space
            parameter_space_validation = self._validate_parameter_space(job_data["parameter_space"])
            if not parameter_space_validation["valid"]:
                return {"success": False, "error": parameter_space_validation["error"]}
            
            # Create tuning job
            tuning_job = HyperparameterTuningJob(
                id=uuid4(),
                user_id=UUID(user_id),
                strategy_id=UUID(job_data["strategy_id"]),
                dataset_id=UUID(job_data["dataset_id"]),
                job_name=job_data["job_name"],
                optimization_algorithm=OptimizationAlgorithm(job_data.get(
                    "optimization_algorithm", OptimizationAlgorithm.RANDOM_SEARCH.value
                )),
                optimization_objective=OptimizationObjective(job_data["optimization_objective"]),
                objective_metric=job_data["objective_metric"],
                max_trials=job_data.get("max_trials", 100),
                max_parallel_trials=job_data.get("max_parallel_trials", 4),
                max_trial_duration_hours=job_data.get("max_trial_duration_hours", 4),
                parameter_space=job_data["parameter_space"],
                early_stopping_config=job_data.get("early_stopping_config", {}),
                instance_type=InstanceType(job_data.get("instance_type", InstanceType.GPU_T4.value)),
                estimated_cost=self._estimate_tuning_cost(job_data),
                status=JobStatus.PENDING
            )
            
            db.add(tuning_job)
            await db.commit()
            await db.refresh(tuning_job)
            
            self.logger.info(f"Created hyperparameter tuning job {tuning_job.id}")
            
            return {
                "success": True,
                "tuning_job_id": str(tuning_job.id),
                "estimated_cost": tuning_job.estimated_cost,
                "estimated_duration_hours": tuning_job.max_trials * tuning_job.max_trial_duration_hours / tuning_job.max_parallel_trials
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create hyperparameter tuning job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def start_tuning_job(self, tuning_job_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Start a hyperparameter tuning job."""
        try:
            result = await db.execute(
                select(HyperparameterTuningJob)
                .where(HyperparameterTuningJob.id == UUID(tuning_job_id))
            )
            tuning_job = result.scalar_one_or_none()
            
            if not tuning_job:
                return {"success": False, "error": "Tuning job not found"}
            
            if tuning_job.status != JobStatus.PENDING:
                return {"success": False, "error": f"Cannot start job with status {tuning_job.status.value}"}
            
            # Update job status
            tuning_job.status = JobStatus.RUNNING
            tuning_job.start_time = datetime.utcnow()
            
            # Initialize optimizer
            parameter_space = ParameterSpace(tuning_job.parameter_space)
            optimizer = self._create_optimizer(tuning_job.optimization_algorithm, parameter_space)
            
            # Generate initial trials
            initial_trials = min(tuning_job.max_parallel_trials, tuning_job.max_trials)
            for i in range(initial_trials):
                suggested_params = optimizer.suggest_parameters(i + 1)
                
                trial = HyperparameterTrial(
                    id=uuid4(),
                    tuning_job_id=tuning_job.id,
                    trial_number=i + 1,
                    hyperparameters=suggested_params,
                    status=JobStatus.PENDING,
                    objective_metric=tuning_job.objective_metric
                )
                
                db.add(trial)
            
            await db.commit()
            
            self.logger.info(f"Started hyperparameter tuning job {tuning_job_id} with {initial_trials} initial trials")
            
            return {
                "success": True,
                "message": "Hyperparameter tuning job started",
                "initial_trials": initial_trials
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start tuning job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def suggest_next_trial(self, tuning_job_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Suggest parameters for the next trial."""
        try:
            result = await db.execute(
                select(HyperparameterTuningJob)
                .options(selectinload(HyperparameterTuningJob.trials))
                .where(HyperparameterTuningJob.id == UUID(tuning_job_id))
            )
            tuning_job = result.scalar_one_or_none()
            
            if not tuning_job:
                return {"success": False, "error": "Tuning job not found"}
            
            # Check if we've reached max trials
            if len(tuning_job.trials) >= tuning_job.max_trials:
                return {"success": False, "error": "Maximum trials reached"}
            
            # Check if we have running capacity
            running_trials = len([t for t in tuning_job.trials if t.status == JobStatus.RUNNING])
            if running_trials >= tuning_job.max_parallel_trials:
                return {"success": False, "error": "Maximum parallel trials reached"}
            
            # Get completed trials for optimization
            completed_trials = []
            for trial in tuning_job.trials:
                if trial.status == JobStatus.COMPLETED and trial.objective_value is not None:
                    completed_trials.append({
                        "hyperparameters": trial.hyperparameters,
                        "objective_value": trial.objective_value,
                        "trial_number": trial.trial_number
                    })
            
            # Create optimizer and suggest parameters
            parameter_space = ParameterSpace(tuning_job.parameter_space)
            optimizer = self._create_optimizer(tuning_job.optimization_algorithm, parameter_space)
            
            trial_number = len(tuning_job.trials) + 1
            suggested_params = optimizer.suggest_parameters(trial_number, completed_trials)
            
            # Create new trial
            trial = HyperparameterTrial(
                id=uuid4(),
                tuning_job_id=tuning_job.id,
                trial_number=trial_number,
                hyperparameters=suggested_params,
                status=JobStatus.PENDING,
                objective_metric=tuning_job.objective_metric
            )
            
            db.add(trial)
            await db.commit()
            await db.refresh(trial)
            
            self.logger.info(f"Suggested trial {trial_number} for tuning job {tuning_job_id}")
            
            return {
                "success": True,
                "trial_id": str(trial.id),
                "trial_number": trial_number,
                "suggested_parameters": suggested_params
            }
            
        except Exception as e:
            self.logger.error(f"Failed to suggest next trial: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_trial_result(self, trial_id: str, result_data: Dict[str, Any],
                                db: AsyncSession) -> Dict[str, Any]:
        """Update trial with results."""
        try:
            result = await db.execute(
                select(HyperparameterTrial)
                .where(HyperparameterTrial.id == UUID(trial_id))
            )
            trial = result.scalar_one_or_none()
            
            if not trial:
                return {"success": False, "error": "Trial not found"}
            
            # Update trial results
            trial.status = JobStatus(result_data.get("status", JobStatus.COMPLETED.value))
            trial.end_time = datetime.utcnow()
            trial.objective_value = result_data.get("objective_value")
            trial.final_metrics = result_data.get("final_metrics", {})
            trial.early_stopped = result_data.get("early_stopped", False)
            trial.compute_cost = result_data.get("compute_cost", 0.0)
            
            if trial.start_time:
                duration = trial.end_time - trial.start_time
                trial.duration_seconds = int(duration.total_seconds())
            
            await db.commit()
            
            # Check if this is the best trial so far
            await self._update_best_trial(trial.tuning_job_id, db)
            
            # Check if tuning job should be completed
            await self._check_tuning_completion(trial.tuning_job_id, db)
            
            self.logger.info(f"Updated trial {trial_id} with objective value {trial.objective_value}")
            
            return {"success": True, "message": "Trial result updated"}
            
        except Exception as e:
            self.logger.error(f"Failed to update trial result: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_tuning_status(self, tuning_job_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get status and progress of hyperparameter tuning job."""
        try:
            result = await db.execute(
                select(HyperparameterTuningJob)
                .options(selectinload(HyperparameterTuningJob.trials))
                .where(HyperparameterTuningJob.id == UUID(tuning_job_id))
            )
            tuning_job = result.scalar_one_or_none()
            
            if not tuning_job:
                return {"error": "Tuning job not found"}
            
            # Calculate statistics
            trials = tuning_job.trials
            total_trials = len(trials)
            completed_trials = len([t for t in trials if t.status == JobStatus.COMPLETED])
            running_trials = len([t for t in trials if t.status == JobStatus.RUNNING])
            failed_trials = len([t for t in trials if t.status == JobStatus.FAILED])
            
            # Get best trial
            best_trial = None
            if tuning_job.best_trial_id:
                for trial in trials:
                    if trial.id == tuning_job.best_trial_id:
                        best_trial = {
                            "trial_id": str(trial.id),
                            "trial_number": trial.trial_number,
                            "hyperparameters": trial.hyperparameters,
                            "objective_value": trial.objective_value,
                            "final_metrics": trial.final_metrics
                        }
                        break
            
            # Calculate progress
            progress_percentage = (completed_trials / tuning_job.max_trials) * 100 if tuning_job.max_trials > 0 else 0
            
            # Get objective values for analysis
            objective_values = [t.objective_value for t in trials 
                              if t.status == JobStatus.COMPLETED and t.objective_value is not None]
            
            # Calculate convergence metrics
            convergence_info = self._analyze_convergence(objective_values, tuning_job.optimization_objective)
            
            return {
                "tuning_job_id": str(tuning_job.id),
                "status": tuning_job.status.value,
                "progress_percentage": round(progress_percentage, 1),
                "trial_statistics": {
                    "total_trials": total_trials,
                    "completed_trials": completed_trials,
                    "running_trials": running_trials,
                    "failed_trials": failed_trials,
                    "max_trials": tuning_job.max_trials
                },
                "best_trial": best_trial,
                "optimization_objective": tuning_job.optimization_objective.value,
                "objective_metric": tuning_job.objective_metric,
                "convergence": convergence_info,
                "start_time": tuning_job.start_time.isoformat() if tuning_job.start_time else None,
                "end_time": tuning_job.end_time.isoformat() if tuning_job.end_time else None,
                "estimated_completion": self._estimate_completion_time(tuning_job, trials),
                "cost_tracking": {
                    "estimated_cost": tuning_job.estimated_cost,
                    "actual_cost": tuning_job.actual_cost,
                    "cost_per_trial": tuning_job.actual_cost / max(completed_trials, 1) if tuning_job.actual_cost else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get tuning status: {str(e)}")
            return {"error": str(e)}
    
    async def stop_tuning_job(self, tuning_job_id: str, user_id: str, 
                            db: AsyncSession) -> Dict[str, Any]:
        """Stop a running hyperparameter tuning job."""
        try:
            result = await db.execute(
                select(HyperparameterTuningJob)
                .where(
                    and_(
                        HyperparameterTuningJob.id == UUID(tuning_job_id),
                        HyperparameterTuningJob.user_id == UUID(user_id)
                    )
                )
            )
            tuning_job = result.scalar_one_or_none()
            
            if not tuning_job:
                return {"success": False, "error": "Tuning job not found or access denied"}
            
            if tuning_job.status not in [JobStatus.RUNNING, JobStatus.PENDING]:
                return {"success": False, "error": f"Cannot stop job with status {tuning_job.status.value}"}
            
            # Update job status
            tuning_job.status = JobStatus.CANCELLED
            tuning_job.end_time = datetime.utcnow()
            
            if tuning_job.start_time:
                duration = tuning_job.end_time - tuning_job.start_time
                tuning_job.duration_seconds = int(duration.total_seconds())
            
            # Cancel running trials
            result = await db.execute(
                select(HyperparameterTrial)
                .where(
                    and_(
                        HyperparameterTrial.tuning_job_id == tuning_job.id,
                        HyperparameterTrial.status.in_([JobStatus.RUNNING, JobStatus.PENDING])
                    )
                )
            )
            running_trials = result.scalars().all()
            
            for trial in running_trials:
                trial.status = JobStatus.CANCELLED
                trial.end_time = datetime.utcnow()
            
            await db.commit()
            
            self.logger.info(f"Stopped hyperparameter tuning job {tuning_job_id}")
            
            return {
                "success": True,
                "message": "Hyperparameter tuning job stopped",
                "cancelled_trials": len(running_trials)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to stop tuning job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _validate_parameter_space(self, parameter_space: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameter space definition."""
        try:
            if not parameter_space:
                return {"valid": False, "error": "Parameter space cannot be empty"}
            
            for param_name, config in parameter_space.items():
                if not isinstance(config, dict):
                    return {"valid": False, "error": f"Parameter {param_name} must be a dictionary"}
                
                param_type = config.get("type")
                if param_type not in ["float", "int", "categorical", "bool"]:
                    return {"valid": False, "error": f"Invalid parameter type: {param_type}"}
                
                if param_type in ["float", "int"]:
                    if "min" not in config or "max" not in config:
                        return {"valid": False, "error": f"Parameters {param_name} missing min or max"}
                    
                    if config["min"] >= config["max"]:
                        return {"valid": False, "error": f"Parameter {param_name} min must be less than max"}
                
                elif param_type == "categorical":
                    if "choices" not in config or not config["choices"]:
                        return {"valid": False, "error": f"Categorical parameter {param_name} must have choices"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _create_optimizer(self, algorithm: OptimizationAlgorithm, 
                         parameter_space: ParameterSpace):
        """Create optimizer based on algorithm."""
        if algorithm == OptimizationAlgorithm.RANDOM_SEARCH:
            return RandomSearchOptimizer(parameter_space)
        elif algorithm == OptimizationAlgorithm.GRID_SEARCH:
            return GridSearchOptimizer(parameter_space)
        elif algorithm == OptimizationAlgorithm.BAYESIAN_OPTIMIZATION:
            return BayesianOptimizer(parameter_space)
        else:
            # Default to random search
            return RandomSearchOptimizer(parameter_space)
    
    def _estimate_tuning_cost(self, job_data: Dict[str, Any]) -> float:
        """Estimate the cost of hyperparameter tuning job."""
        try:
            instance_type = InstanceType(job_data.get("instance_type", InstanceType.GPU_T4.value))
            max_trials = job_data.get("max_trials", 100)
            max_trial_duration_hours = job_data.get("max_trial_duration_hours", 4)
            max_parallel_trials = job_data.get("max_parallel_trials", 4)
            
            # Hourly rates (simplified)
            hourly_rates = {
                InstanceType.CPU_SMALL: 0.05,
                InstanceType.CPU_MEDIUM: 0.10,
                InstanceType.CPU_LARGE: 0.20,
                InstanceType.GPU_T4: 0.35,
                InstanceType.GPU_V100: 2.50,
                InstanceType.GPU_A100: 4.00,
                InstanceType.TPU_V3: 8.00,
                InstanceType.TPU_V4: 12.00
            }
            
            hourly_rate = hourly_rates.get(instance_type, 1.0)
            
            # Estimate total compute hours
            # Assume parallel execution until max_trials is reached
            total_compute_hours = max_trials * max_trial_duration_hours
            
            return total_compute_hours * hourly_rate
            
        except Exception as e:
            self.logger.error(f"Failed to estimate tuning cost: {str(e)}")
            return 100.0  # Default estimate
    
    async def _update_best_trial(self, tuning_job_id: UUID, db: AsyncSession):
        """Update the best trial for a tuning job."""
        try:
            result = await db.execute(
                select(HyperparameterTuningJob)
                .where(HyperparameterTuningJob.id == tuning_job_id)
            )
            tuning_job = result.scalar_one_or_none()
            
            if not tuning_job:
                return
            
            # Get completed trials with objective values
            result = await db.execute(
                select(HyperparameterTrial)
                .where(
                    and_(
                        HyperparameterTrial.tuning_job_id == tuning_job_id,
                        HyperparameterTrial.status == JobStatus.COMPLETED,
                        HyperparameterTrial.objective_value.isnot(None)
                    )
                )
            )
            completed_trials = result.scalars().all()
            
            if not completed_trials:
                return
            
            # Find best trial based on optimization objective
            if tuning_job.optimization_objective == OptimizationObjective.MAXIMIZE:
                best_trial = max(completed_trials, key=lambda t: t.objective_value)
            else:
                best_trial = min(completed_trials, key=lambda t: t.objective_value)
            
            # Update best trial info
            tuning_job.best_trial_id = best_trial.id
            tuning_job.best_hyperparameters = best_trial.hyperparameters
            tuning_job.best_objective_value = best_trial.objective_value
            
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to update best trial: {str(e)}")
    
    async def _check_tuning_completion(self, tuning_job_id: UUID, db: AsyncSession):
        """Check if tuning job should be marked as completed."""
        try:
            result = await db.execute(
                select(HyperparameterTuningJob)
                .options(selectinload(HyperparameterTuningJob.trials))
                .where(HyperparameterTuningJob.id == tuning_job_id)
            )
            tuning_job = result.scalar_one_or_none()
            
            if not tuning_job or tuning_job.status != JobStatus.RUNNING:
                return
            
            trials = tuning_job.trials
            completed_trials = [t for t in trials if t.status in [JobStatus.COMPLETED, JobStatus.FAILED]]
            running_trials = [t for t in trials if t.status == JobStatus.RUNNING]
            
            # Check completion conditions
            should_complete = False
            
            # All trials completed
            if len(completed_trials) >= tuning_job.max_trials:
                should_complete = True
            
            # No running trials and no more trials to start
            elif not running_trials and len(trials) >= tuning_job.max_trials:
                should_complete = True
            
            # Too many failed trials
            failed_trials = [t for t in trials if t.status == JobStatus.FAILED]
            if len(failed_trials) >= tuning_job.max_trials * 0.5:  # 50% failure rate
                should_complete = True
            
            if should_complete:
                tuning_job.status = JobStatus.COMPLETED
                tuning_job.end_time = datetime.utcnow()
                tuning_job.completed_trials = len([t for t in trials if t.status == JobStatus.COMPLETED])
                tuning_job.failed_trials = len(failed_trials)
                
                if tuning_job.start_time:
                    duration = tuning_job.end_time - tuning_job.start_time
                    tuning_job.duration_seconds = int(duration.total_seconds())
                
                await db.commit()
                
                self.logger.info(f"Completed hyperparameter tuning job {tuning_job_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to check tuning completion: {str(e)}")
    
    def _analyze_convergence(self, objective_values: List[float], 
                           optimization_objective: OptimizationObjective) -> Dict[str, Any]:
        """Analyze convergence of optimization process."""
        if not objective_values or len(objective_values) < 3:
            return {"converged": False, "reason": "Insufficient data"}
        
        # Calculate best values over time
        if optimization_objective == OptimizationObjective.MAXIMIZE:
            best_values = []
            current_best = float('-inf')
            for value in objective_values:
                current_best = max(current_best, value)
                best_values.append(current_best)
        else:
            best_values = []
            current_best = float('inf')
            for value in objective_values:
                current_best = min(current_best, value)
                best_values.append(current_best)
        
        # Check for convergence (no improvement in last 20% of trials)
        if len(best_values) >= 10:
            recent_window = max(5, len(best_values) // 5)
            recent_best = best_values[-recent_window:]
            
            if len(set(recent_best)) == 1:  # No improvement
                return {
                    "converged": True,
                    "reason": "No improvement in recent trials",
                    "stagnation_trials": recent_window
                }
        
        # Calculate improvement rate
        if len(best_values) >= 2:
            improvement = abs(best_values[-1] - best_values[0])
            relative_improvement = improvement / abs(best_values[0]) if best_values[0] != 0 else 0
            
            return {
                "converged": False,
                "improvement_rate": relative_improvement,
                "current_best": best_values[-1],
                "trials_analyzed": len(objective_values)
            }
        
        return {"converged": False, "reason": "Analysis incomplete"}
    
    def _estimate_completion_time(self, tuning_job: HyperparameterTuningJob, 
                                trials: List[HyperparameterTrial]) -> Optional[str]:
        """Estimate when tuning job will complete."""
        try:
            if tuning_job.status != JobStatus.RUNNING:
                return None
            
            completed_trials = [t for t in trials if t.status == JobStatus.COMPLETED]
            remaining_trials = tuning_job.max_trials - len(trials)
            
            if not completed_trials or remaining_trials <= 0:
                return None
            
            # Calculate average trial duration
            durations = []
            for trial in completed_trials:
                if trial.start_time and trial.end_time:
                    duration = trial.end_time - trial.start_time
                    durations.append(duration.total_seconds())
            
            if not durations:
                return None
            
            avg_duration_seconds = sum(durations) / len(durations)
            
            # Estimate remaining time considering parallel execution
            remaining_time_seconds = (remaining_trials / tuning_job.max_parallel_trials) * avg_duration_seconds
            
            estimated_completion = datetime.utcnow() + timedelta(seconds=remaining_time_seconds)
            return estimated_completion.isoformat()
            
        except Exception as e:
            self.logger.error(f"Failed to estimate completion time: {str(e)}")
            return None