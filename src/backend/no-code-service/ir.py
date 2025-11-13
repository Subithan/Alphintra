from __future__ import annotations

"""Internal workflow representation used by the code generator.

The IR abstracts away the incoming JSON structure and provides a minimal graph
model consisting of nodes and edges.  This allows the generator and node
handlers to operate on a stable Python API independent from the exact shape of
user supplied JSON.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class Node:
    """Represents a workflow node."""

    id: str
    type: str
    data: Dict[str, Any]


@dataclass
class Edge:
    """Represents a directed connection between two nodes."""

    source: str
    target: str
    source_handle: str = ""
    target_handle: str = ""
    data_type: str = "unknown"
    transformations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    """Graph of nodes and edges."""

    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    @classmethod
    def from_json(cls, workflow: Dict[str, Any]) -> "Workflow":
        """Build :class:`Workflow` from a JSON dictionary."""

        nodes = {
            n.get("id"): Node(id=n.get("id", ""), type=n.get("type", ""), data=n.get("data", {}))
            for n in workflow.get("nodes", [])
            if n.get("id")
        }
        edges: List[Edge] = []
        for edge in workflow.get("edges", []):
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source not in nodes or target not in nodes:
                continue

            data_block = edge.get("data") or {}
            source_handle = (
                edge.get("sourceHandle")
                or data_block.get("sourceHandle")
                or data_block.get("source_handle")
                or ""
            )
            target_handle = (
                edge.get("targetHandle")
                or data_block.get("targetHandle")
                or data_block.get("target_handle")
                or ""
            )
            data_type = (
                data_block.get("dataType")
                or data_block.get("data_type")
                or edge.get("dataType")
                or "unknown"
            )
            transformations = data_block.get("transformations") or []
            if not isinstance(transformations, list):
                transformations = [transformations]

            edges.append(
                Edge(
                    source=source,
                    target=target,
                    source_handle=source_handle,
                    target_handle=target_handle,
                    data_type=data_type,
                    transformations=transformations,
                    metadata=data_block,
                )
            )
        return cls(nodes=nodes, edges=edges)

    # ------------------------------------------------------------------
    # Graph helpers
    # ------------------------------------------------------------------
    def adjacency(self) -> Dict[str, List[str]]:
        """Return adjacency list mapping node IDs to outbound neighbours."""

        graph: Dict[str, List[str]] = {nid: [] for nid in self.nodes}
        for edge in self.edges:
            graph[edge.source].append(edge.target)
        return graph

    def in_degree(self) -> Dict[str, int]:
        """Return in-degree count for each node."""

        indegree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        for edge in self.edges:
            indegree[edge.target] += 1
        return indegree
