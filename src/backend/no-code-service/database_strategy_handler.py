#!/usr/bin/env python3
"""
Database-Only Enhanced Strategy Handler

This handler saves generated strategy code directly to the database
instead of files, eliminating the need for file-based storage.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from enhanced_code_generator import EnhancedCodeGenerator, OutputMode
from models import NoCodeWorkflow, ExecutionHistory
from sqlalchemy.orm import Session
from clients.backtest_client import BacktestClient, BacktestServiceError, BacktestServiceUnavailable


class DatabaseStrategyHandler:
    """Enhanced handler that saves strategy code directly to database"""
    
    def __init__(self):
        self.compiler = EnhancedCodeGenerator()
        self.backtest_client = BacktestClient()
        
    def execute_strategy_mode(self,
                             workflow: NoCodeWorkflow,
                             execution_config: Dict[str, Any],
                             user_id: int,
                             db: Session) -> Dict[str, Any]:
        """
        Execute workflow in strategy mode using Enhanced Compiler
        Save generated code directly to database (no files)
        
        Args:
            workflow: NoCodeWorkflow database object
            execution_config: Configuration from frontend
            user_id: ID of the user executing the strategy
            db: Database session
            
        Returns:
            Dictionary with execution results and database storage info
        """
        
        # Generate unique execution ID
        execution_id = str(uuid.uuid4())
        
        try:
            # Step 1: Compile workflow using Enhanced Compiler
            compilation_result = self.compiler.compile_workflow(
                workflow.workflow_data or {"nodes": [], "edges": []},
                OutputMode.BACKTESTING,  # Default to backtesting for strategy mode
                optimization_level=execution_config.get('optimization_level', 2)
            )
            
            if not compilation_result['success']:
                return {
                    'success': False,
                    'execution_id': execution_id,
                    'error': 'Compilation failed',
                    'details': {
                        'errors': compilation_result.get('errors', []),
                        'warnings': compilation_result.get('warnings', [])
                    }
                }
            
            # Step 2: Calculate code metrics
            generated_code = compilation_result['code']
            code_lines = len(generated_code.split('\n'))
            code_size = len(generated_code.encode('utf-8'))
            
            # Step 3: Update workflow in database with generated code
            self._update_workflow_with_strategy(
                workflow, 
                compilation_result, 
                code_lines,
                code_size,
                db
            )
            
            # Step 4: Create execution record in database (optional - main storage is in workflow)
            try:
                execution_record = self._create_execution_record(
                    workflow,
                    execution_id,
                    execution_config,
                    compilation_result,
                    code_lines,
                    code_size,
                    user_id,
                    db
                )
            except Exception as e:
                # If execution history fails, continue - strategy is still saved in workflow
                print(f"Warning: Could not save execution history: {e}")
                execution_record = None
            
            # Step 5: Automatically run backtest after code generation
            backtest_result = None
            try:
                # Prepare backtest configuration with sensible defaults
                backtest_config = {
                    'start_date': execution_config.get('backtest_start', '2023-01-01'),
                    'end_date': execution_config.get('backtest_end', '2023-12-31'),
                    'initial_capital': execution_config.get('initial_capital', 10000.0),
                    'commission': execution_config.get('commission', 0.001),
                    'symbols': execution_config.get('symbols', ['AAPL']),
                    'timeframe': execution_config.get('timeframe', '1h')
                }
                
                print(f"Auto-running backtest for workflow {workflow.id} with config: {backtest_config}")
                
                # Call backtest service - use the sync wrapper method
                backtest_result = self.backtest_client.run_backtest_sync(
                    workflow_id=str(workflow.uuid),
                    strategy_code=compilation_result['code'],
                    config=backtest_config,
                    metadata={
                        'workflow_name': workflow.name,
                        'auto_generated': True,
                        'compilation_status': 'success',
                        'compiler_version': 'Enhanced v2.0',
                        'generated_code_lines': code_lines,
                        'generated_code_size': code_size
                    }
                )
                
                if backtest_result.get('success'):
                    # Save backtest execution record
                    backtest_execution = ExecutionHistory(
                        uuid=backtest_result['execution_id'],
                        workflow_id=workflow.id,
                        execution_mode='backtest',
                        status='completed',
                        execution_config=backtest_config,
                        results=backtest_result,
                        generated_code=compilation_result['code'],
                        generated_requirements=compilation_result.get('requirements', []),
                        compilation_stats={
                            'auto_backtest': True,
                            'backtest_service_execution': True,
                            'execution_time': datetime.utcnow().isoformat(),
                            'service_url': self.backtest_client.base_url
                        },
                        created_at=datetime.utcnow(),
                        completed_at=datetime.utcnow()
                    )
                    
                    try:
                        db.add(backtest_execution)
                        db.commit()
                        print(f"Backtest results saved for workflow {workflow.id}")
                        
                        # Update workflow stats
                        workflow.total_executions = (workflow.total_executions or 0) + 1
                        if backtest_result.get('performance_metrics', {}).get('total_return_percent', 0) > 0:
                            workflow.successful_executions = (workflow.successful_executions or 0) + 1
                        workflow.last_execution_at = datetime.utcnow()
                        db.commit()
                        
                    except Exception as db_error:
                        print(f"Warning: Failed to save backtest execution: {db_error}")
                        db.rollback()
                
                else:
                    print(f"Auto-backtest failed: {backtest_result.get('error', 'Unknown error')}")
                    
            except (BacktestServiceUnavailable, BacktestServiceError) as e:
                print(f"Backtest service error: {str(e)}")
                # Continue with strategy generation success even if backtest fails
                
            except Exception as e:
                print(f"Unexpected backtest error: {str(e)}")
                # Continue with strategy generation success even if backtest fails
            
            # Step 6: Prepare response
            response = {
                'success': True,
                'execution_id': execution_id,
                'message': 'Strategy generated and saved to database successfully',
                'strategy_details': {
                    'workflow_id': workflow.id,
                    'workflow_uuid': str(workflow.uuid),
                    'code_lines': code_lines,
                    'code_size_bytes': code_size,
                    'requirements': compilation_result['requirements'],
                    'compilation_stats': {
                        'nodes_processed': compilation_result.get('nodes_processed', 0),
                        'edges_processed': compilation_result.get('edges_processed', 0),
                        'optimizations_applied': compilation_result.get('optimizations_applied', 0)
                    },
                    'storage': 'database',
                    'compiler_version': 'Enhanced v2.0'
                },
                'execution_record_id': execution_record.id if execution_record else None,
                'database_storage': {
                    'workflow_table': 'nocode_workflows.generated_code',
                    'execution_table': 'execution_history.generated_code',
                    'stored_at': datetime.utcnow().isoformat()
                }
            }
            
            # Include backtest results if available
            if backtest_result and backtest_result.get('success'):
                response['auto_backtest'] = {
                    'success': True,
                    'execution_id': backtest_result['execution_id'],
                    'performance_metrics': backtest_result.get('performance_metrics', {}),
                    'trade_summary': backtest_result.get('trade_summary', {}),
                    'market_data_stats': backtest_result.get('market_data_stats', {}),
                    'message': 'Backtest completed automatically after code generation'
                }
            elif backtest_result:
                response['auto_backtest'] = {
                    'success': False,
                    'error': backtest_result.get('error', 'Backtest failed'),
                    'message': 'Auto-backtest failed but strategy generation succeeded'
                }
            else:
                response['auto_backtest'] = {
                    'success': False,
                    'error': 'Backtest service unavailable',
                    'message': 'Auto-backtest skipped due to service unavailability'
                }
            
            return response
            
        except Exception as e:
            # Handle any errors
            return {
                'success': False,
                'execution_id': execution_id,
                'error': f'Strategy execution failed: {str(e)}',
                'details': {'exception_type': type(e).__name__}
            }
    
    def _update_workflow_with_strategy(self, 
                                     workflow: NoCodeWorkflow,
                                     compilation_result: Dict[str, Any],
                                     code_lines: int,
                                     code_size: int,
                                     db: Session):
        """Update workflow with strategy compilation results in database"""
        
        # Update workflow fields with generated code
        workflow.generated_code = compilation_result['code']
        workflow.generated_requirements = compilation_result.get('requirements', [])
        workflow.generated_code_lines = code_lines
        workflow.generated_code_size = code_size
        workflow.compiler_version = 'Enhanced v2.0'
        workflow.compilation_status = 'success' if compilation_result['success'] else 'failed'
        workflow.compilation_errors = compilation_result.get('errors', [])
        workflow.execution_mode = 'strategy'
        workflow.updated_at = datetime.utcnow()
        
        # Add strategy metadata to execution metadata
        if not workflow.execution_metadata:
            workflow.execution_metadata = {}
        
        workflow.execution_metadata.update({
            'last_strategy_generation': datetime.utcnow().isoformat(),
            'compiler_version': 'Enhanced v2.0',
            'storage_type': 'database',
            'code_metrics': {
                'lines': code_lines,
                'size_bytes': code_size,
                'requirements_count': len(compilation_result.get('requirements', []))
            }
        })
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
    
    def _create_execution_record(self,
                               workflow: NoCodeWorkflow,
                               execution_id: str,
                               execution_config: Dict[str, Any],
                               compilation_result: Dict[str, Any],
                               code_lines: int,
                               code_size: int,
                               user_id: int,
                               db: Session) -> Optional[ExecutionHistory]:
        """Create execution record in database"""
        
        try:
            execution_record = ExecutionHistory(
                uuid=execution_id,  # Using uuid field
                workflow_id=workflow.id,
                user_id=user_id,
                execution_mode='strategy',
                status='completed' if compilation_result['success'] else 'failed',
                execution_config=execution_config,
                results={
                    'compilation_success': compilation_result['success'],
                    'code_metrics': {
                        'lines': code_lines,
                        'size_bytes': code_size
                    },
                    'storage_location': 'database',
                    'generated_at': datetime.utcnow().isoformat()
                },
                # Store generated code in execution history as well
                generated_code=compilation_result['code'],
                generated_requirements=compilation_result.get('requirements', []),
                compilation_stats={
                    'nodes_processed': compilation_result.get('nodes_processed', 0),
                    'edges_processed': compilation_result.get('edges_processed', 0),
                    'optimizations_applied': compilation_result.get('optimizations_applied', 0)
                },
                error_logs=compilation_result.get('errors', []) if not compilation_result['success'] else [],
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow() if compilation_result['success'] else None
            )
            
            db.add(execution_record)
            db.commit()
            
            return execution_record
            
        except Exception as e:
            # If execution history table doesn't exist, continue without it
            # The strategy is still saved in the workflow table
            db.rollback()
            print(f"Warning: Could not save execution history: {e}")
            return None
    
    def get_strategy_from_database(self, 
                                 workflow_id: int, 
                                 db: Session,
                                 include_code: bool = True) -> Dict[str, Any]:
        """Get strategy details from database"""
        
        try:
            # Get workflow with generated code
            workflow = db.query(NoCodeWorkflow).filter(
                NoCodeWorkflow.id == workflow_id
            ).first()
            
            if not workflow:
                return {'success': False, 'error': 'Workflow not found'}
            
            # Get latest execution record if available
            latest_execution = None
            try:
                latest_execution = db.query(ExecutionHistory).filter(
                    ExecutionHistory.workflow_id == workflow.id,
                    ExecutionHistory.execution_mode == 'strategy'
                ).order_by(ExecutionHistory.created_at.desc()).first()
            except:
                pass  # Table might not exist yet
            
            response = {
                'success': True,
                'workflow': {
                    'id': workflow.id,
                    'uuid': str(workflow.uuid),
                    'name': workflow.name,
                    'compilation_status': workflow.compilation_status,
                    'requirements': workflow.generated_requirements or [],
                    'code_metrics': {
                        'lines': getattr(workflow, 'generated_code_lines', 0),
                        'size_bytes': getattr(workflow, 'generated_code_size', 0)
                    },
                    'compiler_version': getattr(workflow, 'compiler_version', 'Unknown'),
                    'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else None
                },
                'storage': {
                    'type': 'database',
                    'location': 'nocode_workflows.generated_code',
                    'has_code': bool(workflow.generated_code)
                }
            }
            
            # Include generated code if requested
            if include_code and workflow.generated_code:
                response['generated_code'] = workflow.generated_code
            
            # Include execution details if available
            if latest_execution:
                response['latest_execution'] = {
                    'execution_id': str(latest_execution.uuid),
                    'status': latest_execution.status,
                    'created_at': latest_execution.created_at.isoformat(),
                    'compilation_stats': latest_execution.compilation_stats or {}
                }
            
            return response
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to retrieve strategy: {str(e)}'
            }
    
    def list_user_strategies(self, user_id: int, db: Session) -> Dict[str, Any]:
        """List all generated strategies for a user (from database)"""
        
        try:
            # Get all workflows for user with generated code
            workflows = db.query(NoCodeWorkflow).filter(
                NoCodeWorkflow.user_id == user_id,
                NoCodeWorkflow.generated_code.isnot(None)
            ).all()
            
            strategies = []
            for workflow in workflows:
                strategy_info = {
                    'workflow_id': workflow.id,
                    'workflow_uuid': str(workflow.uuid),
                    'name': workflow.name,
                    'compilation_status': workflow.compilation_status,
                    'requirements': workflow.generated_requirements or [],
                    'code_metrics': {
                        'lines': getattr(workflow, 'generated_code_lines', 0),
                        'size_bytes': getattr(workflow, 'generated_code_size', 0)
                    },
                    'compiler_version': getattr(workflow, 'compiler_version', 'Unknown'),
                    'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else None,
                    'storage': 'database'
                }
                strategies.append(strategy_info)
            
            return {
                'success': True,
                'strategies': strategies,
                'total_count': len(strategies),
                'storage_info': {
                    'type': 'database',
                    'total_strategies': len(strategies),
                    'total_code_size': sum(s['code_metrics']['size_bytes'] for s in strategies)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to list strategies: {str(e)}'
            }


# Convenience functions for main.py integration
def execute_database_strategy_mode(workflow: NoCodeWorkflow, 
                                 execution_config: Dict[str, Any],
                                 db: Session) -> Dict[str, Any]:
    """Convenience function for main.py integration"""
    handler = DatabaseStrategyHandler()
    return handler.execute_strategy_mode(workflow, execution_config, db)


def get_strategy_from_database(workflow_id: int, 
                             db: Session,
                             include_code: bool = True) -> Dict[str, Any]:
    """Convenience function to get strategy from database"""
    handler = DatabaseStrategyHandler()
    return handler.get_strategy_from_database(workflow_id, db, include_code)


if __name__ == "__main__":
    # Demo usage
    print("🗄️  Database Strategy Handler")
    print("=" * 50)
    print("This handler saves generated strategy code directly to the database.")
    print("\nFeatures:")
    print("✅ Database-only storage (no files)")
    print("✅ Enhanced Compiler integration")
    print("✅ Code metrics tracking")
    print("✅ Execution history (when table exists)")
    print("✅ Strategy retrieval and listing")
    print("✅ Backward compatibility")
    print("\nReady for database-only strategy generation! 🎉")