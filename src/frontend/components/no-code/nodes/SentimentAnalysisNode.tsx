import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { MessageSquare } from 'lucide-react';

export function SentimentAnalysisNode({ selected }: NodeProps) {
  return (
    <Card className={`min-w-[200px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`}>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          <MessageSquare className="h-4 w-4 text-teal-600 dark:text-teal-400" />
          <span className="font-medium text-sm dark:text-foreground">Sentiment Analysis</span>
        </div>
        <Badge variant="default" className="text-xs font-semibold">
          News/Social Feed
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
          id="positive-output"
          className="w-3 h-3 bg-green-500"
          style={{ right: -6, top: '25%' }}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="neutral-output"
          className="w-3 h-3 bg-yellow-500"
          style={{ right: -6, top: '50%' }}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="negative-output"
          className="w-3 h-3 bg-red-500"
          style={{ right: -6, top: '75%' }}
        />
      </CardContent>
    </Card>
  );
}
