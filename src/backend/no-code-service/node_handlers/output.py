"""Handler for output nodes."""

from typing import List

from ir import Node
from .base import EdgeReference, NodeHandler


class OutputHandler(NodeHandler):
    node_type = "output"

    def handle(self, node: Node, generator) -> str:
        label = node.data.get("label", "output")
        safe_id = self.sanitize_id(node.id)
        column_name = f"output_{safe_id}"
        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        primary = inputs[0] if inputs else None
        expr = self.expression_from_edge(primary)

        lines = [f"# Output aggregation for node {node.id} ({label})"]
        if expr:
            lines.append(f"df['{column_name}'] = {expr}")
        else:
            lines.append(f"df['{column_name}'] = pd.NA")

        if len(inputs) > 1:
            concat_series = ", ".join(
                filter(None, (self.expression_from_edge(edge) for edge in inputs))
            )
            if concat_series:
                lines.append(
                    f"df['{column_name}_composite'] = pd.concat([{concat_series}], axis=1).mean(axis=1)"
                )

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
