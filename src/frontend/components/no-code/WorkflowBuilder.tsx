// Visual Workflow Builder Component
// Main interface for creating and editing trading strategy workflows

import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  Controls,
  Background,
  MiniMap,
  ConnectionMode,
  NodeTypes,
  EdgeTypes,
  Connection,
  MarkerType,
  ReactFlowProvider,
  Panel,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useNoCodeStore } from '../../lib/stores/no-code-store';
import { useWorkflows, useCreateWorkflow, useUpdateWorkflow } from '../../lib/hooks/use-no-code';
import { ComponentPalette } from './ComponentPalette';
import { NodePropertiesPanel } from './NodePropertiesPanel';
import { WorkflowToolbar } from './WorkflowToolbar';
import { EditableTitle } from './EditableTitle';
import { CustomNodes } from './nodes';
import { CustomEdges } from './edges';

// Custom node types for the workflow builder
const nodeTypes: NodeTypes = {
  technicalIndicator: CustomNodes.TechnicalIndicatorNode,
  condition: CustomNodes.ConditionNode,
  action: CustomNodes.ActionNode,
  dataSource: CustomNodes.DataSourceNode,
  riskManagement: CustomNodes.RiskManagementNode,
  output: CustomNodes.OutputNode,
};

// Custom edge types
const edgeTypes: EdgeTypes = {
  default: CustomEdges.DefaultEdge,
  conditional: CustomEdges.ConditionalEdge,
};

interface WorkflowBuilderProps {
  workflowId?: string;
  readOnly?: boolean;
  onSave?: (workflowId: string) => void;
  onExecute?: (workflowId: string) => void;
}

