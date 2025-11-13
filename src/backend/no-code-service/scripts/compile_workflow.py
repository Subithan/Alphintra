#!/usr/bin/env python3
"""CLI for compiling workflow JSON definitions."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from workflow_compiler_updated import WorkflowCompiler
from validate_generated_code import validate_path, generate_sample_ohlcv


def _load_workflow(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text())
    if "nodes" not in data or "edges" not in data:
        raise ValueError("Workflow JSON must include 'nodes' and 'edges' fields.")
    return data


def compile_workflow_file(
    input_path: Path,
    output_mode: str,
    strategy_name: Optional[str] = None,
) -> Dict[str, Any]:
    compiler = WorkflowCompiler()
    workflow = _load_workflow(input_path)
    strategy = strategy_name or workflow.get("name") or input_path.stem
    result = asyncio.run(
        compiler.compile_workflow(
            workflow["nodes"],
            workflow["edges"],
            strategy_name=strategy,
        )
    )
    if not result["success"]:
        raise RuntimeError(f"Compilation failed: {result['errors']}")
    return result


def write_output(code: str, destination: Path) -> None:
    destination.write_text(code.rstrip() + "\n")


def run_simulation(code: str) -> int:
    namespace: Dict[str, Any] = {}
    exec(code, namespace)
    sample_df = generate_sample_ohlcv()
    if "load_data" in namespace:
        namespace["load_data"] = lambda: sample_df.copy()  # type: ignore
    if "run_strategy" not in namespace:
        raise RuntimeError("Generated module lacks run_strategy()")
    df = namespace["run_strategy"]()
    return len(df)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile a workflow JSON definition into Python code.")
    parser.add_argument("input", type=Path, help="Path to the workflow JSON export.")
    parser.add_argument("--output-mode", default="BACKTESTING", choices=["BACKTESTING", "LIVE_TRADING", "TRAINING", "RESEARCH"], help="Target emitter.")
    parser.add_argument("--out", type=Path, help="Optional path to write the generated module.")
    parser.add_argument("--simulate", action="store_true", help="Dry-run the generated strategy after compilation.")
    parser.add_argument("--validate", action="store_true", help="Run syntax validation on the generated file.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = compile_workflow_file(args.input, args.output_mode)
    code = result["code"]
    if args.out:
        write_output(code, args.out)
        target_file = args.out
    else:
        target_file = args.input.with_suffix(".generated.py")
        write_output(code, target_file)

    if args.validate:
        validate_path(target_file, simulate=args.simulate)
    elif args.simulate:
        rows = run_simulation(code)
        print(f"✅ Dry run produced {rows} rows.")
    else:
        print(f"✅ Compilation succeeded ({result['code_type']}). Output: {target_file}")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via subprocess/CLI
    raise SystemExit(main())
