"""Handler for condition nodes."""

from typing import Dict, Any, List

from .base import NodeHandler


class ConditionHandler(NodeHandler):
    node_type = "condition"

    def handle(self, node: Dict[str, Any], generator) -> str:
        params = node.get("data", {}).get("parameters", {})
        operator = params.get("operator", ">")
        threshold = params.get("threshold", 0)

        inputs = generator.get_incoming(node["id"])
        data_src = None
        features: list[str] = []
        for src in inputs:
            src_type = generator.node_map.get(src, {}).get("type")
            if src_type == "dataSource" and not data_src:
                data_src = src
            else:
                features.append(src)

        if not data_src:
            # Fallback: assume all features belong to the first input's frame
            data_src = inputs[0] if inputs else ""

        df_var = f"data_{self.sanitize_id(data_src)}" if data_src else "data"
        target_col = f"target_{self.sanitize_id(node['id'])}"

        if features:
            feat = f"feature_{self.sanitize_id(features[0])}"
            expr = f"{df_var}['{feat}'] {operator} {threshold}"
        else:
            expr = "False"

        return f"{df_var}['{target_col}'] = ({expr}).astype(int)"

    def required_packages(self) -> List[str]:
        return ["pandas"]
