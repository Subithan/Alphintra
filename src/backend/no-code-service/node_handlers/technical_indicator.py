"""Handler for technical indicator nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class TechnicalIndicatorHandler(NodeHandler):
    node_type = "technicalIndicator"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        indicator = params.get("indicator", "SMA")
        period = params.get("period", 20)
        source_col = params.get("source", "close")

        col_name = f"feature_{self.sanitize_id(node.id)}"

        return (
            f"df['{col_name}'] = "
            f"ta.{indicator}(df['{source_col}'], timeperiod={period})"
        )

    def required_packages(self) -> List[str]:
        return ["pandas", "ta-lib"]
