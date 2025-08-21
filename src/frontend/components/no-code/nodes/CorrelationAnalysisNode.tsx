import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Link2 } from 'lucide-react';

export function CorrelationAnalysisNode({ selected }: NodeProps) {
  return (
    <Card className={`min-w-[200px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`}>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          <Link2 className="h-4 w-4 text-orange-600 dark:text-orange-400" />
          <span className="font-medium text-sm dark:text-foreground">Correlation Analysis</span>
        </div>
        <Badge variant="default" className="text-xs font-semibold">
          Asset Correlator
        </Badge>
        <Handle
          type="target"
          position={Position.Left}
          id="data-input-1"
          className="w-3 h-3 bg-gray-400"
          style={{ left: -6, top: '33%' }}
        />
        <Handle
          type="target"
          position={Position.Left}
          id="data-input-2"
          className="w-3 h-3 bg-gray-400"
          style={{ left: -6, top: '66%' }}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="output"
          className="w-3 h-3 bg-orange-500"
          style={{ right: -6, top: '50%' }}
        />
      </CardContent>
    </Card>
  );
}
