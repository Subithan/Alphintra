"""Handler for correlation analysis nodes."""

from __future__ import annotations

from typing import List

from ir import Node
from .base import EdgeReference, NodeHandler


class CorrelationAnalysisHandler(NodeHandler):
    """Compute rolling correlations between two inputs."""

    node_type = "correlationAnalysis"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - base docs
        params = node.data.get("parameters", {})
        window = int(params.get("window", params.get("lookback", 30)))

        safe_id = self.sanitize_id(node.id)
        corr_col = f"correlation_{safe_id}"

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        left_edge = self.find_edge(inputs, "data-input-1")
        right_edge = self.find_edge(inputs, "data-input-2")

        left_expr = self.resolve_series_expression(left_edge, "close")
        right_expr = self.resolve_series_expression(right_edge, "close")

        lines = [f"# Correlation analysis for node {node.id}"]
        lines.extend(
            [
                f"left_series_{safe_id} = {left_expr}",
                f"right_series_{safe_id} = {right_expr}",
                f"returns_left_{safe_id} = left_series_{safe_id}.pct_change().fillna(0)",
                f"returns_right_{safe_id} = right_series_{safe_id}.pct_change().fillna(0)",
                f"rolling_corr_{safe_id} = returns_left_{safe_id}.rolling(window={window}, min_periods=1).corr(returns_right_{safe_id})",
                f"df['{corr_col}'] = rolling_corr_{safe_id}.fillna(0)",
            ]
        )

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]

