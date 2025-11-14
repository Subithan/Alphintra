"""Shared helpers for compiler regression tests."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Tuple, Dict, Any

from tests.backend.no_code_service import SERVICE_ROOT

MODULE_DIR = SERVICE_ROOT
FIXTURE_DIR = SERVICE_ROOT / "tests" / "backend" / "no_code_service" / "fixtures"
_GENERATOR_CACHE: Tuple[object, object] | None = None


def _load_generator() -> Tuple[object, object]:
    """Lazy-load the enhanced code generator module and instance."""
    global _GENERATOR_CACHE
    if _GENERATOR_CACHE:
        return _GENERATOR_CACHE

    sys.path.insert(0, str(MODULE_DIR))
    module_path = MODULE_DIR / "enhanced_code_generator.py"
    spec = importlib.util.spec_from_file_location("enhanced_code_generator", module_path)
    if not spec or not spec.loader:
        raise RuntimeError("Unable to load enhanced_code_generator module")

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    generator = module.EnhancedCodeGenerator()
    _GENERATOR_CACHE = (module, generator)
    return _GENERATOR_CACHE


def compile_fixture(fixture_name: str) -> str:
    """Compile a workflow fixture and return generated Python code."""
    module, generator = _load_generator()
    fixture_path = FIXTURE_DIR / f"{fixture_name}.json"
    workflow = json.loads(fixture_path.read_text())
    result = generator.compile_workflow(workflow, output_mode=module.OutputMode.BACKTESTING)
    assert result.get("success"), f"Compilation failed for {fixture_name}: {result.get('errors')}"
    return result["code"]


def compile_fixture_with_mode(fixture_name: str, mode: str) -> Dict[str, Any]:
    """Compile a fixture under a specific OutputMode."""
    module, generator = _load_generator()
    fixture_path = FIXTURE_DIR / f"{fixture_name}.json"
    workflow = json.loads(fixture_path.read_text())
    target_mode = module.OutputMode[mode]
    result = generator.compile_workflow(workflow, output_mode=target_mode)
    assert result.get("success"), f"Compilation failed for {fixture_name} ({mode}): {result.get('errors')}"
    return result


def load_generator():
    """Expose the generator and module for advanced tests."""
    return _load_generator()


def canonical_ast(code: str) -> str:
    """Return a deterministic AST dump for comparison."""
    normalized = re.sub(
        r"(Generated at:\s+)[^\n]+",
        r"\1<timestamp>",
        code,
    )
    tree = ast.parse(normalized)
    dump = ast.dump(tree, include_attributes=False)
    return dump.replace(", type_params=[]", "")
