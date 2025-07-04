import { EventEmitter } from 'events';
import { MarketDataPoint, MarketDataManager } from '../data/market-data-client';
import { GeneratedCode } from '../code-generator';

// Strategy execution interfaces
export interface StrategyExecution {
  id: string;
  strategyId: string;
  status: 'pending' | 'running' | 'paused' | 'stopped' | 'completed' | 'error';
  mode: 'backtest' | 'paper' | 'live';
  parameters: StrategyParameters;
  startTime: Date;
  endTime?: Date;
  currentTime?: Date;
  progress: number; // 0-100
  performance: PerformanceMetrics;
  positions: Position[];
  orders: Order[];
  logs: ExecutionLog[];
  errors: ExecutionError[];
}

export interface StrategyParameters {
  symbol: string;
  timeframe: string;
  startDate: Date;
  endDate: Date;
  initialCapital: number;
  commission: number;
  slippage: number;
  maxPositions: number;
  riskPerTrade: number;
  stopLoss?: number;
  takeProfit?: number;
  customParameters: Record<string, any>;
}

export interface PerformanceMetrics {
  totalReturn: number;
  totalReturnPercent: number;
  annualizedReturn: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  maxDrawdownPercent: number;
  calmarRatio: number;
  winRate: number;
  profitFactor: number;
  avgWin: number;
  avgLoss: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  currentDrawdown: number;
  currentCapital: number;
  unrealizedPnL: number;
  realizedPnL: number;
  commission: number;
  slippage: number;
}

export interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  entryTime: Date;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  stopLoss?: number;
  takeProfit?: number;
  status: 'open' | 'closed';
}

export interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  quantity: number;
  price?: number;
  stopPrice?: number;
  timeInForce: 'GTC' | 'IOC' | 'FOK' | 'DAY';
  status: 'pending' | 'filled' | 'cancelled' | 'rejected' | 'partial';
  filledQuantity: number;
  avgFillPrice: number;
  timestamp: Date;
  fillTime?: Date;
  commission: number;
  slippage: number;
  reason?: string;
}

export interface ExecutionLog {
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  data?: any;
}

export interface ExecutionError {
  timestamp: Date;
  type: 'compilation' | 'runtime' | 'data' | 'network' | 'validation';
  message: string;
  stack?: string;
  fatal: boolean;
}

export interface TradingSignal {
  symbol: string;
  timestamp: Date;
  action: 'buy' | 'sell' | 'hold';
  confidence: number; // 0-1
  quantity?: number;
  price?: number;
  stopLoss?: number;
  takeProfit?: number;
  reason: string;
  metadata: Record<string, any>;
}

// Strategy runtime environment
export class StrategyRuntime {
  private strategyCode: string;
  private parameters: StrategyParameters;
  private data: MarketDataPoint[] = [];
  private indicators: Record<string, number[]> = {};
  private positions: Position[] = [];
  private orders: Order[] = [];
  private logs: ExecutionLog[] = [];
  private currentBar = 0;

  constructor(generatedCode: GeneratedCode, parameters: StrategyParameters) {
    this.strategyCode = generatedCode.strategy;
    this.parameters = parameters;
  }

  /**
   * Initialize the strategy runtime
   */
  async initialize(): Promise<void> {
    try {
      // In a real implementation, this would compile and validate the Python code
      // For now, we'll simulate the strategy execution
      this.log('info', 'Strategy runtime initialized', { 
        symbol: this.parameters.symbol,
        timeframe: this.parameters.timeframe 
      });
    } catch (error) {
      this.log('error', 'Failed to initialize strategy runtime', { error });
      throw error;
    }
  }

  /**
   * Process a new market data point
   */
  async onData(dataPoint: MarketDataPoint): Promise<TradingSignal[]> {
    try {
      this.data.push(dataPoint);
      this.currentBar++;

      // Update indicators (simplified simulation)
      this.updateIndicators(dataPoint);

      // Generate trading signals (simplified simulation)
      const signals = this.generateSignals(dataPoint);

      // Update positions with current prices
      this.updatePositions(dataPoint);

      this.log('debug', 'Processed market data', {
        symbol: dataPoint.symbol,
        timestamp: dataPoint.timestamp,
        price: dataPoint.close,
        signals: signals.length
      });

      return signals;
    } catch (error) {
      this.log('error', 'Error processing market data', { error, dataPoint });
      return [];
    }
  }

