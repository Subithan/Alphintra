"""Handler for technical indicator nodes."""

from __future__ import annotations

from typing import Callable, Dict, List

from ir import Node
from .base import EdgeReference, NodeHandler


class TechnicalIndicatorHandler(NodeHandler):
    node_type = "technicalIndicator"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - see base class
        params = node.data.get("parameters", {})
        indicator = str(params.get("indicator", params.get("indicatorType", "SMA"))).upper()
        safe_id = self.sanitize_id(node.id)

        inputs: List[EdgeReference] = generator.get_incoming(node.id)
        data_edge = self.find_edge(inputs, "data-input")
        series_expr = self.resolve_series_expression(data_edge, params.get("source", "close"))

        dispatcher: Dict[str, Callable[..., List[str]]] = {
            "SMA": self._trend_sma,
            "EMA": self._trend_ema,
            "WMA": self._trend_wma,
            "HMA": self._trend_hma,
            "RSI": self._momentum_rsi,
            "STOCH": self._momentum_stochastic,
            "MACD": self._momentum_macd,
            "BB": self._volatility_bollinger,
            "BOLLINGER": self._volatility_bollinger,
            "ATR": self._volatility_atr,
            "OBV": self._volume_obv,
            "VWAP": self._volume_vwap,
            "CCI": self._oscillator_cci,
            "MFI": self._oscillator_mfi,
        }

        handler = dispatcher.get(indicator, self._fallback_indicator)
        lines = [f"# Technical indicator: {indicator} ({node.id})"]
        lines.extend(handler(node, safe_id, series_expr, params, data_edge))
        return "\n".join(lines)

    # Helper utilities -------------------------------------------------
    @staticmethod
    def _output_column(safe_id: str, slot: int = 1) -> str:
        return f"indicator_{safe_id}" if slot <= 1 else f"indicator_{safe_id}_{slot}"

    def _trend_sma(self, node, safe_id, series, params, *_):
        period = int(params.get("period", params.get("timeperiod", 20)))
        column = self._output_column(safe_id, 1)
        return [f"df['{column}'] = {series}.rolling(window={period}, min_periods=1).mean()"]

    def _trend_ema(self, node, safe_id, series, params, *_):
        period = int(params.get("period", params.get("timeperiod", 20)))
        column = self._output_column(safe_id, 1)
        return [f"df['{column}'] = {series}.ewm(span={period}, adjust=False).mean()"]

    def _trend_wma(self, node, safe_id, series, params, *_):
        period = int(params.get("period", 14))
        column = self._output_column(safe_id, 1)
        weights = list(range(1, period + 1))
        return [
            f"weights_{safe_id} = pd.Series({weights}, dtype='float64')",
            f"df['{column}'] = ({series}.rolling(window={period}).apply(lambda x: (x * weights_{safe_id}).sum() / weights_{safe_id}.sum(), raw=True))",
            f"df['{column}'] = df['{column}'].fillna(method='bfill').fillna({series})",
        ]

    def _trend_hma(self, node, safe_id, series, params, *_):
        period = int(params.get("period", 21))
        column = self._output_column(safe_id, 1)
        half = max(1, period // 2)
        sqrt = max(1, int(period ** 0.5))
        return [
            f"wma_half_{safe_id} = {series}.rolling(window={half}).mean()*2",
            f"wma_full_{safe_id} = {series}.rolling(window={period}).mean()",
            f"diff_{safe_id} = wma_half_{safe_id} - wma_full_{safe_id}",
            f"df['{column}'] = diff_{safe_id}.rolling(window={sqrt}).mean()",
            f"df['{column}'] = df['{column}'].fillna(method='bfill').fillna({series})",
        ]

    def _momentum_rsi(self, node, safe_id, series, params, *_):
        period = int(params.get("period", 14))
        column = self._output_column(safe_id, 1)
        delta = f"delta_{safe_id}"
        gain = f"gain_{safe_id}"
        loss = f"loss_{safe_id}"
        rs = f"rs_{safe_id}"
        return [
            f"{delta} = {series}.diff()",
            f"{gain} = {delta}.clip(lower=0).ewm(alpha=1/{period}, adjust=False).mean()",
            f"{loss} = (-{delta}.clip(upper=0)).ewm(alpha=1/{period}, adjust=False).mean()",
            f"{rs} = {gain} / {loss}.replace(0, pd.NA)",
            f"df['{column}'] = 100 - (100 / (1 + {rs}))",
            f"df['{column}'] = df['{column}'].clip(0, 100).fillna(50)",
        ]

    def _momentum_stochastic(self, node, safe_id, series, params, data_edge):
        k_period = int(params.get("kPeriod", params.get("period", 14)))
        d_period = int(params.get("dPeriod", 3))
        high_expr = self.resolve_series_expression(data_edge, "high")
        low_expr = self.resolve_series_expression(data_edge, "low")
        k_col = self._output_column(safe_id, 1)
        d_col = self._output_column(safe_id, 2)
        return [
            f"lowest_{safe_id} = {low_expr}.rolling(window={k_period}, min_periods=1).min()",
            f"highest_{safe_id} = {high_expr}.rolling(window={k_period}, min_periods=1).max()",
            f"df['{k_col}'] = (({series} - lowest_{safe_id}) / (highest_{safe_id} - lowest_{safe_id}).replace(0, pd.NA) * 100).clip(0, 100)",
            f"df['{d_col}'] = df['{k_col}'].rolling(window={d_period}, min_periods=1).mean()",
            f"df[['{k_col}', '{d_col}']] = df[['{k_col}', '{d_col}']].fillna(method='bfill').fillna(50)",
        ]

    def _momentum_macd(self, node, safe_id, series, params, *_):
        fast = int(params.get("fastPeriod", 12))
        slow = int(params.get("slowPeriod", 26))
        signal = int(params.get("signalPeriod", 9))
        macd_col = self._output_column(safe_id, 1)
        signal_col = self._output_column(safe_id, 2)
        hist_col = self._output_column(safe_id, 3)
        return [
            f"fast_ema_{safe_id} = {series}.ewm(span={fast}, adjust=False).mean()",
            f"slow_ema_{safe_id} = {series}.ewm(span={slow}, adjust=False).mean()",
            f"df['{macd_col}'] = fast_ema_{safe_id} - slow_ema_{safe_id}",
            f"df['{signal_col}'] = df['{macd_col}'].ewm(span={signal}, adjust=False).mean()",
            f"df['{hist_col}'] = df['{macd_col}'] - df['{signal_col}']",
        ]

    def _volatility_bollinger(self, node, safe_id, series, params, *_):
        period = int(params.get("period", 20))
        std_mult = float(params.get("multiplier", params.get("stdMultiplier", 2)))
        mid = self._output_column(safe_id, 1)
        upper = self._output_column(safe_id, 2)
        lower = self._output_column(safe_id, 3)
        return [
            f"mid_{safe_id} = {series}.rolling(window={period}, min_periods=1).mean()",
            f"std_{safe_id} = {series}.rolling(window={period}, min_periods=1).std().fillna(0)",
            f"df['{mid}'] = mid_{safe_id}",
            f"df['{upper}'] = mid_{safe_id} + std_{safe_id} * {std_mult}",
            f"df['{lower}'] = mid_{safe_id} - std_{safe_id} * {std_mult}",
        ]

    def _volatility_atr(self, node, safe_id, series, params, data_edge):
        period = int(params.get("period", 14))
        tr_col = f"true_range_{safe_id}"
        atr_col = self._output_column(safe_id, 1)
        high_expr = self.resolve_series_expression(data_edge, "high")
        low_expr = self.resolve_series_expression(data_edge, "low")
        close_expr = self.resolve_series_expression(data_edge, "close")
        return [
            f"{tr_col} = pd.concat([",
            f"    {high_expr} - {low_expr},",
            f"    ({high_expr} - {close_expr}.shift(1)).abs(),",
            f"    ({low_expr} - {close_expr}.shift(1)).abs()",
            "], axis=1).max(axis=1)",
            f"df['{atr_col}'] = {tr_col}.rolling(window={period}, min_periods=1).mean().fillna(method='bfill')",
        ]

    def _volume_obv(self, node, safe_id, series, params, data_edge):
        volume_expr = self.resolve_series_expression(data_edge, "volume")
        obv_col = self._output_column(safe_id, 1)
        return [
            f"direction_{safe_id} = {series}.diff().apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)",
            f"df['{obv_col}'] = (direction_{safe_id} * {volume_expr}).cumsum().fillna(0)",
        ]

    def _volume_vwap(self, node, safe_id, series, params, data_edge):
        volume_expr = self.resolve_series_expression(data_edge, "volume")
        high_expr = self.resolve_series_expression(data_edge, "high")
        low_expr = self.resolve_series_expression(data_edge, "low")
        vwap_col = self._output_column(safe_id, 1)
        return [
            f"typical_price_{safe_id} = ({high_expr} + {low_expr} + {series}) / 3",
            f"cum_pv_{safe_id} = (typical_price_{safe_id} * {volume_expr}).cumsum()",
            f"cum_vol_{safe_id} = {volume_expr}.cumsum().replace(0, pd.NA)",
            f"df['{vwap_col}'] = (cum_pv_{safe_id} / cum_vol_{safe_id}).fillna(method='bfill')",
        ]

    def _oscillator_cci(self, node, safe_id, series, params, data_edge):
        period = int(params.get("period", 20))
        high_expr = self.resolve_series_expression(data_edge, "high")
        low_expr = self.resolve_series_expression(data_edge, "low")
        tp = f"tp_{safe_id}"
        cci_col = self._output_column(safe_id, 1)
        return [
            f"{tp} = ({high_expr} + {low_expr} + {series}) / 3",
            f"sma_{safe_id} = {tp}.rolling(window={period}, min_periods=1).mean()",
            f"mad_{safe_id} = ({tp} - sma_{safe_id}).abs().rolling(window={period}, min_periods=1).mean()",
            f"df['{cci_col}'] = ({tp} - sma_{safe_id}) / (0.015 * mad_{safe_id}.replace(0, pd.NA))",
            f"df['{cci_col}'] = df['{cci_col}'].fillna(0)",
        ]

    def _oscillator_mfi(self, node, safe_id, series, params, data_edge):
        period = int(params.get("period", 14))
        high_expr = self.resolve_series_expression(data_edge, "high")
        low_expr = self.resolve_series_expression(data_edge, "low")
        volume_expr = self.resolve_series_expression(data_edge, "volume")
        mfi_col = self._output_column(safe_id, 1)
        return [
            f"typical_price_{safe_id} = ({high_expr} + {low_expr} + {series}) / 3",
            f"money_flow_{safe_id} = typical_price_{safe_id} * {volume_expr}",
            f"positive_flow_{safe_id} = money_flow_{safe_id}.where(typical_price_{safe_id} > typical_price_{safe_id}.shift(1), 0)",
            f"negative_flow_{safe_id} = money_flow_{safe_id}.where(typical_price_{safe_id} < typical_price_{safe_id}.shift(1), 0)",
            f"pmf_{safe_id} = positive_flow_{safe_id}.rolling(window={period}, min_periods=1).sum()",
            f"nmf_{safe_id} = negative_flow_{safe_id}.rolling(window={period}, min_periods=1).sum()",
            f"money_ratio_{safe_id} = pmf_{safe_id} / nmf_{safe_id}.replace(0, pd.NA)",
            f"df['{mfi_col}'] = 100 - (100 / (1 + money_ratio_{safe_id}))",
            f"df['{mfi_col}'] = df['{mfi_col}'].clip(0, 100).fillna(50)",
        ]

    def _fallback_indicator(self, node, safe_id, series, params, *_):
        column = self._output_column(safe_id, 1)
        indicator = params.get("indicator", "UNKNOWN")
        return [
            f"# Fallback: copy source series for unsupported indicator {indicator}",
            f"df['{column}'] = {series}",
        ]

    def required_packages(self) -> List[str]:
        return ["pandas"]
