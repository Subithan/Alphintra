import { Node, Edge } from 'reactflow';

export interface ExecutionConfig {
  strategy_id: string;
  symbol: string;
  timeframe: string;
  live_trading: boolean;
  paper_trading: boolean;
  risk_management: {
    max_position_size: number;
    max_drawdown: number;
    stop_loss_enabled: boolean;
    take_profit_enabled: boolean;
  };
  execution_mode: 'backtest' | 'paper' | 'live';
}

export interface MarketData {
  timestamp: Date;
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SignalResult {
  signal_id: string;
  timestamp: Date;
  action: 'buy' | 'sell' | 'hold';
  symbol: string;
  quantity: number;
  price: number;
  confidence: number;
  metadata: {
    indicators: Record<string, number>;
    conditions: Record<string, boolean>;
    logic_results: Record<string, boolean>;
  };
}

export interface ExecutionResult {
  execution_id: string;
  timestamp: Date;
  signals: SignalResult[];
  performance_metrics: {
    execution_time_ms: number;
    memory_usage_mb: number;
    indicator_calculations: number;
    condition_evaluations: number;
    logic_operations: number;
  };
  errors: string[];
  warnings: string[];
}

export interface IndicatorCache {
  [key: string]: {
    values: number[];
    last_updated: Date;
    parameters: Record<string, any>;
  };
}

export class RealTimeExecutionEngine {
  private config: ExecutionConfig;
  private nodes: Node[];
  private edges: Edge[];
  private indicatorCache: IndicatorCache = {};
  private marketDataBuffer: MarketData[] = [];
  private executionHistory: ExecutionResult[] = [];
  private isRunning = false;

  constructor(config: ExecutionConfig, nodes: Node[], edges: Edge[]) {
    this.config = config;
    this.nodes = nodes;
    this.edges = edges;
    this.initializeEngine();
  }

  private initializeEngine(): void {
    // Initialize indicator cache
    this.initializeIndicatorCache();
    
    // Validate workflow before execution
    this.validateWorkflowForExecution();
    
    console.log('Real-time execution engine initialized');
  }

  private initializeIndicatorCache(): void {
    const indicatorNodes = this.nodes.filter(n => n.type === 'technicalIndicator');
    
    indicatorNodes.forEach(node => {
      const indicatorType = node.data?.parameters?.indicator || 'SMA';
      const period = node.data?.parameters?.period || 20;
      
      this.indicatorCache[node.id] = {
        values: [],
        last_updated: new Date(0),
        parameters: node.data?.parameters || {}
      };
    });
  }

  private validateWorkflowForExecution(): void {
    const dataSourceNodes = this.nodes.filter(n => n.type === 'dataSource');
    const actionNodes = this.nodes.filter(n => n.type === 'action');
    
    if (dataSourceNodes.length === 0) {
      throw new Error('Workflow must have at least one data source for execution');
    }
    
    if (actionNodes.length === 0) {
      throw new Error('Workflow must have at least one action node for execution');
    }
  }

  public async executeStrategy(marketData: MarketData[]): Promise<ExecutionResult> {
    const startTime = performance.now();
    const executionId = `exec_${Date.now()}`;
    
    try {
      // Update market data buffer
      this.updateMarketDataBuffer(marketData);
      
      // Calculate indicators
      const indicators = await this.calculateIndicators();
      
      // Evaluate conditions
      const conditions = await this.evaluateConditions(indicators);
      
      // Process logic gates
      const logicResults = await this.processLogicGates(conditions);
      
      // Generate signals
      const signals = await this.generateSignals(indicators, conditions, logicResults);
      
      // Calculate performance metrics
      const executionTime = performance.now() - startTime;
      const performanceMetrics = this.calculatePerformanceMetrics(executionTime);
      
      const result: ExecutionResult = {
        execution_id: executionId,
        timestamp: new Date(),
        signals,
        performance_metrics: performanceMetrics,
        errors: [],
        warnings: []
      };
      
      this.executionHistory.push(result);
      return result;
      
    } catch (error) {
      console.error('Strategy execution error:', error);
      return {
        execution_id: executionId,
        timestamp: new Date(),
        signals: [],
        performance_metrics: {
          execution_time_ms: performance.now() - startTime,
          memory_usage_mb: 0,
          indicator_calculations: 0,
          condition_evaluations: 0,
          logic_operations: 0
        },
        errors: [error instanceof Error ? error.message : 'Unknown error'],
        warnings: []
      };
    }
  }