  /**
   * Execute a trading signal
   */
  async executeSignal(signal: TradingSignal): Promise<Order | null> {
    try {
      // Risk management checks
      if (!this.validateSignal(signal)) {
        this.log('warn', 'Signal rejected by risk management', { signal });
        return null;
      }

      // Create order
      const order: Order = {
        id: `order_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        symbol: signal.symbol,
        side: signal.action === 'buy' ? 'buy' : 'sell',
        type: 'market',
        quantity: signal.quantity || this.calculatePositionSize(signal),
        timeInForce: 'GTC',
        status: 'pending',
        filledQuantity: 0,
        avgFillPrice: 0,
        timestamp: signal.timestamp,
        commission: 0,
        slippage: 0
      };

      // Simulate order execution
      await this.simulateOrderExecution(order, signal);

      this.orders.push(order);
      this.log('info', 'Order executed', { order });

      return order;
    } catch (error) {
      this.log('error', 'Failed to execute signal', { error, signal });
      return null;
    }
  }

  /**
   * Close a position
   */
  async closePosition(positionId: string, reason: string = 'manual'): Promise<Order | null> {
    const position = this.positions.find(p => p.id === positionId && p.status === 'open');
    if (!position) {
      this.log('warn', 'Position not found or already closed', { positionId });
      return null;
    }

    const signal: TradingSignal = {
      symbol: position.symbol,
      timestamp: new Date(),
      action: position.side === 'long' ? 'sell' : 'buy',
      confidence: 1.0,
      quantity: position.quantity,
      reason: `Close position: ${reason}`,
      metadata: { positionId }
    };

    return this.executeSignal(signal);
  }

  /**
   * Get current performance metrics
   */
  getPerformanceMetrics(): PerformanceMetrics {
    const openPositions = this.positions.filter(p => p.status === 'open');
    const closedPositions = this.positions.filter(p => p.status === 'closed');
    
    // Calculate realized PnL from closed positions
    const realizedPnL = closedPositions.reduce((sum, pos) => {
      return sum + (pos.side === 'long' ? 
        (pos.currentPrice - pos.entryPrice) * pos.quantity :
        (pos.entryPrice - pos.currentPrice) * pos.quantity);
    }, 0);

    // Calculate unrealized PnL from open positions
    const unrealizedPnL = openPositions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0);

    // Calculate total commission and slippage
    const totalCommission = this.orders
      .filter(o => o.status === 'filled')
      .reduce((sum, o) => sum + o.commission, 0);
    
    const totalSlippage = this.orders
      .filter(o => o.status === 'filled')
      .reduce((sum, o) => sum + o.slippage, 0);

    const currentCapital = this.parameters.initialCapital + realizedPnL + unrealizedPnL - totalCommission - totalSlippage;
    const totalReturn = currentCapital - this.parameters.initialCapital;
    const totalReturnPercent = (totalReturn / this.parameters.initialCapital) * 100;

    // Calculate trade statistics
    const trades = this.calculateTradeStatistics();
    const drawdown = this.calculateDrawdown();

    return {
      totalReturn,
      totalReturnPercent,
      annualizedReturn: this.calculateAnnualizedReturn(totalReturnPercent),
      sharpeRatio: this.calculateSharpeRatio(),
      sortinoRatio: this.calculateSortinoRatio(),
      maxDrawdown: drawdown.maxDrawdown,
      maxDrawdownPercent: drawdown.maxDrawdownPercent,
      calmarRatio: totalReturnPercent / Math.max(drawdown.maxDrawdownPercent, 0.01),
      winRate: trades.winRate,
      profitFactor: trades.profitFactor,
      avgWin: trades.avgWin,
      avgLoss: trades.avgLoss,
      totalTrades: trades.total,
      winningTrades: trades.winning,
      losingTrades: trades.losing,
      currentDrawdown: drawdown.currentDrawdown,
      currentCapital,
      unrealizedPnL,
      realizedPnL,
      commission: totalCommission,
      slippage: totalSlippage
    };
  }

  private updateIndicators(dataPoint: MarketDataPoint): void {
    // Simplified indicator calculations
    if (!this.indicators.sma_20) this.indicators.sma_20 = [];
    if (!this.indicators.rsi_14) this.indicators.rsi_14 = [];
    
    // Simple Moving Average (20 periods)
    const closes = this.data.slice(-20).map(d => d.close);
    if (closes.length === 20) {
      const sma = closes.reduce((sum, price) => sum + price, 0) / 20;
      this.indicators.sma_20.push(sma);
    }

    // RSI (14 periods) - simplified calculation
    if (this.data.length >= 15) {
      const changes = this.data.slice(-15).map((d, i, arr) => 
        i === 0 ? 0 : d.close - arr[i - 1].close
      ).slice(1);
      
      const gains = changes.filter(c => c > 0);
      const losses = changes.filter(c => c < 0).map(c => Math.abs(c));
      
      const avgGain = gains.length > 0 ? gains.reduce((sum, g) => sum + g, 0) / gains.length : 0;
      const avgLoss = losses.length > 0 ? losses.reduce((sum, l) => sum + l, 0) / losses.length : 0;
      
      const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      const rsi = 100 - (100 / (1 + rs));
      
      this.indicators.rsi_14.push(rsi);
    }
  }

  private generateSignals(dataPoint: MarketDataPoint): TradingSignal[] {
    const signals: TradingSignal[] = [];

    // Simple strategy: SMA crossover with RSI filter
    if (this.indicators.sma_20.length >= 2 && this.indicators.rsi_14.length >= 1) {
      const currentSMA = this.indicators.sma_20[this.indicators.sma_20.length - 1];
      const previousSMA = this.indicators.sma_20[this.indicators.sma_20.length - 2];
      const currentRSI = this.indicators.rsi_14[this.indicators.rsi_14.length - 1];

      // Buy signal: price crosses above SMA and RSI < 70
      if (dataPoint.close > currentSMA && 
          this.data[this.data.length - 2]?.close <= previousSMA &&
          currentRSI < 70) {
        signals.push({
          symbol: dataPoint.symbol,
          timestamp: dataPoint.timestamp,
          action: 'buy',
          confidence: 0.7,
          reason: 'SMA crossover buy signal with RSI confirmation',
          metadata: {
            sma: currentSMA,
            rsi: currentRSI,
            price: dataPoint.close
          }
        });
      }

      // Sell signal: price crosses below SMA and RSI > 30
      if (dataPoint.close < currentSMA && 
          this.data[this.data.length - 2]?.close >= previousSMA &&
          currentRSI > 30) {
        signals.push({
          symbol: dataPoint.symbol,
          timestamp: dataPoint.timestamp,
          action: 'sell',
          confidence: 0.7,
          reason: 'SMA crossover sell signal with RSI confirmation',
          metadata: {
            sma: currentSMA,
            rsi: currentRSI,
            price: dataPoint.close
          }
        });
      }
    }

    return signals;
  }

  private validateSignal(signal: TradingSignal): boolean {
    // Risk management validation
    
    // Check maximum positions
    const openPositions = this.positions.filter(p => p.status === 'open');
    if (openPositions.length >= this.parameters.maxPositions) {
      return false;
    }

    // Check confidence threshold
    if (signal.confidence < 0.5) {
      return false;
    }

    // Check available capital
    const metrics = this.getPerformanceMetrics();
    const positionValue = (signal.quantity || this.calculatePositionSize(signal)) * (signal.price || 0);
    
    if (positionValue > metrics.currentCapital * 0.1) { // Max 10% per position
      return false;
    }

    return true;
  }

  private calculatePositionSize(signal: TradingSignal): number {
    const metrics = this.getPerformanceMetrics();
    const riskAmount = metrics.currentCapital * this.parameters.riskPerTrade;
    const price = signal.price || this.data[this.data.length - 1]?.close || 0;
    
    if (price === 0) return 0;
    
    // Simple position sizing: risk amount / price
    return Math.floor(riskAmount / price);
  }

  private async simulateOrderExecution(order: Order, signal: TradingSignal): Promise<void> {
    // Simulate market slippage
    const currentPrice = this.data[this.data.length - 1]?.close || 0;
    const slippagePercent = this.parameters.slippage / 100;
    const slippageAmount = currentPrice * slippagePercent * (order.side === 'buy' ? 1 : -1);
    
    order.avgFillPrice = currentPrice + slippageAmount;
    order.filledQuantity = order.quantity;
    order.status = 'filled';
    order.fillTime = signal.timestamp;
    order.commission = order.quantity * order.avgFillPrice * (this.parameters.commission / 100);
    order.slippage = Math.abs(slippageAmount * order.quantity);

    // Create or update position
    if (order.side === 'buy') {
      // Open long position or close short position
      const existingShort = this.positions.find(p => 
        p.symbol === order.symbol && p.side === 'short' && p.status === 'open'
      );

      if (existingShort) {
        // Close short position
        existingShort.status = 'closed';
        existingShort.currentPrice = order.avgFillPrice;
        existingShort.unrealizedPnL = (existingShort.entryPrice - order.avgFillPrice) * existingShort.quantity;
      } else {
        // Open long position
        const position: Position = {
          id: `pos_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          symbol: order.symbol,
          side: 'long',
          quantity: order.filledQuantity,
          entryPrice: order.avgFillPrice,
          currentPrice: order.avgFillPrice,
          entryTime: signal.timestamp,
          unrealizedPnL: 0,
          unrealizedPnLPercent: 0,
          status: 'open'
        };
        this.positions.push(position);
      }
    } else {
      // Open short position or close long position
      const existingLong = this.positions.find(p => 
        p.symbol === order.symbol && p.side === 'long' && p.status === 'open'
      );

      if (existingLong) {
        // Close long position
        existingLong.status = 'closed';
        existingLong.currentPrice = order.avgFillPrice;
        existingLong.unrealizedPnL = (order.avgFillPrice - existingLong.entryPrice) * existingLong.quantity;
      } else {
        // Open short position
        const position: Position = {
          id: `pos_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          symbol: order.symbol,
          side: 'short',
          quantity: order.filledQuantity,
          entryPrice: order.avgFillPrice,
          currentPrice: order.avgFillPrice,
          entryTime: signal.timestamp,
          unrealizedPnL: 0,
          unrealizedPnLPercent: 0,
          status: 'open'
        };
        this.positions.push(position);
      }
    }
  }

  private updatePositions(dataPoint: MarketDataPoint): void {
    const openPositions = this.positions.filter(p => p.status === 'open' && p.symbol === dataPoint.symbol);
    
    for (const position of openPositions) {
      position.currentPrice = dataPoint.close;
      
      if (position.side === 'long') {
        position.unrealizedPnL = (dataPoint.close - position.entryPrice) * position.quantity;
      } else {
        position.unrealizedPnL = (position.entryPrice - dataPoint.close) * position.quantity;
      }
      
      position.unrealizedPnLPercent = (position.unrealizedPnL / (position.entryPrice * position.quantity)) * 100;

      // Check stop loss and take profit
      this.checkStopLossAndTakeProfit(position, dataPoint);
    }
  }

  private checkStopLossAndTakeProfit(position: Position, dataPoint: MarketDataPoint): void {
    const shouldClose = 
      (position.stopLoss && 
       ((position.side === 'long' && dataPoint.close <= position.stopLoss) ||
        (position.side === 'short' && dataPoint.close >= position.stopLoss))) ||
      (position.takeProfit && 
       ((position.side === 'long' && dataPoint.close >= position.takeProfit) ||
        (position.side === 'short' && dataPoint.close <= position.takeProfit)));

    if (shouldClose) {
      const reason = position.stopLoss && 
        ((position.side === 'long' && dataPoint.close <= position.stopLoss) ||
         (position.side === 'short' && dataPoint.close >= position.stopLoss)) 
        ? 'Stop loss triggered' : 'Take profit triggered';

      this.closePosition(position.id, reason);
    }
  }

  private calculateTradeStatistics() {
    const closedPositions = this.positions.filter(p => p.status === 'closed');
    const winningTrades = closedPositions.filter(p => p.unrealizedPnL > 0);
    const losingTrades = closedPositions.filter(p => p.unrealizedPnL <= 0);

    const totalWins = winningTrades.reduce((sum, p) => sum + p.unrealizedPnL, 0);
    const totalLosses = Math.abs(losingTrades.reduce((sum, p) => sum + p.unrealizedPnL, 0));

    return {
      total: closedPositions.length,
      winning: winningTrades.length,
      losing: losingTrades.length,
      winRate: closedPositions.length > 0 ? (winningTrades.length / closedPositions.length) * 100 : 0,
      avgWin: winningTrades.length > 0 ? totalWins / winningTrades.length : 0,
      avgLoss: losingTrades.length > 0 ? totalLosses / losingTrades.length : 0,
      profitFactor: totalLosses > 0 ? totalWins / totalLosses : 0
    };
  }

  private calculateDrawdown() {
    // Simplified drawdown calculation
    let peak = this.parameters.initialCapital;
    let maxDrawdown = 0;
    let maxDrawdownPercent = 0;
    let currentDrawdown = 0;

    const metrics = this.getPerformanceMetrics();
    const currentCapital = metrics.currentCapital;

    if (currentCapital > peak) {
      peak = currentCapital;
      currentDrawdown = 0;
    } else {
      currentDrawdown = peak - currentCapital;
      const currentDrawdownPercent = (currentDrawdown / peak) * 100;
      
      if (currentDrawdown > maxDrawdown) {
        maxDrawdown = currentDrawdown;
        maxDrawdownPercent = currentDrawdownPercent;
      }
    }

    return {
      maxDrawdown,
      maxDrawdownPercent,
      currentDrawdown
    };
  }

  private calculateAnnualizedReturn(totalReturnPercent: number): number {
    // Simplified annualized return calculation
    const daysElapsed = Math.max(1, 
      (Date.now() - this.parameters.startDate.getTime()) / (1000 * 60 * 60 * 24)
    );
    const yearsElapsed = daysElapsed / 365;
    
    return Math.pow(1 + totalReturnPercent / 100, 1 / yearsElapsed) - 1;
  }

  private calculateSharpeRatio(): number {
    // Simplified Sharpe ratio calculation
    // Would need actual returns series for proper calculation
    const metrics = this.getPerformanceMetrics();
    const volatility = 0.15; // Assume 15% volatility for simplification
    const riskFreeRate = 0.02; // Assume 2% risk-free rate
    
    return (metrics.annualizedReturn - riskFreeRate) / volatility;
  }

  private calculateSortinoRatio(): number {
    // Simplified Sortino ratio calculation
    // Would need actual downside deviation for proper calculation
    const metrics = this.getPerformanceMetrics();
    const downsideDeviation = 0.10; // Assume 10% downside deviation
    const riskFreeRate = 0.02;
    
    return (metrics.annualizedReturn - riskFreeRate) / downsideDeviation;
  }

  private log(level: ExecutionLog['level'], message: string, data?: any): void {
    this.logs.push({
      timestamp: new Date(),
      level,
      message,
      data
    });

    // Keep only last 1000 logs
    if (this.logs.length > 1000) {
      this.logs.splice(0, this.logs.length - 1000);
    }
  }

  // Getters
  getLogs(): ExecutionLog[] {
    return [...this.logs];
  }

  getPositions(): Position[] {
    return [...this.positions];
  }

  getOrders(): Order[] {
    return [...this.orders];
  }

  getData(): MarketDataPoint[] {
    return [...this.data];
  }

  getIndicators(): Record<string, number[]> {
    return { ...this.indicators };
  }
}

// Main strategy executor
export class StrategyExecutor extends EventEmitter {
  private executions = new Map<string, StrategyExecution>();
  private runtimes = new Map<string, StrategyRuntime>();
  private marketDataManager: MarketDataManager;

  constructor(marketDataManager: MarketDataManager) {
    super();
    this.marketDataManager = marketDataManager;
    
    // Listen for market data updates
    this.marketDataManager.on('marketData', (data: MarketDataPoint) => {
      this.handleMarketData(data);
    });
  }

  /**
   * Start strategy execution
   */
  async startExecution(
    strategyId: string,
    generatedCode: GeneratedCode,
    parameters: StrategyParameters
  ): Promise<string> {
    const executionId = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const execution: StrategyExecution = {
      id: executionId,
      strategyId,
      status: 'pending',
      mode: parameters.startDate < new Date() ? 'backtest' : 'live',
      parameters,
      startTime: new Date(),
      progress: 0,
      performance: this.getInitialPerformanceMetrics(parameters.initialCapital),
      positions: [],
      orders: [],
      logs: [],
      errors: []
    };

    try {
      // Create runtime
      const runtime = new StrategyRuntime(generatedCode, parameters);
      await runtime.initialize();

      this.executions.set(executionId, execution);
      this.runtimes.set(executionId, runtime);

      // Subscribe to market data
      if (execution.mode === 'live' || execution.mode === 'paper') {
        await this.marketDataManager.subscribe(parameters.symbol, parameters.timeframe);
      }

      execution.status = 'running';
      this.emit('executionStarted', execution);

      // For backtesting, start processing historical data
      if (execution.mode === 'backtest') {
        this.startBacktest(executionId);
      }

      return executionId;
    } catch (error) {
      execution.status = 'error';
      execution.errors.push({
        timestamp: new Date(),
        type: 'compilation',
        message: `Failed to start execution: ${error}`,
        fatal: true
      });
      
      this.emit('executionError', execution, error);
      throw error;
    }
  }

  /**
   * Stop strategy execution
   */
  async stopExecution(executionId: string): Promise<void> {
    const execution = this.executions.get(executionId);
    if (!execution) {
      throw new Error(`Execution ${executionId} not found`);
    }

    execution.status = 'stopped';
    execution.endTime = new Date();
    
    this.runtimes.delete(executionId);
    this.emit('executionStopped', execution);
  }

  /**
   * Pause strategy execution
   */
  async pauseExecution(executionId: string): Promise<void> {
    const execution = this.executions.get(executionId);
    if (!execution) {
      throw new Error(`Execution ${executionId} not found`);
    }

    execution.status = 'paused';
    this.emit('executionPaused', execution);
  }

  /**
   * Resume strategy execution
   */
  async resumeExecution(executionId: string): Promise<void> {
    const execution = this.executions.get(executionId);
    if (!execution) {
      throw new Error(`Execution ${executionId} not found`);
    }

    execution.status = 'running';
    this.emit('executionResumed', execution);
  }

  /**
   * Get execution status
   */
  getExecution(executionId: string): StrategyExecution | undefined {
    return this.executions.get(executionId);
  }

  /**
   * Get all executions
   */
  getAllExecutions(): StrategyExecution[] {
    return Array.from(this.executions.values());
  }

  private async handleMarketData(data: MarketDataPoint): Promise<void> {
    // Process market data for all running executions
    for (const [executionId, execution] of this.executions.entries()) {
      if (execution.status !== 'running') continue;
      
      const runtime = this.runtimes.get(executionId);
      if (!runtime) continue;

      // Check if this data is for the execution's symbol
      if (data.symbol !== execution.parameters.symbol) continue;

      try {
        // Process the data through the strategy
        const signals = await runtime.onData(data);
        
        // Execute any generated signals
        for (const signal of signals) {
          await runtime.executeSignal(signal);
        }

        // Update execution metrics
        execution.performance = runtime.getPerformanceMetrics();
        execution.positions = runtime.getPositions();
        execution.orders = runtime.getOrders();
        execution.currentTime = data.timestamp;

        this.emit('executionUpdated', execution);
      } catch (error) {
        execution.errors.push({
          timestamp: new Date(),
          type: 'runtime',
          message: `Error processing market data: ${error}`,
          fatal: false
        });
        
        this.emit('executionError', execution, error);
      }
    }
  }

  private async startBacktest(executionId: string): Promise<void> {
    const execution = this.executions.get(executionId);
    const runtime = this.runtimes.get(executionId);
    
    if (!execution || !runtime) return;

    try {
      // Get historical data for backtesting
      // In a real implementation, this would fetch actual historical data
      const historicalData = await this.generateMockHistoricalData(
        execution.parameters.symbol,
        execution.parameters.startDate,
        execution.parameters.endDate,
        execution.parameters.timeframe
      );

      // Process historical data
      for (let i = 0; i < historicalData.length; i++) {
        if (execution.status !== 'running') break;

        const dataPoint = historicalData[i];
        
        // Process the data point
        const signals = await runtime.onData(dataPoint);
        
        // Execute signals
        for (const signal of signals) {
          await runtime.executeSignal(signal);
        }

        // Update progress
        execution.progress = ((i + 1) / historicalData.length) * 100;
        execution.performance = runtime.getPerformanceMetrics();
        execution.positions = runtime.getPositions();
        execution.orders = runtime.getOrders();
        execution.currentTime = dataPoint.timestamp;

        // Emit progress updates periodically
        if (i % Math.max(1, Math.floor(historicalData.length / 100)) === 0) {
          this.emit('executionUpdated', execution);
        }
      }

      // Complete the backtest
      execution.status = 'completed';
      execution.endTime = new Date();
      execution.progress = 100;
      
      this.emit('executionCompleted', execution);
    } catch (error) {
      execution.status = 'error';
      execution.errors.push({
        timestamp: new Date(),
        type: 'runtime',
        message: `Backtest failed: ${error}`,
        fatal: true
      });
      
      this.emit('executionError', execution, error);
    }
  }

  private async generateMockHistoricalData(
    symbol: string,
    startDate: Date,
    endDate: Date,
    timeframe: string
  ): Promise<MarketDataPoint[]> {
    // Generate mock historical data for backtesting
    const data: MarketDataPoint[] = [];
    const intervalMs = this.getTimeframeMs(timeframe);
    
    let currentTime = new Date(startDate);
    let currentPrice = 100; // Starting price
    
    while (currentTime <= endDate) {
      // Generate realistic price movement
      const change = (Math.random() - 0.5) * 2; // -1 to 1
      currentPrice += change;
      
      const high = currentPrice + Math.random() * 2;
      const low = currentPrice - Math.random() * 2;
      const open = data.length > 0 ? data[data.length - 1].close : currentPrice;
      const volume = Math.floor(Math.random() * 1000000) + 10000;

      data.push({
        symbol,
        timestamp: new Date(currentTime),
        open,
        high: Math.max(open, currentPrice, high),
        low: Math.min(open, currentPrice, low),
        close: currentPrice,
        volume,
        source: 'backtest',
        quality: 'good'
      });

      currentTime = new Date(currentTime.getTime() + intervalMs);
    }

    return data;
  }

  private getTimeframeMs(timeframe: string): number {
    const intervals: Record<string, number> = {
      '1s': 1000,
      '5s': 5000,
      '10s': 10000,
      '30s': 30000,
      '1m': 60000,
      '5m': 300000,
      '15m': 900000,
      '30m': 1800000,
      '1h': 3600000,
      '4h': 14400000,
      '1d': 86400000
    };
    
    return intervals[timeframe] || 60000;
  }

  private getInitialPerformanceMetrics(initialCapital: number): PerformanceMetrics {
    return {
      totalReturn: 0,
      totalReturnPercent: 0,
      annualizedReturn: 0,
      sharpeRatio: 0,
      sortinoRatio: 0,
      maxDrawdown: 0,
      maxDrawdownPercent: 0,
      calmarRatio: 0,
      winRate: 0,
      profitFactor: 0,
      avgWin: 0,
      avgLoss: 0,
      totalTrades: 0,
      winningTrades: 0,
      losingTrades: 0,
      currentDrawdown: 0,
      currentCapital: initialCapital,
      unrealizedPnL: 0,
      realizedPnL: 0,
      commission: 0,
      slippage: 0
    };
  }
}