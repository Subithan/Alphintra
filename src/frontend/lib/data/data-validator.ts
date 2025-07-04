import { MarketDataPoint, DataQuality, DataQualityIssue } from './market-data-client';

// Validation rules configuration
export interface ValidationRule {
  id: string;
  name: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  parameters: Record<string, any>;
}

export interface ValidationResult {
  isValid: boolean;
  score: number; // 0-100
  issues: DataQualityIssue[];
  appliedRules: string[];
  validationTime: Date;
  processingTimeMs: number;
}

export interface DataStatistics {
  symbol: string;
  timeframe: string;
  periodStart: Date;
  periodEnd: Date;
  totalBars: number;
  missingBars: number;
  completeness: number; // percentage
  averageSpread: number;
  maxSpread: number;
  priceRange: {
    min: number;
    max: number;
    volatility: number;
  };
  volumeStats: {
    average: number;
    median: number;
    outliers: number;
  };
  gapAnalysis: {
    gapCount: number;
    maxGapSize: number;
    gapPercentage: number;
  };
}

// Default validation rules
const DEFAULT_RULES: ValidationRule[] = [
  {
    id: 'price_range_check',
    name: 'Price Range Validation',
    description: 'Validates that prices are within reasonable ranges',
    severity: 'high',
    enabled: true,
    parameters: {
      maxDailyChangePercent: 20,
      minPrice: 0.001,
      maxPrice: 1000000
    }
  },
  {
    id: 'ohlc_consistency',
    name: 'OHLC Consistency Check',
    description: 'Ensures High >= Open, Close and Low <= Open, Close',
    severity: 'critical',
    enabled: true,
    parameters: {}
  },
  {
    id: 'volume_validation',
    name: 'Volume Validation',
    description: 'Checks for reasonable volume values',
    severity: 'medium',
    enabled: true,
    parameters: {
      minVolume: 0,
      maxVolumeMultiplier: 100 // times average volume
    }
  },
  {
    id: 'timestamp_sequence',
    name: 'Timestamp Sequence Check',
    description: 'Validates chronological order of timestamps',
    severity: 'high',
    enabled: true,
    parameters: {
      allowDuplicates: false,
      maxBackwardJumpMs: 1000
    }
  },
  {
    id: 'gap_detection',
    name: 'Data Gap Detection',
    description: 'Identifies missing data points in time series',
    severity: 'medium',
    enabled: true,
    parameters: {
      maxGapMultiplier: 2 // times expected interval
    }
  },
  {
    id: 'spread_analysis',
    name: 'Bid-Ask Spread Analysis',
    description: 'Analyzes spread reasonableness',
    severity: 'low',
    enabled: true,
    parameters: {
      maxSpreadPercent: 5,
      unusualSpreadMultiplier: 3
    }
  },
  {
    id: 'zero_volume_check',
    name: 'Zero Volume Detection',
    description: 'Flags periods with zero trading volume',
    severity: 'low',
    enabled: true,
    parameters: {
      maxConsecutiveZeroVolume: 5
    }
  },
  {
    id: 'price_spike_detection',
    name: 'Price Spike Detection',
    description: 'Identifies unusual price movements',
    severity: 'medium',
    enabled: true,
    parameters: {
      spikeThresholdStdDev: 3,
      lookbackPeriods: 20
    }
  }
];

export class DataValidator {
  private rules: Map<string, ValidationRule>;
  private statistics = new Map<string, DataStatistics>();
  private validationHistory = new Map<string, ValidationResult[]>();

  constructor(customRules?: ValidationRule[]) {
    this.rules = new Map();
    
    // Load default rules
    DEFAULT_RULES.forEach(rule => this.rules.set(rule.id, rule));
    
    // Override with custom rules
    if (customRules) {
      customRules.forEach(rule => this.rules.set(rule.id, rule));
    }
  }

  /**
   * Validate a single market data point
   */
  validateSingle(dataPoint: MarketDataPoint, previousPoint?: MarketDataPoint): ValidationResult {
    const startTime = Date.now();
    const issues: DataQualityIssue[] = [];
    const appliedRules: string[] = [];

    for (const rule of this.rules.values()) {
      if (!rule.enabled) continue;

      appliedRules.push(rule.id);
      const ruleIssues = this.applyRule(rule, [dataPoint], previousPoint);
      issues.push(...ruleIssues);
    }

    const score = this.calculateScore(issues);
    const processingTimeMs = Date.now() - startTime;

    return {
      isValid: issues.filter(i => i.severity === 'critical' || i.severity === 'high').length === 0,
      score,
      issues,
      appliedRules,
      validationTime: new Date(),
      processingTimeMs
    };
  }

