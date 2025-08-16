import { Node, Edge } from 'reactflow';
import { MarketData, ExecutionResult, SignalResult } from './execution-engine';
import { RealTimeExecutionEngine } from './execution-engine';

export interface TimeframeConfig {
  primary: string; // Main timeframe for execution
  secondary: string[]; // Additional timeframes for analysis
  alignment: 'strict' | 'loose'; // How strictly to align timeframes
  lookback_bars: number; // How many bars to maintain for each timeframe
}

export interface MultiTimeframeData {
  timeframe: string;
  data: MarketData[];
  last_updated: Date;
  alignment_offset: number; // Offset in minutes for alignment
}

export interface CrossTimeframeSignal extends SignalResult {
  primary_timeframe: string;
  contributing_timeframes: string[];
  timeframe_alignment: {
    [timeframe: string]: {
      signal_strength: number;
      confidence: number;
      trend_direction: 'bullish' | 'bearish' | 'neutral';
    };
  };
}

export interface MultiTimeframeExecutionResult extends ExecutionResult {
  timeframe_data: {
    [timeframe: string]: {
      bars_processed: number;
      indicators_calculated: number;
      signal_generated: boolean;
      execution_time_ms: number;
    };
  };
  cross_timeframe_signals: CrossTimeframeSignal[];
  alignment_quality: number; // 0-1, how well timeframes are aligned
}

export class MultiTimeframeEngine {
  private config: TimeframeConfig;
  private nodes: Node[];
  private edges: Edge[];
  private timeframeData: Map<string, MultiTimeframeData> = new Map();
  private executionEngines: Map<string, RealTimeExecutionEngine> = new Map();
  private alignmentBuffer: Map<string, MarketData[]> = new Map();
  private lastExecution: Date = new Date(0);

  constructor(config: TimeframeConfig, nodes: Node[], edges: Edge[]) {
    this.config = config;
    this.nodes = nodes;
    this.edges = edges;
    this.initializeTimeframes();
  }

  private initializeTimeframes(): void {
    const allTimeframes = [this.config.primary, ...this.config.secondary];
    
    allTimeframes.forEach(timeframe => {
      // Initialize data storage for each timeframe
      this.timeframeData.set(timeframe, {
        timeframe,
        data: [],
        last_updated: new Date(0),
        alignment_offset: this.calculateAlignmentOffset(timeframe)
      });

      // Create execution engine for each timeframe
      const engine = new RealTimeExecutionEngine(
        {
          strategy_id: `multi_tf_${timeframe}`,
          symbol: this.getSymbolFromNodes(),
          timeframe,
          live_trading: false,
          paper_trading: false,
          risk_management: {
            max_position_size: 1,
            max_drawdown: 0.2,
            stop_loss_enabled: true,
            take_profit_enabled: true
          },
          execution_mode: 'backtest'
        },
        this.nodes,
        this.edges
      );

      this.executionEngines.set(timeframe, engine);
      this.alignmentBuffer.set(timeframe, []);
    });

    console.log(`Multi-timeframe engine initialized for ${allTimeframes.length} timeframes`);
  }

  private getSymbolFromNodes(): string {
    const dataSourceNode = this.nodes.find(n => n.type === 'dataSource');
    return dataSourceNode?.data?.parameters?.symbol || 'AAPL';
  }

  private calculateAlignmentOffset(timeframe: string): number {
    // Calculate minutes offset for timeframe alignment
    const timeframeMinutes: Record<string, number> = {
      '1m': 1,
      '5m': 5,
      '15m': 15,
      '30m': 30,
      '1h': 60,
      '4h': 240,
      '1d': 1440,
      '1w': 10080
    };

    return timeframeMinutes[timeframe] || 60;
  }

  public async updateTimeframeData(timeframe: string, newData: MarketData[]): Promise<void> {
    const timeframeInfo = this.timeframeData.get(timeframe);
    if (!timeframeInfo) {
      console.warn(`Timeframe ${timeframe} not configured`);
      return;
    }

    // Add new data to timeframe buffer
    timeframeInfo.data.push(...newData);
    timeframeInfo.last_updated = new Date();

    // Maintain lookback limit
    if (timeframeInfo.data.length > this.config.lookback_bars) {
      timeframeInfo.data = timeframeInfo.data.slice(-this.config.lookback_bars);
    }

    // Update alignment buffer for cross-timeframe analysis
    const alignmentBuffer = this.alignmentBuffer.get(timeframe) || [];
    alignmentBuffer.push(...newData);
    
    // Keep only recent data in alignment buffer
    const maxBufferSize = Math.max(100, this.config.lookback_bars);
    if (alignmentBuffer.length > maxBufferSize) {
      this.alignmentBuffer.set(timeframe, alignmentBuffer.slice(-maxBufferSize));
    } else {
      this.alignmentBuffer.set(timeframe, alignmentBuffer);
    }

    console.log(`Updated ${timeframe} data: ${timeframeInfo.data.length} bars`);
  }

