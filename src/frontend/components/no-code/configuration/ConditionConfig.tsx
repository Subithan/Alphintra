import { NodeConfigFields, NodeConfigResult } from './types';

// Expanded condition options organized by category
const conditionOptions = [
  // Basic Comparison conditions
  { value: 'greater_than', label: 'Greater Than (>)', category: 'comparison', complexity: 'simple' },
  { value: 'less_than', label: 'Less Than (<)', category: 'comparison', complexity: 'simple' },
  { value: 'equal_to', label: 'Equal To (=)', category: 'comparison', complexity: 'simple' },
  { value: 'not_equal', label: 'Not Equal (!=)', category: 'comparison', complexity: 'simple' },
  { value: 'greater_equal', label: 'Greater or Equal (>=)', category: 'comparison', complexity: 'simple' },
  { value: 'less_equal', label: 'Less or Equal (<=)', category: 'comparison', complexity: 'simple' },
  { value: 'range', label: 'Within Range', category: 'comparison', complexity: 'medium' },
  { value: 'outside_range', label: 'Outside Range', category: 'comparison', complexity: 'medium' },
  { value: 'percentage_change', label: 'Percentage Change', category: 'comparison', complexity: 'medium' },
  { value: 'rate_of_change', label: 'Rate of Change', category: 'comparison', complexity: 'medium' },
  { value: 'absolute_change', label: 'Absolute Change', category: 'comparison', complexity: 'simple' },
  { value: 'z_score', label: 'Z-Score', category: 'comparison', complexity: 'advanced' },
  { value: 'percentile_rank', label: 'Percentile Rank', category: 'comparison', complexity: 'advanced' },
  
  // Advanced Statistical Comparisons
  { value: 'moving_average_deviation', label: 'Moving Average Deviation', category: 'comparison', complexity: 'advanced' },
  { value: 'standard_deviation_multiple', label: 'Standard Deviation Multiple', category: 'comparison', complexity: 'advanced' },
  { value: 'bollinger_position', label: 'Bollinger Band Position', category: 'comparison', complexity: 'advanced' },
  { value: 'keltner_position', label: 'Keltner Channel Position', category: 'comparison', complexity: 'advanced' },
  
  // Crossover conditions
  { value: 'crossover', label: 'Crossover Above', category: 'crossover', complexity: 'medium' },
  { value: 'crossunder', label: 'Crossover Below', category: 'crossover', complexity: 'medium' },
  { value: 'golden_cross', label: 'Golden Cross (50/200 MA)', category: 'crossover', complexity: 'medium' },
  { value: 'death_cross', label: 'Death Cross (50/200 MA)', category: 'crossover', complexity: 'medium' },
  { value: 'bullish_divergence', label: 'Bullish Divergence', category: 'crossover', complexity: 'advanced' },
  { value: 'bearish_divergence', label: 'Bearish Divergence', category: 'crossover', complexity: 'advanced' },
  { value: 'macd_signal_cross', label: 'MACD Signal Cross', category: 'crossover', complexity: 'medium' },
  { value: 'rsi_level_cross', label: 'RSI Level Cross', category: 'crossover', complexity: 'medium' },
  { value: 'stoch_level_cross', label: 'Stochastic Level Cross', category: 'crossover', complexity: 'medium' },
  { value: 'cci_level_cross', label: 'CCI Level Cross', category: 'crossover', complexity: 'medium' },
  { value: 'williams_r_cross', label: 'Williams %R Cross', category: 'crossover', complexity: 'medium' },
  
  // Advanced Crossover Patterns
  { value: 'triple_ma_cross', label: 'Triple MA Crossover', category: 'crossover', complexity: 'advanced' },
  { value: 'ichimoku_cross', label: 'Ichimoku Cross', category: 'crossover', complexity: 'advanced' },
  { value: 'price_envelope_cross', label: 'Price Envelope Cross', category: 'crossover', complexity: 'advanced' },
  
  // Trend conditions
  { value: 'rising', label: 'Rising Trend', category: 'trend', complexity: 'simple' },
  { value: 'falling', label: 'Falling Trend', category: 'trend', complexity: 'simple' },
  { value: 'sideways', label: 'Sideways Movement', category: 'trend', complexity: 'medium' },
  { value: 'trend_strength', label: 'Trend Strength', category: 'trend', complexity: 'medium' },
  { value: 'momentum_change', label: 'Momentum Change', category: 'trend', complexity: 'medium' },
  { value: 'adx_trend', label: 'ADX Trend Strength', category: 'trend', complexity: 'medium' },
  { value: 'parabolic_sar', label: 'Parabolic SAR Trend', category: 'trend', complexity: 'medium' },
  { value: 'aroon_trend', label: 'Aroon Trend Signal', category: 'trend', complexity: 'medium' },
  { value: 'linear_regression_slope', label: 'Linear Regression Slope', category: 'trend', complexity: 'advanced' },
  { value: 'polynomial_trend', label: 'Polynomial Trend Fit', category: 'trend', complexity: 'advanced' },
  
  // Advanced Trend Analysis
  { value: 'trend_acceleration', label: 'Trend Acceleration', category: 'trend', complexity: 'advanced' },
  { value: 'trend_exhaustion', label: 'Trend Exhaustion', category: 'trend', complexity: 'advanced' },
  { value: 'elliott_wave_count', label: 'Elliott Wave Count', category: 'trend', complexity: 'expert' },
  { value: 'wyckoff_phase', label: 'Wyckoff Market Phase', category: 'trend', complexity: 'expert' },
  
  // Pattern Recognition conditions
  { value: 'support_level', label: 'At Support Level', category: 'pattern', complexity: 'medium' },
  { value: 'resistance_level', label: 'At Resistance Level', category: 'pattern', complexity: 'medium' },
  { value: 'breakout_up', label: 'Upward Breakout', category: 'pattern', complexity: 'medium' },
  { value: 'breakout_down', label: 'Downward Breakout', category: 'pattern', complexity: 'medium' },
  { value: 'oversold', label: 'Oversold Condition', category: 'pattern', complexity: 'simple' },
  { value: 'overbought', label: 'Overbought Condition', category: 'pattern', complexity: 'simple' },
  { value: 'double_top', label: 'Double Top Pattern', category: 'pattern', complexity: 'advanced' },
  { value: 'double_bottom', label: 'Double Bottom Pattern', category: 'pattern', complexity: 'advanced' },
  { value: 'head_shoulders', label: 'Head & Shoulders', category: 'pattern', complexity: 'advanced' },
  { value: 'inverse_head_shoulders', label: 'Inverse Head & Shoulders', category: 'pattern', complexity: 'advanced' },
  { value: 'triangle_pattern', label: 'Triangle Pattern', category: 'pattern', complexity: 'advanced' },
  { value: 'flag_pattern', label: 'Flag Pattern', category: 'pattern', complexity: 'medium' },
  { value: 'pennant_pattern', label: 'Pennant Pattern', category: 'pattern', complexity: 'medium' },
  { value: 'wedge_pattern', label: 'Wedge Pattern', category: 'pattern', complexity: 'advanced' },
  
  // Candlestick Patterns
  { value: 'hammer', label: 'Hammer Candlestick', category: 'pattern', complexity: 'medium' },
  { value: 'doji', label: 'Doji Pattern', category: 'pattern', complexity: 'medium' },
  { value: 'engulfing_bullish', label: 'Bullish Engulfing', category: 'pattern', complexity: 'medium' },
  { value: 'engulfing_bearish', label: 'Bearish Engulfing', category: 'pattern', complexity: 'medium' },
  { value: 'morning_star', label: 'Morning Star', category: 'pattern', complexity: 'advanced' },
  { value: 'evening_star', label: 'Evening Star', category: 'pattern', complexity: 'advanced' },
  { value: 'three_white_soldiers', label: 'Three White Soldiers', category: 'pattern', complexity: 'advanced' },
  { value: 'three_black_crows', label: 'Three Black Crows', category: 'pattern', complexity: 'advanced' },
  
  // Multi-timeframe conditions
  { value: 'higher_timeframe_trend', label: 'Higher Timeframe Trend', category: 'timeframe', complexity: 'medium' },
  { value: 'multi_tf_alignment', label: 'Multi-TF Alignment', category: 'timeframe', complexity: 'advanced' },
  { value: 'weekly_monthly_bias', label: 'Weekly/Monthly Bias', category: 'timeframe', complexity: 'medium' },
  { value: 'fractal_alignment', label: 'Fractal Time Alignment', category: 'timeframe', complexity: 'expert' },
  { value: 'seasonal_pattern', label: 'Seasonal Pattern', category: 'timeframe', complexity: 'advanced' },
  { value: 'time_cycle_confluence', label: 'Time Cycle Confluence', category: 'timeframe', complexity: 'expert' },
  
  // Volume-based conditions
  { value: 'volume_spike', label: 'Volume Spike', category: 'volume', complexity: 'medium' },
  { value: 'volume_dry_up', label: 'Volume Dry Up', category: 'volume', complexity: 'medium' },
  { value: 'on_balance_volume', label: 'On Balance Volume', category: 'volume', complexity: 'medium' },
  { value: 'accumulation_distribution', label: 'Accumulation/Distribution', category: 'volume', complexity: 'medium' },
  { value: 'money_flow_index', label: 'Money Flow Index', category: 'volume', complexity: 'medium' },
  { value: 'volume_price_trend', label: 'Volume Price Trend', category: 'volume', complexity: 'advanced' },
  { value: 'chaikin_oscillator', label: 'Chaikin Oscillator', category: 'volume', complexity: 'advanced' },
  { value: 'ease_of_movement', label: 'Ease of Movement', category: 'volume', complexity: 'advanced' },
  
  // Market Structure conditions
  { value: 'higher_high', label: 'Higher High Formation', category: 'structure', complexity: 'simple' },
  { value: 'lower_low', label: 'Lower Low Formation', category: 'structure', complexity: 'simple' },
  { value: 'structure_break', label: 'Structure Break', category: 'structure', complexity: 'medium' },
  { value: 'liquidity_sweep', label: 'Liquidity Sweep', category: 'structure', complexity: 'advanced' },
  { value: 'fair_value_gap', label: 'Fair Value Gap', category: 'structure', complexity: 'advanced' },
  { value: 'order_block', label: 'Order Block', category: 'structure', complexity: 'advanced' },
  { value: 'market_maker_move', label: 'Market Maker Move', category: 'structure', complexity: 'expert' },
  
  // Volatility conditions
  { value: 'volatility_expansion', label: 'Volatility Expansion', category: 'volatility', complexity: 'medium' },
  { value: 'volatility_contraction', label: 'Volatility Contraction', category: 'volatility', complexity: 'medium' },
  { value: 'atr_multiple', label: 'ATR Multiple', category: 'volatility', complexity: 'medium' },
  { value: 'vix_level', label: 'VIX Level', category: 'volatility', complexity: 'medium' },
  { value: 'bollinger_squeeze', label: 'Bollinger Squeeze', category: 'volatility', complexity: 'advanced' },
  { value: 'keltner_squeeze', label: 'Keltner Squeeze', category: 'volatility', complexity: 'advanced' },
  
  // Correlation conditions
  { value: 'correlation_strength', label: 'Correlation Strength', category: 'correlation', complexity: 'advanced' },
  { value: 'correlation_divergence', label: 'Correlation Divergence', category: 'correlation', complexity: 'advanced' },
  { value: 'sector_rotation', label: 'Sector Rotation Signal', category: 'correlation', complexity: 'expert' },
  { value: 'market_regime_change', label: 'Market Regime Change', category: 'correlation', complexity: 'expert' }
];

