from __future__ import annotations

"""Simplified code generation core.

This module exposes a :class:`Generator` that turns a workflow
representation into a block of Python code.  The generator itself does not
know how to deal with individual node types; instead it delegates the
responsibility to specialised :class:`NodeHandler` implementations that live
inside the ``node_handlers`` package.

The design allows new node types to be supported by simply dropping a new
handler class into the registry.
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple

# ``code_generator`` sits alongside the ``node_handlers`` package.  Import the
# registry and base class directly so this module can be used as a standalone
# script or as part of the package.
from node_handlers import HANDLER_REGISTRY, NodeHandler


class Generator:
    """Core workflow code generator.

    The generator iterates through workflow nodes and dispatches them to
    registered :class:`NodeHandler` instances.  Each handler returns a string
    containing the Python code snippet for its node.  The snippets are then
    concatenated into the final strategy code block.
    """

    def __init__(self) -> None:
        # Handlers are stored in a simple dictionary registry.
        self.handlers: Dict[str, NodeHandler] = dict(HANDLER_REGISTRY)
        # Store workflow structure so handlers can resolve connections between
        # nodes when emitting code.
        self.nodes: List[Dict[str, Any]] = []
        self.node_map: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Registry management
    # ------------------------------------------------------------------
    def register_handler(self, handler: NodeHandler) -> None:
        """Register a new handler at runtime."""

        self.handlers[handler.node_type] = handler

    def get_handler(self, node_type: str) -> NodeHandler | None:
        """Return handler for ``node_type`` if it exists."""

        return self.handlers.get(node_type)

    # ------------------------------------------------------------------
    # Graph helpers
    # ------------------------------------------------------------------
    def get_incoming(self, node_id: str) -> List[str]:
        """Return IDs of nodes with edges leading to ``node_id``."""

        return [e.get("source") for e in self.edges if e.get("target") == node_id]

    # ------------------------------------------------------------------
    # Parsing & Validation helpers
    # ------------------------------------------------------------------
    def parse_workflow(self, workflow: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, List[str]], Dict[str, int]]:
        """Read workflow definition and build adjacency lists.

        Returns the nodes, edges, adjacency list mapping node IDs to their
        outbound neighbours and a dictionary containing the in-degree for each
        node.  Edges referencing unknown nodes are ignored during parsing and
        will be reported during validation.
        """

        nodes = workflow.get("nodes", []) or []
        edges = workflow.get("edges", []) or []

        graph: Dict[str, List[str]] = {node.get("id"): [] for node in nodes}
        in_degree: Dict[str, int] = {node.get("id"): 0 for node in nodes}

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source in graph and target in graph:
                graph[source].append(target)
                in_degree[target] += 1

        return nodes, edges, graph, in_degree

    def validate_workflow(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        graph: Dict[str, List[str]],
        in_degree: Dict[str, int],
    ) -> Dict[str, List[str]]:
        """Validate basic workflow structure.

        Checks for required node types, disconnected nodes and cycles.  Returns
        a dictionary containing ``errors`` and ``warnings`` lists which can be
        surfaced to calling services.
        """

        errors: List[str] = []
        warnings: List[str] = []

        # Required node types -------------------------------------------------
        if not any(node.get("type") == "dataSource" for node in nodes):
            errors.append("Workflow must include at least one data source node")

        if not any(node.get("type") == "action" for node in nodes):
            warnings.append("Workflow should include at least one action node")

        # Disconnected nodes --------------------------------------------------
        connected: set[str] = set()
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in graph and tgt in graph:
                connected.add(src)
                connected.add(tgt)

        disconnected = [node["id"] for node in nodes if node["id"] not in connected]
        if disconnected and len(nodes) > 1:
            warnings.append(
                "Disconnected nodes: " + ", ".join(disconnected)
            )

        # Cycle detection using Kahn's algorithm -----------------------------
        local_in_degree = dict(in_degree)
        queue = [nid for nid, deg in local_in_degree.items() if deg == 0]
        visited = 0

        while queue:
            current = queue.pop(0)
            visited += 1
            for neighbour in graph.get(current, []):
                local_in_degree[neighbour] -= 1
                if local_in_degree[neighbour] == 0:
                    queue.append(neighbour)

        if visited != len(nodes):
            errors.append("Workflow contains cycles")

        return {"errors": errors, "warnings": warnings}

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def generate_strategy_code(self, workflow: Dict[str, Any], name: str = "GeneratedStrategy") -> Dict[str, Any]:
        """Generate Python code for a given workflow after validation."""

        nodes, edges, graph, in_degree = self.parse_workflow(workflow)
        # Persist structure for handlers requiring edge information
        self.nodes = nodes
        self.node_map = {n.get("id"): n for n in nodes}
        self.edges = edges

        validation = self.validate_workflow(nodes, edges, graph, in_degree)
        if validation["errors"]:
            return {
                "code": "",
                "requirements": [],
                "metadata": {
                    "name": name,
                    "generatedAt": datetime.utcnow().isoformat(),
                },
                "success": False,
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            }

        code_lines: List[str] = []
        for node in nodes:
            handler = self.get_handler(node.get("type", ""))
            if handler:
                snippet = handler.handle(node, self)
                if snippet:
                    code_lines.append(snippet)
        code = "\n".join(code_lines)

        return {
            "code": code,
            "requirements": [],
            "metadata": {
                "name": name,
                "generatedAt": datetime.utcnow().isoformat(),
            },
            "success": True,
            "warnings": validation["warnings"],
        }


# Backwards compatibility -------------------------------------------------
# ``main.py`` historically imported ``CodeGenerator``.  Keep the same name so
# existing code continues to function.
CodeGenerator = Generator


__all__ = ["Generator", "CodeGenerator"]
