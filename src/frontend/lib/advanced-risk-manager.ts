import { Node, Edge } from 'reactflow';
import { SignalResult, MarketData } from './execution-engine';
import { PortfolioState, PortfolioPosition } from './portfolio-orchestrator';

export interface RiskManagerConfig {
  risk_management_mode: 'conservative' | 'moderate' | 'aggressive';
  base_position_size: number; // Base position size as percentage of portfolio
  max_position_size: number; // Maximum position size limit
  portfolio_heat: number; // Maximum portfolio risk exposure (0-1)
  volatility_lookback: number; // Days for volatility calculation
  correlation_threshold: number; // Maximum correlation between positions
  drawdown_protection: DrawdownProtectionConfig;
  dynamic_sizing: DynamicSizingConfig;
  stop_loss_config: StopLossConfig;
  position_limits: PositionLimitsConfig;
}

export interface DrawdownProtectionConfig {
  enabled: boolean;
  max_portfolio_drawdown: number; // Maximum acceptable drawdown
  drawdown_reduction_factor: number; // Reduce position sizes by this factor during drawdown
  recovery_threshold: number; // Drawdown level to resume normal sizing
  emergency_stop: number; // Stop all trading at this drawdown level
}

export interface DynamicSizingConfig {
  volatility_adjustment: boolean;
  correlation_adjustment: boolean;
  momentum_adjustment: boolean;
  kelly_criterion: boolean;
  risk_parity: boolean;
  confidence_scaling: boolean;
  market_regime_adjustment: boolean;
}

export interface StopLossConfig {
  default_stop_loss: number; // Default stop loss percentage
  trailing_stop: boolean;
  volatility_based_stops: boolean;
  atr_multiplier: number; // ATR multiplier for dynamic stops
  max_stop_distance: number; // Maximum stop loss distance
  profit_protection: boolean; // Protect profits with trailing stops
}

export interface PositionLimitsConfig {
  max_positions: number;
  max_sector_exposure: number;
  max_single_instrument: number;
  max_correlated_positions: number;
  concentration_limits: Record<string, number>;
}

export interface RiskMetrics {
  portfolio_risk: number; // Current portfolio risk level (0-1)
  position_risk: Record<string, number>; // Risk per position
  sector_risk: Record<string, number>; // Risk per sector
  correlation_risk: number; // Overall correlation risk
  volatility_risk: number; // Volatility-based risk
  concentration_risk: number; // Concentration risk measure
  var_1d: number; // 1-day Value at Risk
  var_5d: number; // 5-day Value at Risk
  expected_shortfall: number; // Expected Shortfall (CVaR)
  maximum_drawdown: number; // Maximum historical drawdown
  current_drawdown: number; // Current drawdown level
}

export interface PositionSizeCalculation {
  signal_id: string;
  symbol: string;
  base_size: number; // Base position size
  volatility_adjusted_size: number; // After volatility adjustment
  correlation_adjusted_size: number; // After correlation adjustment
  confidence_adjusted_size: number; // After confidence adjustment
  drawdown_adjusted_size: number; // After drawdown adjustment
  final_position_size: number; // Final calculated size
  risk_contribution: number; // Position's risk contribution
  stop_loss_price: number; // Calculated stop loss
  take_profit_price: number; // Calculated take profit
  max_loss_amount: number; // Maximum loss for this position
  sizing_rationale: string[]; // Explanation of sizing decisions
}

export interface RiskAlert {
  alert_id: string;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
  risk_type: 'position' | 'portfolio' | 'correlation' | 'drawdown' | 'concentration';
  message: string;
  affected_positions: string[];
  recommended_actions: string[];
  auto_action_taken: boolean;
  risk_level: number; // Numerical risk level
}

export interface MarketRegime {
  regime_type: 'trending' | 'ranging' | 'volatile' | 'calm';
  volatility_percentile: number; // Current volatility vs historical
  trend_strength: number; // 0-1, strength of current trend
  correlation_regime: 'high' | 'medium' | 'low'; // Market correlation level
  risk_adjustment_factor: number; // Adjustment to apply to position sizes
}

