import { Node, Edge } from 'reactflow';
import { RealTimeExecutionEngine, MarketData, SignalResult } from './execution-engine';

export interface BacktestConfig {
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission_rate: number;
  slippage_rate: number;
  max_positions: number;
  risk_per_trade: number;
  benchmark_symbol?: string;
}

export interface BacktestResult {
  summary: {
    total_return: number;
    annualized_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    profit_factor: number;
    total_trades: number;
    avg_trade_duration: number;
  };
  trades: Trade[];
  equity_curve: EquityPoint[];
  metrics: {
    daily_returns: number[];
    monthly_returns: number[];
    drawdown_periods: DrawdownPeriod[];
    risk_metrics: RiskMetrics;
  };
  comparison: {
    strategy_vs_benchmark: ComparisonMetrics;
    monte_carlo_analysis?: MonteCarloResult;
  };
}

export interface Trade {
  trade_id: string;
  symbol: string;
  entry_date: Date;
  exit_date: Date;
  entry_price: number;
  exit_price: number;
  quantity: number;
  side: 'long' | 'short';
  pnl: number;
  pnl_percent: number;
  commission: number;
  duration_hours: number;
  exit_reason: 'signal' | 'stop_loss' | 'take_profit' | 'timeout';
  entry_signal_id: string;
  exit_signal_id?: string;
}

export interface EquityPoint {
  date: Date;
  equity: number;
  drawdown: number;
  benchmark_equity?: number;
}

export interface DrawdownPeriod {
  start_date: Date;
  end_date: Date;
  peak_equity: number;
  trough_equity: number;
  drawdown_percent: number;
  recovery_days: number;
}

export interface RiskMetrics {
  volatility: number;
  downside_deviation: number;
  value_at_risk_95: number;
  expected_shortfall: number;
  calmar_ratio: number;
  sortino_ratio: number;
  information_ratio: number;
}

export interface ComparisonMetrics {
  excess_return: number;
  tracking_error: number;
  beta: number;
  alpha: number;
  correlation: number;
}

export interface MonteCarloResult {
  simulations: number;
  confidence_intervals: {
    percentile_5: number;
    percentile_25: number;
    percentile_50: number;
    percentile_75: number;
    percentile_95: number;
  };
  probability_of_loss: number;
  expected_return: number;
}

export class BacktestingEngine {
  private config: BacktestConfig;
  private nodes: Node[];
  private edges: Edge[];
  private executionEngine: RealTimeExecutionEngine;
  private historicalData: MarketData[] = [];
  private trades: Trade[] = [];
  private equityCurve: EquityPoint[] = [];
  private currentEquity: number;
  private peakEquity: number;
  private openPositions: Map<string, Trade> = new Map();

  constructor(config: BacktestConfig, nodes: Node[], edges: Edge[]) {
    this.config = config;
    this.nodes = nodes;
    this.edges = edges;
    this.currentEquity = config.initial_capital;
    this.peakEquity = config.initial_capital;
    
    // Create execution engine for signal generation
    this.executionEngine = new RealTimeExecutionEngine(
      {
        strategy_id: 'backtest',
        symbol: this.getSymbolFromNodes(),
        timeframe: this.getTimeframeFromNodes(),
        live_trading: false,
        paper_trading: false,
        risk_management: {
          max_position_size: config.max_positions,
          max_drawdown: 0.2, // 20% max drawdown
          stop_loss_enabled: true,
          take_profit_enabled: true
        },
        execution_mode: 'backtest'
      },
      nodes,
      edges
    );
  }

  private getSymbolFromNodes(): string {
    const dataSourceNode = this.nodes.find(n => n.type === 'dataSource');
    return dataSourceNode?.data?.parameters?.symbol || 'AAPL';
  }

  private getTimeframeFromNodes(): string {
    const dataSourceNode = this.nodes.find(n => n.type === 'dataSource');
    return dataSourceNode?.data?.parameters?.timeframe || '1h';
  }

