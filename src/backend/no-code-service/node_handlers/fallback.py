"""Fallback handler for unknown node types."""

from typing import Dict, Any
import logging

from .base import NodeHandler

logger = logging.getLogger(__name__)


class FallbackHandler(NodeHandler):
    """Handler used when no specific handler exists for a node type.

    The handler logs a warning and returns an empty string so the generator can
    continue processing the workflow. This preserves forward compatibility when
    newer node types are encountered by older versions of the service.
    """

    node_type = "__fallback__"

    def handle(self, node: Dict[str, Any], generator) -> str:  # noqa: D401
        logger.warning(
            "No handler registered for node type '%s'; node '%s' will be ignored",
            node.get("type"),
            node.get("id"),
        )
        return ""

