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
import functools
import json
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Set, Optional, Union, Tuple
from collections import defaultdict, deque

from ir import Node, Edge, Workflow
from node_handlers import HANDLER_REGISTRY, FALLBACK_HANDLER


@dataclass
class ModuleSections:
    """Intermediate representation of module snippets before emission."""

    header: str
    imports: List[str]
    functions: List[str] = field(default_factory=list)
    adapters: List[str] = field(default_factory=list)


class SnippetMerger:
    """Utility to deduplicate and merge code snippets deterministically."""

    def __init__(self) -> None:
        self._sections: List[str] = []
        self._seen: Set[str] = set()

    def add(self, snippet: Optional[str]) -> None:
        if not snippet:
            return
        normalized = textwrap.dedent(snippet).strip()
        if not normalized or normalized in self._seen:
            return
        self._sections.append(normalized)
        self._seen.add(normalized)

    def build(self) -> str:
        return "\n\n".join(self._sections) + "\n"


class BaseEmitter:
    """Base emitter for converting module sections into final source."""

    name = "base"
    code_type = "module"

    def render(self, sections: ModuleSections) -> str:
        merger = SnippetMerger()
        merger.add(sections.header)
        merger.add(self._merge_imports(sections.imports + self.required_imports()))
        for func in sections.functions:
            merger.add(func)
        for adapter in self.additional_helpers():
            merger.add(adapter)
        for adapter in sections.adapters:
            merger.add(adapter)
        return merger.build()

    def required_imports(self) -> List[str]:
        return []

    def additional_helpers(self) -> List[str]:
        return []

    @staticmethod
    def _merge_imports(import_lines: List[str]) -> str:
        merged: List[str] = []
        seen: Set[str] = set()
        for line in import_lines:
            cleaned = line.rstrip()
            if not cleaned and (not merged or merged[-1] == ""):
                continue
            if cleaned.startswith("import ") or cleaned.startswith("from "):
                if cleaned not in seen:
                    merged.append(cleaned)
                    seen.add(cleaned)
            elif cleaned:
                merged.append(cleaned)
            else:
                merged.append(cleaned)
        return "\n".join(merged)


class BacktestEmitter(BaseEmitter):
    name = "backtesting"

    def required_imports(self) -> List[str]:
        return []

    def additional_helpers(self) -> List[str]:
        return []


class LiveTradingEmitter(BaseEmitter):
    name = "live_trading"

    def required_imports(self) -> List[str]:
        return []

    def additional_helpers(self) -> List[str]:
        return []


class TrainingEmitter(BaseEmitter):
    name = "training"

    def required_imports(self) -> List[str]:
        return []

    def additional_helpers(self) -> List[str]:
        return []


