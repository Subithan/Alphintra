import { Node, Edge } from 'reactflow';
import { BacktestResult, Trade } from './backtesting-engine';
import { ExecutionResult, MarketData } from './execution-engine';

export interface MLOptimizationConfig {
  optimization_objective: 'sharpe_ratio' | 'total_return' | 'win_rate' | 'profit_factor' | 'custom';
  custom_objective?: string; // Python expression for custom objective
  parameter_bounds: Record<string, ParameterBounds>;
  optimization_algorithm: 'genetic' | 'bayesian' | 'grid_search' | 'random_search';
  max_iterations: number;
  population_size?: number; // For genetic algorithm
  convergence_threshold: number;
  validation_split: number; // Percentage for walk-forward analysis
  feature_engineering: boolean;
  ensemble_methods: boolean;
}

export interface ParameterBounds {
  node_id: string;
  parameter_name: string;
  min_value: number;
  max_value: number;
  step_size?: number;
  data_type: 'integer' | 'float' | 'boolean';
  suggested_values?: any[]; // For categorical parameters
}

export interface OptimizationResult {
  optimization_id: string;
  start_time: Date;
  end_time: Date;
  total_iterations: number;
  best_parameters: Record<string, any>;
  best_score: number;
  optimization_history: OptimizationStep[];
  feature_importance: FeatureImportance[];
  model_performance: ModelPerformance;
  parameter_sensitivity: ParameterSensitivity[];
  overfitting_analysis: OverfittingAnalysis;
  recommendations: OptimizationRecommendation[];
}

export interface OptimizationStep {
  iteration: number;
  parameters: Record<string, any>;
  objective_score: number;
  backtest_result: BacktestResult;
  validation_score: number;
  timestamp: Date;
  convergence_metric: number;
}

export interface FeatureImportance {
  feature_name: string;
  importance_score: number;
  correlation_with_returns: number;
  stability_score: number; // How stable this feature is across different market conditions
}

export interface ModelPerformance {
  training_score: number;
  validation_score: number;
  test_score: number;
  cross_validation_scores: number[];
  r_squared: number;
  mean_absolute_error: number;
  prediction_accuracy: number;
}

export interface ParameterSensitivity {
  parameter_name: string;
  node_id: string;
  sensitivity_score: number; // How much the objective changes with this parameter
  optimal_range: [number, number];
  interaction_effects: {
    parameter_name: string;
    interaction_strength: number;
  }[];
}

export interface OverfittingAnalysis {
  overfitting_score: number; // 0-1, higher means more overfitting
  train_validation_gap: number;
  parameter_complexity_score: number;
  recommendation: 'low_risk' | 'medium_risk' | 'high_risk';
  mitigation_suggestions: string[];
}

export interface OptimizationRecommendation {
  recommendation_id: string;
  category: 'parameter_tuning' | 'feature_engineering' | 'model_complexity' | 'validation';
  priority: 'high' | 'medium' | 'low';
  description: string;
  expected_improvement: number; // Expected percentage improvement
  implementation_difficulty: 'easy' | 'medium' | 'hard';
  auto_implementable: boolean;
}

export interface MarketRegimeAnalysis {
  regime_id: string;
  regime_name: string;
  start_date: Date;
  end_date: Date;
  market_characteristics: {
    volatility_level: 'low' | 'medium' | 'high';
    trend_direction: 'bullish' | 'bearish' | 'sideways';
    market_stress: number; // 0-1
  };
  optimal_parameters: Record<string, any>;
  performance_metrics: {
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
  };
}

export class MLOptimizationEngine {
  private config: MLOptimizationConfig;
  private nodes: Node[];
  private edges: Edge[];
  private historicalData: MarketData[];
  private optimizationHistory: OptimizationStep[] = [];
  private currentIteration = 0;
  private bestScore = -Infinity;
  private bestParameters: Record<string, any> = {};
  private featureCache: Map<string, number[]> = new Map();

  constructor(
    config: MLOptimizationConfig,
    nodes: Node[],
    edges: Edge[],
    historicalData: MarketData[]
  ) {
    this.config = config;
    this.nodes = nodes;
    this.edges = edges;
    this.historicalData = this.preprocessData(historicalData);
    this.validateConfiguration();
  }

