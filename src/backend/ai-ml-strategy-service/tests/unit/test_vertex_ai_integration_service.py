import pytest
from types import SimpleNamespace
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from app.models.training import (
    TrainingJob,
    JobType,
    JobStatus,
    InstanceType,
    TrainingPriority,
)
from app.services.vertex_ai_integration import VertexAIIntegrationService


@pytest.fixture
def mock_settings(monkeypatch):
    settings = SimpleNamespace(
        TRAINING_ORCHESTRATOR_URL="https://orchestrator.example.com",
        TRAINING_JOB_QUEUE_TOPIC=None,
        TRAINING_ORCHESTRATOR_TOKEN="unit-test-token",
        TRAINING_ORCHESTRATOR_TIMEOUT=5.0,
        TRAINING_CALLBACK_BASE_URL="https://api.example.com",
    )
    monkeypatch.setattr("app.services.vertex_ai_integration.get_settings", lambda: settings)
    return settings


@pytest.fixture
def dummy_async_client(monkeypatch):
    call_state = {}

    class DummyResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self._data

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            call_state["init_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json=None, headers=None):
            call_state.setdefault("posts", []).append({
                "url": url,
                "json": json,
                "headers": headers,
            })
            if url.endswith("/jobs"):
                return DummyResponse({"job_id": "backend-job-123", "state": "JOB_STATE_QUEUED"})
            raise AssertionError(f"Unexpected POST URL: {url}")

        async def get(self, url, params=None, headers=None):
            raise AssertionError("GET should not be called in this test")

    monkeypatch.setattr("app.services.vertex_ai_integration.httpx.AsyncClient", DummyAsyncClient)
    return call_state


@pytest.mark.asyncio
async def test_submit_training_job_dispatches_to_backend(mock_settings, dummy_async_client):
    service = VertexAIIntegrationService()

    job = TrainingJob(
        id=uuid4(),
        user_id=uuid4(),
        strategy_id=uuid4(),
        dataset_id=uuid4(),
        job_name="unit-test",
        job_type=JobType.TRAINING,
        instance_type=InstanceType.CPU_SMALL,
        machine_type="n1-standard-4",
        disk_size=50,
        timeout_hours=3,
        priority=TrainingPriority.NORMAL,
        hyperparameters={"learning_rate": 0.1},
        training_config={"epochs": 5},
        model_config={"model_name": "xgboost"},
        status=JobStatus.PENDING,
    )

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    result = await service.submit_training_job(job, "gs://datasets/sample.csv", mock_db)

    assert result["success"] is True
    assert job.vertex_ai_job_id == "backend-job-123"
    assert job.status == JobStatus.QUEUED
    assert mock_db.commit.await_count >= 1

    payload = dummy_async_client["posts"][0]["json"]
    assert payload["dataset"]["path"] == "gs://datasets/sample.csv"
    assert payload["callbacks"]["progress"].endswith(f"/api/training/jobs/{job.id}/progress")
    assert payload["training"]["command"] == ["python", "train.py"]


@pytest.mark.asyncio
async def test_sync_job_status_updates_job_state(monkeypatch, mock_settings):
    service = VertexAIIntegrationService()

    job = TrainingJob(
        id=uuid4(),
        user_id=uuid4(),
        strategy_id=uuid4(),
        dataset_id=uuid4(),
        job_name="status-test",
        job_type=JobType.TRAINING,
        instance_type=InstanceType.CPU_SMALL,
        priority=TrainingPriority.NORMAL,
        status=JobStatus.RUNNING,
        vertex_ai_job_id="backend-job-456",
        start_time=datetime.utcnow() - timedelta(minutes=5),
    )

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    status_payload = {
        "state": "JOB_STATE_SUCCEEDED",
        "end_time": datetime.utcnow().isoformat() + "Z",
    }
    monkeypatch.setattr(
        service.vertex_client,
        "fetch_job_status",
        AsyncMock(return_value=status_payload),
    )

    result = await service.sync_job_status(job, mock_db)

    assert result["success"] is True
    assert result["job_status"] == JobStatus.COMPLETED.value
    assert job.status == JobStatus.COMPLETED
    assert mock_db.commit.await_count == 1
*** End of File
