"""Handler for condition nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class ConditionHandler(NodeHandler):
    node_type = "condition"

    # Map frontend condition names to Python operators
    OPERATOR_MAP = {
        "greater_than": ">",
        "less_than": "<",
        "equal_to": "==",
        "greater_than_or_equal_to": ">=",
        "less_than_or_equal_to": "<=",
        "not_equal_to": "!=",
    }

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        condition_type = params.get("conditionType") # e.g., 'comparison', 'crossover'
        condition = params.get("condition", "greater_than")
        value = params.get("value", 0)

        inputs = generator.get_incoming(node.id)
        if not inputs:
            return "# Warning: Condition node has no input."

        source_node_id = inputs[0]
        source_feature_col = f"feature_{self.sanitize_id(source_node_id)}"
        result_var = f"condition_{self.sanitize_id(node.id)}"

        # --- Handle different condition types ---
        if condition_type == "crossover":
            # Crossover requires comparing current and previous values
            # e.g., value was below line, now it's above
            if condition == "crossover":
                expr = f"(previous_row['{source_feature_col}'] < {value}) and (latest_row['{source_feature_col}'] > {value})"
            elif condition == "crossunder":
                expr = f"(previous_row['{source_feature_col}'] > {value}) and (latest_row['{source_feature_col}'] < {value})"
            else: # Handles cases where a second indicator is the value
                other_source_id = inputs[1]
                other_source_col = f"feature_{self.sanitize_id(other_source_id)}"
                if condition == "crossover":
                     expr = f"(previous_row['{source_feature_col}'] < previous_row['{other_source_col}']) and (latest_row['{source_feature_col}'] > latest_row['{other_source_col}'])"
                else: # crossunder
                     expr = f"(previous_row['{source_feature_col}'] > previous_row['{other_source_col}']) and (latest_row['{source_feature_col}'] < latest_row['{other_source_col}'])"

        else: # Default to "comparison"
            operator = self.OPERATOR_MAP.get(condition, ">")
            expr = f"latest_row['{source_feature_col}'] {operator} {value}"

        return f"{result_var} = {expr}"

    def required_packages(self) -> List[str]:
        return []
