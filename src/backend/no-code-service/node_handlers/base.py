"""Base classes for node handlers used by the code generator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any


class NodeHandler(ABC):
    """Abstract handler for a workflow node."""

    #: Type identifier for the node this handler supports.
    node_type: str

    @abstractmethod
    def handle(self, node: Dict[str, Any], generator: "Generator") -> str:
        """Return code snippet for *node*.

        Parameters
        ----------
        node:
            The node dictionary from the workflow definition.
        generator:
            Instance of :class:`Generator` requesting the code.  This allows
            handlers to access shared context or register additional handlers
            if required.
        """

        raise NotImplementedError
