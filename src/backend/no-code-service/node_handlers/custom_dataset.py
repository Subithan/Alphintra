"""Handler for custom dataset nodes."""

from typing import Dict, Any

from .base import NodeHandler


class CustomDatasetHandler(NodeHandler):
    node_type = "customDataset"

    def handle(self, node: Dict[str, Any], generator) -> str:
        path = node.get("data", {}).get("parameters", {}).get("fileName", "dataset.csv")
        return f"# Custom dataset from {path}"
