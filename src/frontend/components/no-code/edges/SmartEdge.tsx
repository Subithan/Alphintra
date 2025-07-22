import React from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from 'reactflow';
import { Badge } from '@/components/ui/no-code/badge';

interface SmartEdgeData {
  rule?: {
    label?: string;
    description?: string;
    dataType?: string;
  };
  sourceNode?: any;
  targetNode?: any;
}

export function SmartEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
  selected,
}: EdgeProps<SmartEdgeData>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const edgeData = data as SmartEdgeData;
  const rule = edgeData?.rule;

  // Enhanced styling based on connection type
  const getEdgeStyle = () => {
    const baseStyle = {
      strokeWidth: selected ? 3 : 2,
      ...style,
    };

    if (rule?.dataType === 'signal') {
      return {
        ...baseStyle,
        strokeDasharray: '8,4',
        stroke: '#F59E0B',
      };
    }

    if (rule?.dataType === 'ohlcv') {
      return {
        ...baseStyle,
        stroke: '#3B82F6',
        strokeWidth: selected ? 4 : 3,
      };
    }

    return baseStyle;
  };

  const getDataTypeColor = (dataType?: string) => {
    switch (dataType) {
      case 'ohlcv':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'numeric':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'signal':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'execution':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={getEdgeStyle()}
      />
      
      {/* Connection Label */}
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            fontSize: 10,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          {(rule?.label || selected) && (
            <div className="flex flex-col items-center space-y-1">
              {rule?.label && (
                <Badge
                  variant="secondary"
                  className={`text-xs px-2 py-0.5 ${getDataTypeColor(rule.dataType)} transition-all ${
                    selected ? 'scale-110' : 'scale-90 opacity-75'
                  }`}
                >
                  {rule.label}
                </Badge>
              )}
              
              {selected && rule?.description && (
                <div className="bg-background border border-border rounded px-2 py-1 shadow-lg max-w-48">
                  <div className="text-xs text-muted-foreground text-center">
                    {rule.description}
                  </div>
                  {rule.dataType && (
                    <div className="text-xs font-mono text-center mt-1 opacity-75">
                      Type: {rule.dataType}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}