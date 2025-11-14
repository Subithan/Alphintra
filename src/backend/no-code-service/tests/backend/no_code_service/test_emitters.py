"""Tests covering emitter-specific behavior and snippet merging."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.backend.no_code_service import compiler_test_utils as utils


FIXTURE_PATH = Path(__file__).resolve().parents[0] / "fixtures" / "core_workflow.json"


@pytest.mark.parametrize(
    "mode, forbidden",
    [
        ("BACKTESTING", "def send_to_backtest_service"),
        ("LIVE_TRADING", "def publish_live_signals"),
        ("TRAINING", "def submit_training_payload"),
    ],
)
def test_emitters_skip_runtime_adapters(mode: str, forbidden: str):
    result = utils.compile_fixture_with_mode("core_workflow", mode)
    assert forbidden not in result["code"]
    assert result["metadata"]["emitter"] == mode.lower()


def test_research_emitter_adds_visualization_helper():
    module, generator = utils.load_generator()
    workflow = json.loads(FIXTURE_PATH.read_text())
    result = generator.compile_workflow(workflow, output_mode=module.OutputMode.RESEARCH)
    assert "visualize_signals" in result["code"]
    assert result["metadata"]["emitter"] == "research"