class ResearchEmitter(BaseEmitter):
    name = "research"

    def required_imports(self) -> List[str]:
        return ["import matplotlib.pyplot as plt"]

    def additional_helpers(self) -> List[str]:
        return [
            textwrap.dedent(
                """
                def visualize_signals(df: pd.DataFrame) -> None:
                    \"\"\"Quick visualization helper for research workflows.\"\"\"
                    plt.figure(figsize=(12, 5))
                    df['close'].plot(label='Close')
                    for column in df.columns:
                        if column.startswith('decision_'):
                            df[column].replace({'BUY': 1, 'SELL': -1, 'HOLD': 0}).plot(alpha=0.4, label=column)
                    plt.legend()
                    plt.title('Strategy Decisions vs Price')
                    plt.show()
                """
            ).strip()
        ]


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
        self.emitters = {
            OutputMode.BACKTESTING: BacktestEmitter(),
            OutputMode.LIVE_TRADING: LiveTradingEmitter(),
            OutputMode.TRAINING: TrainingEmitter(),
            OutputMode.RESEARCH: ResearchEmitter(),
        }
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
        requested_mode = workflow.get("config", {}).get("target_mode") or workflow.get("config", {}).get("execution_target")
        if requested_mode:
            context.target_mode = self._resolve_output_mode(requested_mode, context.target_mode)

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

            # Logic gates support a variable number of signal inputs.
            if node.type == "logic":
                desired_inputs = node.data.get("parameters", {}).get(
                    "inputs",
                    len(node.input_types),
                )
                for index in range(desired_inputs):
                    handle = f"input-{index}"
                    node.input_types.setdefault(handle, DataType.SIGNAL)
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

        # Extract handles using enriched IR metadata
        source_handle = edge.source_handle or self._default_handle(source_node.output_types, fallback="data-output")
        target_handle = edge.target_handle or self._default_handle(target_node.input_types, fallback="data-input")
        
        # If edge has rule data, use its data type
        data_type = DataType.UNKNOWN
        rule = (edge.metadata or {}).get('rule', {})
        candidate_type = (
            edge.data_type
            or rule.get('dataType')
            or rule.get('data_type')
        )
        if candidate_type and candidate_type in [dt.value for dt in DataType]:
            data_type = DataType(candidate_type)
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

    @staticmethod
    def _default_handle(handle_map: Dict[str, DataType], fallback: str) -> str:
        """Return a deterministic handle when metadata is missing."""
        if handle_map:
            return next(iter(handle_map.keys()))
        return fallback

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
            optimization_pass(context)

    def _dead_code_elimination(self, context: CompilationContext) -> None:
        """Remove unreachable nodes."""
        
        # Find nodes that don't contribute to any output
        contributing_nodes = set()
        root_types = {"action", "output", "risk", "riskManagement"}
        queue = deque(
            node_id for node_id, node in context.nodes.items() if node.type in root_types
        )
        
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
        if dead_nodes:
            self._purge_nodes(context, dead_nodes, reason="dead_code_eliminated")

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
        duplicates: Set[str] = set()
        for signature, nodes in expression_groups.items():
            if len(nodes) > 1:
                primary = nodes[0]
                for dup in nodes[1:]:
                    duplicates.add(dup)
                    # Reroute edges produced by duplicate to primary
                    for edge in context.edges:
                        if edge.source == dup:
                            edge.source = primary
                context.nodes[primary].optimizations.append("common_subexpression_primary")

        if duplicates:
            self._purge_nodes(context, duplicates, reason="common_subexpression_eliminated")

    def _constant_folding(self, context: CompilationContext) -> None:
        """Fold constant expressions."""
        
        for node_id, node in context.nodes.items():
            if node.type == "condition":
                params = node.data.get("parameters", {})
                
                # If all inputs are constants, mark for constant folding
                if all(isinstance(params.get(key), (int, float)) for key in ["value", "value2"] if key in params):
                    node.optimizations.append("constant_folded")
                    params["constantValue"] = params.get("value")

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

    def _purge_nodes(self, context: CompilationContext, node_ids: Set[str], reason: str) -> None:
        """Remove nodes and all associated edges."""

        for node_id in node_ids:
            typed_node = context.nodes.get(node_id)
            if typed_node:
                typed_node.optimizations.append(reason)
                del context.nodes[node_id]
            context.incoming_edges.pop(node_id, None)
            context.outgoing_edges.pop(node_id, None)

        context.edges = [
            edge for edge in context.edges
            if edge.source not in node_ids and edge.target not in node_ids
        ]
        for edge_list in context.incoming_edges.values():
            edge_list[:] = [
                edge for edge in edge_list
                if edge.source not in node_ids and edge.target not in node_ids
            ]
        for edge_list in context.outgoing_edges.values():
            edge_list[:] = [
                edge for edge in edge_list
                if edge.source not in node_ids and edge.target not in node_ids
            ]

    def _resolve_output_mode(self, candidate: Any, fallback: OutputMode) -> OutputMode:
        """Resolve string or enum values into a valid OutputMode."""

        if isinstance(candidate, OutputMode):
            return candidate
        if isinstance(candidate, str):
            normalized = candidate.upper()
            alias_map = {
                "BACKTEST": OutputMode.BACKTESTING,
                "BACKTESTING": OutputMode.BACKTESTING,
                "LIVE": OutputMode.LIVE_TRADING,
                "LIVE_TRADING": OutputMode.LIVE_TRADING,
                "TRAINING": OutputMode.TRAINING,
                "RESEARCH": OutputMode.RESEARCH,
            }
            return alias_map.get(normalized, fallback)
        return fallback

    def _generate_code(self, context: CompilationContext, config: Dict[str, Any]) -> Dict[str, str]:
        """Phase 6: Generate a standalone Python module for the workflow."""

        if context.errors:
            return {"error": "Compilation failed with errors"}

        sorted_nodes = sorted(
            context.nodes.values(),
            key=lambda node: node.execution_order
        )

        sections = self._assemble_strategy_module(sorted_nodes, context)
        emitter = self.emitters.get(context.target_mode, self.emitters[OutputMode.BACKTESTING])
        module_source = emitter.render(sections)

        return {
            "main": module_source,
            "type": emitter.code_type,
            "emitter": emitter.name
        }

    # ------------------------------------------------------------------
    # Module assembly helpers
    # ------------------------------------------------------------------
    def _assemble_strategy_module(
        self,
        nodes: List[TypedNode],
        context: CompilationContext
    ) -> ModuleSections:
        """Collect module sections prior to final emission."""

        header = self._emit_module_header()
        imports = self._emit_import_block().splitlines()

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

        functions = [fn for fn in [data_fn, analysis_fn, indicator_fn, condition_fn, logic_fn, risk_fn, action_fn, run_fn] if fn]
        adapters = [self._emit_data_helpers()]

        return ModuleSections(
            header=header,
            imports=imports,
            functions=functions,
            adapters=adapters,
        )

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

    def _emit_data_helpers(self) -> str:
        """Emit helper utilities for market data ingestion."""

        return textwrap.dedent(
            """
            DATA_CACHE: dict[str, pd.DataFrame] = {}
            STREAMING_LOADERS: list = []
            CUSTOM_DATA_LOADER = None
            DB_ENGINE = None

            def register_market_data_loader(callback) -> None:
                # Allow tests or runners to override data ingestion.
                global CUSTOM_DATA_LOADER
                CUSTOM_DATA_LOADER = callback

            def register_streaming_loader(callback) -> None:
                if callback and callback not in STREAMING_LOADERS:
                    STREAMING_LOADERS.append(callback)

            def _normalize_timeframe(value: str) -> str:
                if not value:
                    return "1H"
                value = value.strip()
                lower = value.lower()
                mapping = {
                    "min": "T",
                    "m": "T",
                    "h": "H",
                    "d": "D",
                }
                for suffix, replacement in mapping.items():
                    if lower.endswith(suffix):
                        magnitude = value[: -len(suffix)] or "1"
                        return f"{magnitude}{replacement}"
                return value.upper()

            def _ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
                if not isinstance(df.index, pd.DatetimeIndex):
                    if "timestamp" in df.columns:
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                        df = df.set_index("timestamp")
                    else:
                        inferred = pd.to_datetime(df.index, errors="coerce")
                        if inferred.isnull().all():
                            inferred = pd.date_range(
                                end=pd.Timestamp.utcnow(),
                                periods=len(df),
                                freq="1H",
                            )
                        df.index = inferred
                return df

            def _normalize_price_frame(df: pd.DataFrame, timeframe: str, bars: int) -> pd.DataFrame:
                if df is None or df.empty:
                    return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
                df = _ensure_datetime_index(df)
                df = df.sort_index()
                df = df[~df.index.duplicated(keep="last")]
                if "close" not in df.columns:
                    first_column = df.columns[0] if len(df.columns) else "close"
                    df["close"] = df.get("open", df.get("price", df.get(first_column, 0)))
                for column in ["open", "high", "low", "close", "volume"]:
                    if column not in df.columns:
                        if column == "volume":
                            df[column] = 0.0
                        else:
                            df[column] = df["close"]
                rule = _normalize_timeframe(timeframe)
                try:
                    aggregated = df.resample(rule).agg(
                        {
                            "open": "first",
                            "high": "max",
                            "low": "min",
                            "close": "last",
                            "volume": "sum",
                        }
                    )
                    if not aggregated.empty:
                        df = aggregated
                except Exception:
                    pass
                df = df.ffill().bfill()
                if bars:
                    df = df.tail(int(bars))
                df.index.name = "timestamp"
                return df

            def _load_from_custom(**kwargs):
                if CUSTOM_DATA_LOADER is None:
                    return None
                try:
                    return CUSTOM_DATA_LOADER(**kwargs)
                except Exception as exc:  # pragma: no cover - debug helper
                    warnings.warn(f"Custom market data loader failed: {exc}")
                    return None

            def _load_from_stream(**kwargs):
                for loader in STREAMING_LOADERS:
                    try:
                        data = loader(**kwargs)
                        if data is not None:
                            return data
                    except Exception as exc:  # pragma: no cover - user hooks
                        warnings.warn(f"Streaming loader error: {exc}")
                return None

            def _load_from_rest(**kwargs):
                api_url = os.getenv("MARKET_DATA_API_URL")
                if not api_url:
                    return None
                params = {
                    "symbol": kwargs.get("symbol"),
                    "timeframe": kwargs.get("timeframe"),
                    "limit": kwargs.get("bars"),
                }
                if kwargs.get("start_at"):
                    params["start"] = kwargs["start_at"]
                if kwargs.get("end_at"):
                    params["end"] = kwargs["end_at"]
                if kwargs.get("source"):
                    params["source"] = kwargs["source"]
                if kwargs.get("asset_class"):
                    params["asset_class"] = kwargs["asset_class"]
                headers = {}
                api_key = os.getenv("MARKET_DATA_API_KEY")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                try:
                    response = requests.get(
                        api_url,
                        params=params,
                        headers=headers,
                        timeout=float(os.getenv("MARKET_DATA_TIMEOUT", 5)),
                    )
                    response.raise_for_status()
                    payload = response.json()
                except Exception as exc:  # pragma: no cover - network code
                    warnings.warn(f"REST market data call failed: {exc}")
                    return None
                records = None
                if isinstance(payload, dict):
                    records = payload.get("data") or payload.get("bars") or payload.get("results")
                if records is None:
                    records = payload
                df = pd.DataFrame(records or [])
                if df.empty:
                    return None
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df = df.set_index("timestamp")
                return df

            def _load_from_database(**kwargs):
                db_url = os.getenv("MARKET_DATA_DB_URL")
                if not db_url or create_engine is None or sqlalchemy_text is None:
                    return None
                global DB_ENGINE
                if DB_ENGINE is None:
                    DB_ENGINE = create_engine(db_url)
                filters = ["symbol = :symbol", "timeframe = :timeframe"]
                params = {
                    "symbol": kwargs.get("symbol"),
                    "timeframe": kwargs.get("timeframe"),
                    "limit": int(kwargs.get("bars") or 500),
                }
                if kwargs.get("start_at"):
                    filters.append("timestamp >= :start_at")
                    params["start_at"] = kwargs["start_at"]
                if kwargs.get("end_at"):
                    filters.append("timestamp <= :end_at")
                    params["end_at"] = kwargs["end_at"]
                query = f'''
                    SELECT timestamp, open, high, low, close, volume
                    FROM market_data
                    WHERE {' AND '.join(filters)}
                    ORDER BY timestamp DESC
                    LIMIT :limit
                '''
                try:
                    with DB_ENGINE.connect() as conn:
                        rows = conn.execute(sqlalchemy_text(query), params).fetchall()
                except Exception as exc:  # pragma: no cover - db code
                    warnings.warn(f"Database market data call failed: {exc}")
                    return None
                if not rows:
                    return None
                df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.set_index("timestamp")
                return df

            def _generate_synthetic_series(symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
                bars = max(int(bars or 0), 250)
                freq = _normalize_timeframe(timeframe)
                digest = hashlib.sha256(f"{symbol}:{timeframe}:{bars}".encode("utf-8")).digest()
                seed = int.from_bytes(digest[:8], "big", signed=False)
                rng = np.random.default_rng(seed)
                index = pd.date_range(end=pd.Timestamp.utcnow(), periods=bars, freq=freq)
                steps = np.arange(bars)
                base_trend = 100 + np.sin(steps / 18.0) * 4 + np.cos(steps / 7.0) * 2
                drift = np.linspace(-1.5, 1.5, bars)
                noise = rng.normal(0, 0.4, bars)
                close = base_trend + drift + noise
                open_ = close + rng.normal(0, 0.2, bars)
                high = np.maximum(open_, close) + np.abs(rng.normal(0, 0.3, bars))
                low = np.minimum(open_, close) - np.abs(rng.normal(0, 0.3, bars))
                volume = 1500 + (np.sin(steps / 12.0) + 1.2) * 500 + rng.normal(0, 50, bars)
                df = pd.DataFrame(
                    {
                        "open": open_,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                    },
                    index=index,
                )
                df.index.name = "timestamp"
                return df

            def _fetch_market_data(
                *,
                symbol: str,
                timeframe: str,
                bars: int,
                source: str = "system",
                asset_class: str | None = None,
                start_at: str | None = None,
                end_at: str | None = None,
                live: bool | str = False,
            ) -> pd.DataFrame:
                bars = max(int(bars or 0), 1)
                cache_key = f"{symbol}:{timeframe}:{bars}:{source}:{start_at}:{end_at}:{asset_class}"
                use_cache = os.getenv("MARKET_DATA_DISABLE_CACHE", "0").lower() not in {"1", "true", "yes"}
                if use_cache and cache_key in DATA_CACHE:
                    return DATA_CACHE[cache_key].copy()

                loader_kwargs = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bars": bars,
                    "source": source,
                    "asset_class": asset_class,
                    "start_at": start_at,
                    "end_at": end_at,
                    "live": bool(live),
                }

                loaders = [_load_from_custom, _load_from_stream, _load_from_rest, _load_from_database]
                data_frame = None
                for loader in loaders:
                    if loader is None:
                        continue
                    candidate = loader(**loader_kwargs)
                    if candidate is None or candidate.empty:
                        continue
                    data_frame = _normalize_price_frame(candidate, timeframe, bars)
                    break

                if data_frame is None:
                    allow_synthetic = os.getenv("MARKET_DATA_ALLOW_SYNTHETIC", "true").lower() in {"1", "true", "yes"}
                    if not allow_synthetic:
                        raise RuntimeError("Market data unavailable and synthetic generation disabled")
                    warnings.warn(
                        "Falling back to synthetic market data - configure MARKET_DATA_API_URL or MARKET_DATA_DB_URL"
                    )
                    data_frame = _generate_synthetic_series(symbol, timeframe, bars)

                if use_cache:
                    DATA_CACHE[cache_key] = data_frame.copy()
                return data_frame.copy()
            """
        ).strip()

    def _emit_import_block(self) -> str:
        """Emit the imports required for the lightweight module."""

        imports = [
            "from __future__ import annotations",
            "",
            "import functools",
            "import hashlib",
            "import json",
            "import os",
            "import warnings",
            "",
            "import numpy as np",
            "import pandas as pd",
            "import requests",
        ]
        imports.append(
            textwrap.dedent(
                """
USE_PANDAS_TA = os.getenv("USE_PANDAS_TA", "0").lower() in {"1", "true", "yes"}
if USE_PANDAS_TA:
    try:
        import pandas_ta as pd_ta
    except ImportError:  # pragma: no cover - optional dependency
        pd_ta = None
else:  # pragma: no cover - env-controlled
    pd_ta = None
                """
            ).strip()
        )
        imports.append(
            textwrap.dedent(
                """
try:
    import talib as ta_lib
except ImportError:  # pragma: no cover - optional dependency
    ta_lib = None
                """
            ).strip()
        )
        imports.append(
            textwrap.dedent(
                """
try:
    from sqlalchemy import create_engine, text as sqlalchemy_text
except ImportError:  # pragma: no cover - optional dependency
    create_engine = None
    sqlalchemy_text = None
                """
            ).strip()
        )
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

        primary_node = data_nodes[0]
        params = primary_node.data.get("parameters", {})
        symbol = params.get("symbol", primary_node.data.get("label", primary_node.id))
        timeframe = params.get("timeframe", "1h")
        bars = int(params.get("bars", 250))
        source = params.get("dataSource", params.get("provider", "system"))
        asset_class = params.get("assetClass") or params.get("asset_class")
        start_at = (
            params.get("startDate")
            or params.get("fromDate")
            or params.get("start")
            or params.get("from")
        )
        end_at = (
            params.get("endDate")
            or params.get("toDate")
            or params.get("end")
            or params.get("to")
        )
        live_mode_hint = str(
            params.get("mode")
            or params.get("executionMode")
            or params.get("sessionType")
            or ""
        ).lower()
        live_toggle = params.get("live") or params.get("liveData") or params.get("paperTrading")
        if isinstance(live_toggle, str):
            live_toggle = live_toggle.lower() in {"true", "1", "yes", "live", "paper"}
        else:
            live_toggle = bool(live_toggle)
        live_flag = live_toggle or live_mode_hint in {"live", "paper"}

        asset_class_literal = repr(asset_class) if asset_class else "None"
        start_literal = repr(start_at) if start_at else "None"
        end_literal = repr(end_at) if end_at else "None"
        source_literal = repr(source) if source else "'system'"
        live_literal = "True" if live_flag else "False"

        body.extend([
            f"# Data source: {symbol} ({timeframe})",
            (
                "df = _fetch_market_data("
                f"symbol='{symbol}', "
                f"timeframe='{timeframe}', "
                f"bars={bars}, "
                f"source={source_literal}, "
                f"asset_class={asset_class_literal}, "
                f"start_at={start_literal}, "
                f"end_at={end_literal}, "
                f"live={live_literal}"
                ")"
            ),
            "return df",
        ])
        value_map[(primary_node.id, "data-output")] = "df"
        for node in data_nodes[1:]:
            value_map[(node.id, "data-output")] = "df"

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
            indicator_label = params.get("indicator") or node.data.get("label") or "SMA"
            indicator = self._normalize_indicator_name(indicator_label)
            period = max(1, int(params.get("period", params.get("timeperiod", 14))))
            source_column = params.get("source", "close")
            safe_id = self._sanitize_identifier(node.id)

            data_expr = self._resolve_input_expression(
                node.id,
                "data-input",
                value_map,
                incoming_edges,
                fallback="df['close']"
            )
            if data_expr == "df":
                series_expr = f"df['{source_column}']"
            elif data_expr and data_expr.startswith("df_multi_"):
                series_expr = (
                    f"{data_expr}['{source_column}'] "
                    f"if '{source_column}' in {data_expr}.columns "
                    f"else {data_expr}.iloc[:, 0]"
                )
            else:
                series_expr = data_expr or f"df['{source_column}']"

            source_alias = f"series_{safe_id}"
            body.append(f"# Indicator: {indicator_label} ({node.id})")
            body.append(f"{source_alias} = {series_expr}")
            body.extend([
                f"if isinstance({source_alias}, pd.DataFrame):",
                f"    if '{source_column}' in {source_alias}.columns:",
                f"        {source_alias} = {source_alias}['{source_column}']",
                f"    else:",
                f"        {source_alias} = {source_alias}.iloc[:, 0]",
                f"if not isinstance({source_alias}, pd.Series):",
                f"    {source_alias} = pd.Series({source_alias}, index=df.index)",
                f"{source_alias} = {source_alias}.astype(float).fillna(method='ffill').fillna(method='bfill')",
            ])

            indicator_lower = indicator.lower()

            if indicator == "RSI":
                column_name = f"rsi_{safe_id}"
                body.extend([
                    "if ta_lib is not None and hasattr(ta_lib, 'RSI'):",
                    f"    df['{column_name}'] = pd.Series(ta_lib.RSI({source_alias}.to_numpy(), timeperiod={period}), index=df.index)",
                    "elif pd_ta is not None and hasattr(pd_ta, 'rsi'):",
                    f"    df['{column_name}'] = pd.Series(pd_ta.rsi({source_alias}, length={period}), index=df.index)",
                    "else:",
                    f"    delta_{safe_id} = {source_alias}.diff()",
                    f"    gain_{safe_id} = delta_{safe_id}.where(delta_{safe_id} > 0, 0.0)",
                    f"    loss_{safe_id} = (-delta_{safe_id}).where(delta_{safe_id} < 0, 0.0)",
                    f"    avg_gain_{safe_id} = gain_{safe_id}.rolling(window={period}, min_periods=1).mean()",
                    f"    avg_loss_{safe_id} = loss_{safe_id}.rolling(window={period}, min_periods=1).mean()",
                    f"    rs_{safe_id} = avg_gain_{safe_id} / avg_loss_{safe_id}.replace(0, np.nan)",
                    f"    df['{column_name}'] = 100 - (100 / (1 + rs_{safe_id}))",
                    f"df['{column_name}'] = df['{column_name}'].fillna(method='bfill').fillna(50)",
                ])
                value_map[(node.id, "output-1")] = f"df['{column_name}']"
            elif indicator in {"SMA", "SIMPLE_MOVING_AVERAGE"}:
                column_name = f"sma_{source_column}_{safe_id}"
                body.extend([
                    "if ta_lib is not None and hasattr(ta_lib, 'SMA'):",
                    f"    df['{column_name}'] = pd.Series(ta_lib.SMA({source_alias}.to_numpy(), timeperiod={period}), index=df.index)",
                    "elif pd_ta is not None and hasattr(pd_ta, 'sma'):",
                    f"    df['{column_name}'] = pd.Series(pd_ta.sma({source_alias}, length={period}, min_periods=1), index=df.index)",
                    "else:",
                    f"    df['{column_name}'] = {source_alias}.rolling(window={period}, min_periods=1).mean()",
                    f"df['{column_name}'] = df['{column_name}'].ffill().bfill()",
                ])
                value_map[(node.id, "output-1")] = f"df['{column_name}']"
            elif indicator in {"EMA", "EXPONENTIAL_MOVING_AVERAGE"}:
                column_name = f"ema_{source_column}_{safe_id}"
                body.extend([
                    "if ta_lib is not None and hasattr(ta_lib, 'EMA'):",
                    f"    df['{column_name}'] = pd.Series(ta_lib.EMA({source_alias}.to_numpy(), timeperiod={period}), index=df.index)",
                    "elif pd_ta is not None and hasattr(pd_ta, 'ema'):",
                    f"    df['{column_name}'] = pd.Series(pd_ta.ema({source_alias}, length={period}, min_periods=1), index=df.index)",
                    "else:",
                    f"    df['{column_name}'] = {source_alias}.ewm(span={period}, adjust=False).mean()",
                    f"df['{column_name}'] = df['{column_name}'].ffill().bfill()",
                ])
                value_map[(node.id, "output-1")] = f"df['{column_name}']"
            elif indicator == "MACD":
                fast = int(params.get("fastPeriod", params.get("fast", 12)))
                slow = int(params.get("slowPeriod", params.get("slow", 26)))
                signal_period = int(params.get("signalPeriod", params.get("signal", 9)))
                macd_col = f"macd_line_{safe_id}"
                signal_col = f"macd_signal_{safe_id}"
                hist_col = f"macd_hist_{safe_id}"
                body.extend([
                    "if ta_lib is not None and hasattr(ta_lib, 'MACD'):",
                    f"    macd_vals, signal_vals, hist_vals = ta_lib.MACD({source_alias}.to_numpy(), fastperiod={fast}, slowperiod={slow}, signalperiod={signal_period})",
                    f"    df['{macd_col}'] = pd.Series(macd_vals, index=df.index)",
                    f"    df['{signal_col}'] = pd.Series(signal_vals, index=df.index)",
                    f"    df['{hist_col}'] = pd.Series(hist_vals, index=df.index)",
                    "elif pd_ta is not None and hasattr(pd_ta, 'macd'):",
                    f"    macd_df = pd_ta.macd({source_alias}, fast={fast}, slow={slow}, signal={signal_period})",
                    f"    if isinstance(macd_df, pd.DataFrame) and macd_df.shape[1] >= 3:",
                    f"        df['{macd_col}'] = macd_df.iloc[:, 0]",
                    f"        df['{hist_col}'] = macd_df.iloc[:, 1]",
                    f"        df['{signal_col}'] = macd_df.iloc[:, 2]",
                    "    else:",
                    f"        df['{macd_col}'] = macd_df",
                    f"        df['{signal_col}'] = macd_df",
                    f"        df['{hist_col}'] = macd_df * 0",
                    "else:",
                    f"    ema_fast_{safe_id} = {source_alias}.ewm(span={fast}, adjust=False).mean()",
                    f"    ema_slow_{safe_id} = {source_alias}.ewm(span={slow}, adjust=False).mean()",
                    f"    df['{macd_col}'] = ema_fast_{safe_id} - ema_slow_{safe_id}",
                    f"    df['{signal_col}'] = df['{macd_col}'].ewm(span={signal_period}, adjust=False).mean()",
                    f"    df['{hist_col}'] = df['{macd_col}'] - df['{signal_col}']",
                ])
                for col in [macd_col, signal_col, hist_col]:
                    body.append(f"df['{col}'] = df['{col}'].ffill().bfill()")
                value_map[(node.id, "output-1")] = f"df['{macd_col}']"
                value_map[(node.id, "output-2")] = f"df['{signal_col}']"
                value_map[(node.id, "output-3")] = f"df['{hist_col}']"
            elif indicator in {"BB", "BOLLINGER", "BOLLINGER_BANDS"}:
                multiplier = float(params.get("multiplier", params.get("std", 2)))
                middle_col = f"bollinger_mid_{safe_id}"
                upper_col = f"bollinger_upper_{safe_id}"
                lower_col = f"bollinger_lower_{safe_id}"
                body.extend([
                    "if ta_lib is not None and hasattr(ta_lib, 'BBANDS'):",
                    f"    upper_band, middle_band, lower_band = ta_lib.BBANDS({source_alias}.to_numpy(), timeperiod={period}, nbdevup={multiplier}, nbdevdn={multiplier}, matype=0)",
                    f"    df['{upper_col}'] = pd.Series(upper_band, index=df.index)",
                    f"    df['{middle_col}'] = pd.Series(middle_band, index=df.index)",
                    f"    df['{lower_col}'] = pd.Series(lower_band, index=df.index)",
                    "elif pd_ta is not None and hasattr(pd_ta, 'bbands'):",
                    f"    bb_df = pd_ta.bbands({source_alias}, length={period}, std={multiplier})",
                    f"    if isinstance(bb_df, pd.DataFrame) and bb_df.shape[1] >= 3:",
                    f"        df['{lower_col}'] = bb_df.iloc[:, 0]",
                    f"        df['{middle_col}'] = bb_df.iloc[:, 1]",
                    f"        df['{upper_col}'] = bb_df.iloc[:, 2]",
                    "    else:",
                    f"        df['{middle_col}'] = bb_df",
                    f"        df['{upper_col}'] = bb_df",
                    f"        df['{lower_col}'] = bb_df",
                    "else:",
                    f"    rolling_mean_{safe_id} = {source_alias}.rolling(window={period}, min_periods=1).mean()",
                    f"    rolling_std_{safe_id} = {source_alias}.rolling(window={period}, min_periods=1).std().fillna(0)",
                    f"    df['{middle_col}'] = rolling_mean_{safe_id}",
                    f"    df['{upper_col}'] = df['{middle_col}'] + ({multiplier} * rolling_std_{safe_id})",
                    f"    df['{lower_col}'] = df['{middle_col}'] - ({multiplier} * rolling_std_{safe_id})",
                ])
                for col in [upper_col, middle_col, lower_col]:
                    body.append(f"df['{col}'] = df['{col}'].ffill().bfill()")
                value_map[(node.id, "output-1")] = f"df['{middle_col}']"
                value_map[(node.id, "output-2")] = f"df['{upper_col}']"
                value_map[(node.id, "output-3")] = f"df['{lower_col}']"
            elif indicator in {"ATR", "AVERAGE_TRUE_RANGE"}:
                column_name = f"atr_{safe_id}"
                body.extend([
                    "if ta_lib is not None and hasattr(ta_lib, 'ATR'):",
                    f"    df['{column_name}'] = pd.Series(ta_lib.ATR(df['high'].to_numpy(), df['low'].to_numpy(), df['close'].to_numpy(), timeperiod={period}), index=df.index)",
                    "elif pd_ta is not None and hasattr(pd_ta, 'atr'):",
                    f"    df['{column_name}'] = pd.Series(pd_ta.atr(high=df['high'], low=df['low'], close=df['close'], length={period}), index=df.index)",
                    "else:",
                    f"    high_low_{safe_id} = (df['high'] - df['low']).abs()",
                    f"    high_close_{safe_id} = (df['high'] - df['close'].shift()).abs()",
                    f"    low_close_{safe_id} = (df['low'] - df['close'].shift()).abs()",
                    f"    true_range_{safe_id} = pd.concat([high_low_{safe_id}, high_close_{safe_id}, low_close_{safe_id}], axis=1).max(axis=1)",
                    f"    df['{column_name}'] = true_range_{safe_id}.rolling(window={period}, min_periods=1).mean()",
                    f"df['{column_name}'] = df['{column_name}'].ffill().bfill()",
                ])
                value_map[(node.id, "output-1")] = f"df['{column_name}']"
            elif indicator in {"VWAP", "VOLUME_WEIGHTED_AVERAGE_PRICE"}:
                column_name = f"vwap_{safe_id}"
                body.extend([
                    f"typical_price_{safe_id} = (df['high'] + df['low'] + df['close']) / 3",
                    f"volume_{safe_id} = df['volume'].replace(0, np.nan)",
                    f"cumulative_value_{safe_id} = (typical_price_{safe_id} * volume_{safe_id}).cumsum()",
                    f"df['{column_name}'] = cumulative_value_{safe_id} / volume_{safe_id}.cumsum()",
                    f"df['{column_name}'] = df['{column_name}'].ffill().bfill()",
                ])
                value_map[(node.id, "output-1")] = f"df['{column_name}']"
            elif indicator in {"WMA", "WEIGHTED_MOVING_AVERAGE"}:
                column_name = f"wma_{source_column}_{safe_id}"
                body.extend([
                    "if pd_ta is not None and hasattr(pd_ta, 'wma'):",
                    f"    df['{column_name}'] = pd.Series(pd_ta.wma({source_alias}, length={period}), index=df.index)",
                    "else:",
                    f"    weights_{safe_id} = np.arange(1, {period} + 1)",
                    f"    df['{column_name}'] = {source_alias}.rolling(window={period}).apply(lambda values: np.dot(values, weights_{safe_id}) / weights_{safe_id}.sum(), raw=True)",
                    f"df['{column_name}'] = df['{column_name}'].ffill().bfill()",
                ])
                value_map[(node.id, "output-1")] = f"df['{column_name}']"
            else:
                column_name = f"indicator_{indicator_lower}_{safe_id}"
                body.extend([
                    f"df['{column_name}'] = {source_alias}",
                    f"df['{column_name}'] = df['{column_name}'].ffill().bfill()",
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
            condition_type = (params.get("conditionType") or params.get("type") or "comparison").lower()
            condition = (params.get("condition") or "greater_than").lower()
            default_value = params.get("value", 0)
            secondary_value = params.get("value2", params.get("valueMax", default_value))
            lookback = max(1, int(params.get("lookback", 1)))
            confirmation_bars = int(params.get("confirmationBars", params.get("confirmBars", 0)))
            cooldown_bars = int(params.get("cooldownBars", params.get("cooldown", 0)))
            sensitivity = float(params.get("sensitivity", 0) or 0)
            safe_id = self._sanitize_identifier(node.id)
            column_name = f"signal_{safe_id}"

            try:
                default_numeric = float(default_value)
            except (TypeError, ValueError):
                default_numeric = 0.0
            try:
                secondary_numeric = float(secondary_value)
            except (TypeError, ValueError):
                secondary_numeric = default_numeric

            left_expr = self._resolve_input_expression(
                node.id, "data-input", value_map, incoming_edges,
                fallback="df['close']"
            )
            right_expr = self._resolve_input_expression(
                node.id, "value-input", value_map, incoming_edges,
                fallback=repr(default_value if default_value is not None else 0)
            )
            aux_expr = self._resolve_input_expression(
                node.id, "aux-input", value_map, incoming_edges,
                fallback=None
            )

            has_value_input = any(
                edge.target_handle == "value-input"
                for edge in incoming_edges.get(node.id, [])
            )

            left_alias = f"left_{safe_id}"
            body.extend(self._coerce_series_lines(left_alias, left_expr or "df['close']", column_hint="close"))

            right_alias = f"right_{safe_id}"
            body.extend(self._coerce_series_lines(right_alias, right_expr or repr(default_numeric), column_hint="close"))

            aux_alias: Optional[str] = None
            if aux_expr is not None:
                aux_alias = f"aux_{safe_id}"
                body.extend(self._coerce_series_lines(aux_alias, aux_expr, column_hint="close"))

            adjusted_right = right_alias
            if sensitivity and condition in {"greater_than", "greater_than_equal", "greater_or_equal"}:
                adj_alias = f"threshold_{safe_id}"
                body.append(f"{adj_alias} = {right_alias} * (1 + ({sensitivity} / 100))")
                adjusted_right = adj_alias
            elif sensitivity and condition in {"less_than", "less_than_equal", "less_or_equal"}:
                adj_alias = f"threshold_{safe_id}"
                body.append(f"{adj_alias} = {right_alias} * (1 - ({sensitivity} / 100))")
                adjusted_right = adj_alias

            if condition_type == "crossover" or condition in {"cross_above", "cross_below", "cross_over", "cross_under"}:
                target_series = aux_alias or adjusted_right
                if condition in {"cross_below", "cross_under"}:
                    condition_expr = (
                        f"(({left_alias} < {target_series}) & "
                        f"({left_alias}.shift({lookback}) >= {target_series}.shift({lookback})))"
                    )
                else:
                    condition_expr = (
                        f"(({left_alias} > {target_series}) & "
                        f"({left_alias}.shift({lookback}) <= {target_series}.shift({lookback})))"
                    )
            elif condition_type in {"between", "range"} or condition == "between":
                lower_series = aux_alias
                upper_series = adjusted_right
                if lower_series is None:
                    lower_series = f"lower_{safe_id}"
                    low_value = min(default_numeric, secondary_numeric)
                    body.append(f"{lower_series} = pd.Series({repr(low_value)}, index=df.index)")
                if secondary_value is not None:
                    upper_series = f"upper_{safe_id}"
                    high_value = max(default_numeric, secondary_numeric)
                    body.append(f"{upper_series} = pd.Series({repr(high_value)}, index=df.index)")
                condition_expr = f"(({left_alias} >= {lower_series}) & ({left_alias} <= {upper_series}))"
                if condition in {"outside", "not_between"}:
                    condition_expr = f"~{condition_expr}"
            elif condition_type in {"percent_change", "momentum"} or condition == "percent_change":
                pct_alias = f"percent_change_{safe_id}"
                body.append(f"{pct_alias} = {left_alias}.pct_change(periods={lookback}).fillna(0) * 100")
                comparator = comparison_map.get(condition, comparison_map.get("greater_than"))
                condition_expr = f"({pct_alias}) {comparator} ({adjusted_right})"
            elif condition_type == "trend":
                if condition in {"falling", "bearish"}:
                    condition_expr = f"{left_alias} < {left_alias}.shift({lookback})"
                else:
                    condition_expr = f"{left_alias} > {left_alias}.shift({lookback})"
            elif (
                not has_value_input
                and condition_type == "comparison"
                and condition in {"less_than", "less_than_equal", "less_or_equal"}
                and 0 < abs(default_numeric) < 1
            ):
                price_alias = f"price_{safe_id}"
                body.extend(self._coerce_series_lines(price_alias, "df['close']", column_hint="close"))
                distance_alias = f"distance_{safe_id}"
                tolerance_alias = f"tolerance_{safe_id}"
                body.append(f"{distance_alias} = ({price_alias} - {left_alias}).abs()")
                body.append(f"{tolerance_alias} = {price_alias}.abs() * {abs(default_numeric)}")
                condition_expr = f"{distance_alias} <= {tolerance_alias}"
            else:
                comparator = comparison_map.get(condition, ">")
                condition_expr = f"({left_alias}) {comparator} ({adjusted_right})"

            base_series = f"condition_{safe_id}"
            body.append(f"{base_series} = ({condition_expr}).fillna(False)")
            current_series = base_series

            if confirmation_bars > 0:
                confirm_series = f"{base_series}_confirmed"
                body.extend([
                    f"{confirm_series} = {current_series}.copy()",
                    f"for offset in range(1, {confirmation_bars} + 1):",
                    f"    {confirm_series} &= {current_series}.shift(offset)",
                    f"{confirm_series} = {confirm_series}.fillna(False)",
                ])
                current_series = confirm_series

            if cooldown_bars > 0:
                cooled_values = f"cooldown_values_{safe_id}"
                cooldown_counter = f"cooldown_counter_{safe_id}"
                cooled_series = f"{current_series}_cooldown"
                body.extend([
                    f"{cooled_values} = []",
                    f"{cooldown_counter} = 0",
                    f"for flag in {current_series}.fillna(False):",
                    f"    if flag and {cooldown_counter} == 0:",
                    f"        {cooled_values}.append(True)",
                    f"        {cooldown_counter} = {cooldown_bars}",
                    f"    else:",
                    f"        {cooled_values}.append(False)",
                    f"        if {cooldown_counter} > 0:",
                    f"            {cooldown_counter} -= 1",
                    f"{cooled_series} = pd.Series({cooled_values}, index=df.index)",
                ])
                current_series = cooled_series

            body.append(f"df['{column_name}'] = {current_series}.fillna(False).astype(bool)")
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
            operation = (params.get("operation") or "AND").upper()
            safe_id = self._sanitize_identifier(node.id)
            column_name = f"logic_{safe_id}"

            inputs = self._resolve_logic_inputs(node.id, value_map, incoming_edges)
            expected_inputs = max(1, int(params.get("inputs", len(inputs) or 1)))
            provided_inputs = len(inputs)

            if not inputs:
                body.append(
                    f"warnings.warn(\"Logic node {node.id} has no inputs; defaulting to False\")"
                )
                inputs = ["pd.Series(False, index=df.index)"]
            elif provided_inputs < expected_inputs:
                body.append(
                    f"warnings.warn(\"Logic node {node.id} expected {expected_inputs} inputs but received {provided_inputs}; padding with False\")"
                )
                inputs.extend(["pd.Series(False, index=df.index)"] * (expected_inputs - provided_inputs))

            concat_inputs = ", ".join(inputs)

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
            elif operation == "WEIGHTED":
                weights_param = params.get("weights") or []
                weights: List[float] = []
                for idx in range(len(inputs)):
                    try:
                        weights.append(float(weights_param[idx]))
                    except (TypeError, ValueError, IndexError):
                        weights.append(1.0)
                weight_literal = ", ".join(str(weight) for weight in weights)
                threshold = float(params.get("threshold", 0.5))
                frame_alias = f"logic_frame_{safe_id}"
                weights_alias = f"logic_weights_{safe_id}"
                count_alias = f"logic_input_count_{safe_id}"
                score_alias = f"logic_weighted_{safe_id}"
                view_alias = f"logic_weights_view_{safe_id}"
                body.extend([
                    f"{frame_alias} = pd.concat([{concat_inputs}], axis=1).fillna(False).astype(int)",
                    f"{count_alias} = {frame_alias}.shape[1]",
                    f"{weights_alias} = np.array([{weight_literal}])",
                    f"{view_alias} = {weights_alias}[:{count_alias}] if {count_alias} > 0 else np.array([1.0])",
                    f"if {view_alias}.sum() == 0:",
                    f"    {view_alias} = np.ones_like({view_alias})",
                    f"{score_alias} = ({frame_alias}.iloc[:, :{count_alias}] * {view_alias}).sum(axis=1) / {view_alias}.sum()",
                    f"df['{column_name}'] = ({score_alias} >= {threshold}).fillna(False)",
                ])
                value_map[(node.id, "output")] = f"df['{column_name}']"
                continue
            else:
                combined_expr = " | ".join(f"({expr})" for expr in inputs)

            body.extend([
                f"# Logic ({operation}) for node {node.id}",
                f"df['{column_name}'] = ({combined_expr}).fillna(False)",
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
            risk_type = (params.get("riskType") or "position_size").lower()
            risk_category = (params.get("riskCategory") or "position").lower()
            lookback = max(2, int(params.get("lookback", 5)))

            max_loss_value = self._coerce_float(params.get("maxLoss"))
            portfolio_heat_value = self._coerce_float(params.get("portfolioHeat"))
            drawdown_limit_value = self._coerce_float(params.get("drawdownLimit") or params.get("maxDrawdown"))
            var_confidence_value = self._coerce_float(params.get("varConfidence"))
            leverage_limit_value = self._coerce_float(params.get("leverageLimit"))
            position_size_value = self._coerce_float(params.get("positionSize"))

            signal_expr = self._resolve_input_expression(
                node.id, "signal-input", value_map, incoming_edges,
                fallback=None
            )

            checks: List[str] = []

            if max_loss_value is not None:
                guard_alias = f"max_loss_guard_{safe_id}"
                body.append(
                    f"{guard_alias} = df['close'].pct_change().fillna(0).abs() * 100 <= {max_loss_value}"
                )
                checks.append(guard_alias)

            if portfolio_heat_value is not None:
                heat_guard = f"portfolio_heat_guard_{safe_id}"
                body.extend([
                    f"volatility_{safe_id} = df['close'].pct_change().rolling(window={max(lookback, 5)}, min_periods=2).std().fillna(0) * 100",
                    f"{heat_guard} = volatility_{safe_id} <= {portfolio_heat_value}",
                ])
                checks.append(heat_guard)

            if drawdown_limit_value is not None:
                peak_alias = f"peak_{safe_id}"
                drawdown_alias = f"drawdown_{safe_id}"
                guard_alias = f"drawdown_guard_{safe_id}"
                body.extend([
                    f"{peak_alias} = df['close'].cummax()",
                    f"{drawdown_alias} = ((df['close'] / {peak_alias}) - 1) * 100",
                    f"{guard_alias} = {drawdown_alias} >= -{drawdown_limit_value}",
                ])
                checks.append(guard_alias)

            if var_confidence_value is not None:
                var_guard = f"var_guard_{safe_id}"
                returns_alias = f"returns_{safe_id}"
                std_alias = f"rolling_std_{safe_id}"
                score_alias = f"var_score_{safe_id}"
                var_multiplier = self._approximate_zscore(var_confidence_value)
                var_window = max(lookback, 20)
                var_threshold = max_loss_value if max_loss_value is not None else (portfolio_heat_value or 5.0)
                body.extend([
                    f"{returns_alias} = df['close'].pct_change().fillna(0)",
                    f"{std_alias} = {returns_alias}.rolling(window={var_window}, min_periods=10).std().fillna(0)",
                    f"{score_alias} = {std_alias} * {var_multiplier} * 100",
                    f"{var_guard} = {score_alias} <= {var_threshold}",
                ])
                checks.append(var_guard)

            if leverage_limit_value is not None:
                body.append(f"df['risk_{safe_id}_leverage_limit'] = {leverage_limit_value}")

            if position_size_value is not None:
                body.append(f"df['risk_{safe_id}_allocation'] = {position_size_value}")

            if signal_expr:
                checks.append(signal_expr)

            if not checks:
                combined_expr = "pd.Series(True, index=df.index)"
            else:
                combined_expr = checks[0]
                for expr in checks[1:]:
                    combined_expr = f"({combined_expr}) & ({expr})"

            body.append(f"df['{column_name}'] = ({combined_expr}).fillna(False)")

            metadata_payload = {
                "node": node.id,
                "risk_type": risk_type,
                "category": risk_category,
                "max_loss": max_loss_value,
                "portfolio_heat": portfolio_heat_value,
                "drawdown": drawdown_limit_value,
                "var_confidence": var_confidence_value,
            }
            body.append("df.attrs.setdefault('risk_checks', [])")
            body.append(f"df.attrs['risk_checks'].append({repr(metadata_payload)})")

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
            action = (params.get("action") or "buy").upper()
            action_category = params.get("actionCategory", "entry")
            safe_id = self._sanitize_identifier(node.id)
            column_name = f"decision_{safe_id}"
            payload_column = f"payload_{safe_id}"
            structured_column = f"structured_decision_{safe_id}"

            signal_expr = self._resolve_input_expression(
                node.id, "signal-input", value_map, incoming_edges,
                fallback=None
            )
            risk_expr = self._resolve_input_expression(
                node.id, "risk-input", value_map, incoming_edges,
                fallback=None
            )

            if not signal_expr:
                signal_expr = "pd.Series(False, index=df.index)"

            trigger_expr = signal_expr
            if risk_expr:
                trigger_expr = f"({trigger_expr}) & ({risk_expr})"

            trigger_alias = f"action_trigger_{safe_id}"
            body.append(f"{trigger_alias} = ({trigger_expr}).fillna(False)")

            quantity = params.get("quantity", 1)
            order_type = params.get("order_type", "market")
            position_sizing = params.get("positionSizing")
            stop_loss = params.get("stop_loss")
            take_profit = params.get("take_profit")
            conditional = bool(params.get("conditional_execution"))

            payload = {
                "node_id": node.id,
                "action": action.lower(),
                "category": action_category,
                "quantity": quantity,
                "order_type": order_type,
                "position_sizing": position_sizing,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "conditional": conditional,
            }
            payload_alias = f"decision_payload_{safe_id}"
            body.append(f"{payload_alias} = {repr(payload)}")

            body.extend([
                f"df['{column_name}'] = np.where({trigger_alias}, '{action}', 'HOLD')",
                f"df['{payload_column}'] = np.where({trigger_alias}, {payload_alias}, None)",
                f"df['{structured_column}'] = np.where({trigger_alias}, {{'signal': '{action}', 'payload': {payload_alias}}}, None)",
            ])

            value_map[(node.id, "action-output")] = f"df['{structured_column}']"

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

    def _normalize_indicator_name(self, raw_indicator: Optional[str]) -> str:
        """Normalize indicator labels to canonical identifiers."""

        normalized = (raw_indicator or "SMA")
        normalized = normalized.replace("-", "_").replace(" ", "_").upper()
        alias_map = {
            "SIMPLE_MOVING_AVERAGE": "SMA",
            "EXPONENTIAL_MOVING_AVERAGE": "EMA",
            "RELATIVE_STRENGTH_INDEX": "RSI",
            "BOLLINGER_BANDS": "BOLLINGER",
            "BOLLINGER": "BOLLINGER",
            "AVERAGE_TRUE_RANGE": "ATR",
            "TRUE_RANGE": "ATR",
            "VOLUME_WEIGHTED_AVERAGE_PRICE": "VWAP",
            "VOLUME_WEIGHTED_MOVING_AVERAGE": "VWAP",
            "WEIGHTED_MOVING_AVERAGE": "WMA",
        }
        return alias_map.get(normalized, normalized)

    def _coerce_series_lines(
        self,
        alias: str,
        expression: Optional[str],
        *,
        column_hint: Optional[str] = None,
    ) -> List[str]:
        """Return lines that coerce arbitrary expressions into pandas Series."""

        preferred_column = column_hint or "close"
        fallback = expression or (f"df['{preferred_column}']" if preferred_column else "df['close']")
        return [
            f"{alias} = {fallback}",
            f"if isinstance({alias}, pd.DataFrame):",
            f"    if '{preferred_column}' in {alias}.columns:",
            f"        {alias} = {alias}['{preferred_column}']",
            f"    else:",
            f"        {alias} = {alias}.iloc[:, 0]",
            f"if not isinstance({alias}, pd.Series):",
            f"    {alias} = pd.Series({alias}, index=df.index)",
            f"{alias} = {alias}.astype(float).fillna(method='ffill').fillna(method='bfill')",
        ]

    def _coerce_float(self, raw: Any, default: Optional[float] = None) -> Optional[float]:
        """Best-effort conversion of user-provided numeric parameters."""

        if raw in (None, ""):
            return default
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    def _approximate_zscore(self, confidence: Optional[float]) -> float:
        """Return an approximate z-score for the requested confidence."""

        if confidence is None:
            return 1.65
        try:
            level = float(confidence)
        except (TypeError, ValueError):
            return 1.65

        lookup = [
            (99.9, 3.29),
            (99.5, 2.81),
            (99.0, 2.33),
            (97.5, 1.96),
            (95.0, 1.65),
            (90.0, 1.28),
        ]
        for threshold, score in lookup:
            if level >= threshold:
                return score
        return 1.28

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
        if context.target_mode == OutputMode.BACKTESTING:
            requirements.update(["requests"])
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
                "emitter": generated_code.get("emitter", "base"),
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