  public async runBacktest(historicalData: MarketData[]): Promise<BacktestResult> {
    console.log(`Starting backtest from ${this.config.start_date} to ${this.config.end_date}`);
    
    this.historicalData = this.filterDataByDateRange(historicalData);
    this.initializeBacktest();
    
    // Process each data point
    for (let i = 0; i < this.historicalData.length; i++) {
      await this.processDataPoint(i);
    }
    
    // Close any remaining open positions
    this.closeAllPositions(this.historicalData[this.historicalData.length - 1]);
    
    // Calculate results
    const result = await this.calculateBacktestResults();
    
    console.log('Backtest completed');
    return result;
  }

  private filterDataByDateRange(data: MarketData[]): MarketData[] {
    const startDate = new Date(this.config.start_date);
    const endDate = new Date(this.config.end_date);
    
    return data.filter(point => 
      point.timestamp >= startDate && point.timestamp <= endDate
    );
  }

  private initializeBacktest(): void {
    this.trades = [];
    this.equityCurve = [];
    this.currentEquity = this.config.initial_capital;
    this.peakEquity = this.config.initial_capital;
    this.openPositions.clear();
    
    // Add initial equity point
    this.equityCurve.push({
      date: this.historicalData[0].timestamp,
      equity: this.currentEquity,
      drawdown: 0
    });
  }

  private async processDataPoint(index: number): Promise<void> {
    const currentData = this.historicalData[index];
    const dataWindow = this.historicalData.slice(0, index + 1);
    
    // Check for stop losses and take profits on open positions
    this.checkExitConditions(currentData);
    
    // Generate signals using execution engine
    try {
      const executionResult = await this.executionEngine.executeStrategy(dataWindow);
      
      // Process signals
      for (const signal of executionResult.signals) {
        await this.processSignal(signal, currentData);
      }
      
    } catch (error) {
      console.error('Error processing data point:', error);
    }
    
    // Update equity curve
    this.updateEquityCurve(currentData);
  }

  private checkExitConditions(currentData: MarketData): void {
    for (const [positionId, position] of this.openPositions) {
      let shouldExit = false;
      let exitReason: Trade['exit_reason'] = 'signal';
      
      // Check stop loss
      if (position.side === 'long') {
        const stopLossPrice = position.entry_price * (1 - this.config.risk_per_trade);
        if (currentData.low <= stopLossPrice) {
          shouldExit = true;
          exitReason = 'stop_loss';
        }
      } else {
        const stopLossPrice = position.entry_price * (1 + this.config.risk_per_trade);
        if (currentData.high >= stopLossPrice) {
          shouldExit = true;
          exitReason = 'stop_loss';
        }
      }
      
      // Check take profit (simplified - using 2:1 reward/risk)
      if (!shouldExit) {
        if (position.side === 'long') {
          const takeProfitPrice = position.entry_price * (1 + this.config.risk_per_trade * 2);
          if (currentData.high >= takeProfitPrice) {
            shouldExit = true;
            exitReason = 'take_profit';
          }
        } else {
          const takeProfitPrice = position.entry_price * (1 - this.config.risk_per_trade * 2);
          if (currentData.low <= takeProfitPrice) {
            shouldExit = true;
            exitReason = 'take_profit';
          }
        }
      }
      
      if (shouldExit) {
        this.closePosition(positionId, currentData, exitReason);
      }
    }
  }