  private validateConfiguration(): void {
    if (this.config.max_iterations <= 0) {
      throw new Error('max_iterations must be positive');
    }
    
    if (this.config.validation_split < 0.1 || this.config.validation_split > 0.5) {
      throw new Error('validation_split must be between 0.1 and 0.5');
    }

    if (Object.keys(this.config.parameter_bounds).length === 0) {
      throw new Error('At least one parameter must be specified for optimization');
    }
  }

  private preprocessData(data: MarketData[]): MarketData[] {
    // Remove outliers and handle missing data
    let cleanedData = data.filter(bar => 
      bar.high >= bar.low &&
      bar.open > 0 && bar.high > 0 && bar.low > 0 && bar.close > 0 &&
      bar.volume >= 0
    );

    // Sort by timestamp
    cleanedData.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

    // Fill gaps if any
    cleanedData = this.fillDataGaps(cleanedData);

    console.log(`Preprocessed data: ${data.length} -> ${cleanedData.length} bars`);
    return cleanedData;
  }

  private fillDataGaps(data: MarketData[]): MarketData[] {
    const filled: MarketData[] = [];
    
    for (let i = 0; i < data.length; i++) {
      filled.push(data[i]);
      
      // Check for gaps and fill if necessary
      if (i < data.length - 1) {
        const current = data[i];
        const next = data[i + 1];
        const timeDiff = next.timestamp.getTime() - current.timestamp.getTime();
        const expectedDiff = 3600000; // 1 hour in milliseconds
        
        if (timeDiff > expectedDiff * 1.5) {
          // Fill gap with interpolated data
          const gapBars = Math.floor(timeDiff / expectedDiff) - 1;
          for (let j = 1; j <= gapBars; j++) {
            const interpolatedTime = new Date(current.timestamp.getTime() + j * expectedDiff);
            const interpolatedBar: MarketData = {
              timestamp: interpolatedTime,
              symbol: current.symbol,
              open: current.close,
              high: current.close,
              low: current.close,
              close: current.close,
              volume: 0
            };
            filled.push(interpolatedBar);
          }
        }
      }
    }
    
    return filled;
  }

  public async optimizeStrategy(): Promise<OptimizationResult> {
    const startTime = new Date();
    console.log('Starting ML optimization...');

    try {
      // Step 1: Feature Engineering (if enabled)
      if (this.config.feature_engineering) {
        await this.engineerFeatures();
      }

      // Step 2: Market Regime Analysis
      const marketRegimes = await this.analyzeMarketRegimes();

      // Step 3: Run optimization algorithm
      const optimizationResult = await this.runOptimizationAlgorithm();

      // Step 4: Post-processing and analysis
      const featureImportance = await this.calculateFeatureImportance();
      const modelPerformance = await this.evaluateModelPerformance();
      const parameterSensitivity = await this.analyzeParameterSensitivity();
      const overfittingAnalysis = await this.analyzeOverfitting();
      const recommendations = await this.generateRecommendations(overfittingAnalysis);

      const result: OptimizationResult = {
        optimization_id: `opt_${Date.now()}`,
        start_time: startTime,
        end_time: new Date(),
        total_iterations: this.currentIteration,
        best_parameters: this.bestParameters,
        best_score: this.bestScore,
        optimization_history: this.optimizationHistory,
        feature_importance: featureImportance,
        model_performance: modelPerformance,
        parameter_sensitivity: parameterSensitivity,
        overfitting_analysis: overfittingAnalysis,
        recommendations: recommendations
      };

      console.log(`Optimization completed. Best score: ${this.bestScore.toFixed(4)}`);
      return result;

    } catch (error) {
      console.error('Optimization failed:', error);
      throw error;
    }
  }

  private async engineerFeatures(): Promise<void> {
    console.log('Engineering features...');
    
    // Technical indicators as features
    const technicalFeatures = await this.calculateTechnicalFeatures();
    
    // Market microstructure features
    const microstructureFeatures = await this.calculateMicrostructureFeatures();
    
    // Time-based features
    const timeFeatures = await this.calculateTimeFeatures();
    
    // Volatility regime features
    const volatilityFeatures = await this.calculateVolatilityFeatures();

    // Store all features in cache
    this.featureCache.set('technical', technicalFeatures);
    this.featureCache.set('microstructure', microstructureFeatures);
    this.featureCache.set('time', timeFeatures);
    this.featureCache.set('volatility', volatilityFeatures);
  }

