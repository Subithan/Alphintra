import { Node, Edge } from 'reactflow';

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: 'momentum' | 'mean_reversion' | 'trend_following' | 'arbitrage' | 'risk_management' | 'scalping' | 'swing' | 'breakout';
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  timeframe: string[];
  assetClasses: string[];
  tags: string[];
  nodes: Node[];
  edges: Edge[];
  expectedReturn?: string;
  maxDrawdown?: string;
  sharpeRatio?: string;
  winRate?: string;
  author?: string;
  version: string;
  createdAt: string;
  lastModified: string;
  thumbnail?: string;
}

export const workflowTemplates: WorkflowTemplate[] = [
  // MOMENTUM STRATEGIES
  {
    id: 'moving-average-crossover',
    name: 'Moving Average Crossover',
    description: 'Classic momentum strategy using fast and slow moving average crossover signals',
    category: 'momentum',
    difficulty: 'beginner',
    timeframe: ['1h', '4h', '1d'],
    assetClasses: ['stocks', 'crypto', 'forex'],
    tags: ['MA', 'crossover', 'trend', 'momentum'],
    expectedReturn: '12-18%',
    maxDrawdown: '8-12%',
    sharpeRatio: '1.2-1.8',
    winRate: '45-55%',
    author: 'Alphintra Team',
    version: '1.0.0',
    createdAt: '2024-01-15',
    lastModified: '2024-01-15',
    nodes: [
      {
        id: 'data-1',
        type: 'dataSource',
        position: { x: 100, y: 200 },
        data: {
          label: 'Market Data',
          parameters: { symbol: 'AAPL', timeframe: '1h', bars: 1000, dataSource: 'system', assetClass: 'stocks' }
        }
      },
      {
        id: 'fast-ma',
        type: 'technicalIndicator',
        position: { x: 300, y: 100 },
        data: {
          label: 'Fast MA (20)',
          parameters: { indicatorCategory: 'trend', indicator: 'EMA', period: 20, source: 'close' }
        }
      },
      {
        id: 'slow-ma',
        type: 'technicalIndicator',
        position: { x: 300, y: 300 },
        data: {
          label: 'Slow MA (50)',
          parameters: { indicatorCategory: 'trend', indicator: 'EMA', period: 50, source: 'close' }
        }
      },
      {
        id: 'crossover-condition',
        type: 'condition',
        position: { x: 500, y: 200 },
        data: {
          label: 'MA Crossover',
          parameters: { conditionType: 'crossover', condition: 'cross_above', confirmationBars: 1 }
        }
      },
      {
        id: 'buy-action',
        type: 'action',
        position: { x: 700, y: 150 },
        data: {
          label: 'Buy Signal',
          parameters: { actionCategory: 'entry', action: 'buy', quantity: 100, order_type: 'market', stop_loss: 2.0, take_profit: 4.0 }
        }
      },
      {
        id: 'sell-action',
        type: 'action',
        position: { x: 700, y: 250 },
        data: {
          label: 'Sell Signal',
          parameters: { actionCategory: 'entry', action: 'sell', quantity: 100, order_type: 'market', stop_loss: 2.0, take_profit: 4.0 }
        }
      }
    ],
    edges: [
      { id: 'e1', source: 'data-1', target: 'fast-ma', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e2', source: 'data-1', target: 'slow-ma', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e3', source: 'fast-ma', target: 'crossover-condition', sourceHandle: 'value-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e4', source: 'slow-ma', target: 'crossover-condition', sourceHandle: 'value-output', targetHandle: 'value-input', type: 'smart' },
      { id: 'e5', source: 'crossover-condition', target: 'buy-action', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' }
    ]
  },

  {
    id: 'rsi-momentum',
    name: 'RSI Momentum Strategy',
    description: 'Momentum strategy using RSI divergence and overbought/oversold conditions',
    category: 'momentum',
    difficulty: 'intermediate',
    timeframe: ['15m', '1h', '4h'],
    assetClasses: ['crypto', 'stocks'],
    tags: ['RSI', 'momentum', 'divergence', 'oscillator'],
    expectedReturn: '15-25%',
    maxDrawdown: '10-15%',
    sharpeRatio: '1.0-1.5',
    winRate: '40-50%',
    author: 'Alphintra Team',
    version: '1.0.0',
    createdAt: '2024-01-15',
    lastModified: '2024-01-15',
    nodes: [
      {
        id: 'data-1',
        type: 'dataSource',
        position: { x: 100, y: 200 },
        data: {
          label: 'Market Data',
          parameters: { symbol: 'BTC/USD', timeframe: '1h', bars: 1000, dataSource: 'system', assetClass: 'crypto' }
        }
      },
      {
        id: 'rsi-indicator',
        type: 'technicalIndicator',
        position: { x: 300, y: 200 },
        data: {
          label: 'RSI (14)',
          parameters: { indicatorCategory: 'momentum', indicator: 'RSI', period: 14, source: 'close' }
        }
      },
      {
        id: 'oversold-condition',
        type: 'condition',
        position: { x: 500, y: 150 },
        data: {
          label: 'Oversold',
          parameters: { conditionType: 'comparison', condition: 'less_than', value: 30, confirmationBars: 2 }
        }
      },
      {
        id: 'overbought-condition',
        type: 'condition',
        position: { x: 500, y: 250 },
        data: {
          label: 'Overbought',
          parameters: { conditionType: 'comparison', condition: 'greater_than', value: 70, confirmationBars: 2 }
        }
      },
      {
        id: 'buy-action',
        type: 'action',
        position: { x: 700, y: 150 },
        data: {
          label: 'Buy Oversold',
          parameters: { actionCategory: 'entry', action: 'buy', quantity: 50, order_type: 'limit', stop_loss: 3.0, take_profit: 6.0 }
        }
      },
      {
        id: 'sell-action',
        type: 'action',
        position: { x: 700, y: 250 },
        data: {
          label: 'Sell Overbought',
          parameters: { actionCategory: 'entry', action: 'sell', quantity: 50, order_type: 'limit', stop_loss: 3.0, take_profit: 6.0 }
        }
      }
    ],
    edges: [
      { id: 'e1', source: 'data-1', target: 'rsi-indicator', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e2', source: 'rsi-indicator', target: 'oversold-condition', sourceHandle: 'value-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e3', source: 'rsi-indicator', target: 'overbought-condition', sourceHandle: 'value-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e4', source: 'oversold-condition', target: 'buy-action', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' },
      { id: 'e5', source: 'overbought-condition', target: 'sell-action', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' }
    ]
  },

  {
    id: 'macd-momentum',
    name: 'MACD Momentum',
    description: 'Advanced momentum strategy using MACD histogram and signal line crossovers',
    category: 'momentum',
    difficulty: 'intermediate',
    timeframe: ['1h', '4h', '1d'],
    assetClasses: ['stocks', 'forex'],
    tags: ['MACD', 'histogram', 'signal', 'momentum'],
    expectedReturn: '18-28%',
    maxDrawdown: '12-18%',
    sharpeRatio: '1.3-1.9',
    winRate: '48-58%',
    author: 'Alphintra Team',
    version: '1.0.0',
    createdAt: '2024-01-15',
    lastModified: '2024-01-15',
    nodes: [
      {
        id: 'data-1',
        type: 'dataSource',
        position: { x: 100, y: 200 },
        data: {
          label: 'Market Data',
          parameters: { symbol: 'EUR/USD', timeframe: '4h', bars: 1000, dataSource: 'system', assetClass: 'forex' }
        }
      },
      {
        id: 'macd-indicator',
        type: 'technicalIndicator',
        position: { x: 300, y: 200 },
        data: {
          label: 'MACD (12,26,9)',
          parameters: { indicatorCategory: 'oscillators', indicator: 'MACD', fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 }
        }
      },
      {
        id: 'signal-crossover',
        type: 'condition',
        position: { x: 500, y: 150 },
        data: {
          label: 'Signal Cross',
          parameters: { conditionType: 'crossover', condition: 'cross_above', confirmationBars: 1 }
        }
      },
      {
        id: 'histogram-positive',
        type: 'condition',
        position: { x: 500, y: 250 },
        data: {
          label: 'Histogram > 0',
          parameters: { conditionType: 'comparison', condition: 'greater_than', value: 0 }
        }
      },
      {
        id: 'and-gate',
        type: 'logic',
        position: { x: 650, y: 200 },
        data: {
          label: 'AND Gate',
          parameters: { operation: 'AND', inputs: 2 }
        }
      },
      {
        id: 'buy-action',
        type: 'action',
        position: { x: 800, y: 200 },
        data: {
          label: 'Buy Signal',
          parameters: { actionCategory: 'entry', action: 'buy', quantity: 100, order_type: 'market', stop_loss: 2.5, take_profit: 5.0 }
        }
      }
    ],
    edges: [
      { id: 'e1', source: 'data-1', target: 'macd-indicator', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e2', source: 'macd-indicator', target: 'signal-crossover', sourceHandle: 'macd-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e3', source: 'macd-indicator', target: 'signal-crossover', sourceHandle: 'signal-output', targetHandle: 'value-input', type: 'smart' },
      { id: 'e4', source: 'macd-indicator', target: 'histogram-positive', sourceHandle: 'histogram-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e5', source: 'signal-crossover', target: 'and-gate', sourceHandle: 'signal-output', targetHandle: 'input', type: 'smart' },
      { id: 'e6', source: 'histogram-positive', target: 'and-gate', sourceHandle: 'signal-output', targetHandle: 'input', type: 'smart' },
      { id: 'e7', source: 'and-gate', target: 'buy-action', sourceHandle: 'output', targetHandle: 'trigger-input', type: 'smart' }
    ]
  },

  // MEAN REVERSION STRATEGIES
  {
    id: 'bollinger-bands-mean-reversion',
    name: 'Bollinger Bands Mean Reversion',
    description: 'Mean reversion strategy using Bollinger Bands squeeze and band touches',
    category: 'mean_reversion',
    difficulty: 'intermediate',
    timeframe: ['15m', '1h', '4h'],
    assetClasses: ['stocks', 'crypto'],
    tags: ['bollinger', 'bands', 'mean reversion', 'volatility'],
    expectedReturn: '10-20%',
    maxDrawdown: '8-12%',
    sharpeRatio: '1.4-2.0',
    winRate: '55-65%',
    author: 'Alphintra Team',
    version: '1.0.0',
    createdAt: '2024-01-15',
    lastModified: '2024-01-15',
    nodes: [
      {
        id: 'data-1',
        type: 'dataSource',
        position: { x: 100, y: 200 },
        data: {
          label: 'Market Data',
          parameters: { symbol: 'TSLA', timeframe: '1h', bars: 1000, dataSource: 'system', assetClass: 'stocks' }
        }
      },
      {
        id: 'bb-indicator',
        type: 'technicalIndicator',
        position: { x: 300, y: 200 },
        data: {
          label: 'Bollinger Bands',
          parameters: { indicatorCategory: 'volatility', indicator: 'BB', period: 20, multiplier: 2.0 }
        }
      },
      {
        id: 'lower-touch',
        type: 'condition',
        position: { x: 500, y: 150 },
        data: {
          label: 'Touch Lower Band',
          parameters: { conditionType: 'comparison', condition: 'less_than_equal', confirmationBars: 1 }
        }
      },
      {
        id: 'upper-touch',
        type: 'condition',
        position: { x: 500, y: 250 },
        data: {
          label: 'Touch Upper Band',
          parameters: { conditionType: 'comparison', condition: 'greater_than_equal', confirmationBars: 1 }
        }
      },
      {
        id: 'buy-action',
        type: 'action',
        position: { x: 700, y: 150 },
        data: {
          label: 'Buy at Lower',
          parameters: { actionCategory: 'entry', action: 'buy', quantity: 100, order_type: 'limit', stop_loss: 2.0, take_profit: 3.0 }
        }
      },
      {
        id: 'sell-action',
        type: 'action',
        position: { x: 700, y: 250 },
        data: {
          label: 'Sell at Upper',
          parameters: { actionCategory: 'entry', action: 'sell', quantity: 100, order_type: 'limit', stop_loss: 2.0, take_profit: 3.0 }
        }
      }
    ],
    edges: [
      { id: 'e1', source: 'data-1', target: 'bb-indicator', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e2', source: 'data-1', target: 'lower-touch', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e3', source: 'bb-indicator', target: 'lower-touch', sourceHandle: 'lower-output', targetHandle: 'value-input', type: 'smart' },
      { id: 'e4', source: 'data-1', target: 'upper-touch', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e5', source: 'bb-indicator', target: 'upper-touch', sourceHandle: 'upper-output', targetHandle: 'value-input', type: 'smart' },
      { id: 'e6', source: 'lower-touch', target: 'buy-action', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' },
      { id: 'e7', source: 'upper-touch', target: 'sell-action', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' }
    ]
  },

  {
    id: 'stochastic-mean-reversion',
    name: 'Stochastic Mean Reversion',
    description: 'Mean reversion using Stochastic oscillator extreme readings',
    category: 'mean_reversion',
    difficulty: 'beginner',
    timeframe: ['1h', '4h'],
    assetClasses: ['crypto', 'forex'],
    tags: ['stochastic', 'oversold', 'overbought', 'mean reversion'],
    expectedReturn: '8-15%',
    maxDrawdown: '6-10%',
    sharpeRatio: '1.2-1.7',
    winRate: '60-70%',
    author: 'Alphintra Team',
    version: '1.0.0',
    createdAt: '2024-01-15',
    lastModified: '2024-01-15',
    nodes: [
      {
        id: 'data-1',
        type: 'dataSource',
        position: { x: 100, y: 200 },
        data: {
          label: 'Market Data',
          parameters: { symbol: 'ETH/USD', timeframe: '4h', bars: 1000, dataSource: 'system', assetClass: 'crypto' }
        }
      },
      {
        id: 'stoch-indicator',
        type: 'technicalIndicator',
        position: { x: 300, y: 200 },
        data: {
          label: 'Stochastic (14,3,3)',
          parameters: { indicatorCategory: 'momentum', indicator: 'Stochastic', period: 14, slowPeriod: 3, smoothingPeriod: 3 }
        }
      },
      {
        id: 'oversold-condition',
        type: 'condition',
        position: { x: 500, y: 150 },
        data: {
          label: 'Oversold %K < 20',
          parameters: { conditionType: 'comparison', condition: 'less_than', value: 20, confirmationBars: 2 }
        }
      },
      {
        id: 'overbought-condition',
        type: 'condition',
        position: { x: 500, y: 250 },
        data: {
          label: 'Overbought %K > 80',
          parameters: { conditionType: 'comparison', condition: 'greater_than', value: 80, confirmationBars: 2 }
        }
      },
      {
        id: 'buy-action',
        type: 'action',
        position: { x: 700, y: 150 },
        data: {
          label: 'Buy Oversold',
          parameters: { actionCategory: 'entry', action: 'buy', quantity: 75, order_type: 'market', stop_loss: 2.5, take_profit: 4.0 }
        }
      },
      {
        id: 'sell-action',
        type: 'action',
        position: { x: 700, y: 250 },
        data: {
          label: 'Sell Overbought',
          parameters: { actionCategory: 'entry', action: 'sell', quantity: 75, order_type: 'market', stop_loss: 2.5, take_profit: 4.0 }
        }
      }
    ],
    edges: [
      { id: 'e1', source: 'data-1', target: 'stoch-indicator', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e2', source: 'stoch-indicator', target: 'oversold-condition', sourceHandle: 'k-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e3', source: 'stoch-indicator', target: 'overbought-condition', sourceHandle: 'k-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e4', source: 'oversold-condition', target: 'buy-action', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' },
      { id: 'e5', source: 'overbought-condition', target: 'sell-action', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' }
    ]
  },

  // TREND FOLLOWING STRATEGIES
  {
    id: 'breakout-trend-following',
    name: 'Breakout Trend Following',
    description: 'Trend following strategy using Donchian Channel breakouts with ADX filter',
    category: 'trend_following',
    difficulty: 'advanced',
    timeframe: ['4h', '1d'],
    assetClasses: ['stocks', 'crypto', 'forex'],
    tags: ['breakout', 'donchian', 'ADX', 'trend following'],
    expectedReturn: '20-35%',
    maxDrawdown: '15-25%',
    sharpeRatio: '1.1-1.6',
    winRate: '35-45%',
    author: 'Alphintra Team',
    version: '1.0.0',
    createdAt: '2024-01-15',
    lastModified: '2024-01-15',
    nodes: [
      {
        id: 'data-1',
        type: 'dataSource',
        position: { x: 100, y: 200 },
        data: {
          label: 'Market Data',
          parameters: { symbol: 'NVDA', timeframe: '1d', bars: 1000, dataSource: 'system', assetClass: 'stocks' }
        }
      },
      {
        id: 'donchian-indicator',
        type: 'technicalIndicator',
        position: { x: 300, y: 150 },
        data: {
          label: 'Donchian (20)',
          parameters: { indicatorCategory: 'volatility', indicator: 'donchian', period: 20 }
        }
      },
      {
        id: 'adx-indicator',
        type: 'technicalIndicator',
        position: { x: 300, y: 250 },
        data: {
          label: 'ADX (14)',
          parameters: { indicatorCategory: 'oscillators', indicator: 'ADX', period: 14 }
        }
      },
      {
        id: 'upper-breakout',
        type: 'condition',
        position: { x: 500, y: 100 },
        data: {
          label: 'Upper Breakout',
          parameters: { conditionType: 'comparison', condition: 'greater_than', confirmationBars: 1 }
        }
      },
      {
        id: 'lower-breakout',
        type: 'condition',
        position: { x: 500, y: 200 },
        data: {
          label: 'Lower Breakout',
          parameters: { conditionType: 'comparison', condition: 'less_than', confirmationBars: 1 }
        }
      },
      {
        id: 'adx-filter',
        type: 'condition',
        position: { x: 500, y: 300 },
        data: {
          label: 'Strong Trend ADX > 25',
          parameters: { conditionType: 'comparison', condition: 'greater_than', value: 25 }
        }
      },
      {
        id: 'buy-and-gate',
        type: 'logic',
        position: { x: 650, y: 150 },
        data: {
          label: 'Buy AND',
          parameters: { operation: 'AND', inputs: 2 }
        }
      },
      {
        id: 'sell-and-gate',
        type: 'logic',
        position: { x: 650, y: 250 },
        data: {
          label: 'Sell AND',
          parameters: { operation: 'AND', inputs: 2 }
        }
      },
      {
        id: 'buy-action',
        type: 'action',
        position: { x: 800, y: 150 },
        data: {
          label: 'Buy Breakout',
          parameters: { actionCategory: 'entry', action: 'buy', quantity: 100, order_type: 'stop', stop_loss: 3.0, take_profit: 9.0 }
        }
      },
      {
        id: 'sell-action',
        type: 'action',
        position: { x: 800, y: 250 },
        data: {
          label: 'Sell Breakdown',
          parameters: { actionCategory: 'entry', action: 'sell', quantity: 100, order_type: 'stop', stop_loss: 3.0, take_profit: 9.0 }
        }
      }
    ],
    edges: [
      { id: 'e1', source: 'data-1', target: 'donchian-indicator', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e2', source: 'data-1', target: 'adx-indicator', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e3', source: 'data-1', target: 'upper-breakout', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e4', source: 'donchian-indicator', target: 'upper-breakout', sourceHandle: 'upper-output', targetHandle: 'value-input', type: 'smart' },
      { id: 'e5', source: 'data-1', target: 'lower-breakout', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e6', source: 'donchian-indicator', target: 'lower-breakout', sourceHandle: 'lower-output', targetHandle: 'value-input', type: 'smart' },
      { id: 'e7', source: 'adx-indicator', target: 'adx-filter', sourceHandle: 'adx-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e8', source: 'upper-breakout', target: 'buy-and-gate', sourceHandle: 'signal-output', targetHandle: 'input', type: 'smart' },
      { id: 'e9', source: 'adx-filter', target: 'buy-and-gate', sourceHandle: 'signal-output', targetHandle: 'input', type: 'smart' },
      { id: 'e10', source: 'lower-breakout', target: 'sell-and-gate', sourceHandle: 'signal-output', targetHandle: 'input', type: 'smart' },
      { id: 'e11', source: 'adx-filter', target: 'sell-and-gate', sourceHandle: 'signal-output', targetHandle: 'input', type: 'smart' },
      { id: 'e12', source: 'buy-and-gate', target: 'buy-action', sourceHandle: 'output', targetHandle: 'trigger-input', type: 'smart' },
      { id: 'e13', source: 'sell-and-gate', target: 'sell-action', sourceHandle: 'output', targetHandle: 'trigger-input', type: 'smart' }
    ]
  },

  {
    id: 'turtle-trend-following',
    name: 'Turtle Trading System',
    description: 'Classic trend following strategy based on the famous Turtle Trading rules',
    category: 'trend_following',
    difficulty: 'advanced',
    timeframe: ['1d', '1w'],
    assetClasses: ['stocks', 'forex', 'crypto'],
    tags: ['turtle', 'breakout', 'position sizing', 'trend following'],
    expectedReturn: '25-40%',
    maxDrawdown: '20-30%',
    sharpeRatio: '1.0-1.4',
    winRate: '30-40%',
    author: 'Alphintra Team',
    version: '1.0.0',
    createdAt: '2024-01-15',
    lastModified: '2024-01-15',
    nodes: [
      {
        id: 'data-1',
        type: 'dataSource',
        position: { x: 100, y: 200 },
        data: {
          label: 'Market Data',
          parameters: { symbol: 'AMZN', timeframe: '1d', bars: 1000, dataSource: 'system', assetClass: 'stocks' }
        }
      },
      {
        id: 'entry-breakout',
        type: 'technicalIndicator',
        position: { x: 300, y: 150 },
        data: {
          label: 'Entry Breakout (20)',
          parameters: { indicatorCategory: 'volatility', indicator: 'donchian', period: 20 }
        }
      },
      {
        id: 'exit-breakout',
        type: 'technicalIndicator',
        position: { x: 300, y: 250 },
        data: {
          label: 'Exit Breakout (10)',
          parameters: { indicatorCategory: 'volatility', indicator: 'donchian', period: 10 }
        }
      },
      {
        id: 'atr-indicator',
        type: 'technicalIndicator',
        position: { x: 300, y: 350 },
        data: {
          label: 'ATR (20)',
          parameters: { indicatorCategory: 'volatility', indicator: 'ATR', period: 20 }
        }
      },
      {
        id: 'long-entry',
        type: 'condition',
        position: { x: 500, y: 100 },
        data: {
          label: 'Long Entry',
          parameters: { conditionType: 'comparison', condition: 'greater_than', confirmationBars: 1 }
        }
      },
      {
        id: 'short-entry',
        type: 'condition',
        position: { x: 500, y: 200 },
        data: {
          label: 'Short Entry',
          parameters: { conditionType: 'comparison', condition: 'less_than', confirmationBars: 1 }
        }
      },
      {
        id: 'position-sizing',
        type: 'risk',
        position: { x: 500, y: 350 },
        data: {
          label: 'ATR Position Sizing',
          parameters: { riskCategory: 'position', riskType: 'position_size', maxLoss: 2.0, positionSize: 1.0 }
        }
      },
      {
        id: 'buy-action',
        type: 'action',
        position: { x: 700, y: 100 },
        data: {
          label: 'Buy Turtle',
          parameters: { actionCategory: 'entry', action: 'buy', quantity: 100, order_type: 'stop', stop_loss: 2.0, take_profit: 6.0 }
        }
      },
      {
        id: 'sell-action',
        type: 'action',
        position: { x: 700, y: 200 },
        data: {
          label: 'Sell Turtle',
          parameters: { actionCategory: 'entry', action: 'sell', quantity: 100, order_type: 'stop', stop_loss: 2.0, take_profit: 6.0 }
        }
      }
    ],
    edges: [
      { id: 'e1', source: 'data-1', target: 'entry-breakout', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e2', source: 'data-1', target: 'exit-breakout', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e3', source: 'data-1', target: 'atr-indicator', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e4', source: 'data-1', target: 'long-entry', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e5', source: 'entry-breakout', target: 'long-entry', sourceHandle: 'upper-output', targetHandle: 'value-input', type: 'smart' },
      { id: 'e6', source: 'data-1', target: 'short-entry', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e7', source: 'entry-breakout', target: 'short-entry', sourceHandle: 'lower-output', targetHandle: 'value-input', type: 'smart' },
      { id: 'e8', source: 'atr-indicator', target: 'position-sizing', sourceHandle: 'value-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e9', source: 'long-entry', target: 'buy-action', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' },
      { id: 'e10', source: 'short-entry', target: 'sell-action', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' },
      { id: 'e11', source: 'position-sizing', target: 'buy-action', sourceHandle: 'risk-output', targetHandle: 'risk-input', type: 'smart' },
      { id: 'e12', source: 'position-sizing', target: 'sell-action', sourceHandle: 'risk-output', targetHandle: 'risk-input', type: 'smart' }
    ]
  },

  // RISK MANAGEMENT STRATEGIES
  {
    id: 'portfolio-risk-management',
    name: 'Portfolio Risk Management',
    description: 'Comprehensive portfolio risk management with position sizing and correlation control',
    category: 'risk_management',
    difficulty: 'advanced',
    timeframe: ['1d'],
    assetClasses: ['stocks', 'crypto'],
    tags: ['risk management', 'portfolio', 'position sizing', 'correlation'],
    expectedReturn: '8-15%',
    maxDrawdown: '3-8%',
    sharpeRatio: '1.8-2.5',
    winRate: '50-60%',
    author: 'Alphintra Team',
    version: '1.0.0',
    createdAt: '2024-01-15',
    lastModified: '2024-01-15',
    nodes: [
      {
        id: 'data-1',
        type: 'dataSource',
        position: { x: 100, y: 200 },
        data: {
          label: 'Market Data',
          parameters: { symbol: 'SPY', timeframe: '1d', bars: 1000, dataSource: 'system', assetClass: 'stocks' }
        }
      },
      {
        id: 'portfolio-heat',
        type: 'risk',
        position: { x: 300, y: 150 },
        data: {
          label: 'Portfolio Heat',
          parameters: { riskCategory: 'portfolio', riskType: 'portfolio_heat', portfolioHeat: 15, maxLoss: 5.0 }
        }
      },
      {
        id: 'correlation-control',
        type: 'risk',
        position: { x: 300, y: 250 },
        data: {
          label: 'Correlation Control',
          parameters: { riskCategory: 'portfolio', riskType: 'correlation_control', maxCorrelation: 0.7 }
        }
      },
      {
        id: 'drawdown-protection',
        type: 'risk',
        position: { x: 300, y: 350 },
        data: {
          label: 'Drawdown Protection',
          parameters: { riskCategory: 'protection', riskType: 'drawdown_protection', maxDrawdown: 10.0 }
        }
      },
      {
        id: 'risk-filter',
        type: 'condition',
        position: { x: 500, y: 200 },
        data: {
          label: 'Risk Check',
          parameters: { conditionType: 'comparison', condition: 'less_than', value: 20 }
        }
      },
      {
        id: 'position-sizing',
        type: 'risk',
        position: { x: 500, y: 300 },
        data: {
          label: 'Kelly Position Sizing',
          parameters: { riskCategory: 'position', riskType: 'kelly_criterion', maxLoss: 2.0, winRate: 55 }
        }
      },
      {
        id: 'safe-entry',
        type: 'action',
        position: { x: 700, y: 250 },
        data: {
          label: 'Safe Entry',
          parameters: { actionCategory: 'entry', action: 'buy', quantity: 50, order_type: 'limit', stop_loss: 1.5, take_profit: 3.0 }
        }
      }
    ],
    edges: [
      { id: 'e1', source: 'data-1', target: 'portfolio-heat', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e2', source: 'data-1', target: 'correlation-control', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e3', source: 'data-1', target: 'drawdown-protection', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e4', source: 'portfolio-heat', target: 'risk-filter', sourceHandle: 'risk-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e5', source: 'data-1', target: 'position-sizing', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e6', source: 'risk-filter', target: 'safe-entry', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' },
      { id: 'e7', source: 'position-sizing', target: 'safe-entry', sourceHandle: 'risk-output', targetHandle: 'risk-input', type: 'smart' }
    ]
  },

  // SCALPING STRATEGIES
  {
    id: 'scalping-5min',
    name: '5-Minute Scalping',
    description: 'High-frequency scalping strategy using multiple timeframe analysis',
    category: 'scalping',
    difficulty: 'advanced',
    timeframe: ['1m', '5m'],
    assetClasses: ['forex', 'crypto'],
    tags: ['scalping', 'high frequency', 'multi-timeframe'],
    expectedReturn: '30-50%',
    maxDrawdown: '10-20%',
    sharpeRatio: '1.5-2.2',
    winRate: '65-75%',
    author: 'Alphintra Team',
    version: '1.0.0',
    createdAt: '2024-01-15',
    lastModified: '2024-01-15',
    nodes: [
      {
        id: 'data-5m',
        type: 'dataSource',
        position: { x: 100, y: 150 },
        data: {
          label: '5m Data',
          parameters: { symbol: 'EUR/USD', timeframe: '5m', bars: 500, dataSource: 'system', assetClass: 'forex' }
        }
      },
      {
        id: 'data-1m',
        type: 'dataSource',
        position: { x: 100, y: 250 },
        data: {
          label: '1m Data',
          parameters: { symbol: 'EUR/USD', timeframe: '1m', bars: 500, dataSource: 'system', assetClass: 'forex' }
        }
      },
      {
        id: 'ema-5m',
        type: 'technicalIndicator',
        position: { x: 300, y: 150 },
        data: {
          label: '5m EMA (21)',
          parameters: { indicatorCategory: 'trend', indicator: 'EMA', period: 21 }
        }
      },
      {
        id: 'rsi-1m',
        type: 'technicalIndicator',
        position: { x: 300, y: 250 },
        data: {
          label: '1m RSI (14)',
          parameters: { indicatorCategory: 'momentum', indicator: 'RSI', period: 14 }
        }
      },
      {
        id: 'trend-condition',
        type: 'condition',
        position: { x: 500, y: 150 },
        data: {
          label: '5m Trend Up',
          parameters: { conditionType: 'comparison', condition: 'greater_than' }
        }
      },
      {
        id: 'entry-condition',
        type: 'condition',
        position: { x: 500, y: 250 },
        data: {
          label: '1m RSI < 30',
          parameters: { conditionType: 'comparison', condition: 'less_than', value: 30 }
        }
      },
      {
        id: 'scalp-entry',
        type: 'action',
        position: { x: 700, y: 200 },
        data: {
          label: 'Scalp Buy',
          parameters: { actionCategory: 'entry', action: 'buy', quantity: 1000, order_type: 'market', stop_loss: 0.5, take_profit: 1.0 }
        }
      }
    ],
    edges: [
      { id: 'e1', source: 'data-5m', target: 'ema-5m', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e2', source: 'data-1m', target: 'rsi-1m', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e3', source: 'data-5m', target: 'trend-condition', sourceHandle: 'data-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e4', source: 'ema-5m', target: 'trend-condition', sourceHandle: 'value-output', targetHandle: 'value-input', type: 'smart' },
      { id: 'e5', source: 'rsi-1m', target: 'entry-condition', sourceHandle: 'value-output', targetHandle: 'data-input', type: 'smart' },
      { id: 'e6', source: 'trend-condition', target: 'scalp-entry', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' },
      { id: 'e7', source: 'entry-condition', target: 'scalp-entry', sourceHandle: 'signal-output', targetHandle: 'trigger-input', type: 'smart' }
    ]
  }
];

export const getTemplatesByCategory = (category: WorkflowTemplate['category']): WorkflowTemplate[] => {
  return workflowTemplates.filter(template => template.category === category);
};

export const getTemplatesByDifficulty = (difficulty: WorkflowTemplate['difficulty']): WorkflowTemplate[] => {
  return workflowTemplates.filter(template => template.difficulty === difficulty);
};

export const getTemplatesByAssetClass = (assetClass: string): WorkflowTemplate[] => {
  return workflowTemplates.filter(template => template.assetClasses.includes(assetClass));
};

export const searchTemplates = (query: string): WorkflowTemplate[] => {
  const lowercaseQuery = query.toLowerCase();
  return workflowTemplates.filter(template => 
    template.name.toLowerCase().includes(lowercaseQuery) ||
    template.description.toLowerCase().includes(lowercaseQuery) ||
    template.tags.some(tag => tag.toLowerCase().includes(lowercaseQuery))
  );
};

export const getTemplateById = (id: string): WorkflowTemplate | undefined => {
  return workflowTemplates.find(template => template.id === id);
};