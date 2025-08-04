"""Handler for action nodes."""

from typing import Dict, Any

from .base import NodeHandler


class ActionHandler(NodeHandler):
    node_type = "action"

    def handle(self, node: Dict[str, Any], generator) -> str:
        label = node.get("data", {}).get("label", "action")
        var_name = f"action_{self.sanitize_id(node['id'])}"
        return f"{var_name} = '{label}'  # placeholder for action execution"
