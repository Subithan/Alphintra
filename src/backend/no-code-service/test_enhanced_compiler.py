"""Test suite for the Enhanced Code Generator.

This module demonstrates the enhanced compiler's capabilities with
comprehensive test cases covering various workflow scenarios.
"""

import json
import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_code_generator import EnhancedCodeGenerator, OutputMode, DataType
from enhanced_node_handlers import ENHANCED_HANDLER_REGISTRY


def create_test_workflow():
    """Create a comprehensive test workflow."""
    return {
        "nodes": [
            {
                "id": "dataSource-1",
                "type": "dataSource",
                "position": {"x": 100, "y": 100},
                "data": {
                    "label": "AAPL Data",
                    "parameters": {
                        "symbol": "AAPL",
                        "timeframe": "1h",
                        "bars": 1000,
                        "dataSource": "system",
                        "assetClass": "stocks"
                    }
                }
            },
            {
                "id": "technicalIndicator-1",
                "type": "technicalIndicator",
                "position": {"x": 300, "y": 100},
                "data": {
                    "label": "RSI",
                    "parameters": {
                        "indicatorCategory": "momentum",
                        "indicator": "RSI",
                        "period": 14,
                        "source": "close"
                    }
                }
            },
            {
                "id": "technicalIndicator-2",
                "type": "technicalIndicator",
                "position": {"x": 300, "y": 250},
                "data": {
                    "label": "SMA 20",
                    "parameters": {
                        "indicatorCategory": "trend",
                        "indicator": "SMA",
                        "period": 20,
                        "source": "close"
                    }
                }
            },
            {
                "id": "condition-1",
                "type": "condition",
                "position": {"x": 500, "y": 100},
                "data": {
                    "label": "RSI Oversold",
                    "parameters": {
                        "conditionType": "comparison",
                        "condition": "less_than",
                        "value": 30,
                        "lookback": 1,
                        "confirmationBars": 2
                    }
                }
            },
            {
                "id": "condition-2",
                "type": "condition",
                "position": {"x": 500, "y": 250},
                "data": {
                    "label": "Price Above SMA",
                    "parameters": {
                        "conditionType": "crossover",
                        "condition": "crossover",
                        "value": 0,
                        "lookback": 1
                    }
                }
            },
            {
                "id": "logic-1",
                "type": "logic",
                "position": {"x": 700, "y": 175},
                "data": {
                    "label": "AND Gate",
                    "parameters": {
                        "operation": "AND",
                        "inputs": 2
                    }
                }
            },
            {
                "id": "riskManagement-1",
                "type": "riskManagement",
                "position": {"x": 700, "y": 350},
                "data": {
                    "label": "Position Risk",
                    "parameters": {
                        "riskCategory": "position",
                        "riskType": "position_size",
                        "riskLevel": 2,
                        "maxLoss": 2.0,
                        "portfolioHeat": 10.0
                    }
                }
            },
            {
                "id": "action-1",
                "type": "action",
                "position": {"x": 900, "y": 175},
                "data": {
                    "label": "Buy Order",
                    "parameters": {
                        "actionCategory": "entry",
                        "action": "buy",
                        "quantity": 100,
                        "order_type": "market",
                        "positionSizing": "percentage",
                        "stop_loss": 2,
                        "take_profit": 6
                    }
                }
            }
        ],
        "edges": [
            {
                "id": "edge-1",
                "source": "dataSource-1",
                "target": "technicalIndicator-1",
                "sourceHandle": "data-output",
                "targetHandle": "data-input",
                "type": "smart",
                "data": {
                    "sourceHandle": "data-output",
                    "targetHandle": "data-input",
                    "rule": {
                        "dataType": "ohlcv",
                        "label": "Market Data"
                    }
                }
            },
            {
                "id": "edge-2",
                "source": "dataSource-1",
                "target": "technicalIndicator-2",
                "sourceHandle": "data-output", 
                "targetHandle": "data-input",
                "type": "smart",
                "data": {
                    "sourceHandle": "data-output",
                    "targetHandle": "data-input",
                    "rule": {
                        "dataType": "ohlcv",
                        "label": "Market Data"
                    }
                }
            },
            {
                "id": "edge-3",
                "source": "technicalIndicator-1",
                "target": "condition-1",
                "sourceHandle": "output-1",
                "targetHandle": "data-input",
                "type": "smart",
                "data": {
                    "sourceHandle": "output-1",
                    "targetHandle": "data-input",
                    "rule": {
                        "dataType": "numeric",
                        "label": "RSI Value"
                    }
                }
            },
            {
                "id": "edge-4",
                "source": "technicalIndicator-2",
                "target": "condition-2",
                "sourceHandle": "output-1",
                "targetHandle": "data-input",
                "type": "smart",
                "data": {
                    "sourceHandle": "output-1",
                    "targetHandle": "data-input",
                    "rule": {
                        "dataType": "numeric",
                        "label": "SMA Value"
                    }
                }
            },
            {
                "id": "edge-5",
                "source": "condition-1",
                "target": "logic-1",
                "sourceHandle": "signal-output",
                "targetHandle": "input-0",
                "type": "smart",
                "data": {
                    "sourceHandle": "signal-output",
                    "targetHandle": "input-0",
                    "rule": {
                        "dataType": "signal",
                        "label": "RSI Signal"
                    }
                }
            },
            {
                "id": "edge-6",
                "source": "condition-2",
                "target": "logic-1",
                "sourceHandle": "signal-output",
                "targetHandle": "input-1",
                "type": "smart",
                "data": {
                    "sourceHandle": "signal-output",
                    "targetHandle": "input-1",
                    "rule": {
                        "dataType": "signal",
                        "label": "SMA Signal"
                    }
                }
            },
            {
                "id": "edge-7",
                "source": "logic-1",
                "target": "action-1",
                "sourceHandle": "output",
                "targetHandle": "signal-input",
                "type": "smart",
                "data": {
                    "sourceHandle": "output",
                    "targetHandle": "signal-input",
                    "rule": {
                        "dataType": "signal",
                        "label": "Combined Signal"
                    }
                }
            },
            {
                "id": "edge-8",
                "source": "dataSource-1",
                "target": "riskManagement-1",
                "sourceHandle": "data-output",
                "targetHandle": "data-input",
                "type": "smart",
                "data": {
                    "sourceHandle": "data-output",
                    "targetHandle": "data-input",
                    "rule": {
                        "dataType": "ohlcv",
                        "label": "Price Data"
                    }
                }
            }
        ],
        "config": {
            "model": {
                "type": "random_forest",
                "hyperparameters": {
                    "n_estimators": 100,
                    "max_depth": 10,
                    "random_state": 42
                }
            }
        }
    }


