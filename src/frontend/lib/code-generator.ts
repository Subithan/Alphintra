import { Node, Edge } from 'reactflow';
import { NoCodeWorkflow } from '@/lib/stores/no-code-store';

export interface GeneratedCode {
  strategy: string;
  requirements: string[];
  imports: string[];
  classes: CodeClass[];
  functions: CodeFunction[];
  metadata: {
    name: string;
    description: string;
    author: string;
    version: string;
    generatedAt: string;
    complexity: number;
    estimatedPerformance: {
      executionTime: string;
      memoryUsage: string;
      backtestSpeed: string;
    };
  };
  tests: string;
  documentation: string;
}

export interface CodeClass {
  name: string;
  description: string;
  methods: CodeMethod[];
  properties: CodeProperty[];
}

export interface CodeMethod {
  name: string;
  parameters: CodeParameter[];
  returnType: string;
  description: string;
  code: string;
}

export interface CodeProperty {
  name: string;
  type: string;
  description: string;
  defaultValue?: any;
}

export interface CodeParameter {
  name: string;
  type: string;
  description: string;
  defaultValue?: any;
}

export interface CodeFunction {
  name: string;
  parameters: CodeParameter[];
  returnType: string;
  description: string;
  code: string;
}

export class AdvancedCodeGenerator {
  private nodes: Node[];
  private edges: Edge[];
  private workflow: NoCodeWorkflow;

  constructor(workflow: NoCodeWorkflow) {
    this.workflow = workflow;
    this.nodes = workflow.nodes;
    this.edges = workflow.edges;
  }

  /**
   * Generate complete Python trading strategy
   */
  generateStrategy(): GeneratedCode {
    const topology = this.analyzeTopology();
    const requirements = this.generateRequirements();
    const imports = this.generateImports();
    const strategyClass = this.generateStrategyClass(topology);
    const helperFunctions = this.generateHelperFunctions();
    const tests = this.generateTests();
    const documentation = this.generateDocumentation();

    const strategyCode = this.assembleStrategyCode(imports, strategyClass, helperFunctions);

    return {
      strategy: strategyCode,
      requirements,
      imports,
      classes: [strategyClass],
      functions: helperFunctions,
      metadata: {
        name: this.workflow.name,
        description: this.workflow.description || 'Generated trading strategy',
        author: 'Alphintra Code Generator',
        version: '1.0.0',
        generatedAt: new Date().toISOString(),
        complexity: this.calculateComplexity(),
        estimatedPerformance: this.estimatePerformance()
      },
      tests,
      documentation
    };
  }

  private analyzeTopology() {
    // Build execution graph
    const executionOrder = this.topologicalSort();
    const dataFlow = this.analyzeDataFlow();
    const nodeTypes = this.categorizeNodes();

    return {
      executionOrder,
      dataFlow,
      nodeTypes
    };
  }

  private topologicalSort(): string[] {
    const inDegree = new Map<string, number>();
    const adjList = new Map<string, string[]>();

    // Initialize
    this.nodes.forEach(node => {
      inDegree.set(node.id, 0);
      adjList.set(node.id, []);
    });

    // Build graph
    this.edges.forEach(edge => {
      const sources = adjList.get(edge.source) || [];
      sources.push(edge.target);
      adjList.set(edge.source, sources);
      inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    });

    // Kahn's algorithm
    const queue: string[] = [];
    const result: string[] = [];

    this.nodes.forEach(node => {
      if (inDegree.get(node.id) === 0) {
        queue.push(node.id);
      }
    });

    while (queue.length > 0) {
      const current = queue.shift()!;
      result.push(current);

      const neighbors = adjList.get(current) || [];
      neighbors.forEach(neighbor => {
        const newInDegree = (inDegree.get(neighbor) || 0) - 1;
        inDegree.set(neighbor, newInDegree);
        if (newInDegree === 0) {
          queue.push(neighbor);
        }
      });
    }

    return result;
  }

