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
            "data": {"sourceHandle": "data-output", "targetHandle": "data-input"},
        },
        {
            "id": "edge-2",
            "source": "sma-1",
            "target": "cond-1",
            "sourceHandle": "output-1",
            "targetHandle": "data-input",
            "data": {"sourceHandle": "output-1", "targetHandle": "data-input"},
        },
        {
            "id": "edge-3",
            "source": "cond-1",
            "target": "action-1",
            "sourceHandle": "signal-output",
            "targetHandle": "signal-input",
            "data": {"sourceHandle": "signal-output", "targetHandle": "signal-input"},
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


def _compile_and_run(nodes, edges):
    compiler = WorkflowCompiler()
    result = asyncio.run(compiler.compile_workflow(nodes, edges, strategy_name="Advanced Node Test"))
    assert result["success"], result.get("errors")

    module = types.ModuleType("advanced_strategy")
    exec(result["code"], module.__dict__)

    df = module.run_strategy()
    return df, result


def test_market_regime_detection_integration():
    nodes = [
        {
            "id": "source-1",
            "type": "dataSource",
            "data": {"parameters": {"symbol": "TEST", "timeframe": "1h", "bars": 50}},
        },
        {
            "id": "regime-1",
            "type": "marketRegimeDetection",
            "data": {"parameters": {"trendWindow": 10, "volatilityWindow": 5}},
        },
        {
            "id": "action-1",
            "type": "action",
            "data": {"parameters": {"action": "buy", "quantity": 1}},
        },
    ]

    edges = [
        {
            "id": "edge-1",
            "source": "source-1",
            "target": "regime-1",
            "sourceHandle": "data-output",
            "targetHandle": "data-input",
            "data": {"sourceHandle": "data-output", "targetHandle": "data-input"},
        },
        {
            "id": "edge-2",
            "source": "regime-1",
            "target": "action-1",
            "sourceHandle": "trend-output",
            "targetHandle": "signal-input",
            "data": {"sourceHandle": "trend-output", "targetHandle": "signal-input"},
        },
    ]

    df, result = _compile_and_run(nodes, edges)
    trend_col = "regime_regime_1_trend"
    volatile_col = "regime_regime_1_volatile"
    assert trend_col in df.columns
    assert volatile_col in df.columns
    assert df[trend_col].dtype == bool
    assert not result["errors"]


def test_multi_timeframe_analysis_integration():
    nodes = [
        {
            "id": "source-1",
            "type": "dataSource",
            "data": {"parameters": {"symbol": "TEST", "timeframe": "1h", "bars": 120}},
        },
        {
            "id": "mtf-1",
            "type": "multiTimeframeAnalysis",
            "data": {"parameters": {"timeframes": ["4H", "1D"]}},
        },
        {
            "id": "sma-1",
            "type": "technicalIndicator",
            "data": {"parameters": {"indicator": "SMA", "period": 5, "source": "close"}},
        },
        {
            "id": "cond-1",
            "type": "condition",
            "data": {"parameters": {"condition": "greater_than", "value": 0}},
        },
        {
            "id": "action-1",
            "type": "action",
            "data": {"parameters": {"action": "buy", "quantity": 1}},
        },
    ]

    edges = [
        {
            "id": "edge-1",
            "source": "source-1",
            "target": "mtf-1",
            "sourceHandle": "data-output",
            "targetHandle": "data-input",
            "data": {"sourceHandle": "data-output", "targetHandle": "data-input"},
        },
        {
            "id": "edge-2",
            "source": "mtf-1",
            "target": "sma-1",
            "sourceHandle": "output",
            "targetHandle": "data-input",
            "data": {"sourceHandle": "output", "targetHandle": "data-input"},
        },
        {
            "id": "edge-3",
            "source": "sma-1",
            "target": "cond-1",
            "sourceHandle": "output-1",
            "targetHandle": "data-input",
            "data": {"sourceHandle": "output-1", "targetHandle": "data-input"},
        },
        {
            "id": "edge-4",
            "source": "cond-1",
            "target": "action-1",
            "sourceHandle": "signal-output",
            "targetHandle": "signal-input",
            "data": {"sourceHandle": "signal-output", "targetHandle": "signal-input"},
        },
    ]

    df, _ = _compile_and_run(nodes, edges)
    multi_col = "mtf_mtf_1_close_4H"
    assert multi_col in df.columns


def test_correlation_analysis_integration():
    nodes = [
        {
            "id": "source-1",
            "type": "dataSource",
            "data": {"parameters": {"symbol": "ASSET1", "timeframe": "1h", "bars": 200}},
        },
        {
            "id": "corr-1",
            "type": "correlationAnalysis",
            "data": {"parameters": {"window": 20}},
        },
        {
            "id": "cond-1",
            "type": "condition",
            "data": {"parameters": {"condition": "greater_than", "value": 0.0}},
        },
        {
            "id": "action-1",
            "type": "action",
            "data": {"parameters": {"action": "buy", "quantity": 1}},
        },
    ]

    edges = [
        {
            "id": "edge-1",
            "source": "source-1",
            "target": "corr-1",
            "sourceHandle": "data-output",
            "targetHandle": "data-input-1",
            "data": {"sourceHandle": "data-output", "targetHandle": "data-input-1"},
        },
        {
            "id": "edge-2",
            "source": "source-1",
            "target": "corr-1",
            "sourceHandle": "data-output",
            "targetHandle": "data-input-2",
            "data": {"sourceHandle": "data-output", "targetHandle": "data-input-2"},
        },
        {
            "id": "edge-3",
            "source": "corr-1",
            "target": "cond-1",
            "sourceHandle": "output",
            "targetHandle": "data-input",
            "data": {"sourceHandle": "output", "targetHandle": "data-input"},
        },
        {
            "id": "edge-4",
            "source": "cond-1",
            "target": "action-1",
            "sourceHandle": "signal-output",
            "targetHandle": "signal-input",
            "data": {"sourceHandle": "signal-output", "targetHandle": "signal-input"},
        },
    ]

    df, _ = _compile_and_run(nodes, edges)
    corr_col = "correlation_corr_1"
    assert corr_col in df.columns
    assert df[corr_col].isna().sum() == 0


def test_sentiment_analysis_integration():
    nodes = [
        {
            "id": "source-1",
            "type": "dataSource",
            "data": {"parameters": {"symbol": "TEST", "timeframe": "1h", "bars": 90}},
        },
        {
            "id": "sent-1",
            "type": "sentimentAnalysis",
            "data": {"parameters": {"smoothing": 5, "threshold": 0.02}},
        },
        {
            "id": "action-1",
            "type": "action",
            "data": {"parameters": {"action": "buy", "quantity": 1}},
        },
    ]

    edges = [
        {
            "id": "edge-1",
            "source": "source-1",
            "target": "sent-1",
            "sourceHandle": "data-output",
            "targetHandle": "data-input",
            "data": {"sourceHandle": "data-output", "targetHandle": "data-input"},
        },
        {
            "id": "edge-2",
            "source": "sent-1",
            "target": "action-1",
            "sourceHandle": "positive-output",
            "targetHandle": "signal-input",
            "data": {"sourceHandle": "positive-output", "targetHandle": "signal-input"},
        },
    ]

    df, _ = _compile_and_run(nodes, edges)
    pos_col = "sentiment_sent_1_positive"
    neu_col = "sentiment_sent_1_neutral"
    assert pos_col in df.columns
    assert neu_col in df.columns
    assert set(df[pos_col].unique()).issubset({True, False})

