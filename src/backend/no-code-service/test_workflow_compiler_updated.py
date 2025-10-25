"""Unit tests for the updated workflow compiler."""

import asyncio
import json
from pathlib import Path
import types

import pytest

pd = pytest.importorskip("pandas")

from workflow_compiler_updated import WorkflowCompiler


def test_compiler_handles_console_nodes() -> None:
    """The compiler should accept all console node types and emit code."""

    compiler = WorkflowCompiler()
    workflow_path = Path(__file__).with_name("my_test_workflow.json")
    workflow_definition = json.loads(workflow_path.read_text())

    result = asyncio.run(
        compiler.compile_workflow(
            workflow_definition["nodes"],
            workflow_definition["edges"],
            strategy_name="Console Workflow Test",
        )
    )

    assert result["validation"]["is_valid"], result["validation"]["errors"]
    assert result["success"], result["errors"]
    code = result["code"].strip()
    assert code

    strategy_module = types.ModuleType("generated_strategy")
    exec(code, strategy_module.__dict__)

    expected_functions = [
        "load_data",
        "compute_indicators",
        "evaluate_conditions",
        "combine_logic",
        "apply_risk_controls",
        "generate_trading_decisions",
        "run_strategy",
    ]

    for name in expected_functions:
        assert hasattr(strategy_module, name), f"Missing function: {name}"
        assert callable(getattr(strategy_module, name)), f"{name} should be callable"

    df = strategy_module.run_strategy()
    assert isinstance(df, pd.DataFrame)

    decision_columns = [col for col in df.columns if col.startswith("decision_")]
    assert decision_columns, "Generated dataframe should include decision columns"

    decision_values = set()
    for col in decision_columns:
        decision_values.update(df[col].unique())

    assert any(value in {"BUY", "SELL"} for value in decision_values), "Expected BUY/SELL markers"

    requirements = result["requirements"]
    assert "pandas" in requirements

    expected_types = {node["type"] for node in workflow_definition["nodes"]}
    assert expected_types.issubset(set(compiler.component_registry.keys()))

    summary = result["validation"]["summary"]
    assert summary["total_nodes"] == len(workflow_definition["nodes"])
    assert summary["total_edges"] == len(workflow_definition["edges"])
