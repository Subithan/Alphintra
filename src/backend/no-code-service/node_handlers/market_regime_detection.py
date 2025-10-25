"""Handler for market regime detection nodes."""

from __future__ import annotations

from typing import List

from ir import Node
from .base import EdgeReference, NodeHandler


class MarketRegimeDetectionHandler(NodeHandler):
    """Generate rolling market regime classification signals."""

    node_type = "marketRegimeDetection"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - base docs
        params = node.data.get("parameters", {})
        trend_window = int(params.get("trendWindow", params.get("lookback", 50)))
        volatility_window = int(params.get("volatilityWindow", max(10, trend_window // 2)))
        volatility_multiplier = float(params.get("volatilityMultiplier", 1.5))
        trend_bias = float(params.get("trendThreshold", 0.0))

        safe_id = self.sanitize_id(node.id)
        trend_col = f"regime_{safe_id}_trend"
        sideways_col = f"regime_{safe_id}_sideways"
        volatile_col = f"regime_{safe_id}_volatile"

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        data_edge = self.find_edge(inputs, "data-input")
        series_expr = self.resolve_series_expression(data_edge, "close")

        lines = [f"# Market regime detection for node {node.id}"]
        lines.extend(
            [
                f"price_{safe_id} = {series_expr}",
                f"returns_{safe_id} = price_{safe_id}.pct_change().fillna(0)",
                f"trend_ma_{safe_id} = price_{safe_id}.rolling(window={trend_window}, min_periods=1).mean()",
                f"trend_signal_{safe_id} = (price_{safe_id} > trend_ma_{safe_id} * (1 + {trend_bias})).fillna(False)",
                f"volatility_{safe_id} = returns_{safe_id}.rolling(window={volatility_window}, min_periods=1).std().fillna(0)",
                f"vol_threshold_{safe_id} = volatility_{safe_id}.rolling(window={volatility_window}, min_periods=1).median().fillna(method='bfill').fillna(volatility_{safe_id})",
                f"df['{trend_col}'] = trend_signal_{safe_id}.astype(bool)",
                f"df['{volatile_col}'] = (volatility_{safe_id} > vol_threshold_{safe_id} * {volatility_multiplier}).fillna(False).astype(bool)",
                f"df['{sideways_col}'] = (~df['{trend_col}'] & ~df['{volatile_col}']).astype(bool)",
            ]
        )

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas", "numpy"]