  private analyzeDataFlow() {
    const dataFlow = new Map<string, {
      inputs: string[];
      outputs: string[];
      dataType: string;
    }>();

    this.nodes.forEach(node => {
      const inputs = this.edges
        .filter(edge => edge.target === node.id)
        .map(edge => edge.source);
      
      const outputs = this.edges
        .filter(edge => edge.source === node.id)
        .map(edge => edge.target);

      dataFlow.set(node.id, {
        inputs,
        outputs,
        dataType: this.getNodeDataType(node)
      });
    });

    return dataFlow;
  }

  private categorizeNodes() {
    return {
      dataSources: this.nodes.filter(n => n.type === 'dataSource' || n.type === 'customDataset'),
      indicators: this.nodes.filter(n => n.type === 'technicalIndicator'),
      conditions: this.nodes.filter(n => n.type === 'condition'),
      logic: this.nodes.filter(n => n.type === 'logic'),
      actions: this.nodes.filter(n => n.type === 'action'),
      riskManagement: this.nodes.filter(n => n.type === 'risk'),
      outputs: this.nodes.filter(n => n.type === 'output')
    };
  }

  private generateRequirements(): string[] {
    return [
      'pandas>=2.0.0',
      'numpy>=1.24.0',
      'ta-lib>=0.4.25',
      'backtrader>=1.9.76',
      'yfinance>=0.2.18',
      'scipy>=1.10.0',
      'scikit-learn>=1.3.0',
      'plotly>=5.15.0',
      'fastapi>=0.104.0',
      'pydantic>=2.4.0',
      'asyncio-mqtt>=0.11.0'
    ];
  }

  private generateImports(): string[] {
    return [
      'import pandas as pd',
      'import numpy as np',
      'import talib as ta',
      'from typing import Dict, List, Optional, Tuple, Union',
      'from dataclasses import dataclass',
      'from datetime import datetime, timedelta',
      'from enum import Enum',
      'import logging',
      'import asyncio',
      'from abc import ABC, abstractmethod'
    ];
  }

  private generateStrategyClass(topology: any): CodeClass {
    const methods = [
      this.generateInitMethod(),
      this.generateSetupMethod(topology),
      this.generateOnDataMethod(topology),
      this.generateCalculateIndicatorsMethod(topology),
      this.generateEvaluateConditionsMethod(topology),
      this.generateExecuteActionsMethod(topology),
      this.generateManageRiskMethod(topology),
      this.generateGetSignalsMethod(),
      this.generateBacktestMethod()
    ];

    const properties = [
      { name: 'name', type: 'str', description: 'Strategy name' },
      { name: 'data', type: 'pd.DataFrame', description: 'Market data' },
      { name: 'indicators', type: 'Dict[str, pd.Series]', description: 'Technical indicators' },
      { name: 'signals', type: 'Dict[str, bool]', description: 'Trading signals' },
      { name: 'positions', type: 'Dict[str, float]', description: 'Current positions' },
      { name: 'portfolio_value', type: 'float', description: 'Current portfolio value' },
      { name: 'risk_params', type: 'Dict[str, float]', description: 'Risk management parameters' }
    ];

    return {
      name: this.sanitizeClassName(this.workflow.name),
      description: `Generated trading strategy: ${this.workflow.name}`,
      methods,
      properties
    };
  }

  private generateInitMethod(): CodeMethod {
    return {
      name: '__init__',
      parameters: [
        { name: 'self', type: 'self', description: 'Instance reference' },
        { name: 'config', type: 'Dict[str, any]', description: 'Strategy configuration', defaultValue: '{}' }
      ],
      returnType: 'None',
      description: 'Initialize the trading strategy',
      code: `        """Initialize the trading strategy with configuration."""
        self.name = "${this.workflow.name}"
        self.config = config
        self.data = pd.DataFrame()
        self.indicators = {}
        self.signals = {}
        self.positions = {}
        self.portfolio_value = 100000.0  # Default starting capital
        self.risk_params = self._setup_risk_parameters()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize performance tracking
        self.trades = []
        self.performance_metrics = {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0
        }`
    };
  }

