"""Base classes for node handlers used by the code generator."""

from __future__ import annotations

from abc import ABC, abstractmethod
import re
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

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    @staticmethod
    def sanitize_id(raw_id: str) -> str:
        """Return a safe Python identifier for *raw_id*.

        Node identifiers can contain characters that are not valid in Python
        variable names (dashes, spaces, leading numbers, …).  Handlers use this
        helper to derive variable/column names that won't clash with Python's
        syntax rules.
        """

        # Replace any non-word character and prepend an underscore when the
        # identifier starts with a digit.
        return re.sub(r"\W|^(?=\d)", "_", str(raw_id))