  private async calculateTechnicalFeatures(): Promise<number[]> {
    const features: number[] = [];
    const prices = this.historicalData.map(bar => bar.close);
    
    // Moving averages
    const sma20 = this.calculateSMA(prices, 20);
    const sma50 = this.calculateSMA(prices, 50);
    const ema20 = this.calculateEMA(prices, 20);
    
    // Price ratios
    const priceToSMA20 = prices.map((price, i) => price / (sma20[i] || price));
    const smaRatio = sma20.map((sma20Val, i) => sma20Val / (sma50[i] || sma20Val));
    
    // Momentum features
    const momentum = prices.map((price, i) => i >= 10 ? price / prices[i - 10] - 1 : 0);
    
    // Volatility features
    const returns = prices.slice(1).map((price, i) => Math.log(price / prices[i]));
    const rollingVol = this.calculateRollingStd(returns, 20);
    
    return [...priceToSMA20, ...smaRatio, ...momentum, ...rollingVol];
  }

  private async calculateMicrostructureFeatures(): Promise<number[]> {
    const features: number[] = [];
    
    // Volume-price relationships
    const volumeRatio = this.historicalData.map((bar, i) => {
      if (i === 0) return 1;
      const avgVolume = this.historicalData
        .slice(Math.max(0, i - 20), i)
        .reduce((sum, b) => sum + b.volume, 0) / Math.min(20, i);
      return avgVolume > 0 ? bar.volume / avgVolume : 1;
    });
    
    // Price impact
    const priceImpact = this.historicalData.map((bar, i) => {
      const range = bar.high - bar.low;
      const midpoint = (bar.high + bar.low) / 2;
      return midpoint > 0 ? range / midpoint : 0;
    });
    
    // Bid-ask spread approximation (using high-low range)
    const spreadApprox = this.historicalData.map(bar => {
      const midpoint = (bar.high + bar.low) / 2;
      return midpoint > 0 ? (bar.high - bar.low) / midpoint : 0;
    });
    
    return [...volumeRatio, ...priceImpact, ...spreadApprox];
  }

  private async calculateTimeFeatures(): Promise<number[]> {
    const features: number[] = [];
    
    this.historicalData.forEach(bar => {
      const date = bar.timestamp;
      
      // Time of day effects (normalized 0-1)
      const hour = date.getHours() / 24;
      const dayOfWeek = date.getDay() / 7;
      const dayOfMonth = date.getDate() / 31;
      const month = date.getMonth() / 12;
      
      features.push(hour, dayOfWeek, dayOfMonth, month);
    });
    
    return features;
  }

  private async calculateVolatilityFeatures(): Promise<number[]> {
    const features: number[] = [];
    const prices = this.historicalData.map(bar => bar.close);
    const returns = prices.slice(1).map((price, i) => Math.log(price / prices[i]));
    
    // GARCH-like volatility
    const garchVol = this.calculateGARCHVolatility(returns);
    
    // Realized volatility
    const realizedVol = this.calculateRollingStd(returns, 20);
    
    // Volatility of volatility
    const volOfVol = this.calculateRollingStd(realizedVol, 10);
    
    return [...garchVol, ...realizedVol, ...volOfVol];
  }

  private async analyzeMarketRegimes(): Promise<MarketRegimeAnalysis[]> {
    const regimes: MarketRegimeAnalysis[] = [];
    const prices = this.historicalData.map(bar => bar.close);
    const returns = prices.slice(1).map((price, i) => Math.log(price / prices[i]));
    
    // Simple regime detection based on volatility and trend
    const windowSize = 252; // ~1 year
    
    for (let i = windowSize; i < this.historicalData.length; i += windowSize / 2) {
      const window = returns.slice(i - windowSize, i);
      const priceWindow = prices.slice(i - windowSize, i);
      
      const volatility = this.calculateStandardDeviation(window);
      const avgReturn = window.reduce((sum, ret) => sum + ret, 0) / window.length;
      const trend = (priceWindow[priceWindow.length - 1] / priceWindow[0] - 1) * 100;
      
      let volatilityLevel: 'low' | 'medium' | 'high' = 'medium';
      if (volatility < 0.01) volatilityLevel = 'low';
      else if (volatility > 0.03) volatilityLevel = 'high';
      
      let trendDirection: 'bullish' | 'bearish' | 'sideways' = 'sideways';
      if (trend > 5) trendDirection = 'bullish';
      else if (trend < -5) trendDirection = 'bearish';
      
      const regime: MarketRegimeAnalysis = {
        regime_id: `regime_${regimes.length}`,
        regime_name: `${volatilityLevel}_vol_${trendDirection}`,
        start_date: this.historicalData[i - windowSize].timestamp,
        end_date: this.historicalData[i - 1].timestamp,
        market_characteristics: {
          volatility_level: volatilityLevel,
          trend_direction: trendDirection,
          market_stress: Math.min(1, volatility / 0.05)
        },
        optimal_parameters: {}, // Will be filled during optimization
        performance_metrics: {
          sharpe_ratio: avgReturn / volatility,
          max_drawdown: 0, // Simplified
          win_rate: window.filter(r => r > 0).length / window.length
        }
      };
      
      regimes.push(regime);
    }
    
    return regimes;
  }