  private generateSetupMethod(topology: any): CodeMethod {
    const dataSourceNodes = topology.nodeTypes.dataSources;
    const setupCode = dataSourceNodes.map((node: any) => {
      const params = node.data.parameters || {};
      if (node.type === 'dataSource') {
        return `        # Setup data source: ${node.data.label}
        self.symbol = "${params.symbol || 'AAPL'}"
        self.timeframe = "${params.timeframe || '1h'}"
        self.bars = ${params.bars || 1000}`;
      } else {
        return `        # Setup custom dataset: ${node.data.label}
        self.custom_data_path = "${params.fileName || 'custom_data.csv'}"`;
      }
    }).join('\n');

    return {
      name: 'setup',
      parameters: [
        { name: 'self', type: 'self', description: 'Instance reference' }
      ],
      returnType: 'None',
      description: 'Setup strategy parameters and data sources',
      code: setupCode || '        # No data sources configured\n        pass'
    };
  }

  private generateOnDataMethod(topology: any): CodeMethod {
    return {
      name: 'on_data',
      parameters: [
        { name: 'self', type: 'self', description: 'Instance reference' },
        { name: 'data', type: 'pd.DataFrame', description: 'New market data' }
      ],
      returnType: 'Dict[str, any]',
      description: 'Process new market data and generate trading signals',
      code: `        """Process new market data and generate trading signals."""
        try:
            # Update internal data
            self.data = data
            
            # Calculate technical indicators
            self.calculate_indicators()
            
            # Evaluate trading conditions
            signals = self.evaluate_conditions()
            
            # Execute trading actions based on signals
            actions = self.execute_actions(signals)
            
            # Apply risk management
            actions = self.manage_risk(actions)
            
            # Log performance
            self._log_performance()
            
            return {
                'signals': signals,
                'actions': actions,
                'indicators': self.indicators,
                'portfolio_value': self.portfolio_value
            }
            
        except Exception as e:
            self.logger.error(f"Error in on_data: {str(e)}")
            return {'error': str(e)}`
    };
  }

  private generateCalculateIndicatorsMethod(topology: any): CodeMethod {
    const indicatorNodes = topology.nodeTypes.indicators;
    
    const indicatorCode = indicatorNodes.map((node: any) => {
      const params = node.data.parameters || {};
      const indicator = params.indicator || 'SMA';
      const period = params.period || 20;
      const source = params.source || 'close';
      
      return this.generateIndicatorCode(node.id, indicator, period, source, params);
    }).join('\n\n');

    return {
      name: 'calculate_indicators',
      parameters: [
        { name: 'self', type: 'self', description: 'Instance reference' }
      ],
      returnType: 'None',
      description: 'Calculate all technical indicators',
      code: indicatorCode || '        # No indicators configured\n        pass'
    };
  }

