import { Node, Edge } from 'reactflow';
import { ExecutionResult, SignalResult, MarketData } from './execution-engine';
import { MultiTimeframeExecutionResult } from './multi-timeframe-engine';
import { BacktestResult } from './backtesting-engine';

export interface StrategyConfig {
  strategy_id: string;
  strategy_name: string;
  nodes: Node[];
  edges: Edge[];
  allocation_percentage: number; // 0-100
  risk_budget: number; // Maximum risk allocation for this strategy
  priority: 'high' | 'medium' | 'low';
  active: boolean;
  constraints: StrategyConstraints;
  performance_targets: PerformanceTargets;
}

export interface StrategyConstraints {
  max_position_size: number; // Maximum position size per trade
  max_daily_trades: number;
  max_drawdown: number; // Strategy-specific max drawdown
  correlation_limit: number; // Max correlation with other strategies
  sector_exposure_limit: Record<string, number>; // Sector exposure limits
  instrument_limits: Record<string, number>; // Per-instrument limits
}

export interface PerformanceTargets {
  target_sharpe_ratio: number;
  target_annual_return: number;
  max_acceptable_drawdown: number;
  min_win_rate: number;
  rebalancing_frequency: 'daily' | 'weekly' | 'monthly';
}

export interface PortfolioConfig {
  portfolio_id: string;
  total_capital: number;
  risk_management: PortfolioRiskConfig;
  rebalancing: RebalancingConfig;
  optimization: PortfolioOptimizationConfig;
  constraints: PortfolioConstraints;
}

export interface PortfolioRiskConfig {
  max_portfolio_drawdown: number;
  var_limit: number; // Value at Risk limit
  concentration_limits: {
    max_single_strategy: number; // Max allocation to single strategy
    max_sector_exposure: number;
    max_instrument_exposure: number;
  };
  correlation_monitoring: boolean;
  stress_testing: boolean;
}

export interface RebalancingConfig {
  frequency: 'real_time' | 'hourly' | 'daily' | 'weekly';
  drift_threshold: number; // Percentage drift before rebalancing
  transaction_cost_threshold: number; // Min expected profit after costs
  rebalancing_method: 'proportional' | 'equal_risk' | 'volatility_weighted' | 'mean_reversion';
}

export interface PortfolioOptimizationConfig {
  optimization_objective: 'sharpe_ratio' | 'total_return' | 'risk_adjusted_return' | 'diversification';
  lookback_period: number; // Days for performance calculation
  optimization_frequency: number; // Days between optimization runs
  min_strategy_allocation: number; // Minimum allocation per active strategy
  max_strategy_allocation: number; // Maximum allocation per strategy
}

export interface PortfolioConstraints {
  max_leverage: number;
  cash_reserve_percentage: number;
  max_strategies: number;
  min_strategies: number;
  geographic_limits: Record<string, number>;
  asset_class_limits: Record<string, number>;
}

export interface PortfolioState {
  current_allocations: Record<string, number>; // strategy_id -> allocation
  total_equity: number;
  available_cash: number;
  unrealized_pnl: number;
  realized_pnl: number;
  positions: PortfolioPosition[];
  risk_metrics: PortfolioRiskMetrics;
  performance_metrics: PortfolioPerformanceMetrics;
  last_rebalance: Date;
  next_rebalance: Date;
}

export interface PortfolioPosition {
  position_id: string;
  strategy_id: string;
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  position_value: number;
  allocation_percentage: number;
  risk_contribution: number;
  entry_date: Date;
}

export interface PortfolioRiskMetrics {
  portfolio_var: number; // Value at Risk
  portfolio_cvar: number; // Conditional VaR
  beta: number; // Portfolio beta
  correlation_matrix: Record<string, Record<string, number>>;
  concentration_risk: number;
  max_drawdown: number;
  current_drawdown: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
}

export interface PortfolioPerformanceMetrics {
  total_return: number;
  annualized_return: number;
  volatility: number;
  information_ratio: number;
  tracking_error: number;
  alpha: number;
  strategy_contributions: Record<string, StrategyContribution>;
  attribution_analysis: AttributionAnalysis;
}

export interface StrategyContribution {
  strategy_id: string;
  return_contribution: number;
  risk_contribution: number;
  allocation: number;
  individual_return: number;
  correlation_with_portfolio: number;
}

export interface AttributionAnalysis {
  asset_allocation_effect: number;
  security_selection_effect: number;
  interaction_effect: number;
  timing_effect: number;
  currency_effect: number;
}

export interface RebalancingAction {
  action_id: string;
  timestamp: Date;
  action_type: 'increase_allocation' | 'decrease_allocation' | 'add_strategy' | 'remove_strategy';
  strategy_id: string;
  current_allocation: number;
  target_allocation: number;
  rebalancing_amount: number;
  reason: string;
  expected_impact: {
    risk_change: number;
    return_change: number;
    transaction_cost: number;
  };
}

export interface PortfolioAlert {
  alert_id: string;
  timestamp: Date;
  severity: 'info' | 'warning' | 'critical';
  category: 'risk' | 'performance' | 'allocation' | 'constraint';
  message: string;
  affected_strategies: string[];
  recommended_actions: string[];
  auto_actionable: boolean;
}

