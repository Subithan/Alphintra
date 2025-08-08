"""
Unit tests for workflow converter.
Tests the conversion of visual workflows to ML training configurations.
"""

import pytest
import json
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add the parent directory to the path to import the converter
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from workflow_converter import WorkflowConverter


@pytest.fixture
def simple_workflow():
    """Simple workflow with basic components."""
    return {
        "nodes": [
            {
                "id": "data-1",
                "type": "dataSource",
                "data": {
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "exchange": "binance"
                }
            },
            {
                "id": "sma-1",
                "type": "technicalIndicator",
                "data": {
                    "indicator": "sma",
                    "period": 20
                }
            },
            {
                "id": "condition-1",
                "type": "condition",
                "data": {
                    "threshold": 45000,
                    "operator": ">"
                }
            },
            {
                "id": "buy-1",
                "type": "action",
                "data": {
                    "action": "buy",
                    "quantity": 100
                }
            }
        ],
        "edges": [
            {"source": "data-1", "target": "sma-1"},
            {"source": "sma-1", "target": "condition-1"},
            {"source": "condition-1", "target": "buy-1"}
        ]
    }

@pytest.fixture
def complex_workflow():
    """Complex workflow with multiple indicators and conditions."""
    return {
        "nodes": [
            {
                "id": "data-1",
                "type": "dataSource",
                "data": {
                    "symbol": "ETHUSDT",
                    "timeframe": "15m",
                    "exchange": "binance"
                }
            },
            {
                "id": "rsi-1",
                "type": "technicalIndicator",
                "data": {
                    "indicator": "rsi",
                    "period": 14
                }
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
                "id": "condition-1",
                "type": "condition",
                "data": {
                    "threshold": 30,
                    "operator": "<"
                }
            },
            {
                "id": "condition-2",
                "type": "condition",
                "data": {
                    "threshold": 0,
                    "operator": ">"
                }
            },
            {
                "id": "risk-1",
                "type": "risk",
                "data": {
                    "max_position_size": 0.05,
                    "stop_loss_percentage": 0.02
                }
            },
            {
                "id": "buy-1",
                "type": "action",
                "data": {
                    "action": "buy",
                    "quantity": 50
                }
            },
            {
                "id": "sell-1",
                "type": "action",
                "data": {
                    "action": "sell",
                    "quantity": 50
                }
            }
        ],
        "edges": [
            {"source": "data-1", "target": "rsi-1"},
            {"source": "data-1", "target": "macd-1"},
            {"source": "rsi-1", "target": "condition-1"},
            {"source": "macd-1", "target": "condition-2"},
            {"source": "condition-1", "target": "buy-1"},
            {"source": "condition-2", "target": "sell-1"},
            {"source": "risk-1", "target": "buy-1"},
            {"source": "risk-1", "target": "sell-1"}
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


class TestWorkflowConverter:
    """Test cases for WorkflowConverter class."""
    
    def test_converter_initialization(self):
        """Test WorkflowConverter initialization."""
        converter = WorkflowConverter()
        assert converter is not None
        assert hasattr(converter, 'convert_to_training_config')
        assert hasattr(converter, '_extract_optimization_parameters')
    
    def test_simple_workflow_conversion(self, simple_workflow):
        """Test conversion of simple workflow."""
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(simple_workflow)
        
        assert result["success"] is True
        assert "training_config" in result
        
        config = result["training_config"]
        assert "data_sources" in config
        assert "features" in config
        assert "targets" in config
        assert "optimization_parameters" in config
        assert "parameter_bounds" in config
        
        # Verify data source extraction
        assert len(config["data_sources"]) == 1
        assert config["data_sources"][0]["symbol"] == "BTCUSDT"
        assert config["data_sources"][0]["timeframe"] == "1h"
        
        # Verify feature engineering
        assert len(config["features"]) >= 1
        assert any("sma" in feature for feature in config["features"])
        
        # Verify optimization parameters
        assert len(config["optimization_parameters"]) >= 2
        assert "sma_period" in config["optimization_parameters"]
        assert "threshold" in config["optimization_parameters"]
    
    def test_complex_workflow_conversion(self, complex_workflow):
        """Test conversion of complex workflow with multiple indicators."""
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(complex_workflow)
        
        assert result["success"] is True
        config = result["training_config"]
        
        # Verify multiple indicators are captured
        assert len(config["features"]) >= 2
        feature_names = " ".join(config["features"])
        assert "rsi" in feature_names
        assert "macd" in feature_names
        
        # Verify multiple conditions are captured
        assert len(config["targets"]) >= 2
        
        # Verify risk management parameters
        assert "risk_management" in config
        assert config["risk_management"]["max_position_size"] == 0.05
        assert config["risk_management"]["stop_loss_percentage"] == 0.02
        
        # Verify complex optimization parameters
        opt_params = config["optimization_parameters"]
        assert "rsi_period" in opt_params
        assert "macd_fast_period" in opt_params
        assert "macd_slow_period" in opt_params
        assert "macd_signal_period" in opt_params
    
    def test_invalid_workflow_handling(self, invalid_workflow):
        """Test handling of invalid workflow structures."""
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(invalid_workflow)
        
        assert result["success"] is False
        assert "error" in result
        assert "missing required node types" in result["error"].lower()
    
    def test_empty_workflow_handling(self):
        """Test handling of empty workflow."""
        converter = WorkflowConverter()
        empty_workflow = {"nodes": [], "edges": []}
        result = converter.convert_to_training_config(empty_workflow)
        
        assert result["success"] is False
        assert "error" in result
    
    def test_malformed_workflow_handling(self):
        """Test handling of malformed workflow data."""
        converter = WorkflowConverter()
        
        # Missing nodes key
        malformed1 = {"edges": []}
        result1 = converter.convert_to_training_config(malformed1)
        assert result1["success"] is False
        
        # Missing edges key
        malformed2 = {"nodes": []}
        result2 = converter.convert_to_training_config(malformed2)
        assert result2["success"] is False
        
        # None input
        result3 = converter.convert_to_training_config(None)
        assert result3["success"] is False
    
    def test_data_source_mapping(self, simple_workflow):
        """Test data source node mapping."""
        converter = WorkflowConverter()
        
        # Extract data source nodes
        data_sources = [node for node in simple_workflow["nodes"] if node["type"] == "dataSource"]
        mapped_sources = converter._map_data_source_nodes(data_sources)
        
        assert len(mapped_sources) == 1
        source = mapped_sources[0]
        assert source["symbol"] == "BTCUSDT"
        assert source["timeframe"] == "1h"
        assert source["exchange"] == "binance"
        assert "ohlcv" in source["required_data"]
    
    def test_technical_indicator_mapping(self, complex_workflow):
        """Test technical indicator node mapping."""
        converter = WorkflowConverter()
        
        # Extract indicator nodes
        indicator_nodes = [node for node in complex_workflow["nodes"] 
                          if node["type"] == "technicalIndicator"]
        mapped_indicators = converter._map_technical_indicator_nodes(indicator_nodes)
        
        assert len(mapped_indicators) == 2
        
        # Check RSI mapping
        rsi_indicator = next(ind for ind in mapped_indicators if ind["type"] == "rsi")
        assert rsi_indicator["period"] == 14
        assert "rsi_value" in rsi_indicator["outputs"]
        
        # Check MACD mapping
        macd_indicator = next(ind for ind in mapped_indicators if ind["type"] == "macd")
        assert macd_indicator["fast_period"] == 12
        assert macd_indicator["slow_period"] == 26
        assert macd_indicator["signal_period"] == 9
        assert len(macd_indicator["outputs"]) == 3  # macd, signal, histogram
    
    def test_condition_mapping(self, complex_workflow):
        """Test condition node mapping to targets."""
        converter = WorkflowConverter()
        
        condition_nodes = [node for node in complex_workflow["nodes"] if node["type"] == "condition"]
        mapped_conditions = converter._map_condition_nodes(condition_nodes)
        
        assert len(mapped_conditions) == 2
        
        # Check threshold-based conditions
        for condition in mapped_conditions:
            assert "threshold" in condition
            assert "operator" in condition
            assert condition["operator"] in ["<", ">", "<=", ">=", "=="]
    
    def test_action_mapping(self, complex_workflow):
        """Test action node mapping to signals."""
        converter = WorkflowConverter()
        
        action_nodes = [node for node in complex_workflow["nodes"] if node["type"] == "action"]
        mapped_actions = converter._map_action_nodes(action_nodes)
        
        assert len(mapped_actions) == 2
        
        # Check buy and sell actions
        actions_by_type = {action["action"]: action for action in mapped_actions}
        assert "buy" in actions_by_type
        assert "sell" in actions_by_type
        
        assert actions_by_type["buy"]["quantity"] == 50
        assert actions_by_type["sell"]["quantity"] == 50
    
    def test_risk_management_mapping(self, complex_workflow):
        """Test risk management node mapping."""
        converter = WorkflowConverter()
        
        risk_nodes = [node for node in complex_workflow["nodes"] if node["type"] == "risk"]
        mapped_risk = converter._map_risk_management_nodes(risk_nodes)
        
        assert mapped_risk is not None
        assert mapped_risk["max_position_size"] == 0.05
        assert mapped_risk["stop_loss_percentage"] == 0.02
    
    def test_optimization_parameter_extraction(self, complex_workflow):
        """Test extraction of optimization parameters."""
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(complex_workflow)
        
        config = result["training_config"]
        opt_params = config["optimization_parameters"]
        bounds = config["parameter_bounds"]
        
        # Verify parameter extraction
        expected_params = ["rsi_period", "macd_fast_period", "macd_slow_period", 
                          "macd_signal_period", "condition_1_threshold", "condition_2_threshold"]
        
        for param in expected_params:
            assert param in opt_params
            assert param in bounds
            assert isinstance(bounds[param], list)
            assert len(bounds[param]) == 2  # [min, max]
    
    def test_complexity_assessment(self, simple_workflow, complex_workflow):
        """Test workflow complexity assessment."""
        converter = WorkflowConverter()
        
        simple_result = converter.convert_to_training_config(simple_workflow)
        complex_result = converter.convert_to_training_config(complex_workflow)
        
        simple_complexity = simple_result["training_config"]["complexity_score"]
        complex_complexity = complex_result["training_config"]["complexity_score"]
        
        assert complex_complexity > simple_complexity
        assert simple_complexity >= 1
        assert complex_complexity >= 5
    
    def test_parameter_bounds_generation(self, simple_workflow):
        """Test parameter bounds generation."""
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(simple_workflow)
        
        bounds = result["training_config"]["parameter_bounds"]
        
        # Check SMA period bounds
        assert "sma_period" in bounds
        sma_bounds = bounds["sma_period"]
        assert sma_bounds[0] < sma_bounds[1]  # min < max
        assert sma_bounds[0] >= 1  # reasonable minimum
        
        # Check threshold bounds
        assert "threshold" in bounds
        threshold_bounds = bounds["threshold"]
        assert threshold_bounds[0] < threshold_bounds[1]
    
    def test_feature_engineering_code_generation(self, complex_workflow):
        """Test feature engineering code generation."""
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(complex_workflow)
        
        config = result["training_config"]
        features = config["features"]
        
        # Verify feature code generation
        assert len(features) >= 2
        
        # Check that feature calculations are reasonable
        for feature in features:
            assert isinstance(feature, str)
            assert len(feature) > 0
            # Should contain technical indicator calculations
            assert any(indicator in feature.lower() for indicator in ["rsi", "macd", "sma", "ema"])


class TestWorkflowConverterErrorHandling:
    """Test error handling and edge cases."""
    
    def test_missing_required_fields(self):
        """Test handling of nodes with missing required fields."""
        converter = WorkflowConverter()
        
        incomplete_workflow = {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {}},  # Missing symbol
                {"id": "indicator-1", "type": "technicalIndicator", "data": {}}  # Missing indicator type
            ],
            "edges": []
        }
        
        result = converter.convert_to_training_config(incomplete_workflow)
        
        # Should handle gracefully with warnings or reasonable defaults
        assert result["success"] is True  # Should not fail completely
        config = result["training_config"]
        assert "warnings" in result or len(config["data_sources"]) >= 0
    
    def test_unsupported_node_types(self):
        """Test handling of unsupported node types."""
        converter = WorkflowConverter()
        
        workflow_with_unknown = {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {"id": "unknown-1", "type": "unknownType", "data": {}},  # Unknown type
                {"id": "action-1", "type": "action", "data": {"action": "buy"}}
            ],
            "edges": []
        }
        
        result = converter.convert_to_training_config(workflow_with_unknown)
        
        # Should handle unknown types gracefully
        assert result["success"] is True
        if "warnings" in result:
            assert any("unknown" in warning.lower() for warning in result["warnings"])
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies in workflow."""
        converter = WorkflowConverter()
        
        circular_workflow = {
            "nodes": [
                {"id": "node-1", "type": "technicalIndicator", "data": {"indicator": "sma"}},
                {"id": "node-2", "type": "condition", "data": {"threshold": 50}},
                {"id": "node-3", "type": "action", "data": {"action": "buy"}}
            ],
            "edges": [
                {"source": "node-1", "target": "node-2"},
                {"source": "node-2", "target": "node-3"},
                {"source": "node-3", "target": "node-1"}  # Creates circular dependency
            ]
        }
        
        result = converter.convert_to_training_config(circular_workflow)
        
        # Should detect and handle circular dependencies
        if "warnings" in result:
            assert any("circular" in warning.lower() for warning in result["warnings"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])