export function getConditionConfig(): NodeConfigResult {
  const fields: NodeConfigFields = {
    conditionType: {
      type: 'select',
      label: 'Condition Category',
      description: 'Category of logical condition',
      options: [
        { value: 'comparison', label: 'Value Comparison' },
        { value: 'crossover', label: 'Crossover Detection' },
        { value: 'trend', label: 'Trend Analysis' },
        { value: 'pattern', label: 'Pattern Recognition' },
        { value: 'timeframe', label: 'Multi-Timeframe' },
        { value: 'volume', label: 'Volume Analysis' },
        { value: 'structure', label: 'Market Structure' },
        { value: 'volatility', label: 'Volatility Analysis' },
        { value: 'correlation', label: 'Correlation Analysis' },
      ],
      default: 'comparison'
    },
    
    complexityLevel: {
      type: 'select',
      label: 'Complexity Level',
      description: 'Filter conditions by complexity',
      options: [
        { value: 'all', label: 'All Levels' },
        { value: 'simple', label: 'Simple' },
        { value: 'medium', label: 'Medium' },
        { value: 'advanced', label: 'Advanced' },
        { value: 'expert', label: 'Expert' },
      ],
      default: 'all'
    },

    condition: {
      type: 'select',
      label: 'Condition Type',
      description: 'Specific condition to evaluate',
      options: conditionOptions,
      default: 'greater_than'
    },

    value: {
      type: 'number',
      label: 'Threshold Value',
      description: 'Primary comparison value',
      default: 0
    },

    value2: {
      type: 'number',
      label: 'Secondary Value',
      description: 'Secondary value for range/comparison conditions',
      default: 100
    },

    lookback: {
      type: 'number',
      label: 'Lookback Period',
      description: 'Number of bars to analyze',
      min: 1,
      max: 200,
      default: 1
    },

    sensitivity: {
      type: 'range',
      label: 'Sensitivity',
      description: 'Detection sensitivity (higher = more sensitive)',
      min: 0.1,
      max: 5.0,
      step: 0.1,
      default: 1.0
    },

    confirmationBars: {
      type: 'number',
      label: 'Confirmation Bars',
      description: 'Number of bars to confirm the condition',
      min: 0,
      max: 20,
      default: 0
    },

    percentageThreshold: {
      type: 'number',
      label: 'Percentage Threshold',
      description: 'Percentage threshold for change detection',
      min: 0.1,
      max: 50,
      step: 0.1,
      default: 5.0
    },

    higherTimeframe: {
      type: 'select',
      label: 'Higher Timeframe',
      description: 'Reference timeframe for multi-TF conditions',
      options: [
        { value: '15m', label: '15 Minutes' },
        { value: '1h', label: '1 Hour' },
        { value: '4h', label: '4 Hours' },
        { value: '1d', label: '1 Day' },
        { value: '1w', label: '1 Week' },
        { value: '1M', label: '1 Month' },
      ],
      default: '1h'
    },

    trendStrength: {
      type: 'select',
      label: 'Trend Strength',
      description: 'Required trend strength level',
      options: [
        { value: 'weak', label: 'Weak Trend' },
        { value: 'moderate', label: 'Moderate Trend' },
        { value: 'strong', label: 'Strong Trend' },
        { value: 'very_strong', label: 'Very Strong Trend' },
      ],
      default: 'moderate'
    },

    divergenceType: {
      type: 'select',
      label: 'Divergence Type',
      description: 'Type of divergence to detect',
      options: [
        { value: 'regular', label: 'Regular Divergence' },
        { value: 'hidden', label: 'Hidden Divergence' },
        { value: 'exaggerated', label: 'Exaggerated Divergence' },
      ],
      default: 'regular'
    },
    
    // Volume-specific fields
    volumeThreshold: {
      type: 'number',
      label: 'Volume Threshold',
      description: 'Volume threshold as multiple of average',
      min: 0.1,
      max: 10.0,
      step: 0.1,
      default: 2.0
    },
    
    volumePeriod: {
      type: 'number',
      label: 'Volume Period',
      description: 'Period for volume average calculation',
      min: 5,
      max: 200,
      default: 20
    },
    
    // Pattern-specific fields
    patternStrength: {
      type: 'select',
      label: 'Pattern Strength',
      description: 'Required pattern strength',
      options: [
        { value: 'weak', label: 'Weak' },
        { value: 'moderate', label: 'Moderate' },
        { value: 'strong', label: 'Strong' },
        { value: 'very_strong', label: 'Very Strong' },
      ],
      default: 'moderate'
    },
    
    patternMinBars: {
      type: 'number',
      label: 'Minimum Pattern Bars',
      description: 'Minimum bars required to form pattern',
      min: 3,
      max: 50,
      default: 10
    },
    
    // Structure-specific fields
    structureLookback: {
      type: 'number',
      label: 'Structure Lookback',
      description: 'Bars to look back for structure analysis',
      min: 10,
      max: 500,
      default: 50
    },
    
    levelSpacing: {
      type: 'number',
      label: 'Level Spacing',
      description: 'Minimum spacing between levels (pips/points)',
      min: 1,
      max: 1000,
      default: 20
    },
    
    // Volatility-specific fields
    volatilityPeriod: {
      type: 'number',
      label: 'Volatility Period',
      description: 'Period for volatility calculation',
      min: 5,
      max: 100,
      default: 20
    },
    
    volatilityMultiplier: {
      type: 'number',
      label: 'Volatility Multiplier',
      description: 'Multiplier for volatility threshold',
      min: 0.5,
      max: 5.0,
      step: 0.1,
      default: 1.5
    },
    
    // Correlation-specific fields
    correlationPeriod: {
      type: 'number',
      label: 'Correlation Period',
      description: 'Period for correlation calculation',
      min: 10,
      max: 200,
      default: 50
    },
    
    correlationThreshold: {
      type: 'number',
      label: 'Correlation Threshold',
      description: 'Minimum correlation coefficient',
      min: -1.0,
      max: 1.0,
      step: 0.1,
      default: 0.7
    },
    
    referenceSymbol: {
      type: 'text',
      label: 'Reference Symbol',
      description: 'Symbol to correlate with',
      default: 'SPY'
    }
  };

  const shouldShowField = (key: string, config: any, params: Record<string, any>) => {
    const condition = params.condition;
    const conditionType = params.conditionType;
    
    switch (key) {
      // Basic fields that depend on condition type
      case 'value2':
        return ['range', 'outside_range'].includes(condition);
      
      case 'confirmationBars':
        return ['crossover', 'crossunder', 'breakout_up', 'breakout_down', 'golden_cross', 'death_cross',
               'macd_signal_cross', 'rsi_level_cross', 'stoch_level_cross', 'structure_break'].includes(condition);
      
      case 'percentageThreshold':
        return ['percentage_change', 'breakout_up', 'breakout_down', 'momentum_change', 
               'trend_acceleration', 'volatility_expansion', 'volatility_contraction'].includes(condition);
      
      case 'higherTimeframe':
        return ['higher_timeframe_trend', 'multi_tf_alignment', 'weekly_monthly_bias',
               'fractal_alignment', 'seasonal_pattern', 'time_cycle_confluence'].includes(condition);
      
      case 'trendStrength':
        return ['trend_strength', 'rising', 'falling', 'higher_timeframe_trend', 'adx_trend',
               'trend_acceleration', 'trend_exhaustion'].includes(condition);
      
      case 'divergenceType':
        return ['bullish_divergence', 'bearish_divergence'].includes(condition);
      
      // Volume-specific fields
      case 'volumeThreshold':
      case 'volumePeriod':
        return conditionType === 'volume' || ['volume_spike', 'volume_dry_up', 'on_balance_volume',
               'accumulation_distribution', 'money_flow_index'].includes(condition);
      
      // Pattern-specific fields
      case 'patternStrength':
      case 'patternMinBars':
        return conditionType === 'pattern' || ['double_top', 'double_bottom', 'head_shoulders',
               'triangle_pattern', 'flag_pattern', 'pennant_pattern', 'wedge_pattern'].includes(condition);
      
      // Structure-specific fields
      case 'structureLookback':
      case 'levelSpacing':
        return conditionType === 'structure' || ['support_level', 'resistance_level', 'structure_break',
               'liquidity_sweep', 'fair_value_gap', 'order_block'].includes(condition);
      
      // Volatility-specific fields
      case 'volatilityPeriod':
      case 'volatilityMultiplier':
        return conditionType === 'volatility' || ['volatility_expansion', 'volatility_contraction',
               'atr_multiple', 'bollinger_squeeze', 'keltner_squeeze'].includes(condition);
      
      // Correlation-specific fields
      case 'correlationPeriod':
      case 'correlationThreshold':
      case 'referenceSymbol':
        return conditionType === 'correlation' || ['correlation_strength', 'correlation_divergence',
               'sector_rotation', 'market_regime_change'].includes(condition);
      
      // Show complexity level filter always
      case 'complexityLevel':
        return true;
      
      default:
        return true;
    }
  };

  return { fields, shouldShowField };
}