  private updateMarketDataBuffer(newData: MarketData[]): void {
    this.marketDataBuffer.push(...newData);
    
    // Keep only last 1000 bars to manage memory
    if (this.marketDataBuffer.length > 1000) {
      this.marketDataBuffer = this.marketDataBuffer.slice(-1000);
    }
  }

  private async calculateIndicators(): Promise<Record<string, Record<string, number[]>>> {
    const indicators: Record<string, Record<string, number[]>> = {};
    const indicatorNodes = this.nodes.filter(n => n.type === 'technicalIndicator');
    
    for (const node of indicatorNodes) {
      const indicatorType = node.data?.parameters?.indicator || 'SMA';
      const period = node.data?.parameters?.period || 20;
      
      // Check if we have enough data
      if (this.marketDataBuffer.length < period) {
        console.warn(`Insufficient data for ${indicatorType} (need ${period}, have ${this.marketDataBuffer.length})`);
        continue;
      }
      
      try {
        const calculatedValues = await this.calculateSingleIndicator(node, indicatorType);
        indicators[node.id] = calculatedValues;
        
        // Update cache
        Object.entries(calculatedValues).forEach(([output, values]) => {
          const cacheKey = `${node.id}_${output}`;
          this.indicatorCache[cacheKey] = {
            values,
            last_updated: new Date(),
            parameters: node.data?.parameters || {}
          };
        });
        
      } catch (error) {
        console.error(`Error calculating ${indicatorType} for node ${node.id}:`, error);
      }
    }
    
    return indicators;
  }

  private async calculateSingleIndicator(node: Node, indicatorType: string): Promise<Record<string, number[]>> {
    const parameters = node.data?.parameters || {};
    const period = parameters.period || 20;
    const source = parameters.source || 'close';
    
    const sourceData = this.marketDataBuffer.map(bar => {
      switch (source) {
        case 'open': return bar.open;
        case 'high': return bar.high;
        case 'low': return bar.low;
        case 'close': return bar.close;
        case 'volume': return bar.volume;
        default: return bar.close;
      }
    });

    switch (indicatorType) {
      case 'ADX':
        return await this.calculateADX(period);
        
      case 'BB':
        return await this.calculateBollingerBands(sourceData, period, parameters.multiplier || 2.0);
        
      case 'MACD':
        return await this.calculateMACD(
          sourceData, 
          parameters.fastPeriod || 12,
          parameters.slowPeriod || 26,
          parameters.signalPeriod || 9
        );
        
      case 'RSI':
        return await this.calculateRSI(sourceData, period);
        
      case 'SMA':
        return await this.calculateSMA(sourceData, period);
        
      case 'ATR':
        return await this.calculateATR(period);
        
      default:
        console.warn(`Unknown indicator type: ${indicatorType}`);
        return { value: sourceData };
    }
  }

  private async calculateADX(period: number): Promise<Record<string, number[]>> {
    const high = this.marketDataBuffer.map(bar => bar.high);
    const low = this.marketDataBuffer.map(bar => bar.low);
    const close = this.marketDataBuffer.map(bar => bar.close);
    
    // Simplified ADX calculation (in production, use proper ADX algorithm)
    const adx = this.calculateTechnicalIndicator('ADX', { high, low, close, period });
    const diPlus = this.calculateTechnicalIndicator('DI_PLUS', { high, low, close, period });
    const diMinus = this.calculateTechnicalIndicator('DI_MINUS', { high, low, close, period });
    
    return {
      adx,
      di_plus: diPlus,
      di_minus: diMinus
    };
  }

  private async calculateBollingerBands(
    sourceData: number[], 
    period: number, 
    multiplier: number
  ): Promise<Record<string, number[]>> {
    const sma = this.calculateMovingAverage(sourceData, period);
    const std = this.calculateStandardDeviation(sourceData, period);
    
    const upper = sma.map((avg, i) => avg + (std[i] * multiplier));
    const lower = sma.map((avg, i) => avg - (std[i] * multiplier));
    const width = upper.map((up, i) => ((up - lower[i]) / sma[i]) * 100);
    
    return {
      upper,
      middle: sma,
      lower,
      width
    };
  }

