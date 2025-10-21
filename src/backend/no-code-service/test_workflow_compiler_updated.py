"""Unit tests for the updated workflow compiler."""

import asyncio
import json
from pathlib import Path

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
    assert result["code"].strip()

    requirements = result["requirements"]
    assert "pandas" in requirements

    expected_types = {node["type"] for node in workflow_definition["nodes"]}
    assert expected_types.issubset(set(compiler.component_registry.keys()))

    summary = result["validation"]["summary"]
    assert summary["total_nodes"] == len(workflow_definition["nodes"])
    assert summary["total_edges"] == len(workflow_definition["edges"])
