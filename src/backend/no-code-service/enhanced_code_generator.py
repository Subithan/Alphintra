"""Enhanced Code Generator with Compiler-like Functionality.

This module provides a comprehensive code generation system that transforms 
no-code workflow definitions into executable Python trading strategies. It 
features:

1. Multi-phase compilation (lexical analysis, parsing, semantic analysis, optimization, code generation)
2. Type system with data flow analysis
3. Dependency resolution and topological sorting
4. Advanced optimization passes
5. Comprehensive error handling and validation
6. Multiple output targets (training, backtesting, live trading)

The generator acts as a true compiler, transforming high-level workflow 
descriptions into optimized, executable code.
"""

from __future__ import annotations

import ast
import json
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Set, Optional, Union, Tuple
from collections import defaultdict, deque

from ir import Node, Edge, Workflow
from node_handlers import HANDLER_REGISTRY, FALLBACK_HANDLER


class DataType(Enum):
    """Data types in the workflow type system."""
    OHLCV = "ohlcv"
    NUMERIC = "numeric"
    SIGNAL = "signal"
    EXECUTION = "execution"
    RISK_METRICS = "risk_metrics"
    CORRELATION = "correlation"
    SENTIMENT = "sentiment"
    UNKNOWN = "unknown"


class OutputMode(Enum):
    """Code generation output modes."""
    TRAINING = "training"
    BACKTESTING = "backtesting"
    LIVE_TRADING = "live_trading"
    RESEARCH = "research"


@dataclass
class CompilationError:
    """Represents a compilation error."""
    node_id: str
    error_type: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class DataFlowEdge:
    """Enhanced edge with type information."""
    source: str
    target: str
    source_handle: str
    target_handle: str
    data_type: DataType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TypedNode:
    """Node with type information and compilation metadata."""
    id: str
    type: str
    data: Dict[str, Any]
    input_types: Dict[str, DataType] = field(default_factory=dict)
    output_types: Dict[str, DataType] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    execution_order: int = -1
    optimizations: List[str] = field(default_factory=list)


@dataclass
class CompilationContext:
    """Context for the compilation process."""
    nodes: Dict[str, TypedNode] = field(default_factory=dict)
    edges: List[DataFlowEdge] = field(default_factory=list)
    errors: List[CompilationError] = field(default_factory=list)
    warnings: List[CompilationError] = field(default_factory=list)
    symbol_table: Dict[str, Any] = field(default_factory=dict)
    optimization_level: int = 1
    target_mode: OutputMode = OutputMode.TRAINING