  private generateIndicatorCode(nodeId: string, indicator: string, period: number, source: string, params: any): string {
    const varName = `${indicator.toLowerCase()}_${nodeId.replace('-', '_')}`;
    
    switch (indicator) {
      case 'SMA':
        return `        # Simple Moving Average
        self.indicators['${varName}'] = ta.SMA(self.data['${source}'], timeperiod=${period})`;
      
      case 'EMA':
        return `        # Exponential Moving Average
        self.indicators['${varName}'] = ta.EMA(self.data['${source}'], timeperiod=${period})`;
      
      case 'RSI':
        return `        # Relative Strength Index
        self.indicators['${varName}'] = ta.RSI(self.data['${source}'], timeperiod=${period})`;
      
      case 'MACD':
        const fastPeriod = params.fastPeriod || 12;
        const slowPeriod = params.slowPeriod || 26;
        const signalPeriod = params.signalPeriod || 9;
        return `        # MACD
        macd, signal, histogram = ta.MACD(self.data['${source}'], 
                                         fastperiod=${fastPeriod}, 
                                         slowperiod=${slowPeriod}, 
                                         signalperiod=${signalPeriod})
        self.indicators['${varName}_macd'] = macd
        self.indicators['${varName}_signal'] = signal
        self.indicators['${varName}_histogram'] = histogram`;
      
      case 'BB':
        const multiplier = params.multiplier || 2.0;
        return `        # Bollinger Bands
        upper, middle, lower = ta.BBANDS(self.data['${source}'], 
                                        timeperiod=${period}, 
                                        nbdevup=${multiplier}, 
                                        nbdevdn=${multiplier})
        self.indicators['${varName}_upper'] = upper
        self.indicators['${varName}_middle'] = middle
        self.indicators['${varName}_lower'] = lower
        self.indicators['${varName}_width'] = (upper - lower) / middle`;
      
      case 'ATR':
        return `        # Average True Range
        self.indicators['${varName}'] = ta.ATR(self.data['high'], 
                                             self.data['low'], 
                                             self.data['close'], 
                                             timeperiod=${period})`;
      
      default:
        return `        # ${indicator} (Generic implementation)
        self.indicators['${varName}'] = ta.SMA(self.data['${source}'], timeperiod=${period})`;
    }
  }

  private generateEvaluateConditionsMethod(topology: any): CodeMethod {
    const conditionNodes = topology.nodeTypes.conditions;
    const logicNodes = topology.nodeTypes.logic;
    
    const conditionCode = this.generateConditionsCode(conditionNodes, logicNodes);

    return {
      name: 'evaluate_conditions',
      parameters: [
        { name: 'self', type: 'self', description: 'Instance reference' }
      ],
      returnType: 'Dict[str, bool]',
      description: 'Evaluate all trading conditions and logic',
      code: conditionCode
    };
  }

  private generateConditionsCode(conditionNodes: Node[], logicNodes: Node[]): string {
    if (conditionNodes.length === 0 && logicNodes.length === 0) {
      return '        # No conditions configured\n        return {}';
    }

    let code = '        """Evaluate all trading conditions and logic."""\n        signals = {}\n\n';
    
    // Generate condition evaluations
    conditionNodes.forEach(node => {
      const params = node.data.parameters || {};
      const conditionType = params.conditionType || 'comparison';
      const condition = params.condition || 'greater_than';
      const value = params.value || 0;
      const varName = `condition_${node.id.replace('-', '_')}`;
      
      code += this.generateConditionCode(varName, conditionType, condition, value, params);
    });

    // Generate logic evaluations
    logicNodes.forEach(node => {
      const params = node.data.parameters || {};
      const operation = params.operation || 'AND';
      const varName = `logic_${node.id.replace('-', '_')}`;
      
      code += this.generateLogicCode(varName, operation, node.id);
    });

    code += '\n        return signals';
    return code;
  }

  private generateConditionCode(varName: string, conditionType: string, condition: string, value: any, params: any): string {
    switch (conditionType) {
      case 'comparison':
        const operator = this.getComparisonOperator(condition);
        return `        # ${conditionType} condition
        try:
            # Get the latest indicator value (implement based on connected inputs)
            current_value = self.data['close'].iloc[-1] if len(self.data) > 0 else 0
            signals['${varName}'] = current_value ${operator} ${value}
        except Exception as e:
            self.logger.warning(f"Error evaluating ${varName}: {e}")
            signals['${varName}'] = False

`;
      
      case 'crossover':
        return `        # Crossover condition
        try:
            # Implement crossover logic (requires two input series)
            signals['${varName}'] = False  # Placeholder
        except Exception as e:
            self.logger.warning(f"Error evaluating ${varName}: {e}")
            signals['${varName}'] = False

`;
      
      default:
        return `        # ${conditionType} condition
        signals['${varName}'] = False  # Placeholder

`;
    }
  }

