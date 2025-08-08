"""
Unit tests for workflow parser in AI-ML strategy service.
Tests parsing of visual workflow definitions into ML-ready formats.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the app directory to the path
APP_DIR = Path(__file__).resolve().parents[2] / "app"
sys.path.insert(0, str(APP_DIR))

from services.workflow_parser import (
    WorkflowParser, NodeType, ValidationError, validate_workflow_for_training
)


@pytest.fixture
def minimal_valid_workflow():
    """Minimal valid workflow with all required node types."""
    return {
        "nodes": [
            {
                "id": "data-1",
                "type": "dataSource",
                "data": {"symbol": "BTCUSDT", "timeframe": "1h"}
            },
            {
                "id": "rsi-1",
                "type": "technicalIndicator",
                "data": {"indicator": "rsi", "period": 14}
            },
            {
                "id": "condition-1",
                "type": "condition",
                "data": {"threshold": 30, "operator": "<"}
            },
            {
                "id": "buy-1",
                "type": "action",
                "data": {"action": "buy", "quantity": 100}
            }
        ],
        "edges": [
            {"source": "data-1", "target": "rsi-1"},
            {"source": "rsi-1", "target": "condition-1"},
            {"source": "condition-1", "target": "buy-1"}
        ]
    }

@pytest.fixture
def complex_workflow():
    """Complex workflow with multiple indicators and advanced features."""
    return {
        "nodes": [
            {
                "id": "data-1",
                "type": "dataSource",
                "data": {
                    "symbol": "ETHUSDT",
                    "timeframe": "15m",
                    "exchange": "binance",
                    "lookback_periods": 500
                }
            },
            {
                "id": "rsi-1",
                "type": "technicalIndicator",
                "data": {"indicator": "rsi", "period": 14, "source": "close"}
            },
            {
                "id": "macd-1",
                "type": "technicalIndicator",
                "data": {
                    "indicator": "macd",
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                }
            },
            {
                "id": "bollinger-1",
                "type": "technicalIndicator",
                "data": {
                    "indicator": "bollinger_bands",
                    "period": 20,
                    "std_dev": 2
                }
            },
            {
                "id": "adx-1",
                "type": "technicalIndicator",
                "data": {"indicator": "adx", "period": 14}
            },
            {
                "id": "rsi-condition",
                "type": "condition",
                "data": {
                    "condition_type": "threshold",
                    "operator": "<",
                    "threshold": 30,
                    "comparison_mode": "value"
                }
            },
            {
                "id": "macd-condition",
                "type": "condition",
                "data": {
                    "condition_type": "threshold",
                    "operator": ">",
                    "threshold": 0,
                    "comparison_mode": "cross_above"
                }
            },
            {
                "id": "logic-and",
                "type": "logic",
                "data": {
                    "logic": "AND",
                    "inputs": ["rsi-condition", "macd-condition"]
                }
            },
            {
                "id": "risk-1",
                "type": "risk",
                "data": {
                    "risk_type": "position_size",
                    "max_position_size": 0.1,
                    "stop_loss_percentage": 0.02,
                    "take_profit_percentage": 0.04,
                    "max_daily_trades": 5
                }
            },
            {
                "id": "buy-action",
                "type": "action",
                "data": {
                    "action_type": "buy",
                    "quantity": 50,
                    "order_type": "market",
                    "stop_loss": 0.02,
                    "take_profit": 0.04
                }
            },
            {
                "id": "sell-action",
                "type": "action",
                "data": {
                    "action_type": "sell",
                    "quantity": 50,
                    "order_type": "limit",
                    "price_offset": 0.001
                }
            }
        ],
        "edges": [
            {"source": "data-1", "target": "rsi-1"},
            {"source": "data-1", "target": "macd-1"},
            {"source": "data-1", "target": "bollinger-1"},
            {"source": "data-1", "target": "adx-1"},
            {"source": "rsi-1", "target": "rsi-condition"},
            {"source": "macd-1", "target": "macd-condition"},
            {"source": "rsi-condition", "target": "logic-and"},
            {"source": "macd-condition", "target": "logic-and"},
            {"source": "logic-and", "target": "buy-action"},
            {"source": "bollinger-1", "target": "sell-action"},
            {"source": "risk-1", "target": "buy-action"},
            {"source": "risk-1", "target": "sell-action"}
        ]
    }

@pytest.fixture
def invalid_workflow():
    """Invalid workflow missing required components."""
    return {
        "nodes": [
            {
                "id": "data-1",
                "type": "dataSource",
                "data": {"symbol": "BTCUSDT"}
            }
        ],
        "edges": []
    }


class TestWorkflowParser:
    """Test cases for WorkflowParser class."""
    
    def test_parser_initialization(self):
        """Test WorkflowParser initialization."""
        parser = WorkflowParser()
        assert parser is not None
        assert hasattr(parser, 'parse_workflow')
        assert hasattr(parser, 'parse_data_sources')
        assert hasattr(parser, 'parse_indicators')
    
    def test_minimal_workflow_parsing(self, minimal_valid_workflow):
        """Test parsing of minimal valid workflow."""
        parser = WorkflowParser()
        result = parser.parse_workflow(minimal_valid_workflow)
        
        # Verify successful parsing
        assert "data_sources" in result
        assert "technical_indicators" in result
        assert "conditions" in result
        assert "actions" in result
        assert "execution_graph" in result
        assert "complexity_score" in result
        
        # Verify components were parsed correctly
        assert len(result["data_sources"]) == 1
        assert len(result["technical_indicators"]) == 1
        assert len(result["conditions"]) == 1
        assert len(result["actions"]) == 1
        
        # Verify data source parsing
        data_source = result["data_sources"][0]
        assert data_source["symbol"] == "BTCUSDT"
        assert data_source["timeframe"] == "1h"
        assert data_source["node_type"] == NodeType.DATA_SOURCE
        
        # Verify technical indicator parsing
        indicator = result["technical_indicators"][0]
        assert indicator["indicator_type"] == "rsi"
        assert indicator["period"] == 14
        assert indicator["outputs"] == ["rsi_output"]
        
        # Verify condition parsing
        condition = result["conditions"][0]
        assert condition["operator"] == "<"
        assert condition["threshold"] == 30
        assert condition["optimization_target"] is True
        
        # Verify action parsing
        action = result["actions"][0]
        assert action["action_type"] == "buy"
        assert action["quantity"] == 100
    
    def test_complex_workflow_parsing(self, complex_workflow):
        """Test parsing of complex workflow with all node types."""
        parser = WorkflowParser()
        result = parser.parse_workflow(complex_workflow)
        
        # Verify all component types are present
        assert len(result["data_sources"]) == 1
        assert len(result["technical_indicators"]) == 4
        assert len(result["conditions"]) == 2
        assert len(result["actions"]) == 2
        assert len(result["risk_management"]) == 1
        assert len(result["logic_components"]) == 1
        
        # Verify complex indicators are parsed correctly
        indicators_by_type = {ind["indicator_type"]: ind for ind in result["technical_indicators"]}
        
        # RSI indicator
        assert "rsi" in indicators_by_type
        assert indicators_by_type["rsi"]["period"] == 14
        
        # MACD indicator
        assert "macd" in indicators_by_type
        macd = indicators_by_type["macd"]
        assert macd["fast_period"] == 12
        assert macd["slow_period"] == 26
        assert macd["signal_period"] == 9
        assert len(macd["outputs"]) == 3  # macd, signal, histogram
        
        # Bollinger Bands
        assert "bollinger_bands" in indicators_by_type
        bollinger = indicators_by_type["bollinger_bands"]
        assert bollinger["period"] == 20
        assert bollinger["std_dev"] == 2
        assert len(bollinger["outputs"]) == 4  # upper, middle, lower, width
        
        # ADX indicator
        assert "adx" in indicators_by_type
        adx = indicators_by_type["adx"]
        assert len(adx["outputs"]) == 3  # adx, di_plus, di_minus
        
        # Verify risk management parsing
        risk = result["risk_management"][0]
        assert risk["max_position_size"] == 0.1
        assert risk["stop_loss_percentage"] == 0.02
        assert risk["max_daily_trades"] == 5
        
        # Verify logic component parsing
        logic = result["logic_components"][0]
        assert logic["logic_type"] == "AND"
        assert len(logic["inputs"]) == 2
    
    def test_empty_workflow_validation(self):
        """Test validation of empty workflow."""
        parser = WorkflowParser()
        empty_workflow = {"nodes": [], "edges": []}
        
        with pytest.raises(ValidationError, match="must contain at least one node"):
            parser.parse_workflow(empty_workflow)
    
    def test_missing_required_nodes_validation(self, invalid_workflow):
        """Test validation of workflow missing required node types."""
        parser = WorkflowParser()
        
        with pytest.raises(ValidationError, match="must contain at least one action"):
            parser.parse_workflow(invalid_workflow)
    
    def test_malformed_workflow_handling(self):
        """Test handling of malformed workflow definitions."""
        parser = WorkflowParser()
        
        # Missing nodes key
        with pytest.raises(ValidationError):
            parser.parse_workflow({"edges": []})
        
        # Missing edges key
        with pytest.raises(ValidationError):
            parser.parse_workflow({"nodes": []})
        
        # None input
        with pytest.raises(ValidationError):
            parser.parse_workflow(None)
    
    def test_data_source_parsing(self, complex_workflow):
        """Test specific data source node parsing."""
        parser = WorkflowParser()
        nodes = complex_workflow["nodes"]
        
        data_sources = parser.parse_data_sources(nodes)
        assert len(data_sources) == 1
        
        ds = data_sources[0]
        assert ds["symbol"] == "ETHUSDT"
        assert ds["timeframe"] == "15m"
        assert ds["exchange"] == "binance"
        assert ds["lookback_periods"] == 500
        assert "open" in ds["required_features"]
        assert "close" in ds["required_features"]
        assert "volume" in ds["required_features"]
    
    def test_technical_indicator_parsing_variations(self):
        """Test parsing of various technical indicator configurations."""
        parser = WorkflowParser()
        
        # Test different indicator types
        indicator_nodes = [
            {
                "id": "sma-1",
                "type": "technicalIndicator",
                "data": {"indicator": "sma", "period": 20, "source": "close"}
            },
            {
                "id": "ema-1",
                "type": "technicalIndicator",
                "data": {"indicator": "ema", "period": 12, "source": "high"}
            },
            {
                "id": "wma-1",
                "type": "technicalIndicator",
                "data": {"indicator": "wma", "period": 15}
            }
        ]
        
        indicators = parser.parse_indicators(indicator_nodes)
        assert len(indicators) == 3
        
        # Verify each indicator type
        indicators_by_type = {ind["indicator_type"]: ind for ind in indicators}
        
        assert indicators_by_type["sma"]["period"] == 20
        assert indicators_by_type["sma"]["source"] == "close"
        
        assert indicators_by_type["ema"]["period"] == 12
        assert indicators_by_type["ema"]["source"] == "high"
        
        assert indicators_by_type["wma"]["period"] == 15
    
    def test_condition_parsing_modes(self):
        """Test parsing of different condition types and modes."""
        parser = WorkflowParser()
        
        condition_nodes = [
            {
                "id": "threshold-1",
                "type": "condition",
                "data": {
                    "condition_type": "threshold",
                    "operator": ">",
                    "threshold": 50,
                    "comparison_mode": "value"
                }
            },
            {
                "id": "cross-above-1",
                "type": "condition",
                "data": {
                    "condition_type": "threshold",
                    "operator": ">",
                    "threshold": 0,
                    "comparison_mode": "cross_above"
                }
            },
            {
                "id": "cross-below-1",
                "type": "condition",
                "data": {
                    "condition_type": "threshold",
                    "operator": "<",
                    "threshold": 100,
                    "comparison_mode": "cross_below"
                }
            }
        ]
        
        conditions = parser.parse_conditions(condition_nodes)
        assert len(conditions) == 3
        
        # Verify different comparison modes
        modes = [cond["comparison_mode"] for cond in conditions]
        assert "value" in modes
        assert "cross_above" in modes
        assert "cross_below" in modes
    
    def test_action_parsing_variations(self):
        """Test parsing of different action types."""
        parser = WorkflowParser()
        
        action_nodes = [
            {
                "id": "market-buy",
                "type": "action",
                "data": {
                    "action_type": "buy",
                    "quantity": 100,
                    "order_type": "market"
                }
            },
            {
                "id": "limit-sell",
                "type": "action",
                "data": {
                    "action_type": "sell",
                    "quantity": 50,
                    "order_type": "limit",
                    "price_offset": 0.01,
                    "stop_loss": 0.02,
                    "take_profit": 0.04
                }
            }
        ]
        
        actions = parser.parse_actions(action_nodes)
        assert len(actions) == 2
        
        buy_action = next(a for a in actions if a["action_type"] == "buy")
        assert buy_action["order_type"] == "market"
        assert buy_action["quantity"] == 100
        
        sell_action = next(a for a in actions if a["action_type"] == "sell")
        assert sell_action["order_type"] == "limit"
        assert sell_action["price_offset"] == 0.01
        assert sell_action["stop_loss"] == 0.02
        assert sell_action["take_profit"] == 0.04
    
    def test_execution_graph_building(self, minimal_valid_workflow):
        """Test building of execution dependency graph."""
        parser = WorkflowParser()
        result = parser.parse_workflow(minimal_valid_workflow)
        
        graph = result["execution_graph"]
        
        # Verify graph structure
        assert "data-1" in graph
        assert "rsi-1" in graph
        assert "condition-1" in graph
        assert "buy-1" in graph
        
        # Verify dependencies
        assert graph["data-1"] == []  # No dependencies
        assert "data-1" in graph["rsi-1"]  # RSI depends on data
        assert "rsi-1" in graph["condition-1"]  # Condition depends on RSI
        assert "condition-1" in graph["buy-1"]  # Action depends on condition
    
    def test_complexity_score_calculation(self, minimal_valid_workflow, complex_workflow):
        """Test complexity score calculation."""
        parser = WorkflowParser()
        
        minimal_result = parser.parse_workflow(minimal_valid_workflow)
        complex_result = parser.parse_workflow(complex_workflow)
        
        minimal_score = minimal_result["complexity_score"]
        complex_score = complex_result["complexity_score"]
        
        # Complex workflow should have higher score
        assert complex_score > minimal_score
        assert minimal_score >= 5  # Minimum reasonable score
        assert complex_score >= 20  # Should be significantly higher
    
    def test_workflow_completeness_validation(self):
        """Test workflow completeness validation."""
        parser = WorkflowParser()
        
        # Test workflow without data sources
        no_data_workflow = {
            "nodes": [
                {"id": "condition-1", "type": "condition", "data": {"threshold": 30}},
                {"id": "action-1", "type": "action", "data": {"action": "buy"}}
            ],
            "edges": []
        }
        
        with pytest.raises(ValidationError, match="at least one data source"):
            parser.parse_workflow(no_data_workflow)
        
        # Test workflow without actions
        no_action_workflow = {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {"id": "rsi-1", "type": "technicalIndicator", "data": {"indicator": "rsi"}}
            ],
            "edges": []
        }
        
        with pytest.raises(ValidationError, match="at least one action"):
            parser.parse_workflow(no_action_workflow)


class TestWorkflowValidation:
    """Test workflow validation functions."""
    
    def test_valid_workflow_validation(self, minimal_valid_workflow, complex_workflow):
        """Test validation of valid workflows."""
        # Minimal workflow
        is_valid, errors = validate_workflow_for_training(minimal_valid_workflow)
        assert is_valid is True
        assert len(errors) == 0
        
        # Complex workflow
        is_valid, errors = validate_workflow_for_training(complex_workflow)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_workflow_validation(self, invalid_workflow):
        """Test validation of invalid workflows."""
        is_valid, errors = validate_workflow_for_training(invalid_workflow)
        assert is_valid is False
        assert len(errors) > 0
        assert any("action" in error.lower() for error in errors)
    
    def test_too_simple_workflow_validation(self):
        """Test validation of overly simple workflows."""
        simple_workflow = {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {"id": "action-1", "type": "action", "data": {"action": "buy"}}
            ],
            "edges": [{"source": "data-1", "target": "action-1"}]
        }
        
        is_valid, errors = validate_workflow_for_training(simple_workflow)
        assert is_valid is False
        assert any("too simple" in error.lower() for error in errors)
    
    def test_overly_complex_workflow_validation(self):
        """Test validation of overly complex workflows."""
        # Create workflow with many nodes to trigger complexity warning
        nodes = [{"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}}]
        
        # Add many indicators
        for i in range(50):
            nodes.append({
                "id": f"indicator-{i}",
                "type": "technicalIndicator",
                "data": {"indicator": "sma", "period": i + 1}
            })
        
        # Add action
        nodes.append({"id": "action-1", "type": "action", "data": {"action": "buy"}})
        
        # Add many edges
        edges = [{"source": "data-1", "target": f"indicator-{i}"} for i in range(50)]
        edges.append({"source": "indicator-0", "target": "action-1"})
        
        complex_workflow = {"nodes": nodes, "edges": edges}
        
        is_valid, errors = validate_workflow_for_training(complex_workflow)
        assert is_valid is False
        assert any("too complex" in error.lower() for error in errors)


class TestNodeTypeEnum:
    """Test NodeType enumeration."""
    
    def test_node_type_values(self):
        """Test NodeType enum values."""
        assert NodeType.DATA_SOURCE == "dataSource"
        assert NodeType.TECHNICAL_INDICATOR == "technicalIndicator"
        assert NodeType.CONDITION == "condition"
        assert NodeType.ACTION == "action"
        assert NodeType.RISK == "risk"
        assert NodeType.LOGIC == "logic"
    
    def test_node_type_iteration(self):
        """Test NodeType enum iteration."""
        node_types = list(NodeType)
        assert len(node_types) == 6
        assert NodeType.DATA_SOURCE in node_types
        assert NodeType.TECHNICAL_INDICATOR in node_types
        assert NodeType.CONDITION in node_types
        assert NodeType.ACTION in node_types
        assert NodeType.RISK in node_types
        assert NodeType.LOGIC in node_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])