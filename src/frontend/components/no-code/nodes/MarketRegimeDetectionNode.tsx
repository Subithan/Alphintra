import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Eye } from 'lucide-react';

export function MarketRegimeDetectionNode({ selected }: NodeProps) {
  return (
    <Card className={`min-w-[200px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`}>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          <Eye className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          <span className="font-medium text-sm dark:text-foreground">Market Regime Detection</span>
        </div>
        <Badge variant="default" className="text-xs font-semibold">
          Market State
        </Badge>
        <Handle
          type="target"
          position={Position.Left}
          id="data-input"
          className="w-3 h-3 bg-gray-400"
          style={{ left: -6 }}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="trend-output"
          className="w-3 h-3 bg-green-500"
          style={{ right: -6, top: '25%' }}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="sideways-output"
          className="w-3 h-3 bg-yellow-500"
          style={{ right: -6, top: '50%' }}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="volatile-output"
          className="w-3 h-3 bg-red-500"
          style={{ right: -6, top: '75%' }}
        />
      </CardContent>
    </Card>
  );
}