export class AdvancedRiskManager {
  private config: RiskManagerConfig;
  private portfolioState: PortfolioState;
  private marketData: Map<string, MarketData[]> = new Map();
  private riskMetrics: RiskMetrics;
  private alerts: RiskAlert[] = [];
  private volatilityCache: Map<string, number[]> = new Map();
  private correlationMatrix: number[][] = [];
  private marketRegime: MarketRegime;

  constructor(config: RiskManagerConfig, portfolioState: PortfolioState) {
    this.config = config;
    this.portfolioState = portfolioState;
    this.riskMetrics = this.initializeRiskMetrics();
    this.marketRegime = this.initializeMarketRegime();
    this.validateConfiguration();
  }

  private validateConfiguration(): void {
    if (this.config.base_position_size <= 0 || this.config.base_position_size > 50) {
      throw new Error('Base position size must be between 0 and 50%');
    }

    if (this.config.max_position_size <= this.config.base_position_size) {
      throw new Error('Max position size must be greater than base position size');
    }

    if (this.config.portfolio_heat <= 0 || this.config.portfolio_heat > 1) {
      throw new Error('Portfolio heat must be between 0 and 1');
    }
  }

  private initializeRiskMetrics(): RiskMetrics {
    return {
      portfolio_risk: 0,
      position_risk: {},
      sector_risk: {},
      correlation_risk: 0,
      volatility_risk: 0,
      concentration_risk: 0,
      var_1d: 0,
      var_5d: 0,
      expected_shortfall: 0,
      maximum_drawdown: 0,
      current_drawdown: 0
    };
  }

  private initializeMarketRegime(): MarketRegime {
    return {
      regime_type: 'calm',
      volatility_percentile: 50,
      trend_strength: 0.5,
      correlation_regime: 'medium',
      risk_adjustment_factor: 1.0
    };
  }

  public updateMarketData(symbol: string, data: MarketData[]): void {
    this.marketData.set(symbol, data);
    this.updateVolatilityCache(symbol, data);
    this.updateMarketRegime();
  }

  private updateVolatilityCache(symbol: string, data: MarketData[]): void {
    if (data.length < 2) return;

    const returns = data.slice(1).map((bar, i) => 
      Math.log(bar.close / data[i].close)
    );

    const volatilities = this.calculateRollingVolatility(returns, 20);
    this.volatilityCache.set(symbol, volatilities);
  }

  private updateMarketRegime(): void {
    // Analyze overall market conditions
    const allVolatilities: number[] = [];
    const allReturns: number[] = [];

    this.marketData.forEach(data => {
      if (data.length >= 2) {
        const returns = data.slice(1).map((bar, i) => 
          Math.log(bar.close / data[i].close)
        );
        allReturns.push(...returns);
        
        const vol = this.calculateVolatility(returns);
        if (vol > 0) allVolatilities.push(vol);
      }
    });

    if (allVolatilities.length === 0) return;

    // Calculate market regime
    const avgVolatility = allVolatilities.reduce((sum, vol) => sum + vol, 0) / allVolatilities.length;
    const volatilityPercentile = this.calculatePercentile(allVolatilities, avgVolatility);
    
    // Determine regime type
    let regimeType: MarketRegime['regime_type'] = 'calm';
    if (volatilityPercentile > 80) regimeType = 'volatile';
    else if (volatilityPercentile > 60) regimeType = 'ranging';
    else if (volatilityPercentile < 20) regimeType = 'calm';
    else regimeType = 'trending';

    // Calculate trend strength
    const trendStrength = this.calculateTrendStrength(allReturns);

    // Determine correlation regime
    const correlationLevel = this.calculateMarketCorrelation();
    let correlationRegime: MarketRegime['correlation_regime'] = 'medium';
    if (correlationLevel > 0.7) correlationRegime = 'high';
    else if (correlationLevel < 0.3) correlationRegime = 'low';

    // Calculate risk adjustment factor
    let riskAdjustment = 1.0;
    if (regimeType === 'volatile') riskAdjustment *= 0.7;
    else if (regimeType === 'calm') riskAdjustment *= 1.2;
    
    if (correlationRegime === 'high') riskAdjustment *= 0.8;
    
    this.marketRegime = {
      regime_type: regimeType,
      volatility_percentile,
      trend_strength: trendStrength,
      correlation_regime: correlationRegime,
      risk_adjustment_factor: riskAdjustment
    };
  }