def test_training_mode():
    """Test training mode compilation."""
    print("=" * 60)
    print("TESTING TRAINING MODE")
    print("=" * 60)
    
    # Create enhanced generator with enhanced handlers
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    workflow = create_test_workflow()
    
    result = generator.compile_workflow(
        workflow, 
        output_mode=OutputMode.TRAINING,
        optimization_level=2
    )
    
    print(f"Compilation Success: {result['success']}")
    print(f"Code Type: {result['code_type']}")
    print(f"Nodes Processed: {result['metadata']['nodes_processed']}")
    print(f"Edges Processed: {result['metadata']['edges_processed']}")
    print(f"Optimizations Applied: {result['metadata']['optimizations_applied']}")
    
    if result['errors']:
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error['node_id']}: {error['message']}")
    
    if result['warnings']:
        print("\nWarnings:")
        for warning in result['warnings']:
            print(f"  - {warning['node_id']}: {warning['message']}")
    
    print(f"\nRequirements: {', '.join(result['requirements'])}")
    
    # Save generated code
    with open("/workspace/src/backend/no-code-service/generated_training.py", "w") as f:
        f.write(result['code'])
    
    print("\nGenerated training code saved to generated_training.py")
    
    return result


def test_backtesting_mode():
    """Test backtesting mode compilation."""
    print("\n" + "=" * 60)
    print("TESTING BACKTESTING MODE")
    print("=" * 60)
    
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    workflow = create_test_workflow()
    
    result = generator.compile_workflow(
        workflow,
        output_mode=OutputMode.BACKTESTING,
        optimization_level=1
    )
    
    print(f"Compilation Success: {result['success']}")
    print(f"Code Type: {result['code_type']}")
    
    # Save generated code
    with open("/workspace/src/backend/no-code-service/generated_backtest.py", "w") as f:
        f.write(result['code'])
    
    print("Generated backtesting code saved to generated_backtest.py")
    
    return result


def test_live_trading_mode():
    """Test live trading mode compilation."""
    print("\n" + "=" * 60)
    print("TESTING LIVE TRADING MODE")
    print("=" * 60)
    
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    workflow = create_test_workflow()
    
    result = generator.compile_workflow(
        workflow,
        output_mode=OutputMode.LIVE_TRADING,
        optimization_level=1
    )
    
    print(f"Compilation Success: {result['success']}")
    print(f"Code Type: {result['code_type']}")
    
    # Save generated code
    with open("/workspace/src/backend/no-code-service/generated_live.py", "w") as f:
        f.write(result['code'])
    
    print("Generated live trading code saved to generated_live.py")
    
    return result