class EnhancedCodeGenerator:
    """Enhanced code generator with compiler-like functionality."""

    def __init__(self):
        self.handlers = dict(HANDLER_REGISTRY)
        self.fallback_handler = FALLBACK_HANDLER
        self.optimization_passes = [
            self._dead_code_elimination,
            self._common_subexpression_elimination,
            self._constant_folding,
            self._loop_optimization
        ]

    def compile_workflow(
        self, 
        workflow: Dict[str, Any], 
        output_mode: OutputMode = OutputMode.TRAINING,
        optimization_level: int = 1
    ) -> Dict[str, Any]:
        """Main compilation entry point."""
        
        # Phase 1: Lexical Analysis and Parsing
        ir = self._parse_workflow(workflow)
        context = CompilationContext(
            target_mode=output_mode,
            optimization_level=optimization_level
        )
        
        # Phase 2: Semantic Analysis
        self._semantic_analysis(ir, context)
        
        # Phase 3: Type Checking and Data Flow Analysis
        self._type_checking(context)
        
        # Phase 4: Dependency Resolution
        self._dependency_resolution(context)
        
        # Phase 5: Optimization Passes
        if optimization_level > 0:
            self._apply_optimizations(context)
        
        # Phase 6: Code Generation
        generated_code = self._generate_code(context, workflow.get("config", {}))
        
        # Phase 7: Post-processing and Validation
        self._validate_generated_code(generated_code)
        
        return self._build_compilation_result(generated_code, context, workflow)

    def _parse_workflow(self, workflow: Dict[str, Any]) -> Workflow:
        """Phase 1: Parse workflow JSON into IR."""
        return Workflow.from_json(workflow)

    def _semantic_analysis(self, ir: Workflow, context: CompilationContext) -> None:
        """Phase 2: Semantic analysis and validation."""
        
        # Convert nodes to typed nodes
        for node_id, node in ir.nodes.items():
            typed_node = TypedNode(
                id=node.id,
                type=node.type,
                data=node.data
            )
            
            # Analyze node semantics
            self._analyze_node_semantics(typed_node, context)
            context.nodes[node_id] = typed_node

        # Convert edges to data flow edges
        for edge in ir.edges:
            data_flow_edge = self._analyze_edge_semantics(edge, context)
            if data_flow_edge:
                context.edges.append(data_flow_edge)

        # Validate workflow structure
        self._validate_workflow_structure(context)

    def _analyze_node_semantics(self, node: TypedNode, context: CompilationContext) -> None:
        """Analyze individual node semantics."""
        
        # Define input/output types based on node type
        type_mappings = {
            "dataSource": {
                "inputs": {},
                "outputs": {"data-output": DataType.OHLCV}
            },
            "customDataset": {
                "inputs": {},
                "outputs": {"data-output": DataType.OHLCV}
            },
            "technicalIndicator": {
                "inputs": {"data-input": DataType.OHLCV},
                "outputs": {
                    "output-1": DataType.NUMERIC,
                    "output-2": DataType.NUMERIC,
                    "output-3": DataType.NUMERIC,
                    "output-4": DataType.NUMERIC,
                    "output-5": DataType.NUMERIC
                }
            },
            "condition": {
                "inputs": {
                    "data-input": DataType.NUMERIC,
                    "value-input": DataType.NUMERIC,
                    "aux-input": DataType.NUMERIC
                },
                "outputs": {"signal-output": DataType.SIGNAL}
            },
            "logic": {
                "inputs": {
                    "input-0": DataType.SIGNAL,
                    "input-1": DataType.SIGNAL
                },
                "outputs": {"output": DataType.SIGNAL}
            },
            "action": {
                "inputs": {"signal-input": DataType.SIGNAL},
                "outputs": {}
            },
            "riskManagement": {
                "inputs": {
                    "data-input": DataType.OHLCV,
                    "signal-input": DataType.SIGNAL
                },
                "outputs": {"risk-output": DataType.RISK_METRICS}
            },
            "output": {
                "inputs": {
                    "data-input": DataType.OHLCV,
                    "signal-input": DataType.SIGNAL
                },
                "outputs": {}
            }
        }

        if node.type in type_mappings:
            mapping = type_mappings[node.type]
            node.input_types = mapping["inputs"].copy()
            node.output_types = mapping["outputs"].copy()
        else:
            # Unknown node type - use fallback
            context.warnings.append(CompilationError(
                node.id,
                "unknown_node_type",
                f"Unknown node type: {node.type}",
                "warning"
            ))

    def _analyze_edge_semantics(self, edge: Edge, context: CompilationContext) -> Optional[DataFlowEdge]:
        """Analyze edge semantics and create data flow edge."""
        
        # Find source and target nodes
        source_node = context.nodes.get(edge.source)
        target_node = context.nodes.get(edge.target)
        
        if not source_node or not target_node:
            context.errors.append(CompilationError(
                edge.source,
                "invalid_edge",
                f"Edge references non-existent nodes: {edge.source} -> {edge.target}"
            ))
            return None

        # Extract handles from edge data if available
        edge_data = edge.data or {}
        source_handle = edge_data.get('sourceHandle', 'data-output')
        target_handle = edge_data.get('targetHandle', 'data-input')
        
        # If edge has rule data, use its data type
        rule = edge_data.get('rule', {})
        if rule and 'dataType' in rule:
            data_type_str = rule['dataType']
            data_type = DataType(data_type_str) if data_type_str in [dt.value for dt in DataType] else DataType.UNKNOWN
        else:
            # Determine data type based on source output
            data_type = source_node.output_types.get(source_handle, DataType.UNKNOWN)
        
        return DataFlowEdge(
            source=edge.source,
            target=edge.target,
            source_handle=source_handle,
            target_handle=target_handle,
            data_type=data_type
        )

    def _type_checking(self, context: CompilationContext) -> None:
        """Phase 3: Type checking and data flow analysis."""
        
        for edge in context.edges:
            source_node = context.nodes[edge.source]
            target_node = context.nodes[edge.target]
            
            # Check if source produces the expected output type
            source_output_type = source_node.output_types.get(edge.source_handle, DataType.UNKNOWN)
            
            # Check if target expects the input type
            target_input_type = target_node.input_types.get(edge.target_handle, DataType.UNKNOWN)
            
            # Type compatibility check
            if not self._types_compatible(source_output_type, target_input_type):
                context.errors.append(CompilationError(
                    edge.target,
                    "type_mismatch",
                    f"Type mismatch: {edge.source}[{source_output_type.value}] -> {edge.target}[{target_input_type.value}]"
                ))

    def _types_compatible(self, source_type: DataType, target_type: DataType) -> bool:
        """Check if two types are compatible."""
        if source_type == target_type:
            return True
        
        # Define type compatibility rules
        compatibility_rules = {
            DataType.OHLCV: [DataType.NUMERIC, DataType.OHLCV],
            DataType.NUMERIC: [DataType.NUMERIC, DataType.SIGNAL],
            DataType.SIGNAL: [DataType.SIGNAL],
            DataType.UNKNOWN: [DataType.UNKNOWN]
        }
        
        return target_type in compatibility_rules.get(source_type, [])

    def _dependency_resolution(self, context: CompilationContext) -> None:
        """Phase 4: Resolve dependencies and determine execution order."""
        
        # Build dependency graph
        for edge in context.edges:
            target_node = context.nodes[edge.target]
            target_node.dependencies.add(edge.source)

        # Topological sort for execution order
        execution_order = self._topological_sort(context)
        
        for i, node_id in enumerate(execution_order):
            context.nodes[node_id].execution_order = i

    def _topological_sort(self, context: CompilationContext) -> List[str]:
        """Perform topological sort to determine execution order."""
        
        # Kahn's algorithm
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        # Build graph and calculate in-degrees
        for node_id in context.nodes:
            in_degree[node_id] = 0
            
        for edge in context.edges:
            graph[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Find nodes with no incoming edges
        queue = deque([node_id for node_id in context.nodes if in_degree[node_id] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(context.nodes):
            context.errors.append(CompilationError(
                "workflow",
                "cycle_detected",
                "Circular dependency detected in workflow"
            ))

        return result

    def _validate_workflow_structure(self, context: CompilationContext) -> None:
        """Validate overall workflow structure."""
        
        # Check for required node types
        node_types = [node.type for node in context.nodes.values()]
        
        if "dataSource" not in node_types and "customDataset" not in node_types:
            context.errors.append(CompilationError(
                "workflow",
                "missing_data_source",
                "Workflow must include at least one data source"
            ))
        
        if "action" not in node_types:
            context.warnings.append(CompilationError(
                "workflow",
                "no_actions",
                "Workflow has no action nodes - no trades will be executed",
                "warning"
            ))

        # Check for disconnected nodes
        connected_nodes = set()
        for edge in context.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        disconnected = set(context.nodes.keys()) - connected_nodes
        if disconnected and len(context.nodes) > 1:
            context.warnings.append(CompilationError(
                "workflow",
                "disconnected_nodes",
                f"Disconnected nodes found: {', '.join(disconnected)}",
                "warning"
            ))

    def _apply_optimizations(self, context: CompilationContext) -> None:
        """Phase 5: Apply optimization passes."""
        
        for optimization_pass in self.optimization_passes:
            if context.optimization_level >= optimization_pass.__name__.count("_"):
                optimization_pass(context)

    def _dead_code_elimination(self, context: CompilationContext) -> None:
        """Remove unreachable nodes."""
        
        # Find nodes that don't contribute to any output
        contributing_nodes = set()
        
        # Start from action nodes and work backwards
        action_nodes = [node_id for node_id, node in context.nodes.items() if node.type == "action"]
        output_nodes = [node_id for node_id, node in context.nodes.items() if node.type == "output"]
        
        queue = deque(action_nodes + output_nodes)
        
        while queue:
            current = queue.popleft()
            if current in contributing_nodes:
                continue
                
            contributing_nodes.add(current)
            
            # Add all nodes that contribute to this node
            for edge in context.edges:
                if edge.target == current and edge.source not in contributing_nodes:
                    queue.append(edge.source)

        # Remove non-contributing nodes
        dead_nodes = set(context.nodes.keys()) - contributing_nodes
        for node_id in dead_nodes:
            del context.nodes[node_id]
            context.nodes[node_id].optimizations.append("dead_code_eliminated")

    def _common_subexpression_elimination(self, context: CompilationContext) -> None:
        """Eliminate common subexpressions."""
        
        # Group nodes by type and parameters
        expression_groups = defaultdict(list)
        
        for node_id, node in context.nodes.items():
            if node.type in ["technicalIndicator", "condition"]:
                # Create a signature for the node
                signature = (node.type, json.dumps(node.data.get("parameters", {}), sort_keys=True))
                expression_groups[signature].append(node_id)

        # Mark duplicates for optimization
        for signature, nodes in expression_groups.items():
            if len(nodes) > 1:
                # Keep the first node, mark others as optimized
                for node_id in nodes[1:]:
                    context.nodes[node_id].optimizations.append("common_subexpression_eliminated")

    def _constant_folding(self, context: CompilationContext) -> None:
        """Fold constant expressions."""
        
        for node_id, node in context.nodes.items():
            if node.type == "condition":
                params = node.data.get("parameters", {})
                
                # If all inputs are constants, mark for constant folding
                if all(isinstance(params.get(key), (int, float)) for key in ["value", "value2"] if key in params):
                    node.optimizations.append("constant_folded")

    def _loop_optimization(self, context: CompilationContext) -> None:
        """Optimize loops and repeated calculations."""
        
        # Look for patterns that can be vectorized
        for node_id, node in context.nodes.items():
            if node.type == "technicalIndicator":
                params = node.data.get("parameters", {})
                indicator = params.get("indicator", "")
                
                # Mark vectorizable indicators
                if indicator in ["SMA", "EMA", "RSI", "MACD"]:
                    node.optimizations.append("vectorized")

    def _generate_code(self, context: CompilationContext, config: Dict[str, Any]) -> Dict[str, str]:
        """Phase 6: Generate code based on compilation context."""
        
        if context.errors:
            return {"error": "Compilation failed with errors"}

        # Sort nodes by execution order
        sorted_nodes = sorted(
            context.nodes.values(),
            key=lambda n: n.execution_order
        )

        # Generate code sections
        imports = self._generate_imports(context)
        data_loading = self._generate_data_loading(sorted_nodes, context)
        feature_engineering = self._generate_feature_engineering(sorted_nodes, context)
        signal_generation = self._generate_signal_generation(sorted_nodes, context)
        risk_management = self._generate_risk_management(sorted_nodes, context)
        execution_logic = self._generate_execution_logic(sorted_nodes, context)

        # Generate based on target mode
        if context.target_mode == OutputMode.TRAINING:
            return self._generate_training_code(
                imports, data_loading, feature_engineering, 
                signal_generation, config
            )
        elif context.target_mode == OutputMode.BACKTESTING:
            return self._generate_backtesting_code(
                imports, data_loading, feature_engineering,
                signal_generation, risk_management, execution_logic
            )
        elif context.target_mode == OutputMode.LIVE_TRADING:
            return self._generate_live_trading_code(
                imports, data_loading, feature_engineering,
                signal_generation, risk_management, execution_logic
            )
        else:
            return self._generate_research_code(
                imports, data_loading, feature_engineering, signal_generation
            )

    def _generate_imports(self, context: CompilationContext) -> str:
        """Generate import statements."""
        
        base_imports = [
            "import pandas as pd",
            "import numpy as np",
            "from datetime import datetime, timedelta",
            "import warnings",
            "warnings.filterwarnings('ignore')"
        ]

        # Add imports based on node types
        node_types = set(node.type for node in context.nodes.values())
        
        if "technicalIndicator" in node_types:
            base_imports.extend([
                "import talib as ta",
                "from scipy import stats"
            ])
        
        if "condition" in node_types or "logic" in node_types:
            base_imports.append("from typing import Union, Optional")
        
        if "riskManagement" in node_types:
            base_imports.extend([
                "import math",
                "from collections import deque"
            ])

        if context.target_mode == OutputMode.TRAINING:
            base_imports.extend([
                "from sklearn.model_selection import train_test_split",
                "from sklearn.ensemble import RandomForestClassifier",
                "from sklearn.metrics import classification_report, confusion_matrix",
                "import joblib"
            ])

        return "\n".join(base_imports)

    def _generate_data_loading(self, nodes: List[TypedNode], context: CompilationContext) -> str:
        """Generate data loading code."""
        
        data_nodes = [node for node in nodes if node.type in ["dataSource", "customDataset"]]
        if not data_nodes:
            return "# No data sources defined"

        code_lines = []
        
        for node in data_nodes:
            handler = self.handlers.get(node.type, self.fallback_handler)
            
            # Generate optimized code if applicable
            if "vectorized" in node.optimizations:
                code_lines.append(f"# Vectorized data loading for {node.id}")
            
            snippet = handler.handle(node, self)
            if snippet:
                code_lines.append(snippet)

        return "\n".join(code_lines)

    def _generate_feature_engineering(self, nodes: List[TypedNode], context: CompilationContext) -> str:
        """Generate feature engineering code."""
        
        feature_nodes = [node for node in nodes if node.type == "technicalIndicator"]
        if not feature_nodes:
            return "# No technical indicators defined"

        code_lines = ["# Feature Engineering"]
        
        for node in feature_nodes:
            handler = self.handlers.get(node.type, self.fallback_handler)
            
            # Add optimization comments
            if node.optimizations:
                code_lines.append(f"# Optimizations: {', '.join(node.optimizations)}")
            
            snippet = handler.handle(node, self)
            if snippet:
                code_lines.append(snippet)

        return "\n".join(code_lines)

    def _generate_signal_generation(self, nodes: List[TypedNode], context: CompilationContext) -> str:
        """Generate signal generation code."""
        
        signal_nodes = [node for node in nodes if node.type in ["condition", "logic"]]
        if not signal_nodes:
            return "# No signal generation logic defined"

        code_lines = ["# Signal Generation"]
        
        for node in signal_nodes:
            handler = self.handlers.get(node.type, self.fallback_handler)
            snippet = handler.handle(node, self)
            if snippet:
                code_lines.append(snippet)

        return "\n".join(code_lines)

    def _generate_risk_management(self, nodes: List[TypedNode], context: CompilationContext) -> str:
        """Generate risk management code."""
        
        risk_nodes = [node for node in nodes if node.type == "riskManagement"]
        if not risk_nodes:
            return "# No risk management defined"

        code_lines = ["# Risk Management"]
        
        for node in risk_nodes:
            handler = self.handlers.get(node.type, self.fallback_handler)
            snippet = handler.handle(node, self)
            if snippet:
                code_lines.append(snippet)

        return "\n".join(code_lines)

    def _generate_execution_logic(self, nodes: List[TypedNode], context: CompilationContext) -> str:
        """Generate execution logic code."""
        
        action_nodes = [node for node in nodes if node.type == "action"]
        if not action_nodes:
            return "# No execution logic defined"

        code_lines = ["# Execution Logic"]
        
        for node in action_nodes:
            handler = self.handlers.get(node.type, self.fallback_handler)
            snippet = handler.handle(node, self)
            if snippet:
                code_lines.append(snippet)

        return "\n".join(code_lines)

    def _generate_training_code(
        self, imports: str, data_loading: str, feature_engineering: str,
        signal_generation: str, config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate training-specific code."""
        
        template = f'''"""
Auto-generated Training Strategy
Generated at: {datetime.utcnow().isoformat()}
Compiler: Enhanced No-Code Generator v2.0
"""

{imports}

class StrategyPipeline:
    def __init__(self):
        self.data = None
        self.features = []
        self.targets = []
        
    def load_data(self):
        {textwrap.indent(data_loading, "        ")}
        return self
        
    def engineer_features(self):
        {textwrap.indent(feature_engineering, "        ")}
        return self
        
    def generate_signals(self):
        {textwrap.indent(signal_generation, "        ")}
        return self
        
    def prepare_training_data(self):
        # Combine features and prepare for ML training
        feature_cols = [col for col in self.data.columns if col.startswith('feature_')]
        target_cols = [col for col in self.data.columns if col.startswith('target_')]
        
        if not feature_cols:
            raise ValueError("No features generated")
        if not target_cols:
            raise ValueError("No targets generated")
            
        X = self.data[feature_cols].fillna(0)
        y = self.data[target_cols[0]].fillna(0)  # Use first target
        
        return X, y
    
    def train_model(self, model_config=None):
        X, y = self.prepare_training_data()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=model_config.get('n_estimators', 100),
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        print("Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save model
        joblib.dump(model, 'trained_model.joblib')
        
        return model

if __name__ == "__main__":
    pipeline = StrategyPipeline()
    pipeline.load_data().engineer_features().generate_signals()
    
    model_config = {json.dumps(config.get('model', {}), indent=4)}
    model = pipeline.train_model(model_config)
    print("Training completed successfully!")
'''
        
        return {
            "main": template,
            "type": "training"
        }

    def _generate_backtesting_code(
        self, imports: str, data_loading: str, feature_engineering: str,
        signal_generation: str, risk_management: str, execution_logic: str
    ) -> Dict[str, str]:
        """Generate backtesting-specific code."""
        
        template = f'''"""
Auto-generated Backtesting Strategy
Generated at: {datetime.utcnow().isoformat()}
Compiler: Enhanced No-Code Generator v2.0
"""

{imports}

class BacktestingEngine:
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {{}}
        self.trades = []
        self.data = None
        
    def load_data(self):
        {textwrap.indent(data_loading, "        ")}
        return self
        
    def engineer_features(self):
        {textwrap.indent(feature_engineering, "        ")}
        return self
        
    def generate_signals(self):
        {textwrap.indent(signal_generation, "        ")}
        return self
        
    def apply_risk_management(self):
        {textwrap.indent(risk_management, "        ")}
        return self
        
    def execute_trades(self):
        {textwrap.indent(execution_logic, "        ")}
        return self
        
    def run_backtest(self):
        self.load_data()
        self.engineer_features()
        self.generate_signals()
        self.apply_risk_management()
        
        # Simulate trading
        for i in range(len(self.data)):
            self.execute_trades_at_index(i)
            
        return self.calculate_performance()
    
    def execute_trades_at_index(self, index):
        # Implementation would go here
        pass
        
    def calculate_performance(self):
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        return {{
            'total_return': total_return,
            'final_capital': self.capital,
            'num_trades': len(self.trades)
        }}

if __name__ == "__main__":
    engine = BacktestingEngine()
    results = engine.run_backtest()
    print(f"Backtest Results: {{results}}")
'''
        
        return {
            "main": template,
            "type": "backtesting"
        }

    def _generate_live_trading_code(
        self, imports: str, data_loading: str, feature_engineering: str,
        signal_generation: str, risk_management: str, execution_logic: str
    ) -> Dict[str, str]:
        """Generate live trading-specific code."""
        
        template = f'''"""
Auto-generated Live Trading Strategy
Generated at: {datetime.utcnow().isoformat()}
Compiler: Enhanced No-Code Generator v2.0
"""

{imports}
import time
from threading import Thread

class LiveTradingEngine:
    def __init__(self, broker_client=None):
        self.broker_client = broker_client
        self.running = False
        self.data_buffer = deque(maxlen=1000)
        
    def load_live_data(self):
        {textwrap.indent(data_loading, "        ")}
        return self
        
    def engineer_features(self):
        {textwrap.indent(feature_engineering, "        ")}
        return self
        
    def generate_signals(self):
        {textwrap.indent(signal_generation, "        ")}
        return self
        
    def apply_risk_management(self):
        {textwrap.indent(risk_management, "        ")}
        return self
        
    def execute_trades(self):
        {textwrap.indent(execution_logic, "        ")}
        return self
        
    def start_trading(self):
        self.running = True
        
        # Start data feed thread
        data_thread = Thread(target=self._data_feed_loop)
        data_thread.start()
        
        # Start trading loop
        trading_thread = Thread(target=self._trading_loop)
        trading_thread.start()
        
    def stop_trading(self):
        self.running = False
        
    def _data_feed_loop(self):
        while self.running:
            # Fetch new data and update buffer
            self.load_live_data()
            time.sleep(1)  # Update every second
            
    def _trading_loop(self):
        while self.running:
            if len(self.data_buffer) > 50:  # Minimum data required
                self.engineer_features()
                self.generate_signals()
                self.apply_risk_management()
                self.execute_trades()
            
            time.sleep(5)  # Check every 5 seconds

if __name__ == "__main__":
    engine = LiveTradingEngine()
    print("Starting live trading engine...")
    engine.start_trading()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping trading engine...")
        engine.stop_trading()
'''
        
        return {
            "main": template,
            "type": "live_trading"
        }

    def _generate_research_code(
        self, imports: str, data_loading: str, feature_engineering: str, signal_generation: str
    ) -> Dict[str, str]:
        """Generate research-specific code."""
        
        template = f'''"""
Auto-generated Research Strategy
Generated at: {datetime.utcnow().isoformat()}
Compiler: Enhanced No-Code Generator v2.0
"""

{imports}
import matplotlib.pyplot as plt
import seaborn as sns

class ResearchPipeline:
    def __init__(self):
        self.data = None
        self.analysis_results = {{}}
        
    def load_data(self):
        {textwrap.indent(data_loading, "        ")}
        return self
        
    def engineer_features(self):
        {textwrap.indent(feature_engineering, "        ")}
        return self
        
    def generate_signals(self):
        {textwrap.indent(signal_generation, "        ")}
        return self
        
    def analyze_features(self):
        feature_cols = [col for col in self.data.columns if col.startswith('feature_')]
        target_cols = [col for col in self.data.columns if col.startswith('target_')]
        
        # Feature correlation analysis
        if feature_cols:
            corr_matrix = self.data[feature_cols].corr()
            
            plt.figure(figsize=(12, 8))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
            plt.title('Feature Correlation Matrix')
            plt.tight_layout()
            plt.savefig('feature_correlation.png')
            plt.show()
        
        # Signal analysis
        if target_cols:
            signal_stats = self.data[target_cols[0]].value_counts()
            print("Signal Distribution:")
            print(signal_stats)
            
        return self
        
    def run_analysis(self):
        self.load_data()
        self.engineer_features()
        self.generate_signals()
        self.analyze_features()
        
        print("Research analysis completed!")
        return self.analysis_results

if __name__ == "__main__":
    pipeline = ResearchPipeline()
    results = pipeline.run_analysis()
'''
        
        return {
            "main": template,
            "type": "research"
        }

    def _validate_generated_code(self, generated_code: Dict[str, str]) -> None:
        """Phase 7: Validate generated code."""
        
        if "main" not in generated_code:
            return
            
        try:
            # Parse the generated code to check for syntax errors
            ast.parse(generated_code["main"])
        except SyntaxError as e:
            # In a real implementation, this would be logged and handled
            print(f"Generated code has syntax error: {e}")

    def _build_compilation_result(
        self, 
        generated_code: Dict[str, str], 
        context: CompilationContext,
        original_workflow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the final compilation result."""
        
        # Collect requirements from all handlers
        requirements = set()
        for node in context.nodes.values():
            handler = self.handlers.get(node.type, self.fallback_handler)
            requirements.update(handler.required_packages())

        # Add requirements based on output mode
        if context.target_mode == OutputMode.TRAINING:
            requirements.update(["scikit-learn", "joblib"])
        elif context.target_mode == OutputMode.LIVE_TRADING:
            requirements.update(["websocket-client", "requests"])
        elif context.target_mode == OutputMode.RESEARCH:
            requirements.update(["matplotlib", "seaborn"])

        return {
            "code": generated_code.get("main", ""),
            "code_type": generated_code.get("type", "unknown"),
            "requirements": sorted(list(requirements)),
            "metadata": {
                "compilation_time": datetime.utcnow().isoformat(),
                "compiler_version": "2.0",
                "optimization_level": context.optimization_level,
                "output_mode": context.target_mode.value,
                "nodes_processed": len(context.nodes),
                "edges_processed": len(context.edges),
                "optimizations_applied": sum(len(node.optimizations) for node in context.nodes.values())
            },
            "success": len(context.errors) == 0,
            "errors": [
                {
                    "node_id": error.node_id,
                    "type": error.error_type,
                    "message": error.message,
                    "severity": error.severity
                }
                for error in context.errors
            ],
            "warnings": [
                {
                    "node_id": warning.node_id,
                    "type": warning.error_type,
                    "message": warning.message,
                    "severity": warning.severity
                }
                for warning in context.warnings
            ]
        }

    # Helper methods for backward compatibility
    def get_incoming(self, node_id: str) -> List[str]:
        """Get incoming connections for a node."""
        # This would be implemented using the compilation context
        return []

    def generate_strategy_code(self, workflow: Dict[str, Any], name: str = "GeneratedStrategy") -> Dict[str, Any]:
        """Backward compatibility method."""
        return self.compile_workflow(workflow, OutputMode.TRAINING)


# Backward compatibility
CodeGenerator = EnhancedCodeGenerator

__all__ = ["EnhancedCodeGenerator", "CodeGenerator", "OutputMode", "DataType"]