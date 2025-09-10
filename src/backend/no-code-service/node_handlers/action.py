"""Handler for action nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class ActionHandler(NodeHandler):
    node_type = "action"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        action = params.get("action", "hold") # buy, sell

        # Find the final logic/condition node that triggers this action
        incoming_node_ids = generator.get_incoming(node.id)
        if not incoming_node_ids:
            return f'# Warning: Action node "{node.id}" has no trigger.'

        source_id = incoming_node_ids[0]
        source_node = generator.node_map.get(source_id)
        if not source_node:
            return f'# Warning: Could not find source node {source_id} for action {node.id}'

        # Construct the name of the variable that holds the trigger's result
        sanitized_id = self.sanitize_id(source_id)
        if source_node.type == 'condition':
            trigger_variable = f"condition_{sanitized_id}"
        elif source_node.type == 'logic':
            trigger_variable = f"logic_{sanitized_id}"
        else:
            return f'# Warning: Action node "{node.id}" is triggered by an unsupported node type.'

        # Create the dictionary to be returned for the signal
        signal_dict = {
            "signal": action.upper(),
            "quantity": params.get("quantity"),
            "order_type": params.get("order_type"),
            "stop_loss": params.get("stop_loss"),
            "take_profit": params.get("take_profit"),
        }

        # Generate the 'if' block that returns the signal dictionary
        # This code will be placed inside the `evaluate_conditions` method
        code = f"""
if {trigger_variable}:
    # Logic for action '{node.data.get('label')}' triggered
    return {signal_dict}
"""
        return code.strip()

    def required_packages(self) -> List[str]:
        return []
