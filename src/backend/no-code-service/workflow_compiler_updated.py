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
from collections import Counter
from copy import deepcopy
from typing import Any, Dict, List, Optional

from enhanced_code_generator import EnhancedCodeGenerator


class WorkflowCompiler:
    """Compile visual workflows into executable trading strategies."""

    def __init__(self) -> None:
        self.code_generator = EnhancedCodeGenerator()
        self.component_registry = self._initialize_component_registry()

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
                    "type": "dataset",
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

        validation_result = self._validate_workflow(nodes, edges)
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
            "nodes": nodes,
            "edges": edges,
            "config": {"name": strategy_name},
        }

        generator_result = self.code_generator.compile_workflow(workflow_payload)
        aggregated_requirements = self._aggregate_requirements(
            nodes, generator_result.get("requirements", [])
        )

        generator_errors = self._normalise_messages(generator_result.get("errors", []))
        generator_warnings = self._normalise_messages(generator_result.get("warnings", []))

        errors = validation_result["errors"] + generator_errors
        warnings = validation_result["warnings"] + generator_warnings
        metadata = generator_result.get("metadata", {})

        success = generator_result.get("success", False) and not errors

        return {
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

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _validate_workflow(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not nodes:
            errors.append("Workflow must contain at least one node")
            return {
                "is_valid": False,
                "errors": errors,
                "warnings": warnings,
                "summary": {
                    "total_nodes": 0,
                    "total_edges": len(edges),
                    "categories": {},
                    "node_types": [],
                },
            }

        node_map = {node["id"]: node for node in nodes}
        incoming_edges: Dict[str, List[Dict[str, Any]]] = {node["id"]: [] for node in nodes}
        outgoing_edges: Dict[str, List[Dict[str, Any]]] = {node["id"]: [] for node in nodes}

        for edge in edges:
            src = edge.get("source")
            dst = edge.get("target")
            if src in outgoing_edges:
                outgoing_edges[src].append(edge)
            if dst in incoming_edges:
                incoming_edges[dst].append(edge)

        categories = Counter()
        node_types_present = set()

        for node in nodes:
            node_type = node.get("type", "")
            node_types_present.add(node_type)
            component = self.component_registry.get(node_type)
            if not component:
                errors.append(f"Unsupported node type: {node_type}")
                continue
            categories[component["category"]] += 1

        if categories.get("data_source", 0) + categories.get("dataset", 0) == 0:
            errors.append("Workflow must include at least one data source or dataset")

        if categories.get("action", 0) == 0:
            warnings.append("Workflow should include at least one trading action")

        if categories.get("output", 0) == 0:
            warnings.append("Workflow should include at least one output node")

        if self._has_circular_dependency(nodes, edges):
            errors.append("Workflow contains circular dependencies")

        for edge in edges:
            source_id = edge.get("source")
            target_id = edge.get("target")
            edge_data = edge.get("data") or {}
            source_handle = edge_data.get("sourceHandle")
            target_handle = edge_data.get("targetHandle")

            source_node = node_map.get(source_id)
            target_node = node_map.get(target_id)

            if not source_node:
                errors.append(f"Edge references non-existent source node: {source_id}")
            if not target_node:
                errors.append(f"Edge references non-existent target node: {target_id}")

            if source_node:
                component = self.component_registry.get(source_node.get("type", ""))
                if component:
                    if source_handle:
                        if not self._handle_supported(component, source_handle, "outputs"):
                            errors.append(
                                f"Node '{source_node['id']}' (type {source_node['type']}) "
                                f"does not expose output handle '{source_handle}'"
                            )
                    else:
                        warnings.append(
                            f"Edge from node '{source_node['id']}' is missing a source handle"
                        )

            if target_node:
                component = self.component_registry.get(target_node.get("type", ""))
                if component:
                    if target_handle:
                        if not self._handle_supported(component, target_handle, "inputs"):
                            errors.append(
                                f"Node '{target_node['id']}' (type {target_node['type']}) "
                                f"does not accept input handle '{target_handle}'"
                            )
                    else:
                        warnings.append(
                            f"Edge to node '{target_node['id']}' is missing a target handle"
                        )

        for node in nodes:
            node_type = node.get("type", "")
            component = self.component_registry.get(node_type)
            if not component:
                continue
            if component["category"] in {"action", "output"} and not incoming_edges[node["id"]]:
                warnings.append(
                    f"Node '{node['id']}' of type '{node_type}' has no incoming connections"
                )
            if component["category"] == "data_source" and not outgoing_edges[node["id"]]:
                warnings.append(
                    f"Data source node '{node['id']}' is not connected to any downstream components"
                )

        summary = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "categories": dict(categories),
            "node_types": sorted(node_types_present),
        }

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "summary": summary,
        }

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