  public calculatePositionSize(signal: SignalResult, marketData: MarketData[]): PositionSizeCalculation {
    const sizingRationale: string[] = [];
    
    // Step 1: Base position size
    let baseSize = this.config.base_position_size;
    sizingRationale.push(`Base size: ${baseSize}%`);

    // Step 2: Volatility adjustment
    let volatilityAdjustedSize = baseSize;
    if (this.config.dynamic_sizing.volatility_adjustment) {
      const volatilityAdjustment = this.calculateVolatilityAdjustment(signal.symbol, marketData);
      volatilityAdjustedSize = baseSize * volatilityAdjustment;
      sizingRationale.push(`Volatility adjustment: ${volatilityAdjustment.toFixed(2)}x`);
    }

    // Step 3: Correlation adjustment
    let correlationAdjustedSize = volatilityAdjustedSize;
    if (this.config.dynamic_sizing.correlation_adjustment) {
      const correlationAdjustment = this.calculateCorrelationAdjustment(signal.symbol);
      correlationAdjustedSize = volatilityAdjustedSize * correlationAdjustment;
      sizingRationale.push(`Correlation adjustment: ${correlationAdjustment.toFixed(2)}x`);
    }

    // Step 4: Confidence adjustment
    let confidenceAdjustedSize = correlationAdjustedSize;
    if (this.config.dynamic_sizing.confidence_scaling) {
      const confidenceAdjustment = Math.min(2.0, Math.max(0.5, signal.confidence * 2));
      confidenceAdjustedSize = correlationAdjustedSize * confidenceAdjustment;
      sizingRationale.push(`Confidence adjustment: ${confidenceAdjustment.toFixed(2)}x`);
    }

    // Step 5: Drawdown adjustment
    let drawdownAdjustedSize = confidenceAdjustedSize;
    if (this.config.drawdown_protection.enabled) {
      const drawdownAdjustment = this.calculateDrawdownAdjustment();
      drawdownAdjustedSize = confidenceAdjustedSize * drawdownAdjustment;
      sizingRationale.push(`Drawdown adjustment: ${drawdownAdjustment.toFixed(2)}x`);
    }

    // Step 6: Market regime adjustment
    let regimeAdjustedSize = drawdownAdjustedSize;
    if (this.config.dynamic_sizing.market_regime_adjustment) {
      regimeAdjustedSize = drawdownAdjustedSize * this.marketRegime.risk_adjustment_factor;
      sizingRationale.push(`Market regime adjustment: ${this.marketRegime.risk_adjustment_factor.toFixed(2)}x`);
    }

    // Step 7: Apply limits
    const finalSize = Math.min(
      regimeAdjustedSize,
      this.config.max_position_size,
      this.calculateMaxAllowableSize(signal.symbol)
    );

    if (finalSize < regimeAdjustedSize) {
      sizingRationale.push(`Capped at ${finalSize}% due to limits`);
    }

    // Calculate stop loss and take profit
    const { stopLossPrice, takeProfitPrice } = this.calculateStopLossAndTakeProfit(
      signal, marketData, finalSize
    );

    // Calculate risk contribution
    const positionValue = (finalSize / 100) * this.portfolioState.total_equity;
    const maxLossAmount = Math.abs(signal.price - stopLossPrice) * signal.quantity;
    const riskContribution = maxLossAmount / this.portfolioState.total_equity;

    return {
      signal_id: signal.signal_id,
      symbol: signal.symbol,
      base_size: baseSize,
      volatility_adjusted_size: volatilityAdjustedSize,
      correlation_adjusted_size: correlationAdjustedSize,
      confidence_adjusted_size: confidenceAdjustedSize,
      drawdown_adjusted_size: drawdownAdjustedSize,
      final_position_size: finalSize,
      risk_contribution: riskContribution,
      stop_loss_price: stopLossPrice,
      take_profit_price: takeProfitPrice,
      max_loss_amount: maxLossAmount,
      sizing_rationale: sizingRationale
    };
  }

