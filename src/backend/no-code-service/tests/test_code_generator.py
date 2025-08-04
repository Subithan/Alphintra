import json
import subprocess
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from code_generator import Generator  # noqa: E402

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_workflow(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("workflow_file", sorted(FIXTURE_DIR.glob("*.json")))
def test_generate_and_compile(workflow_file: Path):
    workflow = load_workflow(workflow_file)
    generator = Generator()
    result = generator.generate_strategy_code(workflow, name="TestStrategy")
    assert result["success"], (
        f"Generation failed for {workflow_file.name}: {result.get('errors')}"
    )

    output_dir = BASE_DIR / "generated"
    trainer = output_dir / "trainer.py"
    requirements = output_dir / "requirements.txt"

    assert trainer.is_file(), "trainer.py was not generated"
    assert requirements.is_file(), "requirements.txt was not generated"

    subprocess.run([sys.executable, "-m", "py_compile", str(trainer)], check=True)
    subprocess.run([sys.executable, "-m", "py_compile", str(requirements)], check=True)


def test_unknown_node_triggers_warning(caplog):
    """Ensure unknown node types are handled gracefully with a warning."""

    generator = Generator()
    workflow = {
        "nodes": [
            {"id": "data-1", "type": "dataSource", "data": {"parameters": {}}},
            {"id": "mystery-1", "type": "mystery"},
        ],
        "edges": [],
    }

    with caplog.at_level("WARNING"):
        result = generator.generate_strategy_code(workflow)

    assert result["success"], "Generation should succeed despite unknown node"
    assert "No handler registered for node type 'mystery'" in caplog.text
    assert "df['unknown_mystery" in result["code"]


def test_parse_workflow_builds_ir():
    """Ensure JSON is converted into a graph IR."""

    generator = Generator()
    workflow = {
        "nodes": [
            {"id": "n1", "type": "dataSource", "data": {"parameters": {}}},
            {"id": "n2", "type": "action", "data": {}},
        ],
        "edges": [{"source": "n1", "target": "n2"}],
    }

    ir = generator.parse_workflow(workflow)
    assert set(ir.nodes.keys()) == {"n1", "n2"}
    assert ir.edges and ir.edges[0].source == "n1" and ir.edges[0].target == "n2"
    assert ir.adjacency()["n1"] == ["n2"]


def test_handlers_add_dataframe_columns():
    workflow = {
        "nodes": [
            {"id": "ds1", "type": "dataSource", "data": {"parameters": {}}},
            {"id": "ti1", "type": "technicalIndicator", "data": {"parameters": {}}},
            {"id": "c1", "type": "condition", "data": {"parameters": {}}},
            {"id": "l1", "type": "logic", "data": {}},
            {"id": "a1", "type": "action", "data": {}},
            {"id": "r1", "type": "risk", "data": {}},
            {"id": "o1", "type": "output", "data": {}},
        ],
        "edges": [
            {"source": "ds1", "target": "ti1"},
            {"source": "ti1", "target": "c1"},
            {"source": "c1", "target": "l1"},
            {"source": "l1", "target": "a1"},
            {"source": "a1", "target": "r1"},
            {"source": "r1", "target": "o1"},
        ],
    }

    generator = Generator()
    result = generator.generate_strategy_code(workflow)

    code = result["code"]
    assert "df = pd.DataFrame" in code
    assert "df['feature_ti1']" in code
    assert "df['target_c1']" in code
    assert "df['logic_l1']" in code
    assert "df['action_a1']" in code
    assert "df['risk_r1']" in code
    assert "df['output_o1']" in code
