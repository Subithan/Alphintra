import pytest
import pandas as pd
import numpy as np
from app.services.feature_engineer import FeatureEngineer

@pytest.fixture
def sample_data():
    """Provides a sample DataFrame for testing."""
    dates = pd.date_range(start='2023-01-01', periods=100)
    data = {
        'open': np.random.uniform(90, 110, size=100),
        'high': np.random.uniform(100, 120, size=100),
        'low': np.random.uniform(80, 100, size=100),
        'close': np.random.uniform(95, 115, size=100),
        'volume': np.random.randint(1000, 10000, size=100)
    }
    df = pd.DataFrame(data, index=dates)
    # Ensure high is always >= open and close, and low is <= open and close
    df['high'] = df[['high', 'open', 'close']].max(axis=1)
    df['low'] = df[['low', 'open', 'close']].min(axis=1)
    return df

@pytest.fixture
def sample_workflow():
    """Provides a sample workflow for testing."""
    return {
        "nodes": [
            {"id": "data-1", "type": "dataSource", "data": {"parameters": {"symbol": "BTCUSDT"}}},
            {"id": "sma-1", "type": "technicalIndicator", "data": {"parameters": {"indicator": "SMA", "period": 10, "source": "close"}}},
            {"id": "rsi-1", "type": "technicalIndicator", "data": {"parameters": {"indicator": "RSI", "period": 14, "source": "close"}}},
        ],
        "edges": []
    }

def test_feature_engineer_initialization(sample_workflow, sample_data):
    """Tests FeatureEngineer initialization."""
    fe = FeatureEngineer(sample_workflow, sample_data)
    assert fe.analyzer is not None
    assert fe.data.equals(sample_data)
    assert fe.features.equals(sample_data)

def test_extract_base_features(sample_workflow, sample_data):
    """Tests the extraction of base features (technical indicators)."""
    fe = FeatureEngineer(sample_workflow, sample_data)
    fe._extract_base_features()
    assert 'SMA_10_close' in fe.features.columns
    assert 'RSI_14_close' in fe.features.columns
    assert len(fe.features.columns) > len(sample_data.columns)

def test_generate_rolling_window_statistics(sample_workflow, sample_data):
    """Tests generation of rolling window statistics."""
    fe = FeatureEngineer(sample_workflow, sample_data)
    initial_cols = set(fe.features.columns)
    fe._generate_rolling_window_statistics()
    new_cols = set(fe.features.columns)
    assert len(new_cols) > len(initial_cols)
    assert 'close_rolling_mean_5' in fe.features.columns
    assert 'close_rolling_std_10' in fe.features.columns
    assert 'close_rolling_skew_20' in fe.features.columns
    assert 'close_rolling_kurt_20' in fe.features.columns

def test_generate_lag_features(sample_workflow, sample_data):
    """Tests generation of lag features."""
    fe = FeatureEngineer(sample_workflow, sample_data)
    initial_cols = set(fe.features.columns)
    fe._generate_lag_features()
    new_cols = set(fe.features.columns)
    assert len(new_cols) > len(initial_cols)
    assert 'close_lag_1' in fe.features.columns
    assert 'close_lag_3' in fe.features.columns

def test_generate_technical_indicator_combinations(sample_workflow, sample_data):
    """Tests generation of feature combinations."""
    fe = FeatureEngineer(sample_workflow, sample_data)
    fe._extract_base_features()
    initial_cols = set(fe.features.columns)
    fe._generate_technical_indicator_combinations()
    new_cols = set(fe.features.columns)
    assert len(new_cols) > len(initial_cols)
    # This checks if at least one combination was created. The exact name can be long.
    assert any('_div_' in col for col in new_cols)

def test_generate_features_pipeline(sample_workflow, sample_data):
    """Tests the full feature generation pipeline."""
    fe = FeatureEngineer(sample_workflow, sample_data)
    generated_df = fe.generate_features()
    assert isinstance(generated_df, pd.DataFrame)
    assert len(generated_df.columns) > len(sample_data.columns)
    # Check for no NaNs after pipeline
    assert not generated_df.isnull().values.any()

def test_select_features(sample_workflow, sample_data):
    """Tests the feature selection method."""
    fe = FeatureEngineer(sample_workflow, sample_data)
    fe.generate_features()

    n_select = 10
    selected_df = fe.select_features(n_features_to_select=n_select)
    assert isinstance(selected_df, pd.DataFrame)
    assert len(selected_df.columns) <= n_select
    assert set(selected_df.columns).issubset(set(fe.features.columns))

def test_select_features_with_small_data(sample_workflow):
    """Tests feature selection with a small dataset that might cause issues."""
    data = pd.DataFrame({
        'close': np.random.uniform(95, 115, size=20)
    })
    fe = FeatureEngineer(sample_workflow, data)
    fe.generate_features()

    n_select = 5
    selected_df = fe.select_features(n_features_to_select=n_select, target_horizon=1)
    assert isinstance(selected_df, pd.DataFrame)
    assert len(selected_df.columns) <= n_select
    assert not selected_df.empty

def test_select_features_empty_after_nan_drop(sample_workflow):
    """Tests that feature selection handles cases where all data is dropped."""
    data = pd.DataFrame({'close': [1, 2, 3]})
    fe = FeatureEngineer(sample_workflow, data)
    fe.generate_features()
    # This should result in an empty dataframe for selection as target horizon is too large
    selected_df = fe.select_features(target_horizon=5)
    assert selected_df.empty
