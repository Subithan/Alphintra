import { Node, Edge } from 'reactflow';

export interface GeneratedCode {
  strategy_class: string;
  indicator_calculations: string;
  condition_evaluations: string;
  logic_operations: string;
  execution_engine: string;
  imports: string[];
  complexity_score: number;
  estimated_performance: {
    execution_time_ms: number;
    memory_usage_mb: number;
    cpu_intensity: 'low' | 'medium' | 'high';
  };
}

export interface IndicatorConfig {
  id: string;
  type: string;
  parameters: Record<string, any>;
  outputs: string[];
  dependencies: string[];
}

export interface LogicTreeNode {
  id: string;
  type: 'condition' | 'logic' | 'action';
  operation?: string;
  inputs: LogicTreeNode[];
  code: string;
  depth: number;
}

export class AdvancedCodeGenerator {
  private nodes: Node[] = [];
  private edges: Edge[] = [];
  private indicators: Map<string, IndicatorConfig> = new Map();
  private logicTrees: Map<string, LogicTreeNode> = new Map();
  private executionOrder: string[] = [];

  constructor(nodes: Node[], edges: Edge[]) {
    this.nodes = nodes;
    this.edges = edges;
    this.analyzeWorkflow();
  }

  private analyzeWorkflow(): void {
    // Build indicator configurations
    this.buildIndicatorConfigs();
    
    // Build logic trees for complex nested operations
    this.buildLogicTrees();
    
    // Determine optimal execution order
    this.calculateExecutionOrder();
  }

  private buildIndicatorConfigs(): void {
    const indicatorNodes = this.nodes.filter(n => n.type === 'technicalIndicator');
    
    indicatorNodes.forEach(node => {
      const indicator = node.data?.parameters?.indicator || 'SMA';
      const outputs = this.getIndicatorOutputs(indicator);
      const dependencies = this.getIndicatorDependencies(node.id);
      
      this.indicators.set(node.id, {
        id: node.id,
        type: indicator,
        parameters: node.data?.parameters || {},
        outputs,
        dependencies
      });
    });
  }

  private getIndicatorOutputs(indicator: string): string[] {
    const outputMappings: Record<string, string[]> = {
      'ADX': ['adx', 'di_plus', 'di_minus'],
      'BB': ['upper', 'middle', 'lower', 'width'],
      'MACD': ['macd_line', 'signal_line', 'histogram'],
      'STOCH': ['percent_k', 'percent_d'],
      'KDJ': ['percent_k', 'percent_d', 'percent_j'],
      'RSI': ['rsi_value'],
      'SMA': ['sma_value'],
      'EMA': ['ema_value'],
      'ATR': ['atr_value']
    };
    
    return outputMappings[indicator] || ['value', 'signal'];
  }

  private getIndicatorDependencies(nodeId: string): string[] {
    const incomingEdges = this.edges.filter(e => e.target === nodeId);
    return incomingEdges.map(e => e.source);
  }

  private buildLogicTrees(): void {
    const actionNodes = this.nodes.filter(n => n.type === 'action');
    
    actionNodes.forEach(actionNode => {
      const tree = this.buildLogicTreeForAction(actionNode.id);
      if (tree) {
        this.logicTrees.set(actionNode.id, tree);
      }
    });
  }

  private buildLogicTreeForAction(actionId: string, visited = new Set<string>()): LogicTreeNode | null {
    if (visited.has(actionId)) return null;
    visited.add(actionId);

    const actionNode = this.nodes.find(n => n.id === actionId);
    if (!actionNode) return null;

    const incomingEdges = this.edges.filter(e => e.target === actionId);
    const inputs: LogicTreeNode[] = [];

    incomingEdges.forEach(edge => {
      const sourceNode = this.nodes.find(n => n.id === edge.source);
      if (sourceNode) {
        const childTree = this.buildLogicTreeRecursive(sourceNode.id, visited, 0);
        if (childTree) {
          inputs.push(childTree);
        }
      }
    });

    return {
      id: actionId,
      type: 'action',
      inputs,
      code: this.generateActionCode(actionNode),
      depth: Math.max(0, ...inputs.map(i => i.depth)) + 1
    };
  }

