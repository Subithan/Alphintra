# 🧪 Enhanced Compiler Testing Guide

## Quick Start

### 1. **Run All Tests**
```bash
cd /workspace/src/backend/no-code-service
python3 test_enhanced_compiler.py
```

### 2. **Run Simple Tests**
```bash
# Test simple RSI strategy
python3 simple_test.py simple

# Test all output modes
python3 simple_test.py all

# Interactive mode
python3 simple_test.py
```

## 🎯 **Testing Scenarios**

### **Scenario 1: Basic Strategy Testing**

Test a simple moving average crossover strategy:

```python
from enhanced_code_generator import EnhancedCodeGenerator, OutputMode
from enhanced_node_handlers import ENHANCED_HANDLER_REGISTRY

# Create the workflow
workflow = {
    "nodes": [
        {
            "id": "data-source",
            "type": "dataSource", 
            "data": {
                "parameters": {
                    "symbol": "AAPL",
                    "timeframe": "1h",
                    "bars": 1000
                }
            }
        },
        {
            "id": "sma-fast",
            "type": "technicalIndicator",
            "data": {
                "parameters": {
                    "indicator": "SMA",
                    "period": 10
                }
            }
        },
        {
            "id": "sma-slow", 
            "type": "technicalIndicator",
            "data": {
                "parameters": {
                    "indicator": "SMA",
                    "period": 30
                }
            }
        },
        {
            "id": "crossover",
            "type": "condition",
            "data": {
                "parameters": {
                    "conditionType": "crossover",
                    "condition": "crossover",
                    "value": 0
                }
            }
        },
        {
            "id": "buy-action",
            "type": "action",
            "data": {
                "parameters": {
                    "action": "buy",
                    "quantity": 100,
                    "positionSizing": "fixed"
                }
            }
        }
    ],
    "edges": [
        {
            "source": "data-source",
            "target": "sma-fast",
            "data": {
                "sourceHandle": "data-output",
                "targetHandle": "data-input",
                "rule": {"dataType": "ohlcv"}
            }
        },
        {
            "source": "data-source", 
            "target": "sma-slow",
            "data": {
                "sourceHandle": "data-output",
                "targetHandle": "data-input", 
                "rule": {"dataType": "ohlcv"}
            }
        },
        {
            "source": "sma-fast",
            "target": "crossover",
            "data": {
                "sourceHandle": "output-1",
                "targetHandle": "data-input",
                "rule": {"dataType": "numeric"}
            }
        },
        {
            "source": "crossover",
            "target": "buy-action",
            "data": {
                "sourceHandle": "signal-output",
                "targetHandle": "signal-input",
                "rule": {"dataType": "signal"}
            }
        }
    ]
}

# Compile and test
generator = EnhancedCodeGenerator()
generator.handlers.update(ENHANCED_HANDLER_REGISTRY)

result = generator.compile_workflow(workflow, OutputMode.BACKTESTING)
print(f"Success: {result['success']}")

if result['success']:
    with open('ma_crossover_strategy.py', 'w') as f:
        f.write(result['code'])
    print("Generated ma_crossover_strategy.py")
```

### **Scenario 2: Complex Multi-Indicator Strategy**

