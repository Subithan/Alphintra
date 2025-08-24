import { NodeConfigFields, NodeConfigResult } from './types';
import { commonFields } from './commonFields';

// Technical indicator options organized by category
const indicatorOptions = [
  // Trend Indicators
  { value: 'SMA', label: 'Simple Moving Average', category: 'trend' },
  { value: 'EMA', label: 'Exponential Moving Average', category: 'trend' },
  { value: 'WMA', label: 'Weighted Moving Average', category: 'trend' },
  { value: 'VWMA', label: 'Volume Weighted Moving Average', category: 'trend' },
  { value: 'HMA', label: 'Hull Moving Average', category: 'trend' },
  { value: 'DEMA', label: 'Double Exponential Moving Average', category: 'trend' },
  { value: 'TEMA', label: 'Triple Exponential Moving Average', category: 'trend' },
  { value: 'ZLEMA', label: 'Zero Lag Exponential Moving Average', category: 'trend' },
  { value: 'ALMA', label: 'Arnaud Legoux Moving Average', category: 'trend' },
  { value: 'KAMA', label: 'Kaufman Adaptive Moving Average', category: 'trend' },
  { value: 'MAMA', label: 'MESA Adaptive Moving Average', category: 'trend' },
  { value: 'T3', label: 'T3 Moving Average', category: 'trend' },
  { value: 'FRAMA', label: 'Fractal Adaptive Moving Average', category: 'trend' },
  { value: 'TRIMA', label: 'Triangular Moving Average', category: 'trend' },
  { value: 'VIDYA', label: 'Variable Index Dynamic Average', category: 'trend' },
  
  // Momentum Indicators
  { value: 'RSI', label: 'Relative Strength Index', category: 'momentum' },
  { value: 'STOCH', label: 'Stochastic Oscillator', category: 'momentum' },
  { value: 'STOCHRSI', label: 'Stochastic RSI', category: 'momentum' },
  { value: 'WILLIAMS', label: 'Williams %R', category: 'momentum' },
  { value: 'CCI', label: 'Commodity Channel Index', category: 'momentum' },
  { value: 'ROC', label: 'Rate of Change', category: 'momentum' },
  { value: 'MOM', label: 'Momentum', category: 'momentum' },
  { value: 'TSI', label: 'True Strength Index', category: 'momentum' },
  { value: 'UO', label: 'Ultimate Oscillator', category: 'momentum' },
  { value: 'PPO', label: 'Percentage Price Oscillator', category: 'momentum' },
  { value: 'PMO', label: 'Price Momentum Oscillator', category: 'momentum' },
  { value: 'QQE', label: 'Quantitative Qualitative Estimation', category: 'momentum' },
  { value: 'RMI', label: 'Relative Momentum Index', category: 'momentum' },
  { value: 'IFT_RSI', label: 'Inverse Fisher Transform RSI', category: 'momentum' },
  { value: 'LSMA', label: 'Least Squares Moving Average', category: 'momentum' },
  
  // Volatility Indicators
  { value: 'BB', label: 'Bollinger Bands', category: 'volatility' },
  { value: 'ATR', label: 'Average True Range', category: 'volatility' },
  { value: 'KC', label: 'Keltner Channels', category: 'volatility' },
  { value: 'DC', label: 'Donchian Channels', category: 'volatility' },
  { value: 'STDDEV', label: 'Standard Deviation', category: 'volatility' },
  { value: 'VAR', label: 'Variance', category: 'volatility' },
  { value: 'NATR', label: 'Normalized Average True Range', category: 'volatility' },
  { value: 'TRANGE', label: 'True Range', category: 'volatility' },
  { value: 'BBWIDTH', label: 'Bollinger Band Width', category: 'volatility' },
  { value: 'SQUEEZE', label: 'Squeeze Momentum', category: 'volatility' },
  { value: 'UI', label: 'Ulcer Index', category: 'volatility' },
  { value: 'THERMO', label: 'Ehlers Thermal Index', category: 'volatility' },
  { value: 'CHOP', label: 'Choppiness Index', category: 'volatility' },
  
  // Volume Indicators
  { value: 'OBV', label: 'On Balance Volume', category: 'volume' },
  { value: 'VWAP', label: 'Volume Weighted Average Price', category: 'volume' },
  { value: 'AD', label: 'Accumulation/Distribution', category: 'volume' },
  { value: 'CMF', label: 'Chaikin Money Flow', category: 'volume' },
  { value: 'EMV', label: 'Ease of Movement', category: 'volume' },
  { value: 'FI', label: 'Force Index', category: 'volume' },
  { value: 'NVI', label: 'Negative Volume Index', category: 'volume' },
  { value: 'PVI', label: 'Positive Volume Index', category: 'volume' },
  { value: 'PVT', label: 'Price Volume Trend', category: 'volume' },
  { value: 'VROC', label: 'Volume Rate of Change', category: 'volume' },
  { value: 'MFI', label: 'Money Flow Index', category: 'volume' },
  { value: 'VORTEX', label: 'Vortex Indicator', category: 'volume' },
  { value: 'KVO', label: 'Klinger Volume Oscillator', category: 'volume' },
  
  // Oscillators
  { value: 'MACD', label: 'MACD', category: 'oscillators' },
  { value: 'AO', label: 'Awesome Oscillator', category: 'oscillators' },
  { value: 'AC', label: 'Accelerator Oscillator', category: 'oscillators' },
  { value: 'AROON', label: 'Aroon Oscillator', category: 'oscillators' },
  { value: 'BOP', label: 'Balance of Power', category: 'oscillators' },
  { value: 'FISHER', label: 'Fisher Transform', category: 'oscillators' },
  { value: 'INERTIA', label: 'Inertia', category: 'oscillators' },
  { value: 'KDJ', label: 'KDJ', category: 'oscillators' },
  { value: 'PSAR', label: 'Parabolic SAR', category: 'oscillators' },
  { value: 'ADX', label: 'Average Directional Index', category: 'oscillators' },
  { value: 'DMI', label: 'Directional Movement Index', category: 'oscillators' },
  { value: 'DPO', label: 'Detrended Price Oscillator', category: 'oscillators' }
];