  private generateLogicCode(varName: string, operation: string, nodeId: string): string {
    return `        # Logic gate: ${operation}
        try:
            # Get input signals (implement based on connected inputs)
            input_signals = []  # Placeholder for actual input signals
            if operation == 'AND':
                signals['${varName}'] = all(input_signals) if input_signals else False
            elif operation == 'OR':
                signals['${varName}'] = any(input_signals) if input_signals else False
            elif operation == 'NOT':
                signals['${varName}'] = not input_signals[0] if input_signals else True
        except Exception as e:
            self.logger.warning(f"Error evaluating ${varName}: {e}")
            signals['${varName}'] = False

`;
  }

  private generateExecuteActionsMethod(topology: any): CodeMethod {
    const actionNodes = topology.nodeTypes.actions;
    
    const actionCode = actionNodes.map((node: any) => {
      const params = node.data.parameters || {};
      const action = params.action || 'buy';
      const quantity = params.quantity || 10;
      const orderType = params.order_type || 'market';
      
      return this.generateActionCode(node.id, action, quantity, orderType, params);
    }).join('\n\n');

    return {
      name: 'execute_actions',
      parameters: [
        { name: 'self', type: 'self', description: 'Instance reference' },
        { name: 'signals', type: 'Dict[str, bool]', description: 'Trading signals' }
      ],
      returnType: 'List[Dict[str, any]]',
      description: 'Execute trading actions based on signals',
      code: `        """Execute trading actions based on signals."""
        actions = []
        
${actionCode || '        # No actions configured'}

        return actions`
    };
  }

  private generateActionCode(nodeId: string, action: string, quantity: number, orderType: string, params: any): string {
    const varName = `action_${nodeId.replace('-', '_')}`;
    const stopLoss = params.stop_loss || 0;
    const takeProfit = params.take_profit || 0;
    
    return `        # ${action.toUpperCase()} action
        if signals.get('trigger_signal', False):  # Replace with actual signal
            action = {
                'type': '${action}',
                'symbol': self.symbol,
                'quantity': ${quantity},
                'order_type': '${orderType}',
                'timestamp': datetime.now(),
                'stop_loss': ${stopLoss},
                'take_profit': ${takeProfit}
            }
            actions.append(action)
            self.logger.info(f"Generated {action['type']} order: {action}")`;
  }

  private generateManageRiskMethod(topology: any): CodeMethod {
    const riskNodes = topology.nodeTypes.riskManagement;
    
    return {
      name: 'manage_risk',
      parameters: [
        { name: 'self', type: 'self', description: 'Instance reference' },
        { name: 'actions', type: 'List[Dict[str, any]]', description: 'Proposed trading actions' }
      ],
      returnType: 'List[Dict[str, any]]',
      description: 'Apply risk management to trading actions',
      code: `        """Apply risk management to trading actions."""
        filtered_actions = []
        
        for action in actions:
            # Apply position sizing
            action['quantity'] = self._calculate_position_size(action)
            
            # Check portfolio heat
            if self._check_portfolio_heat(action):
                # Apply stop loss and take profit
                action = self._apply_risk_controls(action)
                filtered_actions.append(action)
            else:
                self.logger.warning(f"Action rejected due to risk limits: {action}")
        
        return filtered_actions`
    };
  }

  private generateGetSignalsMethod(): CodeMethod {
    return {
      name: 'get_signals',
      parameters: [
        { name: 'self', type: 'self', description: 'Instance reference' }
      ],
      returnType: 'Dict[str, any]',
      description: 'Get current trading signals and indicators',
      code: `        """Get current trading signals and indicators."""
        return {
            'signals': self.signals,
            'indicators': self.indicators,
            'portfolio_value': self.portfolio_value,
            'positions': self.positions,
            'timestamp': datetime.now()
        }`
    };
  }