  private calculateVolatilityAdjustment(symbol: string, marketData: MarketData[]): number {
    if (marketData.length < 20) return 1.0;

    const returns = marketData.slice(1).map((bar, i) => 
      Math.log(bar.close / marketData[i].close)
    );

    const currentVolatility = this.calculateVolatility(returns.slice(-20));
    const longTermVolatility = this.calculateVolatility(returns);

    if (longTermVolatility === 0) return 1.0;

    // Inverse volatility scaling - reduce size when volatility is high
    const volatilityRatio = currentVolatility / longTermVolatility;
    return Math.max(0.2, Math.min(2.0, 1 / Math.sqrt(volatilityRatio)));
  }

  private calculateCorrelationAdjustment(symbol: string): number {
    const existingPositions = this.portfolioState.positions;
    
    if (existingPositions.length === 0) return 1.0;

    // Calculate average correlation with existing positions
    let totalCorrelation = 0;
    let correlationCount = 0;

    existingPositions.forEach(position => {
      if (position.symbol !== symbol) {
        const correlation = this.getCorrelation(symbol, position.symbol);
        totalCorrelation += Math.abs(correlation);
        correlationCount++;
      }
    });

    if (correlationCount === 0) return 1.0;

    const avgCorrelation = totalCorrelation / correlationCount;
    
    // Reduce size if high correlation with existing positions
    if (avgCorrelation > this.config.correlation_threshold) {
      return Math.max(0.3, 1 - (avgCorrelation - this.config.correlation_threshold));
    }

    return 1.0;
  }

  private calculateDrawdownAdjustment(): number {
    if (!this.config.drawdown_protection.enabled) return 1.0;

    const currentDrawdown = this.riskMetrics.current_drawdown;
    const maxDrawdown = this.config.drawdown_protection.max_portfolio_drawdown;
    const reductionFactor = this.config.drawdown_protection.drawdown_reduction_factor;
    const recoveryThreshold = this.config.drawdown_protection.recovery_threshold;

    if (currentDrawdown <= recoveryThreshold) {
      return 1.0; // Normal sizing
    }

    if (currentDrawdown >= this.config.drawdown_protection.emergency_stop) {
      return 0.0; // Stop trading
    }

    // Linear reduction between recovery threshold and max drawdown
    const reductionRange = maxDrawdown - recoveryThreshold;
    const currentReduction = (currentDrawdown - recoveryThreshold) / reductionRange;
    
    return Math.max(0.1, 1 - (currentReduction * reductionFactor));
  }

  private calculateMaxAllowableSize(symbol: string): number {
    let maxSize = this.config.max_position_size;

    // Check concentration limits
    const sectorExposure = this.calculateSectorExposure(symbol);
    const remainingSectorCapacity = this.config.position_limits.max_sector_exposure - sectorExposure;
    maxSize = Math.min(maxSize, remainingSectorCapacity);

    // Check single instrument limit
    const currentExposure = this.calculateInstrumentExposure(symbol);
    const remainingInstrumentCapacity = this.config.position_limits.max_single_instrument - currentExposure;
    maxSize = Math.min(maxSize, remainingInstrumentCapacity);

    // Check portfolio heat limit
    const currentHeat = this.calculatePortfolioHeat();
    const remainingHeat = this.config.portfolio_heat - currentHeat;
    const heatBasedSize = (remainingHeat / this.config.portfolio_heat) * 100;
    maxSize = Math.min(maxSize, heatBasedSize);

    return Math.max(0, maxSize);
  }

  private calculateStopLossAndTakeProfit(
    signal: SignalResult, 
    marketData: MarketData[], 
    positionSize: number
  ): { stopLossPrice: number; takeProfitPrice: number } {
    let stopLossPrice = signal.price;
    let takeProfitPrice = signal.price;

    if (this.config.stop_loss_config.volatility_based_stops && marketData.length >= 20) {
      // Use ATR-based stops
      const atr = this.calculateATR(marketData.slice(-20));
      const stopDistance = atr * this.config.stop_loss_config.atr_multiplier;
      
      if (signal.action === 'buy') {
        stopLossPrice = signal.price - stopDistance;
        takeProfitPrice = signal.price + (stopDistance * 2); // 2:1 risk/reward
      } else {
        stopLossPrice = signal.price + stopDistance;
        takeProfitPrice = signal.price - (stopDistance * 2);
      }
    } else {
      // Use percentage-based stops
      const stopPercent = this.config.stop_loss_config.default_stop_loss / 100;
      
      if (signal.action === 'buy') {
        stopLossPrice = signal.price * (1 - stopPercent);
        takeProfitPrice = signal.price * (1 + stopPercent * 2);
      } else {
        stopLossPrice = signal.price * (1 + stopPercent);
        takeProfitPrice = signal.price * (1 - stopPercent * 2);
      }
    }

    // Apply maximum stop distance limit
    const maxStopDistance = (this.config.stop_loss_config.max_stop_distance / 100) * signal.price;
    const currentStopDistance = Math.abs(signal.price - stopLossPrice);
    
    if (currentStopDistance > maxStopDistance) {
      if (signal.action === 'buy') {
        stopLossPrice = signal.price - maxStopDistance;
      } else {
        stopLossPrice = signal.price + maxStopDistance;
      }
    }

    return { stopLossPrice, takeProfitPrice };
  }