  public async executeMultiTimeframeStrategy(): Promise<MultiTimeframeExecutionResult> {
    const startTime = performance.now();
    const executionId = `multi_tf_${Date.now()}`;

    try {
      // Step 1: Execute strategy on each timeframe
      const timeframeResults = await this.executeAllTimeframes();
      
      // Step 2: Analyze cross-timeframe alignment
      const alignmentQuality = this.calculateTimeframeAlignment();
      
      // Step 3: Generate cross-timeframe signals
      const crossTimeframeSignals = await this.generateCrossTimeframeSignals(timeframeResults);
      
      // Step 4: Combine signals from primary timeframe with cross-timeframe analysis
      const finalSignals = this.combineTimeframeSignals(timeframeResults, crossTimeframeSignals);

      const executionTime = performance.now() - startTime;

      const result: MultiTimeframeExecutionResult = {
        execution_id: executionId,
        timestamp: new Date(),
        signals: finalSignals,
        performance_metrics: {
          execution_time_ms: Math.round(executionTime),
          memory_usage_mb: this.calculateMemoryUsage(),
          indicator_calculations: this.calculateTotalIndicators(),
          condition_evaluations: this.calculateTotalConditions(),
          logic_operations: this.calculateTotalLogicOps()
        },
        errors: [],
        warnings: [],
        timeframe_data: this.buildTimeframeMetrics(timeframeResults),
        cross_timeframe_signals: crossTimeframeSignals,
        alignment_quality: alignmentQuality
      };

      return result;

    } catch (error) {
      console.error('Multi-timeframe execution error:', error);
      return {
        execution_id: executionId,
        timestamp: new Date(),
        signals: [],
        performance_metrics: {
          execution_time_ms: Math.round(performance.now() - startTime),
          memory_usage_mb: 0,
          indicator_calculations: 0,
          condition_evaluations: 0,
          logic_operations: 0
        },
        errors: [error instanceof Error ? error.message : 'Unknown error'],
        warnings: [],
        timeframe_data: {},
        cross_timeframe_signals: [],
        alignment_quality: 0
      };
    }
  }

  private async executeAllTimeframes(): Promise<Map<string, ExecutionResult>> {
    const results = new Map<string, ExecutionResult>();
    const allTimeframes = [this.config.primary, ...this.config.secondary];

    // Execute in parallel for performance
    const executionPromises = allTimeframes.map(async (timeframe) => {
      const engine = this.executionEngines.get(timeframe);
      const data = this.timeframeData.get(timeframe)?.data || [];

      if (!engine || data.length === 0) {
        console.warn(`No engine or data for timeframe ${timeframe}`);
        return [timeframe, null] as const;
      }

      try {
        const result = await engine.executeStrategy(data);
        return [timeframe, result] as const;
      } catch (error) {
        console.error(`Error executing ${timeframe}:`, error);
        return [timeframe, null] as const;
      }
    });

    const executionResults = await Promise.all(executionPromises);
    
    executionResults.forEach(([timeframe, result]) => {
      if (result) {
        results.set(timeframe, result);
      }
    });

    return results;
  }

  private calculateTimeframeAlignment(): number {
    const allTimeframes = [this.config.primary, ...this.config.secondary];
    let alignmentScore = 0;
    let comparisons = 0;

    // Compare timestamp alignment between timeframes
    for (let i = 0; i < allTimeframes.length; i++) {
      for (let j = i + 1; j < allTimeframes.length; j++) {
        const tf1Data = this.timeframeData.get(allTimeframes[i])?.data || [];
        const tf2Data = this.timeframeData.get(allTimeframes[j])?.data || [];

        if (tf1Data.length > 0 && tf2Data.length > 0) {
          const lastTimestamp1 = tf1Data[tf1Data.length - 1].timestamp.getTime();
          const lastTimestamp2 = tf2Data[tf2Data.length - 1].timestamp.getTime();
          
          // Calculate alignment based on timestamp difference
          const timeDiff = Math.abs(lastTimestamp1 - lastTimestamp2);
          const maxAcceptableDiff = 5 * 60 * 1000; // 5 minutes
          
          const alignment = Math.max(0, 1 - (timeDiff / maxAcceptableDiff));
          alignmentScore += alignment;
          comparisons++;
        }
      }
    }

    return comparisons > 0 ? alignmentScore / comparisons : 0;
  }