export function getTechnicalIndicatorConfig(): NodeConfigResult {
  const fields: NodeConfigFields = {
    indicatorCategory: {
      type: 'select',
      label: 'Indicator Category',
      description: 'Select the category of technical indicator',
      options: [
        { value: 'trend', label: 'Trend Indicators' },
        { value: 'momentum', label: 'Momentum Indicators' },
        { value: 'volatility', label: 'Volatility Indicators' },
        { value: 'volume', label: 'Volume Indicators' },
        { value: 'oscillators', label: 'Oscillators' },
      ],
      default: 'trend'
    },

    indicator: {
      type: 'select',
      label: 'Indicator Type',
      description: 'Select the technical indicator to calculate',
      options: indicatorOptions,
      default: 'SMA'
    },

    period: commonFields.period,
    source: commonFields.source,
    smoothing: commonFields.smoothing,

    multiplier: {
      type: 'number',
      label: 'Multiplier',
      description: 'Multiplier for indicators like Bollinger Bands',
      min: 0.1,
      max: 5.0,
      step: 0.1,
      default: 2.0
    },

    fastPeriod: {
      type: 'number',
      label: 'Fast Period',
      description: 'Fast period for MACD and other dual-period indicators',
      min: 1,
      max: 100,
      default: 12
    },

    slowPeriod: {
      type: 'number',
      label: 'Slow Period',
      description: 'Slow period for MACD and other dual-period indicators',
      min: 1,
      max: 200,
      default: 26
    },

    signalPeriod: {
      type: 'number',
      label: 'Signal Period',
      description: 'Signal line period for MACD',
      min: 1,
      max: 50,
      default: 9
    },

    kPeriod: {
      type: 'number',
      label: '%K Period',
      description: 'Stochastic %K period',
      min: 1,
      max: 100,
      default: 14
    },

    dPeriod: {
      type: 'number',
      label: '%D Period',
      description: 'Stochastic %D period',
      min: 1,
      max: 50,
      default: 3
    },

    slowing: {
      type: 'number',
      label: 'Slowing',
      description: 'Stochastic slowing factor',
      min: 1,
      max: 10,
      default: 3
    },

    acceleration: {
      type: 'number',
      label: 'Acceleration',
      description: 'Parabolic SAR acceleration factor',
      min: 0.01,
      max: 1.0,
      step: 0.01,
      default: 0.02
    },

    maximum: {
      type: 'number',
      label: 'Maximum',
      description: 'Parabolic SAR maximum value',
      min: 0.1,
      max: 1.0,
      step: 0.01,
      default: 0.2
    },

    outputType: {
      type: 'select',
      label: 'Output Type',
      description: 'Which output to use for multi-output indicators',
      options: [
        { value: 'main', label: 'Main Line' },
        { value: 'signal', label: 'Signal Line' },
        { value: 'histogram', label: 'Histogram' },
        { value: 'upper', label: 'Upper Band' },
        { value: 'lower', label: 'Lower Band' },
        { value: 'middle', label: 'Middle Line' },
      ],
      default: 'main'
    }
  };

  const shouldShowField = (key: string, config: any, params: Record<string, any>) => {
    // Indicator-specific field visibility
    switch (key) {
      case 'multiplier':
        return ['BB', 'KC', 'SQUEEZE'].includes(params.indicator);
      
      case 'smoothing':
        return ['EMA', 'DEMA', 'TEMA', 'ZLEMA', 'ALMA', 'KAMA', 'MAMA', 'T3', 'FRAMA', 'VIDYA', 'MACD'].includes(params.indicator);
      
      case 'fastPeriod':
      case 'slowPeriod':
        return ['MACD', 'PPO', 'AROON', 'STOCHRSI', 'TSI'].includes(params.indicator);
      
      case 'signalPeriod':
        return ['MACD', 'PPO', 'TSI'].includes(params.indicator);
      
      case 'kPeriod':
      case 'dPeriod':
      case 'slowing':
        return ['STOCH', 'STOCHRSI', 'KDJ'].includes(params.indicator);
      
      case 'acceleration':
      case 'maximum':
        return params.indicator === 'PSAR';
      
      case 'outputType':
        return ['MACD', 'BB', 'KC', 'DC', 'STOCH', 'AROON', 'DMI'].includes(params.indicator);
      
      default:
        return true;
    }
  };

  return { fields, shouldShowField };
}

export function validateTechnicalIndicatorConfig(params: Record<string, any>): string[] {
  const errors: string[] = [];

  if (params.period < 1 || params.period > 200) {
    errors.push('Period must be between 1 and 200');
  }

  if (params.fastPeriod && params.slowPeriod && params.fastPeriod >= params.slowPeriod) {
    errors.push('Fast period must be less than slow period');
  }

  if (params.multiplier && (params.multiplier < 0.1 || params.multiplier > 5.0)) {
    errors.push('Multiplier must be between 0.1 and 5.0');
  }

  return errors;
}