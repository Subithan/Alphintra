import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Zap, ArrowUp, ArrowDown, LogIn, LogOut, Settings, BarChart3 } from 'lucide-react';
import { useNoCodeStore } from '@/lib/stores/no-code-store';
import { shallow } from 'zustand/shallow';

interface ActionNodeData {
  label: string;
  parameters: {
    actionCategory?: string;
    action?: string;
    quantity?: number;
    order_type?: string;
    positionSizing?: string;
    stop_loss?: number;
    take_profit?: number;
  };
}

export function ActionNode({ id, selected }: NodeProps<ActionNodeData>) {
  // Get the node data directly from the store and subscribe to updates
  const { data } = useNoCodeStore(
    (state) => {
      const node = state.currentWorkflow?.nodes.find(n => n.id === id);
      return { 
        data: node?.data || { label: 'Action', parameters: {} }
      };
    },
    shallow
  );

  const { label, parameters } = data;
  const actionCategory = parameters?.actionCategory || 'entry';
  const action = parameters?.action || 'buy';
  const orderType = parameters?.order_type || 'market';
  const positionSizing = parameters?.positionSizing;
  const stopLoss = parameters?.stop_loss;
  const takeProfit = parameters?.take_profit;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'entry': return <LogIn className="h-4 w-4 text-green-600 dark:text-green-400" />;
      case 'exit': return <LogOut className="h-4 w-4 text-red-600 dark:text-red-400" />;
      case 'management': return <Settings className="h-4 w-4 text-blue-600 dark:text-blue-400" />;
      case 'portfolio': return <BarChart3 className="h-4 w-4 text-purple-600 dark:text-purple-400" />;
      default: return <Zap className="h-4 w-4 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'entry':
        return 'bg-green-100 text-green-800 dark:text-green-200 border-green-300';
      case 'exit':
        return 'bg-red-100 text-red-800 dark:text-red-200 border-red-300';
      case 'management':
        return 'bg-blue-100 text-blue-800 dark:text-blue-200 border-blue-300';
      case 'portfolio':
        return 'bg-purple-100 text-purple-800 dark:text-purple-200 border-purple-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-300';
    }
  };

  const getActionIcon = (action: string) => {
    if (action.includes('buy') || action === 'long') {
      return <ArrowUp className="h-3 w-3 text-green-600" />;
    }
    if (action.includes('sell') || action === 'short') {
      return <ArrowDown className="h-3 w-3 text-red-600" />;
    }
    return <Zap className="h-3 w-3 text-blue-600" />;
  };

  const getRiskRewardDisplay = () => {
    if (stopLoss && takeProfit) {
      const ratio = (takeProfit / stopLoss).toFixed(1);
      return `R:R ${ratio}:1`;
    }
    return null;
  };

  return (
    <Card
      variant="glass"
      className={`min-w-[200px] node-glow ${selected ? 'ring-2 ring-blue-500' : ''}`}
      suppressHydrationWarning
    >
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          {getCategoryIcon(actionCategory)}
          <span className="font-medium text-sm text-foreground">{label}</span>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <Badge variant="default" className="glass-badge text-xs font-semibold">
              {getActionIcon(action)}
              <span className="ml-1">{action.replace('_', ' ').toUpperCase()}</span>
            </Badge>
            {positionSizing && (
              <Badge variant="outline" className="glass-badge text-xs">
                {positionSizing}
              </Badge>
            )}
          </div>

          <div className={`text-xs px-1.5 py-0.5 rounded border glass-badge ${getCategoryColor(actionCategory)}`}>
            {actionCategory.toUpperCase()}
          </div>
          
          <div className="text-xs text-muted-foreground">
            {orderType} • {getRiskRewardDisplay() || 'No R:R set'}
          </div>
        </div>

        {/* Input Handle */}
        <Handle
          type="target"
          position={Position.Left}
          id="signal-input"
          className="w-3 h-3 bg-green-500"
          style={{ left: -6 }}
        />

        {/* No output handle for action nodes - they are terminal */}
      </CardContent>
    </Card>
  );
}