"""Base classes for node handlers used by the code generator."""

from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import List, Optional, Tuple

from ir import Node


EdgeReference = Tuple[str, str, str]


class NodeHandler(ABC):
    """Abstract handler for a workflow node."""

    #: Type identifier for the node this handler supports.
    node_type: str

    @abstractmethod
    def handle(self, node: Node, generator: "Generator") -> str:
        """Return code snippet for *node*.

        Parameters
        ----------
        node:
            The :class:`~no-code-service.ir.Node` instance representing the
            workflow node.
        generator:
            Instance of :class:`Generator` requesting the code.  This allows
            handlers to access shared context or register additional handlers
            if required.
        """

        raise NotImplementedError

    def required_packages(self) -> List[str]:
        """Return third-party packages required by this handler.

        Sub-classes can override this to declare additional dependencies
        that are needed for the generated code snippet to run.  The generator
        aggregates these across all nodes and writes them to ``requirements.txt``.
        """

        return []

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

    # ------------------------------------------------------------------
    # Graph helpers used by concrete handlers
    # ------------------------------------------------------------------
    @staticmethod
    def find_edge(edges: List[EdgeReference], handle: str) -> Optional[EdgeReference]:
        """Return the first edge targeting *handle* if present."""

        for edge in edges:
            if edge[2] == handle:
                return edge
        return None

    def expression_from_edge(self, edge: Optional[EdgeReference]) -> Optional[str]:
        """Translate an edge reference into a dataframe expression."""

        if not edge:
            return None

        source_id, source_handle, _ = edge
        safe_source = self.sanitize_id(source_id)
        handle_name = source_handle or ""

        if handle_name == "data-output":
            return "df"
        if handle_name.startswith("output"):
            suffix = ""
            if "-" in handle_name:
                _, index = handle_name.split("-", 1)
                suffix = "" if index in {"", "1"} else f"_{index}"
            return f"df['indicator_{safe_source}{suffix}']"
        if handle_name == "signal-output":
            return f"df['signal_{safe_source}']"
        if handle_name == "output":
            return f"df['logic_{safe_source}']"
        if handle_name == "risk-output":
            return f"df['risk_{safe_source}']"
        if handle_name == "action-output":
            return f"df['decision_{safe_source}']"

        normalised_handle = handle_name.replace("-", "_")
        return f"df['{safe_source}_{normalised_handle}']"

    def resolve_series_expression(
        self,
        edge: Optional[EdgeReference],
        default_column: str,
    ) -> str:
        """Return a pandas Series expression for *edge* or a default column."""

        expr = self.expression_from_edge(edge)
        if not expr or expr == "df":
            return f"df['{default_column}']"
        return expr