  private async calculateMACD(
    sourceData: number[], 
    fastPeriod: number, 
    slowPeriod: number, 
    signalPeriod: number
  ): Promise<Record<string, number[]>> {
    const fastEMA = this.calculateEMA(sourceData, fastPeriod);
    const slowEMA = this.calculateEMA(sourceData, slowPeriod);
    
    const macdLine = fastEMA.map((fast, i) => fast - slowEMA[i]);
    const signalLine = this.calculateEMA(macdLine, signalPeriod);
    const histogram = macdLine.map((macd, i) => macd - signalLine[i]);
    
    return {
      macd_line: macdLine,
      signal_line: signalLine,
      histogram
    };
  }

  private async calculateRSI(sourceData: number[], period: number): Promise<Record<string, number[]>> {
    const changes = sourceData.slice(1).map((price, i) => price - sourceData[i]);
    const gains = changes.map(change => change > 0 ? change : 0);
    const losses = changes.map(change => change < 0 ? Math.abs(change) : 0);
    
    const avgGain = this.calculateMovingAverage(gains, period);
    const avgLoss = this.calculateMovingAverage(losses, period);
    
    const rs = avgGain.map((gain, i) => avgLoss[i] === 0 ? 100 : gain / avgLoss[i]);
    const rsi = rs.map(rs_val => 100 - (100 / (1 + rs_val)));
    
    return { rsi_value: rsi };
  }

  private async calculateSMA(sourceData: number[], period: number): Promise<Record<string, number[]>> {
    const sma = this.calculateMovingAverage(sourceData, period);
    return { sma_value: sma };
  }

  private async calculateATR(period: number): Promise<Record<string, number[]>> {
    const trueRanges: number[] = [];
    
    for (let i = 1; i < this.marketDataBuffer.length; i++) {
      const current = this.marketDataBuffer[i];
      const previous = this.marketDataBuffer[i - 1];
      
      const highLow = current.high - current.low;
      const highClosePrev = Math.abs(current.high - previous.close);
      const lowClosePrev = Math.abs(current.low - previous.close);
      
      trueRanges.push(Math.max(highLow, highClosePrev, lowClosePrev));
    }
    
    const atr = this.calculateMovingAverage(trueRanges, period);
    return { atr_value: atr };
  }

  // Helper calculation methods
  private calculateMovingAverage(data: number[], period: number): number[] {
    const result: number[] = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const avg = slice.reduce((sum, val) => sum + val, 0) / period;
      result.push(avg);
    }
    
    return result;
  }

  private calculateEMA(data: number[], period: number): number[] {
    const k = 2 / (period + 1);
    const result: number[] = [];
    
    // Start with SMA for first value
    result.push(data.slice(0, period).reduce((sum, val) => sum + val, 0) / period);
    
    for (let i = period; i < data.length; i++) {
      const ema = (data[i] * k) + (result[result.length - 1] * (1 - k));
      result.push(ema);
    }
    
    return result;
  }

  private calculateStandardDeviation(data: number[], period: number): number[] {
    const result: number[] = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const mean = slice.reduce((sum, val) => sum + val, 0) / period;
      const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period;
      result.push(Math.sqrt(variance));
    }
    