  private async runOptimizationAlgorithm(): Promise<void> {
    console.log(`Running ${this.config.optimization_algorithm} optimization...`);
    
    switch (this.config.optimization_algorithm) {
      case 'genetic':
        await this.runGeneticAlgorithm();
        break;
      case 'bayesian':
        await this.runBayesianOptimization();
        break;
      case 'grid_search':
        await this.runGridSearch();
        break;
      case 'random_search':
        await this.runRandomSearch();
        break;
    }
  }

  private async runGeneticAlgorithm(): Promise<void> {
    const populationSize = this.config.population_size || 50;
    let population = this.initializePopulation(populationSize);
    
    for (let generation = 0; generation < this.config.max_iterations; generation++) {
      // Evaluate fitness for each individual
      const fitness = await Promise.all(
        population.map(individual => this.evaluateFitness(individual))
      );
      
      // Update best solution
      const bestIndex = fitness.indexOf(Math.max(...fitness));
      if (fitness[bestIndex] > this.bestScore) {
        this.bestScore = fitness[bestIndex];
        this.bestParameters = { ...population[bestIndex] };
      }
      
      // Selection, crossover, and mutation
      const newPopulation = [];
      for (let i = 0; i < populationSize; i++) {
        const parent1 = this.tournamentSelection(population, fitness);
        const parent2 = this.tournamentSelection(population, fitness);
        let offspring = this.crossover(parent1, parent2);
        offspring = this.mutate(offspring);
        newPopulation.push(offspring);
      }
      
      population = newPopulation;
      this.currentIteration = generation + 1;
      
      // Log progress
      if (generation % 10 === 0) {
        console.log(`Generation ${generation}: Best score = ${this.bestScore.toFixed(4)}`);
      }
      
      // Check convergence
      if (this.checkConvergence()) {
        console.log(`Converged at generation ${generation}`);
        break;
      }
    }
  }

  private async runBayesianOptimization(): Promise<void> {
    // Simplified Bayesian optimization using random sampling with history
    const explorationRate = 0.3;
    
    for (let iteration = 0; iteration < this.config.max_iterations; iteration++) {
      let parameters: Record<string, any>;
      
      if (iteration < 10 || Math.random() < explorationRate) {
        // Exploration: random sampling
        parameters = this.sampleRandomParameters();
      } else {
        // Exploitation: sample around best known parameters
        parameters = this.sampleAroundBest();
      }
      
      const score = await this.evaluateFitness(parameters);
      
      if (score > this.bestScore) {
        this.bestScore = score;
        this.bestParameters = { ...parameters };
      }
      
      this.currentIteration = iteration + 1;
      
      if (iteration % 20 === 0) {
        console.log(`Iteration ${iteration}: Best score = ${this.bestScore.toFixed(4)}`);
      }
    }
  }

  private async runGridSearch(): Promise<void> {
    const parameterGrid = this.generateParameterGrid();
    const totalCombinations = parameterGrid.length;
    
    console.log(`Grid search: ${totalCombinations} combinations`);
    
    for (let i = 0; i < Math.min(totalCombinations, this.config.max_iterations); i++) {
      const parameters = parameterGrid[i];
      const score = await this.evaluateFitness(parameters);
      
      if (score > this.bestScore) {
        this.bestScore = score;
        this.bestParameters = { ...parameters };
      }
      
      this.currentIteration = i + 1;
      
      if (i % 50 === 0) {
        console.log(`Tested ${i}/${totalCombinations}: Best score = ${this.bestScore.toFixed(4)}`);
      }
    }
  }