export class PortfolioOrchestrator {
  private config: PortfolioConfig;
  private strategies: Map<string, StrategyConfig> = new Map();
  private portfolioState: PortfolioState;
  private executionHistory: Map<string, ExecutionResult[]> = new Map();
  private rebalancingHistory: RebalancingAction[] = [];
  private alerts: PortfolioAlert[] = [];
  private correlationMatrix: number[][] = [];

  constructor(config: PortfolioConfig) {
    this.config = config;
    this.portfolioState = this.initializePortfolioState();
    this.validateConfiguration();
  }

  private validateConfiguration(): void {
    if (this.config.total_capital <= 0) {
      throw new Error('Total capital must be positive');
    }

    if (this.config.constraints.max_strategies < this.config.constraints.min_strategies) {
      throw new Error('Max strategies must be >= min strategies');
    }

    const totalConstraints = Object.values(this.config.constraints.asset_class_limits)
      .reduce((sum, limit) => sum + limit, 0);
    
    if (totalConstraints > 100) {
      throw new Error('Asset class limits cannot exceed 100%');
    }
  }

  private initializePortfolioState(): PortfolioState {
    return {
      current_allocations: {},
      total_equity: this.config.total_capital,
      available_cash: this.config.total_capital,
      unrealized_pnl: 0,
      realized_pnl: 0,
      positions: [],
      risk_metrics: {
        portfolio_var: 0,
        portfolio_cvar: 0,
        beta: 1,
        correlation_matrix: {},
        concentration_risk: 0,
        max_drawdown: 0,
        current_drawdown: 0,
        sharpe_ratio: 0,
        sortino_ratio: 0,
        calmar_ratio: 0
      },
      performance_metrics: {
        total_return: 0,
        annualized_return: 0,
        volatility: 0,
        information_ratio: 0,
        tracking_error: 0,
        alpha: 0,
        strategy_contributions: {},
        attribution_analysis: {
          asset_allocation_effect: 0,
          security_selection_effect: 0,
          interaction_effect: 0,
          timing_effect: 0,
          currency_effect: 0
        }
      },
      last_rebalance: new Date(),
      next_rebalance: this.calculateNextRebalanceDate(new Date())
    };
  }

  public addStrategy(strategy: StrategyConfig): void {
    // Validate strategy constraints
    this.validateStrategy(strategy);
    
    // Check portfolio constraints
    if (this.strategies.size >= this.config.constraints.max_strategies) {
      throw new Error(`Cannot add strategy: Portfolio already has maximum ${this.config.constraints.max_strategies} strategies`);
    }

    // Add strategy
    this.strategies.set(strategy.strategy_id, strategy);
    this.executionHistory.set(strategy.strategy_id, []);

    // Initialize allocation
    this.portfolioState.current_allocations[strategy.strategy_id] = 0;

    console.log(`Strategy ${strategy.strategy_id} added to portfolio`);
    
    // Trigger rebalancing if auto-rebalancing is enabled
    if (this.config.rebalancing.frequency === 'real_time') {
      this.scheduleRebalancing();
    }
  }

  public removeStrategy(strategyId: string): void {
    const strategy = this.strategies.get(strategyId);
    if (!strategy) {
      throw new Error(`Strategy ${strategyId} not found`);
    }

    // Check minimum strategies constraint
    if (this.strategies.size <= this.config.constraints.min_strategies) {
      throw new Error(`Cannot remove strategy: Portfolio must have at least ${this.config.constraints.min_strategies} strategies`);
    }

    // Close all positions for this strategy
    this.closeStrategyPositions(strategyId);

    // Remove from maps
    this.strategies.delete(strategyId);
    this.executionHistory.delete(strategyId);
    delete this.portfolioState.current_allocations[strategyId];

    console.log(`Strategy ${strategyId} removed from portfolio`);
  }

  public async executePortfolio(marketData: Map<string, MarketData[]>): Promise<Map<string, ExecutionResult>> {
    const results = new Map<string, ExecutionResult>();
    
    try {
      // Execute all active strategies in parallel
      const executionPromises = Array.from(this.strategies.entries())
        .filter(([_, strategy]) => strategy.active)
        .map(async ([strategyId, strategy]) => {
          try {
            // Get market data for this strategy
            const strategyData = marketData.get(strategyId) || [];
            
            // Execute strategy (simplified - would use actual execution engine)
            const result = await this.executeStrategy(strategy, strategyData);
            
            // Store execution history
            const history = this.executionHistory.get(strategyId) || [];
            history.push(result);
            this.executionHistory.set(strategyId, history.slice(-100)); // Keep last 100 results
            
            return [strategyId, result] as const;
          } catch (error) {
            console.error(`Error executing strategy ${strategyId}:`, error);
            return [strategyId, this.createErrorResult(strategyId)] as const;
          }
        });

      const executionResults = await Promise.all(executionPromises);
      executionResults.forEach(([strategyId, result]) => {
        results.set(strategyId, result);
      });

      // Process portfolio-level logic
      await this.processPortfolioSignals(results);
      
      // Update portfolio state
      await this.updatePortfolioState(results);
      
      // Check for rebalancing
      await this.checkRebalancingNeeds();
      
      // Monitor risks and generate alerts
      await this.monitorRisksAndAlerts();

      return results;

    } catch (error) {
      console.error('Portfolio execution error:', error);
      throw error;
    }
  }

