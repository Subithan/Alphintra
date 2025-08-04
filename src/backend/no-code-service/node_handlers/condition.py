"""Handler for condition nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class ConditionHandler(NodeHandler):
    node_type = "condition"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        operator = params.get("operator", ">")
        threshold = params.get("threshold", 0)

        inputs = generator.get_incoming(node.id)
        features: list[str] = [src for src in inputs]

        target_col = f"target_{self.sanitize_id(node.id)}"

        if features:
            feat = f"feature_{self.sanitize_id(features[0])}"
            expr = f"df['{feat}'] {operator} {threshold}"
        else:
            expr = "False"

        return f"df['{target_col}'] = ({expr}).astype(int)"

    def required_packages(self) -> List[str]:
        return ["pandas"]
