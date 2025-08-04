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
from typing import Dict, Any, List, Tuple, Set
import os
import json
from textwrap import dedent

# ``code_generator`` sits alongside the ``node_handlers`` package.  Import the
# registry and base class directly so this module can be used as a standalone
# script or as part of the package.
from node_handlers import HANDLER_REGISTRY, NodeHandler

BASE_REQUIREMENTS = {"pandas", "numpy", "scikit-learn", "joblib"}


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
        # Store workflow structure so handlers can resolve connections between
        # nodes when emitting code.
        self.nodes: List[Dict[str, Any]] = []
        self.node_map: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []

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
    # Graph helpers
    # ------------------------------------------------------------------
    def get_incoming(self, node_id: str) -> List[str]:
        """Return IDs of nodes with edges leading to ``node_id``."""

        return [e.get("source") for e in self.edges if e.get("target") == node_id]

    # ------------------------------------------------------------------
    # Parsing & Validation helpers
    # ------------------------------------------------------------------
    def parse_workflow(self, workflow: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, List[str]], Dict[str, int]]:
        """Read workflow definition and build adjacency lists.

        Returns the nodes, edges, adjacency list mapping node IDs to their
        outbound neighbours and a dictionary containing the in-degree for each
        node.  Edges referencing unknown nodes are ignored during parsing and
        will be reported during validation.
        """

        nodes = workflow.get("nodes", []) or []
        edges = workflow.get("edges", []) or []

        graph: Dict[str, List[str]] = {node.get("id"): [] for node in nodes}
        in_degree: Dict[str, int] = {node.get("id"): 0 for node in nodes}

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source in graph and target in graph:
                graph[source].append(target)
                in_degree[target] += 1

        return nodes, edges, graph, in_degree

    def validate_workflow(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        graph: Dict[str, List[str]],
        in_degree: Dict[str, int],
    ) -> Dict[str, List[str]]:
        """Validate basic workflow structure.

        Checks for required node types, disconnected nodes and cycles.  Returns
        a dictionary containing ``errors`` and ``warnings`` lists which can be
        surfaced to calling services.
        """

        errors: List[str] = []
        warnings: List[str] = []

        # Required node types -------------------------------------------------
        if not any(node.get("type") == "dataSource" for node in nodes):
            errors.append("Workflow must include at least one data source node")

        if not any(node.get("type") == "action" for node in nodes):
            warnings.append("Workflow should include at least one action node")

        # Disconnected nodes --------------------------------------------------
        connected: set[str] = set()
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in graph and tgt in graph:
                connected.add(src)
                connected.add(tgt)

        disconnected = [node["id"] for node in nodes if node["id"] not in connected]
        if disconnected and len(nodes) > 1:
            warnings.append(
                "Disconnected nodes: " + ", ".join(disconnected)
            )

        # Cycle detection using Kahn's algorithm -----------------------------
        local_in_degree = dict(in_degree)
        queue = [nid for nid, deg in local_in_degree.items() if deg == 0]
        visited = 0

        while queue:
            current = queue.pop(0)
            visited += 1
            for neighbour in graph.get(current, []):
                local_in_degree[neighbour] -= 1
                if local_in_degree[neighbour] == 0:
                    queue.append(neighbour)

        if visited != len(nodes):
            errors.append("Workflow contains cycles")

        return {"errors": errors, "warnings": warnings}

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def generate_strategy_code(self, workflow: Dict[str, Any], name: str = "GeneratedStrategy") -> Dict[str, Any]:
        """Generate a training script for a given workflow.

        The generator walks through the workflow collecting code snippets for
        data loading, feature engineering and target generation.  These pieces
        are then inserted into a trainer template containing additional model
        training, evaluation and persistence boilerplate.  The final script is
        written to ``generated/trainer.py`` for convenience and the code is
        returned to the caller as a string.
        """

        nodes, edges, graph, in_degree = self.parse_workflow(workflow)
        # Persist structure for handlers requiring edge information
        self.nodes = nodes
        self.node_map = {n.get("id"): n for n in nodes}
        self.edges = edges

        validation = self.validate_workflow(nodes, edges, graph, in_degree)
        if validation["errors"]:
            return {
                "code": "",
                "requirements": [],
                "metadata": {
                    "name": name,
                    "generatedAt": datetime.utcnow().isoformat(),
                },
                "success": False,
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            }

        data_lines: List[str] = []
        feature_lines: List[str] = []
        label_lines: List[str] = []
        feature_cols: List[str] = []
        label_cols: List[str] = []
        df_name: str | None = None
        requirements: Set[str] = set(BASE_REQUIREMENTS)

        for node in nodes:
            handler = self.get_handler(node.get("type", ""))
            if not handler:
                continue
            snippet = handler.handle(node, self)
            if not snippet:
                continue

            requirements.update(handler.required_packages())

            ntype = node.get("type")
            if ntype == "dataSource":
                data_lines.append(snippet)
                if df_name is None:
                    df_name = f"data_{NodeHandler.sanitize_id(node['id'])}"
            elif ntype == "technicalIndicator":
                feature_lines.append(snippet)
                feature_cols.append(f"feature_{NodeHandler.sanitize_id(node['id'])}")
            elif ntype == "condition":
                label_lines.append(snippet)
                label_cols.append(f"target_{NodeHandler.sanitize_id(node['id'])}")

        df_name = df_name or "data"
        label_col = label_cols[0] if label_cols else "target"

        template = dedent(
            '''"""Auto-generated training script."""

# Imports
import pandas as pd
import numpy as np
import talib as ta
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Data Loading
{data_loading}

# Feature Generation
{feature_generation}

# Label Generation
{label_generation}

# Model Training
feature_cols = {feature_cols}
label_col = '{label_col}'
df = {df_name}
X = df[feature_cols]
y = df[label_col]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Evaluation
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Model Persistence
joblib.dump(model, 'trained_model.joblib')
'''
        )

        code = template.format(
            data_loading="\n".join(data_lines) or "# TODO: load data",
            feature_generation="\n".join(feature_lines) or "# TODO: generate features",
            label_generation="\n".join(label_lines) or "# TODO: generate labels",
            feature_cols=feature_cols,
            label_col=label_col,
            df_name=df_name,
        )

        requirements_list = sorted(requirements)

        # Persist trainer script and requirements to disk for convenience
        output_dir = os.path.join(os.path.dirname(__file__), "generated")
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "trainer.py"), "w", encoding="utf-8") as f:
            f.write(code)
        with open(os.path.join(output_dir, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(requirements_list))

        # Metadata -----------------------------------------------------------
        metadata = {
            "name": name,
            "description": "Auto-generated training script",
            "generatedAt": datetime.utcnow().isoformat(),
            "complexity": {
                "nodes": len(nodes),
                "edges": len(edges),
                "linesOfCode": len(code.splitlines()),
            },
        }
        with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # README -------------------------------------------------------------
        readme_content = dedent(
            f"""
            # Generated Trainer

            This directory contains an auto-generated training script `trainer.py`.

            ## Inputs
            * Data loading, feature engineering and label generation logic embedded in `trainer.py`.

            ## Outputs
            * Trained model saved as `trained_model.joblib`.
            * Evaluation report printed to the console.

            ## Usage
            ```bash
            pip install -r requirements.txt
            python trainer.py
            ```
            """
        ).strip() + "\n"
        with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)

        return {
            "code": code,
            "requirements": requirements_list,
            "metadata": metadata,
            "success": True,
            "warnings": validation["warnings"],
        }


# Backwards compatibility -------------------------------------------------
# ``main.py`` historically imported ``CodeGenerator``.  Keep the same name so
# existing code continues to function.
CodeGenerator = Generator


__all__ = ["Generator", "CodeGenerator"]