  private async executeStrategy(strategy: StrategyConfig, marketData: MarketData[]): Promise<ExecutionResult> {
    // Simplified strategy execution
    // In production, this would use the actual execution engines
    
    const signals: SignalResult[] = [];
    const numSignals = Math.floor(Math.random() * 3); // 0-2 signals
    
    for (let i = 0; i < numSignals; i++) {
      const signal: SignalResult = {
        signal_id: `signal_${strategy.strategy_id}_${Date.now()}_${i}`,
        timestamp: new Date(),
        action: Math.random() > 0.5 ? 'buy' : 'sell',
        symbol: 'AAPL', // Simplified
        quantity: Math.floor(Math.random() * 100) + 10,
        price: 150 + Math.random() * 20,
        confidence: Math.random() * 0.4 + 0.6,
        metadata: {
          indicators: {},
          conditions: {},
          logic_results: {}
        }
      };
      
      signals.push(signal);
    }

    return {
      execution_id: `exec_${strategy.strategy_id}_${Date.now()}`,
      timestamp: new Date(),
      signals,
      performance_metrics: {
        execution_time_ms: Math.random() * 100 + 10,
        memory_usage_mb: Math.random() * 50 + 10,
        indicator_calculations: strategy.nodes.filter(n => n.type === 'technicalIndicator').length,
        condition_evaluations: strategy.nodes.filter(n => n.type === 'condition').length,
        logic_operations: strategy.nodes.filter(n => n.type === 'logic').length
      },
      errors: [],
      warnings: []
    };
  }

  private createErrorResult(strategyId: string): ExecutionResult {
    return {
      execution_id: `error_${strategyId}_${Date.now()}`,
      timestamp: new Date(),
      signals: [],
      performance_metrics: {
        execution_time_ms: 0,
        memory_usage_mb: 0,
        indicator_calculations: 0,
        condition_evaluations: 0,
        logic_operations: 0
      },
      errors: ['Strategy execution failed'],
      warnings: []
    };
  }

  private async processPortfolioSignals(results: Map<string, ExecutionResult>): Promise<void> {
    const allSignals: Array<{ strategyId: string; signal: SignalResult }> = [];
    
    // Collect all signals
    results.forEach((result, strategyId) => {
      result.signals.forEach(signal => {
        allSignals.push({ strategyId, signal });
      });
    });

    // Filter signals based on portfolio constraints
    const filteredSignals = this.filterSignalsByConstraints(allSignals);
    
    // Allocate capital to signals based on strategy allocations
    const capitalAllocatedSignals = this.allocateCapitalToSignals(filteredSignals);
    
    // Execute filtered and allocated signals
    await this.executePortfolioSignals(capitalAllocatedSignals);
  }

  private filterSignalsByConstraints(
    signals: Array<{ strategyId: string; signal: SignalResult }>
  ): Array<{ strategyId: string; signal: SignalResult }> {
    return signals.filter(({ strategyId, signal }) => {
      const strategy = this.strategies.get(strategyId);
      if (!strategy) return false;

      // Check daily trade limit
      const todayTrades = this.getTodayTradeCount(strategyId);
      if (todayTrades >= strategy.constraints.max_daily_trades) {
        return false;
      }

      // Check position size limit
      const positionValue = signal.quantity * signal.price;
      if (positionValue > strategy.constraints.max_position_size) {
        return false;
      }

      // Check instrument limits
      const currentExposure = this.getCurrentInstrumentExposure(signal.symbol);
      const newExposure = currentExposure + positionValue;
      const instrumentLimit = strategy.constraints.instrument_limits[signal.symbol] || Infinity;
      
      if (newExposure > instrumentLimit) {
        return false;
      }

      return true;
    });
  }

  private allocateCapitalToSignals(
    signals: Array<{ strategyId: string; signal: SignalResult }>
  ): Array<{ strategyId: string; signal: SignalResult; allocatedCapital: number }> {
    return signals.map(({ strategyId, signal }) => {
      const strategy = this.strategies.get(strategyId)!;
      const strategyAllocation = this.portfolioState.current_allocations[strategyId] || 0;
      const availableCapital = this.portfolioState.available_cash * (strategyAllocation / 100);
      
      // Calculate signal capital based on confidence and available capital
      const signalCapital = availableCapital * signal.confidence * 0.1; // Max 10% per signal
      
      return {
        strategyId,
        signal,
        allocatedCapital: Math.min(signalCapital, signal.quantity * signal.price)
      };
    });
  }

