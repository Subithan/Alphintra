"""Handler for data source nodes."""

from typing import Dict, Any

from .base import NodeHandler


class DataSourceHandler(NodeHandler):
    node_type = "dataSource"

    def handle(self, node: Dict[str, Any], generator) -> str:
        params = node.get("data", {}).get("parameters", {})
        symbol = params.get("symbol", "AAPL")
        timeframe = params.get("timeframe", "1h")
        return f"# Data source for {symbol} ({timeframe})"
