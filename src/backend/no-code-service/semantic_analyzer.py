"""Semantic analysis for workflow graphs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from collections import Counter, defaultdict


@dataclass
class SemanticAnalysisResult:
    """Semantic analysis output."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    type_map: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)


class SemanticAnalyzer:
    """Performs structural and type validation for workflows."""

    REQUIRED_PARAMETERS = {
        "dataSource": ["symbol", "timeframe"],
        "technicalIndicator": ["indicator", "period"],
        "condition": ["condition"],
        "action": ["action"],
        "risk": ["model"],
    }

    def __init__(self, component_registry: Dict[str, Dict[str, Any]]):
        self.component_registry = component_registry

    def analyze(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> SemanticAnalysisResult:
        errors: List[str] = []
        warnings: List[str] = []

        node_map = {node["id"]: node for node in nodes}
        type_map: Dict[str, Dict[str, Dict[str, str]]] = {}
        categories = Counter()
        node_types_present: Set[str] = set()

        for node in nodes:
            node_type = node.get("type", "")
            node_types_present.add(node_type)

            component = self.component_registry.get(node_type)
            if not component:
                errors.append(f"Unsupported node type: {node_type}")
                continue

            categories[component["category"]] += 1
            self._validate_node_parameters(node, errors, warnings)
            type_map[node["id"]] = {
                "inputs": self._resolve_handle_types(component.get("inputs", {})),
                "outputs": self._resolve_handle_types(component.get("outputs", {})),
            }

        if categories.get("data_source", 0) + categories.get("dataset", 0) == 0:
            errors.append("Workflow must include at least one data source or dataset node.")
        if categories.get("action", 0) == 0:
            warnings.append("Workflow should include at least one action node.")
        if categories.get("output", 0) == 0:
            warnings.append("Workflow should include at least one output node.")

        # Connection validation
        normalized_edges = [dict(edge) for edge in edges]
        incoming_edges: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        outgoing_edges: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for edge in normalized_edges:
            self._validate_edge(
                edge,
                node_map,
                type_map,
                errors,
                warnings,
            )
            if edge.get("source") in node_map:
                outgoing_edges[edge["source"]].append(edge)
            if edge.get("target") in node_map:
                incoming_edges[edge["target"]].append(edge)

        # Warn about disconnected nodes
        for node in nodes:
            node_id = node["id"]
            component = self.component_registry.get(node.get("type", ""))
            if not component:
                continue
            category = component["category"]
            if category in {"action", "output"} and not incoming_edges.get(node_id):
                warnings.append(f"Node '{node_id}' has no inbound connections.")
            if category in {"data_source", "dataset"} and not outgoing_edges.get(node_id):
                warnings.append(f"Node '{node_id}' is not connected downstream.")

        summary = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "categories": dict(categories),
            "node_types": sorted(node_types_present),
        }

        return SemanticAnalysisResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            summary=summary,
            type_map=type_map,
            nodes=nodes,
            edges=normalized_edges,
        )

    def _validate_node_parameters(
        self,
        node: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
    ) -> None:
        node_type = node.get("type", "")
        required = self.REQUIRED_PARAMETERS.get(node_type, [])
        params = (node.get("data") or {}).get("parameters") or {}
        for param in required:
            if param not in params:
                errors.append(f"Node '{node['id']}' missing required parameter '{param}'.")
        if not params:
            warnings.append(
                f"Node '{node['id']}' ({node_type}) has no parameters; defaults will be used."
            )

    def _resolve_handle_types(self, handles: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        resolved: Dict[str, str] = {}
        for handle_name, handle_data in handles.items():
            resolved[handle_name] = handle_data.get("type", "unknown")
        return resolved

    def _validate_edge(
        self,
        edge: Dict[str, Any],
        node_map: Dict[str, Dict[str, Any]],
        type_map: Dict[str, Dict[str, Dict[str, str]]],
        errors: List[str],
        warnings: List[str],
    ) -> None:
        source_id = edge.get("source")
        target_id = edge.get("target")
        source_node = node_map.get(source_id)
        target_node = node_map.get(target_id)

        if not source_node or not target_node:
            errors.append(
                f"Edge references unknown nodes: {source_id or '?'} -> {target_id or '?'}"
            )
            return

        component_source = self.component_registry.get(source_node["type"])
        component_target = self.component_registry.get(target_node["type"])
        if not component_source or not component_target:
            return

        source_handle = edge.get("sourceHandle") or self._single_handle(
            component_source.get("outputs", {})
        )
        target_handle = edge.get("targetHandle") or self._single_handle(
            component_target.get("inputs", {})
        )

        if not source_handle:
            warnings.append(f"Edge from '{source_id}' is missing a source handle.")
        if not target_handle:
            warnings.append(f"Edge to '{target_id}' is missing a target handle.")

        edge["sourceHandle"] = source_handle or ""
        edge["targetHandle"] = target_handle or ""
        data_block = edge.setdefault("data", {})
        data_block.setdefault("transformations", [])

        source_type = self._handle_type(
            component_source,
            source_handle,
            direction="outputs",
        )
        target_type = self._handle_type(
            component_target,
            target_handle,
            direction="inputs",
        )

        edge["data"]["dataType"] = source_type or target_type or "unknown"

        if source_type and target_type and source_type != target_type:
            errors.append(
                f"Type mismatch on edge {source_id}->{target_id}: "
                f"{source_type} cannot connect to {target_type}"
            )

        self._populate_type_map_entries(type_map, source_id, source_handle, source_type, "outputs")
        self._populate_type_map_entries(type_map, target_id, target_handle, target_type, "inputs")

    def _handle_type(
        self,
        component: Dict[str, Any],
        handle: Optional[str],
        *,
        direction: str,
    ) -> Optional[str]:
        if not handle:
            return None
        handles = component.get(direction, {})
        if handle in handles:
            return handles[handle].get("type")

        pattern_key = "input_patterns" if direction == "inputs" else "output_patterns"
        for pattern in component.get(pattern_key, []):
            if pattern.match(handle):
                template = handles.get(next(iter(handles), ""), {"type": "unknown"})
                return template.get("type", "unknown")
        return None

    @staticmethod
    def _single_handle(handles: Dict[str, Any]) -> str:
        if len(handles) == 1:
            return next(iter(handles))
        return ""

    @staticmethod
    def _populate_type_map_entries(
        type_map: Dict[str, Dict[str, Dict[str, str]]],
        node_id: str,
        handle: Optional[str],
        resolved_type: Optional[str],
        direction: str,
    ) -> None:
        if not handle:
            return
        node_entry = type_map.setdefault(node_id, {"inputs": {}, "outputs": {}})
        node_entry[direction][handle] = resolved_type or "unknown"


__all__ = ["SemanticAnalyzer", "SemanticAnalysisResult"]
