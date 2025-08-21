"""
Unit tests for strategy generator in AI-ML strategy service.
Tests code generation from parsed workflows.
"""

import pytest
import ast
import re
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# Add the app directory to the path
APP_DIR = Path(__file__).resolve().parents[2] / "app"
sys.path.insert(0, str(APP_DIR))

from services.strategy_generator import (
    StrategyGenerator, StrategyGenerationError, generate_strategy_from_workflow_definition
)


@pytest.fixture
def sample_parsed_workflow():
    """Sample parsed workflow for testing."""
    return {
        "data_sources": [
            {
                "id": "data-1",
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "exchange": "binance",
                "data_type": "ohlcv",
                "lookback_periods": 100,
                "required_features": ["open", "high", "low", "close", "volume"],
                "node_type": "dataSource"
            }
        ],
        "technical_indicators": [
            {
                "id": "rsi-1",
                "indicator_type": "rsi",
                "period": 14,
                "source": "close",
                "outputs": ["rsi_output"],
                "node_type": "technicalIndicator"
            },
            {
                "id": "macd-1",
                "indicator_type": "macd",
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
                "outputs": ["macd_output", "signal_output", "histogram_output"],
                "node_type": "technicalIndicator"
            }
        ],
        "conditions": [
            {
                "id": "condition-1",
                "condition_type": "threshold",
                "operator": "<",
                "threshold": 30,
                "comparison_mode": "value",
                "node_type": "condition",
                "optimization_target": True
            }
        ],
        "actions": [
            {
                "id": "buy-1",
                "action_type": "buy",
                "signal": "buy",
                "quantity": 100,
                "order_type": "market",
                "node_type": "action"
            }
        ],
        "risk_management": [
            {
                "id": "risk-1",
                "risk_type": "position_size",
                "max_position_size": 0.1,
                "stop_loss_percentage": 0.02,
                "take_profit_percentage": 0.04,
                "max_daily_trades": 10,
                "max_drawdown": 0.05,
                "node_type": "risk"
            }
        ],
        "logic_components": [],
        "execution_graph": {
            "data-1": [],
            "rsi-1": ["data-1"],
            "macd-1": ["data-1"],
            "condition-1": ["rsi-1"],
            "buy-1": ["condition-1"]
        },
        "node_count": 5,
        "edge_count": 4,
        "complexity_score": 15
    }

@pytest.fixture
def workflow_metadata():
    """Sample workflow metadata."""
    return {
        "workflow_id": 123,
        "workflow_name": "RSI Strategy",
        "user_id": "user_456"
    }

@pytest.fixture
def simple_parsed_workflow():
    """Simple parsed workflow with minimal components."""
    return {
        "data_sources": [
            {
                "id": "data-1",
                "symbol": "ETHUSDT",
                "timeframe": "15m",
                "exchange": "binance",
                "node_type": "dataSource"
            }
        ],
        "technical_indicators": [
            {
                "id": "sma-1",
                "indicator_type": "sma",
                "period": 20,
                "source": "close",
                "outputs": ["sma_output"],
                "node_type": "technicalIndicator"
            }
        ],
        "conditions": [
            {
                "id": "condition-1",
                "operator": ">",
                "threshold": 3000,
                "node_type": "condition"
            }
        ],
        "actions": [
            {
                "id": "sell-1",
                "action_type": "sell",
                "quantity": 50,
                "order_type": "limit",
                "node_type": "action"
            }
        ],
        "risk_management": [],
        "logic_components": [],
        "execution_graph": {
            "data-1": [],
            "sma-1": ["data-1"],
            "condition-1": ["sma-1"],
            "sell-1": ["condition-1"]
        },
        "node_count": 4,
        "edge_count": 3,
        "complexity_score": 8
    }