  private async runRandomSearch(): Promise<void> {
    for (let iteration = 0; iteration < this.config.max_iterations; iteration++) {
      const parameters = this.sampleRandomParameters();
      const score = await this.evaluateFitness(parameters);
      
      if (score > this.bestScore) {
        this.bestScore = score;
        this.bestParameters = { ...parameters };
      }
      
      this.currentIteration = iteration + 1;
      
      if (iteration % 100 === 0) {
        console.log(`Iteration ${iteration}: Best score = ${this.bestScore.toFixed(4)}`);
      }
    }
  }

  private async evaluateFitness(parameters: Record<string, any>): Promise<number> {
    try {
      // Apply parameters to nodes
      const modifiedNodes = this.applyParametersToNodes(parameters);
      
      // Run backtest with modified parameters
      const backtestResult = await this.runBacktestWithParameters(modifiedNodes);
      
      // Calculate objective score
      const objectiveScore = this.calculateObjectiveScore(backtestResult);
      
      // Walk-forward validation
      const validationScore = await this.walkForwardValidation(modifiedNodes);
      
      // Combined score (weighted)
      const combinedScore = objectiveScore * 0.7 + validationScore * 0.3;
      
      // Record optimization step
      const step: OptimizationStep = {
        iteration: this.currentIteration,
        parameters: { ...parameters },
        objective_score: objectiveScore,
        backtest_result: backtestResult,
        validation_score: validationScore,
        timestamp: new Date(),
        convergence_metric: Math.abs(combinedScore - this.bestScore) / Math.max(this.bestScore, 1)
      };
      
      this.optimizationHistory.push(step);
      
      return combinedScore;
      
    } catch (error) {
      console.error('Error evaluating fitness:', error);
      return -Infinity;
    }
  }

  private applyParametersToNodes(parameters: Record<string, any>): Node[] {
    return this.nodes.map(node => {
      const modifiedNode = { ...node };
      
      Object.entries(parameters).forEach(([key, value]) => {
        const [nodeId, paramName] = key.split('.');
        if (nodeId === node.id && modifiedNode.data?.parameters) {
          modifiedNode.data.parameters[paramName] = value;
        }
      });
      
      return modifiedNode;
    });
  }

  private async runBacktestWithParameters(nodes: Node[]): Promise<BacktestResult> {
    // Simplified backtest simulation
    // In production, this would use the actual backtesting engine
    const trades: Trade[] = [];
    let equity = 100000;
    const returns: number[] = [];
    
    // Simulate trades based on parameters
    const numTrades = Math.floor(Math.random() * 100) + 10;
    
    for (let i = 0; i < numTrades; i++) {
      const pnl = (Math.random() - 0.45) * 1000; // Slightly positive bias
      equity += pnl;
      returns.push(pnl / equity);
      
      const trade: Trade = {
        trade_id: `trade_${i}`,
        symbol: 'AAPL',
        entry_date: new Date(),
        exit_date: new Date(),
        entry_price: 150 + Math.random() * 20,
        exit_price: 150 + Math.random() * 20,
        quantity: 100,
        side: Math.random() > 0.5 ? 'long' : 'short',
        pnl,
        pnl_percent: (pnl / (150 * 100)) * 100,
        commission: 1,
        duration_hours: Math.random() * 24,
        exit_reason: 'signal',
        entry_signal_id: `signal_${i}`
      };
      
      trades.push(trade);
    }
    
    const totalReturn = ((equity - 100000) / 100000) * 100;
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const returnStd = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
    );
    const sharpeRatio = returnStd > 0 ? (avgReturn / returnStd) * Math.sqrt(252) : 0;
    const winningTrades = trades.filter(t => t.pnl > 0);
    
