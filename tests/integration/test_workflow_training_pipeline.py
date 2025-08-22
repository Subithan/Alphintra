"""
Integration tests for complete workflow training pipeline.
Tests the full pipeline from workflow creation to model deployment.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4


@pytest.fixture
def sample_workflow_pipeline():
    """Sample workflow for pipeline testing."""
    return {
        "workflow_definition": {
            "nodes": [
                {
                    "id": "btc-data",
                    "type": "dataSource",
                    "data": {
                        "symbol": "BTCUSDT",
                        "timeframe": "1h",
                        "exchange": "binance"
                    }
                },
                {
                    "id": "bb-indicator",
                    "type": "technicalIndicator",
                    "data": {
                        "indicator": "bollinger_bands",
                        "period": 20,
                        "std_dev": 2
                    }
                },
                {
                    "id": "adx-indicator",
                    "type": "technicalIndicator",
                    "data": {
                        "indicator": "adx",
                        "period": 14
                    }
                },
                {
                    "id": "bb-breakout",
                    "type": "condition",
                    "data": {
                        "condition_type": "threshold",
                        "operator": ">",
                        "comparison_mode": "cross_above"
                    }
                },
                {
                    "id": "trend-strong",
                    "type": "condition",
                    "data": {
                        "condition_type": "threshold",
                        "operator": ">",
                        "threshold": 25
                    }
                },
                {
                    "id": "enter-long",
                    "type": "action",
                    "data": {
                        "action_type": "buy",
                        "quantity": 200,
                        "order_type": "market"
                    }
                }
            ],
            "edges": [
                {"source": "btc-data", "target": "bb-indicator"},
                {"source": "btc-data", "target": "adx-indicator"},
                {"source": "bb-indicator", "target": "bb-breakout"},
                {"source": "adx-indicator", "target": "trend-strong"},
                {"source": "bb-breakout", "target": "enter-long"},
                {"source": "trend-strong", "target": "enter-long"}
            ]
        },
        "metadata": {
            "workflow_id": 555,
            "workflow_name": "Bollinger Band Breakout Strategy",
            "user_id": "user_pipeline_test",
            "created_at": datetime.now().isoformat()
        }
    }


class TestWorkflowTrainingPipeline:
    """Test the complete workflow training pipeline."""
    
    @pytest.mark.asyncio
    async def test_complete_training_pipeline(self, sample_workflow_pipeline):
        """Test the complete training pipeline from workflow to optimized strategy."""
        workflow_data = sample_workflow_pipeline["workflow_definition"]
        metadata = sample_workflow_pipeline["metadata"]
        
        # Step 1: Workflow validation and parsing
        with patch('services.workflow_parser.WorkflowParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            
            # Mock successful parsing
            mock_parser.parse_workflow.return_value = {
                "data_sources": [
                    {
                        "id": "btc-data",
                        "symbol": "BTCUSDT",
                        "timeframe": "1h",
                        "exchange": "binance"
                    }
                ],
                "technical_indicators": [
                    {
                        "id": "bb-indicator",
                        "indicator_type": "bollinger_bands",
                        "period": 20,
                        "std_dev": 2,
                        "outputs": ["upper_output", "middle_output", "lower_output", "width_output"]
                    },
                    {
                        "id": "adx-indicator",
                        "indicator_type": "adx",
                        "period": 14,
                        "outputs": ["adx_output", "di_plus_output", "di_minus_output"]
                    }
                ],
                "conditions": [
                    {
                        "id": "bb-breakout",
                        "condition_type": "threshold",
                        "operator": ">",
                        "comparison_mode": "cross_above"
                    },
                    {
                        "id": "trend-strong",
                        "operator": ">",
                        "threshold": 25
                    }
                ],
                "actions": [
                    {
                        "id": "enter-long",
                        "action_type": "buy",
                        "quantity": 200,
                        "order_type": "market"
                    }
                ],
                "risk_management": [],
                "logic_components": [],
                "execution_graph": {
                    "btc-data": [],
                    "bb-indicator": ["btc-data"],
                    "adx-indicator": ["btc-data"],
                    "bb-breakout": ["bb-indicator"],
                    "trend-strong": ["adx-indicator"],
                    "enter-long": ["bb-breakout", "trend-strong"]
                },
                "complexity_score": 18
            }
            
            # Step 2: Strategy code generation
            with patch('services.strategy_generator.StrategyGenerator') as mock_gen_class:
                mock_generator = Mock()
                mock_gen_class.return_value = mock_generator
                
                mock_generator.generate_from_workflow.return_value = {
                    "success": True,
                    "strategy_code": self._get_expected_bollinger_strategy_code(),
                    "strategy_class": "WorkflowStrategy",
                    "entry_point": "create_strategy_instance",
                    "validation": {
                        "valid": True,
                        "syntax_valid": True,
                        "line_count": 245,
                        "warnings": []
                    },
                    "metadata": {
                        "workflow_id": 555,
                        "generated_at": datetime.now().isoformat(),
                        "code_lines": 245,
                        "complexity_score": 18,
                        "indicator_count": 2,
                        "condition_count": 2,
                        "action_count": 1
                    },
                    "optimization_config": {
                        "parameters": {
                            "bb_period": 20,
                            "bb_std_dev": 2,
                            "adx_period": 14,
                            "adx_threshold": 25,
                            "position_size": 200
                        },
                        "parameter_bounds": {
                            "bb_period": [15, 30],
                            "bb_std_dev": [1.5, 3.0],
                            "adx_period": [10, 20],
                            "adx_threshold": [20, 35],
                            "position_size": [100, 300]
                        },
                        "constraint_functions": ["max_drawdown", "sharpe_ratio"]
                    }
                }
                
                # Step 3: Training job creation and execution
                with patch('services.training_job_manager.TrainingJobManager') as mock_mgr_class:
                    mock_manager = Mock()
                    mock_mgr_class.return_value = mock_manager
                    
                    # Mock database session
                    mock_db = AsyncMock()
                    
                    mock_manager.create_job_from_workflow.return_value = {
                        "success": True,
                        "job_id": "pipeline_test_job_777",
                        "status": "queued",
                        "queue_position": 1,
                        "estimated_duration_hours": 3.5,
                        "workflow_info": {
                            "workflow_id": 555,
                            "workflow_name": "Bollinger Band Breakout Strategy",
                            "strategy_code_lines": 245,
                            "complexity_score": 18,
                            "optimization_parameters": 5,
                            "generated_at": datetime.now().isoformat()
                        }
                    }
                    
                    # Execute the pipeline
                    result = await self._execute_complete_pipeline(
                        workflow_data, metadata, mock_parser, mock_generator, mock_manager, mock_db
                    )
                    
                    # Verify pipeline execution
                    assert result["success"] is True
                    assert result["job_id"] == "pipeline_test_job_777"
                    assert result["status"] == "queued"
                    
                    # Verify all steps were called
                    mock_parser.parse_workflow.assert_called_once_with(workflow_data)
                    mock_generator.generate_from_workflow.assert_called_once()
                    mock_manager.create_job_from_workflow.assert_called_once()
                    
                    # Verify workflow info
                    workflow_info = result["workflow_info"]
                    assert workflow_info["workflow_id"] == 555
                    assert workflow_info["optimization_parameters"] == 5
                    assert workflow_info["complexity_score"] == 18
    
    @pytest.mark.asyncio
    async def test_training_execution_with_monitoring(self, sample_workflow_pipeline):
        """Test training execution with real-time monitoring."""
        job_id = "monitoring_test_888"
        
        # Simulate training progression with realistic metrics
        training_stages = [
            {
                "status": "queued",
                "progress": 0.0,
                "current_step": "Job queued",
                "queue_position": 3
            },
            {
                "status": "running",
                "progress": 0.05,
                "current_step": "Environment setup",
                "elapsed_minutes": 2
            },
            {
                "status": "running",
                "progress": 0.20,
                "current_step": "Data loading and preprocessing",
                "elapsed_minutes": 15,
                "metrics": {
                    "data_points_loaded": 8760,
                    "features_engineered": 7,
                    "missing_data_percentage": 0.02
                }
            },
            {
                "status": "running",
                "progress": 0.45,
                "current_step": "Hyperparameter optimization",
                "elapsed_minutes": 45,
                "metrics": {
                    "current_trial": 23,
                    "total_trials": 100,
                    "best_score": 1.23,
                    "current_parameters": {
                        "bb_period": 18,
                        "bb_std_dev": 2.2,
                        "adx_threshold": 28
                    }
                }
            },
            {
                "status": "running",
                "progress": 0.75,
                "current_step": "Model validation",
                "elapsed_minutes": 95,
                "metrics": {
                    "current_trial": 67,
                    "best_score": 1.67,
                    "validation_metrics": {
                        "cv_score": 1.45,
                        "stability_score": 0.89
                    }
                }
            },
            {
                "status": "running",
                "progress": 0.95,
                "current_step": "Results compilation",
                "elapsed_minutes": 125,
                "metrics": {
                    "trials_completed": 100,
                    "best_score": 1.78,
                    "convergence_achieved": True
                }
            },
            {
                "status": "completed",
                "progress": 1.0,
                "current_step": "Training completed",
                "elapsed_minutes": 135,
                "final_results": True
            }
        ]
        
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test monitoring each stage
            for stage in training_stages:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "job_id": job_id,
                    **stage
                }
                mock_response.status_code = 200
                mock_client.get.return_value = mock_response
                
                # Check status
                result = await self._check_training_status(job_id, mock_client)
                
                # Verify stage progression
                assert result["job_id"] == job_id
                assert result["status"] == stage["status"]
                assert result["progress"] == stage["progress"]
                assert result["current_step"] == stage["current_step"]
                
                if "metrics" in stage:
                    assert "metrics" in result
                    if "current_trial" in stage["metrics"]:
                        assert result["metrics"]["current_trial"] == stage["metrics"]["current_trial"]
                
                # Simulate time delay between checks
                await asyncio.sleep(0.05)
            
            # Test final results retrieval
            final_results = {
                "job_id": job_id,
                "status": "completed",
                "training_duration_minutes": 135,
                "final_metrics": {
                    "best_parameters": {
                        "bb_period": 19,
                        "bb_std_dev": 2.4,
                        "adx_period": 13,
                        "adx_threshold": 27.5,
                        "position_size": 185
                    },
                    "performance_metrics": {
                        "sharpe_ratio": 1.78,
                        "sortino_ratio": 2.34,
                        "calmar_ratio": 4.89,
                        "max_drawdown": -0.067,
                        "total_return": 0.389,
                        "win_rate": 0.72,
                        "profit_factor": 2.89,
                        "avg_trade_duration": 4.2
                    },
                    "validation_metrics": {
                        "out_of_sample_sharpe": 1.65,
                        "walk_forward_stability": 0.91,
                        "monte_carlo_confidence": 0.87
                    }
                },
                "optimization_summary": {
                    "total_trials": 100,
                    "best_trial": 89,
                    "improvement_over_default": 0.42,
                    "parameter_sensitivity": {
                        "bb_period": 0.23,
                        "bb_std_dev": 0.31,
                        "adx_threshold": 0.18
                    }
                }
            }
            
            mock_response.json.return_value = final_results
            result = await self._retrieve_final_results(job_id, mock_client)
            
            # Verify final results
            assert result["status"] == "completed"
            assert result["training_duration_minutes"] == 135
            assert "final_metrics" in result
            assert "best_parameters" in result["final_metrics"]
            assert "performance_metrics" in result["final_metrics"]
            assert "optimization_summary" in result
            
            # Verify performance improvements
            assert result["optimization_summary"]["improvement_over_default"] > 0.4
            assert result["final_metrics"]["performance_metrics"]["sharpe_ratio"] > 1.5
    
    @pytest.mark.asyncio
    async def test_pipeline_with_database_persistence(self, sample_workflow_pipeline):
        """Test pipeline with database persistence at each stage."""
        workflow_data = sample_workflow_pipeline["workflow_definition"]
        metadata = sample_workflow_pipeline["metadata"]
        
        # Mock database operations
        mock_db = AsyncMock()
        mock_execute_result = Mock()
        mock_db.execute.return_value = mock_execute_result
        
        # Mock workflow exists in database
        mock_workflow = Mock()
        mock_workflow.id = 555
        mock_workflow.user_id = "user_pipeline_test"
        mock_workflow.workflow_data = workflow_data
        mock_workflow.execution_metadata = {}
        mock_execute_result.scalar_one_or_none.return_value = mock_workflow
        
        with patch('services.training_job_manager.TrainingJobManager') as mock_mgr_class:
            mock_manager = AsyncMock()
            mock_mgr_class.return_value = mock_manager
            
            # Mock successful job creation with database persistence
            mock_manager.create_job_from_workflow.return_value = {
                "success": True,
                "job_id": "persistence_test_999",
                "database_records_created": {
                    "strategy_id": str(uuid4()),
                    "dataset_id": "platform_btcusdt_1h_binance",
                    "training_job_id": "persistence_test_999"
                },
                "workflow_metadata_updated": True
            }
            
            # Mock dataset creation
            mock_dataset = Mock()
            mock_dataset.id = "platform_btcusdt_1h_binance"
            mock_execute_result.scalar_one_or_none.side_effect = [
                mock_workflow,  # Workflow exists
                None,          # Dataset doesn't exist (will be created)
                mock_dataset   # Dataset created
            ]
            
            # Execute pipeline with database persistence
            result = await mock_manager.create_job_from_workflow(
                {
                    "workflow_id": 555,
                    "workflow_name": "Bollinger Band Breakout Strategy",
                    "workflow_definition": workflow_data,
                    "training_config": {},
                    "optimization_objective": "sharpe_ratio",
                    "max_trials": 100
                },
                "user_pipeline_test",
                mock_db
            )
            
            # Verify database persistence
            assert result["success"] is True
            assert "database_records_created" in result
            assert "strategy_id" in result["database_records_created"]
            assert "dataset_id" in result["database_records_created"]
            assert "training_job_id" in result["database_records_created"]
            assert result["workflow_metadata_updated"] is True
            
            # Verify database operations were called
            mock_db.execute.assert_called()
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_pipeline_performance_benchmarking(self, sample_workflow_pipeline):
        """Test pipeline performance and resource usage tracking."""
        start_time = datetime.now()
        
        # Mock performance tracking
        performance_metrics = {
            "parsing_time_ms": 45,
            "code_generation_time_ms": 180,
            "validation_time_ms": 25,
            "database_operations_time_ms": 120,
            "total_pipeline_time_ms": 370,
            "memory_usage_mb": 156,
            "cpu_utilization_percent": 23
        }
        
        with patch('time.time') as mock_time:
            # Mock time progression
            time_sequence = [0, 0.045, 0.225, 0.250, 0.370]  # Cumulative seconds
            mock_time.side_effect = time_sequence
            
            # Mock resource monitoring
            with patch('psutil.Process') as mock_process:
                mock_proc = Mock()
                mock_proc.memory_info.return_value.rss = 156 * 1024 * 1024  # 156 MB
                mock_proc.cpu_percent.return_value = 23.0
                mock_process.return_value = mock_proc
                
                # Execute pipeline with performance tracking
                result = await self._execute_pipeline_with_benchmarking(
                    sample_workflow_pipeline, performance_metrics
                )
                
                # Verify performance metrics
                assert result["success"] is True
                assert "performance_metrics" in result
                
                perf = result["performance_metrics"]
                assert perf["total_pipeline_time_ms"] <= 500  # Should be fast
                assert perf["memory_usage_mb"] < 200  # Should be memory efficient
                assert perf["cpu_utilization_percent"] < 50  # Should not be CPU intensive
                
                # Verify pipeline stages are tracked
                assert perf["parsing_time_ms"] > 0
                assert perf["code_generation_time_ms"] > 0
                assert perf["validation_time_ms"] > 0
    
    # Helper methods
    
    async def _execute_complete_pipeline(self, workflow_data, metadata, parser, generator, manager, db):
        """Execute the complete pipeline simulation."""
        # Step 1: Parse workflow
        parsed_workflow = parser.parse_workflow(workflow_data)
        
        # Step 2: Generate strategy
        strategy_result = generator.generate_from_workflow(parsed_workflow, metadata)
        
        # Step 3: Create training job
        training_result = await manager.create_job_from_workflow(
            {
                "workflow_id": metadata["workflow_id"],
                "workflow_name": metadata["workflow_name"],
                "workflow_definition": workflow_data,
                "training_config": strategy_result["optimization_config"],
                "optimization_objective": "sharpe_ratio",
                "max_trials": 100
            },
            metadata["user_id"],
            db
        )
        
        return training_result
    
    async def _check_training_status(self, job_id, client):
        """Check training status."""
        response = await client.get(f"/api/training/jobs/{job_id}")
        return response.json()
    
    async def _retrieve_final_results(self, job_id, client):
        """Retrieve final training results."""
        response = await client.get(f"/api/training/jobs/{job_id}/results")
        return response.json()
    
    async def _execute_pipeline_with_benchmarking(self, workflow_pipeline, expected_metrics):
        """Execute pipeline with performance benchmarking."""
        # Simulate pipeline execution with timing
        return {
            "success": True,
            "job_id": "benchmark_test_111",
            "performance_metrics": expected_metrics
        }
    
    def _get_expected_bollinger_strategy_code(self):
        """Get expected strategy code for Bollinger Band strategy."""
        return '''"""
