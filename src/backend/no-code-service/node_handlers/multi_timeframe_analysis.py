"""Handler for multi-timeframe analysis nodes."""

from __future__ import annotations

from typing import Iterable, List

from ir import Node
from .base import EdgeReference, NodeHandler


class MultiTimeframeAnalysisHandler(NodeHandler):
    """Create aggregated OHLCV features across multiple timeframes."""

    node_type = "multiTimeframeAnalysis"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - base docs
        params = node.data.get("parameters", {})
        requested: Iterable[str] = params.get("timeframes") or params.get("higherTimeframes") or ["4H", "1D"]
        if isinstance(requested, str):
            requested = [segment.strip() for segment in requested.split(",") if segment.strip()]
        timeframes = list(requested) or ["4H"]

        safe_id = self.sanitize_id(node.id)
        prefix = f"mtf_{safe_id}"

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        data_edge = self.find_edge(inputs, "data-input")
        source_expr = self.expression_from_edge(data_edge) or "df"

        loop_lines = [
            f"source_df_{safe_id} = {source_expr}",
            f"if isinstance(source_df_{safe_id}, pd.Series):",
            f"    source_df_{safe_id} = source_df_{safe_id}.to_frame(name='close')",
            f"if not isinstance(source_df_{safe_id}, pd.DataFrame):",
            f"    source_df_{safe_id} = df",
            f"timeframes_{safe_id} = {timeframes!r}",
            f"ohlc_map_{safe_id} = {{'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}}",
            f"for tf in timeframes_{safe_id}:",
            f"    aggregated_{safe_id} = source_df_{safe_id}.resample(tf).agg(ohlc_map_{safe_id})",
            f"    aggregated_{safe_id} = aggregated_{safe_id}.reindex(df.index, method='ffill').fillna(method='bfill')",
            f"    suffix_{safe_id} = tf.replace(' ', '').replace(':', '').replace('-', '')",
            f"    for column in ['open', 'high', 'low', 'close', 'volume']:",
            f"        df[f'{prefix}_' + column + '_' + suffix_{safe_id}] = aggregated_{safe_id}[column]",
            f"if timeframes_{safe_id}:",
            f"    highest_tf_{safe_id} = timeframes_{safe_id}[-1]",
            f"    df_multi_{safe_id} = source_df_{safe_id}.resample(highest_tf_{safe_id}).agg(ohlc_map_{safe_id})",
            f"    df_multi_{safe_id} = df_multi_{safe_id}.reindex(df.index, method='ffill').fillna(method='bfill')",
            f"else:",
            f"    df_multi_{safe_id} = source_df_{safe_id}",
        ]

        return "\n".join([f"# Multi-timeframe aggregation for node {node.id}"] + loop_lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]

