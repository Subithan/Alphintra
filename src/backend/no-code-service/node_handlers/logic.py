"""Handler for logic gate nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class LogicHandler(NodeHandler):
    node_type = "logic"

    def handle(self, node: Node, generator) -> str:
        label = node.data.get("label", "logic")
        var_name = f"logic_{self.sanitize_id(node.id)}"
        return f"{var_name} = '{label}'  # placeholder for logic operation"

    def required_packages(self) -> List[str]:
        return []
