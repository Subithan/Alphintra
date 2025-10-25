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
    incoming_edges: Dict[str, List[DataFlowEdge]] = field(default_factory=dict)
    outgoing_edges: Dict[str, List[DataFlowEdge]] = field(default_factory=dict)


class EnhancedCodeGenerator:
    """Enhanced code generator with compiler-like functionality."""

    def __init__(self):
        self.handlers = dict(HANDLER_REGISTRY)

        # Ensure legacy "riskManagement" nodes share the enhanced risk handler
        risk_handler = self.handlers.get("risk")
        if risk_handler and "riskManagement" not in self.handlers:
            self.handlers["riskManagement"] = risk_handler
        self.fallback_handler = FALLBACK_HANDLER
        self.optimization_passes = [
            self._dead_code_elimination,
            self._common_subexpression_elimination,
            self._constant_folding,
            self._loop_optimization
        ]
        self._compilation_context: Optional[CompilationContext] = None

    def compile_workflow(
        self,
        workflow: Dict[str, Any],
        output_mode: OutputMode = OutputMode.TRAINING,
        optimization_level: int = 1
    ) -> Dict[str, Any]:
        """Main compilation entry point."""

        self._compilation_context = None
        # Phase 1: Lexical Analysis and Parsing
        ir = self._parse_workflow(workflow)
        context = CompilationContext(
            target_mode=output_mode,
            optimization_level=optimization_level
        )

        # Phase 2: Semantic Analysis
        self._semantic_analysis(ir, context)
        self._compilation_context = context

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
            context.incoming_edges.setdefault(node_id, [])
            context.outgoing_edges.setdefault(node_id, [])

        # Convert edges to data flow edges
        for edge in ir.edges:
            data_flow_edge = self._analyze_edge_semantics(edge, context)
            if data_flow_edge:
                context.edges.append(data_flow_edge)
                context.incoming_edges.setdefault(data_flow_edge.target, []).append(data_flow_edge)
                context.outgoing_edges.setdefault(data_flow_edge.source, []).append(data_flow_edge)

        # Validate workflow structure
        self._validate_workflow_structure(context)

    def _analyze_node_semantics(self, node: TypedNode, context: CompilationContext) -> None:
        """Analyze individual node semantics."""
        
        # Define input/output types based on node type
        risk_io = {
            "inputs": {
                "data-input": DataType.OHLCV,
                "signal-input": DataType.SIGNAL
            },
            "outputs": {"risk-output": DataType.RISK_METRICS}
        }

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
            "riskManagement": risk_io,
            "risk": risk_io,
            "output": {
                "inputs": {
                    "data-input": DataType.OHLCV,
                    "signal-input": DataType.SIGNAL
                },
                "outputs": {}
            },
            "marketRegimeDetection": {
                "inputs": {"data-input": DataType.OHLCV},
                "outputs": {
                    "trend-output": DataType.SIGNAL,
                    "sideways-output": DataType.SIGNAL,
                    "volatile-output": DataType.SIGNAL
                }
            },
            "multiTimeframeAnalysis": {
                "inputs": {"data-input": DataType.OHLCV},
                "outputs": {"output": DataType.OHLCV}
            },
            "correlationAnalysis": {
                "inputs": {
                    "data-input-1": DataType.OHLCV,
                    "data-input-2": DataType.OHLCV
                },
                "outputs": {"output": DataType.CORRELATION}
            },
            "sentimentAnalysis": {
                "inputs": {"data-input": DataType.OHLCV},
                "outputs": {
                    "positive-output": DataType.SIGNAL,
                    "neutral-output": DataType.SIGNAL,
                    "negative-output": DataType.SIGNAL
                }
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
            DataType.OHLCV: [DataType.NUMERIC, DataType.OHLCV, DataType.CORRELATION, DataType.SENTIMENT, DataType.UNKNOWN],
            DataType.NUMERIC: [DataType.NUMERIC, DataType.SIGNAL, DataType.CORRELATION],
            DataType.SIGNAL: [DataType.SIGNAL, DataType.NUMERIC],
            DataType.CORRELATION: [DataType.CORRELATION, DataType.NUMERIC],
            DataType.SENTIMENT: [DataType.SENTIMENT, DataType.SIGNAL, DataType.NUMERIC],
            DataType.UNKNOWN: [DataType.UNKNOWN, DataType.NUMERIC, DataType.SIGNAL]
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
        """Phase 6: Generate a standalone Python module for the workflow."""

        if context.errors:
            return {"error": "Compilation failed with errors"}

        sorted_nodes = sorted(
            context.nodes.values(),
            key=lambda node: node.execution_order
        )

        module_source = self._assemble_strategy_module(sorted_nodes, context)

        return {
            "main": module_source,
            "type": "module"
        }

    # ------------------------------------------------------------------
    # Module assembly helpers
    # ------------------------------------------------------------------
    def _assemble_strategy_module(
        self,
        nodes: List[TypedNode],
        context: CompilationContext
    ) -> str:
        """Assemble the final module source from workflow nodes."""

        header = self._emit_module_header()
        imports = self._emit_import_block()

        incoming_edges = self._build_incoming_edge_lookup(context)
        value_map: Dict[Tuple[str, str], str] = {}

        data_nodes = [node for node in nodes if node.type in {"dataSource", "customDataset"}]
        analysis_nodes = [
            node
            for node in nodes
            if node.type in {
                "marketRegimeDetection",
                "multiTimeframeAnalysis",
                "correlationAnalysis",
                "sentimentAnalysis",
            }
        ]
        indicator_nodes = [node for node in nodes if node.type == "technicalIndicator"]
        condition_nodes = [node for node in nodes if node.type == "condition"]
        logic_nodes = [node for node in nodes if node.type == "logic"]
        risk_nodes = [node for node in nodes if node.type in {"risk", "riskManagement"}]
        action_nodes = [node for node in nodes if node.type == "action"]

        data_fn, value_map = self._emit_data_function(data_nodes, value_map)
        analysis_fn, value_map = self._emit_analysis_function(
            analysis_nodes, value_map, incoming_edges
        )
        indicator_fn, value_map = self._emit_indicator_function(
            indicator_nodes, value_map, incoming_edges
        )
        condition_fn, value_map = self._emit_condition_function(condition_nodes, value_map, incoming_edges)
        logic_fn, value_map = self._emit_logic_function(logic_nodes, value_map, incoming_edges)
        risk_fn, value_map = self._emit_risk_function(risk_nodes, value_map, incoming_edges)
        action_fn, _ = self._emit_action_function(action_nodes, value_map, incoming_edges)
        run_fn = self._emit_run_function(include_analysis=bool(analysis_nodes))

        sections = [header, "", imports, "", data_fn]
        if analysis_fn:
            sections.extend(["", analysis_fn])
        sections.extend(["", indicator_fn, "", condition_fn])
        sections.extend(["", logic_fn])
        sections.extend(["", risk_fn])
        sections.extend(["", action_fn, "", run_fn])

        return "\n".join(section.rstrip() for section in sections if section is not None)

    def _emit_module_header(self) -> str:
        """Return the module level docstring."""

        timestamp = datetime.utcnow().isoformat()
        return textwrap.dedent(
            f'''"""
            Auto-generated Trading Strategy Module
            Generated at: {timestamp}
            Compiler: Enhanced No-Code Generator v2.0
            """'''
        ).strip()

    def _emit_import_block(self) -> str:
        """Emit the imports required for the lightweight module."""

        imports = [
            "from __future__ import annotations",
            "",
            "import numpy as np",
            "import pandas as pd",
        ]
        return "\n".join(imports)

    def _emit_data_function(
        self,
        data_nodes: List[TypedNode],
        value_map: Dict[Tuple[str, str], str]
    ) -> Tuple[str, Dict[Tuple[str, str], str]]:
        """Emit the load_data function and seed the value map."""

        lines: List[str] = ["def load_data() -> pd.DataFrame:"]

        body: List[str] = []
        if not data_nodes:
            body.extend([
                "df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])",
                "return df",
            ])
            lines.append(self._indent_block(body))
            return "\n".join(lines), value_map

        for index, node in enumerate(data_nodes):
            params = node.data.get("parameters", {})
            label = node.data.get("label") or params.get("label") or node.id
            symbol = params.get("symbol", label)
            timeframe = params.get("timeframe", "1h")
            bars = int(params.get("bars", 250))
            freq = timeframe.upper()
            safe_id = self._sanitize_identifier(node.id)
            df_name = f"df_{safe_id}"
            rng_name = f"rng_{safe_id}"

            body.extend([
                f"# Data source: {symbol} ({timeframe})",
                f"{rng_name} = np.random.default_rng({42 + index})",
                f"index_{safe_id} = pd.date_range(end=pd.Timestamp.utcnow(), periods={bars}, freq='{freq}')",
                f"baseline_{safe_id} = 100 + {rng_name}.normal(0, 1, {bars}).cumsum()",
                f"{df_name} = pd.DataFrame({{",
                f"    'open': baseline_{safe_id} * (1 + {rng_name}.normal(0, 0.002, {bars})),",
                f"    'high': baseline_{safe_id} * (1 + np.abs({rng_name}.normal(0, 0.01, {bars}))),",
                f"    'low': baseline_{safe_id} * (1 - np.abs({rng_name}.normal(0, 0.01, {bars}))),",
                f"    'close': baseline_{safe_id},",
                f"    'volume': {rng_name}.integers(1_000, 10_000, {bars}),",
                f"}}, index=index_{safe_id})",
                f"{df_name}.index.name = 'timestamp'",
            ])

            if index == 0:
                body.append("df = {df_name}.copy()".format(df_name=df_name))
                value_map[(node.id, "data-output")] = "df"
            else:
                value_map[(node.id, "data-output")] = "df"

        body.append("return df")

        lines.append(self._indent_block(body))
        return "\n".join(lines), value_map

    def _emit_analysis_function(
        self,
        analysis_nodes: List[TypedNode],
        value_map: Dict[Tuple[str, str], str],
        incoming_edges: Dict[str, List[DataFlowEdge]]
    ) -> Tuple[str, Dict[Tuple[str, str], str]]:
        """Emit advanced analytics transformations (regime, sentiment, etc.)."""

        lines: List[str] = ["def run_advanced_analysis(df: pd.DataFrame) -> pd.DataFrame:"]
        body: List[str] = ["df = df.copy()"]

        if not analysis_nodes:
            body.append("return df")
            lines.append(self._indent_block(body))
            return "\n".join(lines), value_map

        for node in analysis_nodes:
            safe_id = self._sanitize_identifier(node.id)
            params = node.data.get("parameters", {})

            if node.type == "marketRegimeDetection":
                price_expr = self._resolve_input_expression(
                    node.id,
                    "data-input",
                    value_map,
                    incoming_edges,
                    fallback="df['close']"
                )
                if price_expr == "df":
                    price_expr = "df['close']"

                trend_window = int(params.get("trendWindow", params.get("lookback", 50)))
                volatility_window = int(params.get("volatilityWindow", max(10, trend_window // 2)))
                volatility_multiplier = float(params.get("volatilityMultiplier", 1.5))
                trend_bias = float(params.get("trendThreshold", 0.0))

                trend_col = f"regime_{safe_id}_trend"
                sideways_col = f"regime_{safe_id}_sideways"
                volatile_col = f"regime_{safe_id}_volatile"

                body.extend([
                    f"# Market regime detection for node {node.id}",
                    f"price_{safe_id} = {price_expr}",
                    f"returns_{safe_id} = price_{safe_id}.pct_change().fillna(0)",
                    f"trend_ma_{safe_id} = price_{safe_id}.rolling(window={trend_window}, min_periods=1).mean()",
                    f"trend_signal_{safe_id} = (price_{safe_id} > trend_ma_{safe_id} * (1 + {trend_bias})).fillna(False)",
                    f"volatility_{safe_id} = returns_{safe_id}.rolling(window={volatility_window}, min_periods=1).std().fillna(0)",
                    f"vol_threshold_{safe_id} = volatility_{safe_id}.rolling(window={volatility_window}, min_periods=1).median().fillna(method='bfill').fillna(volatility_{safe_id})",
                    f"df['{trend_col}'] = trend_signal_{safe_id}.astype(bool)",
                    f"df['{volatile_col}'] = (volatility_{safe_id} > vol_threshold_{safe_id} * {volatility_multiplier}).fillna(False).astype(bool)",
                    f"df['{sideways_col}'] = (~df['{trend_col}'] & ~df['{volatile_col}']).astype(bool)",
                ])

                value_map[(node.id, "trend-output")] = f"df['{trend_col}']"
                value_map[(node.id, "sideways-output")] = f"df['{sideways_col}']"
                value_map[(node.id, "volatile-output")] = f"df['{volatile_col}']"

            elif node.type == "multiTimeframeAnalysis":
                data_expr = self._resolve_input_expression(
                    node.id,
                    "data-input",
                    value_map,
                    incoming_edges,
                    fallback="df"
                )
                if data_expr is None:
                    data_expr = "df"

                requested = params.get("timeframes") or params.get("higherTimeframes") or ["4H", "1D"]
                if isinstance(requested, str):
                    requested = [segment.strip() for segment in requested.split(",") if segment.strip()]
                timeframes = list(requested) or ["4H"]

                prefix = f"mtf_{safe_id}"

                body.extend([
                    f"# Multi-timeframe aggregation for node {node.id}",
                    f"source_df_{safe_id} = {data_expr}",
                    f"if isinstance(source_df_{safe_id}, pd.Series):",
                    f"    source_df_{safe_id} = source_df_{safe_id}.to_frame(name='close')",
                    f"if not isinstance(source_df_{safe_id}, pd.DataFrame):",
                    f"    source_df_{safe_id} = df",
                    f"timeframes_{safe_id} = {timeframes!r}",
                    f"ohlc_map_{safe_id} = {{'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}}",
                    f"last_suffix_{safe_id} = None",
                    f"for tf in timeframes_{safe_id}:",
                    f"    aggregated_{safe_id} = source_df_{safe_id}.resample(tf).agg(ohlc_map_{safe_id})",
                    f"    aggregated_{safe_id} = aggregated_{safe_id}.reindex(df.index, method='ffill').fillna(method='bfill')",
                    f"    suffix_{safe_id} = tf.replace(' ', '').replace(':', '').replace('-', '')",
                    f"    for column in ['open', 'high', 'low', 'close', 'volume']:",
                    f"        df[f'{prefix}_' + column + '_' + suffix_{safe_id}] = aggregated_{safe_id}[column]",
                    f"    last_suffix_{safe_id} = suffix_{safe_id}",
                    f"if last_suffix_{safe_id}:",
                    f"    df['{prefix}_active_close'] = df[f'{prefix}_close_' + last_suffix_{safe_id}]",
                    f"else:",
                    f"    df['{prefix}_active_close'] = df['close']",
                ])

                value_map[(node.id, "output")] = f"df['{prefix}_active_close']"

            elif node.type == "correlationAnalysis":
                left_expr = self._resolve_input_expression(
                    node.id,
                    "data-input-1",
                    value_map,
                    incoming_edges,
                    fallback="df['close']"
                )
                right_expr = self._resolve_input_expression(
                    node.id,
                    "data-input-2",
                    value_map,
                    incoming_edges,
                    fallback="df['close']"
                )
                if left_expr == "df":
                    left_expr = "df['close']"
                if right_expr == "df":
                    right_expr = "df['close']"

                corr_col = f"correlation_{safe_id}"
                window = int(params.get("window", params.get("lookback", 30)))

                body.extend([
                    f"# Correlation analysis for node {node.id}",
                    f"left_series_{safe_id} = {left_expr}",
                    f"right_series_{safe_id} = {right_expr}",
                    f"if isinstance(left_series_{safe_id}, pd.DataFrame):",
                    f"    left_series_{safe_id} = left_series_{safe_id}['close']",
                    f"if isinstance(right_series_{safe_id}, pd.DataFrame):",
                    f"    right_series_{safe_id} = right_series_{safe_id}['close']",
                    f"returns_left_{safe_id} = left_series_{safe_id}.pct_change().fillna(0)",
                    f"returns_right_{safe_id} = right_series_{safe_id}.pct_change().fillna(0)",
                    f"rolling_corr_{safe_id} = returns_left_{safe_id}.rolling(window={window}, min_periods=1).corr(returns_right_{safe_id})",
                    f"df['{corr_col}'] = rolling_corr_{safe_id}.fillna(0)",
                ])

                value_map[(node.id, "output")] = f"df['{corr_col}']"

            elif node.type == "sentimentAnalysis":
                data_expr = self._resolve_input_expression(
                    node.id,
                    "data-input",
                    value_map,
                    incoming_edges,
                    fallback="df['close']"
                )
                if data_expr == "df":
                    data_expr = "df['close']"

                smoothing = int(params.get("smoothing", params.get("window", 14)))
                threshold = float(params.get("threshold", 0.05))

                pos_col = f"sentiment_{safe_id}_positive"
                neu_col = f"sentiment_{safe_id}_neutral"
                neg_col = f"sentiment_{safe_id}_negative"

                body.extend([
                    f"# Sentiment analysis for node {node.id}",
                    f"raw_source_{safe_id} = {data_expr}",
                    f"if isinstance(raw_source_{safe_id}, pd.DataFrame):",
                    f"    numeric_cols_{safe_id} = raw_source_{safe_id}.select_dtypes(include=['number'])",
                    f"    base_series_{safe_id} = numeric_cols_{safe_id}.mean(axis=1) if not numeric_cols_{safe_id}.empty else raw_source_{safe_id}.sum(axis=1)",
                    f"else:",
                    f"    base_series_{safe_id} = pd.Series(raw_source_{safe_id}, index=df.index) if not isinstance(raw_source_{safe_id}, pd.Series) else raw_source_{safe_id}",
                    f"smoothed_{safe_id} = base_series_{safe_id}.rolling(window={smoothing}, min_periods=1).mean().fillna(0)",
                    f"df['{pos_col}'] = (smoothed_{safe_id} > {threshold}).fillna(False).astype(bool)",
                    f"df['{neg_col}'] = (smoothed_{safe_id} < -{threshold}).fillna(False).astype(bool)",
                    f"df['{neu_col}'] = (~df['{pos_col}'] & ~df['{neg_col}']).astype(bool)",
                ])

                value_map[(node.id, "positive-output")] = f"df['{pos_col}']"
                value_map[(node.id, "neutral-output")] = f"df['{neu_col}']"
                value_map[(node.id, "negative-output")] = f"df['{neg_col}']"

        body.append("return df")
        lines.append(self._indent_block(body))
        return "\n".join(lines), value_map

    def _emit_indicator_function(
        self,
        indicator_nodes: List[TypedNode],
        value_map: Dict[Tuple[str, str], str],
        incoming_edges: Dict[str, List[DataFlowEdge]]
    ) -> Tuple[str, Dict[Tuple[str, str], str]]:
        """Emit indicator computation code and extend the value map."""

        lines: List[str] = ["def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:"]
        body: List[str] = ["df = df.copy()"]

        if not indicator_nodes:
            body.append("return df")
            lines.append(self._indent_block(body))
            return "\n".join(lines), value_map

        for node in indicator_nodes:
            params = node.data.get("parameters", {})
            indicator = params.get("indicator", "SMA").upper()
            period = int(params.get("period", params.get("timeperiod", 14)))
            source_column = params.get("source", "close")
            safe_id = self._sanitize_identifier(node.id)

            data_expr = self._resolve_input_expression(
                node.id, "data-input", value_map, incoming_edges,
                fallback="df"
            )

            if data_expr == "df":
                series_expr = f"df['{source_column}']"
            elif data_expr and data_expr.startswith("df_multi_"):
                series_expr = f"{data_expr}['{source_column}']"
            else:
                series_expr = data_expr

            body.append(f"# Indicator: {indicator} ({node.id})")

            if indicator == "RSI":
                delta_name = f"delta_{safe_id}"
                gain_name = f"gain_{safe_id}"
                loss_name = f"loss_{safe_id}"
                rs_name = f"rs_{safe_id}"
                column_name = f"indicator_{safe_id}"
                body.extend([
                    f"{delta_name} = {series_expr}.diff()",
                    f"{gain_name} = {delta_name}.clip(lower=0).rolling(window={period}, min_periods={period}).mean()",
                    f"{loss_name} = (-{delta_name}.clip(upper=0)).rolling(window={period}, min_periods={period}).mean()",
                    f"{rs_name} = {gain_name} / {loss_name}.replace(0, np.nan)",
                    f"df['{column_name}'] = 100 - (100 / (1 + {rs_name}))",
                    f"df['{column_name}'] = df['{column_name}'].fillna(method='bfill').fillna(50)",
                ])
                value_map[(node.id, "output-1")] = f"df['{column_name}']"
            elif indicator == "SMA":
                column_name = f"indicator_{safe_id}"
                body.append(f"df['{column_name}'] = {series_expr}.rolling(window={period}, min_periods=1).mean()")
                value_map[(node.id, "output-1")] = f"df['{column_name}']"
            elif indicator == "EMA":
                column_name = f"indicator_{safe_id}"
                body.append(f"df['{column_name}'] = {series_expr}.ewm(span={period}, adjust=False).mean()")
                value_map[(node.id, "output-1")] = f"df['{column_name}']"
            elif indicator == "MACD":
                fast = int(params.get("fastPeriod", 12))
                slow = int(params.get("slowPeriod", 26))
                signal_period = int(params.get("signalPeriod", 9))
                macd_col = f"indicator_{safe_id}_macd"
                signal_col = f"indicator_{safe_id}_signal"
                hist_col = f"indicator_{safe_id}_hist"
                body.extend([
                    f"ema_fast_{safe_id} = {series_expr}.ewm(span={fast}, adjust=False).mean()",
                    f"ema_slow_{safe_id} = {series_expr}.ewm(span={slow}, adjust=False).mean()",
                    f"df['{macd_col}'] = ema_fast_{safe_id} - ema_slow_{safe_id}",
                    f"df['{signal_col}'] = df['{macd_col}'].ewm(span={signal_period}, adjust=False).mean()",
                    f"df['{hist_col}'] = df['{macd_col}'] - df['{signal_col}']",
                ])
                value_map[(node.id, "output-1")] = f"df['{macd_col}']"
                value_map[(node.id, "output-2")] = f"df['{signal_col}']"
                value_map[(node.id, "output-3")] = f"df['{hist_col}']"
            elif indicator in {"BB", "BOLLINGER", "BOLLINGER_BANDS"}:
                multiplier = float(params.get("multiplier", 2))
                middle_col = f"indicator_{safe_id}_middle"
                upper_col = f"indicator_{safe_id}_upper"
                lower_col = f"indicator_{safe_id}_lower"
                rolling_mean = f"rolling_mean_{safe_id}"
                rolling_std = f"rolling_std_{safe_id}"
                body.extend([
                    f"{rolling_mean} = {series_expr}.rolling(window={period}, min_periods=1).mean()",
                    f"{rolling_std} = {series_expr}.rolling(window={period}, min_periods=1).std().fillna(0)",
                    f"df['{middle_col}'] = {rolling_mean}",
                    f"df['{upper_col}'] = df['{middle_col}'] + ({multiplier} * {rolling_std})",
                    f"df['{lower_col}'] = df['{middle_col}'] - ({multiplier} * {rolling_std})",
                ])
                value_map[(node.id, "output-1")] = f"df['{middle_col}']"
                value_map[(node.id, "output-2")] = f"df['{upper_col}']"
                value_map[(node.id, "output-3")] = f"df['{lower_col}']"
            else:
                column_name = f"indicator_{safe_id}"
                body.extend([
                    f"# Fallback indicator implementation for {indicator}",
                    f"df['{column_name}'] = {series_expr}",
                ])
                value_map[(node.id, "output-1")] = f"df['{column_name}']"

        body.append("return df")
        lines.append(self._indent_block(body))
        return "\n".join(lines), value_map

    def _emit_condition_function(
        self,
        condition_nodes: List[TypedNode],
        value_map: Dict[Tuple[str, str], str],
        incoming_edges: Dict[str, List[DataFlowEdge]]
    ) -> Tuple[str, Dict[Tuple[str, str], str]]:
        """Emit boolean signal conditions."""

        lines: List[str] = ["def evaluate_conditions(df: pd.DataFrame) -> pd.DataFrame:"]
        body: List[str] = ["df = df.copy()"]

        if not condition_nodes:
            body.append("return df")
            lines.append(self._indent_block(body))
            return "\n".join(lines), value_map

        comparison_map = {
            "less_than": "<",
            "greater_than": ">",
            "equal_to": "==",
            "not_equal": "!=",
            "greater_than_equal": ">=",
            "greater_or_equal": ">=",
            "less_than_equal": "<=",
            "less_or_equal": "<=",
        }

        for node in condition_nodes:
            params = node.data.get("parameters", {})
            operation = params.get("condition", "greater_than")
            operator = comparison_map.get(operation, ">")
            default_value = params.get("value", 0)
            safe_id = self._sanitize_identifier(node.id)
            column_name = f"signal_{safe_id}"

            left_expr = self._resolve_input_expression(
                node.id, "data-input", value_map, incoming_edges,
                fallback="df['close']"
            )
            right_expr = self._resolve_input_expression(
                node.id, "value-input", value_map, incoming_edges,
                fallback=repr(default_value)
            )

            body.extend([
                f"# Condition ({operation}) for node {node.id}",
                f"df['{column_name}'] = ({left_expr}) {operator} ({right_expr})",
                f"df['{column_name}'] = df['{column_name}'].fillna(False)",
            ])

            value_map[(node.id, "signal-output")] = f"df['{column_name}']"

        body.append("return df")
        lines.append(self._indent_block(body))
        return "\n".join(lines), value_map

    def _emit_logic_function(
        self,
        logic_nodes: List[TypedNode],
        value_map: Dict[Tuple[str, str], str],
        incoming_edges: Dict[str, List[DataFlowEdge]]
    ) -> Tuple[str, Dict[Tuple[str, str], str]]:
        """Emit logic combination function."""

        lines: List[str] = ["def combine_logic(df: pd.DataFrame) -> pd.DataFrame:"]
        body: List[str] = ["df = df.copy()"]

        if not logic_nodes:
            body.append("return df")
            lines.append(self._indent_block(body))
            return "\n".join(lines), value_map

        for node in logic_nodes:
            params = node.data.get("parameters", {})
            operation = params.get("operation", "AND").upper()
            safe_id = self._sanitize_identifier(node.id)
            column_name = f"logic_{safe_id}"

            inputs = self._resolve_logic_inputs(node.id, value_map, incoming_edges)

            if not inputs:
                body.extend([
                    f"# Logic node {node.id} has no inputs; defaulting to False",
                    f"df['{column_name}'] = False",
                ])
            else:
                if operation == "AND":
                    combined_expr = " & ".join(f"({expr})" for expr in inputs)
                elif operation == "OR":
                    combined_expr = " | ".join(f"({expr})" for expr in inputs)
                elif operation == "XOR":
                    combined_expr = inputs[0]
                    for expr in inputs[1:]:
                        combined_expr = f"({combined_expr}) ^ ({expr})"
                elif operation == "NOT":
                    combined_expr = f"~({inputs[0]})"
                else:
                    combined_expr = " | ".join(f"({expr})" for expr in inputs)

                body.extend([
                    f"# Logic ({operation}) for node {node.id}",
                    f"df['{column_name}'] = {combined_expr}",
                    f"df['{column_name}'] = df['{column_name}'].fillna(False)",
                ])

            value_map[(node.id, "output")] = f"df['{column_name}']"

        body.append("return df")
        lines.append(self._indent_block(body))
        return "\n".join(lines), value_map

    def _emit_risk_function(
        self,
        risk_nodes: List[TypedNode],
        value_map: Dict[Tuple[str, str], str],
        incoming_edges: Dict[str, List[DataFlowEdge]]
    ) -> Tuple[str, Dict[Tuple[str, str], str]]:
        """Emit risk control computation."""

        lines: List[str] = ["def apply_risk_controls(df: pd.DataFrame) -> pd.DataFrame:"]
        body: List[str] = ["df = df.copy()"]

        if not risk_nodes:
            body.append("return df")
            lines.append(self._indent_block(body))
            return "\n".join(lines), value_map

        for node in risk_nodes:
            params = node.data.get("parameters", {})
            safe_id = self._sanitize_identifier(node.id)
            column_name = f"risk_{safe_id}"
            max_loss = float(params.get("maxLoss", 5.0))

            signal_expr = self._resolve_input_expression(
                node.id, "signal-input", value_map, incoming_edges,
                fallback=None
            )

            pct_change_expr = "df['close'].pct_change().fillna(0).abs() * 100"
            risk_expr = f"({pct_change_expr}) <= {max_loss}"

            if signal_expr:
                risk_expr = f"({risk_expr}) & ({signal_expr})"

            body.extend([
                f"# Risk control for node {node.id}",
                f"df['{column_name}'] = {risk_expr}",
                f"df['{column_name}'] = df['{column_name}'].fillna(True)",
            ])

            value_map[(node.id, "risk-output")] = f"df['{column_name}']"

        body.append("return df")
        lines.append(self._indent_block(body))
        return "\n".join(lines), value_map

    def _emit_action_function(
        self,
        action_nodes: List[TypedNode],
        value_map: Dict[Tuple[str, str], str],
        incoming_edges: Dict[str, List[DataFlowEdge]]
    ) -> Tuple[str, Dict[Tuple[str, str], str]]:
        """Emit trade decision logic."""

        lines: List[str] = ["def generate_trading_decisions(df: pd.DataFrame) -> pd.DataFrame:"]
        body: List[str] = ["df = df.copy()"]

        if not action_nodes:
            body.append("df['decision'] = 'HOLD'")
            body.append("return df")
            lines.append(self._indent_block(body))
            return "\n".join(lines), value_map

        for node in action_nodes:
            params = node.data.get("parameters", {})
            action = params.get("action", "buy").upper()
            safe_id = self._sanitize_identifier(node.id)
            column_name = f"decision_{safe_id}"

            signal_expr = self._resolve_input_expression(
                node.id, "signal-input", value_map, incoming_edges,
                fallback=None
            )

            if not signal_expr:
                signal_expr = "pd.Series(False, index=df.index)"

            decision_value = "BUY" if action == "BUY" else "SELL" if action == "SELL" else action
            body.extend([
                f"# Trading action for node {node.id}",
                f"df['{column_name}'] = np.where({signal_expr}, '{decision_value}', 'HOLD')",
            ])

            value_map[(node.id, "action-output")] = f"df['{column_name}']"

        body.append("return df")
        lines.append(self._indent_block(body))
        return "\n".join(lines), value_map

    def _emit_run_function(self, include_analysis: bool) -> str:
        """Emit a helper that chains all generated functions."""

        lines = [
            "def run_strategy() -> pd.DataFrame:",
            "    df = load_data()",
        ]
        if include_analysis:
            lines.append("    df = run_advanced_analysis(df)")
        lines.extend([
            "    df = compute_indicators(df)",
            "    df = evaluate_conditions(df)",
            "    df = combine_logic(df)",
            "    df = apply_risk_controls(df)",
            "    df = generate_trading_decisions(df)",
            "    return df",
        ])
        return "\n".join(lines)

    def _resolve_input_expression(
        self,
        node_id: str,
        handle: str,
        value_map: Dict[Tuple[str, str], str],
        incoming_edges: Dict[str, List[DataFlowEdge]],
        *,
        fallback: Optional[str]
    ) -> Optional[str]:
        """Resolve the expression wired into a particular input handle."""

        for edge in incoming_edges.get(node_id, []):
            if edge.target_handle == handle:
                expr = value_map.get((edge.source, edge.source_handle))
                if expr is not None:
                    return expr
                break
        return fallback

    def _resolve_logic_inputs(
        self,
        node_id: str,
        value_map: Dict[Tuple[str, str], str],
        incoming_edges: Dict[str, List[DataFlowEdge]]
    ) -> List[str]:
        """Return logic input expressions ordered by their input handles."""

        inputs = []
        for edge in sorted(incoming_edges.get(node_id, []), key=lambda e: e.target_handle):
            if not edge.target_handle.startswith("input"):
                continue
            expr = value_map.get((edge.source, edge.source_handle))
            if expr is not None:
                inputs.append(expr)
        return inputs

    def _build_incoming_edge_lookup(
        self,
        context: CompilationContext
    ) -> Dict[str, List[DataFlowEdge]]:
        """Build a lookup of incoming edges keyed by target node id."""

        incoming: Dict[str, List[DataFlowEdge]] = defaultdict(list)
        for edge in context.edges:
            incoming[edge.target].append(edge)
        return incoming

    def _indent_block(self, lines: List[str], level: int = 1) -> str:
        """Indent a list of code lines."""

        indent = "    " * level
        return "\n".join(f"{indent}{line}" for line in lines)

    def _sanitize_identifier(self, value: str) -> str:
        """Return a Python-friendly identifier based on a node id."""

        safe = []
        for char in value:
            if char.isalnum():
                safe.append(char.lower())
            else:
                safe.append("_")
        result = "".join(safe).strip("_")
        return result or "node"

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
    def get_incoming(self, node_id: str) -> List[Tuple[str, str, str]]:
        """Get incoming connections for a node."""

        if not self._compilation_context:
            return []

        edges = self._compilation_context.incoming_edges.get(node_id, [])
        sorted_edges = sorted(edges, key=lambda e: (e.target_handle, e.source, e.source_handle))
        return [
            (edge.source, edge.source_handle, edge.target_handle)
            for edge in sorted_edges
        ]

    def generate_strategy_code(self, workflow: Dict[str, Any], name: str = "GeneratedStrategy") -> Dict[str, Any]:
        """Backward compatibility method."""
        return self.compile_workflow(workflow, OutputMode.TRAINING)


# Backward compatibility
CodeGenerator = EnhancedCodeGenerator

__all__ = ["EnhancedCodeGenerator", "CodeGenerator", "OutputMode", "DataType"]