  /**
   * Validate a batch of market data points
   */
  validateBatch(dataPoints: MarketDataPoint[]): ValidationResult {
    const startTime = Date.now();
    const issues: DataQualityIssue[] = [];
    const appliedRules: string[] = [];

    if (dataPoints.length === 0) {
      return {
        isValid: false,
        score: 0,
        issues: [{
          type: 'missing_data',
          severity: 'critical',
          description: 'No data points provided for validation',
          timestamp: new Date(),
          affectedBars: 0,
          suggestion: 'Ensure data source is providing data'
        }],
        appliedRules: [],
        validationTime: new Date(),
        processingTimeMs: Date.now() - startTime
      };
    }

    for (const rule of this.rules.values()) {
      if (!rule.enabled) continue;

      appliedRules.push(rule.id);
      const ruleIssues = this.applyBatchRule(rule, dataPoints);
      issues.push(...ruleIssues);
    }

    const score = this.calculateScore(issues);
    const processingTimeMs = Date.now() - startTime;

    return {
      isValid: issues.filter(i => i.severity === 'critical' || i.severity === 'high').length === 0,
      score,
      issues,
      appliedRules,
      validationTime: new Date(),
      processingTimeMs
    };
  }

  /**
   * Generate comprehensive data quality report
   */
  generateQualityReport(symbol: string, timeframe: string, dataPoints: MarketDataPoint[]): DataQuality {
    if (dataPoints.length === 0) {
      return {
        symbol,
        timeframe,
        completeness: 0,
        timeliness: 0,
        accuracy: 0,
        consistency: 0,
        overallScore: 0,
        issues: [],
        lastChecked: new Date()
      };
    }

    const validation = this.validateBatch(dataPoints);
    const stats = this.calculateStatistics(symbol, timeframe, dataPoints);
    
    // Calculate quality dimensions
    const completeness = this.calculateCompleteness(dataPoints, timeframe);
    const timeliness = this.calculateTimeliness(dataPoints);
    const accuracy = Math.max(0, 100 - (validation.issues.filter(i => i.severity === 'high' || i.severity === 'critical').length * 20));
    const consistency = this.calculateConsistency(dataPoints);
    
    // Weighted overall score
    const overallScore = Math.round(
      (completeness * 0.3) +
      (timeliness * 0.2) +
      (accuracy * 0.3) +
      (consistency * 0.2)
    );

    return {
      symbol,
      timeframe,
      completeness,
      timeliness,
      accuracy,
      consistency,
      overallScore,
      issues: validation.issues,
      lastChecked: new Date()
    };
  }

  /**
   * Calculate data statistics
   */
  calculateStatistics(symbol: string, timeframe: string, dataPoints: MarketDataPoint[]): DataStatistics {
    if (dataPoints.length === 0) {
      throw new Error('Cannot calculate statistics for empty dataset');
    }

    const sortedData = [...dataPoints].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
    const prices = sortedData.map(d => d.close);
    const volumes = sortedData.map(d => d.volume);
    const spreads = sortedData.map(d => ((d.high - d.low) / d.close) * 100);

    // Calculate gaps
    const gaps: number[] = [];
    const expectedInterval = this.getExpectedInterval(timeframe);
    
    for (let i = 1; i < sortedData.length; i++) {
      const timeDiff = sortedData[i].timestamp.getTime() - sortedData[i - 1].timestamp.getTime();
      if (timeDiff > expectedInterval * 1.5) {
        gaps.push(timeDiff);
      }
    }

    // Price statistics
    const priceMin = Math.min(...prices);
    const priceMax = Math.max(...prices);
    const priceStdDev = this.calculateStdDev(prices);

    // Volume statistics
    const volumeAvg = volumes.reduce((sum, v) => sum + v, 0) / volumes.length;
    const volumeMedian = this.calculateMedian(volumes);
    const volumeOutliers = volumes.filter(v => v > volumeAvg * 5 || v === 0).length;

    const stats: DataStatistics = {
      symbol,
      timeframe,
      periodStart: sortedData[0].timestamp,
      periodEnd: sortedData[sortedData.length - 1].timestamp,
      totalBars: sortedData.length,
      missingBars: gaps.length,
      completeness: Math.max(0, 100 - (gaps.length / sortedData.length) * 100),
      averageSpread: spreads.reduce((sum, s) => sum + s, 0) / spreads.length,
      maxSpread: Math.max(...spreads),
      priceRange: {
        min: priceMin,
        max: priceMax,
        volatility: (priceStdDev / (prices.reduce((sum, p) => sum + p, 0) / prices.length)) * 100
      },
      volumeStats: {
        average: volumeAvg,
        median: volumeMedian,
        outliers: volumeOutliers
      },
      gapAnalysis: {
        gapCount: gaps.length,
        maxGapSize: gaps.length > 0 ? Math.max(...gaps) : 0,
        gapPercentage: (gaps.length / sortedData.length) * 100
      }
    };

    this.statistics.set(`${symbol}_${timeframe}`, stats);
    return stats;
  }