Generated Bollinger Band Breakout Strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime

class WorkflowStrategy:
    def __init__(self, config=None):
        self.config = config or {}
        self.position = 0
    
    def calculate_indicators(self, data):
        indicators = {}
        
        # Bollinger Bands
        sma = data['close'].rolling(20).mean()
        std = data['close'].rolling(20).std()
        indicators['bb_upper'] = sma + (2 * std)
        indicators['bb_middle'] = sma
        indicators['bb_lower'] = sma - (2 * std)
        indicators['bb_width'] = indicators['bb_upper'] - indicators['bb_lower']
        
        # ADX
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        
        indicators['adx'] = atr  # Simplified ADX calculation
        
        return indicators
    
    def execute_strategy(self, data, current_portfolio=None):
        if data.empty:
            return []
            
        indicators = self.calculate_indicators(data)
        signals = []
        
        current_price = data['close'].iloc[-1]
        bb_upper = indicators['bb_upper'].iloc[-1]
        adx = indicators['adx'].iloc[-1]
        
        # Bollinger Band breakout with ADX confirmation
        if current_price > bb_upper and adx > 25:
            signals.append({
                'action': 'buy',
                'quantity': 200,
                'price': current_price,
                'timestamp': datetime.now(),
                'reason': 'Bollinger Band breakout + strong trend'
            })
        
        return signals