  private async processSignal(signal: SignalResult, currentData: MarketData): Promise<void> {
    // Skip hold signals
    if (signal.action === 'hold') return;
    
    // Check if we already have maximum positions
    if (this.openPositions.size >= this.config.max_positions) {
      return;
    }
    
    // Calculate position size based on risk management
    const positionSize = this.calculatePositionSize(signal, currentData);
    if (positionSize === 0) return;
    
    // Create new position
    const trade: Trade = {
      trade_id: `trade_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      symbol: signal.symbol,
      entry_date: currentData.timestamp,
      exit_date: currentData.timestamp, // Will be updated on exit
      entry_price: this.calculateEntryPrice(currentData, signal.action),
      exit_price: 0, // Will be updated on exit
      quantity: positionSize,
      side: signal.action === 'buy' ? 'long' : 'short',
      pnl: 0, // Will be calculated on exit
      pnl_percent: 0, // Will be calculated on exit
      commission: this.calculateCommission(positionSize, currentData.close),
      duration_hours: 0, // Will be calculated on exit
      exit_reason: 'signal', // Will be updated on exit
      entry_signal_id: signal.signal_id,
      exit_signal_id: undefined
    };
    
    // Add to open positions
    this.openPositions.set(trade.trade_id, trade);
    
    // Update equity for commission
    this.currentEquity -= trade.commission;
  }

  private calculatePositionSize(signal: SignalResult, currentData: MarketData): number {
    const riskAmount = this.currentEquity * this.config.risk_per_trade;
    const entryPrice = this.calculateEntryPrice(currentData, signal.action);
    const stopLossPrice = signal.action === 'buy' ? 
      entryPrice * (1 - this.config.risk_per_trade) : 
      entryPrice * (1 + this.config.risk_per_trade);
    
    const riskPerShare = Math.abs(entryPrice - stopLossPrice);
    if (riskPerShare === 0) return 0;
    
    const positionSize = Math.floor(riskAmount / riskPerShare);
    const maxPositionValue = this.currentEquity * 0.25; // Max 25% per position
    const maxShares = Math.floor(maxPositionValue / entryPrice);
    
    return Math.min(positionSize, maxShares);
  }

  private calculateEntryPrice(currentData: MarketData, action: string): number {
    // Simulate slippage
    const slippage = this.config.slippage_rate;
    
    if (action === 'buy') {
      return currentData.close * (1 + slippage);
    } else {
      return currentData.close * (1 - slippage);
    }
  }

  private calculateCommission(quantity: number, price: number): number {
    return quantity * price * this.config.commission_rate;
  }

  private closePosition(positionId: string, currentData: MarketData, exitReason: Trade['exit_reason']): void {
    const position = this.openPositions.get(positionId);
    if (!position) return;
    
    // Calculate exit price with slippage
    const exitPrice = position.side === 'long' ? 
      currentData.close * (1 - this.config.slippage_rate) :
      currentData.close * (1 + this.config.slippage_rate);
    
    // Calculate P&L
    const pnl = position.side === 'long' ? 
      (exitPrice - position.entry_price) * position.quantity :
      (position.entry_price - exitPrice) * position.quantity;
    
    const exitCommission = this.calculateCommission(position.quantity, exitPrice);
    const netPnl = pnl - exitCommission;
    
    // Update trade
    const completedTrade: Trade = {
      ...position,
      exit_date: currentData.timestamp,
      exit_price: exitPrice,
      pnl: netPnl,
      pnl_percent: (netPnl / (position.entry_price * position.quantity)) * 100,
      commission: position.commission + exitCommission,
      duration_hours: (currentData.timestamp.getTime() - position.entry_date.getTime()) / (1000 * 60 * 60),
      exit_reason: exitReason
    };
    
    // Update equity
    this.currentEquity += netPnl;
    
    // Add to completed trades
    this.trades.push(completedTrade);
    
    // Remove from open positions
    this.openPositions.delete(positionId);
  }

  private closeAllPositions(finalData: MarketData): void {
    for (const [positionId] of this.openPositions) {
      this.closePosition(positionId, finalData, 'timeout');
    }
  }

  private updateEquityCurve(currentData: MarketData): void {
    // Calculate unrealized P&L for open positions
    let unrealizedPnl = 0;
    for (const position of this.openPositions.values()) {
      const currentPrice = currentData.close;
      const unrealizedPositionPnl = position.side === 'long' ? 
        (currentPrice - position.entry_price) * position.quantity :
        (position.entry_price - currentPrice) * position.quantity;
      unrealizedPnl += unrealizedPositionPnl;
    }
    
    const totalEquity = this.currentEquity + unrealizedPnl;
    this.peakEquity = Math.max(this.peakEquity, totalEquity);
    
    const drawdown = this.peakEquity > 0 ? ((this.peakEquity - totalEquity) / this.peakEquity) * 100 : 0;
    
    this.equityCurve.push({
      date: currentData.timestamp,
      equity: totalEquity,
      drawdown: drawdown
    });
  }

  private async calculateBacktestResults(): Promise<BacktestResult> {
    const summary = this.calculateSummaryMetrics();
    const metrics = this.calculateDetailedMetrics();
    const comparison = await this.calculateComparisonMetrics();
    
    return {
      summary,
      trades: this.trades,
      equity_curve: this.equityCurve,
      metrics,
      comparison
    };
  }

  private calculateSummaryMetrics() {
    const finalEquity = this.equityCurve[this.equityCurve.length - 1].equity;
    const totalReturn = ((finalEquity - this.config.initial_capital) / this.config.initial_capital) * 100;
    
    const daysInBacktest = (new Date(this.config.end_date).getTime() - new Date(this.config.start_date).getTime()) / (1000 * 60 * 60 * 24);
    const annualizedReturn = (Math.pow(finalEquity / this.config.initial_capital, 365 / daysInBacktest) - 1) * 100;
    
    const winningTrades = this.trades.filter(t => t.pnl > 0);
    const winRate = this.trades.length > 0 ? (winningTrades.length / this.trades.length) * 100 : 0;
    
    const grossWins = winningTrades.reduce((sum, t) => sum + t.pnl, 0);
    const grossLosses = Math.abs(this.trades.filter(t => t.pnl < 0).reduce((sum, t) => sum + t.pnl, 0));
    const profitFactor = grossLosses > 0 ? grossWins / grossLosses : 0;
    
    const maxDrawdown = Math.max(...this.equityCurve.map(e => e.drawdown));
    
    const dailyReturns = this.calculateDailyReturns();
    const avgReturn = dailyReturns.reduce((sum, r) => sum + r, 0) / dailyReturns.length;
    const returnStd = Math.sqrt(dailyReturns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / dailyReturns.length);
    const sharpeRatio = returnStd > 0 ? (avgReturn / returnStd) * Math.sqrt(252) : 0;
    
    const avgTradeDuration = this.trades.length > 0 ? 
      this.trades.reduce((sum, t) => sum + t.duration_hours, 0) / this.trades.length : 0;
    
    return {
      total_return: Math.round(totalReturn * 100) / 100,
      annualized_return: Math.round(annualizedReturn * 100) / 100,
      sharpe_ratio: Math.round(sharpeRatio * 100) / 100,
      max_drawdown: Math.round(maxDrawdown * 100) / 100,
      win_rate: Math.round(winRate * 100) / 100,
      profit_factor: Math.round(profitFactor * 100) / 100,
      total_trades: this.trades.length,
      avg_trade_duration: Math.round(avgTradeDuration * 100) / 100
    };
  }

  private calculateDailyReturns(): number[] {
    const dailyReturns: number[] = [];
    
    for (let i = 1; i < this.equityCurve.length; i++) {
      const currentEquity = this.equityCurve[i].equity;
      const previousEquity = this.equityCurve[i - 1].equity;
      const dailyReturn = ((currentEquity - previousEquity) / previousEquity) * 100;
      dailyReturns.push(dailyReturn);
    }
    
    return dailyReturns;
  }

  private calculateDetailedMetrics() {
    const dailyReturns = this.calculateDailyReturns();
    const monthlyReturns = this.calculateMonthlyReturns();
    const drawdownPeriods = this.calculateDrawdownPeriods();
    const riskMetrics = this.calculateRiskMetrics(dailyReturns);
    
    return {
      daily_returns: dailyReturns,
      monthly_returns: monthlyReturns,
      drawdown_periods: drawdownPeriods,
      risk_metrics: riskMetrics
    };
  }

  private calculateMonthlyReturns(): number[] {
    // Simplified monthly returns calculation
    const monthlyReturns: number[] = [];
    const equityByMonth = new Map<string, number[]>();
    
    this.equityCurve.forEach(point => {
      const monthKey = `${point.date.getFullYear()}-${point.date.getMonth()}`;
      if (!equityByMonth.has(monthKey)) {
        equityByMonth.set(monthKey, []);
      }
      equityByMonth.get(monthKey)!.push(point.equity);
    });
    
    for (const [month, equities] of equityByMonth) {
      if (equities.length > 1) {
        const monthReturn = ((equities[equities.length - 1] - equities[0]) / equities[0]) * 100;
        monthlyReturns.push(monthReturn);
      }
    }
    
    return monthlyReturns;
  }

  private calculateDrawdownPeriods(): DrawdownPeriod[] {
    const periods: DrawdownPeriod[] = [];
    let currentPeriod: Partial<DrawdownPeriod> | null = null;
    
    for (let i = 0; i < this.equityCurve.length; i++) {
      const point = this.equityCurve[i];
      
      if (point.drawdown > 0) {
        if (!currentPeriod) {
          // Start new drawdown period
          currentPeriod = {
            start_date: point.date,
            peak_equity: this.equityCurve[Math.max(0, i - 1)]?.equity || point.equity,
            trough_equity: point.equity,
            drawdown_percent: point.drawdown
          };
        } else {
          // Update existing period
          if (point.equity < currentPeriod.trough_equity!) {
            currentPeriod.trough_equity = point.equity;
            currentPeriod.drawdown_percent = point.drawdown;
          }
        }
      } else if (currentPeriod) {
        // End drawdown period
        currentPeriod.end_date = point.date;
        currentPeriod.recovery_days = (point.date.getTime() - currentPeriod.start_date!.getTime()) / (1000 * 60 * 60 * 24);
        
        periods.push(currentPeriod as DrawdownPeriod);
        currentPeriod = null;
      }
    }
    
    return periods;
  }

  private calculateRiskMetrics(dailyReturns: number[]): RiskMetrics {
    const avgReturn = dailyReturns.reduce((sum, r) => sum + r, 0) / dailyReturns.length;
    const variance = dailyReturns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / dailyReturns.length;
    const volatility = Math.sqrt(variance) * Math.sqrt(252); // Annualized
    
    // Downside deviation (returns below 0)
    const negativeReturns = dailyReturns.filter(r => r < 0);
    const downsideVariance = negativeReturns.reduce((sum, r) => sum + Math.pow(r, 2), 0) / negativeReturns.length;
    const downsideDeviation = Math.sqrt(downsideVariance) * Math.sqrt(252);
    
    // VaR at 95% confidence level
    const sortedReturns = [...dailyReturns].sort((a, b) => a - b);
    const var95Index = Math.floor(sortedReturns.length * 0.05);
    const valueAtRisk95 = sortedReturns[var95Index] || 0;
    
    // Expected Shortfall (average of returns worse than VaR)
    const expectedShortfall = sortedReturns.slice(0, var95Index + 1).reduce((sum, r) => sum + r, 0) / (var95Index + 1);
    
    const maxDrawdown = Math.max(...this.equityCurve.map(e => e.drawdown));
    const calmarRatio = maxDrawdown > 0 ? (avgReturn * 252) / maxDrawdown : 0;
    const sortinoRatio = downsideDeviation > 0 ? (avgReturn * Math.sqrt(252)) / downsideDeviation : 0;
    
    return {
      volatility: Math.round(volatility * 100) / 100,
      downside_deviation: Math.round(downsideDeviation * 100) / 100,
      value_at_risk_95: Math.round(valueAtRisk95 * 100) / 100,
      expected_shortfall: Math.round(expectedShortfall * 100) / 100,
      calmar_ratio: Math.round(calmarRatio * 100) / 100,
      sortino_ratio: Math.round(sortinoRatio * 100) / 100,
      information_ratio: 0 // Would need benchmark data
    };
  }

  private async calculateComparisonMetrics(): Promise<{ strategy_vs_benchmark: ComparisonMetrics }> {
    // Simplified comparison metrics (would need actual benchmark data)
    return {
      strategy_vs_benchmark: {
        excess_return: 0,
        tracking_error: 0,
        beta: 1,
        alpha: 0,
        correlation: 0
      }
    };
  }
}

// Export function for creating backtesting engine
export const createBacktestingEngine = (
  config: BacktestConfig,
  nodes: Node[],
  edges: Edge[]
): BacktestingEngine => {
  return new BacktestingEngine(config, nodes, edges);
};