    return result;
  }

  private calculateTechnicalIndicator(type: string, params: any): number[] {
    // Placeholder for complex technical indicators
    // In production, use libraries like TA-Lib or implement full algorithms
    switch (type) {
      case 'ADX':
        return this.calculateMovingAverage(params.close, params.period);
      case 'DI_PLUS':
        return this.calculateMovingAverage(params.high, params.period);
      case 'DI_MINUS':
        return this.calculateMovingAverage(params.low, params.period);
      default:
        return params.close || [];
    }
  }

  private async evaluateConditions(indicators: Record<string, Record<string, number[]>>): Promise<Record<string, boolean>> {
    const conditions: Record<string, boolean> = {};
    const conditionNodes = this.nodes.filter(n => n.type === 'condition');
    
    for (const node of conditionNodes) {
      try {
        const result = await this.evaluateSingleCondition(node, indicators);
        conditions[node.id] = result;
      } catch (error) {
        console.error(`Error evaluating condition ${node.id}:`, error);
        conditions[node.id] = false;
      }
    }
    
    return conditions;
  }

  private async evaluateSingleCondition(
    node: Node, 
    indicators: Record<string, Record<string, number[]>>
  ): Promise<boolean> {
    const condition = node.data?.parameters?.condition || 'greater_than';
    const value = node.data?.parameters?.value || 0;
    const value2 = node.data?.parameters?.value2;
    
    // Find input indicator
    const incomingEdge = this.edges.find(e => e.target === node.id);
    if (!incomingEdge) return false;
    
    const sourceNode = this.nodes.find(n => n.id === incomingEdge.source);
    if (!sourceNode || sourceNode.type !== 'technicalIndicator') return false;
    
    const indicatorData = indicators[sourceNode.id];
    if (!indicatorData) return false;
    
    // Get the specific output based on handle
    const sourceHandle = incomingEdge.sourceHandle || 'output-1';
    const outputKey = this.getIndicatorOutputKey(sourceNode, sourceHandle);
    const values = indicatorData[outputKey];
    
    if (!values || values.length === 0) return false;
    
    const currentValue = values[values.length - 1];
    const previousValue = values.length > 1 ? values[values.length - 2] : currentValue;
    
    switch (condition) {
      case 'greater_than':
        return currentValue > value;
      case 'less_than':
        return currentValue < value;
      case 'equal_to':
        return Math.abs(currentValue - value) < 0.0001;
      case 'crossover':
        return previousValue <= value && currentValue > value;
      case 'crossunder':
        return previousValue >= value && currentValue < value;
      case 'range':
        return currentValue >= value && currentValue <= (value2 || value + 10);
      case 'outside_range':
        return currentValue < value || currentValue > (value2 || value + 10);
      default:
        return currentValue > value;
    }
  }

  private getIndicatorOutputKey(sourceNode: Node, sourceHandle: string): string {
    const indicatorType = sourceNode.data?.parameters?.indicator;
    
    const handleMapping: Record<string, Record<string, string>> = {
      'ADX': {
        'output-1': 'adx',
        'output-2': 'di_plus',
        'output-3': 'di_minus'
      },
      'BB': {
        'output-1': 'upper',
        'output-2': 'middle', 
        'output-3': 'lower',
        'output-4': 'width'
      },
      'MACD': {
        'output-1': 'macd_line',
        'output-2': 'signal_line',
        'output-3': 'histogram'
      },
      'RSI': {
        'output-1': 'rsi_value',
        'output-2': 'rsi_value'
      },
      'SMA': {
        'output-1': 'sma_value',
        'output-2': 'sma_value'
      },
      'ATR': {
        'output-1': 'atr_value',
        'output-2': 'atr_value'
      }
    };
    
    const mapping = handleMapping[indicatorType || ''];
    return mapping?.[sourceHandle] || 'value';
  }

  private async processLogicGates(conditions: Record<string, boolean>): Promise<Record<string, boolean>> {
    const logicResults: Record<string, boolean> = {};
    const logicNodes = this.nodes.filter(n => n.type === 'logic');
    
    // Process logic gates in topological order
    const processedNodes = new Set<string>();
    const remainingNodes = [...logicNodes];
    
    while (remainingNodes.length > 0) {
      const processableNodes = remainingNodes.filter(node => {
        const incomingEdges = this.edges.filter(e => e.target === node.id);
        return incomingEdges.every(edge => {
          const sourceNode = this.nodes.find(n => n.id === edge.source);
          return sourceNode?.type === 'condition' || 
                 (sourceNode?.type === 'logic' && processedNodes.has(sourceNode.id));
        });
      });
      
      if (processableNodes.length === 0) {
        console.warn('Circular dependency detected in logic gates');
        break;
      }
      
      for (const node of processableNodes) {
        const result = await this.processSingleLogicGate(node, conditions, logicResults);
        logicResults[node.id] = result;
        processedNodes.add(node.id);
        
        const index = remainingNodes.indexOf(node);
        if (index > -1) {
          remainingNodes.splice(index, 1);
        }
      }
    }
    
    return logicResults;
  }

  private async processSingleLogicGate(
    node: Node, 
    conditions: Record<string, boolean>,
    logicResults: Record<string, boolean>
  ): Promise<boolean> {
    const operation = node.data?.parameters?.operation || 'AND';
    const incomingEdges = this.edges.filter(e => e.target === node.id);
    
    const inputValues: boolean[] = [];
    
    for (const edge of incomingEdges) {
      const sourceNode = this.nodes.find(n => n.id === edge.source);
      if (sourceNode?.type === 'condition') {
        inputValues.push(conditions[edge.source] || false);
      } else if (sourceNode?.type === 'logic') {
        inputValues.push(logicResults[edge.source] || false);
      }
    }
    
    if (inputValues.length === 0) return false;
    
    switch (operation.toUpperCase()) {
      case 'AND':
        return inputValues.every(val => val);
      case 'OR':
        return inputValues.some(val => val);
      case 'NOT':
        return !inputValues[0];
      case 'XOR':
        return inputValues.reduce((acc, val) => acc !== val, false);
      default:
        return inputValues.every(val => val); // Default to AND
    }
  }

  private async generateSignals(
    indicators: Record<string, Record<string, number[]>>,
    conditions: Record<string, boolean>,
    logicResults: Record<string, boolean>
  ): Promise<SignalResult[]> {
    const signals: SignalResult[] = [];
    const actionNodes = this.nodes.filter(n => n.type === 'action');
    
    for (const actionNode of actionNodes) {
      const incomingEdge = this.edges.find(e => e.target === actionNode.id);
      if (!incomingEdge) continue;
      
      const sourceNode = this.nodes.find(n => n.id === incomingEdge.source);
      if (!sourceNode) continue;
      
      let shouldExecute = false;
      
      if (sourceNode.type === 'condition') {
        shouldExecute = conditions[sourceNode.id] || false;
      } else if (sourceNode.type === 'logic') {
        shouldExecute = logicResults[sourceNode.id] || false;
      }
      
      if (shouldExecute) {
        const signal = this.createSignal(actionNode, indicators, conditions, logicResults);
        signals.push(signal);
      }
    }
    
    return signals;
  }

  private createSignal(
    actionNode: Node,
    indicators: Record<string, Record<string, number[]>>,
    conditions: Record<string, boolean>,
    logicResults: Record<string, boolean>
  ): SignalResult {
    const action = actionNode.data?.parameters?.action || 'buy';
    const quantity = actionNode.data?.parameters?.quantity || 10;
    const currentPrice = this.marketDataBuffer[this.marketDataBuffer.length - 1]?.close || 0;
    
    // Flatten indicators for metadata
    const flattenedIndicators: Record<string, number> = {};
    Object.entries(indicators).forEach(([nodeId, outputs]) => {
      Object.entries(outputs).forEach(([outputKey, values]) => {
        if (values.length > 0) {
          flattenedIndicators[`${nodeId}_${outputKey}`] = values[values.length - 1];
        }
      });
    });
    
    return {
      signal_id: `${actionNode.id}_${Date.now()}`,
      timestamp: new Date(),
      action: action as 'buy' | 'sell' | 'hold',
      symbol: this.config.symbol,
      quantity,
      price: currentPrice,
      confidence: 1.0,
      metadata: {
        indicators: flattenedIndicators,
        conditions,
        logic_results: logicResults
      }
    };
  }

  private calculatePerformanceMetrics(executionTime: number): ExecutionResult['performance_metrics'] {
    const indicatorCount = this.nodes.filter(n => n.type === 'technicalIndicator').length;
    const conditionCount = this.nodes.filter(n => n.type === 'condition').length;
    const logicCount = this.nodes.filter(n => n.type === 'logic').length;
    
    return {
      execution_time_ms: Math.round(executionTime),
      memory_usage_mb: Math.round((this.marketDataBuffer.length * 0.001 + Object.keys(this.indicatorCache).length * 0.01) * 10) / 10,
      indicator_calculations: indicatorCount,
      condition_evaluations: conditionCount,
      logic_operations: logicCount
    };
  }

  public getExecutionHistory(): ExecutionResult[] {
    return this.executionHistory;
  }

  public clearCache(): void {
    this.indicatorCache = {};
    this.marketDataBuffer = [];
    this.executionHistory = [];
  }

  public start(): void {
    this.isRunning = true;
    console.log('Real-time execution engine started');
  }

  public stop(): void {
    this.isRunning = false;
    console.log('Real-time execution engine stopped');
  }

  public isEngineRunning(): boolean {
    return this.isRunning;
  }
}

// Export function for creating execution engine
export const createExecutionEngine = (
  config: ExecutionConfig, 
  nodes: Node[], 
  edges: Edge[]
): RealTimeExecutionEngine => {
  return new RealTimeExecutionEngine(config, nodes, edges);
};