  private generateBacktestMethod(): CodeMethod {
    return {
      name: 'backtest',
      parameters: [
        { name: 'self', type: 'self', description: 'Instance reference' },
        { name: 'start_date', type: 'str', description: 'Backtest start date' },
        { name: 'end_date', type: 'str', description: 'Backtest end date' }
      ],
      returnType: 'Dict[str, any]',
      description: 'Run strategy backtest',
      code: `        """Run strategy backtest over specified period."""
        try:
            # Implement backtesting logic
            results = {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'start_date': start_date,
                'end_date': end_date
            }
            
            self.logger.info(f"Backtest completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}")
            return {'error': str(e)}`
    };
  }

  private generateHelperFunctions(): CodeFunction[] {
    return [
      {
        name: '_setup_risk_parameters',
        parameters: [{ name: 'self', type: 'self', description: 'Instance reference' }],
        returnType: 'Dict[str, float]',
        description: 'Setup default risk management parameters',
        code: `        """Setup default risk management parameters."""
        return {
            'max_position_size': 0.1,  # 10% of portfolio
            'max_portfolio_heat': 0.2,  # 20% total risk
            'stop_loss_pct': 0.02,  # 2% stop loss
            'take_profit_pct': 0.04,  # 4% take profit
            'max_drawdown': 0.15  # 15% max drawdown
        }`
      },
      {
        name: '_calculate_position_size',
        parameters: [
          { name: 'self', type: 'self', description: 'Instance reference' },
          { name: 'action', type: 'Dict[str, any]', description: 'Trading action' }
        ],
        returnType: 'float',
        description: 'Calculate optimal position size based on risk parameters',
        code: `        """Calculate optimal position size based on risk parameters."""
        risk_per_share = action.get('stop_loss', self.risk_params['stop_loss_pct'])
        max_risk = self.portfolio_value * self.risk_params['max_position_size']
        
        if risk_per_share > 0:
            position_size = max_risk / risk_per_share
            return min(position_size, action['quantity'])
        
        return action['quantity']`
      },
      {
        name: '_check_portfolio_heat',
        parameters: [
          { name: 'self', type: 'self', description: 'Instance reference' },
          { name: 'action', type: 'Dict[str, any]', description: 'Trading action' }
        ],
        returnType: 'bool',
        description: 'Check if action exceeds portfolio heat limits',
        code: `        """Check if action exceeds portfolio heat limits."""
        current_heat = sum(abs(pos) for pos in self.positions.values())
        new_heat = current_heat + abs(action['quantity'])
        max_heat = self.portfolio_value * self.risk_params['max_portfolio_heat']
        
        return new_heat <= max_heat`
      },
      {
        name: '_apply_risk_controls',
        parameters: [
          { name: 'self', type: 'self', description: 'Instance reference' },
          { name: 'action', type: 'Dict[str, any]', description: 'Trading action' }
        ],
        returnType: 'Dict[str, any]',
        description: 'Apply stop loss and take profit to action',
        code: `        """Apply stop loss and take profit to action."""
        if action.get('stop_loss', 0) == 0:
            action['stop_loss'] = self.risk_params['stop_loss_pct']
        
        if action.get('take_profit', 0) == 0:
            action['take_profit'] = self.risk_params['take_profit_pct']
        
        return action`
      },
      {
        name: '_log_performance',
        parameters: [{ name: 'self', type: 'self', description: 'Instance reference' }],
        returnType: 'None',
        description: 'Log current performance metrics',
        code: `        """Log current performance metrics."""
        if len(self.data) > 0:
            self.logger.info(f"Portfolio Value: {self.portfolio_value:.2f}")
            self.logger.info(f"Active Positions: {len(self.positions)}")
            self.logger.info(f"Current Signals: {sum(1 for s in self.signals.values() if s)}")`
      }
    ];
  }

