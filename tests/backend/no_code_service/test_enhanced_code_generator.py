"""Regression tests for the enhanced no-code code generator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


def load_enhanced_code_generator():
    """Load the ``enhanced_code_generator`` module from its file path."""

    project_root = Path(__file__).resolve().parents[3]

    module_path = (
        project_root
        / "src"
        / "backend"
        / "no-code-service"
        / "enhanced_code_generator.py"
    )

    spec = importlib.util.spec_from_file_location(
        "enhanced_code_generator", module_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader, "Unable to load enhanced_code_generator module"

    module_dir = str(module_path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module, project_root


def test_risk_nodes_do_not_emit_unknown_type_warning(tmp_path):
    module, project_root = load_enhanced_code_generator()
    generator = module.EnhancedCodeGenerator()

    workflow_path = (
        project_root
        / "src"
        / "backend"
        / "no-code-service"
        / "my_test_workflow.json"
    )

    workflow = json.loads(workflow_path.read_text())

    # Simulate the UI emitting the modern "risk" node type identifier.
    for node in workflow["nodes"]:
        if node["type"] == "riskManagement":
            node["type"] = "risk"

    result = generator.compile_workflow(
        workflow, output_mode=module.OutputMode.BACKTESTING
    )

    assert result["success"], "Compilation should succeed"
    assert not any(
        warning["type"] == "unknown_node_type" for warning in result["warnings"]
    ), "Risk nodes should be recognised and not flagged as unknown"

    # The generated code should include the risk output column from the handler.
    assert "risk_risk_mgmt" in result["code"]
