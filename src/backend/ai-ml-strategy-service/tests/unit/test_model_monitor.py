import pytest
import time
import pandas as pd
from collections import deque

from app.services.model_monitor import ModelMonitoringService, PredictionLog, ConceptDriftAlert
from app.models.model_registry import ModelDeployment

@pytest.fixture
def monitor():
    """Returns a new instance of ModelMonitoringService for each test."""
    return ModelMonitoringService()

@pytest.mark.asyncio
async def test_log_prediction(monitor: ModelMonitoringService):
    log = PredictionLog(
        deployment_id=1,
        request_id="req1",
        features={"f1": 1, "f2": 2},
        prediction=0.8
    )
    await monitor.log_prediction(log)

    assert 1 in monitor.prediction_logs
    assert len(monitor.prediction_logs[1]) == 1
    assert monitor.prediction_logs[1][0] == log
    assert "req1" in monitor.prediction_log_map
    assert monitor.prediction_log_map["req1"] == log

@pytest.mark.asyncio
async def test_log_prediction_deque_eviction(monitor: ModelMonitoringService):
    monitor.prediction_logs[1] = deque(maxlen=2)

    log1 = PredictionLog(deployment_id=1, request_id="req1", features={}, prediction=1)
    log2 = PredictionLog(deployment_id=1, request_id="req2", features={}, prediction=2)
    log3 = PredictionLog(deployment_id=1, request_id="req3", features={}, prediction=3)

    await monitor.log_prediction(log1)
    await monitor.log_prediction(log2)

    assert "req1" in monitor.prediction_log_map
    assert "req2" in monitor.prediction_log_map

    await monitor.log_prediction(log3)

    assert len(monitor.prediction_logs[1]) == 2
    assert monitor.prediction_logs[1][0] == log2
    assert monitor.prediction_logs[1][1] == log3
    assert "req1" not in monitor.prediction_log_map
    assert "req2" in monitor.prediction_log_map
    assert "req3" in monitor.prediction_log_map

@pytest.mark.asyncio
async def test_log_ground_truth(monitor: ModelMonitoringService):
    log = PredictionLog(deployment_id=1, request_id="req1", features={}, prediction=1)
    await monitor.log_prediction(log)

    await monitor.log_ground_truth(deployment_id=1, request_id="req1", ground_truth=1)

    assert monitor.prediction_logs[1][0].ground_truth == 1

@pytest.mark.asyncio
async def test_calculate_accuracy_metrics(monitor: ModelMonitoringService):
    # Log some predictions with ground truth
    for i in range(10):
        log = PredictionLog(deployment_id=1, request_id=f"req{i}", features={}, prediction=i % 2, ground_truth=i % 2)
        await monitor.log_prediction(log)

    # Add one incorrect prediction
    log = PredictionLog(deployment_id=1, request_id="req10", features={}, prediction=1, ground_truth=0)
    await monitor.log_prediction(log)

    metrics = await monitor.calculate_accuracy_metrics(deployment_id=1)

    assert metrics["accuracy"] == 10 / 11
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert metrics["samples_with_ground_truth"] == 11

@pytest.mark.asyncio
async def test_check_concept_drift(monitor: ModelMonitoringService):
    # Setup reference data with predictions
    ref_preds = pd.Series([0.1, 0.2, 0.15, 0.25, 0.18])
    monitor.reference_data[1] = pd.DataFrame({'prediction': ref_preds})

    # Current predictions with a different distribution
    current_preds = pd.Series([0.8, 0.9, 0.85, 0.95, 0.88])

    alert = await monitor.check_concept_drift(1, current_preds)

    assert isinstance(alert, ConceptDriftAlert)
    assert alert.p_value < 0.05

@pytest.mark.asyncio
async def test_check_concept_drift_no_drift(monitor: ModelMonitoringService):
    # Setup reference data with predictions
    ref_preds = pd.Series([0.1, 0.2, 0.15, 0.25, 0.18])
    monitor.reference_data[1] = pd.DataFrame({'prediction': ref_preds})

    # Current predictions with a similar distribution
    current_preds = pd.Series([0.12, 0.21, 0.16, 0.26, 0.19])

    alert = await monitor.check_concept_drift(1, current_preds)

    assert alert is None

# Note: Testing the remediation logic would require a more complex setup
# with a mocked database. This is a good candidate for an integration test.
# For now, we've covered the core logic of the monitoring service.