  private generateTests(): string {
    return `"""
Test suite for ${this.workflow.name} strategy
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class Test${this.sanitizeClassName(this.workflow.name)}(unittest.TestCase):
    
    def setUp(self):
        """Setup test environment."""
        self.strategy = ${this.sanitizeClassName(this.workflow.name)}()
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='1H')
        self.sample_data = pd.DataFrame({
            'open': np.random.randn(len(dates)).cumsum() + 100,
            'high': np.random.randn(len(dates)).cumsum() + 102,
            'low': np.random.randn(len(dates)).cumsum() + 98,
            'close': np.random.randn(len(dates)).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
    
    def test_strategy_initialization(self):
        """Test strategy initialization."""
        self.assertEqual(self.strategy.name, "${this.workflow.name}")
        self.assertIsInstance(self.strategy.indicators, dict)
        self.assertIsInstance(self.strategy.signals, dict)
    
    def test_indicator_calculation(self):
        """Test technical indicator calculations."""
        self.strategy.data = self.sample_data
        self.strategy.calculate_indicators()
        
        # Check that indicators were calculated
        self.assertGreater(len(self.strategy.indicators), 0)
    
    def test_signal_generation(self):
        """Test trading signal generation."""
        self.strategy.data = self.sample_data
        self.strategy.calculate_indicators()
        signals = self.strategy.evaluate_conditions()
        
        self.assertIsInstance(signals, dict)
    
    def test_risk_management(self):
        """Test risk management functions."""
        test_action = {
            'type': 'buy',
            'quantity': 100,
            'stop_loss': 0.02
        }
        
        size = self.strategy._calculate_position_size(test_action)
        self.assertGreater(size, 0)
        
        heat_check = self.strategy._check_portfolio_heat(test_action)
        self.assertIsInstance(heat_check, bool)
    
    def test_backtest(self):
        """Test backtesting functionality."""
        self.strategy.data = self.sample_data
        results = self.strategy.backtest('2023-01-01', '2023-12-31')
        
        self.assertIn('total_return', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('max_drawdown', results)

if __name__ == '__main__':
    unittest.main()
`;
  }

  private generateDocumentation(): string {
    return `# ${this.workflow.name} - Trading Strategy Documentation

## Overview
${this.workflow.description || 'Generated trading strategy using Alphintra No-Code Console'}

**Generated:** ${new Date().toISOString()}
**Version:** 1.0.0

## Strategy Components

### Data Sources
${this.nodes.filter(n => n.type === 'dataSource' || n.type === 'customDataset').map(n => 
  `- **${n.data.label}**: ${n.type === 'dataSource' ? 'Market data feed' : 'Custom dataset'}`
).join('\n')}

### Technical Indicators
${this.nodes.filter(n => n.type === 'technicalIndicator').map(n => {
  const params = n.data.parameters || {};
  return `- **${n.data.label}**: ${params.indicator || 'Unknown'} (Period: ${params.period || 'N/A'})`;
}).join('\n')}

### Trading Conditions
${this.nodes.filter(n => n.type === 'condition').map(n => 
  `- **${n.data.label}**: ${n.data.parameters?.condition || 'Unknown condition'}`
).join('\n')}

### Actions
${this.nodes.filter(n => n.type === 'action').map(n => 
  `- **${n.data.label}**: ${n.data.parameters?.action || 'Unknown action'}`
).join('\n')}

### Risk Management
${this.nodes.filter(n => n.type === 'risk').map(n => 
  `- **${n.data.label}**: ${n.data.parameters?.riskType || 'Unknown risk control'}`
).join('\n')}

## Usage

\`\`\`python
# Initialize strategy
strategy = ${this.sanitizeClassName(this.workflow.name)}()

# Setup with configuration
strategy.setup()

# Process market data
result = strategy.on_data(market_data)

# Run backtest
backtest_results = strategy.backtest('2023-01-01', '2023-12-31')
\`\`\`

## Performance Characteristics

- **Estimated Complexity**: ${this.calculateComplexity()}
- **Estimated Execution Time**: ${this.estimatePerformance().executionTime}
- **Memory Usage**: ${this.estimatePerformance().memoryUsage}

## Risk Controls

- Position sizing based on portfolio percentage
- Stop loss and take profit management
- Portfolio heat monitoring
- Maximum drawdown limits

## Notes

This strategy was automatically generated from a visual workflow. 
Review and test thoroughly before using in production.
`;
  }