def test_research_mode():
    """Test research mode compilation."""
    print("\n" + "=" * 60)
    print("TESTING RESEARCH MODE")
    print("=" * 60)
    
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    workflow = create_test_workflow()
    
    result = generator.compile_workflow(
        workflow,
        output_mode=OutputMode.RESEARCH,
        optimization_level=0
    )
    
    print(f"Compilation Success: {result['success']}")
    print(f"Code Type: {result['code_type']}")
    
    # Save generated code
    with open("/workspace/src/backend/no-code-service/generated_research.py", "w") as f:
        f.write(result['code'])
    
    print("Generated research code saved to generated_research.py")
    
    return result


def test_error_handling():
    """Test error handling with invalid workflow."""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    # Create workflow with errors
    invalid_workflow = {
        "nodes": [
            {
                "id": "condition-1",
                "type": "condition",
                "data": {
                    "label": "Orphaned Condition",
                    "parameters": {
                        "condition": "greater_than",
                        "value": 50
                    }
                }
            },
            {
                "id": "action-1", 
                "type": "action",
                "data": {
                    "label": "Orphaned Action",
                    "parameters": {
                        "action": "buy"
                    }
                }
            }
        ],
        "edges": [
            {
                "id": "invalid-edge",
                "source": "nonexistent-node",
                "target": "condition-1"
            }
        ]
    }
    
    result = generator.compile_workflow(invalid_workflow)
    
    print(f"Compilation Success: {result['success']}")
    print(f"Number of Errors: {len(result['errors'])}")
    print(f"Number of Warnings: {len(result['warnings'])}")
    
    if result['errors']:
        print("\nErrors Found:")
        for error in result['errors']:
            print(f"  - {error['type']}: {error['message']}")
    
    if result['warnings']:
        print("\nWarnings Found:")
        for warning in result['warnings']:
            print(f"  - {warning['type']}: {warning['message']}")
    
    return result


def test_optimization_levels():
    """Test different optimization levels."""
    print("\n" + "=" * 60)
    print("TESTING OPTIMIZATION LEVELS")
    print("=" * 60)
    
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    workflow = create_test_workflow()
    
    for opt_level in [0, 1, 2]:
        print(f"\nOptimization Level {opt_level}:")
        result = generator.compile_workflow(
            workflow,
            output_mode=OutputMode.TRAINING,
            optimization_level=opt_level
        )
        
        print(f"  Success: {result['success']}")
        print(f"  Optimizations Applied: {result['metadata']['optimizations_applied']}")
        print(f"  Code Lines: {len(result['code'].splitlines())}")