  private applyRule(rule: ValidationRule, dataPoints: MarketDataPoint[], previousPoint?: MarketDataPoint): DataQualityIssue[] {
    const issues: DataQualityIssue[] = [];
    const dataPoint = dataPoints[0];

    switch (rule.id) {
      case 'price_range_check':
        const maxChange = rule.parameters.maxDailyChangePercent / 100;
        if (previousPoint) {
          const change = Math.abs(dataPoint.close - previousPoint.close) / previousPoint.close;
          if (change > maxChange) {
            issues.push({
              type: 'invalid_price',
              severity: rule.severity,
              description: `Price change of ${(change * 100).toFixed(2)}% exceeds threshold of ${rule.parameters.maxDailyChangePercent}%`,
              timestamp: dataPoint.timestamp,
              affectedBars: 1,
              suggestion: 'Verify data source and check for corporate actions'
            });
          }
        }
        break;

      case 'ohlc_consistency':
        if (dataPoint.high < Math.max(dataPoint.open, dataPoint.close) ||
            dataPoint.low > Math.min(dataPoint.open, dataPoint.close)) {
          issues.push({
            type: 'invalid_price',
            severity: rule.severity,
            description: 'OHLC values are inconsistent (High < Max(Open,Close) or Low > Min(Open,Close))',
            timestamp: dataPoint.timestamp,
            affectedBars: 1,
            suggestion: 'Check data source for corrupted price data'
          });
        }
        break;

      case 'volume_validation':
        if (dataPoint.volume < 0) {
          issues.push({
            type: 'volume_anomaly',
            severity: rule.severity,
            description: 'Negative volume detected',
            timestamp: dataPoint.timestamp,
            affectedBars: 1,
            suggestion: 'Verify volume data from source'
          });
        }
        break;

      case 'timestamp_sequence':
        if (previousPoint && dataPoint.timestamp <= previousPoint.timestamp) {
          if (!rule.parameters.allowDuplicates || dataPoint.timestamp < previousPoint.timestamp) {
            issues.push({
              type: 'invalid_price',
              severity: rule.severity,
              description: 'Timestamp sequence violation (non-chronological order)',
              timestamp: dataPoint.timestamp,
              affectedBars: 1,
              suggestion: 'Sort data chronologically and remove duplicates'
            });
          }
        }
        break;
    }

    return issues;
  }

  private applyBatchRule(rule: ValidationRule, dataPoints: MarketDataPoint[]): DataQualityIssue[] {
    const issues: DataQualityIssue[] = [];
    const sortedData = [...dataPoints].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

    switch (rule.id) {
      case 'gap_detection':
        const expectedInterval = this.getExpectedInterval('1m'); // Default to 1 minute
        const maxGap = expectedInterval * rule.parameters.maxGapMultiplier;
        
        for (let i = 1; i < sortedData.length; i++) {
          const timeDiff = sortedData[i].timestamp.getTime() - sortedData[i - 1].timestamp.getTime();
          if (timeDiff > maxGap) {
            issues.push({
              type: 'gap_detected',
              severity: rule.severity,
              description: `Data gap of ${Math.round(timeDiff / 60000)} minutes detected`,
              timestamp: sortedData[i - 1].timestamp,
              affectedBars: 1,
              suggestion: 'Fill gaps with interpolated data or mark as missing'
            });
          }
        }
        break;

      case 'zero_volume_check':
        let consecutiveZero = 0;
        for (const point of sortedData) {
          if (point.volume === 0) {
            consecutiveZero++;
            if (consecutiveZero > rule.parameters.maxConsecutiveZeroVolume) {
              issues.push({
                type: 'volume_anomaly',
                severity: rule.severity,
                description: `${consecutiveZero} consecutive bars with zero volume`,
                timestamp: point.timestamp,
                affectedBars: consecutiveZero,
                suggestion: 'Check for market holidays or trading halts'
              });
              consecutiveZero = 0; // Reset to avoid duplicate issues
            }
          } else {
            consecutiveZero = 0;
          }
        }
        break;

      case 'price_spike_detection':
        const lookback = rule.parameters.lookbackPeriods;
        const threshold = rule.parameters.spikeThresholdStdDev;
        
        for (let i = lookback; i < sortedData.length; i++) {
          const window = sortedData.slice(i - lookback, i);
          const prices = window.map(d => d.close);
          const mean = prices.reduce((sum, p) => sum + p, 0) / prices.length;
          const stdDev = this.calculateStdDev(prices);
          
          const currentPrice = sortedData[i].close;
          const zScore = Math.abs(currentPrice - mean) / stdDev;
          
          if (zScore > threshold) {
            issues.push({
              type: 'invalid_price',
              severity: rule.severity,
              description: `Price spike detected: ${zScore.toFixed(2)} standard deviations from mean`,
              timestamp: sortedData[i].timestamp,
              affectedBars: 1,
              suggestion: 'Verify price data and check for news events'
            });
          }
        }
        break;
    }

    return issues;
  }

