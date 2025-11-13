#!/usr/bin/env python3
"""
Validation and simulation utilities for generated strategy modules.

Used as both a CLI (`python validate_generated_code.py --file generated.py`)
and as an importable helper within the compiler test suite.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import io
import os
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd


@dataclass
class ValidationReport:
    filename: str
    syntax_ok: bool
    metrics: Optional[dict] = None
    simulation_rows: Optional[int] = None
    errors: List[str] = None


def _load_code(path: Path) -> str:
    with path.open("r") as handle:
        return handle.read()


def validate_python_syntax(path: Path) -> ValidationReport:
    """Validate that generated code parses and compiles."""

    report = ValidationReport(filename=str(path), syntax_ok=False, metrics={}, errors=[])
    if not path.exists():
        report.errors.append(f"File {path} not found")
        return report

    code = _load_code(path)
    try:
        tree = ast.parse(code)
        compile(code, str(path), "exec")
        report.syntax_ok = True
    except SyntaxError as exc:  # pragma: no cover - depends on codegen output
        report.errors.append(f"Syntax error at line {exc.lineno}: {exc.msg}")
        return report

    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    lines = code.splitlines()
    comments = sum(1 for line in lines if line.strip().startswith("#"))
    report.metrics = {
        "lines": len(lines),
        "functions": len(functions),
        "imports": len(imports),
        "comment_ratio": round(comments / max(1, len(lines)) * 100, 2),
    }
    return report


def generate_sample_ohlcv(rows: int = 500) -> pd.DataFrame:
    rng = pd.Series(range(rows), dtype="float64")
    index = pd.date_range(end=pd.Timestamp.utcnow(), periods=rows, freq="1h")
    df = pd.DataFrame(
        {
            "open": 100 + rng * 0.01,
            "high": 100 + rng * 0.015,
            "low": 100 + rng * 0.005,
            "close": 100 + rng * 0.01,
            "volume": 1_000 + rng * 10,
        },
        index=index,
    )
    df.index.name = "timestamp"
    return df


def _load_module_from_path(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def dry_run_strategy(path: Path, rows: int = 500) -> int:
    """Execute run_strategy inside generated module with sample data."""

    module = _load_module_from_path(path)
    sample_df = generate_sample_ohlcv(rows)
    if hasattr(module, "load_data"):
        module.load_data = lambda: sample_df.copy()  # type: ignore[attr-defined]
    if not hasattr(module, "run_strategy"):
        raise RuntimeError("Generated module does not expose run_strategy()")
    result = module.run_strategy()
    if not isinstance(result, pd.DataFrame):
        raise RuntimeError("run_strategy() must return a pandas DataFrame")
    return len(result)


def validate_path(path: Path, simulate: bool = False) -> ValidationReport:
    report = validate_python_syntax(path)
    if report.syntax_ok and simulate:
        try:
            report.simulation_rows = dry_run_strategy(path)
        except Exception as exc:  # pragma: no cover - simulation failure
            report.errors = report.errors or []
            report.errors.append(str(exc))
            report.simulation_rows = 0
    return report


def validate_directory(directory: Path, simulate: bool = False) -> List[ValidationReport]:
    reports: List[ValidationReport] = []
    for path in directory.glob("*.py"):
        if path.name.startswith(("generated_", "test_", "simple_")):
            reports.append(validate_path(path, simulate=simulate))
    return reports


def format_report(report: ValidationReport) -> str:
    body = [f"🔍 {report.filename}", f"   Syntax OK: {'yes' if report.syntax_ok else 'no'}"]
    if report.metrics:
        body.append(
            "   Metrics: "
            + ", ".join(f"{key}={value}" for key, value in report.metrics.items())
        )
    if report.simulation_rows is not None:
        body.append(f"   Simulation rows: {report.simulation_rows}")
    if report.errors:
        body.extend(f"   ❌ {error}" for error in report.errors)
    return "\n".join(body)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate compiled no-code strategies.")
    parser.add_argument(
        "--file",
        type=Path,
        help="Specific generated Python file to validate.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("."),
        help="Directory containing generated artifacts (default: current).",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run dry-run simulation using synthetic OHLCV data.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    reports = []
    if args.file:
        reports.append(validate_path(args.file, simulate=args.simulate))
    else:
        reports.extend(validate_directory(args.dir, simulate=args.simulate))

    if not reports:
        print("❌ No generated files found.")
        return 1

    all_ok = True
    for report in reports:
        print(format_report(report))
        print()
        all_ok = all_ok and report.syntax_ok and (not report.errors)
    return 0 if all_ok else 2


if __name__ == "__main__":  # pragma: no cover - exercised via CLI
    sys.exit(main())
