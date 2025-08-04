"""Handler for logic gate nodes."""

from typing import Dict, Any

from .base import NodeHandler


class LogicHandler(NodeHandler):
    node_type = "logic"

    def handle(self, node: Dict[str, Any], generator) -> str:
        label = node.get("data", {}).get("label", "logic")
        return f"# Logic operation: {label}"
