"""Unit tests for enhanced Phase 2 node handlers."""

from __future__ import annotations

import sys
from typing import Dict, List, Tuple

import pytest

from tests.backend.no_code_service import SERVICE_ROOT

if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from ir import Node  # noqa: E402

from node_handlers.action import ActionHandler  # noqa: E402
from node_handlers.condition import ConditionHandler  # noqa: E402
from node_handlers.custom_dataset import CustomDatasetHandler  # noqa: E402
from node_handlers.data_source import DataSourceHandler  # noqa: E402
from node_handlers.logic import LogicHandler  # noqa: E402
from node_handlers.risk import RiskHandler  # noqa: E402
from node_handlers.technical_indicator import TechnicalIndicatorHandler  # noqa: E402


class StubGenerator:
    """Minimal generator stub exposing get_incoming."""

    def __init__(self, edges: Dict[str, List[Tuple[str, str, str]]]):
        self.edges = edges

    def get_incoming(self, node_id: str) -> List[Tuple[str, str, str]]:
        return self.edges.get(node_id, [])


def test_data_source_handler_includes_normalisation():
    handler = DataSourceHandler()
    node = Node(
        id="data-1",
        type="dataSource",
        data={
            "parameters": {
                "symbol": "BTC-USD",
                "timeframe": "4h",
                "missingStrategy": "drop",
                "timezone": "US/Eastern",
                "inlineData": [{"open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 1000}],
            }
        },
    )
    snippet = handler.handle(node, generator=None)
    assert "df = df.sort_index()" in snippet
    assert "df = df.dropna()" in snippet
    assert "tz_convert('US/Eastern')" in snippet


def test_custom_dataset_handler_detects_format_and_fills_missing():
    handler = CustomDatasetHandler()
    node = Node(
        id="dataset",
        type="customDataset",
        data={
            "parameters": {
                "fileName": "features.parquet",
                "format": "parquet",
                "dateColumn": "timestamp",
                "valueColumns": ["close", "volume"],
                "fillMethod": "zero",
            }
        },
    )
    snippet = handler.handle(node, generator=None)
    assert "pd.read_parquet('features.parquet')" in snippet
    assert "df['timestamp'] = pd.to_datetime" in snippet
    assert "df = df.fillna(0)" in snippet


def test_technical_indicator_handler_supports_macd_and_bollinger():
    handler = TechnicalIndicatorHandler()
    generator = StubGenerator(
        edges={
            "macd-node": [("source", "data-output", "data-input")],
            "bb-node": [("source", "data-output", "data-input")],
        }
    )
    macd_node = Node(
        id="macd-node",
        type="technicalIndicator",
        data={"parameters": {"indicator": "MACD", "source": "close"}},
    )
    snippet = handler.handle(macd_node, generator)
    assert "indicator_macd_node_2" in snippet  # signal line
    assert "indicator_macd_node_3" in snippet  # histogram

    bb_node = Node(
        id="bb-node",
        type="technicalIndicator",
        data={"parameters": {"indicator": "BB", "period": 10}},
    )
    snippet = handler.handle(bb_node, generator)
    assert "indicator_bb_node_2" in snippet
    assert "indicator_bb_node_3" in snippet


def test_condition_handler_supports_between_and_confirmation():
    handler = ConditionHandler()
    generator = StubGenerator(
        edges={"cond-1": [("source", "output-1", "data-input")]}
    )
    node = Node(
        id="cond-1",
        type="condition",
        data={
            "parameters": {
                "condition": "between",
                "minValue": 10,
                "maxValue": 20,
                "confirmationBars": 3,
                "invertCondition": True,
            }
        },
    )
    snippet = handler.handle(node, generator)
    assert "rolling(window=3" in snippet
    assert "~condition_cond_1" in snippet


def test_logic_handler_supports_majority_operation():
    handler = LogicHandler()
    generator = StubGenerator(
        edges={
            "logic-1": [
                ("sig-a", "signal-output", "input-0"),
                ("sig-b", "signal-output", "input-1"),
                ("sig-c", "signal-output", "input-2"),
            ]
        }
    )
    node = Node(
        id="logic-1",
        type="logic",
        data={"parameters": {"operation": "MAJORITY"}},
    )
    snippet = handler.handle(node, generator)
    assert "signals_logic_1.sum(axis=1)" in snippet


def test_action_handler_generates_order_metadata():
    handler = ActionHandler()
    generator = StubGenerator(
        edges={
            "action-1": [
                ("logic-1", "output", "signal-input"),
            ]
        }
    )
    node = Node(
        id="action-1",
        type="action",
        data={
            "parameters": {
                "action": "buy",
                "actionCategory": "entry",
                "order_type": "limit",
                "limitPrice": 120.5,
                "positionSizing": "percentage",
                "percentSize": 5,
                "take_profit": 2,
                "stop_loss": 1,
            }
        },
    )
    snippet = handler.handle(node, generator)
    assert "order_type_action_1" in snippet
    assert "limit_price_action_1" in snippet


def test_risk_handler_emits_drawdown_and_action_columns():
    handler = RiskHandler()
    node = Node(
        id="risk-1",
        type="risk",
        data={
            "parameters": {
                "maxLoss": 3,
                "portfolioHeat": 20,
                "maxDrawdown": 12,
                "emergencyAction": "flatten_positions",
            }
        },
    )
    snippet = handler.handle(node, generator=None)
    assert "risk_drawdown_alert_risk_1" in snippet
    assert "risk_action_risk_1" in snippet
