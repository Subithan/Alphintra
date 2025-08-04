"""Handler for output nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class OutputHandler(NodeHandler):
    node_type = "output"

    def handle(self, node: Node, generator) -> str:
        label = node.data.get("label", "output")
        inputs = generator.get_incoming(node.id)
        src = inputs[0] if inputs else ""
        src_var = f"target_{self.sanitize_id(src)}" if src else ""  # assume last signal
        var_name = f"output_{self.sanitize_id(node.id)}"
        return f"{var_name} = {src_var}  # {label}"

    def required_packages(self) -> List[str]:
        return ["pandas"]
