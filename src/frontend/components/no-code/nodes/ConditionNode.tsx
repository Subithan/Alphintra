import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Target, TrendingUp, GitMerge, Activity, Search, Clock } from 'lucide-react';

interface ConditionNodeData {
  label: string;
  parameters: {
    conditionType?: string;
    condition?: string;
    value?: number;
    value2?: number;
    lookback?: number;
    confirmationBars?: number;
    higherTimeframe?: string;
  };
}

export function ConditionNode({ data, selected }: NodeProps<ConditionNodeData>) {
  const { label, parameters } = data;
  const conditionType = parameters?.conditionType || 'comparison';
  const condition = parameters?.condition || 'greater_than';
  const value = parameters?.value || 0;
  const value2 = parameters?.value2;
  const confirmationBars = parameters?.confirmationBars;
  const higherTimeframe = parameters?.higherTimeframe;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'comparison': return <Target className="h-4 w-4 text-orange-600 dark:text-orange-400" />;
      case 'crossover': return <GitMerge className="h-4 w-4 text-blue-600 dark:text-blue-400" />;
      case 'trend': return <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />;
      case 'pattern': return <Search className="h-4 w-4 text-purple-600 dark:text-purple-400" />;
      case 'timeframe': return <Clock className="h-4 w-4 text-red-600 dark:text-red-400" />;
      default: return <Target className="h-4 w-4 text-orange-600 dark:text-orange-400" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'comparison': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'crossover': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'trend': return 'bg-green-100 text-green-800 border-green-300';
      case 'pattern': return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'timeframe': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-orange-100 text-orange-800 border-orange-300';
    }
  };

  const getConditionDisplay = (condition: string) => {
    switch (condition) {
      case 'greater_than': return '>';
      case 'less_than': return '<';
      case 'equal_to': return '=';
      case 'not_equal': return '!=';
      case 'greater_equal': return '>=';
      case 'less_equal': return '<=';
      case 'crossover': return '↗';
      case 'crossunder': return '↘';
      case 'golden_cross': return '🥇';
      case 'death_cross': return '💀';
      case 'rising': return '📈';
      case 'falling': return '📉';
      case 'range': return '⬌';
      case 'outside_range': return '⬆⬇';
      case 'breakout_up': return '🚀';
      case 'breakout_down': return '⬇️';
      case 'oversold': return '📉';
      case 'overbought': return '📈';
      default: return '?';
    }
  };

  const getValueDisplay = () => {
    if (value2 !== undefined && ['range', 'outside_range'].includes(condition)) {
      return `${value}-${value2}`;
    }
    if (higherTimeframe && conditionType === 'timeframe') {
      return higherTimeframe;
    }
    if (condition === 'percentage_change') {
      return `${value}%`;
    }
    return value !== undefined ? value.toString() : '';
  };

  return (
    <Card className={`min-w-[200px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`} suppressHydrationWarning>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          {getCategoryIcon(conditionType)}
          <span className="font-medium text-sm dark:text-foreground">{label}</span>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <Badge variant="default" className="text-xs font-semibold">
              {getConditionDisplay(condition)} {getValueDisplay()}
            </Badge>
            {confirmationBars && confirmationBars > 0 && (
              <Badge variant="outline" className="text-xs">
                {confirmationBars}b
              </Badge>
            )}
          </div>
          
          <div className={`text-xs px-1.5 py-0.5 rounded border ${getCategoryColor(conditionType)}`}>
            {conditionType.toUpperCase()}
          </div>
          
          <div className="text-xs text-muted-foreground">
            {condition.replace(/_/g, ' ')}
          </div>
        </div>

        {/* Input Handles */}
        <Handle
          type="target"
          position={Position.Left}
          id="data-input"
          className="w-3 h-3 bg-gray-400"
          style={{ left: -6, top: '30%' }}
        />
        <Handle
          type="target"
          position={Position.Left}
          id="value-input"
          className="w-3 h-3 bg-blue-500"
          style={{ left: -6, top: '70%' }}
        />

        {/* Output Handle */}
        <Handle
          type="source"
          position={Position.Right}
          id="signal-output"
          className="w-3 h-3 bg-green-500"
          style={{ right: -6 }}
        />
      </CardContent>
    </Card>
  );
}