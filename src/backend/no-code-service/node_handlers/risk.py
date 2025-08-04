"""Handler for risk management nodes."""

from typing import Dict, Any

from .base import NodeHandler


class RiskHandler(NodeHandler):
    node_type = "risk"

    def handle(self, node: Dict[str, Any], generator) -> str:
        label = node.get("data", {}).get("label", "risk")
        return f"# Apply risk management: {label}"
