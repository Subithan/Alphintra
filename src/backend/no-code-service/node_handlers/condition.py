"""Handler for condition nodes."""

from __future__ import annotations

from typing import List

from ir import Node
from .base import EdgeReference, NodeHandler


class ConditionHandler(NodeHandler):
    node_type = "condition"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - see base class
        params = node.data.get("parameters", {})
        operation = str(
            params.get("condition", params.get("operator", "greater_than"))
        ).lower()
        default_value = params.get("value", params.get("threshold", 0))

        safe_id = self.sanitize_id(node.id)
        column_name = f"signal_{safe_id}"
        temp_var = f"condition_{safe_id}"

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        data_edge = self.find_edge(inputs, "data-input")
        value_edge = self.find_edge(inputs, "value-input")

        left_expr = self.resolve_series_expression(data_edge, params.get("leftSource", "close"))
        if value_edge:
            right_expr = self.resolve_series_expression(value_edge, params.get("rightSource", "close"))
        else:
            right_expr = repr(default_value)

        if operation in {"greater_than", "gt", ">"}:
            comparison = f"({left_expr}) > ({right_expr})"
        elif operation in {"greater_than_equal", "greater_or_equal", ">="}:
            comparison = f"({left_expr}) >= ({right_expr})"
        elif operation in {"less_than", "lt", "<"}:
            comparison = f"({left_expr}) < ({right_expr})"
        elif operation in {"less_than_equal", "less_or_equal", "<="}:
            comparison = f"({left_expr}) <= ({right_expr})"
        elif operation in {"equal_to", "=="}:
            comparison = f"({left_expr}) == ({right_expr})"
        elif operation in {"not_equal", "!="}:
            comparison = f"({left_expr}) != ({right_expr})"
        elif operation in {"crosses_above", "cross_above", "cross_over"}:
            comparison = (
                f"(({left_expr}) > ({right_expr})) & (({left_expr}).shift(1) <= ({right_expr}).shift(1))"
            )
        elif operation in {"crosses_below", "cross_below"}:
            comparison = (
                f"(({left_expr}) < ({right_expr})) & (({left_expr}).shift(1) >= ({right_expr}).shift(1))"
            )
        else:
            comparison = f"({left_expr}) > ({right_expr})"

        lines = [f"# Condition ({operation}) for node {node.id}"]
        lines.append(f"{temp_var} = ({comparison}).fillna(False)")
        lines.append(f"df['{column_name}'] = {temp_var}.astype(bool)")

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
