"""Label generation utilities for trading models.

This module constructs target values (y) for machine learning models
based on ActionNode trading signals and subsequent price movements.
It supports both classification and regression semantics.
"""

from __future__ import annotations

from typing import Literal
import numpy as np
import pandas as pd

TaskType = Literal["classification", "regression"]


def construct_labels(
    data: pd.DataFrame,
    price_col: str = "close",
    signal_col: str = "signal",
    horizon: int = 1,
    task: TaskType = "classification",
    threshold: float = 0.0,
) -> pd.Series:
    """Construct target labels based on trading signals and future prices.

    Parameters
    ----------
    data : pd.DataFrame
        Input data containing price information and ActionNode signals.
    price_col : str, default "close"
        Column name for current asset price.
    signal_col : str, default "signal"
        Column name for ActionNode signals. Signals can be integers
        (1 for buy, -1 for sell, 0 for hold) or strings ("buy", "sell", "hold").
    horizon : int, default 1
        Number of periods ahead to look when computing future price change.
    task : {"classification", "regression"}, default "classification"
        Type of label to generate.
        - ``"classification"`` returns 1 when the price moves in the direction
          of the signal by more than ``threshold`` and 0 otherwise.
        - ``"regression"`` returns the realized return scaled by the signal.
    threshold : float, default 0.0
        Minimum absolute return required to consider a move significant in
        classification mode.

    Returns
    -------
    pd.Series
        Series of target values aligned with ``data`` index. The final
        ``horizon`` rows will be NaN because future prices are unknown.
    """

    if price_col not in data or signal_col not in data:
        raise KeyError(f"Data must contain '{price_col}' and '{signal_col}' columns")

    price = data[price_col]
    future_price = price.shift(-horizon)
    future_return = (future_price - price) / price

    signal = data[signal_col]
    if signal.dtype == object:
        mapping = {"buy": 1, "sell": -1, "hold": 0, "": 0, None: 0}
        signal = signal.astype(str).str.lower().map(mapping)
    signal = signal.fillna(0)

    action_return = future_return * signal

    if task == "regression":
        y = action_return
    elif task == "classification":
        y = np.where(
            np.isnan(action_return),
            np.nan,
            np.where(action_return > threshold, 1, 0),
        )
        y = pd.Series(y, index=data.index)
    else:
        raise ValueError("task must be 'classification' or 'regression'")

    return pd.Series(y, index=data.index, name="y")
