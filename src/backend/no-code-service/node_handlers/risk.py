"""Handler for risk management nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class RiskHandler(NodeHandler):
    node_type = "risk"

    def handle(self, node: Node, generator) -> str:
        label = node.data.get("label", "risk")
        var_name = f"risk_{self.sanitize_id(node.id)}"
        return f"{var_name} = '{label}'  # placeholder for risk management"

    def required_packages(self) -> List[str]:
        return []