  private async generateCrossTimeframeSignals(
    timeframeResults: Map<string, ExecutionResult>
  ): Promise<CrossTimeframeSignal[]> {
    const crossSignals: CrossTimeframeSignal[] = [];
    const primaryResult = timeframeResults.get(this.config.primary);

    if (!primaryResult || primaryResult.signals.length === 0) {
      return crossSignals;
    }

    // Analyze each primary signal against secondary timeframes
    for (const primarySignal of primaryResult.signals) {
      const timeframeAlignment: CrossTimeframeSignal['timeframe_alignment'] = {};
      const contributingTimeframes: string[] = [this.config.primary];

      // Analyze secondary timeframes
      for (const secondaryTf of this.config.secondary) {
        const secondaryResult = timeframeResults.get(secondaryTf);
        if (!secondaryResult) continue;

        const analysis = this.analyzeTimeframeContribution(
          primarySignal,
          secondaryResult,
          secondaryTf
        );

        timeframeAlignment[secondaryTf] = analysis;

        // If secondary timeframe has strong signal, add to contributing
        if (analysis.signal_strength > 0.6) {
          contributingTimeframes.push(secondaryTf);
        }
      }

      // Create cross-timeframe signal
      const crossSignal: CrossTimeframeSignal = {
        ...primarySignal,
        signal_id: `cross_tf_${primarySignal.signal_id}`,
        primary_timeframe: this.config.primary,
        contributing_timeframes: contributingTimeframes,
        timeframe_alignment: timeframeAlignment,
        confidence: this.calculateCrossTimeframeConfidence(timeframeAlignment)
      };

      crossSignals.push(crossSignal);
    }

    return crossSignals;
  }

  private analyzeTimeframeContribution(
    primarySignal: SignalResult,
    secondaryResult: ExecutionResult,
    timeframe: string
  ): {
    signal_strength: number;
    confidence: number;
    trend_direction: 'bullish' | 'bearish' | 'neutral';
  } {
    let signalStrength = 0;
    let confidence = 0;
    let trendDirection: 'bullish' | 'bearish' | 'neutral' = 'neutral';

    // Analyze secondary timeframe signals
    const recentSignals = secondaryResult.signals.filter(
      signal => Math.abs(signal.timestamp.getTime() - primarySignal.timestamp.getTime()) < 3600000 // 1 hour
    );

    if (recentSignals.length > 0) {
      // Calculate signal strength based on consistency
      const bullishSignals = recentSignals.filter(s => s.action === 'buy').length;
      const bearishSignals = recentSignals.filter(s => s.action === 'sell').length;
      const totalSignals = recentSignals.length;

      if (bullishSignals > bearishSignals) {
        trendDirection = 'bullish';
        signalStrength = bullishSignals / totalSignals;
      } else if (bearishSignals > bullishSignals) {
        trendDirection = 'bearish';
        signalStrength = bearishSignals / totalSignals;
      } else {
        trendDirection = 'neutral';
        signalStrength = 0.5;
      }

      // Calculate confidence based on signal frequency and alignment
      confidence = Math.min(1.0, totalSignals / 10); // Max confidence at 10+ signals
      
      // Boost confidence if directions align
      if (
        (primarySignal.action === 'buy' && trendDirection === 'bullish') ||
        (primarySignal.action === 'sell' && trendDirection === 'bearish')
      ) {
        confidence *= 1.2;
        signalStrength *= 1.1;
      }
    }

    return {
      signal_strength: Math.min(1.0, signalStrength),
      confidence: Math.min(1.0, confidence),
      trend_direction: trendDirection
    };
  }

  private calculateCrossTimeframeConfidence(
    alignment: CrossTimeframeSignal['timeframe_alignment']
  ): number {
    const alignmentValues = Object.values(alignment);
    if (alignmentValues.length === 0) return 0.5;

    const avgConfidence = alignmentValues.reduce((sum, a) => sum + a.confidence, 0) / alignmentValues.length;
    const avgStrength = alignmentValues.reduce((sum, a) => sum + a.signal_strength, 0) / alignmentValues.length;

    return Math.min(1.0, (avgConfidence + avgStrength) / 2);
  }

  private combineTimeframeSignals(
    timeframeResults: Map<string, ExecutionResult>,
    crossSignals: CrossTimeframeSignal[]
  ): SignalResult[] {
    const combinedSignals: SignalResult[] = [];
    const primaryResult = timeframeResults.get(this.config.primary);

    // Start with primary timeframe signals
    if (primaryResult) {
      combinedSignals.push(...primaryResult.signals);
    }

    // Add cross-timeframe signals with high confidence
    const highConfidenceCrossSignals = crossSignals.filter(signal => 
      signal.confidence > 0.7 && signal.contributing_timeframes.length >= 2
    );

    combinedSignals.push(...highConfidenceCrossSignals);

    // Remove duplicate signals (same symbol, similar timestamp, same action)
    const uniqueSignals = this.deduplicateSignals(combinedSignals);

    return uniqueSignals;
  }

