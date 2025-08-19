import pytest
from app.utils.workflow_analyzer import WorkflowAnalyzer

@pytest.fixture
def sample_workflow():
    """Provides a sample workflow for testing."""
    return {
        "nodes": [
            {"id": "data-1", "type": "dataSource", "data": {"parameters": {"symbol": "BTCUSDT"}}},
            {"id": "sma-1", "type": "technicalIndicator", "data": {"parameters": {"indicator": "SMA", "period": 20}}},
            {"id": "ema-1", "type": "technicalIndicator", "data": {"parameters": {"indicator": "EMA", "period": 50}}},
            {"id": "condition-1", "type": "condition", "data": {"parameters": {"threshold": 30, "operator": "<"}}},
            {"id": "action-1", "type": "action", "data": {"parameters": {"signal": "buy", "quantity": 100}}}
        ],
        "edges": [
            {"source": "data-1", "target": "sma-1"},
            {"source": "data-1", "target": "ema-1"},
            {"source": "sma-1", "target": "condition-1"},
            {"source": "ema-1", "target": "condition-1"}
        ]
    }

def test_workflow_analyzer_initialization(sample_workflow):
    """Tests that the WorkflowAnalyzer initializes correctly."""
    analyzer = WorkflowAnalyzer(sample_workflow)
    assert analyzer.workflow == sample_workflow
    assert len(analyzer.nodes) == 5
    assert len(analyzer.edges) == 4
    assert "data-1" in analyzer.nodes

def test_get_node_by_id(sample_workflow):
    """Tests retrieving a node by its ID."""
    analyzer = WorkflowAnalyzer(sample_workflow)
    node = analyzer.get_node_by_id("sma-1")
    assert node is not None
    assert node['id'] == "sma-1"
    assert node['type'] == "technicalIndicator"

    non_existent_node = analyzer.get_node_by_id("non-existent")
    assert non_existent_node is None

def test_get_node_type(sample_workflow):
    """Tests retrieving the type of a node."""
    analyzer = WorkflowAnalyzer(sample_workflow)
    assert analyzer.get_node_type("data-1") == "dataSource"
    assert analyzer.get_node_type("sma-1") == "technicalIndicator"
    assert analyzer.get_node_type("non-existent-node") == ''

def test_get_technical_indicators(sample_workflow):
    """Tests extracting all technical indicator nodes."""
    analyzer = WorkflowAnalyzer(sample_workflow)
    indicators = analyzer.get_technical_indicators()
    assert len(indicators) == 2
    indicator_ids = {ind['id'] for ind in indicators}
    assert "sma-1" in indicator_ids
    assert "ema-1" in indicator_ids

def test_get_data_sources(sample_workflow):
    """Tests extracting all data source nodes."""
    analyzer = WorkflowAnalyzer(sample_workflow)
    sources = analyzer.get_data_sources()
    assert len(sources) == 1
    assert sources[0]['id'] == 'data-1'

def test_empty_workflow(sample_workflow):
    """Tests handling of an empty workflow."""
    empty_workflow = {"nodes": [], "edges": []}
    analyzer = WorkflowAnalyzer(empty_workflow)
    assert len(analyzer.nodes) == 0
    assert len(analyzer.edges) == 0
    assert analyzer.get_technical_indicators() == []
    assert analyzer.get_data_sources() == []

def test_workflow_with_no_indicators(sample_workflow):
    """Tests a workflow without any technical indicators."""
    workflow = {
        "nodes": [
            {"id": "data-1", "type": "dataSource", "data": {"parameters": {"symbol": "BTCUSDT"}}},
            {"id": "action-1", "type": "action", "data": {"parameters": {"signal": "buy"}}}
        ],
        "edges": []
    }
    analyzer = WorkflowAnalyzer(workflow)
    assert analyzer.get_technical_indicators() == []
    assert len(analyzer.get_data_sources()) == 1
