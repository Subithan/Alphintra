"""
Workflow definition parser for converting no-code workflows to training configurations.
Handles parsing of visual workflow nodes/edges into ML-ready data structures.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """Supported workflow node types."""
    DATA_SOURCE = "dataSource"
    TECHNICAL_INDICATOR = "technicalIndicator" 
    CONDITION = "condition"
    ACTION = "action"
    RISK = "risk"
    LOGIC = "logic"


class ValidationError(Exception):
    """Workflow validation error."""
    pass


class WorkflowParser:
    """
    Parser for converting visual workflow definitions to ML training configurations.
    Validates workflow structure and extracts training-relevant information.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Node type handlers
        self._node_handlers = {
            NodeType.DATA_SOURCE: self._parse_data_source_node,
            NodeType.TECHNICAL_INDICATOR: self._parse_indicator_node,
            NodeType.CONDITION: self._parse_condition_node,
            NodeType.ACTION: self._parse_action_node,
            NodeType.RISK: self._parse_risk_node,
            NodeType.LOGIC: self._parse_logic_node
        }
    
    def parse_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse complete workflow definition into training-ready format.
        
        Args:
            workflow_definition: Visual workflow with nodes/edges
            
        Returns:
            Dict containing parsed workflow components
            
        Raises:
            ValidationError: If workflow is invalid
        """
        try:
            self.logger.info("Starting workflow parsing")
            
            # Extract and validate basic structure
            nodes = workflow_definition.get("nodes", [])
            edges = workflow_definition.get("edges", [])
            
            if not nodes:
                raise ValidationError("Workflow must contain at least one node")
            
            # Parse individual components
            data_sources = self.parse_data_sources(nodes)
            indicators = self.parse_indicators(nodes)
            conditions = self.parse_conditions(nodes)
            actions = self.parse_actions(nodes)
            risk_nodes = self.parse_risk_nodes(nodes)
            logic_nodes = self.parse_logic_nodes(nodes)
            
            # Validate workflow completeness
            self._validate_workflow_completeness(data_sources, indicators, conditions, actions)
            
            # Build execution graph
            execution_graph = self._build_execution_graph(nodes, edges)
            
            parsed_workflow = {
                "data_sources": data_sources,
                "technical_indicators": indicators,
                "conditions": conditions,
                "actions": actions,
                "risk_management": risk_nodes,
                "logic_components": logic_nodes,
                "execution_graph": execution_graph,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "complexity_score": self._calculate_complexity_score(nodes, edges)
            }
            
            self.logger.info(f"Workflow parsing completed successfully. Nodes: {len(nodes)}, Complexity: {parsed_workflow['complexity_score']}")
            return parsed_workflow
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error parsing workflow: {str(e)}")
            raise ValidationError(f"Workflow parsing failed: {str(e)}")
    
    def parse_data_sources(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse data source nodes from workflow."""
        try:
            data_sources = []
            for node in nodes:
                if node.get("type") == NodeType.DATA_SOURCE:
                    parsed_source = self._parse_data_source_node(node)
                    data_sources.append(parsed_source)
            
            if not data_sources:
                raise ValidationError("Workflow must contain at least one data source")
            
            self.logger.debug(f"Parsed {len(data_sources)} data sources")
            return data_sources
            
        except Exception as e:
            raise ValidationError(f"Error parsing data sources: {str(e)}")
    
    def parse_indicators(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse technical indicator nodes from workflow."""
        try:
            indicators = []
            for node in nodes:
                if node.get("type") == NodeType.TECHNICAL_INDICATOR:
                    parsed_indicator = self._parse_indicator_node(node)
                    indicators.append(parsed_indicator)
            
            self.logger.debug(f"Parsed {len(indicators)} technical indicators")
            return indicators
            
        except Exception as e:
            raise ValidationError(f"Error parsing indicators: {str(e)}")
    
    def parse_conditions(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse condition nodes from workflow."""
        try:
            conditions = []
            for node in nodes:
                if node.get("type") == NodeType.CONDITION:
                    parsed_condition = self._parse_condition_node(node)
                    conditions.append(parsed_condition)
            
            self.logger.debug(f"Parsed {len(conditions)} conditions")
            return conditions
            
        except Exception as e:
            raise ValidationError(f"Error parsing conditions: {str(e)}")
    
    def parse_actions(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse action nodes from workflow."""
        try:
            actions = []
            for node in nodes:
                if node.get("type") == NodeType.ACTION:
                    parsed_action = self._parse_action_node(node)
                    actions.append(parsed_action)
            
            if not actions:
                raise ValidationError("Workflow must contain at least one action")
            
            self.logger.debug(f"Parsed {len(actions)} actions")
            return actions
            
        except Exception as e:
            raise ValidationError(f"Error parsing actions: {str(e)}")
    
    def parse_risk_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse risk management nodes from workflow."""
        try:
            risk_nodes = []
            for node in nodes:
                if node.get("type") == NodeType.RISK:
                    parsed_risk = self._parse_risk_node(node)
                    risk_nodes.append(parsed_risk)
            
            self.logger.debug(f"Parsed {len(risk_nodes)} risk management nodes")
            return risk_nodes
            
        except Exception as e:
            raise ValidationError(f"Error parsing risk nodes: {str(e)}")
    
    def parse_logic_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse logic nodes (AND/OR/NOT) from workflow."""
        try:
            logic_nodes = []
            for node in nodes:
                if node.get("type") == NodeType.LOGIC:
                    parsed_logic = self._parse_logic_node(node)
                    logic_nodes.append(parsed_logic)
            
            self.logger.debug(f"Parsed {len(logic_nodes)} logic nodes")
            return logic_nodes
            
        except Exception as e:
            raise ValidationError(f"Error parsing logic nodes: {str(e)}")
    
    # Private node parsing methods
    def _parse_data_source_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual data source node."""
        node_data = node.get("data", {})
        
        return {
            "id": node.get("id"),
            "symbol": node_data.get("symbol", "BTCUSDT"),
            "timeframe": node_data.get("timeframe", "1h"),
            "exchange": node_data.get("exchange", "binance"),
            "data_type": node_data.get("data_type", "ohlcv"),
            "lookback_periods": node_data.get("lookback_periods", 100),
            "required_features": ["open", "high", "low", "close", "volume"],
            "node_type": NodeType.DATA_SOURCE
        }
    
    def _parse_indicator_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual technical indicator node."""
        node_data = node.get("data", {})
        indicator_type = node_data.get("indicator", "sma")
        
        # Common parameters for all indicators
        base_config = {
            "id": node.get("id"),
            "indicator_type": indicator_type,
            "parameters": node_data.get("parameters", {}),
            "node_type": NodeType.TECHNICAL_INDICATOR
        }
        
        # Indicator-specific parsing
        if indicator_type in ["sma", "ema", "wma"]:
            base_config.update({
                "period": node_data.get("period", 20),
                "source": node_data.get("source", "close"),
                "outputs": [f"{indicator_type}_output"]
            })
        elif indicator_type == "rsi":
            base_config.update({
                "period": node_data.get("period", 14),
                "source": node_data.get("source", "close"),
                "outputs": ["rsi_output"]
            })
        elif indicator_type == "macd":
            base_config.update({
                "fast_period": node_data.get("fast_period", 12),
                "slow_period": node_data.get("slow_period", 26),
                "signal_period": node_data.get("signal_period", 9),
                "outputs": ["macd_output", "signal_output", "histogram_output"]
            })
        elif indicator_type == "bollinger_bands":
            base_config.update({
                "period": node_data.get("period", 20),
                "std_dev": node_data.get("std_dev", 2),
                "outputs": ["upper_output", "middle_output", "lower_output", "width_output"]
            })
        elif indicator_type == "adx":
            base_config.update({
                "period": node_data.get("period", 14),
                "outputs": ["adx_output", "di_plus_output", "di_minus_output"]
            })
        
        return base_config
    
    def _parse_condition_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual condition node."""
        node_data = node.get("data", {})
        
        return {
            "id": node.get("id"),
            "condition_type": node_data.get("condition_type", "threshold"),
            "operator": node_data.get("operator", ">"),
            "threshold": node_data.get("threshold", 0),
            "left_operand": node_data.get("left_operand"),
            "right_operand": node_data.get("right_operand"),
            "comparison_mode": node_data.get("comparison_mode", "value"),  # value, cross_above, cross_below
            "node_type": NodeType.CONDITION,
            "optimization_target": True  # Conditions are optimization targets
        }
    
    def _parse_action_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual action node."""
        node_data = node.get("data", {})
        action_type = node_data.get("action", "buy")
        
        return {
            "id": node.get("id"),
            "action_type": action_type,
            "signal": node_data.get("signal", action_type),
            "quantity": node_data.get("quantity", 100),
            "order_type": node_data.get("order_type", "market"),
            "price_offset": node_data.get("price_offset", 0),
            "stop_loss": node_data.get("stop_loss"),
            "take_profit": node_data.get("take_profit"),
            "node_type": NodeType.ACTION
        }
    
    def _parse_risk_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual risk management node."""
        node_data = node.get("data", {})
        
        return {
            "id": node.get("id"),
            "risk_type": node_data.get("risk_type", "position_size"),
            "max_position_size": node_data.get("max_position_size", 0.1),
            "stop_loss_percentage": node_data.get("stop_loss_percentage", 0.02),
            "take_profit_percentage": node_data.get("take_profit_percentage", 0.04),
            "max_daily_trades": node_data.get("max_daily_trades", 10),
            "max_drawdown": node_data.get("max_drawdown", 0.05),
            "node_type": NodeType.RISK
        }
    
    def _parse_logic_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual logic node (AND/OR/NOT)."""
        node_data = node.get("data", {})
        
        return {
            "id": node.get("id"),
            "logic_type": node_data.get("logic", "AND"),
            "inputs": node_data.get("inputs", []),
            "node_type": NodeType.LOGIC
        }
    
    def _validate_workflow_completeness(self, data_sources: List, indicators: List, 
                                       conditions: List, actions: List) -> None:
        """Validate that workflow has all required components."""
        if not data_sources:
            raise ValidationError("Workflow requires at least one data source")
        
        if not actions:
            raise ValidationError("Workflow requires at least one action")
        
        # Optional but recommended components
        if not indicators and not conditions:
            self.logger.warning("Workflow has no indicators or conditions - strategy may be too simple")
    
    def _build_execution_graph(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, List[str]]:
        """Build execution dependency graph from nodes and edges."""
        graph = {}
        
        # Initialize all nodes
        for node in nodes:
            graph[node["id"]] = []
        
        # Add edges (dependencies)
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            
            if source and target and target in graph:
                graph[target].append(source)
        
        return graph
    
    def _calculate_complexity_score(self, nodes: List[Dict], edges: List[Dict]) -> int:
        """Calculate workflow complexity score for resource allocation."""
        base_score = len(nodes) * 2 + len(edges)
        
        # Additional complexity for specific node types
        complexity_multipliers = {
            NodeType.TECHNICAL_INDICATOR: 3,
            NodeType.CONDITION: 2,
            NodeType.LOGIC: 2,
            NodeType.RISK: 1,
            NodeType.ACTION: 1,
            NodeType.DATA_SOURCE: 1
        }
        
        node_complexity = sum(
            complexity_multipliers.get(node.get("type"), 1) 
            for node in nodes
        )
        
        return base_score + node_complexity


def validate_workflow_for_training(workflow_definition: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate workflow suitability for ML training.
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        parser = WorkflowParser()
        parsed = parser.parse_workflow(workflow_definition)
        
        errors = []
        
        # Check minimum requirements for training
        if len(parsed["data_sources"]) == 0:
            errors.append("Training requires at least one data source")
        
        if len(parsed["actions"]) == 0:
            errors.append("Training requires at least one action for signal generation")
        
        if len(parsed["technical_indicators"]) == 0 and len(parsed["conditions"]) == 0:
            errors.append("Training requires indicators or conditions for feature engineering")
        
        # Check complexity requirements
        if parsed["complexity_score"] < 5:
            errors.append("Workflow too simple for meaningful ML training")
        
        if parsed["complexity_score"] > 100:
            errors.append("Workflow too complex - consider simplifying for training")
        
        return len(errors) == 0, errors
        
    except ValidationError as e:
        return False, [str(e)]
    except Exception as e:
        return False, [f"Validation failed: {str(e)}"]