"""Fallback handler for unknown node types."""

import logging
from typing import List

from ir import Node
from .base import NodeHandler

logger = logging.getLogger(__name__)


class FallbackHandler(NodeHandler):
    """Handler used when no specific handler exists for a node type.

    The handler logs a warning and returns an empty string so the generator can
    continue processing the workflow. This preserves forward compatibility when
    newer node types are encountered by older versions of the service.
    """

    node_type = "__fallback__"

    def handle(self, node: Node, generator) -> str:  # noqa: D401
        logger.warning(
            "No handler registered for node type '%s'; node '%s' will be processed as a placeholder",
            node.type,
            node.id,
        )
        col_name = f"unknown_{self.sanitize_id(node.id)}"
        return (
            f"df['{col_name}'] = None  # Unsupported node type {node.type}"
        )

    def required_packages(self) -> List[str]:
        return ["pandas"]

