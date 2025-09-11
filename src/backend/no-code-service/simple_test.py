#!/usr/bin/env python3
"""
Simple Test Script for Enhanced Compiler
Run this to test the compiler with your own workflows
"""

import sys
import os
import json

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_code_generator import EnhancedCodeGenerator, OutputMode
from enhanced_node_handlers import ENHANCED_HANDLER_REGISTRY


def test_simple_workflow():
    """Test a simple RSI strategy."""
    print("🔍 Testing Simple RSI Strategy...")
    
    # Simple workflow: Data -> RSI -> Condition -> Action
    workflow = {
        "nodes": [
            {
                "id": "data-1",
                "type": "dataSource",
                "data": {
                    "label": "AAPL Data",
                    "parameters": {
                        "symbol": "AAPL",
                        "timeframe": "1h",
                        "bars": 500
                    }
                }
            },
            {
                "id": "rsi-1",
                "type": "technicalIndicator",
                "data": {
                    "label": "RSI 14",
                    "parameters": {
                        "indicator": "RSI",
                        "period": 14
                    }
                }
            },
            {
                "id": "condition-1",
                "type": "condition",
                "data": {
                    "label": "RSI Oversold",
                    "parameters": {
                        "conditionType": "comparison",
                        "condition": "less_than",
                        "value": 30
                    }
                }
            },
            {
                "id": "buy-1",
                "type": "action",
                "data": {
                    "label": "Buy Signal",
                    "parameters": {
                        "action": "buy",
                        "quantity": 100
                    }
                }
            }
        ],
        "edges": [
            {
                "source": "data-1",
                "target": "rsi-1",
                "data": {
                    "sourceHandle": "data-output",
                    "targetHandle": "data-input",
                    "rule": {"dataType": "ohlcv"}
                }
            },
            {
                "source": "rsi-1",
                "target": "condition-1",
                "data": {
                    "sourceHandle": "output-1",
                    "targetHandle": "data-input",
                    "rule": {"dataType": "numeric"}
                }
            },
            {
                "source": "condition-1",
                "target": "buy-1",
                "data": {
                    "sourceHandle": "signal-output",
                    "targetHandle": "signal-input",
                    "rule": {"dataType": "signal"}
                }
            }
        ]
    }
    
    # Create compiler
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    # Compile
    result = generator.compile_workflow(workflow, OutputMode.TRAINING)
    
    print(f"✅ Success: {result['success']}")
    print(f"📊 Nodes: {result['metadata']['nodes_processed']}")
    print(f"🔗 Edges: {result['metadata']['edges_processed']}")
    
    if result['success']:
        # Save generated code
        with open('simple_strategy.py', 'w') as f:
            f.write(result['code'])
        print("💾 Generated code saved to 'simple_strategy.py'")
        
        # Show first 20 lines
        print("\n📄 Generated Code Preview:")
        lines = result['code'].split('\n')[:20]
        for i, line in enumerate(lines, 1):
            print(f"{i:2d}: {line}")
        print("... (truncated)")
    else:
        print("❌ Compilation failed:")
        for error in result['errors']:
            print(f"   - {error['message']}")
    
    return result


def test_with_your_workflow(workflow_file):
    """Test with your own workflow JSON file."""
    print(f"🔍 Testing workflow from {workflow_file}...")
    
    try:
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
    except FileNotFoundError:
        print(f"❌ File {workflow_file} not found!")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {workflow_file}: {e}")
        return None
    
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    result = generator.compile_workflow(workflow, OutputMode.BACKTESTING)
    
    print(f"✅ Success: {result['success']}")
    
    if result['success']:
        output_file = f"generated_from_{os.path.basename(workflow_file).replace('.json', '.py')}"
        with open(output_file, 'w') as f:
            f.write(result['code'])
        print(f"💾 Generated code saved to '{output_file}'")
    else:
        print("❌ Compilation failed:")
        for error in result['errors']:
            print(f"   - {error['message']}")
    
    return result


def test_all_modes():
    """Test all output modes."""
    print("🔍 Testing All Output Modes...")
    
    # Simple workflow
    workflow = {
        "nodes": [
            {
                "id": "data-1",
                "type": "dataSource",
                "data": {
                    "parameters": {
                        "symbol": "TSLA",
                        "timeframe": "4h"
                    }
                }
            },
            {
                "id": "sma-1",
                "type": "technicalIndicator",
                "data": {
                    "parameters": {
                        "indicator": "SMA",
                        "period": 20
                    }
                }
            },
            {
                "id": "condition-1",
                "type": "condition",
                "data": {
                    "parameters": {
                        "condition": "greater_than",
                        "value": 0
                    }
                }
            },
            {
                "id": "action-1",
                "type": "action",
                "data": {
                    "parameters": {
                        "action": "buy"
                    }
                }
            }
        ],
        "edges": [
            {
                "source": "data-1", 
                "target": "sma-1", 
                "data": {
                    "sourceHandle": "data-output",
                    "targetHandle": "data-input",
                    "rule": {"dataType": "ohlcv"}
                }
            },
            {
                "source": "sma-1", 
                "target": "condition-1", 
                "data": {
                    "sourceHandle": "output-1",
                    "targetHandle": "data-input",
                    "rule": {"dataType": "numeric"}
                }
            },
            {
                "source": "condition-1", 
                "target": "action-1", 
                "data": {
                    "sourceHandle": "signal-output",
                    "targetHandle": "signal-input",
                    "rule": {"dataType": "signal"}
                }
            }
        ]
    }
    
    generator = EnhancedCodeGenerator()
    generator.handlers.update(ENHANCED_HANDLER_REGISTRY)
    
    modes = [
        (OutputMode.TRAINING, "training"),
        (OutputMode.BACKTESTING, "backtesting"), 
        (OutputMode.LIVE_TRADING, "live_trading"),
        (OutputMode.RESEARCH, "research")
    ]
    
    for mode, name in modes:
        print(f"\n🎯 Testing {name.upper()} mode...")
        result = generator.compile_workflow(workflow, mode)
        
        if result['success']:
            filename = f"test_{name}.py"
            with open(filename, 'w') as f:
                f.write(result['code'])
            print(f"   ✅ Generated {filename} ({len(result['code'].splitlines())} lines)")
        else:
            print(f"   ❌ Failed: {len(result['errors'])} errors")


def interactive_test():
    """Interactive testing mode."""
    print("🎮 Interactive Testing Mode")
    print("=" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. Test simple RSI strategy")
        print("2. Test all output modes")
        print("3. Test with workflow file")
        print("4. Show generated files")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            test_simple_workflow()
        elif choice == '2':
            test_all_modes()
        elif choice == '3':
            filename = input("Enter workflow JSON filename: ").strip()
            test_with_your_workflow(filename)
        elif choice == '4':
            print("\n📁 Generated files:")
            for f in os.listdir('.'):
                if f.startswith('generated_') or f.startswith('test_') or f.startswith('simple_'):
                    if f.endswith('.py'):
                        size = os.path.getsize(f)
                        print(f"   {f} ({size} bytes)")
        elif choice == '5':
            break
        else:
            print("❌ Invalid choice!")


if __name__ == "__main__":
    print("🚀 Enhanced Compiler Test Suite")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "simple":
            test_simple_workflow()
        elif sys.argv[1] == "all":
            test_all_modes()
        elif sys.argv[1].endswith('.json'):
            test_with_your_workflow(sys.argv[1])
        else:
            print("Usage: python3 simple_test.py [simple|all|workflow.json]")
    else:
        # Interactive mode
        interactive_test()
    
    print("\n🎉 Testing complete!")