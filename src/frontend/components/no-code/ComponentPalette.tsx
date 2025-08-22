// Component Palette for Workflow Builder
// Provides drag-and-drop components for building trading strategies

import React, { useState } from 'react';
import { useComponents } from '../../lib/hooks/use-no-code';

interface ComponentItem {
  id: string;
  type: string;
  label: string;
  description: string;
  category: string;
  icon: string;
  color: string;
}

// Built-in component definitions
const BUILTIN_COMPONENTS: ComponentItem[] = [
  // Data Sources
  {
    id: 'data-source-market',
    type: 'dataSource',
    label: 'Market Data',
    description: 'Real-time market price data',
    category: 'Data Sources',
    icon: '📊',
    color: 'bg-blue-500',
  },
  {
    id: 'data-source-orderbook',
    type: 'dataSource', 
    label: 'Order Book',
    description: 'Market depth and liquidity data',
    category: 'Data Sources',
    icon: '📈',
    color: 'bg-blue-500',
  },

  // Technical Indicators
  {
    id: 'indicator-sma',
    type: 'technicalIndicator',
    label: 'Simple Moving Average',
    description: 'Average price over a period',
    category: 'Technical Indicators',
    icon: '📈',
    color: 'bg-green-500',
  },
  {
    id: 'indicator-ema',
    type: 'technicalIndicator',
    label: 'Exponential Moving Average',
    description: 'Weighted average favoring recent prices',
    category: 'Technical Indicators',
    icon: '📈',
    color: 'bg-green-500',
  },
  {
    id: 'indicator-rsi',
    type: 'technicalIndicator',
    label: 'RSI',
    description: 'Relative Strength Index momentum oscillator',
    category: 'Technical Indicators',
    icon: '🔄',
    color: 'bg-green-500',
  },
  {
    id: 'indicator-macd',
    type: 'technicalIndicator',
    label: 'MACD',
    description: 'Moving Average Convergence Divergence',
    category: 'Technical Indicators',
    icon: '〰️',
    color: 'bg-green-500',
  },
  {
    id: 'indicator-bollinger',
    type: 'technicalIndicator',
    label: 'Bollinger Bands',
    description: 'Volatility indicator with upper/lower bands',
    category: 'Technical Indicators',
    icon: '📏',
    color: 'bg-green-500',
  },

  // Conditions
  {
    id: 'condition-price-above',
    type: 'condition',
    label: 'Price Above',
    description: 'Check if price is above a value',
    category: 'Conditions',
    icon: '⬆️',
    color: 'bg-yellow-500',
  },
  {
    id: 'condition-price-below',
    type: 'condition',
    label: 'Price Below', 
    description: 'Check if price is below a value',
    category: 'Conditions',
    icon: '⬇️',
    color: 'bg-yellow-500',
  },
  {
    id: 'condition-crossover',
    type: 'condition',
    label: 'Crossover',
    description: 'Detect when one line crosses above another',
    category: 'Conditions',
    icon: '✂️',
    color: 'bg-yellow-500',
  },
  {
    id: 'condition-and',
    type: 'condition',
    label: 'AND Logic',
    description: 'Combine multiple conditions with AND',
    category: 'Conditions',
    icon: '&',
    color: 'bg-yellow-500',
  },
  {
    id: 'condition-or',
    type: 'condition',
    label: 'OR Logic',
    description: 'Combine multiple conditions with OR',
    category: 'Conditions',
    icon: '|',
    color: 'bg-yellow-500',
  },

  // Actions
  {
    id: 'action-buy',
    type: 'action',
    label: 'Buy Order',
    description: 'Execute a buy order',
    category: 'Actions',
    icon: '💰',
    color: 'bg-emerald-500',
  },
  {
    id: 'action-sell',
    type: 'action',
    label: 'Sell Order',
    description: 'Execute a sell order',
    category: 'Actions',
    icon: '💸',
    color: 'bg-red-500',
  },
  {
    id: 'action-close-position',
    type: 'action',
    label: 'Close Position',
    description: 'Close an existing position',
    category: 'Actions',
    icon: '🔒',
    color: 'bg-gray-500',
  },
  {
    id: 'action-set-stop-loss',
    type: 'action',
    label: 'Set Stop Loss',
    description: 'Set a stop loss order',
    category: 'Actions',
    icon: '🛡️',
    color: 'bg-red-400',
  },
  {
    id: 'action-set-take-profit',
    type: 'action',
    label: 'Set Take Profit',
    description: 'Set a take profit order',
    category: 'Actions',
    icon: '🎯',
    color: 'bg-green-400',
  },

  // Risk Management
  {
    id: 'risk-position-size',
    type: 'riskManagement',
    label: 'Position Sizing',
    description: 'Calculate optimal position size',
    category: 'Risk Management',
    icon: '⚖️',
    color: 'bg-purple-500',
  },
  {
    id: 'risk-portfolio-heat',
    type: 'riskManagement',
    label: 'Portfolio Heat',
    description: 'Monitor overall portfolio risk',
    category: 'Risk Management',
    icon: '🌡️',
    color: 'bg-purple-500',
  },
  {
    id: 'risk-max-drawdown',
    type: 'riskManagement',
    label: 'Max Drawdown',
    description: 'Limit maximum portfolio drawdown',
    category: 'Risk Management',
    icon: '📉',
    color: 'bg-purple-500',
  },

  // Output
  {
    id: 'output-signal',
    type: 'output',
    label: 'Trading Signal',
    description: 'Output trading signal',
    category: 'Outputs',
    icon: '📡',
    color: 'bg-indigo-500',
  },
  {
    id: 'output-log',
    type: 'output',
    label: 'Log Message',
    description: 'Log a message for debugging',
    category: 'Outputs',
    icon: '📝',
    color: 'bg-gray-500',
  },

  // Advanced Nodes
  {
    id: 'advanced-market-regime',
    type: 'marketRegimeDetection',
    label: 'Market Regime Detection',
    description: 'Detect trend, sideways, or volatile market regimes',
    category: 'Advanced Nodes',
    icon: '👁️',
    color: 'bg-purple-600',
  },
  {
    id: 'advanced-multi-timeframe',
    type: 'multiTimeframeAnalysis',
    label: 'Multi-Timeframe Analysis',
    description: 'Analyze multiple timeframes simultaneously',
    category: 'Advanced Nodes',
    icon: '🕒',
    color: 'bg-cyan-600',
  },
  {
    id: 'advanced-correlation',
    type: 'correlationAnalysis',
    label: 'Correlation Analysis',
    description: 'Analyze correlation between different assets',
    category: 'Advanced Nodes',
    icon: '🔗',
    color: 'bg-orange-600',
  },
  {
    id: 'advanced-sentiment',
    type: 'sentimentAnalysis',
    label: 'Sentiment Analysis',
    description: 'Analyze market sentiment from news and social media',
    category: 'Advanced Nodes',
    icon: '💬',
    color: 'bg-teal-600',
  },
];

