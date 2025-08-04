'use client';

import React, { useCallback, useEffect, useState, useRef } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  ReactFlowProvider,
  BackgroundVariant,
  useReactFlow,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { TechnicalIndicatorNode } from './nodes/TechnicalIndicatorNode';
import { ConditionNode } from './nodes/ConditionNode';
import { ActionNode } from './nodes/ActionNode';
import { DataSourceNode } from './nodes/DataSourceNode';
import { CustomDatasetNode } from './nodes/CustomDatasetNode';
import { OutputNode } from './nodes/OutputNode';
import { LogicNode } from './nodes/LogicNode';
import { RiskManagementNode } from './nodes/RiskManagementNode';
import { SmartEdge } from './edges/SmartEdge';
import { useNoCodeStore } from '@/lib/stores/no-code-store';
import { connectionManager } from '@/lib/connection-manager';
import { validateWorkflow, ValidationResult } from '@/lib/workflow-validation';
import { ConfigurationPanel } from './ConfigurationPanel';
import { X, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { Button } from '@/components/ui/no-code/button';

const nodeTypes = {
  technicalIndicator: TechnicalIndicatorNode,
  condition: ConditionNode,
  action: ActionNode,
  dataSource: DataSourceNode,
  customDataset: CustomDatasetNode,
  output: OutputNode,
  logic: LogicNode,
  risk: RiskManagementNode,
};

const edgeTypes = {
  smart: SmartEdge,
};

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

interface NoCodeWorkflowEditorProps {
  selectedNode: string | null;
  onNodeSelect: (nodeId: string | null) => void;
}

function NoCodeWorkflowEditorInner({ selectedNode, onNodeSelect }: NoCodeWorkflowEditorProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [isClosingModal, setIsClosingModal] = useState(false);
  const [modalSelectedNode, setModalSelectedNode] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [showValidationPanel, setShowValidationPanel] = useState(false);
  const { currentWorkflow, updateWorkflow, addNode, removeNode } = useNoCodeStore();
  const { screenToFlowPosition } = useReactFlow();
  
  // Use ReactFlow state as primary, sync to store when needed
  const [nodes, setNodes, onNodesChange] = useNodesState(currentWorkflow?.nodes || []);
  const [edges, setEdges, onEdgesChange] = useEdgesState(currentWorkflow?.edges || []);
  
  // Sync store changes to ReactFlow when store is updated externally
  useEffect(() => {
    if (currentWorkflow) {
      setNodes(currentWorkflow.nodes);
      setEdges(currentWorkflow.edges);
    }
  }, [currentWorkflow?.nodes?.length, currentWorkflow?.edges?.length, setNodes, setEdges]);

  // Run validation when workflow changes
  useEffect(() => {
    if (nodes.length > 0 || edges.length > 0) {
      const result = validateWorkflow(nodes, edges);
      setValidationResult(result);
    } else {
      setValidationResult(null);
    }
  }, [nodes, edges]);

  // Validate connection before ReactFlow attempts to create it
  const isValidConnection = useCallback(
    (connection: Connection) => {
      // Find source and target nodes for validation
      const sourceNode = nodes.find(n => n.id === connection.source);
      const targetNode = nodes.find(n => n.id === connection.target);
      
      if (!sourceNode || !targetNode) {
        console.warn('Source or target node not found for validation');
        return false;
      }

      // For technical indicators, check if the handle should exist based on the indicator type
      if (sourceNode.type === 'technicalIndicator' && connection.sourceHandle) {
        const indicator = sourceNode.data?.parameters?.indicator;
        console.log(`🔍 Checking handle ${connection.sourceHandle} for indicator ${indicator}`);
        
        // List of valid handles for each indicator (full handle IDs)
        const validHandles: Record<string, string[]> = {
          'ADX': ['adx-output', 'di_plus-output', 'di_minus-output'],
          'BB': ['upper-output', 'middle-output', 'lower-output', 'width-output'],
          'MACD': ['macd-output', 'signal-output', 'histogram-output'],
          'STOCH': ['k-output', 'd-output'],
          'Stochastic': ['k-output', 'd-output'],
        };

        const expectedHandles = validHandles[indicator] || ['value-output', 'signal-output'];
        if (!expectedHandles.includes(connection.sourceHandle)) {
          console.warn(`Handle ${connection.sourceHandle} not valid for indicator ${indicator}`);
          return false;
        }
      }

      // Validate connection using connection manager
      const validation = connectionManager.validateConnection(
        sourceNode,
        connection.sourceHandle || 'default',
        targetNode,
        connection.targetHandle || 'default'
      );

      if (!validation.valid) {
        console.warn('Invalid connection attempt:', validation.reason);
        return false;
      }

      return true;
    },
    [nodes]
  );

  const onConnect = useCallback(
    (params: Connection) => {
      console.log('🔗 Creating connection:', params);
      
      // Find source and target nodes for validation
      const sourceNode = nodes.find(n => n.id === params.source);
      const targetNode = nodes.find(n => n.id === params.target);
      
      if (!sourceNode || !targetNode) {
        console.warn('Source or target node not found');
        return;
      }

      // Validate connection using connection manager
      const validation = connectionManager.validateConnection(
        sourceNode,
        params.sourceHandle || 'default',
        targetNode,
        params.targetHandle || 'default'
      );

      if (!validation.valid) {
        console.warn('Invalid connection:', validation.reason);
        return;
      }

      // Create the edge with enhanced styling
      const newEdge: Edge = {
        id: `${params.source}-${params.target}-${Date.now()}`,
        source: params.source!,
        target: params.target!,
        sourceHandle: params.sourceHandle,
        targetHandle: params.targetHandle,
        type: 'smart',
        markerEnd: { type: MarkerType.ArrowClosed },
        ...connectionManager.getConnectionStyle(validation.rule),
        animated: validation.rule?.dataType === 'signal',
        data: {
          rule: validation.rule,
          sourceNode,
          targetNode
        }
      };

      // Create connection config and add to manager
      connectionManager.createConnection(newEdge, validation.rule);
      
      // Add edge to ReactFlow state
      setEdges((eds) => [...eds, newEdge]);
    },
    [setEdges, nodes]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    onNodeSelect(node.id);
  }, [onNodeSelect]);

  const onNodeDoubleClick = useCallback((event: React.MouseEvent, node: Node) => {
    console.log('Double click on node:', node.id); // Debug log
    setModalSelectedNode(node.id);
    setShowConfigModal(true);
    onNodeSelect(node.id);
  }, [onNodeSelect]);

  const handleCloseModal = useCallback(() => {
    setIsClosingModal(true);
    // Wait for exit animation to complete before hiding modal
    setTimeout(() => {
      setShowConfigModal(false);
      setModalSelectedNode(null);
      setIsClosingModal(false);
    }, 200); // Match animation duration
  }, []);

  const onPaneClick = useCallback(() => {
    onNodeSelect(null);
  }, [onNodeSelect]);

  const onEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    console.log('🔗 Edge clicked:', edge.id);
    event.stopPropagation();
  }, []);

  // Handle node changes - let ReactFlow manage dragging, sync to store on end
  const handleNodesChange = useCallback((changes: any) => {
    console.log('🔄 ReactFlow node changes:', changes);
    
    // Let ReactFlow handle its own state changes
    onNodesChange(changes);
    
    // Sync to store only when drag ends or nodes are removed/added
    const needsSync = changes.some((change: any) => 
      change.type === 'position' && change.dragging === false ||
      change.type === 'remove' ||
      change.type === 'add'
    );
    
    if (needsSync) {
      setTimeout(() => {
        console.log('📍 Syncing node changes to store');
        updateWorkflow({ nodes, edges });
      }, 100);
    }
  }, [onNodesChange, updateWorkflow, nodes, edges]);

  const handleEdgesChange = useCallback((changes: any) => {
    console.log('🔄 ReactFlow edge changes:', changes);
    
    // Let ReactFlow handle its own state changes
    onEdgesChange(changes);
    
    // Sync to store after edge changes (but not for every selection change)
    const needsSync = changes.some((change: any) => 
      change.type === 'remove' || change.type === 'add'
    );
    
    if (needsSync) {
      setTimeout(() => {
        console.log('📍 Syncing edge changes to store');
        updateWorkflow({ nodes, edges });
      }, 100);
    }
  }, [onEdgesChange, updateWorkflow, nodes, edges]);

  // Handle dropping nodes from the component library
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      console.log('📦 Drop event triggered'); // Debug log

      const type = event.dataTransfer.getData('application/reactflow') || event.dataTransfer.getData('text/plain');
      const label = event.dataTransfer.getData('application/reactflow-label');
      
      console.log('📦 Drop data:', { type, label }); // Debug log

      if (!type) {
        console.log('No type found in dataTransfer, available types:', event.dataTransfer.types);
        return;
      }

      try {
        // Use ReactFlow's screenToFlowPosition for accurate positioning
        const position = screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });

        const nodeId = `${type}-${Date.now()}`;
        const newNode: Node = {
          id: nodeId,
          type,
          position,
          data: {
            label: label || `${type} Node`,
            parameters: getDefaultParameters(type),
          },
        };

        console.log('Creating new node:', newNode); // Debug log

        // Add node to ReactFlow state
        setNodes((nds) => nds.concat(newNode));
        
        setIsDragOver(false);
        
        // Auto-select the new node
        onNodeSelect(nodeId);
        console.log('Node creation completed successfully'); // Debug log
      } catch (error) {
        console.error('Error creating node:', error); // Debug log
      }
    },
    [screenToFlowPosition, setNodes, onNodeSelect]
  );

  const getDefaultParameters = (nodeType: string) => {
    switch (nodeType) {
      case 'technicalIndicator':
        return { 
          indicatorCategory: 'trend',
          indicator: 'SMA', 
          period: 20, 
          source: 'close',
          smoothing: 0.2,
          multiplier: 2.0,
          outputType: 'main'
        };
      case 'condition':
        return { 
          conditionType: 'comparison',
          condition: 'greater_than', 
          value: 0, 
          lookback: 1,
          sensitivity: 1.0,
          confirmationBars: 0
        };
      case 'action':
        return { 
          actionCategory: 'entry',
          action: 'buy', 
          quantity: 10, 
          order_type: 'market',
          positionSizing: 'percentage',
          stop_loss: 2.0,
          take_profit: 4.0,
          conditional_execution: false
        };
      case 'dataSource':
        return { 
          symbol: 'AAPL', 
          timeframe: '1h', 
          bars: 1000, 
          dataSource: 'system', 
          assetClass: 'stocks' 
        };
      case 'customDataset':
        return {
          fileName: 'No file uploaded',
          dateColumn: 'Date',
          openColumn: 'Open',
          highColumn: 'High',
          lowColumn: 'Low',
          closeColumn: 'Close',
          volumeColumn: 'Volume',
          normalization: 'none',
          missingValues: 'forward_fill',
          validateData: true
        };
      case 'logic':
        return { operation: 'AND', inputs: 2 };
      case 'risk':
        return { 
          riskCategory: 'position',
          riskType: 'position_size', 
          riskLevel: 2, 
          maxLoss: 2.0,
          positionSize: 5.0,
          portfolioHeat: 20,
          emergencyAction: 'alert_only'
        };
      default:
        return {};
    }
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = 'move';
    setIsDragOver(true);
  }, []);

  const onDragEnter = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(true);
  }, []);

  const onDragLeave = useCallback((event: React.DragEvent) => {
    // Only set to false if we're leaving the main container
    if (!event.currentTarget.contains(event.relatedTarget as Element)) {
      console.log('Drag leave canvas'); // Debug log
      setIsDragOver(false);
    }
  }, []);

  const getValidationIcon = () => {
    if (!validationResult) return null;
    
    if (validationResult.errors.length > 0) {
      return <AlertTriangle className="h-4 w-4 text-red-500" />;
    } else if (validationResult.warnings.length > 0) {
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    } else {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
  };

  const getValidationStatus = () => {
    if (!validationResult) return 'No validation';
    
    if (validationResult.errors.length > 0) {
      return `${validationResult.errors.length} error${validationResult.errors.length > 1 ? 's' : ''}`;
    } else if (validationResult.warnings.length > 0) {
      return `${validationResult.warnings.length} warning${validationResult.warnings.length > 1 ? 's' : ''}`;
    } else {
      return 'Valid workflow';
    }
  };

  return (
    <div className="w-full h-full relative" suppressHydrationWarning>
      {/* Validation Status Bar */}
      {validationResult && (
        <div className="absolute top-4 left-4 z-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 shadow-lg">
          <div className="flex items-center space-x-2">
            {getValidationIcon()}
            <span className="text-sm font-medium">{getValidationStatus()}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowValidationPanel(!showValidationPanel)}
              className="h-6 px-2 text-xs"
            >
              {showValidationPanel ? 'Hide' : 'Details'}
            </Button>
          </div>
          
          {/* Performance Metrics */}
          {validationResult.performance && (
            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              Complexity: {validationResult.performance.estimatedComplexity} | 
              Logic Depth: {validationResult.performance.logicDepth} | 
              Indicators: {validationResult.performance.indicatorCount}
            </div>
          )}
        </div>
      )}

      {/* Validation Panel */}
      {showValidationPanel && validationResult && (
        <div className="absolute top-20 left-4 z-40 w-96 max-h-96 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden">
          <div className="p-3 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-sm">Workflow Validation</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowValidationPanel(false)}
                className="h-6 w-6 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          <div className="overflow-y-auto max-h-80">
            {/* Errors */}
            {validationResult.errors.length > 0 && (
              <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-red-600 dark:text-red-400 mb-2">
                  Errors ({validationResult.errors.length})
                </h4>
                {validationResult.errors.map((error, index) => (
                  <div key={index} className="mb-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs">
                    <div className="font-medium text-red-800 dark:text-red-300">{error.message}</div>
                    {error.suggestion && (
                      <div className="text-red-600 dark:text-red-400 mt-1">{error.suggestion}</div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Warnings */}
            {validationResult.warnings.length > 0 && (
              <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-yellow-600 dark:text-yellow-400 mb-2">
                  Warnings ({validationResult.warnings.length})
                </h4>
                {validationResult.warnings.map((warning, index) => (
                  <div key={index} className="mb-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-xs">
                    <div className="font-medium text-yellow-800 dark:text-yellow-300">{warning.message}</div>
                    {warning.suggestion && (
                      <div className="text-yellow-600 dark:text-yellow-400 mt-1">{warning.suggestion}</div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Suggestions */}
            {validationResult.suggestions && validationResult.suggestions.length > 0 && (
              <div className="p-3">
                <h4 className="text-sm font-medium text-blue-600 dark:text-blue-400 mb-2">
                  Suggestions ({validationResult.suggestions.length})
                </h4>
                {validationResult.suggestions.map((suggestion, index) => (
                  <div key={index} className="mb-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-xs">
                    <div className="font-medium text-blue-800 dark:text-blue-300">{suggestion.message}</div>
                    <div className="text-blue-600 dark:text-blue-400 mt-1 capitalize">
                      {suggestion.type} • Priority: {suggestion.priority}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {isDragOver && (
        <div className="absolute inset-0 bg-blue-100/20 dark:bg-blue-900/20 border-2 border-dashed border-blue-400 dark:border-blue-600 z-50 flex items-center justify-center pointer-events-none">
          <div className="bg-blue-50 dark:bg-blue-900/50 px-4 py-2 rounded-lg border border-blue-200 dark:border-blue-700">
            <span className="text-blue-600 dark:text-blue-400 font-medium">Drop component here</span>
          </div>
        </div>
      )}
      
      {/* Empty state with instructions */}
      {nodes.length === 0 && !isDragOver && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center space-y-3 max-w-md">
            <h3 className="text-lg font-medium text-muted-foreground">Start Building Your Strategy</h3>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>• Drag components from the left panel to create nodes</p>
              <p>• Connect nodes by dragging from output handles to input handles</p>
              <p>• Select connections and press Delete/Backspace to remove them</p>
              <p>• Double-click nodes to configure their settings</p>
            </div>
          </div>
        </div>
      )}
      
      <div 
        className="w-full h-full"
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          onPaneClick={onPaneClick}
          onEdgeClick={onEdgeClick}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          className="bg-background dark:bg-background"
          minZoom={0.1}
          maxZoom={2}
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          suppressHydrationWarning
          deleteKeyCode={['Delete', 'Backspace']}
          multiSelectionKeyCode={['Meta', 'Shift']}
          selectionKeyCode={null}
          defaultEdgeOptions={{
            type: 'default',
            markerEnd: { type: MarkerType.ArrowClosed },
            style: { strokeWidth: 2, stroke: 'hsl(var(--foreground) / 0.4)' },
          }}
        >
        <Controls className="dark:bg-background dark:border-border" />
        <MiniMap 
          className="dark:bg-background dark:border-border"
          nodeColor={(node) => {
            switch (node.type) {
              case 'dataSource': return '#8B5CF6';
              case 'technicalIndicator': return '#3B82F6';
              case 'condition': return '#F59E0B';
              case 'action': return '#10B981';
              default: return '#6B7280';
            }
          }}
        />
        <Background
          variant={BackgroundVariant.Dots}
          gap={12}
          size={1}
          color="hsl(var(--foreground) / 0.1)"
          className="dark:bg-background"
        />
        </ReactFlow>
      </div>
      
      {/* Configuration Modal */}
      {showConfigModal && modalSelectedNode && (
        <div className={`fixed inset-0 z-50 flex items-center justify-center ${
          isClosingModal 
            ? 'animate-out fade-out-0 duration-200' 
            : 'animate-in fade-in-0 duration-200'
        }`}>
          {/* Blur Background Overlay */}
          <div 
            className={`absolute inset-0 bg-black/30 backdrop-blur-sm ${
              isClosingModal 
                ? 'animate-out fade-out-0 duration-200' 
                : 'animate-in fade-in-0 duration-200'
            }`}
            onClick={handleCloseModal}
          />
          
          {/* Modal Content */}
          <div className={`relative bg-white dark:bg-gray-900 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 w-[700px] max-w-[95vw] max-h-[95vh] overflow-hidden ${
            isClosingModal 
              ? 'animate-out zoom-out-95 slide-out-to-bottom-2 duration-200' 
              : 'animate-in zoom-in-95 slide-in-from-bottom-2 duration-200'
          }`}>
            
            {/* Modal Body */}
            <div className="overflow-y-auto max-h-[calc(95vh-80px)] p-1">
              <ConfigurationPanel 
                selectedNode={modalSelectedNode}
                onNodeSelect={(nodeId) => {
                  if (nodeId) {
                    setModalSelectedNode(nodeId);
                    onNodeSelect(nodeId);
                  } else {
                    handleCloseModal();
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function NoCodeWorkflowEditor(props: NoCodeWorkflowEditorProps) {
  return (
    <ReactFlowProvider>
      <NoCodeWorkflowEditorInner {...props} />
    </ReactFlowProvider>
  );
}

export function NoCodeWorkflowEditorWrapper(props: NoCodeWorkflowEditorProps) {
  return <NoCodeWorkflowEditor {...props} />;
}