class TestStrategyGenerator:
    """Test cases for StrategyGenerator class."""
    
    def test_generator_initialization(self):
        """Test StrategyGenerator initialization."""
        generator = StrategyGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_from_workflow')
        assert hasattr(generator, '_generate_indicator_calculations')
        assert hasattr(generator, '_generate_condition_evaluations')
        assert hasattr(generator, '_generate_signal_generation')
    
    def test_successful_code_generation(self, sample_parsed_workflow, workflow_metadata):
        """Test successful strategy code generation."""
        generator = StrategyGenerator()
        result = generator.generate_from_workflow(sample_parsed_workflow, workflow_metadata)
        
        # Verify successful generation
        assert result["success"] is True
        assert "strategy_code" in result
        assert "strategy_class" in result
        assert "entry_point" in result
        assert "validation" in result
        assert "metadata" in result
        assert "optimization_config" in result
        
        # Verify strategy code structure
        code = result["strategy_code"]
        assert isinstance(code, str)
        assert len(code) > 0
        assert "class WorkflowStrategy" in code
        assert "def execute_strategy" in code
        assert "def create_strategy_instance" in code
        
        # Verify metadata
        metadata = result["metadata"]
        assert metadata["workflow_id"] == 123
        assert metadata["workflow_name"] == "RSI Strategy"
        assert metadata["indicator_count"] == 2
        assert metadata["condition_count"] == 1
        assert metadata["action_count"] == 1
        assert metadata["complexity_score"] == 15
    
    def test_indicator_calculations_generation(self, sample_parsed_workflow):
        """Test generation of indicator calculation code."""
        generator = StrategyGenerator()
        indicators = sample_parsed_workflow["technical_indicators"]
        
        indicator_code = generator._generate_indicator_calculations(indicators)
        
        # Verify RSI calculation code
        assert "rsi-1 - RSI" in indicator_code
        assert "delta = data['close'].diff()" in indicator_code
        assert "gain = (delta.where(delta > 0, 0)).rolling(14).mean()" in indicator_code
        assert "loss = (-delta.where(delta < 0, 0)).rolling(14).mean()" in indicator_code
        assert "100 - (100 / (1 + rs))" in indicator_code
        
        # Verify MACD calculation code
        assert "macd-1 - MACD" in indicator_code
        assert "ema_fast = data['close'].ewm(span=12).mean()" in indicator_code
        assert "ema_slow = data['close'].ewm(span=26).mean()" in indicator_code
        assert "signal_line = macd_line.ewm(span=9).mean()" in indicator_code
    
    def test_condition_evaluations_generation(self, sample_parsed_workflow):
        """Test generation of condition evaluation code."""
        generator = StrategyGenerator()
        conditions = sample_parsed_workflow["conditions"]
        indicators = sample_parsed_workflow["technical_indicators"]
        
        condition_code = generator._generate_condition_evaluations(conditions, indicators)
        
        # Verify condition code
        assert "condition-1 - Threshold condition" in condition_code
        assert "current_price < 30" in condition_code
        assert "conditions['condition-1']" in condition_code
    
    def test_signal_generation_code(self, sample_parsed_workflow):
        """Test generation of signal generation code."""
        generator = StrategyGenerator()
        actions = sample_parsed_workflow["actions"]
        conditions = sample_parsed_workflow["conditions"]
        
        signal_code = generator._generate_signal_generation(actions, conditions)
        
        # Verify signal generation code
        assert "buy-1 - Buy signal" in signal_code
        assert "'action': 'buy'" in signal_code
        assert "'quantity': 100" in signal_code
        assert "'order_type': 'market'" in signal_code
        assert "signals.append" in signal_code
    
    def test_risk_parameters_generation(self, sample_parsed_workflow):
        """Test generation of risk management parameters."""
        generator = StrategyGenerator()
        risk_nodes = sample_parsed_workflow["risk_management"]
        
        risk_params = generator._generate_risk_parameters(risk_nodes)
        
        # Parse the JSON-like string back to dict for validation
        risk_dict = eval(risk_params.replace('"', "'"))
        
        assert risk_dict["max_position_size"] == 0.1
        assert risk_dict["max_drawdown"] == 0.05
        assert risk_dict["max_daily_trades"] == 10
    
    def test_optimization_parameters_generation(self, sample_parsed_workflow):
        """Test generation of optimization parameters."""
        generator = StrategyGenerator()
        indicators = sample_parsed_workflow["technical_indicators"]
        conditions = sample_parsed_workflow["conditions"]
        
        opt_params = generator._generate_optimization_parameters(indicators, conditions)
        
        # Parse the JSON-like string back to dict
        params_dict = eval(opt_params.replace('"', "'"))
        
        # Verify indicator parameters
        assert "rsi-1_period" in params_dict
        assert params_dict["rsi-1_period"] == 14
        
        assert "macd-1_fast_period" in params_dict
        assert params_dict["macd-1_fast_period"] == 12
        assert "macd-1_slow_period" in params_dict
        assert params_dict["macd-1_slow_period"] == 26
        assert "macd-1_signal_period" in params_dict
        assert params_dict["macd-1_signal_period"] == 9
        
        # Verify condition parameters
        assert "condition-1_threshold" in params_dict
        assert params_dict["condition-1_threshold"] == 30
    
    def test_parameter_bounds_generation(self, sample_parsed_workflow):
        """Test generation of parameter bounds for optimization."""
        generator = StrategyGenerator()
        indicators = sample_parsed_workflow["technical_indicators"]
        conditions = sample_parsed_workflow["conditions"]
        
        bounds = generator._generate_parameter_bounds(indicators, conditions)
        
        # Verify RSI bounds
        assert "rsi-1_period" in bounds
        rsi_bounds = bounds["rsi-1_period"]
        assert isinstance(rsi_bounds, list)
        assert len(rsi_bounds) == 2
        assert rsi_bounds[0] < rsi_bounds[1]
        
        # Verify MACD bounds
        assert "macd-1_fast_period" in bounds
        assert "macd-1_slow_period" in bounds
        assert "macd-1_signal_period" in bounds
        
        # Verify condition bounds
        assert "condition-1_threshold" in bounds
        threshold_bounds = bounds["condition-1_threshold"]
        assert isinstance(threshold_bounds, list)
        assert len(threshold_bounds) == 2
    
    def test_code_validation(self, sample_parsed_workflow, workflow_metadata):
        """Test generated code validation."""
        generator = StrategyGenerator()
        result = generator.generate_from_workflow(sample_parsed_workflow, workflow_metadata)
        
        validation = result["validation"]
        
        # Verify validation results
        assert validation["valid"] is True
        assert validation["syntax_valid"] is True
        assert "line_count" in validation
        assert validation["line_count"] > 0
        
        # Verify generated code is syntactically correct
        code = result["strategy_code"]
        try:
            ast.parse(code)
        except SyntaxError:
            pytest.fail("Generated code has syntax errors")
    
    def test_simple_workflow_generation(self, simple_parsed_workflow, workflow_metadata):
        """Test generation from simple workflow."""
        generator = StrategyGenerator()
        result = generator.generate_from_workflow(simple_parsed_workflow, workflow_metadata)
        
        assert result["success"] is True
        
        # Verify SMA indicator is generated
        code = result["strategy_code"]
        assert "sma" in code.lower()
        assert "rolling(20)" in code
        
        # Verify sell action is generated
        assert "'action': 'sell'" in code
        assert "'quantity': 50" in code
        assert "'order_type': 'limit'" in code
    
    def test_empty_components_handling(self):
        """Test handling of workflows with empty component lists."""
        generator = StrategyGenerator()
        
        empty_workflow = {
            "data_sources": [],
            "technical_indicators": [],
            "conditions": [],
            "actions": [],
            "risk_management": [],
            "logic_components": [],
            "execution_graph": {},
            "complexity_score": 0
        }
        
        metadata = {"workflow_id": 1, "workflow_name": "Empty"}
        
        # Should handle gracefully
        result = generator.generate_from_workflow(empty_workflow, metadata)
        
        # Code should still be generated with default/placeholder content
        assert result["success"] is True
        assert "strategy_code" in result
        assert "class WorkflowStrategy" in result["strategy_code"]
    
    def test_bollinger_bands_generation(self):
        """Test generation of Bollinger Bands indicator."""
        generator = StrategyGenerator()
        
        bollinger_indicator = [{
            "id": "bb-1",
            "indicator_type": "bollinger_bands",
            "period": 20,
            "std_dev": 2,
            "outputs": ["upper_output", "middle_output", "lower_output", "width_output"],
            "node_type": "technicalIndicator"
        }]
        
        code = generator._generate_indicator_calculations(bollinger_indicator)
        
        # Verify Bollinger Bands calculation
        assert "bb-1 - Bollinger Bands" in code
        assert "sma = data['close'].rolling(20).mean()" in code
        assert "std = data['close'].rolling(20).std()" in code
        assert "sma + (2 * std)" in code
        assert "sma - (2 * std)" in code
    
    def test_different_indicator_types(self):
        """Test generation of different indicator types."""
        generator = StrategyGenerator()
        
        indicators = [
            {
                "id": "sma-1",
                "indicator_type": "sma",
                "period": 10,
                "source": "close",
                "node_type": "technicalIndicator"
            },
            {
                "id": "ema-1", 
                "indicator_type": "ema",
                "period": 15,
                "source": "high",
                "node_type": "technicalIndicator"
            },
            {
                "id": "wma-1",
                "indicator_type": "wma", 
                "period": 25,
                "source": "low",
                "node_type": "technicalIndicator"
            }
        ]
        
        code = generator._generate_indicator_calculations(indicators)
        
        # Verify all indicator types are handled
        assert "sma-1 - SMA" in code
        assert "ema-1 - EMA" in code
        assert "wma-1 - WMA" in code
        assert "rolling(10)" in code
        assert "rolling(15)" in code
        assert "rolling(25)" in code
    
    def test_cross_conditions_generation(self):
        """Test generation of cross-over/cross-under conditions."""
        generator = StrategyGenerator()
        
        conditions = [
            {
                "id": "cross-above-1",
                "operator": ">",
                "threshold": 50,
                "comparison_mode": "cross_above",
                "node_type": "condition"
            },
            {
                "id": "cross-below-1",
                "operator": "<",
                "threshold": 80,
                "comparison_mode": "cross_below",
                "node_type": "condition"
            }
        ]
        
        code = generator._generate_condition_evaluations(conditions, [])
        
        # Verify cross-over conditions
        assert "cross_above" in code or "cross-above" in code
        assert "cross_below" in code or "cross-below" in code
        assert "data['close'].iloc[-2]" in code  # Previous value check
    
    def test_metadata_formatting(self, workflow_metadata):
        """Test metadata formatting for code generation."""
        generator = StrategyGenerator()
        formatted = generator._format_metadata(workflow_metadata)
        
        # Should be valid JSON-like string
        assert '"workflow_id": 123' in formatted
        assert '"workflow_name": "RSI Strategy"' in formatted
        assert '"user_id": "user_456"' in formatted