  private calculateScore(issues: DataQualityIssue[]): number {
    let score = 100;
    
    for (const issue of issues) {
      switch (issue.severity) {
        case 'critical':
          score -= 25;
          break;
        case 'high':
          score -= 15;
          break;
        case 'medium':
          score -= 8;
          break;
        case 'low':
          score -= 3;
          break;
      }
    }
    
    return Math.max(0, Math.min(100, score));
  }

  private calculateCompleteness(dataPoints: MarketDataPoint[], timeframe: string): number {
    if (dataPoints.length === 0) return 0;
    
    const sortedData = [...dataPoints].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
    const startTime = sortedData[0].timestamp;
    const endTime = sortedData[sortedData.length - 1].timestamp;
    const expectedInterval = this.getExpectedInterval(timeframe);
    
    const expectedBars = Math.floor((endTime.getTime() - startTime.getTime()) / expectedInterval) + 1;
    const actualBars = sortedData.length;
    
    return Math.min(100, (actualBars / expectedBars) * 100);
  }

  private calculateTimeliness(dataPoints: MarketDataPoint[]): number {
    if (dataPoints.length === 0) return 0;
    
    const now = Date.now();
    const latestTimestamp = Math.max(...dataPoints.map(d => d.timestamp.getTime()));
    const ageMs = now - latestTimestamp;
    
    // Data is considered "fresh" if less than 5 minutes old
    const freshnessThreshold = 5 * 60 * 1000;
    
    if (ageMs <= freshnessThreshold) {
      return 100;
    } else if (ageMs <= freshnessThreshold * 6) { // 30 minutes
      return Math.max(0, 100 - ((ageMs - freshnessThreshold) / (freshnessThreshold * 5)) * 100);
    } else {
      return 0;
    }
  }

  private calculateConsistency(dataPoints: MarketDataPoint[]): number {
    if (dataPoints.length < 2) return 100;
    
    let consistencyScore = 100;
    const sortedData = [...dataPoints].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
    
    // Check for reasonable price movements
    for (let i = 1; i < sortedData.length; i++) {
      const prevPrice = sortedData[i - 1].close;
      const currentPrice = sortedData[i].close;
      const change = Math.abs(currentPrice - prevPrice) / prevPrice;
      
      if (change > 0.1) { // 10% change
        consistencyScore -= 5;
      }
    }
    
    return Math.max(0, consistencyScore);
  }

  private getExpectedInterval(timeframe: string): number {
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
    
    return intervals[timeframe] || 60000; // Default to 1 minute
  }

  private calculateStdDev(numbers: number[]): number {
    const mean = numbers.reduce((sum, n) => sum + n, 0) / numbers.length;
    const squaredDiffs = numbers.map(n => Math.pow(n - mean, 2));
    const variance = squaredDiffs.reduce((sum, diff) => sum + diff, 0) / numbers.length;
    return Math.sqrt(variance);
  }

  private calculateMedian(numbers: number[]): number {
    const sorted = [...numbers].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
  }

  // Rule management methods
  addRule(rule: ValidationRule): void {
    this.rules.set(rule.id, rule);
  }

  removeRule(ruleId: string): void {
    this.rules.delete(ruleId);
  }

  enableRule(ruleId: string): void {
    const rule = this.rules.get(ruleId);
    if (rule) {
      rule.enabled = true;
    }
  }

  disableRule(ruleId: string): void {
    const rule = this.rules.get(ruleId);
    if (rule) {
      rule.enabled = false;
    }
  }

  getRules(): ValidationRule[] {
    return Array.from(this.rules.values());
  }

  getStatistics(symbol: string, timeframe: string): DataStatistics | undefined {
    return this.statistics.get(`${symbol}_${timeframe}`);
  }

  clearStatistics(): void {
    this.statistics.clear();
  }
}