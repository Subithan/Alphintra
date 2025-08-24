import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.models.dataset import Dataset

@pytest.fixture
def sample_workflow():
    """Provides a sample workflow for testing."""
    return {
        "nodes": [
            {"id": "data-1", "type": "dataSource", "data": {"parameters": {"symbol": "TEST"}}},
            {"id": "sma-1", "type": "technicalIndicator", "data": {"parameters": {"indicator": "SMA", "period": 10, "source": "close"}}},
        ],
        "edges": []
    }

@pytest.fixture
def sample_data():
    """Provides a sample DataFrame for testing."""
    dates = pd.date_range(start='2023-01-01', periods=100)
    return pd.DataFrame({
        'close': np.random.uniform(95, 115, size=100)
    }, index=dates)

def test_run_feature_engineering_success(client: TestClient, sample_workflow, sample_data):
    """
    Tests the feature engineering endpoint with a successful scenario.
    """
    with patch('app.api.endpoints.feature_engineering.get_dataset_by_id') as mock_get_dataset, \
         patch('app.services.storage_manager.StorageManager.retrieve_dataset') as mock_retrieve_dataset:

        # Setup mocks
        mock_dataset = Dataset(id="a1b2c3d4-e5f6-7890-1234-567890abcdef", file_path="/fake/path")
        mock_get_dataset.return_value = mock_dataset
        mock_retrieve_dataset.return_value = sample_data

        # Prepare request payload
        payload = {
            "workflow_definition": sample_workflow,
            "dataset_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "n_features_to_select": 5
        }

        # Make API call
        response = client.post("/feature-engineering/", json=payload)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "selected_features" in data
        assert "generated_features_count" in data
        assert "dataset_id" in data
        assert len(data["selected_features"]) <= 5
        assert data["generated_features_count"] > 1 # close + generated features
        assert data["dataset_id"] == "a1b2c3d4-e5f6-7890-1234-567890abcdef"

        mock_get_dataset.assert_called_once()
        mock_retrieve_dataset.assert_called_once()


def test_run_feature_engineering_dataset_not_found(client: TestClient, sample_workflow):
    """
    Tests the case where the dataset ID is not found.
    """
    with patch('app.api.endpoints.feature_engineering.get_dataset_by_id') as mock_get_dataset:
        # Setup mock to simulate dataset not found by raising a 404 HTTPException
        mock_get_dataset.side_effect = HTTPException(status_code=404, detail="Dataset not found")

        # Prepare request payload
        payload = {
            "workflow_definition": sample_workflow,
            "dataset_id": "fake-id",
            "n_features_to_select": 5
        }

        # Make API call
        response = client.post("/feature-engineering/", json=payload)

        # Assertions
        assert response.status_code == 404
        assert "Dataset not found" in response.json()["detail"]


def test_run_feature_engineering_data_retrieval_fails(client: TestClient, sample_workflow):
    """
    Tests the case where retrieving data from storage fails.
    """
    with patch('app.api.endpoints.feature_engineering.get_dataset_by_id') as mock_get_dataset, \
         patch('app.services.storage_manager.StorageManager.retrieve_dataset') as mock_retrieve_dataset:

        # Setup mocks
        mock_dataset = Dataset(id="a1b2c3d4-e5f6-7890-1234-567890abcdef", file_path="/fake/path")
        mock_get_dataset.return_value = mock_dataset
        mock_retrieve_dataset.return_value = None  # Simulate failure

        # Prepare request payload
        payload = {
            "workflow_definition": sample_workflow,
            "dataset_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "n_features_to_select": 5
        }

        # Make API call
        response = client.post("/feature-engineering/", json=payload)

        # Assertions
        assert response.status_code == 500
        assert "Failed to retrieve dataset data" in response.json()["detail"]
