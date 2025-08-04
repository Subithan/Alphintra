"""Handler for condition nodes."""

from typing import Dict, Any

from .base import NodeHandler


class ConditionHandler(NodeHandler):
    node_type = "condition"

    def handle(self, node: Dict[str, Any], generator) -> str:
        label = node.get("data", {}).get("label", "condition")
        return f"# Evaluate condition: {label}"
