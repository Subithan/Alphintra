"""Handler for output nodes."""

from typing import Dict, Any

from .base import NodeHandler


class OutputHandler(NodeHandler):
    node_type = "output"

    def handle(self, node: Dict[str, Any], generator) -> str:
        label = node.get("data", {}).get("label", "output")
        inputs = generator.get_incoming(node["id"])
        src = inputs[0] if inputs else ""
        src_var = f"target_{self.sanitize_id(src)}" if src else ""  # assume last signal
        var_name = f"output_{self.sanitize_id(node['id'])}"
        return f"{var_name} = {src_var}  # {label}"
