import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add path to label_generation module
MODULE_PATH = Path(__file__).resolve().parent / 'src' / 'ai-ml' / 'feature-engineering'
sys.path.append(str(MODULE_PATH))

from label_generation import construct_labels


def test_construct_labels_classification():
    df = pd.DataFrame({
        'close': [100, 102, 101, 103],
        'signal': [1, -1, 0, 1]
    })
    y = construct_labels(df, task='classification', horizon=1)
    assert y.iloc[0] == 1
    assert y.iloc[1] == 1
    assert y.iloc[2] == 0
    assert np.isnan(y.iloc[3])


def test_construct_labels_regression():
    df = pd.DataFrame({
        'close': [100, 102, 101, 103],
        'signal': [1, -1, 0, 1]
    })
    y = construct_labels(df, task='regression', horizon=1)
    expected = [0.02, 0.00980392156862745, 0.0, np.nan]
    np.testing.assert_almost_equal(y.values[:-1], expected[:-1])
    assert np.isnan(y.values[-1])