  private buildLogicTreeRecursive(nodeId: string, visited: Set<string>, depth: number): LogicTreeNode | null {
    if (visited.has(nodeId)) return null;
    visited.add(nodeId);

    const node = this.nodes.find(n => n.id === nodeId);
    if (!node) return null;

    const incomingEdges = this.edges.filter(e => e.target === nodeId);
    const inputs: LogicTreeNode[] = [];

    incomingEdges.forEach(edge => {
      const sourceNode = this.nodes.find(n => n.id === edge.source);
      if (sourceNode) {
        const childTree = this.buildLogicTreeRecursive(sourceNode.id, new Set(visited), depth + 1);
        if (childTree) {
          inputs.push(childTree);
        }
      }
    });

    let code = '';
    let operation = '';

    switch (node.type) {
      case 'condition':
        code = this.generateConditionCode(node);
        break;
      case 'logic':
        operation = node.data?.parameters?.operation || 'AND';
        code = this.generateLogicGateCode(node, operation);
        break;
      default:
        code = `# ${node.type} node`;
    }

    return {
      id: nodeId,
      type: node.type as 'condition' | 'logic' | 'action',
      operation,
      inputs,
      code,
      depth
    };
  }

  private calculateExecutionOrder(): void {
    // Topological sort to determine execution order
    const inDegree = new Map<string, number>();
    const adjList = new Map<string, string[]>();

    // Initialize
    this.nodes.forEach(node => {
      inDegree.set(node.id, 0);
      adjList.set(node.id, []);
    });

    // Build adjacency list and calculate in-degrees
    this.edges.forEach(edge => {
      const sources = adjList.get(edge.source) || [];
      sources.push(edge.target);
      adjList.set(edge.source, sources);
      inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    });

    // Kahn's algorithm
    const queue: string[] = [];
    this.nodes.forEach(node => {
      if (inDegree.get(node.id) === 0) {
        queue.push(node.id);
      }
    });

    while (queue.length > 0) {
      const current = queue.shift()!;
      this.executionOrder.push(current);

      const neighbors = adjList.get(current) || [];
      neighbors.forEach(neighbor => {
        const newInDegree = (inDegree.get(neighbor) || 0) - 1;
        inDegree.set(neighbor, newInDegree);
        if (newInDegree === 0) {
          queue.push(neighbor);
        }
      });
    }
  }

  public generateStrategy(): GeneratedCode {
    const imports = this.generateImports();
    const strategyClass = this.generateStrategyClass();
    const indicatorCalculations = this.generateIndicatorCalculations();
    const conditionEvaluations = this.generateConditionEvaluations();
    const logicOperations = this.generateLogicOperations();
    const executionEngine = this.generateExecutionEngine();
    
    const complexityScore = this.calculateComplexityScore();
    const estimatedPerformance = this.estimatePerformance();

    return {
      strategy_class: strategyClass,
      indicator_calculations: indicatorCalculations,
      condition_evaluations: conditionEvaluations,
      logic_operations: logicOperations,
      execution_engine: executionEngine,
      imports,
      complexity_score: complexityScore,
      estimated_performance: estimatedPerformance
    };
  }

  private generateImports(): string[] {
    const imports = [
      'import pandas as pd',
      'import numpy as np',
      'from typing import Dict, List, Optional, Tuple',
      'from dataclasses import dataclass',
      'import talib',
      'from datetime import datetime',
      'import logging'
    ];

    // Add specific imports based on indicators used
    const indicators = Array.from(this.indicators.values());
    const hasAdvancedIndicators = indicators.some(ind => 
      ['ADX', 'BB', 'MACD', 'STOCH'].includes(ind.type)
    );

    if (hasAdvancedIndicators) {
      imports.push('from scipy import signal');
      imports.push('from sklearn.preprocessing import StandardScaler');
    }

    return imports;
  }

  private generateStrategyClass(): string {
    const dataSourceNodes = this.nodes.filter(n => n.type === 'dataSource');
    const actionNodes = this.nodes.filter(n => n.type === 'action');
    
    const className = 'AdvancedTradingStrategy';
    const symbol = dataSourceNodes[0]?.data?.parameters?.symbol || 'AAPL';
    const timeframe = dataSourceNodes[0]?.data?.parameters?.timeframe || '1h';

    return `
@dataclass
class StrategyConfig:
    symbol: str = "${symbol}"
    timeframe: str = "${timeframe}"
    lookback_period: int = 500
    risk_per_trade: float = 0.02
    max_positions: int = 1

class ${className}:
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.positions = {}
        self.indicators = {}
        self.conditions = {}
        self.logic_results = {}
        
    def initialize(self):
        """Initialize strategy components"""
        self.logger.info(f"Initializing {self.__class__.__name__} for {self.config.symbol}")
        
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate all technical indicators"""
        results = {}
        ${this.generateIndicatorCalculations()}
        return results
        
    def evaluate_conditions(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        """Evaluate all conditions"""
        results = {}
        ${this.generateConditionEvaluations()}
        return results
        
    def process_logic_gates(self, conditions: Dict) -> Dict:
        """Process all logic gate operations"""
        results = {}
        ${this.generateLogicOperations()}
        return results
        
    def execute_strategy(self, data: pd.DataFrame) -> List[Dict]:
        """Main strategy execution"""
        signals = []
        
        # Calculate indicators
        indicators = self.calculate_indicators(data)
        
        # Evaluate conditions
        conditions = self.evaluate_conditions(data, indicators)
        
        # Process logic gates
        logic_results = self.process_logic_gates(conditions)
        
        # Generate signals
        ${this.generateExecutionEngine()}
        
        return signals
`;
  }

