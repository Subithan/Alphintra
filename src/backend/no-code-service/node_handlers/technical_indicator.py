"""Handler for technical indicator nodes."""

from typing import Dict, Any, List

from .base import NodeHandler


class TechnicalIndicatorHandler(NodeHandler):
    node_type = "technicalIndicator"

    def handle(self, node: Dict[str, Any], generator) -> str:
        params = node.get("data", {}).get("parameters", {})
        indicator = params.get("indicator", "SMA")
        period = params.get("period", 20)
        source_col = params.get("source", "close")

        inputs = generator.get_incoming(node["id"])
        df_var = f"data_{self.sanitize_id(inputs[0])}" if inputs else "data"
        col_name = f"feature_{self.sanitize_id(node['id'])}"

        return (
            f"{df_var}['{col_name}'] = "
            f"ta.{indicator}({df_var}['{source_col}'], timeperiod={period})"
        )

    def required_packages(self) -> List[str]:
        return ["pandas", "ta-lib"]
