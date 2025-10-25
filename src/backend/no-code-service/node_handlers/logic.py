"""Handler for logic gate nodes."""

from __future__ import annotations

from typing import List

from ir import Node
from .base import EdgeReference, NodeHandler


class LogicHandler(NodeHandler):
    node_type = "logic"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - see base class
        params = node.data.get("parameters", {})
        operation = str(params.get("operation", "AND")).upper()
        safe_id = self.sanitize_id(node.id)
        column_name = f"logic_{safe_id}"

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        signal_edges = [edge for edge in inputs if edge[2].startswith("input")]
        signal_exprs = [self.expression_from_edge(edge) for edge in signal_edges]
        signal_exprs = [expr for expr in signal_exprs if expr]

        lines = [f"# Logic ({operation}) for node {node.id}"]

        if not signal_exprs:
            lines.append(f"df['{column_name}'] = pd.Series(False, index=df.index)")
            lines.append(f"df['{column_name}'] = df['{column_name}'].astype(bool)")
            return "\n".join(lines)

        if operation == "AND":
            combined = " & ".join(f"({expr})" for expr in signal_exprs)
        elif operation == "OR":
            combined = " | ".join(f"({expr})" for expr in signal_exprs)
        elif operation == "XOR":
            xor_expr = signal_exprs[0]
            for expr in signal_exprs[1:]:
                xor_expr = f"({xor_expr}) ^ ({expr})"
            combined = xor_expr
        elif operation == "NOT":
            combined = f"~({signal_exprs[0]})"
        else:
            combined = " | ".join(f"({expr})" for expr in signal_exprs)

        lines.append(f"df['{column_name}'] = ({combined}).fillna(False)")
        lines.append(f"df['{column_name}'] = df['{column_name}'].astype(bool)")

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
