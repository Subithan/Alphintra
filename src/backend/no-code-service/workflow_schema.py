"""Structured validation helpers for incoming workflow payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class NodeModel(BaseModel):
    """Pydantic model describing a workflow node."""

    id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    position: Dict[str, float] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("position", mode="before")
    def _ensure_position(cls, value: Dict[str, Any] | None) -> Dict[str, float]:
        value = value or {}
        return {
            "x": float(value.get("x", 0.0)),
            "y": float(value.get("y", 0.0)),
        }

    @field_validator("data", mode="before")
    def _ensure_data_block(cls, value: Dict[str, Any] | None) -> Dict[str, Any]:
        block = value or {}
        block.setdefault("parameters", {})
        block.setdefault("metadata", {})
        return block


class EdgeModel(BaseModel):
    """Pydantic model describing a workflow edge."""

    id: str | None = None
    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    sourceHandle: str | None = None
    targetHandle: str | None = None
    data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("data", mode="before")
    def _ensure_data(cls, value: Dict[str, Any] | None) -> Dict[str, Any]:
        block = value or {}
        block.setdefault("transformations", [])
        if not isinstance(block["transformations"], list):
            block["transformations"] = [block["transformations"]]
        block.setdefault("metadata", {})
        return block

    @model_validator(mode="after")
    def _mirror_handles_in_data(cls, values: "EdgeModel") -> "EdgeModel":
        data = values.data
        source_handle = values.sourceHandle or data.get("sourceHandle") or ""
        target_handle = values.targetHandle or data.get("targetHandle") or ""
        values.sourceHandle = source_handle
        values.targetHandle = target_handle
        data.setdefault("sourceHandle", source_handle)
        data.setdefault("targetHandle", target_handle)
        return values


class WorkflowPayloadModel(BaseModel):
    """Full workflow payload model."""

    nodes: List[NodeModel] = Field(..., min_items=1)
    edges: List[EdgeModel] = Field(default_factory=list)


@dataclass
class WorkflowSchemaResult:
    """Result of schema validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class WorkflowSchemaValidator:
    """Validate and normalise workflow structures."""

    def validate(
        self,
        nodes: List[Dict[str, Any]] | None,
        edges: List[Dict[str, Any]] | None,
    ) -> WorkflowSchemaResult:
        errors: List[str] = []
        warnings: List[str] = []

        try:
            payload = WorkflowPayloadModel(nodes=nodes or [], edges=edges or [])
        except ValidationError as exc:
            errors.extend(self._format_validation_errors(exc))
            return WorkflowSchemaResult(False, errors, warnings, [], [])

        normalized_nodes = [self._normalise_node(node) for node in payload.nodes]
        normalized_edges = [self._normalise_edge(edge) for edge in payload.edges]

        self._detect_duplicate_ids(normalized_nodes, normalized_edges, warnings)

        return WorkflowSchemaResult(
            True,
            errors,
            warnings,
            normalized_nodes,
            normalized_edges,
        )

    @staticmethod
    def _normalise_node(node: NodeModel) -> Dict[str, Any]:
        node_dict = node.model_dump()
        node_dict.setdefault("data", {}).setdefault("parameters", {})
        node_dict["data"].setdefault("metadata", {})
        node_dict.setdefault("position", {"x": 0.0, "y": 0.0})
        return node_dict

    @staticmethod
    def _normalise_edge(edge: EdgeModel) -> Dict[str, Any]:
        edge_dict = edge.model_dump()
        data = edge_dict.setdefault("data", {})
        data.setdefault("dataType", data.get("data_type", "unknown"))
        data.setdefault("rule", {})
        data.setdefault("transformations", [])
        if not isinstance(data["transformations"], list):
            data["transformations"] = [data["transformations"]]
        return edge_dict

    @staticmethod
    def _format_validation_errors(exc: ValidationError) -> List[str]:
        formatted: List[str] = []
        for error in exc.errors():
            loc = " -> ".join(str(part) for part in error.get("loc", []))
            msg = error.get("msg", "Invalid value")
            formatted.append(f"{loc}: {msg}")
        return formatted

    @staticmethod
    def _detect_duplicate_ids(
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        warnings: List[str],
    ) -> None:
        seen_nodes: Dict[str, int] = {}
        for node in nodes:
            node_id = node["id"]
            seen_nodes[node_id] = seen_nodes.get(node_id, 0) + 1
        duplicates = [node_id for node_id, count in seen_nodes.items() if count > 1]
        if duplicates:
            warnings.append(
                f"Duplicate node identifiers detected: {', '.join(sorted(duplicates))}"
            )

        seen_edges: Dict[str, int] = {}
        for edge in edges:
            edge_id = edge.get("id")
            if not edge_id:
                continue
            seen_edges[edge_id] = seen_edges.get(edge_id, 0) + 1
        edge_duplicates = [edge_id for edge_id, count in seen_edges.items() if count > 1]
        if edge_duplicates:
            warnings.append(
                f"Duplicate edge identifiers detected: {', '.join(sorted(edge_duplicates))}"
            )


__all__ = ["WorkflowSchemaValidator", "WorkflowSchemaResult"]
