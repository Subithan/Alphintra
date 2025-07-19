import { NodeConfigFields, NodeConfigResult } from './types';

// Condition options organized by category
const conditionOptions = [
  // Comparison conditions
  { value: 'greater_than', label: 'Greater Than (>)', category: 'comparison' },
  { value: 'less_than', label: 'Less Than (<)', category: 'comparison' },
  { value: 'equal_to', label: 'Equal To (=)', category: 'comparison' },
  { value: 'not_equal', label: 'Not Equal (!=)', category: 'comparison' },
  { value: 'greater_equal', label: 'Greater or Equal (>=)', category: 'comparison' },
  { value: 'less_equal', label: 'Less or Equal (<=)', category: 'comparison' },
  { value: 'range', label: 'Within Range', category: 'comparison' },
  { value: 'outside_range', label: 'Outside Range', category: 'comparison' },
  { value: 'percentage_change', label: 'Percentage Change', category: 'comparison' },
  
  // Crossover conditions
  { value: 'crossover', label: 'Crossover Above', category: 'crossover' },
  { value: 'crossunder', label: 'Crossover Below', category: 'crossover' },
  { value: 'golden_cross', label: 'Golden Cross (50/200 MA)', category: 'crossover' },
  { value: 'death_cross', label: 'Death Cross (50/200 MA)', category: 'crossover' },
  { value: 'bullish_divergence', label: 'Bullish Divergence', category: 'crossover' },
  { value: 'bearish_divergence', label: 'Bearish Divergence', category: 'crossover' },
  
  // Trend conditions
  { value: 'rising', label: 'Rising Trend', category: 'trend' },
  { value: 'falling', label: 'Falling Trend', category: 'trend' },
  { value: 'sideways', label: 'Sideways Movement', category: 'trend' },
  { value: 'trend_strength', label: 'Trend Strength', category: 'trend' },
  { value: 'momentum_change', label: 'Momentum Change', category: 'trend' },
  
  // Pattern conditions
  { value: 'support_level', label: 'At Support Level', category: 'pattern' },
  { value: 'resistance_level', label: 'At Resistance Level', category: 'pattern' },
  { value: 'breakout_up', label: 'Upward Breakout', category: 'pattern' },
  { value: 'breakout_down', label: 'Downward Breakout', category: 'pattern' },
  { value: 'oversold', label: 'Oversold Condition', category: 'pattern' },
  { value: 'overbought', label: 'Overbought Condition', category: 'pattern' },
  
  // Multi-timeframe conditions
  { value: 'higher_timeframe_trend', label: 'Higher Timeframe Trend', category: 'timeframe' },
  { value: 'multi_tf_alignment', label: 'Multi-TF Alignment', category: 'timeframe' },
  { value: 'weekly_monthly_bias', label: 'Weekly/Monthly Bias', category: 'timeframe' }
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
      ],
      default: 'comparison'
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
    }
  };

  const shouldShowField = (key: string, config: any, params: Record<string, any>) => {
    switch (key) {
      case 'value2':
        return ['range', 'outside_range'].includes(params.condition);
      
      case 'confirmationBars':
        return ['crossover', 'crossunder', 'breakout_up', 'breakout_down', 'golden_cross', 'death_cross'].includes(params.condition);
      
      case 'percentageThreshold':
        return ['percentage_change', 'breakout_up', 'breakout_down', 'momentum_change'].includes(params.condition);
      
      case 'higherTimeframe':
        return ['higher_timeframe_trend', 'multi_tf_alignment', 'weekly_monthly_bias'].includes(params.condition);
      
      case 'trendStrength':
        return ['trend_strength', 'rising', 'falling', 'higher_timeframe_trend'].includes(params.condition);
      
      case 'divergenceType':
        return ['bullish_divergence', 'bearish_divergence'].includes(params.condition);
      
      default:
        return true;
    }
  };

  return { fields, shouldShowField };
}

export function validateConditionConfig(params: Record<string, any>): string[] {
  const errors: string[] = [];

  if (params.condition === 'range' && params.value >= params.value2) {
    errors.push('Upper threshold must be greater than lower threshold');
  }

  if (params.lookback < 1 || params.lookback > 200) {
    errors.push('Lookback period must be between 1 and 200');
  }

  if (params.confirmationBars < 0 || params.confirmationBars > 20) {
    errors.push('Confirmation bars must be between 0 and 20');
  }

  return errors;
}