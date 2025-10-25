"""Handler for sentiment analysis nodes."""

from __future__ import annotations

from typing import List

from ir import Node
from .base import EdgeReference, NodeHandler


class SentimentAnalysisHandler(NodeHandler):
    """Derive simple sentiment scores and boolean sentiment flags."""

    node_type = "sentimentAnalysis"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - base docs
        params = node.data.get("parameters", {})
        smoothing = int(params.get("smoothing", params.get("window", 14)))
        threshold = float(params.get("threshold", 0.05))

        safe_id = self.sanitize_id(node.id)
        pos_col = f"sentiment_{safe_id}_positive"
        neu_col = f"sentiment_{safe_id}_neutral"
        neg_col = f"sentiment_{safe_id}_negative"

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        data_edge = self.find_edge(inputs, "data-input")
        source_expr = self.expression_from_edge(data_edge) or "df['close']"

        lines = [f"# Sentiment analysis for node {node.id}"]
        lines.extend(
            [
                f"raw_source_{safe_id} = {source_expr}",
                f"if isinstance(raw_source_{safe_id}, pd.DataFrame):",
                f"    numeric_cols_{safe_id} = raw_source_{safe_id}.select_dtypes(include=['number'])",
                f"    base_series_{safe_id} = numeric_cols_{safe_id}.mean(axis=1) if not numeric_cols_{safe_id}.empty else raw_source_{safe_id}.sum(axis=1)",
                f"else:",
                f"    base_series_{safe_id} = pd.Series(raw_source_{safe_id}, index=df.index) if not isinstance(raw_source_{safe_id}, pd.Series) else raw_source_{safe_id}",
                f"smoothed_{safe_id} = base_series_{safe_id}.rolling(window={smoothing}, min_periods=1).mean().fillna(0)",
                f"df['{pos_col}'] = (smoothed_{safe_id} > {threshold}).fillna(False).astype(bool)",
                f"df['{neg_col}'] = (smoothed_{safe_id} < -{threshold}).fillna(False).astype(bool)",
                f"df['{neu_col}'] = (~df['{pos_col}'] & ~df['{neg_col}']).astype(bool)",
            ]
        )

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]

