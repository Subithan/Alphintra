from __future__ import annotations

from pathlib import Path

import pytest

from tests.backend.no_code_service.compiler_test_utils import (
    canonical_ast,
    compile_fixture,
)

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "core_workflow",
        "custom_dataset_workflow",
        "advanced_analytics_workflow",
    ],
)
def test_fixture_ast_matches_golden(fixture_name: str) -> None:
    """Each representative workflow compiles to the stored AST."""
    code = compile_fixture(fixture_name)
    ast_dump = canonical_ast(code)
    golden_path = GOLDEN_DIR / f"{fixture_name}.ast"
    assert golden_path.exists(), f"Missing golden file for {fixture_name}"
    assert ast_dump.strip() == golden_path.read_text().strip()
