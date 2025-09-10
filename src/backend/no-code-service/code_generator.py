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
from typing import Dict, Any, List, Set
import os
import json
from textwrap import dedent
import textwrap

# ``code_generator`` sits alongside the ``node_handlers`` package.  Import the
# registry and base class directly so this module can be used as a standalone
# script or as part of the package.
from node_handlers import HANDLER_REGISTRY, NodeHandler, FALLBACK_HANDLER
from ir import Node, Edge, Workflow

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
        # Fallback handler used when no specific handler is registered.
        self.fallback_handler: NodeHandler = FALLBACK_HANDLER
        # Store workflow structure so handlers can resolve connections between
        # nodes when emitting code.
        self.nodes: List[Node] = []
        self.node_map: Dict[str, Node] = {}
        self.edges: List[Edge] = []

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

        return [e.source for e in self.edges if e.target == node_id]

    def topological_sort(self) -> List[Node]:
        """
        Performs a topological sort of the workflow nodes.
        Uses the graph representation already stored on the instance.
        """
        # Build in-degree map and adjacency list from self.edges
        in_degree = {node_id: 0 for node_id in self.node_map}
        adj = {node_id: [] for node_id in self.node_map}
        for edge in self.edges:
            if edge.source in adj and edge.target in in_degree:
                adj[edge.source].append(edge.target)
                in_degree[edge.target] += 1

        # Initialize the queue with all nodes that have an in-degree of 0
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]

        sorted_nodes = []
        while queue:
            node_id = queue.pop(0)
            if node_id in self.node_map:
                sorted_nodes.append(self.node_map[node_id])

            # For each neighbor, decrement its in-degree
            for neighbor_id in adj.get(node_id, []):
                in_degree[neighbor_id] -= 1
                # If in-degree becomes 0, add it to the queue
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        return sorted_nodes

    # ------------------------------------------------------------------
    # Parsing & Validation helpers
    # ------------------------------------------------------------------
    def parse_workflow(self, workflow: Dict[str, Any]) -> Workflow:
        """Convert workflow JSON definition into internal IR."""

        return Workflow.from_json(workflow)

    def validate_workflow(self, ir: Workflow) -> Dict[str, List[str]]:
        """Validate basic workflow structure.

        Checks for required node types, disconnected nodes and cycles.  Returns
        a dictionary containing ``errors`` and ``warnings`` lists which can be
        surfaced to calling services.
        """

        nodes = list(ir.nodes.values())
        edges = ir.edges
        graph = ir.adjacency()
        in_degree = ir.in_degree()

        errors: List[str] = []
        warnings: List[str] = []

        # Required node types -------------------------------------------------
        if not any(node.type == "dataSource" for node in nodes):
            errors.append("Workflow must include at least one data source node")

        if not any(node.type == "action" for node in nodes):
            warnings.append("Workflow should include at least one action node")

        # Disconnected nodes --------------------------------------------------
        connected: set[str] = set()
        for edge in edges:
            if edge.source in graph and edge.target in graph:
                connected.add(edge.source)
                connected.add(edge.target)

        disconnected = [node.id for node in nodes if node.id not in connected]
        if disconnected and len(nodes) > 1:
            warnings.append("Disconnected nodes: " + ", ".join(disconnected))

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
    def generate_strategy_code(
        self, workflow: Dict[str, Any], name: str = "GeneratedStrategy"
    ) -> Dict[str, Any]:
        """Generate a live trading script for a given workflow.

        The generator walks through the workflow collecting code snippets for
        data sourcing, indicator calculation, condition evaluation, and actions.
        These pieces are then inserted into a live trading template that runs
        in a continuous loop. The final script is written to
        ``generated/generated_strategy.py`` for convenience and the code is
        returned to the caller as a string.
        """

        ir = self.parse_workflow(workflow)
        # Persist structure for handlers requiring edge information
        self.nodes = list(ir.nodes.values())
        self.node_map = ir.nodes
        self.edges = ir.edges

        validation = self.validate_workflow(ir)
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

        # --- New snippet categories for live trading ---
        indicator_lines: List[str] = []
        condition_lines: List[str] = []
        action_lines: List[str] = []
        requirements: Set[str] = set(BASE_REQUIREMENTS)

        # This will hold config values extracted from nodes, e.g., symbol, timeframe
        strategy_config = {}

        sorted_nodes = self.topological_sort()

        for node in sorted_nodes:
            handler = self.get_handler(node.type)
            if not handler:
                handler = self.fallback_handler

            snippet = handler.handle(node, self)
            if not snippet:
                continue

            requirements.update(handler.required_packages())

            ntype = node.type
            if ntype in {"dataSource", "customDataset"}:
                # Extract config from dataSource node
                params = node.data.get("parameters", {})
                strategy_config['symbol'] = params.get('symbol', 'BTC/USDT')
                strategy_config['timeframe'] = params.get('timeframe', '1h')
            elif ntype == "technicalIndicator":
                indicator_lines.append(snippet)
            elif ntype in {"condition", "logic"}:
                condition_lines.append(snippet)
            elif ntype == "action":
                action_lines.append(snippet)
            else:
                indicator_lines.append(snippet)

        # --- New template for live trading ---
        template = dedent(
            '''"""Auto-generated live trading script."""

# Imports
import pandas as pd
import numpy as np
import talib as ta
import time
import json
import os

# This is a placeholder for a real broker connection
class MockBroker:
    def get_latest_data(self, symbol, timeframe):
        """Generates mock OHLCV data."""
        print("Fetching latest data for " + symbol + " on " + timeframe + " timeframe...")
        data = {{
            'open': np.random.uniform(100, 102, 100),
            'high': np.random.uniform(102, 104, 100),
            'low': np.random.uniform(99, 101, 100),
            'close': np.random.uniform(101, 103, 100),
            'volume': np.random.uniform(1000, 5000, 100)
        }}
        return pd.DataFrame(data)

class Strategy:
    def __init__(self, config):
        self.config = config
        self.broker = MockBroker() # In a real scenario, this would be a real broker client

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates all technical indicators for the strategy."""
{indicator_code}
        return df

    def evaluate_conditions(self, df: pd.DataFrame) -> dict:
        """Evaluates the logic to determine if a signal should be generated."""
        if len(df) < 2:
            return {{ "signal": "HOLD" }} # Not enough data to evaluate

        latest_row = df.iloc[-1]
        previous_row = df.iloc[-2]
{condition_code}
        return {{ "signal": "HOLD" }} # Default action

    def execute_signal(self, signal_data: dict, df: pd.DataFrame):
        """Executes the given signal."""
        if not signal_data or signal_data.get("signal", "HOLD") == "HOLD":
            return

        latest_price = df.iloc[-1]['close']
        signal_data['price'] = latest_price
        signal_data['timestamp'] = pd.Timestamp.now().isoformat()

        print("--- SIGNAL GENERATED ---")
        print(json.dumps(signal_data, indent=2))
        print("------------------------")

    def run(self):
        """Main strategy execution loop."""
        print("Starting strategy '" + str(self.config.get('name', 'Unnamed Strategy')) + "'...")
        print("Configuration: " + json.dumps(self.config, indent=2))

        while True:
            try:
                # 1. Fetch latest data
                df = self.broker.get_latest_data(
                    self.config.get('symbol'),
                    self.config.get('timeframe')
                )

                # 2. Calculate indicators
                df = self.calculate_indicators(df)

                # 3. Evaluate conditions to get a signal
                signal_data = self.evaluate_conditions(df)

                # 4. Execute signal if it's not HOLD
                if signal_data.get("signal", "HOLD") != "HOLD":
                    self.execute_signal(signal_data, df)

                # Wait for the next candle
                print("Waiting for next candle...")
                time.sleep(60) # Placeholder for actual timeframe logic

            except Exception as e:
                print("An error occurred: " + str(e))
                time.sleep(60)


if __name__ == '__main__':
    config = {strategy_config}
    config['name'] = "{strategy_name}"
    strategy = Strategy(config)
    strategy.run()
'''
        )

        # Combine conditions and actions, as actions are 'if...return' statements
        # that belong in the same evaluation method.
        evaluation_code_lines = condition_lines + action_lines

        # Indent the code blocks correctly for insertion into the class methods
        indicator_code_block = textwrap.indent(
            "\n".join(indicator_lines) or "        pass", "        "
        )
        condition_code_block = textwrap.indent(
            "\n".join(evaluation_code_lines) or "        pass", "        "
        )

        code = template.format(
            indicator_code=indicator_code_block,
            condition_code=condition_code_block,
            strategy_config=json.dumps(strategy_config, indent=4),
            strategy_name=name,
        )

        requirements_list = sorted(requirements)

        # --- Persist to new files ---
        output_dir = os.path.join(os.path.dirname(__file__), "generated")
        os.makedirs(output_dir, exist_ok=True)

        # Write the main strategy script
        with open(os.path.join(output_dir, "generated_strategy.py"), "w", encoding="utf-8") as f:
            f.write(code)

        # Write the requirements file
        with open(
            os.path.join(output_dir, "requirements.txt"), "w", encoding="utf-8"
        ) as f:
            f.write("\n".join(requirements_list))

        # --- Metadata and README ---
        metadata = {
            "name": name,
            "description": "Auto-generated live trading script",
            "generatedAt": datetime.utcnow().isoformat(),
            "complexity": {
                "nodes": len(self.nodes),
                "edges": len(self.edges),
                "linesOfCode": len(code.splitlines()),
            },
            "config": strategy_config
        }
        with open(
            os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(metadata, f, indent=2)

        readme_content = (
            dedent(
                f"""# Generated Strategy

                This directory contains an auto-generated trading strategy `generated_strategy.py`.

                ## Usage
                This script is designed to run continuously. Ensure you have a broker connection
                properly configured (the default is a mock broker).

                ```bash
                pip install -r requirements.txt
                python generated_strategy.py
                ```
                """
            ).strip()
            + "\n"
        )
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