  private deduplicateSignals(signals: SignalResult[]): SignalResult[] {
    const unique: SignalResult[] = [];
    const seen = new Set<string>();

    signals.forEach(signal => {
      const key = `${signal.symbol}_${signal.action}_${Math.floor(signal.timestamp.getTime() / 300000)}`; // 5-minute buckets
      
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(signal);
      }
    });

    return unique;
  }

  private buildTimeframeMetrics(
    timeframeResults: Map<string, ExecutionResult>
  ): MultiTimeframeExecutionResult['timeframe_data'] {
    const metrics: MultiTimeframeExecutionResult['timeframe_data'] = {};

    timeframeResults.forEach((result, timeframe) => {
      const data = this.timeframeData.get(timeframe);
      
      metrics[timeframe] = {
        bars_processed: data?.data.length || 0,
        indicators_calculated: result.performance_metrics.indicator_calculations,
        signal_generated: result.signals.length > 0,
        execution_time_ms: result.performance_metrics.execution_time_ms
      };
    });

    return metrics;
  }

  private calculateMemoryUsage(): number {
    let totalMemory = 0;
    
    this.timeframeData.forEach(data => {
      totalMemory += data.data.length * 0.1; // Estimate 0.1 MB per bar
    });

    this.alignmentBuffer.forEach(buffer => {
      totalMemory += buffer.length * 0.05; // Smaller memory for buffer
    });

    return Math.round(totalMemory * 10) / 10;
  }

  private calculateTotalIndicators(): number {
    return this.nodes.filter(n => n.type === 'technicalIndicator').length * 
           (1 + this.config.secondary.length); // Primary + secondary timeframes
  }

  private calculateTotalConditions(): number {
    return this.nodes.filter(n => n.type === 'condition').length *
           (1 + this.config.secondary.length);
  }

  private calculateTotalLogicOps(): number {
    return this.nodes.filter(n => n.type === 'logic').length *
           (1 + this.config.secondary.length);
  }

  public getTimeframeData(timeframe: string): MarketData[] {
    return this.timeframeData.get(timeframe)?.data || [];
  }

  public getAlignmentQuality(): number {
    return this.calculateTimeframeAlignment();
  }

  public clearTimeframeData(timeframe?: string): void {
    if (timeframe) {
      this.timeframeData.get(timeframe)?.data.splice(0);
      this.alignmentBuffer.get(timeframe)?.splice(0);
    } else {
      this.timeframeData.forEach(data => data.data.splice(0));
      this.alignmentBuffer.forEach(buffer => buffer.splice(0));
    }
  }
}

// Export function for creating multi-timeframe engine
export const createMultiTimeframeEngine = (
  config: TimeframeConfig,
  nodes: Node[],
  edges: Edge[]
): MultiTimeframeEngine => {
  return new MultiTimeframeEngine(config, nodes, edges);
};

// Utility functions for timeframe conversion
export const timeframeToMinutes = (timeframe: string): number => {
  const mapping: Record<string, number> = {
    '1m': 1,
    '5m': 5,
    '15m': 15,
    '30m': 30,
    '1h': 60,
    '4h': 240,
    '1d': 1440,
    '1w': 10080
  };
  return mapping[timeframe] || 60;
};

export const alignTimeframes = (
  higherTfData: MarketData[],
  lowerTfData: MarketData[],
  higherTf: string,
  lowerTf: string
): { aligned: MarketData[]; quality: number } => {
  const higherMinutes = timeframeToMinutes(higherTf);
  const lowerMinutes = timeframeToMinutes(lowerTf);
  
  if (higherMinutes <= lowerMinutes) {
    return { aligned: higherTfData, quality: 1.0 };
  }

  const ratio = higherMinutes / lowerMinutes;
  const aligned: MarketData[] = [];
  let qualityScore = 0;
  let alignedBars = 0;

  higherTfData.forEach(higherBar => {
    const startTime = higherBar.timestamp.getTime();
    const endTime = startTime + (higherMinutes * 60 * 1000);

    const correspondingBars = lowerTfData.filter(bar => 
      bar.timestamp.getTime() >= startTime && bar.timestamp.getTime() < endTime
    );

    if (correspondingBars.length > 0) {
      // Use the last bar from the corresponding period
      const alignedBar = correspondingBars[correspondingBars.length - 1];
      aligned.push(alignedBar);
      
      // Quality based on how many lower timeframe bars we found vs expected
      const expectedBars = ratio;
      const actualBars = correspondingBars.length;
      qualityScore += Math.min(1.0, actualBars / expectedBars);
      alignedBars++;
    }
  });

  const overallQuality = alignedBars > 0 ? qualityScore / alignedBars : 0;
  
  return {
    aligned,
    quality: overallQuality
  };
};