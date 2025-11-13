"""Handler for action nodes."""

from __future__ import annotations

from typing import List

from ir import Node
from .base import EdgeReference, NodeHandler


class ActionHandler(NodeHandler):
    node_type = "action"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - see base class
        params = node.data.get("parameters", {})
        action = str(params.get("action", node.data.get("label", "hold"))).upper()
        quantity = params.get("quantity", params.get("positionSize", 1))
        take_profit = params.get("take_profit", params.get("takeProfit"))
        stop_loss = params.get("stop_loss", params.get("stopLoss"))
        order_type = str(params.get("order_type", params.get("orderType", "market"))).lower()
        action_category = str(params.get("actionCategory", "entry")).lower()
        time_in_force = params.get("timeInForce", "GTC")
        trail_percent = params.get("trailingPercent", params.get("trailPercent"))
        limit_price = params.get("limitPrice")
        capital_base = float(params.get("capitalBase", 100000))
        sizing_mode = str(params.get("positionSizing", params.get("sizingMode", "fixed"))).lower()

        safe_id = self.sanitize_id(node.id)
        decision_column = f"decision_{safe_id}"
        quantity_column = f"quantity_{safe_id}"
        order_type_column = f"order_type_{safe_id}"
        tif_column = f"time_in_force_{safe_id}"

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        signal_edge = self.find_edge(inputs, "signal-input")
        signal_expr = self.expression_from_edge(signal_edge)

        if not signal_expr or signal_expr == "df":
            signal_expr = "pd.Series(False, index=df.index)"

        if action_category == "exit":
            decision_value = "EXIT"
        elif action_category == "management":
            decision_value = action or "MANAGE"
        else:
            decision_value = "BUY" if action == "BUY" else "SELL" if action == "SELL" else action

        lines = [f"# Action execution for node {node.id}"]
        signal_var = f"signal_{safe_id}"
        lines.append(f"{signal_var} = {signal_expr}.fillna(False).astype(bool)")
        lines.append(f"df['{decision_column}'] = 'HOLD'")
        lines.append(f"df.loc[{signal_var}, '{decision_column}'] = '{decision_value}'")
        lines.append(f"df['{order_type_column}'] = '{order_type.upper()}'")
        lines.append(f"df['{tif_column}'] = '{time_in_force}'")

        if isinstance(quantity, (int, float)):
            quantity_literal = float(quantity)
        else:
            quantity_literal = repr(quantity) if quantity is not None else 0

        if sizing_mode == "percentage":
            percent = float(params.get("percentSize", quantity_literal))
            lines.append(f"df['{quantity_column}'] = 0")
            lines.append(
                f"df.loc[{signal_var}, '{quantity_column}'] = ( {percent} / 100 ) * {capital_base} / df.loc[{signal_var}, 'close'].replace(0, pd.NA)"
            )
        elif sizing_mode == "risk":
            risk_pct = float(params.get("riskPercent", 1.0))
            lines.append(f"df['{quantity_column}'] = 0")
            lines.append(
                f"df.loc[{signal_var}, '{quantity_column}'] = (({risk_pct} / 100) * {capital_base}) / (df.loc[{signal_var}, 'close'] - df.loc[{signal_var}, 'close'] * (1 - {float(stop_loss or 1)/100}))"
            )
        else:
            lines.append(f"df['{quantity_column}'] = 0")
            lines.append(f"df.loc[{signal_var}, '{quantity_column}'] = {quantity_literal}")

        if take_profit is not None:
            tp_literal = float(take_profit) if isinstance(take_profit, (int, float)) else None
            tp_column = f"take_profit_{safe_id}"
            lines.append(f"df['{tp_column}'] = pd.NA")
            if tp_literal is not None:
                lines.append(
                    f"df.loc[{signal_var}, '{tp_column}'] = df.loc[{signal_var}, 'close'] * (1 + {tp_literal} / 100)"
                )
            else:
                lines.append(
                    f"df.loc[{signal_var}, '{tp_column}'] = {repr(take_profit)}"
                )

        if stop_loss is not None:
            sl_literal = float(stop_loss) if isinstance(stop_loss, (int, float)) else None
            sl_column = f"stop_loss_{safe_id}"
            lines.append(f"df['{sl_column}'] = pd.NA")
            if sl_literal is not None:
                lines.append(
                    f"df.loc[{signal_var}, '{sl_column}'] = df.loc[{signal_var}, 'close'] * (1 - {sl_literal} / 100)"
                )
            else:
                lines.append(
                    f"df.loc[{signal_var}, '{sl_column}'] = {repr(stop_loss)}"
                )

        if order_type == "limit" and limit_price is not None:
            limit_column = f"limit_price_{safe_id}"
            limit_literal = float(limit_price) if isinstance(limit_price, (int, float)) else repr(limit_price)
            lines.append(f"df['{limit_column}'] = pd.NA")
            lines.append(f"df.loc[{signal_var}, '{limit_column}'] = {limit_literal}")

        if order_type in {"trailing", "trailing_stop"} and trail_percent is not None:
            trail_column = f"trailing_stop_{safe_id}"
            lines.append(f"df['{trail_column}'] = pd.NA")
            lines.append(
                f"df.loc[{signal_var}, '{trail_column}'] = df.loc[{signal_var}, 'close'] * (1 - {float(trail_percent)}/100)"
            )

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