  private assembleStrategyCode(imports: string[], strategyClass: CodeClass, helperFunctions: CodeFunction[]): string {
    const importsSection = imports.join('\n');
    const classSection = this.generateClassCode(strategyClass);
    const functionsSection = helperFunctions.map(f => this.generateFunctionCode(f)).join('\n\n');

    return `${importsSection}

# Generated Trading Strategy: ${this.workflow.name}
# Created: ${new Date().toISOString()}
# Generator: Alphintra Advanced Code Generator v1.0.0

${classSection}

${functionsSection}

# Example usage
if __name__ == "__main__":
    # Initialize strategy
    strategy = ${strategyClass.name}()
    
    # Setup strategy
    strategy.setup()
    
    print(f"Strategy '{strategy.name}' initialized successfully!")
    print(f"Indicators: {list(strategy.indicators.keys())}")
    print(f"Risk Parameters: {strategy.risk_params}")
`;
  }

  private generateClassCode(classObj: CodeClass): string {
    const methodsCode = classObj.methods.map(method => 
      `    def ${method.name}(${method.parameters.map(p => p.name + (p.defaultValue ? ` = ${p.defaultValue}` : '')).join(', ')}) -> ${method.returnType}:
        """${method.description}"""
${method.code}`
    ).join('\n\n');

    return `class ${classObj.name}:
    """${classObj.description}"""
    
${methodsCode}`;
  }

  private generateFunctionCode(func: CodeFunction): string {
    return `def ${func.name}(${func.parameters.map(p => p.name + (p.defaultValue ? ` = ${p.defaultValue}` : '')).join(', ')}) -> ${func.returnType}:
    """${func.description}"""
${func.code}`;
  }

  // Helper methods
  private getNodeDataType(node: Node): string {
    switch (node.type) {
      case 'dataSource':
      case 'customDataset':
        return 'ohlcv';
      case 'technicalIndicator':
        return 'numeric';
      case 'condition':
      case 'logic':
        return 'signal';
      case 'action':
        return 'order';
      case 'risk':
        return 'risk';
      default:
        return 'unknown';
    }
  }

  private getComparisonOperator(condition: string): string {
    switch (condition) {
      case 'greater_than': return '>';
      case 'less_than': return '<';
      case 'greater_than_equal': return '>=';
      case 'less_than_equal': return '<=';
      case 'equal': return '==';
      case 'not_equal': return '!=';
      default: return '>';
    }
  }

  private sanitizeClassName(name: string): string {
    return name
      .replace(/[^a-zA-Z0-9]/g, '')
      .replace(/^[0-9]/, 'Strategy$&')
      .replace(/^$/, 'GeneratedStrategy');
  }

  private calculateComplexity(): number {
    return this.nodes.length * 10 + this.edges.length * 5;
  }

  private estimatePerformance() {
    const complexity = this.calculateComplexity();
    return {
      executionTime: complexity < 100 ? '<10ms' : complexity < 500 ? '<50ms' : '<100ms',
      memoryUsage: complexity < 100 ? '<1MB' : complexity < 500 ? '<5MB' : '<10MB',
      backtestSpeed: complexity < 100 ? 'Fast' : complexity < 500 ? 'Medium' : 'Slow'
    };
  }
}

// Export utility function
export function generateStrategyCode(workflow: NoCodeWorkflow): GeneratedCode {
  const generator = new AdvancedCodeGenerator(workflow);
  return generator.generateStrategy();
}