"""Handler for data source nodes."""

from __future__ import annotations

from typing import List

from ir import Node
from .base import NodeHandler


class DataSourceHandler(NodeHandler):
    node_type = "dataSource"

    def handle(self, node: Node, generator) -> str:  # noqa: D401 - see base class
        params = node.data.get("parameters", {})
        symbol = params.get("symbol", "AAPL")
        timeframe = params.get("timeframe", "1h")
        bars = int(params.get("bars", params.get("lookback", 100)))
        source_type = params.get("dataSource", "system")
        asset_class = params.get("assetClass", "stocks")
        timezone = params.get("timezone", "UTC")
        missing_strategy = str(params.get("missingStrategy", "ffill")).lower()
        enforce_positive = bool(params.get("enforcePositivePrices", True))
        inline_data = params.get("inlineData") or params.get("data")

        lines = [
            f"# Load {asset_class} OHLCV data for {symbol} ({timeframe}) via {source_type}",
        ]

        if inline_data:
            lines.extend([
                f"df = pd.DataFrame({repr(inline_data)})",
                "df = df.rename(columns=str.lower)",
                "required_cols = ['open', 'high', 'low', 'close', 'volume']",
                "missing = [col for col in required_cols if col not in df.columns]",
                "if missing:",
                "    raise ValueError(f'Missing OHLCV columns: {missing}')",
                "df = df[required_cols]",
            ])
        else:
            freq_map = {
                "1m": "1min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "1h": "1H",
                "4h": "4H",
                "1d": "1D",
            }
            freq = freq_map.get(str(timeframe).lower(), timeframe.upper())
            lines.extend([
                f"index = pd.date_range(end=pd.Timestamp.utcnow(), periods={bars}, freq='{freq}')",
                "base = pd.Series(range(len(index)), index=index, dtype='float64')",
                "df = pd.DataFrame({",
                "    'open': 100 + base * 0.01,",
                "    'high': 100 + base * 0.015,",
                "    'low': 100 + base * 0.005,",
                "    'close': 100 + base * 0.01,",
                "    'volume': pd.Series([1_000 + i * 10 for i in range(len(index))], index=index, dtype='float64')",
                "})",
                "df.index.name = 'timestamp'",
                "df = df.tz_localize('UTC', nonexistent='shift_forward', ambiguous='NaT').tz_convert('UTC')",
            ])

        lines.extend([
            "df = df.sort_index()",
            "df = df.loc[~df.index.duplicated(keep='last')]",
            f"df = df.tz_convert('{timezone}') if df.index.tz else df.tz_localize('{timezone}')",
            "numeric_cols = ['open', 'high', 'low', 'close', 'volume']",
            "for col in numeric_cols:",
            "    if col not in df:",
            "        df[col] = pd.NA",
        ])

        if missing_strategy == "drop":
            lines.append("df = df.dropna()")
        elif missing_strategy == "zero":
            lines.append("df = df.fillna(0)")
        else:
            lines.append("df = df.fillna(method='ffill').fillna(method='bfill')")

        if enforce_positive:
            lines.extend([
                "for col in ['open', 'high', 'low', 'close']:",
                "    df[col] = df[col].clip(lower=0.01)",
            ])

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
