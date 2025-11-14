"""Tests for validation tooling, CLI, and telemetry (Phase 4)."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pandas as pd
import pytest

from app.telemetry import telemetry_recorder
from scripts.compile_workflow import (
    compile_workflow_file,
    run_simulation as cli_run_simulation,
    write_output as cli_write_output,
)
from validate_generated_code import validate_path
from workflow_compiler_updated import WorkflowCompiler

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def test_validate_tool_detects_syntax_error(tmp_path):
    faulty = tmp_path / "broken.py"
    faulty.write_text("def broken(:\n    pass\n")
    report = validate_path(faulty)
    assert not report.syntax_ok
    assert report.errors


def test_validate_tool_simulates_module(tmp_path):
    module = tmp_path / "strategy.py"
    module.write_text(
        """
import pandas as pd

def load_data():
    return pd.DataFrame(
        {
            "open": [1, 1.1, 1.2],
            "high": [1.2, 1.3, 1.4],
            "low": [0.9, 1.0, 1.1],
            "close": [1.1, 1.2, 1.3],
            "volume": [100, 110, 120],
        }
    )

def run_strategy():
    df = load_data().copy()
    df["decision_test"] = "HOLD"
    return df
"""
    )
    report = validate_path(module, simulate=True)
    assert report.syntax_ok
    assert report.simulation_rows == 500


def test_compile_cli_helpers(tmp_path):
    fixture_data = json.loads((FIXTURE_DIR / "core_workflow.json").read_text())
    for node in fixture_data["nodes"]:
        if node["type"] == "risk":
            node.setdefault("data", {}).setdefault("parameters", {})["model"] = "basic"
    fixture_tmp = tmp_path / "workflow.json"
    fixture_tmp.write_text(json.dumps(fixture_data))
    result = compile_workflow_file(fixture_tmp, "BACKTESTING")
    assert result["success"]
    out_file = tmp_path / "core_strategy.py"
    cli_write_output(result["code"], out_file)
    validation = validate_path(out_file)
    assert validation.syntax_ok
    rows = cli_run_simulation(result["code"])
    assert rows > 0


@pytest.mark.asyncio
async def test_telemetry_recorder_writes_json(tmp_path):
    telemetry_file = tmp_path / "telemetry.log"
    telemetry_recorder.configure(str(telemetry_file))
    compiler = WorkflowCompiler()
    workflow = json.loads((FIXTURE_DIR / "core_workflow.json").read_text())
    for node in workflow["nodes"]:
        if node["type"] == "risk":
            node.setdefault("data", {}).setdefault("parameters", {})["model"] = "basic"
    await compiler.compile_workflow(workflow["nodes"], workflow["edges"], strategy_name="telemetry-test")
    telemetry_recorder.flush()
    telemetry_recorder.configure(None)
    contents = telemetry_file.read_text().strip().splitlines()
    assert contents
    payload = json.loads(contents[-1])
    assert payload["event"] == "compiler_run"
    assert payload["success"] is True