class TestStrategyGenerationErrorHandling:
    """Test error handling in strategy generation."""
    
    def test_malformed_workflow_handling(self):
        """Test handling of malformed workflow data."""
        generator = StrategyGenerator()
        
        malformed_workflow = {
            "data_sources": None,  # Should be list
            "technical_indicators": "invalid",  # Should be list
            "conditions": [],
            "actions": [],
            "complexity_score": "not_a_number"  # Should be int
        }
        
        metadata = {"workflow_id": 1}
        
        # Should handle gracefully and return error
        result = generator.generate_from_workflow(malformed_workflow, metadata)
        
        # Should fail gracefully
        assert result["success"] is False
        assert "error" in result
    
    def test_missing_metadata_handling(self, sample_parsed_workflow):
        """Test handling of missing metadata."""
        generator = StrategyGenerator()
        
        # Empty metadata
        result = generator.generate_from_workflow(sample_parsed_workflow, {})
        
        # Should still generate code with defaults
        assert result["success"] is True
        assert "workflow_id" in result["strategy_code"]  # Should handle missing ID
    
    def test_invalid_indicator_types(self):
        """Test handling of invalid indicator types."""
        generator = StrategyGenerator()
        
        invalid_indicators = [{
            "id": "unknown-1",
            "indicator_type": "unknown_indicator",
            "period": 14,
            "node_type": "technicalIndicator"
        }]
        
        code = generator._generate_indicator_calculations(invalid_indicators)
        
        # Should handle unknown indicators gracefully
        assert code is not None
        assert isinstance(code, str)
    
    def test_code_validation_failure_handling(self):
        """Test handling of code validation failures."""
        generator = StrategyGenerator()
        
        # Mock validation to return failure
        with patch.object(generator, '_validate_generated_code') as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "syntax_valid": False,
                "error": "Syntax error in generated code"
            }
            
            result = generator.generate_from_workflow({
                "data_sources": [],
                "technical_indicators": [],
                "conditions": [],
                "actions": [],
                "risk_management": [],
                "logic_components": [],
                "execution_graph": {},
                "complexity_score": 0
            }, {"workflow_id": 1})
            
            # Should still return result but with validation failure
            assert result["success"] is True
            assert result["validation"]["valid"] is False


