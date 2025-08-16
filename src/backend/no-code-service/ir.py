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
        edges = [
            Edge(source=e.get("source", ""), target=e.get("target", ""))
            for e in workflow.get("edges", [])
            if e.get("source") in nodes and e.get("target") in nodes
        ]
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