  private generateIndicatorCalculations(): string {
    let code = '';
    const processedIndicators = new Set<string>();

    this.executionOrder.forEach(nodeId => {
      const indicator = this.indicators.get(nodeId);
      if (indicator && !processedIndicators.has(nodeId)) {
        code += this.generateIndicatorCode(indicator);
        processedIndicators.add(nodeId);
      }
    });

    return code;
  }

  private generateIndicatorCode(indicator: IndicatorConfig): string {
    const { id, type, parameters } = indicator;
    const period = parameters.period || 20;
    const source = parameters.source || 'close';

    switch (type) {
      case 'ADX':
        return `
        # ADX Calculation for ${id}
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        adx_values = talib.ADX(high, low, close, timeperiod=${period})
        di_plus_values = talib.PLUS_DI(high, low, close, timeperiod=${period})
        di_minus_values = talib.MINUS_DI(high, low, close, timeperiod=${period})
        
        results['${id}_adx'] = adx_values
        results['${id}_di_plus'] = di_plus_values
        results['${id}_di_minus'] = di_minus_values
        `;

      case 'BB':
        const multiplier = parameters.multiplier || 2.0;
        return `
        # Bollinger Bands Calculation for ${id}
        close_prices = data['${source}'].values
        
        bb_upper, bb_middle, bb_lower = talib.BBANDS(
            close_prices, 
            timeperiod=${period}, 
            nbdevup=${multiplier}, 
            nbdevdn=${multiplier}
        )
        bb_width = (bb_upper - bb_lower) / bb_middle * 100
        
        results['${id}_upper'] = bb_upper
        results['${id}_middle'] = bb_middle  
        results['${id}_lower'] = bb_lower
        results['${id}_width'] = bb_width
        `;

      case 'MACD':
        const fastPeriod = parameters.fastPeriod || 12;
        const slowPeriod = parameters.slowPeriod || 26;
        const signalPeriod = parameters.signalPeriod || 9;
        return `
        # MACD Calculation for ${id}
        close_prices = data['${source}'].values
        
        macd_line, signal_line, histogram = talib.MACD(
            close_prices,
            fastperiod=${fastPeriod},
            slowperiod=${slowPeriod}, 
            signalperiod=${signalPeriod}
        )
        
        results['${id}_macd_line'] = macd_line
        results['${id}_signal_line'] = signal_line
        results['${id}_histogram'] = histogram
        `;

      case 'RSI':
        return `
        # RSI Calculation for ${id}
        close_prices = data['${source}'].values
        rsi_values = talib.RSI(close_prices, timeperiod=${period})
        
        results['${id}_rsi_value'] = rsi_values
        `;

      case 'SMA':
        return `
        # SMA Calculation for ${id}
        source_prices = data['${source}'].values
        sma_values = talib.SMA(source_prices, timeperiod=${period})
        
        results['${id}_sma_value'] = sma_values
        `;

      case 'ATR':
        return `
        # ATR Calculation for ${id}
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        atr_values = talib.ATR(high, low, close, timeperiod=${period})
        
        results['${id}_atr_value'] = atr_values
        `;

      default:
        return `# Unknown indicator type: ${type}\n`;
    }
  }

  private generateConditionEvaluations(): string {
    let code = '';
    const conditionNodes = this.nodes.filter(n => n.type === 'condition');

    conditionNodes.forEach(node => {
      code += this.generateConditionCode(node);
    });

    return code;
  }