  public updateRiskMetrics(): void {
    // Calculate portfolio-level risk metrics
    this.riskMetrics.portfolio_risk = this.calculatePortfolioRisk();
    this.riskMetrics.correlation_risk = this.calculateCorrelationRisk();
    this.riskMetrics.concentration_risk = this.calculateConcentrationRisk();
    this.riskMetrics.volatility_risk = this.calculateVolatilityRisk();
    
    // Calculate VaR and Expected Shortfall
    const returns = this.calculatePortfolioReturns();
    this.riskMetrics.var_1d = this.calculateVaR(returns, 0.95, 1);
    this.riskMetrics.var_5d = this.calculateVaR(returns, 0.95, 5);
    this.riskMetrics.expected_shortfall = this.calculateExpectedShortfall(returns, 0.95);

    // Update drawdown metrics
    const { maxDrawdown, currentDrawdown } = this.calculateDrawdownMetrics();
    this.riskMetrics.maximum_drawdown = maxDrawdown;
    this.riskMetrics.current_drawdown = currentDrawdown;

    // Calculate position-level risks
    this.updatePositionRisks();
    this.updateSectorRisks();
  }

  private calculatePortfolioRisk(): number {
    const positions = this.portfolioState.positions;
    if (positions.length === 0) return 0;

    let totalRisk = 0;
    positions.forEach(position => {
      const positionRisk = this.calculatePositionRisk(position);
      totalRisk += positionRisk;
    });

    return Math.min(1, totalRisk);
  }

  private calculatePositionRisk(position: PortfolioPosition): number {
    // Risk as percentage of portfolio value
    const volatility = this.getInstrumentVolatility(position.symbol);
    const positionWeight = position.position_value / this.portfolioState.total_equity;
    
    return positionWeight * volatility;
  }

