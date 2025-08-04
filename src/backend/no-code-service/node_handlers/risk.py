"""Handler for risk management nodes."""

from typing import Dict, Any

from .base import NodeHandler


class RiskHandler(NodeHandler):
    node_type = "risk"

    def handle(self, node: Dict[str, Any], generator) -> str:
        label = node.get("data", {}).get("label", "risk")
        var_name = f"risk_{self.sanitize_id(node['id'])}"
        return f"{var_name} = '{label}'  # placeholder for risk management"
