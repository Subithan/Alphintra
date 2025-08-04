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
      case 'trend':
        return 'bg-blue-100 text-blue-800 dark:text-blue-200 border-blue-300';
      case 'momentum':
        return 'bg-yellow-100 text-yellow-800 dark:text-yellow-200 border-yellow-300';
      case 'volatility':
        return 'bg-red-100 text-red-800 dark:text-red-200 border-red-300';
      case 'volume':
        return 'bg-green-100 text-green-800 dark:text-green-200 border-green-300';
      case 'oscillators':
        return 'bg-purple-100 text-purple-800 dark:text-purple-200 border-purple-300';
      default:
        return 'bg-blue-100 text-blue-800 dark:text-blue-200 border-blue-300';
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
          { id: 'upper', label: 'Upper', color: 'bg-red-500', position: 20 },
          { id: 'middle', label: 'Middle', color: 'bg-blue-500', position: 40 },
          { id: 'lower', label: 'Lower', color: 'bg-green-500', position: 60 },
          { id: 'width', label: 'Width', color: 'bg-purple-500', position: 80 }
        );
        break;
      case 'MACD':
        outputs.push(
          { id: 'macd', label: 'MACD', color: 'bg-blue-500', position: 25 },
          { id: 'signal', label: 'Signal', color: 'bg-green-500', position: 50 },
          { id: 'histogram', label: 'Histogram', color: 'bg-orange-500', position: 75 }
        );
        break;
      case 'STOCH': // Stochastic
      case 'Stochastic':
        outputs.push(
          { id: 'k', label: '%K', color: 'bg-blue-500', position: 35 },
          { id: 'd', label: '%D', color: 'bg-green-500', position: 65 }
        );
        break;
      case 'ADX':
        outputs.push(
          { id: 'adx', label: 'ADX', color: 'bg-blue-500', position: 25 },
          { id: 'di_plus', label: 'DI+', color: 'bg-green-500', position: 50 },
          { id: 'di_minus', label: 'DI-', color: 'bg-red-500', position: 75 }
        );
        break;
      case 'KC': // Keltner Channels
        outputs.push(
          { id: 'upper', label: 'Upper', color: 'bg-red-500', position: 25 },
          { id: 'middle', label: 'Middle', color: 'bg-blue-500', position: 50 },
          { id: 'lower', label: 'Lower', color: 'bg-green-500', position: 75 }
        );
        break;
      case 'DC': // Donchian Channels
        outputs.push(
          { id: 'upper', label: 'Upper', color: 'bg-red-500', position: 25 },
          { id: 'middle', label: 'Middle', color: 'bg-blue-500', position: 50 },
          { id: 'lower', label: 'Lower', color: 'bg-green-500', position: 75 }
        );
        break;
      case 'AROON':
        outputs.push(
          { id: 'aroon_up', label: 'Aroon Up', color: 'bg-green-500', position: 35 },
          { id: 'aroon_down', label: 'Aroon Down', color: 'bg-red-500', position: 65 }
        );
        break;
      case 'STOCHRSI': // Stochastic RSI
        outputs.push(
          { id: 'k', label: '%K', color: 'bg-blue-500', position: 35 },
          { id: 'd', label: '%D', color: 'bg-green-500', position: 65 }
        );
        break;
      case 'DMI': // Directional Movement Index
        outputs.push(
          { id: 'dmi_plus', label: 'DMI+', color: 'bg-green-500', position: 25 },
          { id: 'dmi_minus', label: 'DMI-', color: 'bg-red-500', position: 50 },
          { id: 'adx', label: 'ADX', color: 'bg-blue-500', position: 75 }
        );
        break;
      case 'PPO': // Percentage Price Oscillator
        outputs.push(
          { id: 'ppo', label: 'PPO', color: 'bg-blue-500', position: 25 },
          { id: 'signal', label: 'Signal', color: 'bg-green-500', position: 50 },
          { id: 'histogram', label: 'Histogram', color: 'bg-orange-500', position: 75 }
        );
        break;
      case 'TSI': // True Strength Index
        outputs.push(
          { id: 'tsi', label: 'TSI', color: 'bg-blue-500', position: 35 },
          { id: 'signal', label: 'Signal', color: 'bg-green-500', position: 65 }
        );
        break;
      case 'KDJ':
        outputs.push(
          { id: 'k', label: '%K', color: 'bg-blue-500', position: 25 },
          { id: 'd', label: '%D', color: 'bg-green-500', position: 50 },
          { id: 'j', label: '%J', color: 'bg-orange-500', position: 75 }
        );
        break;
      case 'VORTEX':
        outputs.push(
          { id: 'vi_plus', label: 'VI+', color: 'bg-green-500', position: 35 },
          { id: 'vi_minus', label: 'VI-', color: 'bg-red-500', position: 65 }
        );
        break;
      default:
        outputs.push(
          { id: 'value', label: 'Value', color: 'bg-blue-500', position: 40 },
          { id: 'signal', label: 'Signal', color: 'bg-green-500', position: 70 }
        );
    }

    return outputs;
  };

  const availableOutputs = getAvailableOutputs();

  return (
    <Card
      variant="glass"
      className={`min-w-[200px] node-glow ${selected ? 'ring-2 ring-blue-500' : ''}`}
      suppressHydrationWarning
    >
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          {getCategoryIcon(indicatorCategory)}
          <span className="font-medium text-sm text-foreground">{label}</span>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <Badge variant="default" className="glass-badge text-xs font-semibold">
              {indicator}
            </Badge>
            {outputType && outputType !== 'main' && (
              <Badge variant="outline" className="glass-badge text-xs">
                {outputType}
              </Badge>
            )}
          </div>

          <div className={`text-xs px-1.5 py-0.5 rounded border glass-badge ${getCategoryColor(indicatorCategory)}`}>
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

        {/* 4 STATIC OUTPUT HANDLES - ALWAYS PRESENT FOR ALL TECHNICAL INDICATORS */}
        
        {/* Output 1 - Always at 25% */}
        <Handle
          type="source"
          position={Position.Right}
          id="output-1"
          className={`w-3 h-3 ${availableOutputs[0] ? availableOutputs[0].color : 'opacity-0 pointer-events-none'}`}
          style={{ 
            right: -6, 
            top: '25%'
          }}
        />
        <div className={`absolute text-xs font-medium text-gray-600 dark:text-gray-300 pointer-events-none ${availableOutputs[0] ? '' : 'opacity-0'}`} 
             style={{ right: -45, top: 'calc(25% - 8px)', fontSize: '10px' }}>
          {availableOutputs[0] ? availableOutputs[0].label : ''}
        </div>
        
        {/* Output 2 - Always at 50% */}
        <Handle
          type="source"
          position={Position.Right}
          id="output-2"
          className={`w-3 h-3 ${availableOutputs[1] ? availableOutputs[1].color : 'opacity-0 pointer-events-none'}`}
          style={{ 
            right: -6, 
            top: '50%'
          }}
        />
        <div className={`absolute text-xs font-medium text-gray-600 dark:text-gray-300 pointer-events-none ${availableOutputs[1] ? '' : 'opacity-0'}`} 
             style={{ right: -45, top: 'calc(50% - 8px)', fontSize: '10px' }}>
          {availableOutputs[1] ? availableOutputs[1].label : ''}
        </div>
        
        {/* Output 3 - Always at 75% */}
        <Handle
          type="source"
          position={Position.Right}
          id="output-3"
          className={`w-3 h-3 ${availableOutputs[2] ? availableOutputs[2].color : 'opacity-0 pointer-events-none'}`}
          style={{ 
            right: -6, 
            top: '75%'
          }}
        />
        <div className={`absolute text-xs font-medium text-gray-600 dark:text-gray-300 pointer-events-none ${availableOutputs[2] ? '' : 'opacity-0'}`} 
             style={{ right: -45, top: 'calc(75% - 8px)', fontSize: '10px' }}>
          {availableOutputs[2] ? availableOutputs[2].label : ''}
        </div>
        
        {/* Output 4 - Always at 90% */}
        <Handle
          type="source"
          position={Position.Right}
          id="output-4"
          className={`w-3 h-3 ${availableOutputs[3] ? availableOutputs[3].color : 'opacity-0 pointer-events-none'}`}
          style={{ 
            right: -6, 
            top: '90%'
          }}
        />
        <div className={`absolute text-xs font-medium text-gray-600 dark:text-gray-300 pointer-events-none ${availableOutputs[3] ? '' : 'opacity-0'}`} 
             style={{ right: -45, top: 'calc(90% - 8px)', fontSize: '10px' }}>
          {availableOutputs[3] ? availableOutputs[3].label : ''}
        </div>
      </CardContent>
    </Card>
  );
}