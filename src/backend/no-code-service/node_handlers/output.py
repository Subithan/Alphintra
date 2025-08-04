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
        src_col = f"target_{self.sanitize_id(src)}" if src else ""
        col_name = f"output_{self.sanitize_id(node.id)}"
        if src_col:
            return f"df['{col_name}'] = df['{src_col}']  # {label}"
        return f"df['{col_name}'] = None  # {label}"

    def required_packages(self) -> List[str]:
        return ["pandas"]
