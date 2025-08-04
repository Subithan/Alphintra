"""Handler for action nodes."""

from typing import Dict, Any

from .base import NodeHandler


class ActionHandler(NodeHandler):
    node_type = "action"

    def handle(self, node: Dict[str, Any], generator) -> str:
        label = node.get("data", {}).get("label", "action")
        return f"# Execute action: {label}"