  private generateConditionCode(node: Node): string {
    const { id, data } = node;
    const conditionType = data?.parameters?.conditionType || 'comparison';
    const condition = data?.parameters?.condition || 'greater_than';
    const value = data?.parameters?.value || 0;
    const value2 = data?.parameters?.value2;

    // Find the input indicator
    const incomingEdge = this.edges.find(e => e.target === id);
    if (!incomingEdge) {
      return `# No input found for condition ${id}\n`;
    }

    const sourceNode = this.nodes.find(n => n.id === incomingEdge.source);
    if (!sourceNode) {
      return `# Source node not found for condition ${id}\n`;
    }

    let inputVariable = '';
    if (sourceNode.type === 'technicalIndicator') {
      const sourceHandle = incomingEdge.sourceHandle || 'output-1';
      const indicator = this.indicators.get(sourceNode.id);
      inputVariable = this.getIndicatorOutputVariable(sourceNode.id, sourceHandle, indicator?.type);
    }

    switch (condition) {
      case 'greater_than':
        return `
        # Condition: ${id} - Greater Than
        results['${id}'] = indicators['${inputVariable}'] > ${value}
        `;

      case 'less_than':
        return `
        # Condition: ${id} - Less Than  
        results['${id}'] = indicators['${inputVariable}'] < ${value}
        `;

      case 'crossover':
        return `
        # Condition: ${id} - Crossover
        current_value = indicators['${inputVariable}'][-1]
        previous_value = indicators['${inputVariable}'][-2] if len(indicators['${inputVariable}']) > 1 else current_value
        results['${id}'] = (previous_value <= ${value}) & (current_value > ${value})
        `;

      case 'crossunder':
        return `
        # Condition: ${id} - Crossunder
        current_value = indicators['${inputVariable}'][-1] 
        previous_value = indicators['${inputVariable}'][-2] if len(indicators['${inputVariable}']) > 1 else current_value
        results['${id}'] = (previous_value >= ${value}) & (current_value < ${value})
        `;

      case 'range':
        return `
        # Condition: ${id} - Range
        current_value = indicators['${inputVariable}'][-1]
        results['${id}'] = (current_value >= ${value}) & (current_value <= ${value2 || value + 10})
        `;

      default:
        return `
        # Condition: ${id} - ${condition}
        results['${id}'] = indicators['${inputVariable}'] > ${value}  # Default comparison
        `;
    }
  }

  private getIndicatorOutputVariable(nodeId: string, sourceHandle: string, indicatorType?: string): string {
    const handleMapping: Record<string, Record<string, string>> = {
      'ADX': {
        'output-1': `${nodeId}_adx`,
        'output-2': `${nodeId}_di_plus`, 
        'output-3': `${nodeId}_di_minus`
      },
      'BB': {
        'output-1': `${nodeId}_upper`,
        'output-2': `${nodeId}_middle`,
        'output-3': `${nodeId}_lower`,
        'output-4': `${nodeId}_width`
      },
      'MACD': {
        'output-1': `${nodeId}_macd_line`,
        'output-2': `${nodeId}_signal_line`,
        'output-3': `${nodeId}_histogram`
      },
      'RSI': {
        'output-1': `${nodeId}_rsi_value`,
        'output-2': `${nodeId}_rsi_value`
      }
    };

    const mapping = handleMapping[indicatorType || ''];
    return mapping?.[sourceHandle] || `${nodeId}_value`;
  }

  private generateLogicOperations(): string {
    let code = '';
    const logicNodes = this.nodes.filter(n => n.type === 'logic');

    logicNodes.forEach(node => {
      code += this.generateLogicGateCode(node, node.data?.parameters?.operation || 'AND');
    });

    return code;
  }

  private generateLogicGateCode(node: Node, operation: string): string {
    const { id } = node;
    const incomingEdges = this.edges.filter(e => e.target === id);
    
    if (incomingEdges.length === 0) {
      return `# No inputs for logic gate ${id}\n`;
    }

    const inputConditions = incomingEdges.map(edge => {
      const sourceNode = this.nodes.find(n => n.id === edge.source);
      if (sourceNode?.type === 'condition') {
        return `conditions['${edge.source}']`;
      } else if (sourceNode?.type === 'logic') {
        return `results['${edge.source}']`;
      }
      return 'False';
    });

    switch (operation.toUpperCase()) {
      case 'AND':
        return `
        # Logic Gate: ${id} - AND
        results['${id}'] = ${inputConditions.join(' & ')}
        `;

      case 'OR':
        return `
        # Logic Gate: ${id} - OR  
        results['${id}'] = ${inputConditions.join(' | ')}
        `;

      case 'NOT':
        return `
        # Logic Gate: ${id} - NOT
        results['${id}'] = ~(${inputConditions[0] || 'False'})
        `;

      case 'XOR':
        return `
        # Logic Gate: ${id} - XOR
        results['${id}'] = ${inputConditions.join(' ^ ')}
        `;

      default:
        return `
        # Logic Gate: ${id} - ${operation}
        results['${id}'] = ${inputConditions.join(' & ')}  # Default to AND
        `;
    }
  }

