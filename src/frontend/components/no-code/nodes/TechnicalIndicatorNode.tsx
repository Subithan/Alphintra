import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { TrendingUp, Activity, BarChart3, Volume2, Zap } from 'lucide-react';
import { useNoCodeStore } from '@/lib/stores/no-code-store';
import { shallow } from 'zustand/shallow';

interface TechnicalIndicatorNodeData {
  label: string;
  parameters: {
    indicatorCategory?: string;
    indicator?: string;
    period?: number;
    source?: string;
    fastPeriod?: number;
    slowPeriod?: number;
    outputType?: string;
    enableMultiOutput?: boolean;
    outputConfiguration?: {
      main: boolean;
      signal: boolean;
      upper?: boolean;
      lower?: boolean;
      histogram?: boolean;
    };
  };
}

export function TechnicalIndicatorNode({ id, selected }: NodeProps<TechnicalIndicatorNodeData>) {
  // Get the node data directly from the store and subscribe to updates
  const { data } = useNoCodeStore(
    (state) => {
      const node = state.currentWorkflow?.nodes.find(n => n.id === id);
      return { 
        data: node?.data || { label: 'Technical Indicator', parameters: {} }
      };
    },
    shallow
  );

  const { label, parameters } = data;
  const indicatorCategory = parameters?.indicatorCategory || 'trend';
  const indicator = parameters?.indicator || 'SMA';
  const period = parameters?.period || 20;
  const fastPeriod = parameters?.fastPeriod;
  const slowPeriod = parameters?.slowPeriod;
  const outputType = parameters?.outputType;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'trend': return <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />;
      case 'momentum': return <Zap className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />;
      case 'volatility': return <Activity className="h-4 w-4 text-red-600 dark:text-red-400" />;
      case 'volume': return <Volume2 className="h-4 w-4 text-green-600 dark:text-green-400" />;
      case 'oscillators': return <BarChart3 className="h-4 w-4 text-purple-600 dark:text-purple-400" />;
      default: return <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'trend': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'momentum': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'volatility': return 'bg-red-100 text-red-800 border-red-300';
      case 'volume': return 'bg-green-100 text-green-800 border-green-300';
      case 'oscillators': return 'bg-purple-100 text-purple-800 border-purple-300';
      default: return 'bg-blue-100 text-blue-800 border-blue-300';
    }
  };

  const getPeriodDisplay = () => {
    if (fastPeriod && slowPeriod) {
      return `${fastPeriod}/${slowPeriod}`;
    }
    if (period) {
      return period.toString();
    }
    return '';
  };

  // Get available outputs based on indicator type
  const getAvailableOutputs = () => {
    const indicator = parameters?.indicator || 'SMA';
    const outputs = [];

    switch (indicator) {
      case 'BB': // Bollinger Bands
        outputs.push(
          { label: 'Upper', color: 'bg-red-500' },
          { label: 'Middle', color: 'bg-blue-500' },
          { label: 'Lower', color: 'bg-green-500' },
          { label: 'Width', color: 'bg-purple-500' }
        );
        break;
      case 'MACD':
        outputs.push(
          { label: 'MACD', color: 'bg-blue-500' },
          { label: 'Signal', color: 'bg-green-500' },
          { label: 'Histogram', color: 'bg-orange-500' }
        );
        break;
      case 'STOCH': // Stochastic
      case 'Stochastic':
        outputs.push(
          { label: '%K', color: 'bg-blue-500' },
          { label: '%D', color: 'bg-green-500' }
        );
        break;
      case 'ADX':
        outputs.push(
          { label: 'ADX', color: 'bg-blue-500' },
          { label: 'DI+', color: 'bg-green-500' },
          { label: 'DI-', color: 'bg-red-500' }
        );
        break;
      case 'KC': // Keltner Channels
        outputs.push(
          { label: 'Upper', color: 'bg-red-500' },
          { label: 'Middle', color: 'bg-blue-500' },
          { label: 'Lower', color: 'bg-green-500' }
        );
        break;
      case 'DC': // Donchian Channels
        outputs.push(
          { label: 'Upper', color: 'bg-red-500' },
          { label: 'Middle', color: 'bg-blue-500' },
          { label: 'Lower', color: 'bg-green-500' }
        );
        break;
      case 'AROON':
        outputs.push(
          { label: 'Aroon Up', color: 'bg-green-500' },
          { label: 'Aroon Down', color: 'bg-red-500' }
        );
        break;
      case 'STOCHRSI': // Stochastic RSI
        outputs.push(
          { label: '%K', color: 'bg-blue-500' },
          { label: '%D', color: 'bg-green-500' }
        );
        break;
      case 'DMI': // Directional Movement Index
        outputs.push(
          { label: 'DMI+', color: 'bg-green-500' },
          { label: 'DMI-', color: 'bg-red-500' },
          { label: 'ADX', color: 'bg-blue-500' }
        );
        break;
      case 'PPO': // Percentage Price Oscillator
        outputs.push(
          { label: 'PPO', color: 'bg-blue-500' },
          { label: 'Signal', color: 'bg-green-500' },
          { label: 'Histogram', color: 'bg-orange-500' }
        );
        break;
      case 'TSI': // True Strength Index
        outputs.push(
          { label: 'TSI', color: 'bg-blue-500' },
          { label: 'Signal', color: 'bg-green-500' }
        );
        break;
      case 'KDJ':
        outputs.push(
          { label: '%K', color: 'bg-blue-500' },
          { label: '%D', color: 'bg-green-500' },
          { label: '%J', color: 'bg-orange-500' }
        );
        break;
      case 'VORTEX':
        outputs.push(
          { label: 'VI+', color: 'bg-green-500' },
          { label: 'VI-', color: 'bg-red-500' }
        );
        break;
      case 'Ichimoku':
        outputs.push(
          { label: 'Tenkan', color: 'bg-blue-500' },
          { label: 'Kijun', color: 'bg-red-500' },
          { label: 'Senkou A', color: 'bg-green-500' },
          { label: 'Senkou B', color: 'bg-purple-500' },
          { label: 'Chikou', color: 'bg-yellow-500' },
        );
        break;
      case 'VolumeProfile':
        outputs.push(
          { label: 'POC', color: 'bg-blue-500' },
          { label: 'VAH', color: 'bg-green-500' },
          { label: 'VAL', color: 'bg-red-500' },
        );
        break;
      case 'MarketStructure':
        outputs.push(
          { label: 'Higher High', color: 'bg-green-500' },
          { label: 'Lower Low', color: 'bg-red-500' },
          { label: 'Support', color: 'bg-blue-500' },
          { label: 'Resistance', color: 'bg-purple-500' },
        );
        break;
      default:
        outputs.push(
          { label: 'Value', color: 'bg-blue-500' },
          { label: 'Signal', color: 'bg-green-500' }
        );
    }

    return outputs;
  };

  const availableOutputs = getAvailableOutputs();
  const outputPositions = [20, 35, 50, 65, 80];

  return (
    <Card 
      className={`min-w-[200px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`} 
      suppressHydrationWarning
    >
      <CardContent className="p-3 relative">
        <div className="flex items-center space-x-2 mb-2">
          {getCategoryIcon(indicatorCategory)}
          <span className="font-medium text-sm dark:text-foreground">{label}</span>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <Badge variant="default" className="text-xs font-semibold">
              {indicator}
            </Badge>
            {outputType && outputType !== 'main' && (
              <Badge variant="outline" className="text-xs">
                {outputType}
              </Badge>
            )}
          </div>
          
          <div className={`text-xs px-1.5 py-0.5 rounded border ${getCategoryColor(indicatorCategory)}`}>
            {indicatorCategory.toUpperCase()}
          </div>
          
          {getPeriodDisplay() && (
            <div className="text-xs text-muted-foreground">
              Period: {getPeriodDisplay()}
            </div>
          )}
        </div>

        {/* Input Handle */}
        <Handle
          type="target"
          position={Position.Left}
          id="data-input"
          className="w-3 h-3 bg-gray-400"
          style={{ left: -6 }}
        />

        {/* 5 Static Output Handles */}
        {outputPositions.map((top, index) => {
          const output = availableOutputs[index];
          return (
            <React.Fragment key={index}>
              <Handle
                type="source"
                position={Position.Right}
                id={`output-${index + 1}`}
                className={`w-3 h-3 ${output ? output.color : 'opacity-0 pointer-events-none'}`}
                style={{
                  right: -6,
                  top: `${top}%`
                }}
              />
              <div
                className={`absolute text-xs font-medium text-gray-600 dark:text-gray-300 pointer-events-none ${output ? '' : 'opacity-0'}`}
                style={{
                  right: 12,
                  top: `calc(${top}% - 8px)`,
                  fontSize: '10px'
                }}
              >
                {output ? output.label : ''}
              </div>
            </React.Fragment>
          );
        })}
      </CardContent>
    </Card>
  );
}