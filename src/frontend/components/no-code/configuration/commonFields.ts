import { CommonFields, ConfigFieldOption } from './types';

// Common field definitions that are reused across multiple node types
export const commonFields: CommonFields = {
  period: {
    type: 'number',
    label: 'Period',
    description: 'Number of periods for calculation',
    min: 1,
    max: 200,
    default: 20
  },

  source: {
    type: 'select',
    label: 'Price Source',
    description: 'Which price to use for calculation',
    options: [
      { value: 'close', label: 'Close' },
      { value: 'open', label: 'Open' },
      { value: 'high', label: 'High' },
      { value: 'low', label: 'Low' },
      { value: 'hl2', label: 'HL2 (High+Low)/2' },
      { value: 'hlc3', label: 'HLC3 (High+Low+Close)/3' },
      { value: 'ohlc4', label: 'OHLC4 (Open+High+Low+Close)/4' },
      { value: 'volume', label: 'Volume' },
    ],
    default: 'close'
  },

  smoothing: {
    type: 'range',
    label: 'Smoothing Factor',
    description: 'Smoothing factor for EMA-based indicators',
    min: 0.1,
    max: 1.0,
    step: 0.1,
    default: 0.2
  },

  timeframe: {
    type: 'select',
    label: 'Timeframe',
    description: 'Chart timeframe for analysis',
    options: [
      { value: '1m', label: '1 Minute' },
      { value: '5m', label: '5 Minutes' },
      { value: '15m', label: '15 Minutes' },
      { value: '30m', label: '30 Minutes' },
      { value: '1h', label: '1 Hour' },
      { value: '4h', label: '4 Hours' },
      { value: '1d', label: '1 Day' },
      { value: '1w', label: '1 Week' },
      { value: '1M', label: '1 Month' },
    ],
    default: '1h'
  },

  symbol: {
    type: 'select',
    label: 'Symbol',
    description: 'Trading symbol with autocomplete',
    options: [
      // Popular Stocks
      { value: 'AAPL', label: 'AAPL - Apple Inc.' },
      { value: 'GOOGL', label: 'GOOGL - Alphabet Inc.' },
      { value: 'MSFT', label: 'MSFT - Microsoft Corp.' },
      { value: 'AMZN', label: 'AMZN - Amazon.com Inc.' },
      { value: 'TSLA', label: 'TSLA - Tesla Inc.' },
      { value: 'META', label: 'META - Meta Platforms Inc.' },
      { value: 'NVDA', label: 'NVDA - NVIDIA Corp.' },
      { value: 'SPY', label: 'SPY - SPDR S&P 500 ETF' },
      { value: 'QQQ', label: 'QQQ - Invesco QQQ Trust' },
      // Crypto
      { value: 'BTCUSD', label: 'BTCUSD - Bitcoin' },
      { value: 'ETHUSD', label: 'ETHUSD - Ethereum' },
      { value: 'ADAUSD', label: 'ADAUSD - Cardano' },
      { value: 'SOLUSD', label: 'SOLUSD - Solana' },
      { value: 'DOTUSD', label: 'DOTUSD - Polkadot' },
      // Forex
      { value: 'EURUSD', label: 'EURUSD - Euro/US Dollar' },
      { value: 'GBPUSD', label: 'GBPUSD - British Pound/US Dollar' },
      { value: 'USDJPY', label: 'USDJPY - US Dollar/Japanese Yen' },
      { value: 'AUDUSD', label: 'AUDUSD - Australian Dollar/US Dollar' },
      { value: 'USDCAD', label: 'USDCAD - US Dollar/Canadian Dollar' },
    ],
    default: 'AAPL'
  },

  riskLevel: {
    type: 'range',
    label: 'Risk Level',
    description: 'Risk tolerance level (1=Conservative, 5=Aggressive)',
    min: 1,
    max: 5,
    step: 1,
    default: 2
  },

  positionSize: {
    type: 'number',
    label: 'Position Size %',
    description: 'Percentage of portfolio per position',
    min: 0.1,
    max: 100,
    step: 0.1,
    default: 5.0
  },

  maxLoss: {
    type: 'number',
    label: 'Max Loss %',
    description: 'Maximum loss percentage per trade',
    min: 0.1,
    max: 50,
    step: 0.1,
    default: 2.0
  },

  quantity: {
    type: 'number',
    label: 'Quantity/Amount',
    description: 'Position size (depends on sizing method)',
    min: 0,
    default: 10
  },

  stopLoss: {
    type: 'number',
    label: 'Stop Loss %',
    description: 'Stop loss as percentage from entry',
    min: 0.1,
    max: 50,
    step: 0.1,
    default: 2.0
  },

  takeProfit: {
    type: 'number',
    label: 'Take Profit %',
    description: 'Take profit as percentage from entry',
    min: 0.1,
    max: 100,
    step: 0.1,
    default: 4.0
  }
};

// Common option groups
export const assetClassOptions: ConfigFieldOption[] = [
  { value: 'stocks', label: 'Stocks (Equities)' },
  { value: 'crypto', label: 'Cryptocurrency' },
  { value: 'forex', label: 'Foreign Exchange' },
];

export const orderTypeOptions: ConfigFieldOption[] = [
  { value: 'market', label: 'Market Order' },
  { value: 'limit', label: 'Limit Order' },
  { value: 'stop', label: 'Stop Order' },
  { value: 'stop_limit', label: 'Stop Limit Order' },
  { value: 'trailing_stop', label: 'Trailing Stop' },
  { value: 'iceberg', label: 'Iceberg Order' },
  { value: 'twap', label: 'TWAP (Time Weighted)' },
  { value: 'vwap', label: 'VWAP (Volume Weighted)' },
  { value: 'bracket', label: 'Bracket Order' },
  { value: 'oco', label: 'One-Cancels-Other' },
];

export const timeInForceOptions: ConfigFieldOption[] = [
  { value: 'GTC', label: 'Good Till Canceled' },
  { value: 'DAY', label: 'Day Order' },
  { value: 'IOC', label: 'Immediate or Cancel' },
  { value: 'FOK', label: 'Fill or Kill' },
  { value: 'GTD', label: 'Good Till Date' },
  { value: 'ATC', label: 'At The Close' },
  { value: 'ATO', label: 'At The Open' },
];

export const positionSizingOptions: ConfigFieldOption[] = [
  { value: 'fixed_amount', label: 'Fixed Amount' },
  { value: 'percentage', label: 'Percentage of Portfolio' },
  { value: 'fixed_risk', label: 'Fixed Risk Amount' },
  { value: 'kelly_criterion', label: 'Kelly Criterion' },
  { value: 'volatility_based', label: 'Volatility Based' },
  { value: 'equal_weight', label: 'Equal Weight' },
];