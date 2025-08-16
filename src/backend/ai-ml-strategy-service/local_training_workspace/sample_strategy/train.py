
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib
import argparse
import os
import time

def train(args):
    """
    A realistic training script that loads market data, trains a simple model,
    and saves the model artifact.
    """
    print("--- Local Training Simulation ---")
    print(f"Job ID: {args.job_id}")
    print(f"Strategy ID: {args.strategy_id}")
    print(f"Dataset ID: {args.dataset_id}")
    print("---------------------------------")

    # Load data
    print("Loading market data from market_data.csv...")
    try:
        data = pd.read_csv('market_data.csv')
        print("Data loaded successfully.")
    except FileNotFoundError:
        print("Error: market_data.csv not found. Make sure it's in the same directory as train.py.")
        return

    # Feature Engineering
    print("Performing feature engineering...")
    data['Date'] = pd.to_datetime(data['Date'])
    data['dayofyear'] = data['Date'].dt.dayofyear
    data['lag_close'] = data['Close'].shift(1)
    data = data.dropna()
    print("Feature engineering complete.")

    # Prepare data for training
    X = data[['dayofyear', 'lag_close']]
    y = data['Close']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the model
    print("Training Linear Regression model...")
    model = LinearRegression()
    for epoch in range(5):
        print(f"Epoch {epoch+1}/5...")
        model.fit(X_train, y_train)
        time.sleep(1) # Simulate training time
    
    print("Model training complete.")

    # Evaluate the model
    score = model.score(X_test, y_test)
    print(f"Model R^2 score: {score:.4f}")

    # Save the model artifact
    # In a real Vertex AI job, this path would be a GCS bucket.
    # We simulate it with a local directory.
    model_dir = os.getenv("AIP_MODEL_DIR", "/tmp/models")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, f"{args.job_id}_model.pkl")
    
    print(f"Saving model to {model_path}...")
    joblib.dump(model, model_path)
    print("Model saved successfully.")
    print("--- Training Finished ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--strategy-id", required=True)
    parser.add_argument("--dataset-id", required=True)
    # In a real scenario, you might have more arguments for hyperparameters, etc.
    args = parser.parse_args()
    train(args)