class TestHighLevelFunctions:
    """Test high-level utility functions."""
    
    def test_generate_strategy_from_workflow_definition(self):
        """Test high-level strategy generation function."""
        workflow_definition = {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {"id": "rsi-1", "type": "technicalIndicator", "data": {"indicator": "rsi", "period": 14}},
                {"id": "condition-1", "type": "condition", "data": {"threshold": 30, "operator": "<"}},
                {"id": "action-1", "type": "action", "data": {"action": "buy", "quantity": 100}}
            ],
            "edges": [
                {"source": "data-1", "target": "rsi-1"},
                {"source": "rsi-1", "target": "condition-1"},
                {"source": "condition-1", "target": "action-1"}
            ]
        }
        
        metadata = {"workflow_id": 123, "workflow_name": "Test Strategy"}
        
        with patch('services.strategy_generator.WorkflowParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_workflow.return_value = {
                "data_sources": [{"symbol": "BTCUSDT"}],
                "technical_indicators": [{"indicator_type": "rsi", "period": 14}],
                "conditions": [{"operator": "<", "threshold": 30}],
                "actions": [{"action_type": "buy", "quantity": 100}],
                "risk_management": [],
                "logic_components": [],
                "execution_graph": {},
                "complexity_score": 10
            }
            
            result = generate_strategy_from_workflow_definition(workflow_definition, metadata)
            
            # Verify parsing was called
            mock_parser.parse_workflow.assert_called_once_with(workflow_definition)
            
            # Verify strategy generation
            assert result["success"] is True
            assert "strategy_code" in result
    
    def test_high_level_function_error_handling(self):
        """Test error handling in high-level function."""
        invalid_workflow = None
        metadata = {}
        
        result = generate_strategy_from_workflow_definition(invalid_workflow, metadata)
        
        assert result["success"] is False
        assert "error" in result
        assert result["strategy_code"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])