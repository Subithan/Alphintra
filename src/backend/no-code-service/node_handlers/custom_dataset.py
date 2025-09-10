"""Handler for custom dataset nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class CustomDatasetHandler(NodeHandler):
    node_type = "customDataset"

    def handle(self, node: Node, generator) -> str:
        # Custom datasets are not applicable for the live trading script,
        # which relies on continuously fetched data from a broker.
        # This handler will return an empty string.
        return "# Warning: CustomDataset nodes are not supported in live trading mode."

    def required_packages(self) -> List[str]:
        return []
