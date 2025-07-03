'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  BarChart3, 
  Target, 
  Zap, 
  Database, 
  Settings, 
  GitBranch, 
  Shield,
  DollarSign,
  Timer,
  AlertTriangle,
  Activity
} from 'lucide-react';

interface ComponentItem {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  type: string;
  category: string;
  tags: string[];
}

const componentLibrary: ComponentItem[] = [
  // Data Sources
  {
    id: 'data-source',
    name: 'Market Data',
    description: 'Real-time or historical market data feed',
    icon: <Database className="h-4 w-4" />,
    type: 'dataSource',
    category: 'Data Sources',
    tags: ['data', 'input', 'market']
  },
  {
    id: 'custom-dataset',
    name: 'Custom Dataset',
    description: 'Upload your own CSV/Excel dataset',
    icon: <Database className="h-4 w-4" />,
    type: 'customDataset',
    category: 'Data Sources',
    tags: ['data', 'custom', 'upload', 'csv', 'excel']
  },

  // Technical Indicators - Trend
  {
    id: 'sma',
    name: 'Simple Moving Average',
    description: 'Calculate simple moving average',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Trend Indicators',
    tags: ['sma', 'trend', 'moving average']
  },
  {
    id: 'ema',
    name: 'Exponential Moving Average',
    description: 'Calculate exponential moving average',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Trend Indicators',
    tags: ['ema', 'trend', 'moving average']
  },
  {
    id: 'wma',
    name: 'Weighted Moving Average',
    description: 'Weighted moving average',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Trend Indicators',
    tags: ['wma', 'trend', 'weighted']
  },
  {
    id: 'vwma',
    name: 'Volume Weighted MA',
    description: 'Volume weighted moving average',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Trend Indicators',
    tags: ['vwma', 'trend', 'volume']
  },
  {
    id: 'hma',
    name: 'Hull Moving Average',
    description: 'Hull moving average',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Trend Indicators',
    tags: ['hma', 'trend', 'hull']
  },

  // Technical Indicators - Momentum
  {
    id: 'rsi',
    name: 'RSI',
    description: 'Relative Strength Index oscillator',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Momentum Indicators',
    tags: ['rsi', 'oscillator', 'momentum']
  },
  {
    id: 'stochastic',
    name: 'Stochastic',
    description: 'Stochastic momentum oscillator',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Momentum Indicators',
    tags: ['stochastic', 'momentum', 'oscillator']
  },
  {
    id: 'williams-r',
    name: 'Williams %R',
    description: 'Williams percent range',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Momentum Indicators',
    tags: ['williams', 'momentum', 'oscillator']
  },
  {
    id: 'cci',
    name: 'CCI',
    description: 'Commodity Channel Index',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Momentum Indicators',
    tags: ['cci', 'momentum', 'channel']
  },
  {
    id: 'roc',
    name: 'Rate of Change',
    description: 'Price rate of change',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Momentum Indicators',
    tags: ['roc', 'momentum', 'change']
  },

  // Technical Indicators - Volatility
  {
    id: 'bollinger',
    name: 'Bollinger Bands',
    description: 'Volatility bands around moving average',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Volatility Indicators',
    tags: ['bollinger', 'volatility', 'bands']
  },
  {
    id: 'atr',
    name: 'ATR',
    description: 'Average True Range',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Volatility Indicators',
    tags: ['atr', 'volatility', 'range']
  },
  {
    id: 'keltner',
    name: 'Keltner Channels',
    description: 'Keltner channel bands',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Volatility Indicators',
    tags: ['keltner', 'volatility', 'channels']
  },
  {
    id: 'donchian',
    name: 'Donchian Channels',
    description: 'Donchian channel breakouts',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Volatility Indicators',
    tags: ['donchian', 'volatility', 'breakout']
  },

  // Technical Indicators - Volume
  {
    id: 'obv',
    name: 'On Balance Volume',
    description: 'On balance volume indicator',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Volume Indicators',
    tags: ['obv', 'volume', 'balance']
  },
  {
    id: 'vwap',
    name: 'VWAP',
    description: 'Volume weighted average price',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Volume Indicators',
    tags: ['vwap', 'volume', 'price']
  },
  {
    id: 'mfi',
    name: 'Money Flow Index',
    description: 'Money flow index oscillator',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Volume Indicators',
    tags: ['mfi', 'volume', 'money flow']
  },

  // Technical Indicators - Oscillators  
  {
    id: 'macd',
    name: 'MACD',
    description: 'Moving Average Convergence Divergence',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Oscillators',
    tags: ['macd', 'momentum', 'divergence']
  },
  {
    id: 'ao',
    name: 'Awesome Oscillator',
    description: 'Awesome oscillator momentum',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Oscillators',
    tags: ['ao', 'awesome', 'oscillator']
  },
  {
    id: 'adx',
    name: 'ADX',
    description: 'Average Directional Index',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Oscillators',
    tags: ['adx', 'directional', 'trend']
  },

  // Conditions - Comparison
  {
    id: 'value-comparison',
    name: 'Value Comparison',
    description: 'Compare values with operators',
    icon: <Target className="h-4 w-4" />,
    type: 'condition',
    category: 'Comparison Conditions',
    tags: ['comparison', 'value', 'operator']
  },
  {
    id: 'range-condition',
    name: 'Range Condition',
    description: 'Check if value is within range',
    icon: <Target className="h-4 w-4" />,
    type: 'condition',
    category: 'Comparison Conditions',
    tags: ['range', 'boundary', 'condition']
  },
  {
    id: 'percentage-change',
    name: 'Percentage Change',
    description: 'Monitor percentage changes',
    icon: <Target className="h-4 w-4" />,
    type: 'condition',
    category: 'Comparison Conditions',
    tags: ['percentage', 'change', 'threshold']
  },

  // Conditions - Crossover
  {
    id: 'crossover',
    name: 'Crossover',
    description: 'Detect line crossovers',
    icon: <GitBranch className="h-4 w-4" />,
    type: 'condition',
    category: 'Crossover Conditions',
    tags: ['crossover', 'intersection', 'signal']
  },
  {
    id: 'golden-cross',
    name: 'Golden Cross',
    description: 'Detect golden cross pattern',
    icon: <GitBranch className="h-4 w-4" />,
    type: 'condition',
    category: 'Crossover Conditions',
    tags: ['golden', 'cross', 'bullish']
  },
  {
    id: 'divergence',
    name: 'Divergence',
    description: 'Detect price-indicator divergence',
    icon: <GitBranch className="h-4 w-4" />,
    type: 'condition',
    category: 'Crossover Conditions',
    tags: ['divergence', 'indicator', 'signal']
  },

  // Conditions - Trend
  {
    id: 'trend-direction',
    name: 'Trend Direction',
    description: 'Analyze trend direction',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'condition',
    category: 'Trend Conditions',
    tags: ['trend', 'direction', 'rising', 'falling']
  },
  {
    id: 'trend-strength',
    name: 'Trend Strength',
    description: 'Measure trend strength',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'condition',
    category: 'Trend Conditions',
    tags: ['trend', 'strength', 'momentum']
  },

  // Conditions - Pattern
  {
    id: 'support-resistance',
    name: 'Support/Resistance',
    description: 'Detect support and resistance levels',
    icon: <Target className="h-4 w-4" />,
    type: 'condition',
    category: 'Pattern Conditions',
    tags: ['support', 'resistance', 'level']
  },
  {
    id: 'breakout',
    name: 'Breakout',
    description: 'Detect breakout patterns',
    icon: <Target className="h-4 w-4" />,
    type: 'condition',
    category: 'Pattern Conditions',
    tags: ['breakout', 'pattern', 'volatility']
  },
  {
    id: 'overbought-oversold',
    name: 'Overbought/Oversold',
    description: 'Detect extreme conditions',
    icon: <Target className="h-4 w-4" />,
    type: 'condition',
    category: 'Pattern Conditions',
    tags: ['overbought', 'oversold', 'extreme']
  },

  // Conditions - Multi-Timeframe
  {
    id: 'multi-timeframe',
    name: 'Multi-Timeframe',
    description: 'Multi-timeframe analysis',
    icon: <Timer className="h-4 w-4" />,
    type: 'condition',
    category: 'Multi-Timeframe Conditions',
    tags: ['timeframe', 'alignment', 'bias']
  },

  // Actions - Entry
  {
    id: 'buy-order',
    name: 'Buy Order',
    description: 'Execute buy/long entry order',
    icon: <Zap className="h-4 w-4 text-green-600" />,
    type: 'action',
    category: 'Entry Actions',
    tags: ['buy', 'order', 'long', 'entry']
  },
  {
    id: 'sell-order',
    name: 'Sell Order',
    description: 'Execute sell/short entry order',
    icon: <Zap className="h-4 w-4 text-red-600" />,
    type: 'action',
    category: 'Entry Actions',
    tags: ['sell', 'order', 'short', 'entry']
  },
  {
    id: 'limit-entry',
    name: 'Limit Entry',
    description: 'Place limit entry order',
    icon: <Zap className="h-4 w-4 text-blue-600" />,
    type: 'action',
    category: 'Entry Actions',
    tags: ['limit', 'entry', 'order']
  },
  {
    id: 'stop-entry',
    name: 'Stop Entry',
    description: 'Place stop entry order',
    icon: <Zap className="h-4 w-4 text-orange-600" />,
    type: 'action',
    category: 'Entry Actions',
    tags: ['stop', 'entry', 'breakout']
  },

  // Actions - Exit
  {
    id: 'close-position',
    name: 'Close Position',
    description: 'Close open position',
    icon: <Zap className="h-4 w-4 text-gray-600" />,
    type: 'action',
    category: 'Exit Actions',
    tags: ['close', 'position', 'exit']
  },
  {
    id: 'stop-loss',
    name: 'Stop Loss',
    description: 'Set stop loss order',
    icon: <Shield className="h-4 w-4" />,
    type: 'action',
    category: 'Exit Actions',
    tags: ['stop', 'loss', 'risk', 'exit']
  },
  {
    id: 'take-profit',
    name: 'Take Profit',
    description: 'Set take profit order',
    icon: <DollarSign className="h-4 w-4" />,
    type: 'action',
    category: 'Exit Actions',
    tags: ['take', 'profit', 'target', 'exit']
  },
  {
    id: 'trailing-stop',
    name: 'Trailing Stop',
    description: 'Set trailing stop order',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'action',
    category: 'Exit Actions',
    tags: ['trailing', 'stop', 'dynamic']
  },

  // Actions - Management
  {
    id: 'scale-in',
    name: 'Scale In',
    description: 'Scale into position',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'action',
    category: 'Management Actions',
    tags: ['scale', 'in', 'position', 'management']
  },
  {
    id: 'scale-out',
    name: 'Scale Out',
    description: 'Scale out of position',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'action',
    category: 'Management Actions',
    tags: ['scale', 'out', 'position', 'management']
  },
  {
    id: 'modify-order',
    name: 'Modify Order',
    description: 'Modify existing order',
    icon: <Settings className="h-4 w-4" />,
    type: 'action',
    category: 'Management Actions',
    tags: ['modify', 'order', 'adjustment']
  },

  // Actions - Portfolio
  {
    id: 'rebalance',
    name: 'Rebalance',
    description: 'Rebalance portfolio',
    icon: <Activity className="h-4 w-4" />,
    type: 'action',
    category: 'Portfolio Actions',
    tags: ['rebalance', 'portfolio', 'allocation']
  },
  {
    id: 'risk-off',
    name: 'Risk Off',
    description: 'Reduce portfolio risk',
    icon: <AlertTriangle className="h-4 w-4" />,
    type: 'action',
    category: 'Portfolio Actions',
    tags: ['risk', 'off', 'protection']
  },

  // Logic
  {
    id: 'and-gate',
    name: 'AND Gate',
    description: 'Logical AND operation',
    icon: <GitBranch className="h-4 w-4" />,
    type: 'logic',
    category: 'Logic',
    tags: ['and', 'logic', 'gate']
  },
  {
    id: 'or-gate',
    name: 'OR Gate',
    description: 'Logical OR operation',  
    icon: <GitBranch className="h-4 w-4" />,
    type: 'logic',
    category: 'Logic',
    tags: ['or', 'logic', 'gate']
  },
  {
    id: 'not-gate',
    name: 'NOT Gate',
    description: 'Logical NOT operation',
    icon: <GitBranch className="h-4 w-4" />,
    type: 'logic',
    category: 'Logic',
    tags: ['not', 'logic', 'gate']
  },

  // Risk Management - Position Level
  {
    id: 'position-sizing',
    name: 'Position Sizing',
    description: 'Calculate optimal position size',
    icon: <Settings className="h-4 w-4" />,
    type: 'risk',
    category: 'Position Risk',
    tags: ['position', 'size', 'calculation']
  },
  {
    id: 'stop-loss-management',
    name: 'Stop Loss Management',
    description: 'Advanced stop loss controls',
    icon: <Shield className="h-4 w-4" />,
    type: 'risk',
    category: 'Position Risk',
    tags: ['stop', 'loss', 'management']
  },
  {
    id: 'position-limits',
    name: 'Position Limits',
    description: 'Set position time and size limits',
    icon: <Timer className="h-4 w-4" />,
    type: 'risk',
    category: 'Position Risk',
    tags: ['position', 'limits', 'time']
  },

  // Risk Management - Portfolio Level
  {
    id: 'portfolio-heat',
    name: 'Portfolio Heat',
    description: 'Monitor portfolio risk exposure',
    icon: <Activity className="h-4 w-4" />,
    type: 'risk',
    category: 'Portfolio Risk',
    tags: ['portfolio', 'heat', 'exposure']
  },
  {
    id: 'correlation-control',
    name: 'Correlation Control',
    description: 'Manage position correlations',
    icon: <GitBranch className="h-4 w-4" />,
    type: 'risk',
    category: 'Portfolio Risk',
    tags: ['correlation', 'diversification']
  },
  {
    id: 'concentration-limits',
    name: 'Concentration Limits',
    description: 'Prevent over-concentration',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'risk',
    category: 'Portfolio Risk',
    tags: ['concentration', 'limits', 'diversification']
  },

  // Risk Management - Market Risk
  {
    id: 'volatility-filter',
    name: 'Volatility Filter',
    description: 'Filter trades by volatility',
    icon: <Activity className="h-4 w-4" />,
    type: 'risk',
    category: 'Market Risk',
    tags: ['volatility', 'filter', 'market']
  },
  {
    id: 'liquidity-check',
    name: 'Liquidity Check',
    description: 'Ensure adequate liquidity',
    icon: <Activity className="h-4 w-4" />,
    type: 'risk',
    category: 'Market Risk',
    tags: ['liquidity', 'check', 'volume']
  },

  // Risk Management - Drawdown Protection
  {
    id: 'drawdown-protection',
    name: 'Drawdown Protection',
    description: 'Protect against large drawdowns',
    icon: <Shield className="h-4 w-4" />,
    type: 'risk',
    category: 'Drawdown Protection',
    tags: ['drawdown', 'protection', 'limits']
  },
  {
    id: 'emergency-controls',
    name: 'Emergency Controls',
    description: 'Emergency risk management',
    icon: <AlertTriangle className="h-4 w-4" />,
    type: 'risk',
    category: 'Drawdown Protection',
    tags: ['emergency', 'controls', 'protection']
  },

  // Output Nodes
  {
    id: 'output-display',
    name: 'Output Display',
    description: 'Display strategy results',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'output',
    category: 'Output',
    tags: ['output', 'display', 'results']
  }
];