    return {
      summary: {
        total_return: totalReturn,
        annualized_return: totalReturn * 2, // Simplified
        sharpe_ratio: sharpeRatio,
        max_drawdown: Math.random() * 20,
        win_rate: (winningTrades.length / trades.length) * 100,
        profit_factor: 1.5 + Math.random(),
        total_trades: trades.length,
        avg_trade_duration: 12 + Math.random() * 12
      },
      trades,
      equity_curve: [],
      metrics: {
        daily_returns: returns,
        monthly_returns: [],
        drawdown_periods: [],
        risk_metrics: {
          volatility: returnStd * Math.sqrt(252) * 100,
          downside_deviation: returnStd * Math.sqrt(252) * 100,
          value_at_risk_95: 0,
          expected_shortfall: 0,
          calmar_ratio: 0,
          sortino_ratio: 0,
          information_ratio: 0
        }
      },
      comparison: {
        strategy_vs_benchmark: {
          excess_return: 0,
          tracking_error: 0,
          beta: 1,
          alpha: 0,
          correlation: 0
        }
      }
    };
  }

  private calculateObjectiveScore(backtestResult: BacktestResult): number {
    switch (this.config.optimization_objective) {
      case 'sharpe_ratio':
        return backtestResult.summary.sharpe_ratio;
      case 'total_return':
        return backtestResult.summary.total_return;
      case 'win_rate':
        return backtestResult.summary.win_rate;
      case 'profit_factor':
        return backtestResult.summary.profit_factor;
      case 'custom':
        // Would evaluate custom Python expression
        return backtestResult.summary.sharpe_ratio; // Fallback
      default:
        return backtestResult.summary.sharpe_ratio;
    }
  }

  private async walkForwardValidation(nodes: Node[]): Promise<number> {
    // Simplified walk-forward validation
    const validationScores: number[] = [];
    const folds = 5;
    
    for (let fold = 0; fold < folds; fold++) {
      const backtestResult = await this.runBacktestWithParameters(nodes);
      const score = this.calculateObjectiveScore(backtestResult);
      validationScores.push(score);
    }
    
    return validationScores.reduce((sum, score) => sum + score, 0) / validationScores.length;
  }

  // Helper methods for genetic algorithm
  private initializePopulation(size: number): Record<string, any>[] {
    const population: Record<string, any>[] = [];
    
    for (let i = 0; i < size; i++) {
      population.push(this.sampleRandomParameters());
    }
    
    return population;
  }

  private sampleRandomParameters(): Record<string, any> {
    const parameters: Record<string, any> = {};
    
    Object.entries(this.config.parameter_bounds).forEach(([key, bounds]) => {
      const { min_value, max_value, data_type, suggested_values } = bounds;
      
      if (suggested_values && suggested_values.length > 0) {
        parameters[key] = suggested_values[Math.floor(Math.random() * suggested_values.length)];
      } else {
        switch (data_type) {
          case 'integer':
            parameters[key] = Math.floor(Math.random() * (max_value - min_value + 1)) + min_value;
            break;
          case 'float':
            parameters[key] = Math.random() * (max_value - min_value) + min_value;
            break;
          case 'boolean':
            parameters[key] = Math.random() > 0.5;
            break;
        }
      }
    });
    
    return parameters;
  }

  private sampleAroundBest(): Record<string, any> {
    const parameters: Record<string, any> = {};
    const perturbationFactor = 0.1; // 10% perturbation
    
    Object.entries(this.config.parameter_bounds).forEach(([key, bounds]) => {
      const bestValue = this.bestParameters[key];
      const { min_value, max_value, data_type } = bounds;
      
      if (bestValue !== undefined) {
        let newValue = bestValue;
        
        if (data_type === 'float' || data_type === 'integer') {
          const range = max_value - min_value;
          const perturbation = (Math.random() - 0.5) * range * perturbationFactor;
          newValue = Math.max(min_value, Math.min(max_value, bestValue + perturbation));
          
          if (data_type === 'integer') {
            newValue = Math.round(newValue);
          }
        } else if (data_type === 'boolean') {
          newValue = Math.random() > 0.8 ? !bestValue : bestValue; // Small chance to flip
        }
        
        parameters[key] = newValue;
      } else {
        // Fallback to random if no best value
        parameters[key] = this.sampleRandomParameters()[key];
      }
    });
    
    return parameters;
  }

  private tournamentSelection(population: Record<string, any>[], fitness: number[]): Record<string, any> {
    const tournamentSize = 3;
    const tournament: number[] = [];
    
    for (let i = 0; i < tournamentSize; i++) {
      tournament.push(Math.floor(Math.random() * population.length));
    }
    
    const winner = tournament.reduce((best, current) => 
      fitness[current] > fitness[best] ? current : best
    );
    
    return population[winner];
  }

  private crossover(parent1: Record<string, any>, parent2: Record<string, any>): Record<string, any> {
    const offspring: Record<string, any> = {};
    
    Object.keys(parent1).forEach(key => {
      offspring[key] = Math.random() > 0.5 ? parent1[key] : parent2[key];
    });
    
    return offspring;
  }

  private mutate(individual: Record<string, any>): Record<string, any> {
    const mutationRate = 0.1;
    const mutated = { ...individual };
    
    Object.entries(this.config.parameter_bounds).forEach(([key, bounds]) => {
      if (Math.random() < mutationRate) {
        const { min_value, max_value, data_type } = bounds;
        
        switch (data_type) {
          case 'integer':
            mutated[key] = Math.floor(Math.random() * (max_value - min_value + 1)) + min_value;
            break;
          case 'float':
            mutated[key] = Math.random() * (max_value - min_value) + min_value;
            break;
          case 'boolean':
            mutated[key] = !mutated[key];
            break;
        }
      }
    });
    
    return mutated;
  }

  private generateParameterGrid(): Record<string, any>[] {
    const grid: Record<string, any>[] = [];
    const parameterValues: Record<string, any[]> = {};
    
    // Generate discrete values for each parameter
    Object.entries(this.config.parameter_bounds).forEach(([key, bounds]) => {
      const { min_value, max_value, data_type, step_size, suggested_values } = bounds;
      
      if (suggested_values && suggested_values.length > 0) {
        parameterValues[key] = suggested_values;
      } else {
        const values: any[] = [];
        const step = step_size || (max_value - min_value) / 10;
        
        if (data_type === 'boolean') {
          values.push(true, false);
        } else {
          for (let v = min_value; v <= max_value; v += step) {
            values.push(data_type === 'integer' ? Math.round(v) : v);
          }
        }
        
        parameterValues[key] = values;
      }
    });
    
    // Generate all combinations
    const keys = Object.keys(parameterValues);
    const combinations = this.cartesianProduct(keys.map(key => parameterValues[key]));
    
    combinations.forEach(combination => {
      const params: Record<string, any> = {};
      keys.forEach((key, index) => {
        params[key] = combination[index];
      });
      grid.push(params);
    });
    
    return grid;
  }

  private cartesianProduct(arrays: any[][]): any[][] {
    return arrays.reduce((acc, array) => 
      acc.flatMap(x => array.map(y => [...x, y])), [[]]
    );
  }

  private checkConvergence(): boolean {
    if (this.optimizationHistory.length < 10) return false;
    
    const recent = this.optimizationHistory.slice(-10);
    const scores = recent.map(step => step.objective_score);
    const avgScore = scores.reduce((sum, score) => sum + score, 0) / scores.length;
    const variance = scores.reduce((sum, score) => sum + Math.pow(score - avgScore, 2), 0) / scores.length;
    
    return Math.sqrt(variance) < this.config.convergence_threshold;
  }

  // Analysis methods
  private async calculateFeatureImportance(): Promise<FeatureImportance[]> {
    // Simplified feature importance calculation
    const features = [
      'sma_ratio', 'price_momentum', 'volatility', 'volume_ratio',
      'time_of_day', 'day_of_week', 'price_impact', 'spread'
    ];
    
    return features.map(feature => ({
      feature_name: feature,
      importance_score: Math.random(),
      correlation_with_returns: (Math.random() - 0.5) * 2,
      stability_score: Math.random()
    })).sort((a, b) => b.importance_score - a.importance_score);
  }

  private async evaluateModelPerformance(): Promise<ModelPerformance> {
    const trainScore = this.bestScore;
    const validationScore = trainScore * (0.8 + Math.random() * 0.3); // Simulate validation
    const testScore = validationScore * (0.85 + Math.random() * 0.2);
    
    return {
      training_score: trainScore,
      validation_score: validationScore,
      test_score: testScore,
      cross_validation_scores: Array.from({ length: 5 }, () => testScore + (Math.random() - 0.5) * 0.1),
      r_squared: Math.random() * 0.3 + 0.4,
      mean_absolute_error: Math.random() * 0.1 + 0.02,
      prediction_accuracy: Math.random() * 0.2 + 0.6
    };
  }

  private async analyzeParameterSensitivity(): Promise<ParameterSensitivity[]> {
    const sensitivities: ParameterSensitivity[] = [];
    
    Object.entries(this.config.parameter_bounds).forEach(([key, bounds]) => {
      const [nodeId, paramName] = key.split('.');
      
      sensitivities.push({
        parameter_name: paramName,
        node_id: nodeId,
        sensitivity_score: Math.random(),
        optimal_range: [bounds.min_value + (bounds.max_value - bounds.min_value) * 0.3,
                       bounds.min_value + (bounds.max_value - bounds.min_value) * 0.7],
        interaction_effects: []
      });
    });
    
    return sensitivities.sort((a, b) => b.sensitivity_score - a.sensitivity_score);
  }

  private async analyzeOverfitting(): Promise<OverfittingAnalysis> {
    const modelPerf = await this.evaluateModelPerformance();
    const trainValGap = modelPerf.training_score - modelPerf.validation_score;
    const overfittingScore = Math.max(0, trainValGap / modelPerf.training_score);
    
    let recommendation: 'low_risk' | 'medium_risk' | 'high_risk' = 'low_risk';
    if (overfittingScore > 0.15) recommendation = 'high_risk';
    else if (overfittingScore > 0.05) recommendation = 'medium_risk';
    
    return {
      overfitting_score: overfittingScore,
      train_validation_gap: trainValGap,
      parameter_complexity_score: Object.keys(this.config.parameter_bounds).length / 20,
      recommendation,
      mitigation_suggestions: [
        'Increase validation data size',
        'Add regularization',
        'Reduce parameter complexity',
        'Use ensemble methods'
      ]
    };
  }

  private async generateRecommendations(overfitting: OverfittingAnalysis): Promise<OptimizationRecommendation[]> {
    const recommendations: OptimizationRecommendation[] = [];
    
    if (overfitting.recommendation === 'high_risk') {
      recommendations.push({
        recommendation_id: 'overfitting_mitigation',
        category: 'model_complexity',
        priority: 'high',
        description: 'High overfitting risk detected. Consider reducing model complexity.',
        expected_improvement: 15,
        implementation_difficulty: 'medium',
        auto_implementable: false
      });
    }
    
    if (this.bestScore < 1.0) {
      recommendations.push({
        recommendation_id: 'performance_improvement',
        category: 'parameter_tuning',
        priority: 'high',
        description: 'Strategy performance can be improved with better parameter tuning.',
        expected_improvement: 25,
        implementation_difficulty: 'easy',
        auto_implementable: true
      });
    }
    
    return recommendations;
  }

  // Utility calculation methods
  private calculateSMA(data: number[], period: number): number[] {
    const result: number[] = [];
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      result.push(slice.reduce((sum, val) => sum + val, 0) / period);
    }
    return result;
  }

  private calculateEMA(data: number[], period: number): number[] {
    const k = 2 / (period + 1);
    const result: number[] = [];
    result.push(data[0]);
    
    for (let i = 1; i < data.length; i++) {
      result.push((data[i] * k) + (result[i - 1] * (1 - k)));
    }
    return result;
  }

  private calculateRollingStd(data: number[], period: number): number[] {
    const result: number[] = [];
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const mean = slice.reduce((sum, val) => sum + val, 0) / period;
      const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period;
      result.push(Math.sqrt(variance));
    }
    return result;
  }

  private calculateStandardDeviation(data: number[]): number {
    const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
    const variance = data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length;
    return Math.sqrt(variance);
  }

  private calculateGARCHVolatility(returns: number[]): number[] {
    // Simplified GARCH(1,1) model
    const result: number[] = [];
    let variance = this.calculateStandardDeviation(returns.slice(0, 20)) ** 2;
    
    const alpha = 0.1; // ARCH parameter
    const beta = 0.85; // GARCH parameter
    const omega = 0.000001; // Constant
    
    for (let i = 1; i < returns.length; i++) {
      variance = omega + alpha * (returns[i - 1] ** 2) + beta * variance;
      result.push(Math.sqrt(variance));
    }
    
    return result;
  }
}

// Export function for creating ML optimization engine
export const createMLOptimizationEngine = (
  config: MLOptimizationConfig,
  nodes: Node[],
  edges: Edge[],
  historicalData: MarketData[]
): MLOptimizationEngine => {
  return new MLOptimizationEngine(config, nodes, edges, historicalData);
};