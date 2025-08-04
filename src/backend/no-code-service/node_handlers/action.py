"""Handler for action nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class ActionHandler(NodeHandler):
    node_type = "action"

    def handle(self, node: Node, generator) -> str:
        label = node.data.get("label", "action")
        col_name = f"action_{self.sanitize_id(node.id)}"
        return f"df['{col_name}'] = '{label}'  # placeholder for action execution"

    def required_packages(self) -> List[str]:
        return ["pandas"]
