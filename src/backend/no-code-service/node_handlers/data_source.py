"""Handler for data source nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class DataSourceHandler(NodeHandler):
    node_type = "dataSource"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        symbol = params.get("symbol", "AAPL")
        timeframe = params.get("timeframe", "1h")
        return (
            f"df = pd.DataFrame()  # TODO load {symbol} ({timeframe})"
        )

    def required_packages(self) -> List[str]:
        return ["pandas"]