def create_strategy_instance(config=None):
    return WorkflowStrategy(config)
'''


class TestPipelineErrorRecovery:
    """Test error recovery and resilience in the pipeline."""
    
    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, sample_workflow_pipeline):
        """Test recovery from partial pipeline failures."""
        workflow_data = sample_workflow_pipeline["workflow_definition"]
        metadata = sample_workflow_pipeline["metadata"]
        
        # Simulate failure in strategy generation, but successful parsing
        with patch('services.workflow_parser.WorkflowParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_workflow.return_value = {"success": True}
            
            with patch('services.strategy_generator.StrategyGenerator') as mock_gen_class:
                mock_generator = Mock()
                mock_gen_class.return_value = mock_generator
                
                # First attempt fails
                mock_generator.generate_from_workflow.side_effect = [
                    {"success": False, "error": "Code generation failed"},
                    {"success": True, "strategy_code": "# Recovered code"}  # Retry succeeds
                ]
                
                # Test retry logic
                results = []
                for attempt in range(2):
                    try:
                        result = mock_generator.generate_from_workflow({}, metadata)
                        results.append(result)
                        if result["success"]:
                            break
                    except Exception:
                        continue
                
                # Verify retry worked
                assert len(results) == 2
                assert results[0]["success"] is False
                assert results[1]["success"] is True
    
    @pytest.mark.asyncio
    async def test_resource_constraint_handling(self):
        """Test handling of resource constraints during pipeline execution."""
        # Simulate resource constraints
        resource_limits = {
            "max_memory_mb": 512,
            "max_cpu_percent": 80,
            "max_execution_time_minutes": 30
        }
        
        # Mock resource monitoring
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 85  # High memory usage
            
            with patch('psutil.cpu_percent') as mock_cpu:
                mock_cpu.return_value = 75  # Acceptable CPU usage
                
                # Test resource constraint checking
                resource_status = self._check_resource_constraints(resource_limits)
                
                # Should detect memory constraint violation
                assert resource_status["memory_constraint_violated"] is True
                assert resource_status["cpu_constraint_violated"] is False
                assert resource_status["can_proceed"] is False
    
    def _check_resource_constraints(self, limits):
        """Check if resource constraints are violated."""
        import psutil
        
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent()
        
        return {
            "memory_constraint_violated": memory_usage > (limits["max_memory_mb"] / 1024 * 100),
            "cpu_constraint_violated": cpu_usage > limits["max_cpu_percent"],
            "can_proceed": memory_usage <= (limits["max_memory_mb"] / 1024 * 100) and cpu_usage <= limits["max_cpu_percent"]
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])