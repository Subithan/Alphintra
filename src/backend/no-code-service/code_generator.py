from __future__ import annotations

"""Simplified code generation core.

This module exposes a :class:`Generator` that turns a workflow
representation into a block of Python code.  The generator itself does not
know how to deal with individual node types; instead it delegates the
responsibility to specialised :class:`NodeHandler` implementations that live
inside the ``node_handlers`` package.

The design allows new node types to be supported by simply dropping a new
handler class into the registry.
"""

from datetime import datetime
from typing import Dict, Any, List

# ``code_generator`` sits alongside the ``node_handlers`` package.  Import the
# registry and base class directly so this module can be used as a standalone
# script or as part of the package.
from node_handlers import HANDLER_REGISTRY, NodeHandler


class Generator:
    """Core workflow code generator.

    The generator iterates through workflow nodes and dispatches them to
    registered :class:`NodeHandler` instances.  Each handler returns a string
    containing the Python code snippet for its node.  The snippets are then
    concatenated into the final strategy code block.
    """

    def __init__(self) -> None:
        # Handlers are stored in a simple dictionary registry.
        self.handlers: Dict[str, NodeHandler] = dict(HANDLER_REGISTRY)

    # ------------------------------------------------------------------
    # Registry management
    # ------------------------------------------------------------------
    def register_handler(self, handler: NodeHandler) -> None:
        """Register a new handler at runtime."""

        self.handlers[handler.node_type] = handler

    def get_handler(self, node_type: str) -> NodeHandler | None:
        """Return handler for ``node_type`` if it exists."""

        return self.handlers.get(node_type)

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def generate_strategy_code(self, workflow: Dict[str, Any], name: str = "GeneratedStrategy") -> Dict[str, Any]:
        """Generate Python code for a given workflow.

        Parameters
        ----------
        workflow:
            Workflow dictionary containing ``nodes`` and ``edges`` lists.
        name:
            Optional strategy name.  Stored in the returned metadata.
        """

        code_lines: List[str] = []
        nodes = workflow.get("nodes", [])
        for node in nodes:
            handler = self.get_handler(node.get("type", ""))
            if handler:
                snippet = handler.handle(node, self)
                if snippet:
                    code_lines.append(snippet)
        code = "\n".join(code_lines)

        return {
            "code": code,
            "requirements": [],
            "metadata": {
                "name": name,
                "generatedAt": datetime.utcnow().isoformat(),
            },
            "success": True,
        }


# Backwards compatibility -------------------------------------------------
# ``main.py`` historically imported ``CodeGenerator``.  Keep the same name so
# existing code continues to function.
CodeGenerator = Generator


__all__ = ["Generator", "CodeGenerator"]
