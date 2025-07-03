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
        // You could show a toast notification here
        return;
      }

      // Create the edge with enhanced styling
      const newEdge: Edge = {
        id: `${params.source}-${params.target}-${Date.now()}`,
        source: params.source!,
        target: params.target!,
        sourceHandle: params.sourceHandle,
        targetHandle: params.targetHandle,
        type: 'smart', // Use our custom smart edge
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
    onNodeSelect(node.id);
    // Auto-focus on parameters tab when double-clicking
    setTimeout(() => {
      // Try multiple selectors to find the parameters tab
      const selectors = [
        '[data-value="parameters"]',
        'button[data-value="parameters"]',
        '[role="tab"][data-value="parameters"]',
        '.parameters-tab'
      ];
      
      let parametersTab: HTMLElement | null = null;
      for (const selector of selectors) {
        parametersTab = document.querySelector(selector) as HTMLElement;
        if (parametersTab) break;
      }
      
      if (parametersTab) {
        parametersTab.click();
        console.log('Clicked parameters tab with selector:', selectors.find(s => document.querySelector(s))); // Debug log
      } else {
        console.log('Parameters tab not found, available tabs:', 
          Array.from(document.querySelectorAll('[role="tab"]')).map(el => ({
            text: el.textContent,
            attributes: Array.from(el.attributes).map(attr => `${attr.name}="${attr.value}"`).join(' ')
          }))
        ); // Debug log
      }
    }, 300);
  }, [onNodeSelect]);

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

  return (
    <div className="w-full h-full relative" suppressHydrationWarning>
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
            style: { strokeWidth: 2, stroke: '#6B7280' },
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
          className="dark:bg-background"
        />
        </ReactFlow>
      </div>
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