import pandas as pd
from typing import Any, Dict
import os

from .base import BaseModel

class XGBoostModel(BaseModel):
    """
    XGBoost model implementation.
    """

    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        # We don't instantiate the model here anymore, to avoid the import.
        # The model will be instantiated on demand in train() or load().

    def _get_model(self):
        import xgboost as xgb
        if self._model is None:
            model_type = self.model_config.get("model_type", "classifier")
            xgb_params = self.model_config.get("xgb_params", {})
            if model_type == "classifier":
                self._model = xgb.XGBClassifier(**xgb_params)
            elif model_type == "regressor":
                self._model = xgb.XGBRegressor(**xgb_params)
            else:
                raise ValueError(f"Unsupported model_type: {model_type}")
        return self._model

    def train(self, X_train: pd.DataFrame, y_train: pd.DataFrame, **kwargs) -> None:
        model = self._get_model()
        model.fit(X_train, y_train, **kwargs)

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        model = self._get_model()
        predictions = model.predict(X)
        return pd.DataFrame(predictions, index=X.index, columns=['prediction'])

    def save(self, path: str) -> None:
        model = self._get_model()
        os.makedirs(path, exist_ok=True)
        model_path = os.path.join(path, 'model.xgb')
        model.save_model(model_path)

    def load(self, path: str) -> Any:
        import xgboost as xgb
        model_path = os.path.join(path, 'model.xgb')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")

        # Instantiate a new model object before loading state
        model_type = self.model_config.get("model_type", "classifier")
        xgb_params = self.model_config.get("xgb_params", {})
        if model_type == "classifier":
            self._model = xgb.XGBClassifier(**xgb_params)
        elif model_type == "regressor":
            self._model = xgb.XGBRegressor(**xgb_params)

        self._model.load_model(model_path)
        return self._model
