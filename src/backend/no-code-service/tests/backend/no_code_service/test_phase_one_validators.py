"""Unit tests for Phase 1 compiler infrastructure."""

from __future__ import annotations

import sys

import pytest

from tests.backend.no_code_service import SERVICE_ROOT

if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from execution_planner import ExecutionPlanner  # noqa: E402
from semantic_analyzer import SemanticAnalyzer  # noqa: E402
from workflow_schema import WorkflowSchemaValidator  # noqa: E402
from workflow_compiler_updated import WorkflowCompiler  # noqa: E402


def _base_nodes():
    return [
        {
            "id": "data-1",
            "type": "dataSource",
            "position": {"x": 0, "y": 0},
            "data": {"parameters": {"symbol": "AAPL", "timeframe": "1h"}},
        },
        {
            "id": "indicator-1",
            "type": "technicalIndicator",
            "position": {"x": 1, "y": 1},
            "data": {"parameters": {"indicator": "EMA", "period": 5}},
        },
        {
            "id": "action-1",
            "type": "action",
            "position": {"x": 2, "y": 2},
            "data": {"parameters": {"action": "buy"}},
        },
    ]


def test_schema_validator_rejects_empty_node_id():
    validator = WorkflowSchemaValidator()
    result = validator.validate(
        nodes=[
            {"id": "", "type": "dataSource", "position": {}, "data": {"parameters": {}}},
        ],
        edges=[],
    )
    assert not result.is_valid
    assert any("id" in error for error in result.errors)


def test_schema_validator_normalizes_edge_transformations():
    validator = WorkflowSchemaValidator()
    nodes = _base_nodes()[:2]
    edges = [
        {
            "id": "edge-1",
            "source": "data-1",
            "target": "indicator-1",
            "data": {"transformations": "log"},
        }
    ]
    result = validator.validate(nodes, edges)
    assert result.is_valid
    edge = result.edges[0]
    assert edge["data"]["transformations"] == ["log"]
    assert "sourceHandle" in edge and "targetHandle" in edge


def test_semantic_analyzer_detects_missing_data_source():
    compiler = WorkflowCompiler()
    analyzer = compiler.semantic_analyzer
    nodes = [
        {
            "id": "action-only",
            "type": "action",
            "position": {"x": 0, "y": 0},
            "data": {"parameters": {"action": "buy"}},
        }
    ]
    result = analyzer.analyze(nodes, [])
    assert not result.is_valid
    assert any("data source" in error.lower() for error in result.errors)


def test_semantic_analyzer_detects_type_mismatch():
    compiler = WorkflowCompiler()
    analyzer = compiler.semantic_analyzer
    nodes = _base_nodes()
    edges = [
        {
            "id": "edge-1",
            "source": "data-1",
            "target": "action-1",
            "sourceHandle": "data-output",
            "targetHandle": "signal-input",
            "data": {},
        }
    ]
    result = analyzer.analyze(nodes, edges)
    assert not result.is_valid
    assert any("type mismatch" in error.lower() for error in result.errors)


def test_execution_planner_orders_nodes_and_detects_cycles():
    planner = ExecutionPlanner()
    nodes = _base_nodes()
    edges = [
        {"source": "data-1", "target": "indicator-1"},
        {"source": "indicator-1", "target": "action-1"},
    ]
    plan = planner.plan(nodes, edges)
    assert plan.is_valid
    assert plan.ordered_nodes[0] == "data-1"
    assert len(plan.stages) >= 2

    cyclic_edges = edges + [{"source": "action-1", "target": "data-1"}]
    cyclic_plan = planner.plan(nodes, cyclic_edges)
    assert not cyclic_plan.is_valid
    assert any("circular" in error.lower() for error in cyclic_plan.errors)
