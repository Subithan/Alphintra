import pandas as pd
import numpy as np
import talib
from typing import Dict, Any, List
from itertools import combinations
from sklearn.feature_selection import mutual_info_classif
from app.utils.workflow_analyzer import WorkflowAnalyzer

class FeatureEngineer:
    """
    Generates and selects optimal features from workflow definitions.
    """

    def __init__(self, workflow: Dict[str, Any], data: pd.DataFrame):
        """
        Initializes the FeatureEngineer.

        :param workflow: The workflow definition.
        :param data: The input data as a pandas DataFrame, expecting columns like 'open', 'high', 'low', 'close', 'volume'.
        """
        self.analyzer = WorkflowAnalyzer(workflow)
        self.data = data
        self.features = self.data.copy()

    def generate_features(self) -> pd.DataFrame:
        """
        Runs the entire feature engineering pipeline.
        """
        self._extract_base_features()
        self._generate_rolling_window_statistics()
        self._generate_lag_features()
        self._generate_technical_indicator_combinations()

        # Clean up NaNs produced by rolling/lagging operations
        self.features.fillna(method='bfill', inplace=True)
        self.features.fillna(method='ffill', inplace=True)

        return self.features

    def _extract_base_features(self):
        """
        Calculates and adds technical indicators from the workflow to the features DataFrame.
        """
        indicators = self.analyzer.get_technical_indicators()
        for indicator_node in indicators:
            params = indicator_node.get('data', {}).get('parameters', {})
            indicator_type = params.get('indicator', 'SMA').upper()
            period = params.get('period', 20)
            source_column = params.get('source', 'close')

            if source_column not in self.data.columns:
                print(f"Warning: Source column '{source_column}' not in data. Skipping indicator.")
                continue

            feature_name = f"{indicator_type}_{period}_{source_column}"
            source_data = self.data[source_column]

            try:
                if indicator_type == 'SMA':
                    self.features[feature_name] = talib.SMA(source_data, timeperiod=period)
                elif indicator_type == 'EMA':
                    self.features[feature_name] = talib.EMA(source_data, timeperiod=period)
                elif indicator_type == 'RSI':
                    self.features[feature_name] = talib.RSI(source_data, timeperiod=period)
                elif indicator_type == 'MACD':
                    # MACD returns 3 values, we'll store them as separate features
                    macd, macdsignal, macdhist = talib.MACD(source_data, fastperiod=12, slowperiod=26, signalperiod=9)
                    self.features[f'{feature_name}_macd'] = macd
                    self.features[f'{feature_name}_signal'] = macdsignal
                    self.features[f'{feature_name}_hist'] = macdhist
                elif indicator_type == 'BBANDS':
                    upper, middle, lower = talib.BBANDS(source_data, timeperiod=period)
                    self.features[f'{feature_name}_upper'] = upper
                    self.features[f'{feature_name}_middle'] = middle
                    self.features[f'{feature_name}_lower'] = lower
            except Exception as e:
                print(f"Error calculating {indicator_type}: {e}")


    def _generate_technical_indicator_combinations(self):
        """
        Generates features by combining technical indicators.
        """
        indicator_features = [col for col in self.features.columns if any(ind in col for ind in ['SMA', 'EMA', 'RSI', 'MACD', 'BBANDS'])]

        for feat1, feat2 in combinations(indicator_features, 2):
            # To avoid feature explosion, only do division for now
            # and avoid division by zero
            if not self.features[feat2].eq(0).all():
                self.features[f'{feat1}_div_{feat2}'] = self.features[feat1] / (self.features[feat2] + 1e-9)

    def _generate_rolling_window_statistics(self):
        """
        Generates rolling window statistics for existing features.
        """
        features_to_roll = [col for col in self.features.columns if self.features[col].dtype in [np.float64, np.int64]]
        windows = [5, 10, 20]

        for feature in features_to_roll:
            for window in windows:
                if len(self.features[feature]) > window:
                    self.features[f'{feature}_rolling_mean_{window}'] = self.features[feature].rolling(window=window).mean()
                    self.features[f'{feature}_rolling_std_{window}'] = self.features[feature].rolling(window=window).std()
                    self.features[f'{feature}_rolling_skew_{window}'] = self.features[feature].rolling(window=window).skew()
                    self.features[f'{feature}_rolling_kurt_{window}'] = self.features[feature].rolling(window=window).kurt()


    def _generate_lag_features(self):
        """
        Generates lag features for existing features.
        """
        features_to_lag = list(self.features.columns)
        lags = [1, 2, 3, 5]

        for feature in features_to_lag:
            for lag in lags:
                self.features[f'{feature}_lag_{lag}'] = self.features[feature].shift(lag)

    def select_features(self, n_features_to_select: int = 20, target_horizon: int = 1) -> pd.DataFrame:
        """
        Selects the best features using mutual information.

        :param n_features_to_select: The number of top features to select.
        :param target_horizon: The prediction horizon for the target variable.
        :return: A DataFrame with the selected features.
        """
        # Define the target variable
        y = (self.features['close'].shift(-target_horizon) > self.features['close']).astype(int)

        # Align features and target
        X = self.features.copy()

        # Drop rows with NaN in target
        X = X.iloc[:-target_horizon]
        y = y.iloc[:-target_horizon]

        # Drop any remaining NaNs from features and align y
        X.dropna(inplace=True)
        y = y[X.index]

        if X.empty:
            print("Warning: Feature set is empty after cleaning NaNs. Skipping selection.")
            return pd.DataFrame()

        mi_scores = mutual_info_classif(X, y, random_state=42)
        mi_scores = pd.Series(mi_scores, name="MI Scores", index=X.columns)
        mi_scores = mi_scores.sort_values(ascending=False)

        # Select top N features
        selected_features = mi_scores.head(n_features_to_select).index.tolist()

        print(f"Selected features based on Mutual Information: {selected_features}")

        return self.features[selected_features]
