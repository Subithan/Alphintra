import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

# Load dataset
# In a real scenario, this would be loaded from a specified path
# For this test, we'll create a dummy dataset
data = {
    'feature1': range(100),
    'feature2': range(100, 200),
    'target': [0, 1] * 50
}
df = pd.DataFrame(data)

X = df[['feature1', 'feature2']]
y = df['target']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=10, random_state=42)
print("Training model...")
model.fit(X_train, y_train)
print("Model training complete.")

# Evaluate model
preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)
print(f"Model accuracy: {acc}")

# Save model
output_dir = os.environ.get("AIP_MODEL_DIR", "/tmp/models")
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

model_path = os.path.join(output_dir, "model.joblib")
joblib.dump(model, model_path)
print(f"Model saved to {model_path}")