```python
# RSI + MACD + Bollinger Bands strategy
complex_workflow = {
    "nodes": [
        # Data source
        {
            "id": "data-1",
            "type": "dataSource",
            "data": {"parameters": {"symbol": "TSLA", "timeframe": "4h"}}
        },
        
        # Technical indicators
        {
            "id": "rsi-1", 
            "type": "technicalIndicator",
            "data": {"parameters": {"indicator": "RSI", "period": 14}}
        },
        {
            "id": "macd-1",
            "type": "technicalIndicator", 
            "data": {"parameters": {"indicator": "MACD", "fastPeriod": 12, "slowPeriod": 26}}
        },
        {
            "id": "bb-1",
            "type": "technicalIndicator",
            "data": {"parameters": {"indicator": "BB", "period": 20, "multiplier": 2}}
        },
        
        # Conditions
        {
            "id": "rsi-oversold",
            "type": "condition",
            "data": {"parameters": {"condition": "less_than", "value": 30}}
        },
        {
            "id": "macd-bullish",
            "type": "condition", 
            "data": {"parameters": {"conditionType": "crossover", "condition": "crossover", "value": 0}}
        },
        {
            "id": "bb-squeeze",
            "type": "condition",
            "data": {"parameters": {"condition": "less_than", "value": 0.02}}
        },
        
        # Logic gates
        {
            "id": "and-gate-1",
            "type": "logic",
            "data": {"parameters": {"operation": "AND", "inputs": 2}}
        },
        {
            "id": "and-gate-2", 
            "type": "logic",
            "data": {"parameters": {"operation": "AND", "inputs": 2}}
        },
        
        # Risk management
        {
            "id": "risk-mgmt",
            "type": "riskManagement",
            "data": {"parameters": {"riskType": "position_size", "maxLoss": 2.0}}
        },
        
        # Action
        {
            "id": "buy-order",
            "type": "action", 
            "data": {"parameters": {"action": "buy", "quantity": 50, "stop_loss": 3, "take_profit": 9}}
        }
    ],
    "edges": [
        # Data to indicators
        {"source": "data-1", "target": "rsi-1", "data": {"sourceHandle": "data-output", "targetHandle": "data-input", "rule": {"dataType": "ohlcv"}}},
        {"source": "data-1", "target": "macd-1", "data": {"sourceHandle": "data-output", "targetHandle": "data-input", "rule": {"dataType": "ohlcv"}}},
        {"source": "data-1", "target": "bb-1", "data": {"sourceHandle": "data-output", "targetHandle": "data-input", "rule": {"dataType": "ohlcv"}}},
        
        # Indicators to conditions
        {"source": "rsi-1", "target": "rsi-oversold", "data": {"sourceHandle": "output-1", "targetHandle": "data-input", "rule": {"dataType": "numeric"}}},
        {"source": "macd-1", "target": "macd-bullish", "data": {"sourceHandle": "output-1", "targetHandle": "data-input", "rule": {"dataType": "numeric"}}},
        {"source": "bb-1", "target": "bb-squeeze", "data": {"sourceHandle": "output-4", "targetHandle": "data-input", "rule": {"dataType": "numeric"}}},
        
        # Conditions to logic gates
        {"source": "rsi-oversold", "target": "and-gate-1", "data": {"sourceHandle": "signal-output", "targetHandle": "input-0", "rule": {"dataType": "signal"}}},
        {"source": "macd-bullish", "target": "and-gate-1", "data": {"sourceHandle": "signal-output", "targetHandle": "input-1", "rule": {"dataType": "signal"}}},
        {"source": "and-gate-1", "target": "and-gate-2", "data": {"sourceHandle": "output", "targetHandle": "input-0", "rule": {"dataType": "signal"}}},
        {"source": "bb-squeeze", "target": "and-gate-2", "data": {"sourceHandle": "signal-output", "targetHandle": "input-1", "rule": {"dataType": "signal"}}},
        
        # Final signal to action
        {"source": "and-gate-2", "target": "buy-order", "data": {"sourceHandle": "output", "targetHandle": "signal-input", "rule": {"dataType": "signal"}}},
        
        # Risk management
        {"source": "data-1", "target": "risk-mgmt", "data": {"sourceHandle": "data-output", "targetHandle": "data-input", "rule": {"dataType": "ohlcv"}}}
    ]
}

result = generator.compile_workflow(complex_workflow, OutputMode.LIVE_TRADING)
```

### **Scenario 3: Error Testing**

Test error handling with invalid workflows:

```python
# Test missing data source
invalid_workflow = {
    "nodes": [
        {
            "id": "condition-1",
            "type": "condition", 
            "data": {"parameters": {"condition": "greater_than", "value": 50}}
        }
    ],
    "edges": []
}

result = generator.compile_workflow(invalid_workflow)
print("Errors:", result['errors'])
print("Warnings:", result['warnings'])
```

## 🔧 **Manual Testing**

### **1. Test Generated Code**

After generating code, you can test it manually:

```bash
# Generate training code
python3 simple_test.py simple

# Test the generated code
cd /workspace/src/backend/no-code-service
python3 -c "
import simple_strategy
pipeline = simple_strategy.StrategyPipeline()
try:
    pipeline.load_data().engineer_features().generate_signals()
    print('✅ Pipeline executed successfully!')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### **2. Test Different Symbols**

Modify the test workflows to use different symbols:

```python
# Test with crypto
workflow['nodes'][0]['data']['parameters']['symbol'] = 'BTC-USD'

