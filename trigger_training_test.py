import requests
import json
import os
import time

# Give the service time to start
time.sleep(15)

# --- Create Strategy ---
strategy_data = {
  "name": "Dummy Strategy for Local Training",
  "description": "A dummy strategy to trigger local training.",
  "code": "print('This is a dummy strategy.')",
  "parameters": {},
  "tags": ["test"]
}
try:
    # NOTE: This is an unauthenticated request. In a real environment, you would need a valid JWT token.
    response = requests.post("http://localhost:8002/api/strategies", json=strategy_data, headers={"Authorization": "Bearer test-token"})
    response.raise_for_status()
    strategy_id = response.json()["strategy_id"]
    print(f"Created strategy with ID: {strategy_id}")
except requests.exceptions.RequestException as e:
    print(f"Error creating strategy: {e}")
    exit(1)

# --- Create Dataset ---
# Create a dummy CSV file
dummy_csv_path = "/tmp/dummy_dataset.csv"
with open(dummy_csv_path, "w") as f:
    f.write("feature1,feature2,target\n")
    f.write("1,101,0\n")
    f.write("2,102,1\n")

dataset_metadata = {
  "name": "Dummy Dataset for Local Training",
  "description": "A dummy dataset.",
  "asset_class": "stocks",
  "symbols": ["DUMMY"],
  "frequency": "1d",
  "tags": ["test"]
}
try:
    with open(dummy_csv_path, "rb") as f:
        files = {"file": ("dummy_dataset.csv", f, "text/csv")}
        response = requests.post(
            "http://localhost:8002/api/datasets/upload",
            files=files,
            data={"metadata": json.dumps(dataset_metadata)},
            headers={"Authorization": "Bearer test-token"}
        )
        response.raise_for_status()
        dataset_id = response.json()["dataset_id"]
        print(f"Created dataset with ID: {dataset_id}")
except requests.exceptions.RequestException as e:
    print(f"Error creating dataset: {e}")
    exit(1)
finally:
    if os.path.exists(dummy_csv_path):
        os.remove(dummy_csv_path)

# --- Create Training Job ---
training_data = {
  "strategy_id": strategy_id,
  "dataset_id": dataset_id,
  "job_name": "Test Automated Training",
  "job_type": "training",
  "instance_type": "CPU_MEDIUM",
  "hyperparameters": {
    "n_estimators": 10,
    "max_depth": 5
  },
  "training_config": {}
}
try:
    response = requests.post("http://localhost:8002/api/training/jobs", json=training_data, headers={"Authorization": "Bearer test-token"})
    response.raise_for_status()
    print("Training job created successfully:")
    print(response.json())
except requests.exceptions.RequestException as e:
    print(f"Error creating training job: {e}")
    exit(1)
