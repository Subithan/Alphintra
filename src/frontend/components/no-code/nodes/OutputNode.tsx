import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { BarChart3 } from 'lucide-react';
import { useNoCodeStore } from '@/lib/stores/no-code-store';
import { shallow } from 'zustand/shallow';

interface OutputNodeData {
  label: string;
  parameters: {
    output_type?: string;
    format?: string;
  };
}

export function OutputNode({ id, selected }: NodeProps<OutputNodeData>) {
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
  const outputType = parameters?.output_type || 'signals';

  return (
    <Card variant="glass" className={`min-w-[160px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`} suppressHydrationWarning>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          <BarChart3 className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
          <span className="font-medium text-sm dark:text-foreground">{label}</span>
        </div>
        
        <div className="space-y-1">
          <Badge variant="outline" className="text-xs">
            {outputType}
          </Badge>
          <div className="text-xs text-muted-foreground">
            Strategy output
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
          id="signal-input"
          className="w-3 h-3 bg-green-500"
          style={{ left: -6, top: '70%' }}
        />
      </CardContent>
    </Card>
  );
}