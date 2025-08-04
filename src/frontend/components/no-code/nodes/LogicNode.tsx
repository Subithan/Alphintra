import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { GitBranch } from 'lucide-react';
import { useNoCodeStore } from '@/lib/stores/no-code-store';
import { shallow } from 'zustand/shallow';

interface LogicNodeData {
  label: string;
  parameters: {
    operation?: string;
    inputs?: number;
  };
}

export function LogicNode({ id, selected }: NodeProps<LogicNodeData>) {
  // Get the node data directly from the store and subscribe to updates
  const { data } = useNoCodeStore(
    (state) => {
      const node = state.currentWorkflow?.nodes.find(n => n.id === id);
      return { 
        data: node?.data || { label: 'Node', parameters: {} }
      };
    },
    shallow
  );

  const { label, parameters } = data;
  const operation = parameters?.operation || 'AND';
  const inputs = parameters?.inputs || 2;

  const getOperationSymbol = (op: string) => {
    switch (op) {
      case 'AND': return '&';
      case 'OR': return '|';
      case 'NOT': return '!';
      case 'XOR': return '⊕';
      default: return '&';
    }
  };

  const getOperationColor = (op: string) => {
    switch (op) {
      case 'AND': return 'text-blue-600 dark:text-blue-400';
      case 'OR': return 'text-green-600 dark:text-green-400';
      case 'NOT': return 'text-red-600 dark:text-red-400';
      case 'XOR': return 'text-purple-600 dark:text-purple-400';
      default: return 'text-blue-600 dark:text-blue-400';
    }
  };

  return (
    <Card variant="glass" className={`min-w-[140px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`} suppressHydrationWarning>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          <GitBranch className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
          <span className="font-medium text-sm dark:text-foreground">{label}</span>
        </div>
        
        <div className="space-y-1">
          <Badge variant="outline" className="text-xs">
            <span className={`font-bold ${getOperationColor(operation)}`}>
              {getOperationSymbol(operation)}
            </span>
            <span className="ml-1">{operation}</span>
          </Badge>
          <div className="text-xs text-muted-foreground">
            {inputs} inputs
          </div>
        </div>

        {/* Input Handles - dynamic based on input count */}
        {Array.from({ length: inputs }, (_, i) => (
          <Handle
            key={`input-${i}`}
            type="target"
            position={Position.Left}
            id={`input-${i}`}
            className="w-3 h-3 bg-blue-500"
            style={{ 
              left: -6, 
              top: `${30 + (i * 20)}%`
            }}
          />
        ))}

        {/* Output Handle */}
        <Handle
          type="source"
          position={Position.Right}
          id="output"
          className="w-3 h-3 bg-green-500"
          style={{ right: -6 }}
        />
      </CardContent>
    </Card>
  );
}