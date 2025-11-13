"""Handler for logic gate nodes."""

from __future__ import annotations

import math
from typing import List

from ir import Node
from .base import EdgeReference, NodeHandler


class LogicHandler(NodeHandler):
    node_type = "logic"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - see base class
        params = node.data.get("parameters", {})
        operation = str(params.get("operation", "AND")).upper()
        safe_id = self.sanitize_id(node.id)
        column_name = f"logic_{safe_id}"

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        signal_edges = [edge for edge in inputs if edge[2].startswith("input")]
        signal_exprs = [self.expression_from_edge(edge) for edge in signal_edges]
        signal_exprs = [expr for expr in signal_exprs if expr]

        lines = [f"# Logic ({operation}) for node {node.id}"]

        if not signal_exprs:
            lines.append(f"df['{column_name}'] = pd.Series(False, index=df.index, dtype=bool)")
            return "\n".join(lines)

        concat_series = ", ".join(signal_exprs)
        if concat_series:
            lines.append(
                f"signals_{safe_id} = pd.concat([{concat_series}], axis=1).fillna(False)"
            )
        else:
            lines.append(f"signals_{safe_id} = pd.DataFrame(columns=['placeholder'])")

        if operation == "AND":
            combined = f"(signals_{safe_id}.all(axis=1))"
        elif operation == "OR":
            combined = f"(signals_{safe_id}.any(axis=1))"
        elif operation == "XOR":
            combined = f"(signals_{safe_id}.sum(axis=1) % 2 == 1)"
        elif operation == "NOT":
            combined = f"(~signals_{safe_id}.iloc[:, 0])"
        elif operation == "MAJORITY":
            threshold = int(params.get("threshold", math.floor(len(signal_exprs) / 2) + 1))
            combined = f"(signals_{safe_id}.sum(axis=1) >= {threshold})"
        elif operation == "WEIGHTED":
            weights = params.get("weights") or [1] * len(signal_exprs)
            weights = (weights + [weights[-1]])[:len(signal_exprs)]
            lines.append(f"weights_{safe_id} = pd.Series({weights}, dtype='float64')")
            combined = (
                f"(signals_{safe_id}.mul(weights_{safe_id}, axis=1).sum(axis=1) "
                f">= {params.get('weightThreshold', sum(weights)/2)})"
            )
        else:
            min_signals = int(params.get("minSignals", 1))
            combined = f"(signals_{safe_id}.sum(axis=1) >= {min_signals})"

        lines.append(f"df['{column_name}'] = ({combined}).fillna(False).astype(bool)")
        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
