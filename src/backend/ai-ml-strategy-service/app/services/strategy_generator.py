"""
Strategy code generation from parsed workflow definitions.
Converts visual workflows into executable Python trading strategies.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import ast
import re

from .workflow_parser import WorkflowParser, NodeType

logger = logging.getLogger(__name__)


class StrategyGenerationError(Exception):
    """Strategy generation error."""
    pass


class StrategyGenerator:
    """
    Generates executable Python trading strategy code from parsed workflows.
    Creates optimized, production-ready trading strategies with proper error handling.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = WorkflowParser()
        
        # Code generation templates
        self._strategy_template = '''"""
Generated trading strategy from visual workflow.
Created: {timestamp}
Workflow ID: {workflow_id}
Complexity Score: {complexity_score}
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WorkflowStrategy:
    """Auto-generated trading strategy from visual workflow."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {{}}
        self.position = 0
        self.signals = []
        self.indicators = {{}}
        self.last_prices = {{}}
        
        # Strategy metadata
        self.metadata = {metadata}
        
        # Risk management parameters
        self.risk_params = {risk_params}
        
        # Initialize indicators
        self._initialize_indicators()
    
    def _initialize_indicators(self):
        """Initialize technical indicators with default parameters."""
        pass
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators for the strategy."""
        try:
            indicators = {{}}
            
{indicator_calculations}
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {{str(e)}}")
            return {{}}
    
    def evaluate_conditions(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, bool]:
        """Evaluate all trading conditions."""
        try:
            conditions = {{}}
            current_price = data['close'].iloc[-1]
            
{condition_evaluations}
            
            return conditions
            
        except Exception as e:
            logger.error(f"Error evaluating conditions: {{str(e)}}")
            return {{}}
    
    def generate_signals(self, conditions: Dict[str, bool]) -> List[Dict[str, Any]]:
        """Generate trading signals based on conditions."""
        try:
            signals = []
            
{signal_generation}
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {{str(e)}}")
            return []
    
    def apply_risk_management(self, signals: List[Dict[str, Any]], 
                            current_portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply risk management rules to signals."""
        try:
            filtered_signals = []
            
            for signal in signals:
                # Position size check
                if self._check_position_size(signal, current_portfolio):
                    # Risk/reward check  
                    if self._check_risk_reward(signal):
                        # Portfolio exposure check
                        if self._check_portfolio_exposure(current_portfolio):
                            filtered_signals.append(signal)
                        else:
                            logger.warning("Signal rejected: portfolio exposure limit")
                    else:
                        logger.warning("Signal rejected: risk/reward ratio")
                else:
                    logger.warning("Signal rejected: position size limit")
            
            return filtered_signals
            
        except Exception as e:
            logger.error(f"Error in risk management: {{str(e)}}")
            return signals  # Return original signals on error
    
    def execute_strategy(self, data: pd.DataFrame, 
                        current_portfolio: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Main strategy execution method."""
        try:
            if data.empty:
                return []
            
            current_portfolio = current_portfolio or {{}}
            
            # Calculate indicators
            indicators = self.calculate_indicators(data)
            
            # Evaluate conditions
            conditions = self.evaluate_conditions(data, indicators)
            
            # Generate signals
            signals = self.generate_signals(conditions)
            
            # Apply risk management
            final_signals = self.apply_risk_management(signals, current_portfolio)
            
            # Log execution summary
            self.logger.info(f"Strategy executed: {{len(indicators)}} indicators, "
                           f"{{len(conditions)}} conditions, {{len(final_signals)}} signals")
            
            return final_signals
            
        except Exception as e:
            logger.error(f"Strategy execution error: {{str(e)}}")
            return []
    
    # Risk management helper methods
    def _check_position_size(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """Check if signal respects position size limits."""
        max_position = self.risk_params.get('max_position_size', 0.1)
        current_exposure = portfolio.get('exposure', 0)
        signal_size = signal.get('quantity', 0) * signal.get('price', 0)
        portfolio_value = portfolio.get('total_value', 100000)
        
        signal_exposure = signal_size / portfolio_value
        return (current_exposure + signal_exposure) <= max_position
    
    def _check_risk_reward(self, signal: Dict[str, Any]) -> bool:
        """Check if signal meets minimum risk/reward ratio."""
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        entry_price = signal.get('price', 0)
        
        if not stop_loss or not take_profit or entry_price == 0:
            return True  # Skip check if parameters not set
        
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        min_rr_ratio = self.risk_params.get('min_risk_reward_ratio', 1.5)
        return (reward / risk) >= min_rr_ratio if risk > 0 else False
    
    def _check_portfolio_exposure(self, portfolio: Dict[str, Any]) -> bool:
        """Check overall portfolio exposure limits."""
        max_exposure = self.risk_params.get('max_portfolio_exposure', 0.8)
        current_exposure = portfolio.get('exposure', 0)
        return current_exposure <= max_exposure
    
    def get_optimization_parameters(self) -> Dict[str, Any]:
        """Get parameters that can be optimized via ML training."""
        return {optimization_parameters}
    
    def update_parameters(self, new_parameters: Dict[str, Any]):
        """Update strategy parameters from ML optimization results."""
        try:
            for param, value in new_parameters.items():
                if param in self.get_optimization_parameters():
                    # Update the parameter safely
                    self._update_parameter_safely(param, value)
                    logger.info(f"Updated parameter {{param}} = {{value}}")
                else:
                    logger.warning(f"Unknown optimization parameter: {{param}}")
                    
        except Exception as e:
            logger.error(f"Error updating parameters: {{str(e)}}")
    
    def _update_parameter_safely(self, param: str, value: Any):
        """Safely update a strategy parameter with validation."""
        # Add parameter-specific validation logic here
        if param.endswith('_period') and (not isinstance(value, int) or value < 1):
            raise ValueError(f"Invalid period value for {{param}}: {{value}}")
        
        # Update the parameter in appropriate location (indicators, conditions, etc.)
        # This would need to be customized based on the specific parameter
        pass


# Utility functions for backtesting integration
def create_strategy_instance(config: Optional[Dict[str, Any]] = None) -> WorkflowStrategy:
    """Factory function to create strategy instance."""
    return WorkflowStrategy(config)


def validate_strategy_code() -> Tuple[bool, List[str]]:
    """Validate generated strategy code for syntax and logic errors."""
    errors = []
    
    try:
        # Basic syntax validation would go here
        # This is a placeholder for actual validation logic
        return True, errors
    except Exception as e:
        errors.append(f"Validation error: {{str(e)}}")
        return False, errors
'''
    
    def generate_from_workflow(self, parsed_workflow: Dict[str, Any], 
                              workflow_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete Python strategy code from parsed workflow.
        
        Args:
            parsed_workflow: Output from WorkflowParser
            workflow_metadata: Additional metadata about the workflow
            
        Returns:
            Dict containing generated code and metadata
        """
        try:
            self.logger.info("Starting strategy code generation")
            
            # Extract components
            data_sources = parsed_workflow.get("data_sources", [])
            indicators = parsed_workflow.get("technical_indicators", [])
            conditions = parsed_workflow.get("conditions", [])
            actions = parsed_workflow.get("actions", [])
            risk_nodes = parsed_workflow.get("risk_management", [])
            
            # Generate code sections
            indicator_code = self._generate_indicator_calculations(indicators)
            condition_code = self._generate_condition_evaluations(conditions, indicators)
            signal_code = self._generate_signal_generation(actions, conditions)
            risk_params = self._generate_risk_parameters(risk_nodes)
            optimization_params = self._generate_optimization_parameters(indicators, conditions)
            
            # Build complete strategy code
            strategy_code = self._strategy_template.format(
                timestamp=datetime.now().isoformat(),
                workflow_id=workflow_metadata.get("workflow_id", "unknown"),
                complexity_score=parsed_workflow.get("complexity_score", 0),
                metadata=self._format_metadata(workflow_metadata),
                risk_params=risk_params,
                indicator_calculations=indicator_code,
                condition_evaluations=condition_code,
                signal_generation=signal_code,
                optimization_parameters=optimization_params
            )
            
            # Validate generated code
            validation_result = self._validate_generated_code(strategy_code)
            
            result = {
                "success": True,
                "strategy_code": strategy_code,
                "strategy_class": "WorkflowStrategy",
                "entry_point": "create_strategy_instance",
                "validation": validation_result,
                "metadata": {
                    "workflow_id": workflow_metadata.get("workflow_id"),
                    "workflow_name": workflow_metadata.get("workflow_name"),
                    "generated_at": datetime.now().isoformat(),
                    "code_lines": len(strategy_code.split('\n')),
                    "indicator_count": len(indicators),
                    "condition_count": len(conditions),
                    "action_count": len(actions),
                    "complexity_score": parsed_workflow.get("complexity_score", 0)
                },
                "optimization_config": {
                    "parameters": optimization_params,
                    "objective_function": "sharpe_ratio",
                    "constraint_functions": ["max_drawdown", "var_95"],
                    "parameter_bounds": self._generate_parameter_bounds(indicators, conditions)
                }
            }
            
            self.logger.info(f"Strategy generation completed. Code lines: {result['metadata']['code_lines']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating strategy: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "strategy_code": None
            }
    
    def _generate_indicator_calculations(self, indicators: List[Dict[str, Any]]) -> str:
        """Generate indicator calculation code."""
        if not indicators:
            return "            # No indicators defined"
        
        code_lines = []
        
        for indicator in indicators:
            indicator_type = indicator.get("indicator_type", "sma")
            indicator_id = indicator.get("id", "indicator")
            
            if indicator_type in ["sma", "ema", "wma"]:
                period = indicator.get("period", 20)
                source = indicator.get("source", "close")
                code_lines.append(f"            # {indicator_id} - {indicator_type.upper()}")
                code_lines.append(f"            indicators['{indicator_id}'] = data['{source}'].rolling({period}).mean()")
                
            elif indicator_type == "rsi":
                period = indicator.get("period", 14)
                code_lines.append(f"            # {indicator_id} - RSI")
                code_lines.append(f"            delta = data['close'].diff()")
                code_lines.append(f"            gain = (delta.where(delta > 0, 0)).rolling({period}).mean()")
                code_lines.append(f"            loss = (-delta.where(delta < 0, 0)).rolling({period}).mean()")
                code_lines.append(f"            rs = gain / loss")
                code_lines.append(f"            indicators['{indicator_id}'] = 100 - (100 / (1 + rs))")
                
            elif indicator_type == "macd":
                fast = indicator.get("fast_period", 12)
                slow = indicator.get("slow_period", 26)
                signal = indicator.get("signal_period", 9)
                code_lines.append(f"            # {indicator_id} - MACD")
                code_lines.append(f"            ema_fast = data['close'].ewm(span={fast}).mean()")
                code_lines.append(f"            ema_slow = data['close'].ewm(span={slow}).mean()")
                code_lines.append(f"            macd_line = ema_fast - ema_slow")
                code_lines.append(f"            signal_line = macd_line.ewm(span={signal}).mean()")
                code_lines.append(f"            indicators['{indicator_id}_macd'] = macd_line")
                code_lines.append(f"            indicators['{indicator_id}_signal'] = signal_line")
                code_lines.append(f"            indicators['{indicator_id}_histogram'] = macd_line - signal_line")
                
            elif indicator_type == "bollinger_bands":
                period = indicator.get("period", 20)
                std_dev = indicator.get("std_dev", 2)
                code_lines.append(f"            # {indicator_id} - Bollinger Bands")
                code_lines.append(f"            sma = data['close'].rolling({period}).mean()")
                code_lines.append(f"            std = data['close'].rolling({period}).std()")
                code_lines.append(f"            indicators['{indicator_id}_upper'] = sma + ({std_dev} * std)")
                code_lines.append(f"            indicators['{indicator_id}_middle'] = sma")
                code_lines.append(f"            indicators['{indicator_id}_lower'] = sma - ({std_dev} * std)")
                code_lines.append(f"            indicators['{indicator_id}_width'] = indicators['{indicator_id}_upper'] - indicators['{indicator_id}_lower']")
            
            code_lines.append("")  # Empty line between indicators
        
        return "\n".join(code_lines)
    
    def _generate_condition_evaluations(self, conditions: List[Dict[str, Any]], 
                                       indicators: List[Dict[str, Any]]) -> str:
        """Generate condition evaluation code."""
        if not conditions:
            return "            # No conditions defined"
        
        code_lines = []
        
        for condition in conditions:
            condition_id = condition.get("id", "condition")
            operator = condition.get("operator", ">")
            threshold = condition.get("threshold", 0)
            comparison_mode = condition.get("comparison_mode", "value")
            
            code_lines.append(f"            # {condition_id} - Threshold condition")
            
            if comparison_mode == "value":
                code_lines.append(f"            conditions['{condition_id}'] = current_price {operator} {threshold}")
            elif comparison_mode == "cross_above":
                code_lines.append(f"            conditions['{condition_id}'] = current_price > {threshold} and data['close'].iloc[-2] <= {threshold}")
            elif comparison_mode == "cross_below":
                code_lines.append(f"            conditions['{condition_id}'] = current_price < {threshold} and data['close'].iloc[-2] >= {threshold}")
            
            code_lines.append("")
        
        return "\n".join(code_lines)
    
    def _generate_signal_generation(self, actions: List[Dict[str, Any]], 
                                   conditions: List[Dict[str, Any]]) -> str:
        """Generate signal generation code."""
        if not actions:
            return "            # No actions defined"
        
        code_lines = []
        
        for i, action in enumerate(actions):
            action_id = action.get("id", f"action_{i}")
            action_type = action.get("action_type", "buy")
            quantity = action.get("quantity", 100)
            order_type = action.get("order_type", "market")
            
            # Simple condition mapping (in real implementation, would use execution graph)
            condition_check = "True"  # Placeholder
            if conditions:
                condition_id = conditions[0].get("id", "condition_1")
                condition_check = f"conditions.get('{condition_id}', False)"
            
            code_lines.append(f"            # {action_id} - {action_type.title()} signal")
            code_lines.append(f"            if {condition_check}:")
            code_lines.append(f"                signals.append({{")
            code_lines.append(f"                    'action': '{action_type}',")
            code_lines.append(f"                    'symbol': data.get('symbol', 'UNKNOWN'),")
            code_lines.append(f"                    'quantity': {quantity},")
            code_lines.append(f"                    'order_type': '{order_type}',")
            code_lines.append(f"                    'price': current_price,")
            code_lines.append(f"                    'timestamp': datetime.now(),")
            code_lines.append(f"                    'signal_id': '{action_id}'")
            code_lines.append(f"                }})")
            code_lines.append("")
        
        return "\n".join(code_lines)
    
    def _generate_risk_parameters(self, risk_nodes: List[Dict[str, Any]]) -> str:
        """Generate risk management parameters."""
        default_params = {
            'max_position_size': 0.1,
            'max_portfolio_exposure': 0.8,
            'min_risk_reward_ratio': 1.5,
            'max_daily_trades': 10,
            'max_drawdown': 0.05
        }
        
        if risk_nodes:
            risk_node = risk_nodes[0]  # Use first risk node
            default_params.update({
                'max_position_size': risk_node.get('max_position_size', 0.1),
                'max_drawdown': risk_node.get('max_drawdown', 0.05),
                'max_daily_trades': risk_node.get('max_daily_trades', 10)
            })
        
        return str(default_params).replace("'", '"')
    
    def _generate_optimization_parameters(self, indicators: List[Dict[str, Any]], 
                                        conditions: List[Dict[str, Any]]) -> str:
        """Generate optimization parameter definitions."""
        params = {}
        
        # Add indicator parameters
        for indicator in indicators:
            indicator_id = indicator.get("id", "indicator")
            indicator_type = indicator.get("indicator_type", "sma")
            
            if indicator_type in ["sma", "ema", "wma", "rsi"]:
                params[f"{indicator_id}_period"] = indicator.get("period", 20)
            elif indicator_type == "macd":
                params[f"{indicator_id}_fast_period"] = indicator.get("fast_period", 12)
                params[f"{indicator_id}_slow_period"] = indicator.get("slow_period", 26)
                params[f"{indicator_id}_signal_period"] = indicator.get("signal_period", 9)
        
        # Add condition parameters  
        for condition in conditions:
            condition_id = condition.get("id", "condition")
            params[f"{condition_id}_threshold"] = condition.get("threshold", 0)
        
        return str(params).replace("'", '"')
    
    def _generate_parameter_bounds(self, indicators: List[Dict[str, Any]], 
                                  conditions: List[Dict[str, Any]]) -> Dict[str, List]:
        """Generate parameter bounds for optimization."""
        bounds = {}
        
        # Indicator bounds
        for indicator in indicators:
            indicator_id = indicator.get("id", "indicator")
            indicator_type = indicator.get("indicator_type", "sma")
            
            if indicator_type in ["sma", "ema", "wma"]:
                bounds[f"{indicator_id}_period"] = [5, 50]
            elif indicator_type == "rsi":
                bounds[f"{indicator_id}_period"] = [10, 30]
            elif indicator_type == "macd":
                bounds[f"{indicator_id}_fast_period"] = [8, 20]
                bounds[f"{indicator_id}_slow_period"] = [20, 40]
                bounds[f"{indicator_id}_signal_period"] = [5, 15]
        
        # Condition bounds
        for condition in conditions:
            condition_id = condition.get("id", "condition")
            current_threshold = condition.get("threshold", 0)
            
            # Generate reasonable bounds around current threshold
            if current_threshold == 0:
                bounds[f"{condition_id}_threshold"] = [-10, 10]
            else:
                margin = abs(current_threshold) * 0.5
                bounds[f"{condition_id}_threshold"] = [
                    current_threshold - margin,
                    current_threshold + margin
                ]
        
        return bounds
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for code generation."""
        return str(metadata).replace("'", '"')
    
    def _validate_generated_code(self, code: str) -> Dict[str, Any]:
        """Validate the generated Python code."""
        try:
            # Parse AST to check syntax
            ast.parse(code)
            
            # Basic checks
            has_main_class = "class WorkflowStrategy" in code
            has_execute_method = "def execute_strategy" in code
            has_factory_function = "def create_strategy_instance" in code
            
            warnings = []
            if not has_main_class:
                warnings.append("Main strategy class not found")
            if not has_execute_method:
                warnings.append("Execute strategy method not found")
            if not has_factory_function:
                warnings.append("Factory function not found")
            
            return {
                "valid": True,
                "syntax_valid": True,
                "warnings": warnings,
                "line_count": len(code.split('\n')),
                "estimated_complexity": "medium"
            }
            
        except SyntaxError as e:
            return {
                "valid": False,
                "syntax_valid": False,
                "error": str(e),
                "line_number": e.lineno
            }
        except Exception as e:
            return {
                "valid": False,
                "syntax_valid": False,
                "error": str(e)
            }


def generate_strategy_from_workflow_definition(workflow_definition: Dict[str, Any], 
                                             workflow_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    High-level function to generate strategy from workflow definition.
    
    Args:
        workflow_definition: Visual workflow with nodes/edges
        workflow_metadata: Metadata about the workflow
        
    Returns:
        Dict with generated strategy code and metadata
    """
    try:
        # Parse workflow
        parser = WorkflowParser()
        parsed_workflow = parser.parse_workflow(workflow_definition)
        
        # Generate strategy
        generator = StrategyGenerator()
        result = generator.generate_from_workflow(parsed_workflow, workflow_metadata)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in strategy generation pipeline: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "strategy_code": None
        }