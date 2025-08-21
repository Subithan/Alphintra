"""
Unit tests for training job manager workflow functionality.
Tests workflow-specific methods in the TrainingJobManager class.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4, UUID
import sys
from pathlib import Path

# Add the app directory to the path
APP_DIR = Path(__file__).resolve().parents[2] / "app"
sys.path.insert(0, str(APP_DIR))

from services.training_job_manager import TrainingJobManager


@pytest.fixture
def sample_workflow_metadata():
    """Sample workflow metadata for testing."""
    return {
        "workflow_id": 123,
        "workflow_name": "RSI Strategy Test",
        "workflow_definition": {
            "nodes": [
                {
                    "id": "data-1",
                    "type": "dataSource",
                    "data": {"symbol": "BTCUSDT", "timeframe": "1h"}
                },
                {
                    "id": "rsi-1",
                    "type": "technicalIndicator",
                    "data": {"indicator": "rsi", "period": 14}
                },
                {
                    "id": "condition-1",
                    "type": "condition",
                    "data": {"threshold": 30, "operator": "<"}
                },
                {
                    "id": "buy-1",
                    "type": "action",
                    "data": {"action": "buy", "quantity": 100}
                }
            ],
            "edges": [
                {"source": "data-1", "target": "rsi-1"},
                {"source": "rsi-1", "target": "condition-1"},
                {"source": "condition-1", "target": "buy-1"}
            ]
        },
        "training_config": {
            "optimization_parameters": ["rsi_period", "threshold"],
            "parameter_bounds": {"rsi_period": [10, 20], "threshold": [20, 40]}
        },
        "optimization_objective": "sharpe_ratio",
        "max_trials": 50,
        "instance_type": "CPU_MEDIUM",
        "timeout_hours": 12,
        "priority": "NORMAL"
    }

@pytest.fixture
def mock_strategy_result():
    """Mock strategy generation result."""
    return {
        "success": True,
        "strategy_code": "# Generated strategy code\nclass WorkflowStrategy:\n    pass",
        "strategy_class": "WorkflowStrategy",
        "entry_point": "create_strategy_instance",
        "metadata": {
            "workflow_id": 123,
            "code_lines": 50,
            "complexity_score": 15,
            "indicator_count": 1,
            "condition_count": 1,
            "action_count": 1
        },
        "optimization_config": {
            "parameters": {"rsi_period": 14, "threshold": 30},
            "parameter_bounds": {"rsi_period": [10, 20], "threshold": [20, 40]},
            "constraint_functions": ["max_drawdown", "var_95"]
        }
    }

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    return session


class TestTrainingJobManagerWorkflow:
    """Test workflow-specific functionality in TrainingJobManager."""
    
    def test_manager_initialization(self):
        """Test TrainingJobManager initialization."""
        manager = TrainingJobManager()
        assert manager is not None
        assert hasattr(manager, 'create_job_from_workflow')
        assert hasattr(manager, '_create_workflow_dataset')
        assert hasattr(manager, '_create_strategy_from_workflow')
    
    @pytest.mark.asyncio
    async def test_successful_workflow_job_creation(self, sample_workflow_metadata, 
                                                   mock_strategy_result, mock_db_session):
        """Test successful training job creation from workflow."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        # Mock workflow validation
        with patch('services.training_job_manager.validate_workflow_for_training') as mock_validate:
            mock_validate.return_value = (True, [])
            
            # Mock strategy generation
            with patch('services.training_job_manager.generate_strategy_from_workflow_definition') as mock_generate:
                mock_generate.return_value = mock_strategy_result
                
                # Mock dataset creation
                with patch.object(manager, '_create_workflow_dataset') as mock_dataset:
                    mock_dataset.return_value = "platform_btcusdt_1h_binance"
                    
                    # Mock strategy creation
                    with patch.object(manager, '_create_strategy_from_workflow') as mock_strategy:
                        strategy_id = uuid4()
                        mock_strategy.return_value = strategy_id
                        
                        # Mock existing training job creation
                        with patch.object(manager, 'create_training_job') as mock_create_job:
                            mock_create_job.return_value = {
                                "success": True,
                                "job_id": "training_job_123",
                                "status": "queued"
                            }
                            
                            # Execute method
                            result = await manager.create_job_from_workflow(
                                sample_workflow_metadata, user_id, mock_db_session
                            )
                            
                            # Verify successful result
                            assert result["success"] is True
                            assert result["job_id"] == "training_job_123"
                            assert result["status"] == "queued"
                            assert "workflow_info" in result
                            
                            # Verify workflow info
                            workflow_info = result["workflow_info"]
                            assert workflow_info["workflow_id"] == 123
                            assert workflow_info["workflow_name"] == "RSI Strategy Test"
                            assert workflow_info["strategy_code_lines"] == 50
                            assert workflow_info["complexity_score"] == 15
                            assert workflow_info["optimization_parameters"] == 2
                            
                            # Verify method calls
                            mock_validate.assert_called_once()
                            mock_generate.assert_called_once()
                            mock_dataset.assert_called_once()
                            mock_strategy.assert_called_once()
                            mock_create_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_validation_failure(self, sample_workflow_metadata, mock_db_session):
        """Test handling of workflow validation failure."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        # Mock workflow validation failure
        with patch('services.training_job_manager.validate_workflow_for_training') as mock_validate:
            mock_validate.return_value = (False, ["Missing required node types", "Workflow too simple"])
            
            result = await manager.create_job_from_workflow(
                sample_workflow_metadata, user_id, mock_db_session
            )
            
            # Verify failure result
            assert result["success"] is False
            assert "Workflow validation failed" in result["error"]
            assert "Missing required node types" in result["error"]
            assert "Workflow too simple" in result["error"]
    
    @pytest.mark.asyncio
    async def test_strategy_generation_failure(self, sample_workflow_metadata, mock_db_session):
        """Test handling of strategy generation failure."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        # Mock successful validation
        with patch('services.training_job_manager.validate_workflow_for_training') as mock_validate:
            mock_validate.return_value = (True, [])
            
            # Mock strategy generation failure
            with patch('services.training_job_manager.generate_strategy_from_workflow_definition') as mock_generate:
                mock_generate.return_value = {
                    "success": False,
                    "error": "Invalid workflow structure for strategy generation"
                }
                
                result = await manager.create_job_from_workflow(
                    sample_workflow_metadata, user_id, mock_db_session
                )
                
                # Verify failure result
                assert result["success"] is False
                assert "Strategy generation failed" in result["error"]
                assert "Invalid workflow structure" in result["error"]
    
    @pytest.mark.asyncio
    async def test_dataset_creation_with_provided_id(self, sample_workflow_metadata, 
                                                    mock_strategy_result, mock_db_session):
        """Test workflow job creation with provided dataset ID."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        # Add dataset_id to metadata
        metadata_with_dataset = sample_workflow_metadata.copy()
        metadata_with_dataset["dataset_id"] = "custom_dataset_123"
        
        with patch('services.training_job_manager.validate_workflow_for_training') as mock_validate:
            mock_validate.return_value = (True, [])
            
            with patch('services.training_job_manager.generate_strategy_from_workflow_definition') as mock_generate:
                mock_generate.return_value = mock_strategy_result
                
                with patch.object(manager, '_create_strategy_from_workflow') as mock_strategy:
                    mock_strategy.return_value = uuid4()
                    
                    with patch.object(manager, 'create_training_job') as mock_create_job:
                        mock_create_job.return_value = {"success": True, "job_id": "test_job"}
                        
                        result = await manager.create_job_from_workflow(
                            metadata_with_dataset, user_id, mock_db_session
                        )
                        
                        # Verify dataset creation was skipped
                        assert result["success"] is True
                        
                        # Verify create_training_job was called with custom dataset ID
                        call_args = mock_create_job.call_args[0][0]
                        assert call_args["dataset_id"] == "custom_dataset_123"
    
    @pytest.mark.asyncio
    async def test_workflow_dataset_creation(self, mock_db_session):
        """Test _create_workflow_dataset method."""
        manager = TrainingJobManager()
        
        workflow_definition = {
            "nodes": [
                {
                    "id": "data-1",
                    "type": "dataSource",
                    "data": {
                        "symbol": "ETHUSDT",
                        "timeframe": "4h",
                        "exchange": "kraken"
                    }
                }
            ]
        }
        
        # Mock dataset doesn't exist
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        dataset_id = await manager._create_workflow_dataset(workflow_definition, mock_db_session)
        
        # Verify dataset ID generation
        assert dataset_id == "platform_ethusdt_4h_kraken"
        
        # Verify dataset was added to session
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_dataset_exists(self, mock_db_session):
        """Test _create_workflow_dataset when dataset already exists."""
        manager = TrainingJobManager()
        
        workflow_definition = {
            "nodes": [
                {"id": "data-1", "type": "dataSource", "data": {"symbol": "BTCUSDT"}}
            ]
        }
        
        # Mock existing dataset
        existing_dataset = Mock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_dataset
        mock_db_session.execute.return_value = mock_result
        
        dataset_id = await manager._create_workflow_dataset(workflow_definition, mock_db_session)
        
        # Verify dataset ID is returned
        assert dataset_id == "platform_btcusdt_1d_binance"  # Default values
        
        # Verify no new dataset was created
        mock_db_session.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_workflow_dataset_no_data_sources(self, mock_db_session):
        """Test dataset creation with no data sources in workflow."""
        manager = TrainingJobManager()
        
        workflow_definition = {"nodes": []}
        
        dataset_id = await manager._create_workflow_dataset(workflow_definition, mock_db_session)
        
        # Should return default dataset
        assert dataset_id == "platform_default_1d"
    
    @pytest.mark.asyncio
    async def test_strategy_creation_from_workflow(self, mock_strategy_result, 
                                                  sample_workflow_metadata, mock_db_session):
        """Test _create_strategy_from_workflow method."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        # Mock Strategy model
        with patch('services.training_job_manager.Strategy') as mock_strategy_class:
            mock_strategy_instance = Mock()
            mock_strategy_instance.id = uuid4()
            mock_strategy_class.return_value = mock_strategy_instance
            
            strategy_id = await manager._create_strategy_from_workflow(
                mock_strategy_result, sample_workflow_metadata, user_id, mock_db_session
            )
            
            # Verify strategy creation
            assert strategy_id == mock_strategy_instance.id
            
            # Verify database operations
            mock_db_session.add.assert_called_once_with(mock_strategy_instance)
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once_with(mock_strategy_instance)
            
            # Verify strategy configuration
            call_args = mock_strategy_class.call_args[1]
            assert call_args["user_id"] == UUID(user_id)
            assert "Workflow_RSI Strategy Test_123" in call_args["name"]
            assert call_args["strategy_code"] == mock_strategy_result["strategy_code"]
            assert call_args["entry_point"] == "create_strategy_instance"
    
    @pytest.mark.asyncio
    async def test_training_job_data_preparation(self, sample_workflow_metadata, 
                                                mock_strategy_result, mock_db_session):
        """Test preparation of training job data from workflow."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        with patch('services.training_job_manager.validate_workflow_for_training') as mock_validate:
            mock_validate.return_value = (True, [])
            
            with patch('services.training_job_manager.generate_strategy_from_workflow_definition') as mock_generate:
                mock_generate.return_value = mock_strategy_result
                
                with patch.object(manager, '_create_workflow_dataset') as mock_dataset:
                    mock_dataset.return_value = "test_dataset"
                    
                    with patch.object(manager, '_create_strategy_from_workflow') as mock_strategy:
                        mock_strategy.return_value = uuid4()
                        
                        with patch.object(manager, 'create_training_job') as mock_create_job:
                            mock_create_job.return_value = {"success": True}
                            
                            await manager.create_job_from_workflow(
                                sample_workflow_metadata, user_id, mock_db_session
                            )
                            
                            # Verify job data preparation
                            call_args = mock_create_job.call_args[0][0]
                            
                            assert call_args["job_name"] == "Workflow_RSI Strategy Test_123"
                            assert call_args["job_type"] == "training"
                            assert call_args["instance_type"] == "cpu_medium"
                            assert call_args["timeout_hours"] == 12
                            assert call_args["priority"] == "normal"
                            assert call_args["dataset_id"] == "test_dataset"
                            
                            # Verify training configuration
                            training_config = call_args["training_config"]
                            assert training_config["optimization_objective"] == "sharpe_ratio"
                            assert training_config["max_trials"] == 50
                            assert "workflow_metadata" in training_config
                            assert "parameter_bounds" in training_config
                            
                            # Verify ML model configuration
                            ml_config = call_args["ml_model_config"]
                            assert ml_config["model_type"] == "ensemble"
                            assert ml_config["optimization_algorithm"] == "bayesian"
                            assert ml_config["early_stopping"] is True


class TestWorkflowJobManagerErrorHandling:
    """Test error handling in workflow job management."""
    
    @pytest.mark.asyncio
    async def test_database_error_in_dataset_creation(self, sample_workflow_metadata, mock_db_session):
        """Test handling of database errors during dataset creation."""
        manager = TrainingJobManager()
        
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database connection failed")
        
        dataset_id = await manager._create_workflow_dataset(
            sample_workflow_metadata["workflow_definition"], mock_db_session
        )
        
        # Should return fallback dataset ID
        assert dataset_id == "platform_default_1d"
    
    @pytest.mark.asyncio
    async def test_strategy_creation_database_error(self, mock_strategy_result, 
                                                   sample_workflow_metadata, mock_db_session):
        """Test handling of database errors during strategy creation."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        # Mock database error
        mock_db_session.add.side_effect = Exception("Database write failed")
        
        with pytest.raises(Exception, match="Database write failed"):
            await manager._create_strategy_from_workflow(
                mock_strategy_result, sample_workflow_metadata, user_id, mock_db_session
            )
    
    @pytest.mark.asyncio
    async def test_workflow_job_creation_general_error(self, sample_workflow_metadata, mock_db_session):
        """Test handling of general errors in workflow job creation."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        # Mock validation to throw unexpected error
        with patch('services.training_job_manager.validate_workflow_for_training') as mock_validate:
            mock_validate.side_effect = Exception("Unexpected validation error")
            
            result = await manager.create_job_from_workflow(
                sample_workflow_metadata, user_id, mock_db_session
            )
            
            # Should return graceful error response
            assert result["success"] is False
            assert "Workflow job creation failed" in result["error"]
            assert "Unexpected validation error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_missing_workflow_definition(self, mock_db_session):
        """Test handling of missing workflow definition."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        incomplete_metadata = {
            "workflow_id": 123,
            "workflow_name": "Test",
            # Missing workflow_definition
        }
        
        result = await manager.create_job_from_workflow(
            incomplete_metadata, user_id, mock_db_session
        )
        
        # Should handle gracefully
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_invalid_user_id(self, sample_workflow_metadata, mock_db_session):
        """Test handling of invalid user ID."""
        manager = TrainingJobManager()
        
        with patch('services.training_job_manager.validate_workflow_for_training') as mock_validate:
            mock_validate.return_value = (True, [])
            
            result = await manager.create_job_from_workflow(
                sample_workflow_metadata, "invalid-uuid", mock_db_session
            )
            
            # Should handle invalid UUID gracefully
            assert result["success"] is False
            assert "error" in result