def test_complex_workflow():
    """Test a more complex workflow with multiple paths."""
    print("\n" + "=" * 60)
    print("TESTING COMPLEX WORKFLOW")
    print("=" * 60)
    
    complex_workflow = {
        "nodes": [
            # Data sources
            {
                "id": "dataSource-1",
                "type": "dataSource",
                "data": {
                    "label": "AAPL Data",
                    "parameters": {
                        "symbol": "AAPL",
                        "timeframe": "1h",
                        "bars": 1000
                    }
                }
            },
            {
                "id": "customDataset-1",
                "type": "customDataset",
                "data": {
                    "label": "Custom Data",
                    "parameters": {
                        "fileName": "custom_indicators.csv",
                        "dateColumn": "timestamp",
                        "columns": ["vix", "sentiment", "volume_profile"]
                    }
                }
            },
            # Technical indicators
            {
                "id": "technicalIndicator-1",
                "type": "technicalIndicator",
                "data": {
                    "label": "MACD",
                    "parameters": {
                        "indicator": "MACD",
                        "fastPeriod": 12,
                        "slowPeriod": 26,
                        "signalPeriod": 9
                    }
                }
            },
            {
                "id": "technicalIndicator-2",
                "type": "technicalIndicator",
                "data": {
                    "label": "Bollinger Bands",
                    "parameters": {
                        "indicator": "BB",
                        "period": 20,
                        "multiplier": 2
                    }
                }
            },
            {
                "id": "technicalIndicator-3",
                "type": "technicalIndicator",
                "data": {
                    "label": "ADX",
                    "parameters": {
                        "indicator": "ADX",
                        "period": 14
                    }
                }
            },
            # Multiple conditions
            {
                "id": "condition-1",
                "type": "condition",
                "data": {
                    "label": "MACD Crossover",
                    "parameters": {
                        "conditionType": "crossover",
                        "condition": "crossover",
                        "value": 0
                    }
                }
            },
            {
                "id": "condition-2",
                "type": "condition",
                "data": {
                    "label": "BB Squeeze",
                    "parameters": {
                        "conditionType": "comparison",
                        "condition": "less_than",
                        "value": 0.02
                    }
                }
            },
            {
                "id": "condition-3",
                "type": "condition",
                "data": {
                    "label": "Strong Trend",
                    "parameters": {
                        "conditionType": "comparison",
                        "condition": "greater_than",
                        "value": 25
                    }
                }
            },
            # Complex logic
            {
                "id": "logic-1",
                "type": "logic",
                "data": {
                    "label": "Entry Logic",
                    "parameters": {
                        "operation": "AND",
                        "inputs": 2
                    }
                }
            },
            {
                "id": "logic-2",
                "type": "logic",
                "data": {
                    "label": "Trend Filter",
                    "parameters": {
                        "operation": "OR",
                        "inputs": 2
                    }
                }
            },
            # Risk management
            {
                "id": "riskManagement-1",
                "type": "riskManagement",
                "data": {
                    "label": "Portfolio Risk",
                    "parameters": {
                        "riskCategory": "portfolio",
                        "riskType": "drawdown_limit",
                        "drawdownLimit": 15.0,
                        "emergencyAction": "reduce_positions"
                    }
                }
            },
            # Multiple actions
            {
                "id": "action-1",
                "type": "action",
                "data": {
                    "label": "Long Entry",
                    "parameters": {
                        "action": "buy",
                        "positionSizing": "percentage",
                        "quantity": 2,
                        "stop_loss": 3,
                        "take_profit": 9
                    }
                }
            },
            {
                "id": "action-2",
                "type": "action",
                "data": {
                    "label": "Short Entry",
                    "parameters": {
                        "action": "sell",
                        "positionSizing": "percentage",
                        "quantity": 1.5,
                        "stop_loss": 2,
                        "take_profit": 6
                    }
                }
            }
        ],
        "edges": [
            # Data flow
            {"source": "dataSource-1", "target": "technicalIndicator-1"},
            {"source": "dataSource-1", "target": "technicalIndicator-2"},
            {"source": "dataSource-1", "target": "technicalIndicator-3"},
            {"source": "customDataset-1", "target": "condition-2"},
            
            # Indicator to conditions
            {"source": "technicalIndicator-1", "target": "condition-1"},
            {"source": "technicalIndicator-2", "target": "condition-2"},
            {"source": "technicalIndicator-3", "target": "condition-3"},
            
            # Logic combinations
            {"source": "condition-1", "target": "logic-1"},
            {"source": "condition-2", "target": "logic-1"},
            {"source": "condition-3", "target": "logic-2"},
            {"source": "logic-1", "target": "logic-2"},
            
            # Actions
            {"source": "logic-2", "target": "action-1"},
            {"source": "logic-2", "target": "action-2"},
            
            # Risk management
            {"source": "dataSource-1", "target": "riskManagement-1"}
        ]
    }
    
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    result = generator.compile_workflow(
        complex_workflow,
        output_mode=OutputMode.BACKTESTING,
        optimization_level=2
    )
    
    print(f"Complex Workflow Compilation Success: {result['success']}")
    print(f"Nodes Processed: {result['metadata']['nodes_processed']}")
    print(f"Edges Processed: {result['metadata']['edges_processed']}")
    print(f"Generated Code Lines: {len(result['code'].splitlines())}")
    
    if result['errors']:
        print(f"Errors: {len(result['errors'])}")
        for error in result['errors'][:3]:  # Show first 3 errors
            print(f"  - {error['message']}")
    
    if result['warnings']:
        print(f"Warnings: {len(result['warnings'])}")
        for warning in result['warnings'][:3]:  # Show first 3 warnings
            print(f"  - {warning['message']}")
    
    # Save complex workflow code
    with open("/workspace/src/backend/no-code-service/generated_complex.py", "w") as f:
        f.write(result['code'])
    
    print("Complex workflow code saved to generated_complex.py")
    
    return result


def main():
    """Run all tests."""
    print("Enhanced Code Generator Test Suite")
    print("=" * 60)
    
    try:
        # Basic functionality tests
        test_training_mode()
        test_backtesting_mode()
        test_live_trading_mode()
        test_research_mode()
        
        # Advanced tests
        test_error_handling()
        test_optimization_levels()
        test_complex_workflow()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\nGenerated Files:")
        print("- generated_training.py (Training mode)")
        print("- generated_backtest.py (Backtesting mode)")
        print("- generated_live.py (Live trading mode)")
        print("- generated_research.py (Research mode)")
        print("- generated_complex.py (Complex workflow)")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)