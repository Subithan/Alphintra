"""Workflow compiler entry point for the no-code console.

This module bridges the lighter-weight API entry points with the
``EnhancedCodeGenerator`` that powers the end-to-end strategy code
emission.  It keeps a lightweight registry of the node types that the
console produces so we can perform structural validation, map handles to
semantic meaning, and aggregate third-party package requirements before
handing execution off to the enhanced compiler.
"""

from __future__ import annotations

import re
import time
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from enhanced_code_generator import EnhancedCodeGenerator
from execution_planner import ExecutionPlanner
from semantic_analyzer import SemanticAnalyzer
from workflow_schema import WorkflowSchemaValidator
from app.telemetry import telemetry_recorder


class WorkflowCompiler:
    """Compile visual workflows into executable trading strategies."""

    def __init__(self) -> None:
        self.code_generator = EnhancedCodeGenerator()
        self.component_registry = self._initialize_component_registry()
        self.schema_validator = WorkflowSchemaValidator()
        self.semantic_analyzer = SemanticAnalyzer(self.component_registry)
        self.execution_planner = ExecutionPlanner()

    # ------------------------------------------------------------------
    # Registry initialisation
    # ------------------------------------------------------------------
    def _initialize_component_registry(self) -> Dict[str, Dict[str, Any]]:
        """Register node types exposed in the no-code console.

        Each registry entry describes the category of the node, the input
        and output handles it exposes, and a small template string that
        documents what each handle represents.  The template strings are
        descriptive only – real code generation is delegated to the
        :class:`EnhancedCodeGenerator` and the handler associated with the
        node type.
        """

        handler_lookup = getattr(self.code_generator, "handlers", {})
        fallback_handler = getattr(self.code_generator, "fallback_handler", None)

        registry: Dict[str, Dict[str, Any]] = {}

        def register(
            node_type: str,
            *,
            category: str,
            inputs: Optional[Dict[str, Dict[str, Any]]] = None,
            outputs: Optional[Dict[str, Dict[str, Any]]] = None,
            templates: Optional[Dict[str, str]] = None,
            input_patterns: Optional[List[str]] = None,
            output_patterns: Optional[List[str]] = None,
            handler_key: Optional[str] = None,
            alias_for: Optional[str] = None,
        ) -> None:
            handler = handler_lookup.get(handler_key or node_type, fallback_handler)
            entry = {
                "type": node_type,
                "category": category,
                "inputs": inputs or {},
                "outputs": outputs or {},
                "templates": templates or {},
                "input_patterns": [re.compile(p) for p in (input_patterns or [])],
                "output_patterns": [re.compile(p) for p in (output_patterns or [])],
                "handler": handler,
            }
            if alias_for:
                entry["alias_for"] = alias_for
            registry[node_type] = entry

        register(
            "dataSource",
            category="data_source",
            inputs={},
            outputs={
                "data-output": {
                    "type": "ohlcv",
                    "description": "Historical OHLCV price data",
                }
            },
            templates={
                "data-output": "load_market_data(symbol='{symbol}', timeframe='{timeframe}', bars={bars})",
            },
        )

        register(
            "customDataset",
            category="dataset",
            inputs={},
            outputs={
                "data-output": {
                    "type": "dataset",
                    "description": "Custom tabular dataset loaded from storage",
                }
            },
            templates={
                "data-output": "pd.read_csv('{fileName}')",
            },
        )

        indicator_outputs = {
            f"output-{idx}": {
                "type": "numeric",
                "description": f"Indicator derived series #{idx}",
            }
            for idx in range(1, 6)
        }
        register(
            "technicalIndicator",
            category="technical_indicator",
            inputs={
                "data-input": {
                    "type": "ohlcv",
                    "description": "Indicator source data frame",
                }
            },
            outputs=indicator_outputs,
            templates={
                "data-input": "indicator_source_dataframe",
                "output-1": "ta.{indicator}(data['{source}'], timeperiod={period})",
                "output-2": "indicator_secondary_output",
                "output-3": "indicator_tertiary_output",
                "output-4": "indicator_fourth_output",
                "output-5": "indicator_fifth_output",
            },
        )

        register(
            "condition",
            category="condition",
            inputs={
                "data-input": {
                    "type": "numeric",
                    "description": "Primary indicator series",
                },
                "value-input": {
                    "type": "numeric",
                    "description": "Comparison threshold or reference",
                },
                "aux-input": {
                    "type": "numeric",
                    "description": "Optional context series",
                },
            },
            outputs={
                "signal-output": {
                    "type": "signal",
                    "description": "Boolean trading signal",
                }
            },
            templates={
                "signal-output": "build_condition(signal=indicator, operator='{condition}', value={value})",
            },
        )

        register(
            "logic",
            category="logic",
            inputs={
                "input-pattern": {
                    "type": "signal",
                    "description": "Dynamic logic input handle pattern (input-0, input-1, ...)",
                }
            },
            outputs={
                "output": {
                    "type": "signal",
                    "description": "Combined logical signal",
                }
            },
            templates={
                "output": "combine_signals(operation='{operation}', inputs=list_of_signals)",
            },
            input_patterns=[r"^input-\d+$"],
        )

        register(
            "action",
            category="action",
            inputs={
                "signal-input": {
                    "type": "signal",
                    "description": "Trigger signal for the action",
                }
            },
            outputs={},
            templates={
                "signal-input": "execute_action_when(signal, action='{action}', quantity={quantity})",
            },
        )

        risk_inputs = {
            "data-input": {
                "type": "ohlcv",
                "description": "Market data for risk controls",
            },
            "signal-input": {
                "type": "signal",
                "description": "Signal stream to gate with risk",
            },
        }
        risk_outputs = {
            "risk-output": {
                "type": "risk_signal",
                "description": "Risk-filtered signal",
            }
        }
        risk_templates = {
            "risk-output": "apply_risk_management(signal, data, policy='{riskType}')",
        }
        register(
            "risk",
            category="risk",
            inputs=deepcopy(risk_inputs),
            outputs=deepcopy(risk_outputs),
            templates=deepcopy(risk_templates),
        )
        register(
            "riskManagement",
            category="risk",
            inputs=deepcopy(risk_inputs),
            outputs=deepcopy(risk_outputs),
            templates=deepcopy(risk_templates),
            handler_key="risk",
            alias_for="risk",
        )

        register(
            "output",
            category="output",
            inputs={
                "data-input": {
                    "type": "dataset",
                    "description": "Data frame to summarise",
                },
                "signal-input": {
                    "type": "signal",
                    "description": "Signal stream to expose",
                },
            },
            outputs={},
            templates={
                "data-input": "render_output_dataframe(data)",
                "signal-input": "render_output_signal(signal)",
            },
        )

        register(
            "marketRegimeDetection",
            category="analysis",
            inputs={
                "data-input": {
                    "type": "ohlcv",
                    "description": "Price series used for regime classification",
                }
            },
            outputs={
                "trend-output": {
                    "type": "signal",
                    "description": "Boolean flag indicating a trending market",
                },
                "sideways-output": {
                    "type": "signal",
                    "description": "Boolean flag indicating a range-bound market",
                },
                "volatile-output": {
                    "type": "signal",
                    "description": "Boolean flag indicating a high-volatility market",
                },
            },
            templates={
                "trend-output": "trend regime detection output",
                "sideways-output": "sideways regime detection output",
                "volatile-output": "volatile regime detection output",
            },
        )

        register(
            "multiTimeframeAnalysis",
            category="analysis",
            inputs={
                "data-input": {
                    "type": "ohlcv",
                    "description": "Base timeframe OHLCV data",
                }
            },
            outputs={
                "output": {
                    "type": "ohlcv",
                    "description": "Aggregated OHLCV features across requested timeframes",
                }
            },
            templates={
                "output": "multi-timeframe aggregation output",
            },
        )

        register(
            "correlationAnalysis",
            category="analysis",
            inputs={
                "data-input-1": {
                    "type": "ohlcv",
                    "description": "Primary asset OHLCV data",
                },
                "data-input-2": {
                    "type": "ohlcv",
                    "description": "Secondary asset OHLCV data",
                },
            },
            outputs={
                "output": {
                    "type": "numeric",
                    "description": "Rolling correlation between the two inputs",
                }
            },
            templates={
                "output": "correlation analysis output",
            },
        )

        register(
            "sentimentAnalysis",
            category="analysis",
            inputs={
                "data-input": {
                    "type": "ohlcv",
                    "description": "Structured sentiment feed or derived features",
                }
            },
            outputs={
                "positive-output": {
                    "type": "signal",
                    "description": "Positive sentiment trigger",
                },
                "neutral-output": {
                    "type": "signal",
                    "description": "Neutral sentiment trigger",
                },
                "negative-output": {
                    "type": "signal",
                    "description": "Negative sentiment trigger",
                },
            },
            templates={
                "positive-output": "positive sentiment output",
                "neutral-output": "neutral sentiment output",
                "negative-output": "negative sentiment output",
            },
        )

        return registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def compile_workflow(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        strategy_name: str = "Generated Strategy",
    ) -> Dict[str, Any]:
        """Compile a workflow into executable Python code."""

        timings: Dict[str, float] = {}
        start = time.perf_counter()
        validation_result, normalized_nodes, normalized_edges = self._validate_workflow(nodes, edges)
        timings["validation"] = time.perf_counter() - start
        if not validation_result["is_valid"]:
            return {
                "success": False,
                "code": "",
                "requirements": [],
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"],
                "validation": validation_result,
            }

        workflow_payload = {
            "nodes": normalized_nodes,
            "edges": normalized_edges,
            "config": {"name": strategy_name},
        }

        start = time.perf_counter()
        generator_result = self.code_generator.compile_workflow(workflow_payload)
        timings["code_generation"] = time.perf_counter() - start
        aggregated_requirements = self._aggregate_requirements(
            nodes, generator_result.get("requirements", [])
        )

        generator_errors = self._normalise_messages(generator_result.get("errors", []))
        generator_warnings = self._normalise_messages(generator_result.get("warnings", []))

        errors = validation_result["errors"] + generator_errors
        warnings = validation_result["warnings"] + generator_warnings
        metadata = generator_result.get("metadata", {})

        success = generator_result.get("success", False) and not errors

        result = {
            "success": success,
            "code": generator_result.get("code", ""),
            "code_type": generator_result.get("code_type", "unknown"),
            "requirements": aggregated_requirements,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata,
            "nodes_processed": metadata.get("nodes_processed", len(nodes)),
            "edges_processed": metadata.get("edges_processed", len(edges)),
            "optimizations_applied": metadata.get("optimizations_applied", 0),
            "validation": validation_result,
        }
        result["metadata"]["timings"] = timings

        telemetry_recorder.record_compilation(
            {
                "strategy_name": strategy_name,
                "success": success,
                "node_count": len(normalized_nodes),
                "edge_count": len(normalized_edges),
                "timings": timings,
                "emitter": generator_result.get("emitter"),
            }
        )
        return result

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _validate_workflow(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        schema_result = self.schema_validator.validate(nodes, edges)
        normalized_nodes = schema_result.nodes
        normalized_edges = schema_result.edges

        if not schema_result.is_valid:
            summary = {
                "total_nodes": len(normalized_nodes),
                "total_edges": len(normalized_edges),
                "categories": {},
                "node_types": [],
            }
            validation = {
                "is_valid": False,
                "errors": schema_result.errors,
                "warnings": schema_result.warnings,
                "summary": summary,
                "type_map": {},
                "execution_plan": {
                    "ordered_nodes": [],
                    "stages": [],
                    "critical_path_length": 0,
                },
            }
            return validation, normalized_nodes, normalized_edges

        semantic_result = self.semantic_analyzer.analyze(normalized_nodes, normalized_edges)
        plan_result = self.execution_planner.plan(semantic_result.nodes, semantic_result.edges)

        errors = schema_result.errors + semantic_result.errors + plan_result.errors
        warnings = schema_result.warnings + semantic_result.warnings + plan_result.warnings

        summary = dict(semantic_result.summary)
        summary["execution_stages"] = len(plan_result.stages)
        summary["critical_path"] = plan_result.critical_path_length

        validation = {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "summary": summary,
            "type_map": semantic_result.type_map,
            "execution_plan": {
                "ordered_nodes": plan_result.ordered_nodes,
                "stages": [
                    {
                        "index": stage.index,
                        "nodes": stage.nodes,
                        "parallelizable": stage.parallelizable,
                    }
                    for stage in plan_result.stages
                ],
                "critical_path_length": plan_result.critical_path_length,
            },
        }

        return validation, semantic_result.nodes, semantic_result.edges

    def _handle_supported(
        self, component: Dict[str, Any], handle_name: str, direction: str
    ) -> bool:
        """Check if a handle exists on a component definition."""

        handles = component.get(direction, {})
        if handle_name in handles:
            return True

        pattern_key = "input_patterns" if direction == "inputs" else "output_patterns"
        for pattern in component.get(pattern_key, []):
            if pattern.match(handle_name):
                return True
        return False

    # ------------------------------------------------------------------
    # Requirement aggregation
    # ------------------------------------------------------------------
    def _aggregate_requirements(
        self, nodes: List[Dict[str, Any]], base_requirements: List[str]
    ) -> List[str]:
        packages = set(base_requirements or [])
        for node in nodes:
            node_type = node.get("type", "")
            component = self.component_registry.get(node_type)
            handler = component.get("handler") if component else None
            if handler and hasattr(handler, "required_packages"):
                try:
                    packages.update(handler.required_packages())
                except Exception:
                    # Handlers are lightweight; if something goes wrong we simply skip.
                    continue
        return sorted(packages)

    def _normalise_messages(self, messages: Optional[List[Any]]) -> List[str]:
        normalised: List[str] = []
        if not messages:
            return normalised

        for message in messages:
            if isinstance(message, str):
                normalised.append(message)
            elif isinstance(message, dict):
                node_id = message.get("node_id")
                text = message.get("message", "")
                if node_id:
                    normalised.append(f"[{node_id}] {text}")
                else:
                    normalised.append(text)
            else:
                normalised.append(str(message))
        return normalised

    # ------------------------------------------------------------------
    # Graph utilities
    # ------------------------------------------------------------------
    def _topological_sort(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        graph = {node["id"]: [] for node in nodes}
        in_degree = {node["id"]: 0 for node in nodes}

        for edge in edges:
            src = edge.get("source")
            dst = edge.get("target")
            if src in graph and dst in in_degree:
                graph[src].append(dst)
                in_degree[dst] += 1

        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        sorted_ids: List[str] = []

        while queue:
            current = queue.pop(0)
            sorted_ids.append(current)
            for neighbour in graph[current]:
                in_degree[neighbour] -= 1
                if in_degree[neighbour] == 0:
                    queue.append(neighbour)

        node_lookup = {node["id"]: node for node in nodes}
        return [node_lookup[node_id] for node_id in sorted_ids if node_id in node_lookup]

    def _has_circular_dependency(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> bool:
        sorted_nodes = self._topological_sort(nodes, edges)
        return len(sorted_nodes) != len(nodes)


__all__ = ["WorkflowCompiler"]