  private async executePortfolioSignals(
    signals: Array<{ strategyId: string; signal: SignalResult; allocatedCapital: number }>
  ): Promise<void> {
    for (const { strategyId, signal, allocatedCapital } of signals) {
      try {
        // Create portfolio position
        const position: PortfolioPosition = {
          position_id: `pos_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          strategy_id: strategyId,
          symbol: signal.symbol,
          quantity: Math.floor(allocatedCapital / signal.price),
          entry_price: signal.price,
          current_price: signal.price,
          unrealized_pnl: 0,
          position_value: allocatedCapital,
          allocation_percentage: (allocatedCapital / this.portfolioState.total_equity) * 100,
          risk_contribution: this.calculateRiskContribution(allocatedCapital, signal.symbol),
          entry_date: signal.timestamp
        };

        this.portfolioState.positions.push(position);
        this.portfolioState.available_cash -= allocatedCapital;

        console.log(`Executed signal: ${signal.action} ${position.quantity} ${signal.symbol} @ ${signal.price}`);
      } catch (error) {
        console.error('Error executing portfolio signal:', error);
      }
    }
  }

  private async updatePortfolioState(results: Map<string, ExecutionResult>): Promise<void> {
    // Update position values (simulate market movement)
    this.updatePositionValues();
    
    // Calculate portfolio metrics
    await this.calculatePortfolioMetrics();
    
    // Update strategy contributions
    await this.calculateStrategyContributions();
    
    // Update risk metrics
    await this.calculateRiskMetrics();
  }

  private updatePositionValues(): void {
    let totalUnrealizedPnL = 0;
    
    this.portfolioState.positions.forEach(position => {
      // Simulate price movement
      const priceChange = (Math.random() - 0.5) * 0.02; // ±1%
      position.current_price = position.entry_price * (1 + priceChange);
      position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity;
      position.position_value = position.current_price * position.quantity;
      
      totalUnrealizedPnL += position.unrealized_pnl;
    });
    
    this.portfolioState.unrealized_pnl = totalUnrealizedPnL;
    this.portfolioState.total_equity = this.config.total_capital + 
                                       this.portfolioState.realized_pnl + 
                                       this.portfolioState.unrealized_pnl;
  }

  private async calculatePortfolioMetrics(): Promise<void> {
    const totalValue = this.portfolioState.total_equity;
    const initialValue = this.config.total_capital;
    
    // Basic performance metrics
    const totalReturn = ((totalValue - initialValue) / initialValue) * 100;
    const annualizedReturn = totalReturn * 2; // Simplified annualization
    
    // Calculate daily returns (simplified)
    const dailyReturns = this.calculateDailyReturns();
    const volatility = this.calculateVolatility(dailyReturns);
    const sharpeRatio = volatility > 0 ? (annualizedReturn / 100) / volatility : 0;
    
    this.portfolioState.performance_metrics = {
      total_return: totalReturn,
      annualized_return: annualizedReturn,
      volatility: volatility * 100,
      information_ratio: sharpeRatio,
      tracking_error: volatility * 100,
      alpha: annualizedReturn - 8, // Assuming 8% benchmark
      strategy_contributions: this.portfolioState.performance_metrics.strategy_contributions,
      attribution_analysis: this.portfolioState.performance_metrics.attribution_analysis
    };
  }

  private async calculateStrategyContributions(): Promise<void> {
    const contributions: Record<string, StrategyContribution> = {};
    
    this.strategies.forEach((strategy, strategyId) => {
      const strategyPositions = this.portfolioState.positions.filter(p => p.strategy_id === strategyId);
      const strategyValue = strategyPositions.reduce((sum, pos) => sum + pos.position_value, 0);
      const strategyPnL = strategyPositions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0);
      const strategyReturn = strategyValue > 0 ? (strategyPnL / strategyValue) * 100 : 0;
      const allocation = this.portfolioState.current_allocations[strategyId] || 0;
      
      contributions[strategyId] = {
        strategy_id: strategyId,
        return_contribution: strategyReturn * (allocation / 100),
        risk_contribution: this.calculateStrategyRiskContribution(strategyId),
        allocation: allocation,
        individual_return: strategyReturn,
        correlation_with_portfolio: this.calculateCorrelationWithPortfolio(strategyId)
      };
    });
    
    this.portfolioState.performance_metrics.strategy_contributions = contributions;
  }

  private async calculateRiskMetrics(): Promise<void> {
    // Calculate correlation matrix
    await this.updateCorrelationMatrix();
    
    // Calculate portfolio VaR (simplified)
    const dailyReturns = this.calculateDailyReturns();
    const sortedReturns = dailyReturns.sort((a, b) => a - b);
    const var95Index = Math.floor(sortedReturns.length * 0.05);
    const portfolioVar = sortedReturns[var95Index] || 0;
    
    // Calculate drawdown
    const { maxDrawdown, currentDrawdown } = this.calculateDrawdown();
    
    // Update risk metrics
    this.portfolioState.risk_metrics = {
      portfolio_var: Math.abs(portfolioVar) * this.portfolioState.total_equity / 100,
      portfolio_cvar: Math.abs(portfolioVar * 1.3) * this.portfolioState.total_equity / 100,
      beta: this.calculatePortfolioBeta(),
      correlation_matrix: this.buildCorrelationMatrix(),
      concentration_risk: this.calculateConcentrationRisk(),
      max_drawdown: maxDrawdown,
      current_drawdown: currentDrawdown,
      sharpe_ratio: this.portfolioState.performance_metrics.information_ratio,
      sortino_ratio: this.calculateSortinoRatio(),
      calmar_ratio: this.calculateCalmarRatio()
    };
  }

  private async checkRebalancingNeeds(): Promise<void> {
    if (this.shouldRebalance()) {
      await this.rebalancePortfolio();
    }
  }

  private shouldRebalance(): boolean {
    const now = new Date();
    
    // Check time-based rebalancing
    if (now >= this.portfolioState.next_rebalance) {
      return true;
    }
    
    // Check drift-based rebalancing
    const maxDrift = this.calculateMaxAllocationDrift();
    if (maxDrift > this.config.rebalancing.drift_threshold) {
      return true;
    }
    
    // Check risk-based rebalancing
    if (this.portfolioState.risk_metrics.current_drawdown > this.config.risk_management.max_portfolio_drawdown * 0.8) {
      return true;
    }
    
    return false;
  }

  private async rebalancePortfolio(): Promise<void> {
    console.log('Starting portfolio rebalancing...');
    
    try {
      // Calculate optimal allocations
      const optimalAllocations = await this.calculateOptimalAllocations();
      
      // Generate rebalancing actions
      const actions = this.generateRebalancingActions(optimalAllocations);
      
      // Execute rebalancing actions
      await this.executeRebalancingActions(actions);
      
      // Update state
      this.portfolioState.last_rebalance = new Date();
      this.portfolioState.next_rebalance = this.calculateNextRebalanceDate(new Date());
      
      console.log('Portfolio rebalancing completed');
      
    } catch (error) {
      console.error('Error during portfolio rebalancing:', error);
    }
  }

  private async calculateOptimalAllocations(): Promise<Record<string, number>> {
    const allocations: Record<string, number> = {};
    
    switch (this.config.optimization.optimization_objective) {
      case 'sharpe_ratio':
        return this.optimizeForSharpeRatio();
      case 'total_return':
        return this.optimizeForTotalReturn();
      case 'risk_adjusted_return':
        return this.optimizeForRiskAdjustedReturn();
      case 'diversification':
        return this.optimizeForDiversification();
      default:
        return this.equalWeightAllocation();
    }
  }

  private optimizeForSharpeRatio(): Record<string, number> {
    // Simplified mean-variance optimization
    const allocations: Record<string, number> = {};
    const activeStrategies = Array.from(this.strategies.entries()).filter(([_, s]) => s.active);
    
    if (activeStrategies.length === 0) return allocations;
    
    // Calculate expected returns and risks for each strategy
    const expectedReturns = activeStrategies.map(([id, _]) => this.getStrategyExpectedReturn(id));
    const risks = activeStrategies.map(([id, _]) => this.getStrategyRisk(id));
    
    // Simple inverse volatility weighting
    const inverseVolatilities = risks.map(risk => risk > 0 ? 1 / risk : 1);
    const totalInverseVol = inverseVolatilities.reduce((sum, iv) => sum + iv, 0);
    
    activeStrategies.forEach(([id, _], index) => {
      const weight = (inverseVolatilities[index] / totalInverseVol) * 100;
      allocations[id] = Math.max(
        this.config.optimization.min_strategy_allocation,
        Math.min(this.config.optimization.max_strategy_allocation, weight)
      );
    });
    
    return this.normalizeAllocations(allocations);
  }

  private optimizeForTotalReturn(): Record<string, number> {
    const allocations: Record<string, number> = {};
    const activeStrategies = Array.from(this.strategies.entries()).filter(([_, s]) => s.active);
    
    // Weight by expected returns
    const expectedReturns = activeStrategies.map(([id, _]) => Math.max(0, this.getStrategyExpectedReturn(id)));
    const totalReturn = expectedReturns.reduce((sum, ret) => sum + ret, 0);
    
    if (totalReturn === 0) return this.equalWeightAllocation();
    
    activeStrategies.forEach(([id, _], index) => {
      const weight = (expectedReturns[index] / totalReturn) * 100;
      allocations[id] = Math.max(
        this.config.optimization.min_strategy_allocation,
        Math.min(this.config.optimization.max_strategy_allocation, weight)
      );
    });
    
    return this.normalizeAllocations(allocations);
  }

  private optimizeForRiskAdjustedReturn(): Record<string, number> {
    const allocations: Record<string, number> = {};
    const activeStrategies = Array.from(this.strategies.entries()).filter(([_, s]) => s.active);
    
    // Weight by Sharpe ratio
    const sharpeRatios = activeStrategies.map(([id, _]) => this.getStrategySharpeRatio(id));
    const totalSharpe = sharpeRatios.reduce((sum, sr) => sum + Math.max(0, sr), 0);
    
    if (totalSharpe === 0) return this.equalWeightAllocation();
    
    activeStrategies.forEach(([id, _], index) => {
      const weight = (Math.max(0, sharpeRatios[index]) / totalSharpe) * 100;
      allocations[id] = Math.max(
        this.config.optimization.min_strategy_allocation,
        Math.min(this.config.optimization.max_strategy_allocation, weight)
      );
    });
    
    return this.normalizeAllocations(allocations);
  }

  private optimizeForDiversification(): Record<string, number> {
    // Equal risk contribution
    const allocations: Record<string, number> = {};
    const activeStrategies = Array.from(this.strategies.entries()).filter(([_, s]) => s.active);
    
    const risks = activeStrategies.map(([id, _]) => this.getStrategyRisk(id));
    const totalRiskInverse = risks.reduce((sum, risk) => sum + (risk > 0 ? 1/risk : 1), 0);
    
    activeStrategies.forEach(([id, _], index) => {
      const riskInverse = risks[index] > 0 ? 1/risks[index] : 1;
      const weight = (riskInverse / totalRiskInverse) * 100;
      allocations[id] = Math.max(
        this.config.optimization.min_strategy_allocation,
        Math.min(this.config.optimization.max_strategy_allocation, weight)
      );
    });
    
    return this.normalizeAllocations(allocations);
  }

  private equalWeightAllocation(): Record<string, number> {
    const allocations: Record<string, number> = {};
    const activeStrategies = Array.from(this.strategies.entries()).filter(([_, s]) => s.active);
    
    if (activeStrategies.length === 0) return allocations;
    
    const equalWeight = 100 / activeStrategies.length;
    activeStrategies.forEach(([id, _]) => {
      allocations[id] = equalWeight;
    });
    
    return allocations;
  }

  private normalizeAllocations(allocations: Record<string, number>): Record<string, number> {
    const total = Object.values(allocations).reduce((sum, alloc) => sum + alloc, 0);
    
    if (total === 0) return allocations;
    
    const normalized: Record<string, number> = {};
    Object.entries(allocations).forEach(([id, alloc]) => {
      normalized[id] = (alloc / total) * 100;
    });
    
    return normalized;
  }

  private generateRebalancingActions(optimalAllocations: Record<string, number>): RebalancingAction[] {
    const actions: RebalancingAction[] = [];
    
    Object.entries(optimalAllocations).forEach(([strategyId, targetAllocation]) => {
      const currentAllocation = this.portfolioState.current_allocations[strategyId] || 0;
      const allocationDiff = Math.abs(targetAllocation - currentAllocation);
      
      if (allocationDiff > this.config.rebalancing.drift_threshold) {
        const action: RebalancingAction = {
          action_id: `rebal_${Date.now()}_${strategyId}`,
          timestamp: new Date(),
          action_type: targetAllocation > currentAllocation ? 'increase_allocation' : 'decrease_allocation',
          strategy_id: strategyId,
          current_allocation: currentAllocation,
          target_allocation: targetAllocation,
          rebalancing_amount: (targetAllocation - currentAllocation) * this.portfolioState.total_equity / 100,
          reason: `Drift exceeded threshold: ${allocationDiff.toFixed(2)}%`,
          expected_impact: {
            risk_change: this.estimateRiskChange(strategyId, targetAllocation - currentAllocation),
            return_change: this.estimateReturnChange(strategyId, targetAllocation - currentAllocation),
            transaction_cost: this.estimateTransactionCost(strategyId, Math.abs(targetAllocation - currentAllocation))
          }
        };
        
        actions.push(action);
      }
    });
    
    return actions;
  }

  private async executeRebalancingActions(actions: RebalancingAction[]): Promise<void> {
    for (const action of actions) {
      try {
        // Update allocation
        this.portfolioState.current_allocations[action.strategy_id] = action.target_allocation;
        
        // Adjust positions if needed
        await this.adjustStrategyPositions(action);
        
        // Record action
        this.rebalancingHistory.push(action);
        
        console.log(`Rebalancing: ${action.action_type} ${action.strategy_id} to ${action.target_allocation.toFixed(2)}%`);
        
      } catch (error) {
        console.error(`Error executing rebalancing action for ${action.strategy_id}:`, error);
      }
    }
  }

  private async adjustStrategyPositions(action: RebalancingAction): Promise<void> {
    const strategyPositions = this.portfolioState.positions.filter(p => p.strategy_id === action.strategy_id);
    const allocationChange = action.target_allocation - action.current_allocation;
    
    if (allocationChange > 0) {
      // Increase allocation - add cash to strategy
      const additionalCash = (allocationChange / 100) * this.portfolioState.total_equity;
      this.portfolioState.available_cash -= additionalCash;
    } else {
      // Decrease allocation - remove cash from strategy
      const cashToRemove = Math.abs(allocationChange / 100) * this.portfolioState.total_equity;
      
      // Close some positions if needed
      let cashRemoved = 0;
      for (const position of strategyPositions) {
        if (cashRemoved >= cashToRemove) break;
        
        const positionValue = position.position_value;
        const neededCash = Math.min(positionValue, cashToRemove - cashRemoved);
        
        // Partial or full position close
        const closeRatio = neededCash / positionValue;
        position.quantity = Math.floor(position.quantity * (1 - closeRatio));
        position.position_value = position.current_price * position.quantity;
        
        cashRemoved += neededCash;
        this.portfolioState.available_cash += neededCash;
        this.portfolioState.realized_pnl += position.unrealized_pnl * closeRatio;
      }
      
      // Remove fully closed positions
      this.portfolioState.positions = this.portfolioState.positions.filter(p => p.quantity > 0);
    }
  }

  private async monitorRisksAndAlerts(): Promise<void> {
    const newAlerts: PortfolioAlert[] = [];
    
    // Risk monitoring
    if (this.portfolioState.risk_metrics.current_drawdown > this.config.risk_management.max_portfolio_drawdown) {
      newAlerts.push({
        alert_id: `alert_${Date.now()}_drawdown`,
        timestamp: new Date(),
        severity: 'critical',
        category: 'risk',
        message: `Portfolio drawdown (${this.portfolioState.risk_metrics.current_drawdown.toFixed(2)}%) exceeds limit (${this.config.risk_management.max_portfolio_drawdown}%)`,
        affected_strategies: Array.from(this.strategies.keys()),
        recommended_actions: ['Reduce portfolio risk', 'Consider defensive positioning'],
        auto_actionable: false
      });
    }
    
    // Concentration risk
    if (this.portfolioState.risk_metrics.concentration_risk > this.config.risk_management.concentration_limits.max_single_strategy) {
      newAlerts.push({
        alert_id: `alert_${Date.now()}_concentration`,
        timestamp: new Date(),
        severity: 'warning',
        category: 'risk',
        message: `High concentration risk detected`,
        affected_strategies: [],
        recommended_actions: ['Diversify positions', 'Reduce position sizes'],
        auto_actionable: true
      });
    }
    
    // Performance alerts
    const portfolioReturn = this.portfolioState.performance_metrics.total_return;
    if (portfolioReturn < -10) { // 10% loss
      newAlerts.push({
        alert_id: `alert_${Date.now()}_performance`,
        timestamp: new Date(),
        severity: 'warning',
        category: 'performance',
        message: `Portfolio performance is significantly negative (${portfolioReturn.toFixed(2)}%)`,
        affected_strategies: Array.from(this.strategies.keys()),
        recommended_actions: ['Review strategy performance', 'Consider rebalancing'],
        auto_actionable: false
      });
    }
    
    // Add new alerts
    this.alerts.push(...newAlerts);
    
    // Keep only recent alerts (last 100)
    this.alerts = this.alerts.slice(-100);
  }

  // Utility methods
  private closeStrategyPositions(strategyId: string): void {
    const strategyPositions = this.portfolioState.positions.filter(p => p.strategy_id === strategyId);
    
    strategyPositions.forEach(position => {
      this.portfolioState.realized_pnl += position.unrealized_pnl;
      this.portfolioState.available_cash += position.position_value;
    });
    
    // Remove strategy positions
    this.portfolioState.positions = this.portfolioState.positions.filter(p => p.strategy_id !== strategyId);
  }

  private calculateNextRebalanceDate(fromDate: Date): Date {
    const next = new Date(fromDate);
    
    switch (this.config.rebalancing.frequency) {
      case 'real_time':
        next.setMinutes(next.getMinutes() + 1);
        break;
      case 'hourly':
        next.setHours(next.getHours() + 1);
        break;
      case 'daily':
        next.setDate(next.getDate() + 1);
        break;
      case 'weekly':
        next.setDate(next.getDate() + 7);
        break;
    }
    
    return next;
  }

  private validateStrategy(strategy: StrategyConfig): void {
    if (strategy.allocation_percentage < 0 || strategy.allocation_percentage > 100) {
      throw new Error('Strategy allocation must be between 0 and 100%');
    }
    
    if (strategy.risk_budget <= 0) {
      throw new Error('Strategy risk budget must be positive');
    }
  }

  private getTodayTradeCount(strategyId: string): number {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return this.portfolioState.positions.filter(p => 
      p.strategy_id === strategyId && p.entry_date >= today
    ).length;
  }

  private getCurrentInstrumentExposure(symbol: string): number {
    return this.portfolioState.positions
      .filter(p => p.symbol === symbol)
      .reduce((sum, p) => sum + p.position_value, 0);
  }

  private calculateRiskContribution(capital: number, symbol: string): number {
    // Simplified risk contribution calculation
    return (capital / this.portfolioState.total_equity) * 0.02; // 2% risk per $
  }

  private calculateDailyReturns(): number[] {
    // Simplified daily returns calculation
    return Array.from({ length: 30 }, () => (Math.random() - 0.5) * 0.02);
  }

  private calculateVolatility(returns: number[]): number {
    if (returns.length === 0) return 0;
    
    const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / returns.length;
    return Math.sqrt(variance);
  }

  private calculateDrawdown(): { maxDrawdown: number; currentDrawdown: number } {
    // Simplified drawdown calculation
    const currentEquity = this.portfolioState.total_equity;
    const initialEquity = this.config.total_capital;
    const peak = Math.max(currentEquity, initialEquity);
    
    const currentDrawdown = peak > 0 ? ((peak - currentEquity) / peak) * 100 : 0;
    const maxDrawdown = Math.max(currentDrawdown, 5); // Assume 5% historical max
    
    return { maxDrawdown, currentDrawdown };
  }

  private calculateMaxAllocationDrift(): number {
    let maxDrift = 0;
    
    this.strategies.forEach((strategy, strategyId) => {
      const currentAllocation = this.portfolioState.current_allocations[strategyId] || 0;
      const targetAllocation = strategy.allocation_percentage;
      const drift = Math.abs(currentAllocation - targetAllocation);
      
      maxDrift = Math.max(maxDrift, drift);
    });
    
    return maxDrift;
  }

  private getStrategyExpectedReturn(strategyId: string): number {
    const history = this.executionHistory.get(strategyId) || [];
    if (history.length === 0) return 0;
    
    // Simplified expected return calculation
    return Math.random() * 0.15 + 0.05; // 5-20% annual return
  }

  private getStrategyRisk(strategyId: string): number {
    // Simplified risk calculation
    return Math.random() * 0.1 + 0.05; // 5-15% volatility
  }

  private getStrategySharpeRatio(strategyId: string): number {
    const expectedReturn = this.getStrategyExpectedReturn(strategyId);
    const risk = this.getStrategyRisk(strategyId);
    
    return risk > 0 ? expectedReturn / risk : 0;
  }

  private calculateStrategyRiskContribution(strategyId: string): number {
    const allocation = this.portfolioState.current_allocations[strategyId] || 0;
    const strategyRisk = this.getStrategyRisk(strategyId);
    
    return (allocation / 100) * strategyRisk;
  }

  private calculateCorrelationWithPortfolio(strategyId: string): number {
    // Simplified correlation calculation
    return Math.random() * 0.6 + 0.2; // 0.2 to 0.8 correlation
  }

  private async updateCorrelationMatrix(): Promise<void> {
    const strategyIds = Array.from(this.strategies.keys());
    const n = strategyIds.length;
    
    this.correlationMatrix = Array(n).fill(0).map(() => Array(n).fill(0));
    
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (i === j) {
          this.correlationMatrix[i][j] = 1.0;
        } else {
          // Simplified correlation calculation
          this.correlationMatrix[i][j] = Math.random() * 0.8 - 0.4; // -0.4 to 0.4
        }
      }
    }
  }

  private buildCorrelationMatrix(): Record<string, Record<string, number>> {
    const matrix: Record<string, Record<string, number>> = {};
    const strategyIds = Array.from(this.strategies.keys());
    
    strategyIds.forEach((id1, i) => {
      matrix[id1] = {};
      strategyIds.forEach((id2, j) => {
        matrix[id1][id2] = this.correlationMatrix[i]?.[j] || 0;
      });
    });
    
    return matrix;
  }

  private calculatePortfolioBeta(): number {
    // Simplified beta calculation
    return 0.8 + Math.random() * 0.4; // 0.8 to 1.2
  }

  private calculateConcentrationRisk(): number {
    if (this.portfolioState.positions.length === 0) return 0;
    
    // Herfindahl-Hirschman Index for concentration
    const weights = this.portfolioState.positions.map(p => p.allocation_percentage / 100);
    const hhi = weights.reduce((sum, weight) => sum + weight * weight, 0);
    
    return hhi * 100; // Convert to percentage
  }

  private calculateSortinoRatio(): number {
    const returns = this.calculateDailyReturns();
    const negativeReturns = returns.filter(r => r < 0);
    
    if (negativeReturns.length === 0) return Infinity;
    
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const downsideVariance = negativeReturns.reduce((sum, r) => sum + r * r, 0) / negativeReturns.length;
    const downsideDeviation = Math.sqrt(downsideVariance);
    
    return downsideDeviation > 0 ? avgReturn / downsideDeviation : 0;
  }

  private calculateCalmarRatio(): number {
    const annualizedReturn = this.portfolioState.performance_metrics.annualized_return;
    const maxDrawdown = this.portfolioState.risk_metrics.max_drawdown;
    
    return maxDrawdown > 0 ? annualizedReturn / maxDrawdown : 0;
  }

  private estimateRiskChange(strategyId: string, allocationChange: number): number {
    const strategyRisk = this.getStrategyRisk(strategyId);
    return (allocationChange / 100) * strategyRisk;
  }

  private estimateReturnChange(strategyId: string, allocationChange: number): number {
    const strategyReturn = this.getStrategyExpectedReturn(strategyId);
    return (allocationChange / 100) * strategyReturn;
  }

  private estimateTransactionCost(strategyId: string, allocationChange: number): number {
    const transactionValue = (allocationChange / 100) * this.portfolioState.total_equity;
    return transactionValue * 0.001; // 0.1% transaction cost
  }

  // Public API methods
  public getPortfolioState(): PortfolioState {
    return { ...this.portfolioState };
  }

  public getStrategies(): StrategyConfig[] {
    return Array.from(this.strategies.values());
  }

  public getAlerts(): PortfolioAlert[] {
    return [...this.alerts];
  }

  public getRebalancingHistory(): RebalancingAction[] {
    return [...this.rebalancingHistory];
  }

  public updateStrategyAllocation(strategyId: string, newAllocation: number): void {
    if (newAllocation < 0 || newAllocation > 100) {
      throw new Error('Allocation must be between 0 and 100%');
    }

    const strategy = this.strategies.get(strategyId);
    if (!strategy) {
      throw new Error(`Strategy ${strategyId} not found`);
    }

    strategy.allocation_percentage = newAllocation;
    this.scheduleRebalancing();
  }

  public activateStrategy(strategyId: string): void {
    const strategy = this.strategies.get(strategyId);
    if (!strategy) {
      throw new Error(`Strategy ${strategyId} not found`);
    }

    strategy.active = true;
    console.log(`Strategy ${strategyId} activated`);
  }

  public deactivateStrategy(strategyId: string): void {
    const strategy = this.strategies.get(strategyId);
    if (!strategy) {
      throw new Error(`Strategy ${strategyId} not found`);
    }

    strategy.active = false;
    this.closeStrategyPositions(strategyId);
    console.log(`Strategy ${strategyId} deactivated`);
  }

  private scheduleRebalancing(): void {
    // Trigger immediate rebalancing check
    setTimeout(() => {
      this.checkRebalancingNeeds();
    }, 1000);
  }
}

// Export function for creating portfolio orchestrator
export const createPortfolioOrchestrator = (config: PortfolioConfig): PortfolioOrchestrator => {
  return new PortfolioOrchestrator(config);
};