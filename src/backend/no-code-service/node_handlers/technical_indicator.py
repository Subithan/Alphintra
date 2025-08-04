"""Handler for technical indicator nodes."""

from typing import Dict, Any

from .base import NodeHandler


class TechnicalIndicatorHandler(NodeHandler):
    node_type = "technicalIndicator"

    def handle(self, node: Dict[str, Any], generator) -> str:
        params = node.get("data", {}).get("parameters", {})
        indicator = params.get("indicator", "SMA")
        period = params.get("period", 20)
        source = params.get("source", "close")
        var_name = f"{indicator.lower()}_{node['id'].replace('-', '_')}"
        return (
            f"self.indicators['{var_name}'] = "
            f"ta.{indicator}(self.data['{source}'], timeperiod={period})"
        )
