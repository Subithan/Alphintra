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
        confirmation_bars = int(params.get("confirmationBars", 1))
        cooldown_bars = int(params.get("cooldownBars", 0))
        hold_bars = int(params.get("holdBars", 0))
        invert = bool(params.get("invertCondition", False))

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
        elif operation in {"between", "range"}:
            lower = params.get("minValue", params.get("lowerBound", default_value))
            upper = params.get("maxValue", params.get("upperBound", default_value))
            comparison = f"({left_expr} >= {lower}) & ({left_expr} <= {upper})"
        elif operation in {"percent_change", "pct_change"}:
            lookback = int(params.get("lookback", 1))
            pct_threshold = float(params.get("value", 0)) / 100
            comparison = f"({left_expr}.pct_change(periods={lookback}).fillna(0)) > {pct_threshold}"
        elif operation in {"slope_positive", "slope"}:
            window = int(params.get("window", 5))
            comparison = f"({left_expr}.diff({window}).fillna(0)) > 0"
        elif operation in {"rolling_max_breakout", "breakout"}:
            window = int(params.get("window", 20))
            comparison = f"({left_expr} >= ({left_expr}.rolling(window={window}, min_periods=1).max()))"
        elif operation in {"rolling_min_breakdown", "breakdown"}:
            window = int(params.get("window", 20))
            comparison = f"({left_expr} <= ({left_expr}.rolling(window={window}, min_periods=1).min()))"
        elif operation in {"ratio_above"}:
            ratio = params.get("ratioValue", 1)
            comparison = f"(({left_expr}) / ({right_expr}).replace(0, pd.NA)) > {ratio}"
        else:
            comparison = f"({left_expr}) > ({right_expr})"

        lines = [f"# Condition ({operation}) for node {node.id}"]
        lines.append(f"{temp_var} = ({comparison}).fillna(False)")

        if confirmation_bars > 1:
            lines.append(
                f"{temp_var} = {temp_var}.rolling(window={confirmation_bars}, min_periods={confirmation_bars}).apply(lambda x: x.all(), raw=False).fillna(False).astype(bool)"
            )

        if hold_bars > 1:
            lines.append(
                f"{temp_var} = {temp_var}.rolling(window={hold_bars}, min_periods=1).max().astype(bool)"
            )

        if cooldown_bars > 0:
            lines.append(
                f"cooldown_{safe_id} = {temp_var}.shift(1).rolling(window={cooldown_bars}, min_periods=1).any().fillna(False)"
            )
            lines.append(f"{temp_var} = {temp_var} & ~cooldown_{safe_id}")

        if invert:
            lines.append(f"{temp_var} = ~{temp_var}")

        lines.append(f"df['{column_name}'] = {temp_var}.astype(bool)")

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