# Test with forex  
workflow['nodes'][0]['data']['parameters']['symbol'] = 'EURUSD=X'

# Test with different timeframes
workflow['nodes'][0]['data']['parameters']['timeframe'] = '1d'
```

### **3. Test Optimization Levels**

```python
# Test different optimization levels
for opt_level in [0, 1, 2]:
    result = generator.compile_workflow(
        workflow, 
        OutputMode.TRAINING,
        optimization_level=opt_level
    )
    print(f"Optimization {opt_level}: {result['metadata']['optimizations_applied']} optimizations")
```

## 📊 **Performance Testing**

### **Benchmark Generation Speed**

```python
import time

start_time = time.time()
result = generator.compile_workflow(large_workflow, OutputMode.BACKTESTING)
end_time = time.time()

print(f"Compilation time: {end_time - start_time:.2f} seconds")
print(f"Generated {len(result['code'].splitlines())} lines of code")
print(f"Processing rate: {result['metadata']['nodes_processed'] / (end_time - start_time):.1f} nodes/sec")
```

### **Memory Usage Testing**

```python
import psutil
import os

process = psutil.Process(os.getpid())
memory_before = process.memory_info().rss / 1024 / 1024  # MB

result = generator.compile_workflow(workflow, OutputMode.TRAINING)

memory_after = process.memory_info().rss / 1024 / 1024  # MB
print(f"Memory usage: {memory_after - memory_before:.2f} MB")
```

## 🐛 **Debugging Tips**

### **1. Enable Verbose Output**

```python
# Set optimization level to 0 for debugging
result = generator.compile_workflow(
    workflow, 
    OutputMode.TRAINING,
    optimization_level=0
)

# Check compilation metadata
print("Compilation metadata:")
for key, value in result['metadata'].items():
    print(f"  {key}: {value}")
```

### **2. Validate Workflow Structure**

```python
# Check node types
node_types = [node['type'] for node in workflow['nodes']]
print("Node types:", set(node_types))

# Check edge connections
for edge in workflow['edges']:
    print(f"Edge: {edge['source']} -> {edge['target']}")
    if 'data' in edge and 'rule' in edge['data']:
        print(f"  Type: {edge['data']['rule'].get('dataType', 'unknown')}")
```

### **3. Test Individual Handlers**

```python
from enhanced_node_handlers import EnhancedTechnicalIndicatorHandler
from ir import Node

# Test individual handler
handler = EnhancedTechnicalIndicatorHandler()
node = Node(
    id="test-rsi",
    type="technicalIndicator",
    data={"parameters": {"indicator": "RSI", "period": 14}}
)

code = handler.handle(node, generator)
print("Generated code:", code)
```

## 📋 **Test Checklist**

- [ ] Basic workflow compilation
- [ ] All output modes (training, backtesting, live, research)  
- [ ] Error handling with invalid workflows
- [ ] Different optimization levels
- [ ] Various technical indicators
- [ ] Complex logic combinations
- [ ] Risk management integration
- [ ] Multiple symbols and timeframes
- [ ] Generated code execution
- [ ] Performance benchmarks

## 🚀 **Integration Testing**

### **With Frontend Data**

Test with actual data from your React Flow frontend:

```python
# Save workflow from frontend as JSON
# Then test with:
python3 simple_test.py my_frontend_workflow.json
```

### **With Live Data**

Test generated strategies with real market data:

```python
# Generate live trading code
result = generator.compile_workflow(workflow, OutputMode.LIVE_TRADING)

# Test with paper trading first
# Modify generated code to use paper trading mode
```

## 📈 **Results Validation**

After testing, validate:

1. **Code Quality**: Generated code is readable and follows Python best practices
2. **Functionality**: All workflow logic is correctly translated
3. **Performance**: Code executes efficiently
4. **Error Handling**: Graceful handling of edge cases
5. **Type Safety**: No type mismatches in generated code

## 🎉 **Success Metrics**

A successful test should show:
- ✅ Compilation success: `True`
- ✅ No critical errors
- ✅ Generated code runs without syntax errors
- ✅ Logical flow matches workflow design
- ✅ Performance within acceptable limits

Happy testing! 🚀