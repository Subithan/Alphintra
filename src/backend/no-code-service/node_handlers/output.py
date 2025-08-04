"""Handler for output nodes."""

from typing import Dict, Any

from .base import NodeHandler


class OutputHandler(NodeHandler):
    node_type = "output"

    def handle(self, node: Dict[str, Any], generator) -> str:
        label = node.get("data", {}).get("label", "output")
        return f"# Output node: {label}"