interface ComponentPaletteProps {
  onComponentSelect?: (component: ComponentItem) => void;
}

export const ComponentPalette: React.FC<ComponentPaletteProps> = ({
  onComponentSelect,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['Technical Indicators', 'Conditions', 'Actions'])
  );

  // Get components from API (fallback to built-in if API unavailable)
  const { data: apiComponents, isLoading } = useComponents();
  const components = apiComponents?.length ? 
    apiComponents.map(comp => ({
      id: comp.uuid,
      type: comp.component_type,
      label: comp.display_name,
      description: comp.description || '',
      category: comp.category,
      icon: comp.icon || '🔧',
      color: 'bg-gray-500',
    })) : 
    BUILTIN_COMPONENTS;

  // Filter components
  const filteredComponents = components.filter(component => {
    const matchesSearch = component.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         component.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || component.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Group components by category
  const componentsByCategory = filteredComponents.reduce((acc, component) => {
    if (!acc[component.category]) {
      acc[component.category] = [];
    }
    acc[component.category].push(component);
    return acc;
  }, {} as Record<string, ComponentItem[]>);

  const categories = Object.keys(componentsByCategory).sort();
  const allCategories = ['all', ...new Set(components.map(c => c.category))];

  // Handle drag start
  const onDragStart = (event: React.DragEvent, component: ComponentItem) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(component));
    event.dataTransfer.effectAllowed = 'move';
  };

  // Toggle category expansion
  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Component Palette</h3>
        
        {/* Search */}
        <div className="relative mb-3">
          <input
            type="text"
            placeholder="Search components..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* Category Filter */}
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {allCategories.map(category => (
            <option key={category} value={category}>
              {category === 'all' ? 'All Categories' : category}
            </option>
          ))}
        </select>
      </div>

      {/* Components List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-500">
            Loading components...
          </div>
        ) : categories.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            No components found
          </div>
        ) : (
          <div className="space-y-1">
            {categories.map(category => (
              <div key={category}>
                {/* Category Header */}
                <button
                  onClick={() => toggleCategory(category)}
                  className="w-full px-4 py-2 text-left text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center justify-between"
                >
                  <span>{category}</span>
                  <svg
                    className={`h-4 w-4 transform transition-transform ${
                      expandedCategories.has(category) ? 'rotate-90' : ''
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                {/* Category Components */}
                {expandedCategories.has(category) && (
                  <div className="space-y-1 pb-2">
                    {componentsByCategory[category].map(component => (
                      <div
                        key={component.id}
                        draggable
                        onDragStart={(event) => onDragStart(event, component)}
                        onClick={() => onComponentSelect?.(component)}
                        className="mx-2 p-3 bg-white border border-gray-200 rounded-lg cursor-move hover:shadow-md transition-shadow group"
                      >
                        <div className="flex items-start space-x-3">
                          <div className={`w-8 h-8 ${component.color} rounded-lg flex items-center justify-center text-white text-sm flex-shrink-0`}>
                            {component.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                              {component.label}
                            </h4>
                            <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                              {component.description}
                            </p>
                          </div>
                        </div>
                        
                        {/* Drag Indicator */}
                        <div className="mt-2 flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                          <div className="text-xs text-gray-400 flex items-center space-x-1">
                            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                            </svg>
                            <span>Drag to canvas</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-500 space-y-1">
          <div>💡 Drag components to the canvas</div>
          <div>🔗 Connect components with edges</div>
          <div>⚙️ Configure properties in the panel</div>
        </div>
      </div>
    </div>
  );
};

export default ComponentPalette;