class TestWorkflowJobManagerIntegration:
    """Integration-style tests for workflow job management."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_processing(self, sample_workflow_metadata, 
                                                 mock_strategy_result, mock_db_session):
        """Test complete end-to-end workflow processing."""
        manager = TrainingJobManager()
        user_id = str(uuid4())
        
        # Mock all dependencies for complete flow
        with patch('services.training_job_manager.validate_workflow_for_training') as mock_validate:
            mock_validate.return_value = (True, [])
            
            with patch('services.training_job_manager.generate_strategy_from_workflow_definition') as mock_generate:
                mock_generate.return_value = mock_strategy_result
                
                # Mock dataset operations
                dataset_result = Mock()
                dataset_result.scalar_one_or_none.return_value = None
                mock_db_session.execute.return_value = dataset_result
                
                # Mock strategy creation
                with patch('services.training_job_manager.Strategy') as mock_strategy_class:
                    mock_strategy = Mock()
                    strategy_id = uuid4()
                    mock_strategy.id = strategy_id
                    mock_strategy_class.return_value = mock_strategy
                    
                    # Mock training job creation
                    with patch.object(manager, 'create_training_job') as mock_create_job:
                        mock_create_job.return_value = {
                            "success": True,
                            "job_id": "training_job_complete_test",
                            "status": "queued",
                            "estimated_duration_hours": 2.5
                        }
                        
                        # Execute complete workflow
                        result = await manager.create_job_from_workflow(
                            sample_workflow_metadata, user_id, mock_db_session
                        )
                        
                        # Verify complete success
                        assert result["success"] is True
                        assert result["job_id"] == "training_job_complete_test"
                        assert "workflow_info" in result
                        
                        # Verify all steps were executed
                        mock_validate.assert_called_once()
                        mock_generate.assert_called_once()
                        mock_db_session.add.assert_called()  # Dataset and strategy creation
                        mock_create_job.assert_called_once()
                        
                        # Verify job data contains workflow information
                        job_data = mock_create_job.call_args[0][0]
                        assert job_data["strategy_id"] == str(strategy_id)
                        assert "workflow_metadata" in job_data["training_config"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])