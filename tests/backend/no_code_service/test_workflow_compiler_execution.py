"""Integration tests for the workflow compiler execution path."""

from __future__ import annotations

import asyncio
import types

import pytest

pd = pytest.importorskip("pandas")

from workflow_compiler_updated import WorkflowCompiler


def _build_simple_workflow():
    nodes = [
        {
            "id": "source-1",
            "type": "dataSource",
            "data": {
                "label": "Sample Data",
                "parameters": {
                    "symbol": "TEST",
                    "timeframe": "1d",
                    "bars": 5,
                },
            },
        },
        {
            "id": "sma-1",
            "type": "technicalIndicator",
            "data": {
                "label": "SMA",
                "parameters": {
                    "indicator": "SMA",
                    "period": 3,
                    "source": "close",
                },
            },
        },
        {
            "id": "cond-1",
            "type": "condition",
            "data": {
                "label": "SMA above threshold",
                "parameters": {
                    "condition": "greater_than",
                    "value": 103,
                },
            },
        },
        {
            "id": "action-1",
            "type": "action",
            "data": {
                "label": "Enter position",
                "parameters": {
                    "action": "buy",
                    "quantity": 10,
                    "take_profit": 5,
                    "stop_loss": 2,
                },
            },
        },
    ]

    edges = [
        {
            "id": "edge-1",
            "source": "source-1",
            "target": "sma-1",
            "sourceHandle": "data-output",
            "targetHandle": "data-input",
        },
        {
            "id": "edge-2",
            "source": "sma-1",
            "target": "cond-1",
            "sourceHandle": "output-1",
            "targetHandle": "data-input",
        },
        {
            "id": "edge-3",
            "source": "cond-1",
            "target": "action-1",
            "sourceHandle": "signal-output",
            "targetHandle": "signal-input",
        },
    ]

    return nodes, edges


def test_compiled_strategy_computes_expected_columns():
    compiler = WorkflowCompiler()
    nodes, edges = _build_simple_workflow()

    result = asyncio.run(
        compiler.compile_workflow(nodes, edges, strategy_name="Unit Test Strategy")
    )

    assert result["success"], result.get("errors")

    module = types.ModuleType("generated_strategy")
    exec(result["code"], module.__dict__)

    prices = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [101.0, 102.0, 103.0, 104.0, 105.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "close": [100.0, 102.0, 104.0, 106.0, 108.0],
            "volume": [1_000, 1_200, 1_300, 1_400, 1_500],
        },
        index=pd.date_range("2023-01-01", periods=5, freq="D"),
    )

    df = module.compute_indicators(prices.copy())
    indicator_col = "indicator_sma_1"
    expected_indicator = prices["close"].rolling(window=3, min_periods=1).mean()
    pd.testing.assert_series_equal(
        df[indicator_col], expected_indicator, check_names=False
    )

    df = module.evaluate_conditions(df)
    signal_col = "signal_cond_1"
    expected_signal = (expected_indicator > 103).fillna(False)
    pd.testing.assert_series_equal(
        df[signal_col], expected_signal.astype(bool), check_names=False
    )

    df = module.combine_logic(df)
    df = module.apply_risk_controls(df)
    df = module.generate_trading_decisions(df)

    decision_col = "decision_action_1"
    expected_decisions = ["HOLD", "HOLD", "HOLD", "BUY", "BUY"]
    assert list(df[decision_col]) == expected_decisions