export function validateConditionConfig(params: Record<string, any>): string[] {
  const errors: string[] = [];

  // Basic validation
  if (params.condition === 'range' && params.value >= params.value2) {
    errors.push('Upper threshold must be greater than lower threshold');
  }

  if (params.lookback < 1 || params.lookback > 200) {
    errors.push('Lookback period must be between 1 and 200');
  }

  if (params.confirmationBars < 0 || params.confirmationBars > 20) {
    errors.push('Confirmation bars must be between 0 and 20');
  }

  // Volume-specific validation
  if (params.volumeThreshold && (params.volumeThreshold < 0.1 || params.volumeThreshold > 10)) {
    errors.push('Volume threshold must be between 0.1 and 10.0');
  }

  if (params.volumePeriod && (params.volumePeriod < 5 || params.volumePeriod > 200)) {
    errors.push('Volume period must be between 5 and 200');
  }

  // Pattern-specific validation
  if (params.patternMinBars && (params.patternMinBars < 3 || params.patternMinBars > 50)) {
    errors.push('Pattern minimum bars must be between 3 and 50');
  }

  // Structure-specific validation
  if (params.structureLookback && (params.structureLookback < 10 || params.structureLookback > 500)) {
    errors.push('Structure lookback must be between 10 and 500');
  }

  if (params.levelSpacing && (params.levelSpacing < 1 || params.levelSpacing > 1000)) {
    errors.push('Level spacing must be between 1 and 1000');
  }

  // Volatility-specific validation
  if (params.volatilityPeriod && (params.volatilityPeriod < 5 || params.volatilityPeriod > 100)) {
    errors.push('Volatility period must be between 5 and 100');
  }

  if (params.volatilityMultiplier && (params.volatilityMultiplier < 0.5 || params.volatilityMultiplier > 5.0)) {
    errors.push('Volatility multiplier must be between 0.5 and 5.0');
  }

  // Correlation-specific validation
  if (params.correlationPeriod && (params.correlationPeriod < 10 || params.correlationPeriod > 200)) {
    errors.push('Correlation period must be between 10 and 200');
  }

  if (params.correlationThreshold && (params.correlationThreshold < -1.0 || params.correlationThreshold > 1.0)) {
    errors.push('Correlation threshold must be between -1.0 and 1.0');
  }

  if (params.referenceSymbol && !params.referenceSymbol.trim()) {
    errors.push('Reference symbol cannot be empty');
  }

  return errors;
}