const WorkflowBuilderContent: React.FC<WorkflowBuilderProps> = ({
  workflowId,
  readOnly = false,
  onSave,
  onExecute,
}) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { project } = useReactFlow();
  
  // Zustand store - single source of truth
  const {
    currentWorkflow,
    selectedNode,
    updateWorkflow,
    setSelectedNode,
    addNode,
    removeNode,
    updateNodeParameters,
    saveWorkflow,
    loadWorkflow,
    compileWorkflow,
    isCompiling,
    compilationResult,
    createWorkflowOnServer,
  } = useNoCodeStore();

  // Get nodes and edges directly from store
  const nodes = currentWorkflow?.nodes || [];
  const edges = currentWorkflow?.edges || [];
  
  // UI state
  const [isPaletteOpen, setIsPaletteOpen] = useState(true);
  const [isPropertiesOpen, setIsPropertiesOpen] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // API hooks
  const createWorkflowMutation = useCreateWorkflow();
  const updateWorkflowMutation = useUpdateWorkflow();

  // Initialize workflow
  useEffect(() => {
    if (workflowId && workflowId !== currentWorkflow?.id) {
      loadWorkflow(workflowId);
    }
  }, [workflowId, loadWorkflow, currentWorkflow?.id]);

  // No more syncing needed - store is the single source of truth

  // Handle new connections between nodes
  const onConnect = useCallback(
    (params: Connection) => {
      if (readOnly) return;
      
      const newEdge = {
        ...params,
        id: `${params.source}-${params.target}-${Date.now()}`,
        type: 'default',
      };
      
      updateWorkflow({ nodes, edges: [...edges, newEdge as Edge] });
    },
    [readOnly, updateWorkflow, nodes, edges]
  );

  // Handle node selection
  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      setSelectedNode(node.id);
    },
    [setSelectedNode]
  );

  // Handle node deletion
  const onNodesDelete = useCallback(
    (nodesToDelete: Node[]) => {
      if (readOnly) return;
      
      nodesToDelete.forEach(node => {
        removeNode(node.id);
      });
    },
    [removeNode, readOnly]
  );

  // Handle drag and drop from palette
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      
      if (readOnly) return;

      const componentDataString = event.dataTransfer.getData('application/reactflow');

      if (!componentDataString || !reactFlowWrapper.current) {
        return;
      }

      const component = JSON.parse(componentDataString);
      const { type, label, ...rest } = component;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode: Node = {
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: {
          label: label || type,
          ...rest,
          parameters: { ...rest.parameters }, // Ensure parameters are copied
        },
      };

      addNode(newNode);
    },
    [project, addNode, readOnly]
  );

  // Handle property updates - simply use store function
  const handleUpdateNode = updateNodeParameters;

  // Save workflow
  const handleSave = useCallback(async () => {
    if (!currentWorkflow) return;
    
    setIsSaving(true);
    setSaveStatus('saving');
    
    try {
      if (currentWorkflow.id === 'default') {
        // Create new workflow
        const name = prompt('Enter workflow name:');
        if (name) {
          await createWorkflowOnServer(name);
          setSaveStatus('saved');
          onSave?.(currentWorkflow.id);
        }
      } else {
        // Update existing workflow
        await updateWorkflowMutation.mutateAsync({
          workflowId: currentWorkflow.id,
          updates: {
            workflow_data: {
              nodes: nodes.map(node => ({
                id: node.id,
                type: node.type!,
                position: node.position,
                data: node.data,
              })),
              edges: edges.map(edge => ({
                id: edge.id,
                source: edge.source,
                target: edge.target,
                sourceHandle: edge.sourceHandle || undefined,
                targetHandle: edge.targetHandle || undefined,
              })),
            },
          },
        });
        setSaveStatus('saved');
        onSave?.(currentWorkflow.id);
      }
      
      // Clear saved status after 2 seconds
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      console.error('Failed to save workflow:', error);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } finally {
      setIsSaving(false);
    }
  }, [currentWorkflow, nodes, edges, createWorkflowOnServer, updateWorkflowMutation, onSave]);

  // Compile workflow
  const handleCompile = useCallback(async () => {
    try {
      await compileWorkflow();
    } catch (error) {
      console.error('Compilation failed:', error);
    }
  }, [compileWorkflow]);

  // Execute workflow
  const handleExecute = useCallback(() => {
    if (currentWorkflow && onExecute) {
      onExecute(currentWorkflow.id);
    }
  }, [currentWorkflow, onExecute]);

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Toolbar */}
      <WorkflowToolbar
        workflow={currentWorkflow}
        onSave={handleSave}
        onCompile={handleCompile}
        onExecute={handleExecute}
        isSaving={isSaving}
        isCompiling={isCompiling}
        saveStatus={saveStatus}
        readOnly={readOnly}
        onTogglePalette={() => setIsPaletteOpen(!isPaletteOpen)}
        onToggleProperties={() => setIsPropertiesOpen(!isPropertiesOpen)}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Component Palette */}
        {isPaletteOpen && (
          <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
            <ComponentPalette />
          </div>
        )}

        {/* Main Workflow Canvas */}
        <div className="flex-1 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={(changes) => {
              // Only sync position/removal changes, ignore select events to prevent parameter overwrites
              const relevantChanges = changes.filter(
                (change) => change.type === 'position' || change.type === 'remove'
              );
              if (relevantChanges.length === 0) return;

              const newNodes = applyNodeChanges(relevantChanges, nodes);
              updateWorkflow({ nodes: newNodes, edges });
            }}
            onEdgesChange={(changes) => {
              const newEdges = applyEdgeChanges(changes, edges);
              updateWorkflow({ nodes, edges: newEdges });
            }}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onNodesDelete={onNodesDelete}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            connectionMode={ConnectionMode.Loose}
            defaultEdgeOptions={{
              type: 'default',
              markerEnd: { type: MarkerType.ArrowClosed },
              style: { strokeWidth: 2, stroke: 'hsl(var(--foreground) / 0.4)' },
            }}
            fitView
            attributionPosition="bottom-left"
            className="bg-background dark:bg-background"
            deleteKeyCode={readOnly ? null : ['Backspace', 'Delete']}
            multiSelectionKeyCode={readOnly ? null : ['Meta', 'Ctrl']}
            selectionKeyCode={readOnly ? null : ['Shift']}
          >
            <Background color="hsl(var(--foreground) / 0.1)" gap={20} />
            <Controls showInteractive={!readOnly} />
            <MiniMap 
              nodeColor="#3b82f6"
              className="bg-white border border-gray-200"
            />
            
            {/* Editable Title Panel */}
            <Panel position="top-center" className="!left-auto !right-auto !transform-none w-full max-w-4xl">
              <div className="px-8">
                <EditableTitle 
                  workflowId={currentWorkflow?.id || 'default'}
                  initialTitle={currentWorkflow?.name || 'Untitled Model'} 
                  readOnly={readOnly}
                />
              </div>
            </Panel>
            
            {/* Status Panel */}
            <Panel position="top-right" className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
              <div className="space-y-2 text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span>{nodes.length} components</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>{edges.length} connections</span>
                </div>
                {compilationResult && (
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span>Compiled</span>
                  </div>
                )}
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {/* Properties Panel */}
        {isPropertiesOpen && (
          <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
            <NodePropertiesPanel
              selectedNodeId={selectedNode}
              nodes={nodes}
              onUpdateNode={updateNodeParameters}
              readOnly={readOnly}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export const WorkflowBuilder: React.FC<WorkflowBuilderProps> = (props) => {
  return (
    <ReactFlowProvider>
      <WorkflowBuilderContent {...props} />
    </ReactFlowProvider>
  );
};

export default WorkflowBuilder;