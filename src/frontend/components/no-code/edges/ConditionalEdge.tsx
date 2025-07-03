// Conditional Edge Component
// Edge for conditional logic connections with different styling

import React from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer } from 'reactflow';

export const ConditionalEdge: React.FC<EdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const conditionType = data?.conditionType || 'true';
  
  const getEdgeStyle = () => {
    switch (conditionType) {
      case 'true':
        return {
          stroke: '#10b981', // green
          strokeWidth: 2,
          strokeDasharray: '0',
        };
      case 'false':
        return {
          stroke: '#ef4444', // red
          strokeWidth: 2,
          strokeDasharray: '0',
        };
      case 'maybe':
        return {
          stroke: '#f59e0b', // amber
          strokeWidth: 2,
          strokeDasharray: '5,5',
        };
      default:
        return {
          stroke: '#6b7280', // gray
          strokeWidth: 2,
          strokeDasharray: '0',
        };
    }
  };

  const getLabel = () => {
    if (data?.label) return data.label;
    
    switch (conditionType) {
      case 'true':
        return 'TRUE';
      case 'false':
        return 'FALSE';
      case 'maybe':
        return 'MAYBE';
      default:
        return '';
    }
  };

  const getLabelStyle = () => {
    switch (conditionType) {
      case 'true':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'false':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'maybe':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <>
      <path
        id={id}
        style={{
          ...getEdgeStyle(),
          fill: 'none',
          ...style,
        }}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
      />
      {getLabel() && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              fontSize: 11,
              pointerEvents: 'all',
            }}
            className={`nodrag nopan px-2 py-1 rounded border font-medium ${getLabelStyle()}`}
          >
            {getLabel()}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};