  private calculateCorrelationRisk(): number {
    const positions = this.portfolioState.positions;
    if (positions.length < 2) return 0;

    let totalCorrelationRisk = 0;
    let pairCount = 0;

    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        const correlation = this.getCorrelation(positions[i].symbol, positions[j].symbol);
        const weight1 = positions[i].position_value / this.portfolioState.total_equity;
        const weight2 = positions[j].position_value / this.portfolioState.total_equity;
        
        totalCorrelationRisk += Math.abs(correlation) * weight1 * weight2;
        pairCount++;
      }
    }

    return pairCount > 0 ? totalCorrelationRisk / pairCount : 0;
  }

  private calculateConcentrationRisk(): number {
    const positions = this.portfolioState.positions;
    if (positions.length === 0) return 0;

    // Herfindahl-Hirschman Index for concentration
    const weights = positions.map(p => p.position_value / this.portfolioState.total_equity);
    const hhi = weights.reduce((sum, weight) => sum + weight * weight, 0);
    
    return hhi;
  }

  private calculateVolatilityRisk(): number {
    const positions = this.portfolioState.positions;
    if (positions.length === 0) return 0;

    let weightedVolatility = 0;
    positions.forEach(position => {
      const volatility = this.getInstrumentVolatility(position.symbol);
      const weight = position.position_value / this.portfolioState.total_equity;
      weightedVolatility += volatility * weight;
    });

    return weightedVolatility;
  }

  private calculatePortfolioReturns(): number[] {
    // Simplified portfolio returns calculation
    // In production, this would use actual historical portfolio values
    return Array.from({ length: 252 }, () => (Math.random() - 0.5) * 0.04);
  }

  private calculateVaR(returns: number[], confidence: number, days: number): number {
    if (returns.length === 0) return 0;

    const sortedReturns = [...returns].sort((a, b) => a - b);
    const index = Math.floor((1 - confidence) * sortedReturns.length);
    const dailyVaR = Math.abs(sortedReturns[index] || 0);
    
    // Scale for multiple days
    return dailyVaR * Math.sqrt(days) * this.portfolioState.total_equity;
  }

  private calculateExpectedShortfall(returns: number[], confidence: number): number {
    if (returns.length === 0) return 0;

    const sortedReturns = [...returns].sort((a, b) => a - b);
    const cutoffIndex = Math.floor((1 - confidence) * sortedReturns.length);
    
    if (cutoffIndex === 0) return Math.abs(sortedReturns[0] || 0) * this.portfolioState.total_equity;
    
    const tailReturns = sortedReturns.slice(0, cutoffIndex);
    const avgTailReturn = tailReturns.reduce((sum, ret) => sum + ret, 0) / tailReturns.length;
    
    return Math.abs(avgTailReturn) * this.portfolioState.total_equity;
  }

  private calculateDrawdownMetrics(): { maxDrawdown: number; currentDrawdown: number } {
    // Simplified drawdown calculation
    const currentEquity = this.portfolioState.total_equity;
    const initialEquity = 100000; // Assume starting value
    const peakEquity = Math.max(currentEquity, initialEquity * 1.2); // Assume some peak
    
    const currentDrawdown = ((peakEquity - currentEquity) / peakEquity) * 100;
    const maxDrawdown = Math.max(currentDrawdown, 15); // Assume 15% historical max
    
    return { maxDrawdown, currentDrawdown };
  }

  private updatePositionRisks(): void {
    this.riskMetrics.position_risk = {};
    
    this.portfolioState.positions.forEach(position => {
      this.riskMetrics.position_risk[position.position_id] = this.calculatePositionRisk(position);
    });
  }

  private updateSectorRisks(): void {
    this.riskMetrics.sector_risk = {};
    const sectorExposure: Record<string, number> = {};
    
    this.portfolioState.positions.forEach(position => {
      const sector = this.getInstrumentSector(position.symbol);
      const exposure = position.position_value / this.portfolioState.total_equity;
      
      sectorExposure[sector] = (sectorExposure[sector] || 0) + exposure;
    });
    
    Object.entries(sectorExposure).forEach(([sector, exposure]) => {
      this.riskMetrics.sector_risk[sector] = exposure;
    });
  }

  public generateRiskAlerts(): RiskAlert[] {
    const newAlerts: RiskAlert[] = [];
    
    // Portfolio-level alerts
    if (this.riskMetrics.portfolio_risk > 0.8) {
      newAlerts.push({
        alert_id: `risk_alert_${Date.now()}_portfolio`,
        timestamp: new Date(),
        severity: 'high',
        risk_type: 'portfolio',
        message: `Portfolio risk level is high (${(this.riskMetrics.portfolio_risk * 100).toFixed(1)}%)`,
        affected_positions: this.portfolioState.positions.map(p => p.position_id),
        recommended_actions: ['Reduce position sizes', 'Close some positions', 'Hedge portfolio'],
        auto_action_taken: false,
        risk_level: this.riskMetrics.portfolio_risk
      });
    }

    // Concentration alerts
    if (this.riskMetrics.concentration_risk > 0.5) {
      newAlerts.push({
        alert_id: `risk_alert_${Date.now()}_concentration`,
        timestamp: new Date(),
        severity: 'medium',
        risk_type: 'concentration',
        message: 'High portfolio concentration detected',
        affected_positions: [],
        recommended_actions: ['Diversify positions', 'Reduce large positions'],
        auto_action_taken: false,
        risk_level: this.riskMetrics.concentration_risk
      });
    }

    // Correlation alerts
    if (this.riskMetrics.correlation_risk > 0.7) {
      newAlerts.push({
        alert_id: `risk_alert_${Date.now()}_correlation`,
        timestamp: new Date(),
        severity: 'medium',
        risk_type: 'correlation',
        message: 'High correlation between positions detected',
        affected_positions: this.portfolioState.positions.map(p => p.position_id),
        recommended_actions: ['Reduce correlated positions', 'Add uncorrelated assets'],
        auto_action_taken: false,
        risk_level: this.riskMetrics.correlation_risk
      });
    }

    // Drawdown alerts
    if (this.riskMetrics.current_drawdown > this.config.drawdown_protection.max_portfolio_drawdown) {
      newAlerts.push({
        alert_id: `risk_alert_${Date.now()}_drawdown`,
        timestamp: new Date(),
        severity: 'critical',
        risk_type: 'drawdown',
        message: `Portfolio drawdown (${this.riskMetrics.current_drawdown.toFixed(1)}%) exceeds limit`,
        affected_positions: this.portfolioState.positions.map(p => p.position_id),
        recommended_actions: ['Stop new positions', 'Close losing positions', 'Review strategy'],
        auto_action_taken: this.config.drawdown_protection.enabled,
        risk_level: this.riskMetrics.current_drawdown / 100
      });
    }

    // Add new alerts to the list
    this.alerts.push(...newAlerts);
    
    // Keep only recent alerts (last 50)
    this.alerts = this.alerts.slice(-50);

    return newAlerts;
  }

  public shouldBlockTrade(signal: SignalResult): { blocked: boolean; reason: string } {
    // Check emergency stop
    if (this.config.drawdown_protection.enabled && 
        this.riskMetrics.current_drawdown >= this.config.drawdown_protection.emergency_stop) {
      return { blocked: true, reason: 'Emergency stop activated due to excessive drawdown' };
    }

    // Check position limits
    if (this.portfolioState.positions.length >= this.config.position_limits.max_positions) {
      return { blocked: true, reason: 'Maximum number of positions reached' };
    }

    // Check correlation limits
    const avgCorrelation = this.calculateAverageCorrelation(signal.symbol);
    if (avgCorrelation > this.config.correlation_threshold) {
      return { blocked: true, reason: 'Position would exceed correlation limits' };
    }

    // Check concentration limits
    const sectorExposure = this.calculateSectorExposure(signal.symbol);
    if (sectorExposure > this.config.position_limits.max_sector_exposure) {
      return { blocked: true, reason: 'Position would exceed sector exposure limits' };
    }

    // Check portfolio heat
    const currentHeat = this.calculatePortfolioHeat();
    if (currentHeat >= this.config.portfolio_heat) {
      return { blocked: true, reason: 'Portfolio heat limit reached' };
    }

    return { blocked: false, reason: '' };
  }

  // Utility methods
  private calculateRollingVolatility(returns: number[], window: number): number[] {
    const volatilities: number[] = [];
    
    for (let i = window - 1; i < returns.length; i++) {
      const windowReturns = returns.slice(i - window + 1, i + 1);
      const volatility = this.calculateVolatility(windowReturns);
      volatilities.push(volatility);
    }
    
    return volatilities;
  }

  private calculateVolatility(returns: number[]): number {
    if (returns.length < 2) return 0;
    
    const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / (returns.length - 1);
    
    return Math.sqrt(variance * 252); // Annualized volatility
  }

  private calculatePercentile(values: number[], target: number): number {
    const sorted = [...values].sort((a, b) => a - b);
    const index = sorted.findIndex(val => val >= target);
    
    if (index === -1) return 100;
    return (index / sorted.length) * 100;
  }

  private calculateTrendStrength(returns: number[]): number {
    if (returns.length < 20) return 0.5;
    
    // Calculate trend using linear regression slope
    const n = returns.length;
    const x = Array.from({ length: n }, (_, i) => i);
    const y = returns.map((ret, i) => returns.slice(0, i + 1).reduce((sum, r) => sum + r, 0));
    
    const sumX = x.reduce((sum, val) => sum + val, 0);
    const sumY = y.reduce((sum, val) => sum + val, 0);
    const sumXY = x.reduce((sum, val, i) => sum + val * y[i], 0);
    const sumXX = x.reduce((sum, val) => sum + val * val, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    
    return Math.max(0, Math.min(1, Math.abs(slope) * 10));
  }

  private calculateMarketCorrelation(): number {
    // Simplified market correlation calculation
    return 0.4 + Math.random() * 0.4; // 0.4 to 0.8
  }

  private calculateATR(data: MarketData[]): number {
    if (data.length < 2) return 0;
    
    const trueRanges = data.slice(1).map((bar, i) => {
      const prevClose = data[i].close;
      return Math.max(
        bar.high - bar.low,
        Math.abs(bar.high - prevClose),
        Math.abs(bar.low - prevClose)
      );
    });
    
    return trueRanges.reduce((sum, tr) => sum + tr, 0) / trueRanges.length;
  }

  private calculateSectorExposure(symbol: string): number {
    const sector = this.getInstrumentSector(symbol);
    return this.riskMetrics.sector_risk[sector] || 0;
  }

  private calculateInstrumentExposure(symbol: string): number {
    const positions = this.portfolioState.positions.filter(p => p.symbol === symbol);
    const totalExposure = positions.reduce((sum, p) => sum + p.position_value, 0);
    
    return (totalExposure / this.portfolioState.total_equity) * 100;
  }

  private calculatePortfolioHeat(): number {
    let totalHeat = 0;
    
    this.portfolioState.positions.forEach(position => {
      const positionRisk = this.calculatePositionRisk(position);
      totalHeat += positionRisk;
    });
    
    return totalHeat;
  }

  private calculateAverageCorrelation(symbol: string): number {
    const existingSymbols = [...new Set(this.portfolioState.positions.map(p => p.symbol))];
    
    if (existingSymbols.length === 0) return 0;
    
    const correlations = existingSymbols.map(existingSymbol => 
      Math.abs(this.getCorrelation(symbol, existingSymbol))
    );
    
    return correlations.reduce((sum, corr) => sum + corr, 0) / correlations.length;
  }

  private getCorrelation(symbol1: string, symbol2: string): number {
    if (symbol1 === symbol2) return 1.0;
    
    // Simplified correlation calculation
    // In production, this would use actual price correlation
    const key = [symbol1, symbol2].sort().join('_');
    return Math.random() * 0.8 - 0.4; // -0.4 to 0.4
  }

  private getInstrumentVolatility(symbol: string): number {
    const volatilities = this.volatilityCache.get(symbol);
    if (!volatilities || volatilities.length === 0) return 0.2; // Default 20% volatility
    
    return volatilities[volatilities.length - 1];
  }

  private getInstrumentSector(symbol: string): string {
    // Simplified sector mapping
    const sectorMap: Record<string, string> = {
      'AAPL': 'Technology',
      'GOOGL': 'Technology',
      'MSFT': 'Technology',
      'TSLA': 'Automotive',
      'JPM': 'Financial',
      'BAC': 'Financial',
      'XOM': 'Energy',
      'CVX': 'Energy'
    };
    
    return sectorMap[symbol] || 'Other';
  }

  // Public API methods
  public getRiskMetrics(): RiskMetrics {
    return { ...this.riskMetrics };
  }

  public getAlerts(): RiskAlert[] {
    return [...this.alerts];
  }

  public getMarketRegime(): MarketRegime {
    return { ...this.marketRegime };
  }

  public updatePortfolioState(newState: PortfolioState): void {
    this.portfolioState = newState;
    this.updateRiskMetrics();
  }

  public setRiskMode(mode: RiskManagerConfig['risk_management_mode']): void {
    this.config.risk_management_mode = mode;
    
    // Adjust parameters based on risk mode
    switch (mode) {
      case 'conservative':
        this.config.base_position_size = Math.min(this.config.base_position_size, 2);
        this.config.max_position_size = Math.min(this.config.max_position_size, 5);
        this.config.portfolio_heat = Math.min(this.config.portfolio_heat, 0.3);
        break;
      case 'moderate':
        this.config.base_position_size = Math.min(this.config.base_position_size, 5);
        this.config.max_position_size = Math.min(this.config.max_position_size, 10);
        this.config.portfolio_heat = Math.min(this.config.portfolio_heat, 0.6);
        break;
      case 'aggressive':
        // Keep current settings or increase them
        break;
    }
  }
}

// Export function for creating advanced risk manager
export const createAdvancedRiskManager = (
  config: RiskManagerConfig,
  portfolioState: PortfolioState
): AdvancedRiskManager => {
  return new AdvancedRiskManager(config, portfolioState);
};