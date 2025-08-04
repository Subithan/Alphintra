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
