"""Handler for logic gate nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class LogicHandler(NodeHandler):
    node_type = "logic"

    LOGIC_MAP = {
        "AND": "and",
        "OR": "or",
    }

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        operation = params.get("operation", "AND")

        py_operator = self.LOGIC_MAP.get(operation, "and")

        # Get the variable names of the input conditions/logics
        incoming_node_ids = generator.get_incoming(node.id)
        if not incoming_node_ids:
            return "# Warning: Logic node has no inputs."

        # The result of a condition/logic node is a variable named `..._met`
        # We need to find out the type of the source node to construct the variable name.
        input_vars = []
        for source_id in incoming_node_ids:
            source_node = generator.node_map.get(source_id)
            if not source_node:
                continue

            # Assuming the variable name is based on the source node's type and id.
            # e.g., condition_... or logic_...
            sanitized_id = self.sanitize_id(source_id)
            if source_node.type == 'condition':
                input_vars.append(f"condition_{sanitized_id}")
            elif source_node.type == 'logic':
                input_vars.append(f"logic_{sanitized_id}")


        if not input_vars:
            return f"# Warning: Could not resolve inputs for Logic node {node.id}."

        # The variable name for this logic node's result
        result_var = f"logic_{self.sanitize_id(node.id)}"

        # Combine the inputs with the operator
        expression = f" {py_operator} ".join(input_vars)

        return f"{result_var} = {expression}"

    def required_packages(self) -> List[str]:
        return []
