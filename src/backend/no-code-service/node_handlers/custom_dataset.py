"""Handler for custom dataset nodes."""

from typing import List

from ir import Node
from .base import NodeHandler


class CustomDatasetHandler(NodeHandler):
    node_type = "customDataset"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        path = params.get("fileName") or params.get("path") or "dataset.csv"
        fmt = str(params.get("format") or path.split(".")[-1]).lower()
        date_column = params.get("dateColumn") or params.get("indexColumn")
        value_columns = params.get("valueColumns")
        fill_method = params.get("fillMethod", "ffill")
        dropna = bool(params.get("dropMissingRows", False))

        lines = [f"# Load custom dataset from {path}"]
        loader = "pd.read_csv"
        if fmt in {"parquet", "pq"}:
            loader = "pd.read_parquet"
        elif fmt in {"json"}:
            loader = "pd.read_json"

        lines.append(f"df = {loader}('{path}')")
        lines.append("df.columns = [str(col).strip() for col in df.columns]")
        if date_column:
            lines.extend([
                f"df['{date_column}'] = pd.to_datetime(df['{date_column}'], errors='coerce')",
                f"df = df.set_index('{date_column}').sort_index()",
            ])
        if value_columns:
            cols = ", ".join(repr(col) for col in value_columns)
            lines.append(f"value_columns = [{cols}]")
            lines.append("df = df[value_columns]")
        lines.append("df = df.apply(pd.to_numeric, errors='ignore')")

        if dropna:
            lines.append("df = df.dropna()")
        elif fill_method == "bfill":
            lines.append("df = df.fillna(method='bfill')")
        elif fill_method == "zero":
            lines.append("df = df.fillna(0)")
        else:
            lines.append("df = df.fillna(method='ffill').fillna(method='bfill')")

        if date_column:
            lines.append("df.index = df.index.tz_localize('UTC', nonexistent='shift_forward', ambiguous='NaT')")

        return "\n".join(lines)

    def required_packages(self) -> List[str]:
        return ["pandas"]