  private generateExecutionEngine(): string {
    const actionNodes = this.nodes.filter(n => n.type === 'action');
    let code = '';

    actionNodes.forEach(actionNode => {
      const incomingEdge = this.edges.find(e => e.target === actionNode.id);
      if (incomingEdge) {
        const sourceNode = this.nodes.find(n => n.id === incomingEdge.source);
        let signalCondition = 'False';
        
        if (sourceNode?.type === 'logic') {
          signalCondition = `logic_results['${sourceNode.id}']`;
        } else if (sourceNode?.type === 'condition') {
          signalCondition = `conditions['${sourceNode.id}']`;
        }

        code += this.generateActionCode(actionNode, signalCondition);
      }
    });

    return code;
  }

  private generateActionCode(node: Node, signalCondition = 'True'): string {
    const { id, data } = node;
    const action = data?.parameters?.action || 'buy';
    const quantity = data?.parameters?.quantity || 10;
    const orderType = data?.parameters?.order_type || 'market';
    const stopLoss = data?.parameters?.stop_loss || 2.0;
    const takeProfit = data?.parameters?.take_profit || 4.0;

    return `
        # Action: ${id} - ${action.toUpperCase()}
        if ${signalCondition}:
            signal = {
                'timestamp': data.index[-1],
                'action': '${action}',
                'symbol': self.config.symbol,
                'quantity': ${quantity},
                'order_type': '${orderType}',
                'stop_loss_pct': ${stopLoss},
                'take_profit_pct': ${takeProfit},
                'signal_id': '${id}',
                'confidence': 1.0
            }
            signals.append(signal)
            self.logger.info(f"Generated {action} signal: {signal}")
        `;
  }

  private calculateComplexityScore(): number {
    let score = 0;
    
    // Base complexity from node count
    score += this.nodes.length * 5;
    
    // Indicator complexity
    const indicatorCount = this.nodes.filter(n => n.type === 'technicalIndicator').length;
    score += indicatorCount * 10;
    
    // Multi-output indicator complexity
    const multiOutputIndicators = Array.from(this.indicators.values()).filter(
      ind => ['ADX', 'BB', 'MACD'].includes(ind.type)
    ).length;
    score += multiOutputIndicators * 15;
    
    // Logic gate complexity
    const logicNodes = this.nodes.filter(n => n.type === 'logic');
    score += logicNodes.length * 8;
    
    // Nesting depth complexity
    const maxDepth = Math.max(0, ...Array.from(this.logicTrees.values()).map(tree => tree.depth));
    score += maxDepth * 12;
    
    return Math.min(score, 100);
  }

  private estimatePerformance(): GeneratedCode['estimated_performance'] {
    const indicatorCount = this.nodes.filter(n => n.type === 'technicalIndicator').length;
    const logicDepth = Math.max(0, ...Array.from(this.logicTrees.values()).map(tree => tree.depth));
    const complexityScore = this.calculateComplexityScore();
    
    // Estimate execution time (ms)
    let executionTime = 10; // Base time
    executionTime += indicatorCount * 3; // Indicator calculation time
    executionTime += logicDepth * 2; // Logic processing time
    executionTime += this.edges.length * 0.5; // Connection processing time
    
    // Estimate memory usage (MB)
    let memoryUsage = 5; // Base memory
    memoryUsage += indicatorCount * 2; // Indicator arrays
    memoryUsage += this.nodes.length * 0.1; // Node overhead
    
    // Determine CPU intensity
    let cpuIntensity: 'low' | 'medium' | 'high' = 'low';
    if (complexityScore > 70) cpuIntensity = 'high';
    else if (complexityScore > 40) cpuIntensity = 'medium';
    
    return {
      execution_time_ms: Math.round(executionTime),
      memory_usage_mb: Math.round(memoryUsage * 10) / 10,
      cpu_intensity: cpuIntensity
    };
  }
}

// Export function for use in components
export const generateAdvancedStrategy = (nodes: Node[], edges: Edge[]): GeneratedCode => {
  const generator = new AdvancedCodeGenerator(nodes, edges);
  return generator.generateStrategy();
};