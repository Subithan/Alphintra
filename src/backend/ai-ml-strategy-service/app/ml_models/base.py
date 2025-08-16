from abc import ABC, abstractmethod
import pandas as pd
from typing import Any, Dict

class BaseModel(ABC):
    """
    Abstract base class for all machine learning models.
    """

    def __init__(self, model_config: Dict[str, Any]):
        self.model_config = model_config
        self._model = None

    @abstractmethod
    def train(self, X_train: pd.DataFrame, y_train: pd.DataFrame, **kwargs) -> None:
        """
        Train the model on the given data.

        Args:
            X_train: Training data features.
            y_train: Training data labels.
            **kwargs: Additional arguments for training.
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Make predictions on the given data.

        Args:
            X: Data to make predictions on.

        Returns:
            A DataFrame with the predictions.
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """
        Save the trained model to the given path.

        Args:
            path: Path to save the model to.
        """
        pass

    @abstractmethod
    def load(self, path: str) -> Any:
        """
        Load a trained model from the given path.

        Args:
            path: Path to load the model from.

        Returns:
            The loaded model.
        """
        pass