const groupedComponents = componentLibrary.reduce((acc, component) => {
  if (!acc[component.category]) {
    acc[component.category] = [];
  }
  acc[component.category].push(component);
  return acc;
}, {} as Record<string, ComponentItem[]>);

export function ComponentLibrary() {
  const [draggedItem, setDraggedItem] = React.useState<string | null>(null);

  const onDragStart = (event: React.DragEvent, nodeType: string, label: string) => {
    console.log('🚀 Drag start:', { nodeType, label }); // Debug log
    
    // Set data with multiple formats for compatibility
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.setData('application/reactflow-label', label);
    event.dataTransfer.setData('text/plain', nodeType); // Fallback
    
    // Set effect allowed
    event.dataTransfer.effectAllowed = 'move';
    
    setDraggedItem(nodeType);
  };

  const onDragEnd = (event: React.DragEvent) => {
    console.log('Drag end:', { dropEffect: event.dataTransfer.dropEffect }); // Debug log
    setDraggedItem(null);
  };

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4 dark:bg-background">
      <div className="space-y-2">
        <h2 className="text-lg font-semibold dark:text-foreground">Component Library</h2>
        <p className="text-sm text-muted-foreground">
          Drag components to the canvas to build your strategy
        </p>
      </div>

      <Accordion type="multiple" defaultValue={Object.keys(groupedComponents)} className="w-full">
        {Object.entries(groupedComponents).map(([category, components]) => (
          <AccordionItem key={category} value={category}>
            <AccordionTrigger className="text-sm font-medium">
              {category} ({components.length})
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-2">
                {components.map((component) => (
                  <Card
                    key={component.id}
                    className={`cursor-grab active:cursor-grabbing hover:shadow-md transition-all dark:bg-card dark:border-border ${
                      draggedItem === component.type ? 'opacity-50 scale-95' : 'hover:scale-[1.02]'
                    }`}
                    draggable={true}
                    onDragStart={(e) => onDragStart(e, component.type, component.name)}
                    onDragEnd={onDragEnd}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 mt-1">
                          {component.icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium truncate">
                            {component.name}
                          </h4>
                          <p className="text-xs text-muted-foreground mt-1">
                            {component.description}
                          </p>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {component.tags.slice(0, 2).map((tag) => (
                              <Badge
                                key={tag}
                                variant="secondary"
                                className="text-xs px-1 py-0"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}