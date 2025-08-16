import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
import pandas as pd

from app.services.model_training_service import ModelTrainingService
from app.models.training import TrainingJob, JobStatus

@pytest.fixture
def sample_training_job():
    """Fixture for a sample training job."""
    job_id = uuid4()
    return TrainingJob(
        id=job_id,
        user_id=uuid4(),
        strategy_id=uuid4(),
        dataset_id=uuid4(),
        job_name="Test XGBoost Training",
        job_type="TRAINING",
        instance_type="CPU_MEDIUM",
        model_config={
            "model_name": "xgboost",
            "search_space": {
                "n_estimators": {"type": "int", "low": 100, "high": 200},
                "max_depth": {"type": "int", "low": 3, "high": 10},
            },
            "cv_folds": 3,
        },
        training_config={"n_trials": 5},
        status=JobStatus.PENDING,
    )

@pytest.mark.asyncio
async def test_run_training_successful(sample_training_job):
    """Test the successful run of a training job."""

    # Mock the database session and job retrieval
    mock_db_session = AsyncMock()
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_training_job

    # Mock optuna
    mock_trial = MagicMock()
    mock_trial.suggest_int.side_effect = [150, 5] # n_estimators, max_depth
    mock_trial.value = 0.85 # The score to be returned by the objective

    mock_study = MagicMock()
    mock_study.best_trial = mock_trial
    mock_study.optimize = Mock()

    # Mock model
    mock_model_instance = MagicMock()
    mock_model_instance.train = Mock()
    mock_model_instance.save = Mock()

    with patch("app.services.model_training_service.get_session", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db_session), __aexit__=AsyncMock())):
        with patch("app.services.model_training_service.optuna.create_study", return_value=mock_study) as mock_create_study:
            with patch("app.services.model_training_service.XGBoostModel", return_value=mock_model_instance) as mock_model_class:
                # We need to mock cross_val_score as well
                with patch("app.services.model_training_service.cross_val_score", return_value=MagicMock(mean=lambda: 0.85)):

                    service = ModelTrainingService(job_id=sample_training_job.id)
                    await service.run_training()

                    # --- Assertions ---

                    # Assert job status was updated
                    assert sample_training_job.status == JobStatus.COMPLETED

                    # Assert Optuna study was created and optimized
                    mock_create_study.assert_called_once()
                    mock_study.optimize.assert_called_once()

                    # Assert model was trained and saved
                    mock_model_instance.train.assert_called_once()
                    mock_model_instance.save.assert_called_once()

                    # Assert final metrics are updated
                    assert "best_score" in sample_training_job.final_metrics
                    assert sample_training_job.final_metrics["best_score"] == 0.85
