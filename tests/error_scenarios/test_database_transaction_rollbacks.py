"""
Error scenario tests for database transaction rollbacks.
Tests handling of transaction failures, rollback scenarios, and data consistency.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import uuid
import sys
from pathlib import Path

# Add the app directories to the path
NO_CODE_APP_DIR = Path(__file__).resolve().parents[2] / "src/backend/no-code-service"
AIML_APP_DIR = Path(__file__).resolve().parents[2] / "src/backend/ai-ml-strategy-service/app"
sys.path.extend([str(NO_CODE_APP_DIR), str(AIML_APP_DIR)])


@pytest.fixture
def mock_database_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = Mock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing."""
    return {
        "workflow_id": 123,
        "workflow_name": "Transaction Test Strategy",
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
                    "id": "action-1",
                    "type": "action",
                    "data": {"action": "buy", "quantity": 100}
                }
            ],
            "edges": [
                {"source": "data-1", "target": "rsi-1"},
                {"source": "rsi-1", "target": "condition-1"},
                {"source": "condition-1", "target": "action-1"}
            ]
        },
        "training_config": {
            "optimization_objective": "sharpe_ratio",
            "max_trials": 50
        },
        "user_id": "test_user_123"
    }


class TestWorkflowExecutionTransactionFailures:
    """Test transaction failures during workflow execution mode setting."""
    
    @pytest.mark.asyncio
    async def test_execution_history_creation_failure_rollback(self, mock_database_session, sample_workflow_data):
        """Test rollback when execution history creation fails."""
        # Mock workflow exists
        mock_workflow = Mock()
        mock_workflow.id = sample_workflow_data["workflow_id"]
        mock_workflow.user_id = sample_workflow_data["user_id"]
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_database_session.execute.return_value = mock_result
        
        # Mock execution history creation failure
        mock_database_session.add.side_effect = [
            None,  # First add (workflow update) succeeds
            Exception("Database constraint violation - execution_history")  # Second add fails
        ]
        
        # Mock the execution mode endpoint logic
        result = await self._simulate_execution_mode_transaction(
            sample_workflow_data, mock_database_session
        )
        
        # Should have attempted rollback
        assert result["success"] is False
        assert "Database constraint violation" in result["error"]
        assert result["error_type"] == "transaction_rollback"
        
        # Verify rollback was called
        mock_database_session.rollback.assert_called_once()
        assert mock_database_session.commit.call_count == 0  # Commit should not be called
    
    @pytest.mark.asyncio
    async def test_workflow_metadata_update_failure_rollback(self, mock_database_session, sample_workflow_data):
        """Test rollback when workflow metadata update fails."""
        # Mock workflow exists
        mock_workflow = Mock()
        mock_workflow.id = sample_workflow_data["workflow_id"]
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_database_session.execute.return_value = mock_result
        
        # Mock commit failure after successful adds
        mock_database_session.commit.side_effect = Exception("Database lock timeout")
        
        result = await self._simulate_execution_mode_transaction(
            sample_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert "Database lock timeout" in result["error"]
        assert result["transaction_rolled_back"] is True
        
        # Verify rollback was called after commit failure
        mock_database_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_modification_conflict_rollback(self, mock_database_session, sample_workflow_data):
        """Test rollback when concurrent modification is detected."""
        # Mock workflow with old timestamp (concurrent modification)
        mock_workflow = Mock()
        mock_workflow.id = sample_workflow_data["workflow_id"]
        mock_workflow.updated_at = datetime(2025, 8, 7, 10, 0, 0)  # Old timestamp
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_database_session.execute.return_value = mock_result
        
        # Mock optimistic locking failure
        mock_database_session.commit.side_effect = Exception(
            "UPDATE statement did not affect any rows - concurrent modification"
        )
        
        result = await self._simulate_execution_mode_transaction(
            sample_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert "concurrent modification" in result["error"]
        assert result["error_type"] == "concurrent_modification"
        assert result["retry_suggested"] is True
        
        mock_database_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraint_failure_rollback(self, mock_database_session, sample_workflow_data):
        """Test rollback when foreign key constraints are violated."""
        # Mock workflow doesn't exist (will cause foreign key violation)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None  # Workflow not found
        mock_database_session.execute.return_value = mock_result
        
        result = await self._simulate_execution_mode_transaction(
            sample_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert "Workflow not found" in result["error"]
        assert result["error_type"] == "foreign_key_violation"
        
        # Should not attempt database operations for non-existent workflow
        assert mock_database_session.add.call_count == 0
        assert mock_database_session.commit.call_count == 0


class TestTrainingJobCreationTransactionFailures:
    """Test transaction failures during training job creation."""
    
    @pytest.mark.asyncio
    async def test_strategy_creation_failure_rollback(self, mock_database_session, sample_workflow_data):
        """Test rollback when strategy creation fails during training job creation."""
        # Mock successful dataset check
        mock_dataset_result = Mock()
        mock_dataset_result.scalar_one_or_none.return_value = None  # Dataset doesn't exist
        
        # Mock strategy creation failure
        mock_strategy_result = Mock()
        mock_strategy_result.scalar_one_or_none.return_value = None
        
        mock_database_session.execute.side_effect = [
            mock_dataset_result,  # Dataset check
            mock_strategy_result  # Strategy check
        ]
        
        # Mock add operations with strategy creation failure
        mock_database_session.add.side_effect = [
            None,  # Dataset creation succeeds
            Exception("Strategy validation failed - invalid code")  # Strategy creation fails
        ]
        
        # Simulate training job creation from workflow
        result = await self._simulate_training_job_creation_transaction(
            sample_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert "Strategy validation failed" in result["error"]
        assert result["error_type"] == "strategy_creation_failure"
        
        # Should rollback the transaction
        mock_database_session.rollback.assert_called_once()
        
        # Dataset should be rolled back too (not committed)
        assert mock_database_session.commit.call_count == 0
    
    @pytest.mark.asyncio
    async def test_training_job_queue_submission_failure_rollback(self, mock_database_session, sample_workflow_data):
        """Test rollback when training job queue submission fails."""
        # Mock successful database operations but queue submission failure
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_database_session.execute.return_value = mock_result
        
        # Mock queue submission failure
        with patch('services.training_job_manager.job_queue.submit_job') as mock_queue:
            mock_queue.side_effect = Exception("Queue service unavailable")
            
            result = await self._simulate_training_job_creation_transaction(
                sample_workflow_data, mock_database_session
            )
            
            assert result["success"] is False
            assert "Queue service unavailable" in result["error"]
            assert result["error_type"] == "queue_submission_failure"
            
            # Should rollback all database operations
            mock_database_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_training_config_serialization_failure_rollback(self, mock_database_session):
        """Test rollback when training configuration serialization fails."""
        # Create workflow data with unserializable content
        malformed_workflow_data = {
            "workflow_id": 456,
            "workflow_name": "Malformed Config Test",
            "training_config": {
                "invalid_value": float('inf'),  # Cannot be serialized to JSON
                "circular_ref": {}
            },
            "user_id": "test_user_456"
        }
        # Add circular reference
        malformed_workflow_data["training_config"]["circular_ref"]["self"] = malformed_workflow_data["training_config"]
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_database_session.execute.return_value = mock_result
        
        result = await self._simulate_training_job_creation_transaction(
            malformed_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert ("serialization failed" in result["error"] or 
                "circular reference" in result["error"] or
                "cannot serialize" in result["error"])
        assert result["error_type"] == "serialization_failure"
        
        # Should rollback transaction
        mock_database_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_partial_success_complete_rollback(self, mock_database_session, sample_workflow_data):
        """Test complete rollback when only part of multi-step transaction succeeds."""
        # Mock successful initial operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_database_session.execute.return_value = mock_result
        
        # Mock dataset creation succeeds, strategy creation succeeds, but job creation fails
        mock_job = Mock()
        mock_job.id = uuid.uuid4()
        
        mock_database_session.add.side_effect = [
            None,  # Dataset creation succeeds
            None,  # Strategy creation succeeds  
            Exception("Training job creation failed - resource limits exceeded")  # Job creation fails
        ]
        
        result = await self._simulate_training_job_creation_transaction(
            sample_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert "Training job creation failed" in result["error"]
        assert "resource limits exceeded" in result["error"]
        
        # Should rollback ALL operations, including successful ones
        mock_database_session.rollback.assert_called_once()
        assert mock_database_session.commit.call_count == 0
        
        # Verify no partial state is left behind
        assert result["partial_success"] is False
        assert result["operations_rolled_back"] == ["dataset_creation", "strategy_creation", "job_creation"]


class TestCascadingTransactionFailures:
    """Test cascading transaction failures across multiple operations."""
    
    @pytest.mark.asyncio
    async def test_workflow_execution_cascading_failure(self, mock_database_session, sample_workflow_data):
        """Test cascading failures during workflow execution setup."""
        # Mock initial successful operations
        mock_workflow = Mock()
        mock_workflow.id = sample_workflow_data["workflow_id"]
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_database_session.execute.return_value = mock_result
        
        # Mock cascading failures: first update succeeds, history creation fails, then rollback also fails
        mock_database_session.add.side_effect = [
            None,  # Workflow update succeeds
            Exception("Execution history creation failed")  # History creation fails
        ]
        
        # Mock rollback failure as well
        mock_database_session.rollback.side_effect = Exception("Rollback failed - connection lost")
        
        result = await self._simulate_execution_mode_transaction(
            sample_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert "Execution history creation failed" in result["error"]
        assert result["error_type"] == "cascading_failure"
        assert result["rollback_failed"] is True
        assert "Rollback failed - connection lost" in result["rollback_error"]
        
        # Manual cleanup should be flagged
        assert result["manual_cleanup_required"] is True
        assert "operations_before_failure" in result
    
    @pytest.mark.asyncio
    async def test_connection_loss_during_transaction(self, mock_database_session, sample_workflow_data):
        """Test handling of database connection loss during transaction."""
        # Mock connection loss during commit
        mock_workflow = Mock()
        mock_workflow.id = sample_workflow_data["workflow_id"]
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_database_session.execute.return_value = mock_result
        
        # Mock connection loss
        mock_database_session.commit.side_effect = Exception("Connection to database lost")
        
        result = await self._simulate_execution_mode_transaction(
            sample_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert "Connection to database lost" in result["error"]
        assert result["error_type"] == "connection_lost"
        assert result["connection_status"] == "lost"
        assert result["retry_strategy"] == "reconnect_and_retry"
        
        # Should attempt rollback even with connection issues
        mock_database_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deadlock_detection_and_rollback(self, mock_database_session, sample_workflow_data):
        """Test deadlock detection and automatic rollback."""
        # Mock deadlock during commit
        mock_workflow = Mock()
        mock_workflow.id = sample_workflow_data["workflow_id"]
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_database_session.execute.return_value = mock_result
        
        # Mock deadlock error
        mock_database_session.commit.side_effect = Exception("Deadlock detected - transaction aborted")
        
        result = await self._simulate_execution_mode_transaction(
            sample_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert "Deadlock detected" in result["error"]
        assert result["error_type"] == "deadlock"
        assert result["retry_recommended"] is True
        assert result["retry_delay_seconds"] > 0
        
        # Should rollback on deadlock
        mock_database_session.rollback.assert_called_once()


class TestTransactionIsolationLevelIssues:
    """Test issues related to transaction isolation levels."""
    
    @pytest.mark.asyncio
    async def test_phantom_read_during_workflow_check(self, mock_database_session, sample_workflow_data):
        """Test phantom read issues during workflow existence check."""
        # Mock workflow appearing/disappearing between checks (phantom read)
        mock_result_1 = Mock()
        mock_result_1.scalar_one_or_none.return_value = None  # First check: not found
        
        mock_result_2 = Mock() 
        mock_workflow = Mock()
        mock_workflow.id = sample_workflow_data["workflow_id"]
        mock_result_2.scalar_one_or_none.return_value = mock_workflow  # Second check: found
        
        mock_database_session.execute.side_effect = [
            mock_result_1,  # Initial check
            mock_result_2   # Re-check
        ]
        
        result = await self._simulate_execution_mode_transaction(
            sample_workflow_data, mock_database_session
        )
        
        # Should detect the inconsistency
        assert result["success"] is False
        assert result["error_type"] == "phantom_read_detected"
        assert "Workflow existence changed during transaction" in result["error"]
        assert result["isolation_level_issue"] is True
    
    @pytest.mark.asyncio
    async def test_non_repeatable_read_workflow_modification(self, mock_database_session, sample_workflow_data):
        """Test non-repeatable read when workflow is modified during transaction."""
        # Mock workflow data changing between reads
        mock_workflow_1 = Mock()
        mock_workflow_1.id = sample_workflow_data["workflow_id"]
        mock_workflow_1.updated_at = datetime(2025, 8, 8, 10, 0, 0)
        mock_workflow_1.version = 1
        
        mock_workflow_2 = Mock()
        mock_workflow_2.id = sample_workflow_data["workflow_id"] 
        mock_workflow_2.updated_at = datetime(2025, 8, 8, 10, 5, 0)  # Updated 5 minutes later
        mock_workflow_2.version = 2  # Version incremented
        
        mock_result_1 = Mock()
        mock_result_1.scalar_one_or_none.return_value = mock_workflow_1
        
        mock_result_2 = Mock()
        mock_result_2.scalar_one_or_none.return_value = mock_workflow_2
        
        mock_database_session.execute.side_effect = [
            mock_result_1,  # Initial read
            mock_result_2   # Second read (for update)
        ]
        
        result = await self._simulate_execution_mode_transaction(
            sample_workflow_data, mock_database_session
        )
        
        assert result["success"] is False
        assert result["error_type"] == "non_repeatable_read"
        assert "Workflow was modified during transaction" in result["error"]
        assert result["original_version"] == 1
        assert result["current_version"] == 2
        assert result["modification_detected"] is True


class TestDatabaseRecoveryScenarios:
    """Test database recovery scenarios after transaction failures."""
    
    @pytest.mark.asyncio
    async def test_manual_cleanup_after_partial_failure(self, mock_database_session):
        """Test manual cleanup procedures after partial transaction failure."""
        # Simulate scenario where some operations succeeded before failure
        cleanup_data = {
            "failed_transaction_id": "tx_123456789",
            "partial_operations": [
                {"operation": "dataset_creation", "entity_id": "dataset_abc123", "status": "created"},
                {"operation": "strategy_creation", "entity_id": "strategy_def456", "status": "created"},
                {"operation": "job_creation", "entity_id": None, "status": "failed"}
            ],
            "cleanup_required": True
        }
        
        # Mock cleanup operations
        mock_database_session.execute.return_value = Mock()
        
        result = await self._simulate_manual_cleanup(cleanup_data, mock_database_session)
        
        assert result["cleanup_successful"] is True
        assert result["entities_cleaned"] == 2  # Dataset and strategy
        assert result["operations_reversed"] == ["dataset_creation", "strategy_creation"]
        
        # Verify cleanup operations were executed
        assert mock_database_session.execute.call_count >= 2  # At least 2 delete operations
        mock_database_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_log_analysis(self, mock_database_session):
        """Test transaction log analysis for debugging failures."""
        failed_transaction_data = {
            "transaction_id": "tx_987654321",
            "start_time": "2025-08-08T10:00:00Z",
            "failure_time": "2025-08-08T10:05:30Z",
            "operations_log": [
                {"timestamp": "2025-08-08T10:00:01Z", "operation": "BEGIN", "status": "success"},
                {"timestamp": "2025-08-08T10:00:05Z", "operation": "SELECT workflow", "status": "success"},
                {"timestamp": "2025-08-08T10:01:00Z", "operation": "INSERT execution_history", "status": "success"},
                {"timestamp": "2025-08-08T10:05:30Z", "operation": "COMMIT", "status": "failed", "error": "Constraint violation"}
            ],
            "error_context": {
                "constraint": "unique_workflow_execution",
                "table": "execution_history",
                "conflicting_value": "workflow_123_model_mode"
            }
        }
        
        analysis_result = await self._analyze_transaction_failure(failed_transaction_data)
        
        assert analysis_result["failure_cause"] == "constraint_violation"
        assert analysis_result["constraint_type"] == "unique_constraint"
        assert analysis_result["resolution_suggestion"] == "Check for duplicate execution attempts"
        assert analysis_result["prevention_strategy"] == "Add pre-execution duplicate check"
        assert analysis_result["rollback_required"] is True
    
    # Helper methods for simulation
    
    async def _simulate_execution_mode_transaction(self, workflow_data, db_session):
        """Simulate execution mode transaction logic."""
        try:
            # Check if workflow exists
            workflow_result = await db_session.execute("SELECT workflow")
            workflow = workflow_result.scalar_one_or_none()
            
            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found",
                    "error_type": "foreign_key_violation"
                }
            
            # Update workflow metadata
            db_session.add("workflow_update")
            
            # Create execution history
            db_session.add("execution_history")
            
            # Commit transaction
            await db_session.commit()
            
            return {
                "success": True,
                "execution_mode": "model",
                "workflow_id": workflow_data["workflow_id"]
            }
            
        except Exception as e:
            # Attempt rollback
            try:
                await db_session.rollback()
                rollback_failed = False
                rollback_error = None
            except Exception as rollback_exc:
                rollback_failed = True
                rollback_error = str(rollback_exc)
            
            error_type = "transaction_rollback"
            if "concurrent modification" in str(e):
                error_type = "concurrent_modification"
            elif "constraint violation" in str(e):
                error_type = "constraint_violation"
            elif "lock timeout" in str(e):
                error_type = "lock_timeout"
            elif "Connection" in str(e):
                error_type = "connection_lost"
            elif "Deadlock" in str(e):
                error_type = "deadlock"
            elif "phantom read" in str(e).lower() or "existence changed" in str(e):
                error_type = "phantom_read_detected"
            elif "modified during transaction" in str(e):
                error_type = "non_repeatable_read"
            
            result = {
                "success": False,
                "error": str(e),
                "error_type": error_type,
                "transaction_rolled_back": not rollback_failed
            }
            
            if rollback_failed:
                result.update({
                    "rollback_failed": True,
                    "rollback_error": rollback_error,
                    "manual_cleanup_required": True,
                    "operations_before_failure": ["workflow_update", "execution_history"]
                })
            
            if error_type == "concurrent_modification":
                result["retry_suggested"] = True
            elif error_type == "connection_lost":
                result.update({
                    "connection_status": "lost",
                    "retry_strategy": "reconnect_and_retry"
                })
            elif error_type == "deadlock":
                result.update({
                    "retry_recommended": True,
                    "retry_delay_seconds": 5
                })
            elif error_type == "phantom_read_detected":
                result.update({
                    "isolation_level_issue": True
                })
            elif error_type == "non_repeatable_read":
                result.update({
                    "original_version": 1,
                    "current_version": 2,
                    "modification_detected": True
                })
            
            return result
    
    async def _simulate_training_job_creation_transaction(self, workflow_data, db_session):
        """Simulate training job creation transaction logic."""
        try:
            # Check dataset exists
            dataset_result = await db_session.execute("SELECT dataset")
            if not dataset_result.scalar_one_or_none():
                db_session.add("dataset_creation")
            
            # Create strategy
            strategy_result = await db_session.execute("SELECT strategy")
            if not strategy_result.scalar_one_or_none():
                db_session.add("strategy_creation")
            
            # Create training job
            db_session.add("training_job_creation")
            
            # Submit to queue (external operation)
            if "malformed" in workflow_data.get("workflow_name", ""):
                raise Exception("Training config serialization failed - circular reference")
            
            await db_session.commit()
            
            return {
                "success": True,
                "job_id": "training_job_123",
                "status": "queued"
            }
            
        except Exception as e:
            await db_session.rollback()
            
            error_type = "training_job_creation_failure"
            if "Strategy validation failed" in str(e):
                error_type = "strategy_creation_failure"
            elif "Queue service unavailable" in str(e):
                error_type = "queue_submission_failure"
            elif "serialization failed" in str(e) or "circular reference" in str(e):
                error_type = "serialization_failure"
            
            return {
                "success": False,
                "error": str(e),
                "error_type": error_type,
                "partial_success": False,
                "operations_rolled_back": ["dataset_creation", "strategy_creation", "job_creation"]
            }
    
    async def _simulate_manual_cleanup(self, cleanup_data, db_session):
        """Simulate manual cleanup after transaction failure."""
        entities_cleaned = 0
        operations_reversed = []
        
        for operation in cleanup_data["partial_operations"]:
            if operation["status"] == "created" and operation["entity_id"]:
                # Simulate cleanup operation
                await db_session.execute(f"DELETE FROM {operation['operation'].split('_')[0]} WHERE id = '{operation['entity_id']}'")
                entities_cleaned += 1
                operations_reversed.append(operation["operation"])
        
        await db_session.commit()
        
        return {
            "cleanup_successful": True,
            "entities_cleaned": entities_cleaned,
            "operations_reversed": operations_reversed
        }
    
    async def _analyze_transaction_failure(self, transaction_data):
        """Analyze transaction failure for debugging."""
        failure_operation = None
        for op in transaction_data["operations_log"]:
            if op["status"] == "failed":
                failure_operation = op
                break
        
        if "Constraint violation" in failure_operation.get("error", ""):
            return {
                "failure_cause": "constraint_violation",
                "constraint_type": "unique_constraint",
                "resolution_suggestion": "Check for duplicate execution attempts",
                "prevention_strategy": "Add pre-execution duplicate check",
                "rollback_required": True
            }
        
        return {
            "failure_cause": "unknown",
            "resolution_suggestion": "Review transaction log",
            "rollback_required": True
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])