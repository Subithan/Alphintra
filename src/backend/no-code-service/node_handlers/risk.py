"""Handler for risk management nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class RiskHandler(NodeHandler):
    node_type = "risk"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        safe_id = self.sanitize_id(node.id)
        capital_base = float(params.get("capitalBase", 100000))
        max_loss = float(params.get("maxLoss", 2.0))
        portfolio_heat = float(params.get("portfolioHeat", 15.0))
        drawdown_limit = float(params.get("maxDrawdown", 10.0))
        exposure_limit = float(params.get("maxExposure", 0.5))
        var_window = int(params.get("varWindow", 30))
        emergency_action = params.get("emergencyAction", "reduce_positions")

        size_column = f"risk_position_size_{safe_id}"
        drawdown_column = f"risk_drawdown_alert_{safe_id}"
        heat_column = f"risk_heat_{safe_id}"
        var_column = f"risk_var_{safe_id}"
        action_column = f"risk_action_{safe_id}"

        lines = [f"# Risk management block for node {node.id}"]
        lines.extend([
            f"portfolio_value_{safe_id} = {capital_base}",
            f"max_loss_value_{safe_id} = portfolio_value_{safe_id} * {max_loss} / 100",
            f"df['{size_column}'] = max_loss_value_{safe_id} / df['close'].replace(0, pd.NA)",
            f"rolling_peak_{safe_id} = df['close'].cummax()",
            f"drawdown_{safe_id} = (df['close'] - rolling_peak_{safe_id}) / rolling_peak_{safe_id} * 100",
            f"df['{drawdown_column}'] = (drawdown_{safe_id} <= -{drawdown_limit}).fillna(False)",
            f"positions_{safe_id} = df.filter(like='quantity_').sum(axis=1).replace(pd.NA, 0)",
            f"df['{heat_column}'] = (positions_{safe_id}.abs() / portfolio_value_{safe_id}) * 100",
            f"pct_changes_{safe_id} = df['close'].pct_change().fillna(0)",
            f"df['{var_column}'] = pct_changes_{safe_id}.rolling(window={var_window}, min_periods=1).quantile(0.05) * portfolio_value_{safe_id}",
            f"exposure_{safe_id} = (positions_{safe_id}.abs() / portfolio_value_{safe_id})",
            f"risk_flags_{safe_id} = (df['{drawdown_column}'] | (df['{heat_column}'] > {portfolio_heat}) | (exposure_{safe_id} > {exposure_limit}) | (df['{var_column}'] < -max_loss_value_{safe_id}))",
            f"df['{action_column}'] = 'hold'",
            f"df.loc[risk_flags_{safe_id}, '{action_column}'] = '{emergency_action}'",
        ])

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
