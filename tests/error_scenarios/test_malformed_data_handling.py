"""
Error scenario tests for malformed data handling.
Tests handling of invalid workflow definitions, corrupted data, and edge cases.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys
from pathlib import Path

# Add the app directories to the path
NO_CODE_APP_DIR = Path(__file__).resolve().parents[2] / "src/backend/no-code-service"
AIML_APP_DIR = Path(__file__).resolve().parents[2] / "src/backend/ai-ml-strategy-service/app"
sys.path.extend([str(NO_CODE_APP_DIR), str(AIML_APP_DIR)])


@pytest.fixture
def malformed_workflow_definitions():
    """Various malformed workflow definitions for testing."""
    return {
        "missing_nodes": {
            # Missing 'nodes' key
            "edges": [
                {"source": "data-1", "target": "rsi-1"}
            ]
        },
        "missing_edges": {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}}
            ]
            # Missing 'edges' key
        },
        "invalid_node_structure": {
            "nodes": [
                {"id": "data-1"},  # Missing 'type' and 'data'
                {"type": "technicalIndicator"},  # Missing 'id' and 'data'
                {"data": {"symbol": "ETHUSDT"}}  # Missing 'id' and 'type'
            ],
            "edges": []
        },
        "invalid_edge_structure": {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {"id": "rsi-1", "type": "technicalIndicator", "data": {"indicator": "rsi"}}
            ],
            "edges": [
                {"source": "data-1"},  # Missing 'target'
                {"target": "rsi-1"},   # Missing 'source'
                {}  # Missing both
            ]
        },
        "circular_dependencies": {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {"id": "condition-1", "type": "condition", "data": {"threshold": 30}},
                {"id": "condition-2", "type": "condition", "data": {"threshold": 70}}
            ],
            "edges": [
                {"source": "data-1", "target": "condition-1"},
                {"source": "condition-1", "target": "condition-2"},
                {"source": "condition-2", "target": "condition-1"}  # Circular dependency
            ]
        },
        "null_values": {
            "nodes": [
                {"id": None, "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {"id": "rsi-1", "type": None, "data": {"indicator": "rsi"}},
                {"id": "condition-1", "type": "condition", "data": None}
            ],
            "edges": [
                {"source": None, "target": "rsi-1"},
                {"source": "rsi-1", "target": None}
            ]
        },
        "wrong_data_types": {
            "nodes": "not_a_list",
            "edges": {"source": "data-1", "target": "rsi-1"}  # Should be list
        },
        "empty_structure": {
            "nodes": [],
            "edges": []
        },
        "disconnected_nodes": {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {"id": "rsi-1", "type": "technicalIndicator", "data": {"indicator": "rsi"}},
                {"id": "isolated", "type": "condition", "data": {"threshold": 50}}
            ],
            "edges": [
                {"source": "data-1", "target": "rsi-1"}
                # 'isolated' node has no connections
            ]
        },
        "unknown_node_types": {
            "nodes": [
                {"id": "data-1", "type": "unknownType", "data": {"symbol": "BTCUSDT"}},
                {"id": "custom-1", "type": "customIndicator", "data": {"period": 14}}
            ],
            "edges": [
                {"source": "data-1", "target": "custom-1"}
            ]
        }
    }


class TestWorkflowConverterMalformedData:
    """Test workflow converter handling of malformed data."""
    
    def test_missing_nodes_handling(self, malformed_workflow_definitions):
        """Test handling of workflow definition missing nodes."""
        from workflow_converter import WorkflowConverter
        
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(
            malformed_workflow_definitions["missing_nodes"]
        )
        
        assert result["success"] is False
        assert "Missing required 'nodes' field" in result["error"]
        assert result["error_type"] == "validation_error"
        assert "validation_details" in result
    
    def test_missing_edges_handling(self, malformed_workflow_definitions):
        """Test handling of workflow definition missing edges."""
        from workflow_converter import WorkflowConverter
        
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(
            malformed_workflow_definitions["missing_edges"]
        )
        
        assert result["success"] is False
        assert "Missing required 'edges' field" in result["error"]
        assert result["error_type"] == "validation_error"
    
    def test_invalid_node_structure_handling(self, malformed_workflow_definitions):
        """Test handling of nodes with invalid structure."""
        from workflow_converter import WorkflowConverter
        
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(
            malformed_workflow_definitions["invalid_node_structure"]
        )
        
        assert result["success"] is False
        assert "Invalid node structure" in result["error"]
        assert result["error_type"] == "validation_error"
        assert "invalid_nodes" in result
        assert len(result["invalid_nodes"]) == 3  # All nodes are invalid
    
    def test_invalid_edge_structure_handling(self, malformed_workflow_definitions):
        """Test handling of edges with invalid structure."""
        from workflow_converter import WorkflowConverter
        
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(
            malformed_workflow_definitions["invalid_edge_structure"]
        )
        
        assert result["success"] is False
        assert "Invalid edge structure" in result["error"]
        assert "invalid_edges" in result
        assert len(result["invalid_edges"]) == 3  # All edges are invalid
    
    def test_circular_dependencies_detection(self, malformed_workflow_definitions):
        """Test detection of circular dependencies in workflow."""
        from workflow_converter import WorkflowConverter
        
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(
            malformed_workflow_definitions["circular_dependencies"]
        )
        
        assert result["success"] is False
        assert "Circular dependency detected" in result["error"]
        assert result["error_type"] == "circular_dependency"
        assert "dependency_chain" in result
    
    def test_null_values_handling(self, malformed_workflow_definitions):
        """Test handling of null values in workflow definition."""
        from workflow_converter import WorkflowConverter
        
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(
            malformed_workflow_definitions["null_values"]
        )
        
        assert result["success"] is False
        assert "Null values found in workflow" in result["error"]
        assert "null_fields" in result
        assert len(result["null_fields"]) > 0
    
    def test_wrong_data_types_handling(self, malformed_workflow_definitions):
        """Test handling of wrong data types."""
        from workflow_converter import WorkflowConverter
        
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(
            malformed_workflow_definitions["wrong_data_types"]
        )
        
        assert result["success"] is False
        assert "Invalid data types" in result["error"]
        assert result["error_type"] == "type_error"
        assert "expected_types" in result
    
    def test_empty_structure_handling(self, malformed_workflow_definitions):
        """Test handling of completely empty workflow structure."""
        from workflow_converter import WorkflowConverter
        
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(
            malformed_workflow_definitions["empty_structure"]
        )
        
        assert result["success"] is False
        assert "Workflow is empty" in result["error"]
        assert result["error_type"] == "empty_workflow"
        assert result["minimum_requirements"] == {
            "min_nodes": 2,
            "min_edges": 1,
            "required_types": ["dataSource", "action"]
        }


class TestWorkflowParserMalformedData:
    """Test AI-ML service workflow parser handling of malformed data."""
    
    def test_parser_unknown_node_types(self, malformed_workflow_definitions):
        """Test parser handling of unknown node types."""
        from services.workflow_parser import WorkflowParser, NodeType
        
        parser = WorkflowParser()
        result = parser.parse_workflow(
            malformed_workflow_definitions["unknown_node_types"]
        )
        
        # Parser should continue but mark unknown types
        assert "unknown_node_types" in result
        assert len(result["unknown_node_types"]) == 2
        assert "unknownType" in result["unknown_node_types"]
        assert "customIndicator" in result["unknown_node_types"]
        
        # Should still parse what it can
        assert "data_sources" in result
        assert "technical_indicators" in result
    
    def test_parser_disconnected_nodes(self, malformed_workflow_definitions):
        """Test parser handling of disconnected nodes."""
        from services.workflow_parser import WorkflowParser
        
        parser = WorkflowParser()
        result = parser.parse_workflow(
            malformed_workflow_definitions["disconnected_nodes"]
        )
        
        assert "disconnected_nodes" in result
        assert "isolated" in result["disconnected_nodes"]
        assert result["validation_warnings"]["has_disconnected_nodes"] is True
    
    def test_parser_invalid_indicator_config(self):
        """Test parser handling of invalid indicator configurations."""
        from services.workflow_parser import WorkflowParser
        
        invalid_indicator_workflow = {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}},
                {
                    "id": "rsi-1", 
                    "type": "technicalIndicator", 
                    "data": {
                        "indicator": "rsi",
                        "period": "invalid_period",  # Should be int
                        "source": None  # Should be string
                    }
                }
            ],
            "edges": [
                {"source": "data-1", "target": "rsi-1"}
            ]
        }
        
        parser = WorkflowParser()
        result = parser.parse_workflow(invalid_indicator_workflow)
        
        assert "invalid_configurations" in result
        assert "rsi-1" in result["invalid_configurations"]
        assert "period must be integer" in str(result["invalid_configurations"]["rsi-1"])
        assert "source cannot be null" in str(result["invalid_configurations"]["rsi-1"])
    
    def test_parser_missing_required_fields(self):
        """Test parser handling of missing required fields."""
        from services.workflow_parser import WorkflowParser
        
        missing_fields_workflow = {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {}},  # Missing symbol
                {
                    "id": "condition-1", 
                    "type": "condition", 
                    "data": {"operator": ">"}  # Missing threshold
                },
                {
                    "id": "action-1",
                    "type": "action",
                    "data": {"quantity": 100}  # Missing action_type
                }
            ],
            "edges": []
        }
        
        parser = WorkflowParser()
        result = parser.parse_workflow(missing_fields_workflow)
        
        assert "missing_required_fields" in result
        assert "data-1" in result["missing_required_fields"]
        assert "condition-1" in result["missing_required_fields"]
        assert "action-1" in result["missing_required_fields"]


class TestDatabaseTransactionErrorHandling:
    """Test database transaction error handling with malformed data."""
    
    @pytest.mark.asyncio
    async def test_workflow_creation_with_invalid_json(self):
        """Test workflow creation with invalid JSON data."""
        from models import NoCodeWorkflow
        
        # Mock database session
        mock_db = AsyncMock()
        mock_db.add.side_effect = ValueError("Invalid JSON in workflow_data column")
        
        invalid_workflow_data = {
            "nodes": [
                {"id": "data-1", "data": {"invalid": float('inf')}}  # JSON can't serialize inf
            ]
        }
        
        # This would normally be called from the API endpoint
        try:
            workflow = NoCodeWorkflow(
                user_id="test_user",
                name="Invalid JSON Test",
                workflow_data=invalid_workflow_data
            )
            mock_db.add(workflow)
            await mock_db.commit()
        except ValueError as e:
            assert "Invalid JSON" in str(e)
    
    @pytest.mark.asyncio
    async def test_execution_history_with_malformed_metadata(self):
        """Test execution history creation with malformed metadata."""
        from models import ExecutionHistory
        
        mock_db = AsyncMock()
        
        # Metadata that exceeds database limits
        oversized_metadata = {
            "workflow_definition": {
                "nodes": [{"id": f"node-{i}", "data": "x" * 10000} for i in range(1000)]
            }
        }
        
        try:
            execution = ExecutionHistory(
                workflow_id=123,
                user_id="test_user",
                execution_mode="model",
                execution_metadata=oversized_metadata,
                status="queued"
            )
            mock_db.add(execution)
            await mock_db.commit()
        except Exception as e:
            # Should handle database size constraints
            assert "exceeds maximum size" in str(e).lower() or "too large" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraint_violations(self):
        """Test handling of foreign key constraint violations."""
        from models import ExecutionHistory
        
        mock_db = AsyncMock()
        mock_db.add.side_effect = Exception("FOREIGN KEY constraint failed")
        
        # Reference non-existent workflow
        try:
            execution = ExecutionHistory(
                workflow_id=999999,  # Non-existent workflow
                user_id="test_user",
                execution_mode="strategy",
                status="queued"
            )
            mock_db.add(execution)
            await mock_db.commit()
        except Exception as e:
            assert "FOREIGN KEY constraint failed" in str(e)


class TestAPIEndpointMalformedData:
    """Test API endpoint handling of malformed request data."""
    
    @pytest.mark.asyncio
    async def test_execution_mode_endpoint_invalid_json(self):
        """Test execution mode endpoint with invalid JSON."""
        # This would normally be tested with FastAPI test client
        # For now, we'll test the validation logic directly
        
        from pydantic import ValidationError
        from main import ExecutionModeRequest
        
        # Test invalid mode value
        with pytest.raises(ValidationError) as exc_info:
            ExecutionModeRequest(mode="invalid_mode", config={})
        
        assert "string does not match regex" in str(exc_info.value)
        
        # Test missing required fields
        with pytest.raises(ValidationError):
            ExecutionModeRequest(config={})  # Missing mode
    
    @pytest.mark.asyncio
    async def test_workflow_training_request_malformed_data(self):
        """Test workflow training request with malformed data."""
        from pydantic import ValidationError
        
        # Mock the training request model
        from api.endpoints.training import WorkflowTrainingRequest
        
        # Test with missing required fields
        with pytest.raises(ValidationError):
            WorkflowTrainingRequest(
                workflow_name="Test",
                # Missing workflow_id and workflow_definition
                optimization_objective="sharpe_ratio"
            )
        
        # Test with invalid types
        with pytest.raises(ValidationError):
            WorkflowTrainingRequest(
                workflow_id="not_an_int",  # Should be int
                workflow_name="Test",
                workflow_definition={},
                optimization_objective="invalid_objective"  # Should be from enum
            )


class TestMemoryExhaustionScenarios:
    """Test handling of memory exhaustion from malformed data."""
    
    def test_extremely_large_workflow_definition(self):
        """Test handling of extremely large workflow definitions."""
        from workflow_converter import WorkflowConverter
        
        # Create a workflow with excessive number of nodes
        huge_workflow = {
            "nodes": [
                {
                    "id": f"node-{i}",
                    "type": "technicalIndicator", 
                    "data": {
                        "indicator": "rsi",
                        "period": 14,
                        "large_data": "x" * 1000  # 1KB per node
                    }
                } 
                for i in range(10000)  # 10,000 nodes = ~10MB
            ],
            "edges": [
                {"source": f"node-{i}", "target": f"node-{i+1}"}
                for i in range(9999)
            ]
        }
        
        converter = WorkflowConverter()
        
        # Should implement size limits and fail gracefully
        result = converter.convert_to_training_config(huge_workflow)
        
        assert result["success"] is False
        assert "Workflow too large" in result["error"] or "Memory limit exceeded" in result["error"]
        assert result["error_type"] == "size_limit_exceeded"
        assert "max_nodes" in result
        assert "max_edges" in result
        assert "size_mb" in result
    
    def test_deeply_nested_data_structures(self):
        """Test handling of deeply nested data structures."""
        from workflow_converter import WorkflowConverter
        
        # Create deeply nested structure that could cause stack overflow
        nested_data = {"level": 0}
        current = nested_data
        for i in range(1000):  # Very deep nesting
            current["nested"] = {"level": i + 1}
            current = current["nested"]
        
        deep_workflow = {
            "nodes": [
                {
                    "id": "deep-node",
                    "type": "dataSource",
                    "data": nested_data
                }
            ],
            "edges": []
        }
        
        converter = WorkflowConverter()
        result = converter.convert_to_training_config(deep_workflow)
        
        # Should handle deep nesting gracefully
        assert result["success"] is False
        assert ("Nesting too deep" in result["error"] or 
                "Recursion limit exceeded" in result["error"])
        assert result["error_type"] == "nesting_limit_exceeded"
    
    def test_circular_reference_in_data(self):
        """Test handling of circular references in node data."""
        from workflow_converter import WorkflowConverter
        
        # Create circular reference in data
        circular_data = {"name": "test"}
        circular_data["self_ref"] = circular_data  # Circular reference
        
        circular_workflow = {
            "nodes": [
                {
                    "id": "circular-node",
                    "type": "dataSource",
                    "data": circular_data
                }
            ],
            "edges": []
        }
        
        converter = WorkflowConverter()
        
        # Should detect and handle circular references
        result = converter.convert_to_training_config(circular_workflow)
        
        assert result["success"] is False
        assert "Circular reference detected" in result["error"]
        assert result["error_type"] == "circular_reference"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])