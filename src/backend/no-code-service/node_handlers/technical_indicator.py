"""Handler for technical indicator nodes."""

from __future__ import annotations

from typing import List

from ir import Node
from .base import EdgeReference, NodeHandler


class TechnicalIndicatorHandler(NodeHandler):
    node_type = "technicalIndicator"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - see base class
        params = node.data.get("parameters", {})
        indicator = str(params.get("indicator", "SMA")).upper()
        period = int(params.get("period", params.get("timeperiod", 14)))
        source_col = params.get("source", "close")

        safe_id = self.sanitize_id(node.id)
        target_column = f"indicator_{safe_id}"

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        data_edge = self.find_edge(inputs, "data-input")
        series_expr = self.resolve_series_expression(data_edge, source_col)

        lines = [f"# Technical indicator: {indicator} ({node.id})"]

        if indicator == "SMA":
            lines.append(
                f"df['{target_column}'] = {series_expr}.rolling(window={period}, min_periods=1).mean()"
            )
        elif indicator == "EMA":
            lines.append(
                f"df['{target_column}'] = {series_expr}.ewm(span={period}, adjust=False).mean()"
            )
        elif indicator == "RSI":
            delta_var = f"delta_{safe_id}"
            gain_var = f"gain_{safe_id}"
            loss_var = f"loss_{safe_id}"
            rs_var = f"rs_{safe_id}"
            lines.extend([
                f"{delta_var} = {series_expr}.diff()",
                f"{gain_var} = {delta_var}.clip(lower=0).rolling(window={period}, min_periods={period}).mean()",
                f"{loss_var} = (-{delta_var}.clip(upper=0)).rolling(window={period}, min_periods={period}).mean()",
                f"{rs_var} = {gain_var} / {loss_var}.replace(0, pd.NA)",
                f"df['{target_column}'] = 100 - (100 / (1 + {rs_var}))",
                f"df['{target_column}'] = df['{target_column}'].fillna(method='bfill').fillna(50)",
            ])
        else:
            lines.extend([
                f"# Fallback: copy source series for unsupported indicator {indicator}",
                f"df['{target_column}'] = {series_expr}",
            ])

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
