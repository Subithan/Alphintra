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

  // Technical Indicators
  {
    id: 'sma',
    name: 'Simple Moving Average',
    description: 'Calculate simple moving average',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Technical Indicators',
    tags: ['sma', 'trend', 'moving average']
  },
  {
    id: 'ema',
    name: 'Exponential Moving Average',
    description: 'Calculate exponential moving average',
    icon: <TrendingUp className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Technical Indicators',
    tags: ['ema', 'trend', 'moving average']
  },
  {
    id: 'rsi',
    name: 'RSI',
    description: 'Relative Strength Index oscillator',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Technical Indicators',
    tags: ['rsi', 'oscillator', 'momentum']
  },
  {
    id: 'macd',
    name: 'MACD',
    description: 'Moving Average Convergence Divergence',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Technical Indicators',
    tags: ['macd', 'momentum', 'divergence']
  },
  {
    id: 'bollinger',
    name: 'Bollinger Bands',
    description: 'Volatility bands around moving average',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Technical Indicators',
    tags: ['bollinger', 'volatility', 'bands']
  },
  {
    id: 'stochastic',
    name: 'Stochastic',
    description: 'Stochastic momentum oscillator',
    icon: <BarChart3 className="h-4 w-4" />,
    type: 'technicalIndicator',
    category: 'Technical Indicators',
    tags: ['stochastic', 'momentum', 'oscillator']
  },

  // Conditions
  {
    id: 'price-condition',
    name: 'Price Condition',
    description: 'Compare price values',
    icon: <Target className="h-4 w-4" />,
    type: 'condition',
    category: 'Conditions',
    tags: ['price', 'comparison', 'condition']
  },
  {
    id: 'indicator-condition',
    name: 'Indicator Condition',
    description: 'Compare indicator values',
    icon: <Target className="h-4 w-4" />,
    type: 'condition',
    category: 'Conditions',
    tags: ['indicator', 'comparison', 'condition']
  },
  {
    id: 'crossover',
    name: 'Crossover',
    description: 'Detect line crossovers',
    icon: <GitBranch className="h-4 w-4" />,
    type: 'condition',
    category: 'Conditions',
    tags: ['crossover', 'intersection', 'signal']
  },
  {
    id: 'time-condition',
    name: 'Time Condition',
    description: 'Time-based conditions',
    icon: <Timer className="h-4 w-4" />,
    type: 'condition',
    category: 'Conditions',
    tags: ['time', 'schedule', 'condition']
  },

  // Actions
  {
    id: 'buy-order',
    name: 'Buy Order',
    description: 'Execute buy order',
    icon: <Zap className="h-4 w-4 text-green-600" />,
    type: 'action',
    category: 'Trading Actions',
    tags: ['buy', 'order', 'long']
  },
  {
    id: 'sell-order',
    name: 'Sell Order',
    description: 'Execute sell order',
    icon: <Zap className="h-4 w-4 text-red-600" />,
    type: 'action',
    category: 'Trading Actions',
    tags: ['sell', 'order', 'short']
  },
  {
    id: 'stop-loss',
    name: 'Stop Loss',
    description: 'Set stop loss order',
    icon: <Shield className="h-4 w-4" />,
    type: 'action',
    category: 'Risk Management',
    tags: ['stop', 'loss', 'risk']
  },
  {
    id: 'take-profit',
    name: 'Take Profit',
    description: 'Set take profit order',
    icon: <DollarSign className="h-4 w-4" />,
    type: 'action',
    category: 'Risk Management',
    tags: ['take', 'profit', 'target']
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

  // Risk Management
  {
    id: 'position-size',
    name: 'Position Sizing',
    description: 'Calculate position size',
    icon: <Settings className="h-4 w-4" />,
    type: 'risk',
    category: 'Risk Management',
    tags: ['position', 'size', 'risk']
  },
  {
    id: 'risk-limit',
    name: 'Risk Limit',
    description: 'Set risk limits',
    icon: <AlertTriangle className="h-4 w-4" />,
    type: 'risk',
    category: 'Risk Management',
    tags: ['risk', 'limit', 'protection']
  },
  {
    id: 'portfolio-heat',
    name: 'Portfolio Heat',
    description: 'Monitor portfolio risk exposure',
    icon: <Activity className="h-4 w-4" />,
    type: 'risk',
    category: 'Risk Management',
    tags: ['portfolio', 'heat', 'exposure']
  },
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