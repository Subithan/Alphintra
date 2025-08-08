"""
Workflow-to-Training Converter

Converts visual React Flow workflows to AI-ML training configurations.
This handles the transformation from no-code visual definitions to 
machine learning training parameters.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Supported node types for workflow conversion"""
    DATA_SOURCE = "dataSource"
    TECHNICAL_INDICATOR = "technicalIndicator" 
    CONDITION = "condition"
    ACTION = "action"
    RISK = "risk"
    LOGIC = "logic"
    OUTPUT = "output"
    CUSTOM_DATASET = "customDataset"


@dataclass
class TrainingConfig:
    """Training configuration generated from workflow"""
    dataset_requirements: Dict[str, Any]
    feature_engineering: List[Dict[str, Any]]
    target_generation: Dict[str, Any]
    optimization_targets: List[str]
    constraints: Dict[str, Any]
    strategy_name: str
    estimated_complexity: str  # 'low', 'medium', 'high'
    
    
@dataclass 
class NodeMapping:
    """Mapping result for a single node"""
    node_id: str
    node_type: str
    config: Dict[str, Any]
    dependencies: List[str]  # IDs of nodes this depends on


class WorkflowConverter:
    """Converts visual workflows to ML training configurations"""
    
    def __init__(self):
        self.supported_indicators = {
            'sma', 'ema', 'rsi', 'macd', 'bollinger_bands', 
            'stochastic', 'adx', 'cci', 'williams_r'
        }
        self.supported_conditions = {
            'greater_than', 'less_than', 'equals', 'cross_above', 
            'cross_below', 'between', 'outside_range'
        }
        
    def convert_to_training_config(self, workflow_data: Dict[str, Any]) -> TrainingConfig:
        """
        Convert workflow data to training configuration
        
        Args:
            workflow_data: React Flow workflow with nodes and edges
            
        Returns:
            TrainingConfig object for AI-ML service
        """
        try:
            nodes = workflow_data.get('nodes', [])
            edges = workflow_data.get('edges', [])
            
            logger.info(f"Converting workflow with {len(nodes)} nodes and {len(edges)} edges")
            
            # Validate workflow has required node types
            self._validate_workflow_for_training(nodes)
            
            # Map nodes by type
            node_mappings = self._map_nodes(nodes, edges)
            
            # Extract training components
            dataset_requirements = self._extract_dataset_requirements(node_mappings)
            feature_engineering = self._extract_feature_engineering(node_mappings)
            target_generation = self._extract_target_generation(node_mappings)
            optimization_targets = self._extract_optimization_targets(node_mappings)
            constraints = self._extract_constraints(node_mappings)
            
            # Assess complexity
            complexity = self._assess_complexity(node_mappings)
            
            return TrainingConfig(
                dataset_requirements=dataset_requirements,
                feature_engineering=feature_engineering,
                target_generation=target_generation,
                optimization_targets=optimization_targets,
                constraints=constraints,
                strategy_name=workflow_data.get('name', 'Unnamed Strategy'),
                estimated_complexity=complexity
            )
            
        except Exception as e:
            logger.error(f"Error converting workflow to training config: {str(e)}")
            raise ValueError(f"Failed to convert workflow: {str(e)}")
    
    def _validate_workflow_for_training(self, nodes: List[Dict[str, Any]]) -> None:
        """Validate workflow has required components for ML training"""
        node_types = [node.get('type') for node in nodes]
        
        # Must have at least one data source
        if not any(nt in [NodeType.DATA_SOURCE.value, NodeType.CUSTOM_DATASET.value] for nt in node_types):
            raise ValueError("Workflow must include at least one data source for training")
        
        # Must have at least one condition for target generation
        if NodeType.CONDITION.value not in node_types:
            raise ValueError("Workflow must include at least one condition for target generation")
            
        # Should have technical indicators for features
        if NodeType.TECHNICAL_INDICATOR.value not in node_types:
            logger.warning("Workflow has no technical indicators - may limit model features")
    
    def _map_nodes(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[NodeMapping]:
        """Map workflow nodes to training components"""
        mappings = []
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(edges)
        
        for node in nodes:
            node_id = node.get('id')
            node_type = node.get('type')
            node_data = node.get('data', {})
            
            if not node_id or not node_type:
                logger.warning(f"Skipping malformed node: {node}")
                continue
            
            mapping = NodeMapping(
                node_id=node_id,
                node_type=node_type,
                config=node_data,
                dependencies=dependencies.get(node_id, [])
            )
            mappings.append(mapping)
            
        return mappings
    
    def _build_dependency_graph(self, edges: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build dependency graph from edges"""
        dependencies = {}
        
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            
            if source and target:
                if target not in dependencies:
                    dependencies[target] = []
                dependencies[target].append(source)
                
        return dependencies
    
    def _extract_dataset_requirements(self, mappings: List[NodeMapping]) -> Dict[str, Any]:
        """Extract dataset requirements from data source nodes"""
        requirements = {
            'symbols': [],
            'timeframes': [],
            'data_types': ['ohlcv'],  # Default to OHLCV data
            'lookback_period': 252,  # Default 1 year
            'features_required': []
        }
        
        for mapping in mappings:
            if mapping.node_type == NodeType.DATA_SOURCE.value:
                config = mapping.config
                
                # Extract symbol
                if 'symbol' in config:
                    requirements['symbols'].append(config['symbol'])
                
                # Extract timeframe
                if 'timeframe' in config:
                    requirements['timeframes'].append(config['timeframe'])
                    
            elif mapping.node_type == NodeType.CUSTOM_DATASET.value:
                config = mapping.config
                
                # Handle custom dataset
                requirements['custom_dataset'] = {
                    'dataset_id': config.get('dataset_id'),
                    'name': config.get('name'),
                    'type': config.get('type', 'uploaded')
                }
        
        # Remove duplicates
        requirements['symbols'] = list(set(requirements['symbols']))
        requirements['timeframes'] = list(set(requirements['timeframes']))
        
        return requirements
    
    def _extract_feature_engineering(self, mappings: List[NodeMapping]) -> List[Dict[str, Any]]:
        """Extract feature engineering pipeline from indicator nodes"""
        features = []
        
        for mapping in mappings:
            if mapping.node_type == NodeType.TECHNICAL_INDICATOR.value:
                config = mapping.config
                indicator_type = config.get('indicatorType', config.get('type', 'unknown'))
                
                if indicator_type in self.supported_indicators:
                    feature = {
                        'type': 'technical_indicator',
                        'indicator': indicator_type,
                        'parameters': self._extract_indicator_parameters(config),
                        'output_name': f"feature_{mapping.node_id}",
                        'dependencies': mapping.dependencies
                    }
                    features.append(feature)
                else:
                    logger.warning(f"Unsupported indicator type: {indicator_type}")
                    
        return features
    
    def _extract_indicator_parameters(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for technical indicators"""
        parameters = {}
        
        # Common parameters
        if 'period' in config:
            parameters['period'] = config['period']
        if 'fast_period' in config:
            parameters['fast_period'] = config['fast_period']
        if 'slow_period' in config:
            parameters['slow_period'] = config['slow_period']
        if 'signal_period' in config:
            parameters['signal_period'] = config['signal_period']
        if 'std_dev' in config:
            parameters['std_dev'] = config['std_dev']
            
        return parameters
    
    def _extract_target_generation(self, mappings: List[NodeMapping]) -> Dict[str, Any]:
        """Extract target generation logic from condition nodes"""
        targets = []
        
        for mapping in mappings:
            if mapping.node_type == NodeType.CONDITION.value:
                config = mapping.config
                condition_type = config.get('conditionType', config.get('type', 'unknown'))
                
                if condition_type in self.supported_conditions:
                    target = {
                        'type': 'condition',
                        'condition': condition_type,
                        'parameters': {
                            'threshold': config.get('threshold', config.get('value', 0)),
                            'operator': config.get('operator', condition_type)
                        },
                        'target_name': f"target_{mapping.node_id}",
                        'dependencies': mapping.dependencies
                    }
                    targets.append(target)
        
        return {
            'targets': targets,
            'target_type': 'classification',  # Default to classification
            'primary_target': targets[0]['target_name'] if targets else None
        }
    
    def _extract_optimization_targets(self, mappings: List[NodeMapping]) -> List[str]:
        """Extract optimization targets from action nodes"""
        targets = ['profit']  # Default optimization target
        
        for mapping in mappings:
            if mapping.node_type == NodeType.ACTION.value:
                config = mapping.config
                action_type = config.get('actionType', config.get('type'))
                
                if action_type in ['buy', 'sell']:
                    # Add signal accuracy as optimization target
                    targets.append('signal_accuracy')
                elif action_type in ['stop_loss', 'take_profit']:
                    # Add risk-adjusted returns
                    targets.append('sharpe_ratio')
                    
        return list(set(targets))  # Remove duplicates
    
    def _extract_constraints(self, mappings: List[NodeMapping]) -> Dict[str, Any]:
        """Extract training constraints from risk nodes"""
        constraints = {
            'max_drawdown': 0.2,  # Default 20% max drawdown
            'min_sharpe_ratio': 1.0,  # Default minimum Sharpe ratio
            'max_trades_per_day': None,
            'position_sizing': 'fixed'
        }
        
        for mapping in mappings:
            if mapping.node_type == NodeType.RISK.value:
                config = mapping.config
                
                # Extract risk parameters
                if 'max_drawdown' in config:
                    constraints['max_drawdown'] = config['max_drawdown'] / 100
                if 'stop_loss_percent' in config:
                    constraints['stop_loss'] = config['stop_loss_percent'] / 100
                if 'take_profit_percent' in config:
                    constraints['take_profit'] = config['take_profit_percent'] / 100
                if 'position_size' in config:
                    constraints['position_sizing'] = config['position_size']
                    
        return constraints
    
    def _assess_complexity(self, mappings: List[NodeMapping]) -> str:
        """Assess workflow complexity for training resource allocation"""
        total_nodes = len(mappings)
        indicator_nodes = len([m for m in mappings if m.node_type == NodeType.TECHNICAL_INDICATOR.value])
        condition_nodes = len([m for m in mappings if m.node_type == NodeType.CONDITION.value])
        
        # Simple complexity heuristic
        if total_nodes <= 5 and indicator_nodes <= 2:
            return 'low'
        elif total_nodes <= 15 and indicator_nodes <= 8:
            return 'medium'
        else:
            return 'high'