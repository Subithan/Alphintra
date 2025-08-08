"""Handler for custom dataset nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class CustomDatasetHandler(NodeHandler):
    node_type = "customDataset"

    def handle(self, node: Node, generator) -> str:
        path = node.data.get("parameters", {}).get("fileName", "dataset.csv")
        return f"df = pd.read_csv('{path}')"

    def required_packages(self) -> List[str]:
        return ["pandas"]
