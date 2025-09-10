"""Handler for data source nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class DataSourceHandler(NodeHandler):
    node_type = "dataSource"

    def handle(self, node: Node, generator) -> str:
        # Data fetching is handled by the strategy template's run loop.
        # This handler's primary role is to allow the generator to identify
        # the node and extract parameters from it. It does not need to
        # generate any code for the strategy class methods.
        return ""

    def required_packages(self) -> List[str]:
        return []
