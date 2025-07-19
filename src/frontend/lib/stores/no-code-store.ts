import { create } from 'zustand';
import { Node, Edge } from 'reactflow';
import { noCodeGraphQLApiClient, type Workflow as ApiWorkflow, type WorkflowData } from '../api/no-code-graphql-api';

export interface NoCodeWorkflow {
  id: string;
  name: string;
  description?: string;
  nodes: Node[];
  edges: Edge[];
  parameters: Record<string, any>;
  createdAt: string | Date;
  lastModified?: string | Date;
  updatedAt?: Date;
  hasUnsavedChanges?: boolean;
  version?: number;
  parent_workflow_id?: number;
}

export interface NoCodeState {
  currentWorkflow: NoCodeWorkflow | null;
  workflows: NoCodeWorkflow[];
  selectedNode: string | null;
  isCompiling: boolean;
  compilationResult: string | null;
  
  // Actions
  updateWorkflow: (workflow: { nodes: Node[]; edges: Edge[] }) => void;
  setSelectedNode: (nodeId: string | null) => void;
  saveWorkflow: (name: string) => void;
  loadWorkflow: (workflowOrId: string | NoCodeWorkflow) => void;
  deleteWorkflow: (id: string) => void;
  compileWorkflow: () => Promise<void>;
  syncWithApi: () => Promise<void>;
  createWorkflowOnServer: (name: string, description?: string) => Promise<void>;
  updateNodeParameters: (nodeId: string, parameters: Record<string, any>) => void;
  addNode: (node: Node) => void;
  removeNode: (nodeId: string) => void;
  duplicateNode: (nodeId: string) => void;
}

export const useNoCodeStore = create<NoCodeState>((set, get) => ({
  currentWorkflow: {
    id: 'default',
    name: 'Untitled Model',
    nodes: [],
    edges: [],
    parameters: {},
    createdAt: new Date(),
    updatedAt: new Date(),
  },
  workflows: [],
  selectedNode: null,
  isCompiling: false,
  compilationResult: null,

  updateWorkflow: (workflow) => {
    const current = get().currentWorkflow;
    if (current) {
      set({
        currentWorkflow: {
          ...current,
          nodes: workflow.nodes,
          edges: workflow.edges,
          updatedAt: new Date(),
        },
      });
    } else {
      // Initialize current workflow if it doesn't exist
      set({
        currentWorkflow: {
          id: 'default',
          name: 'Untitled Model',
          nodes: workflow.nodes,
          edges: workflow.edges,
          parameters: {},
          createdAt: new Date(),
          updatedAt: new Date(),
        },
      });
    }
  },

  setSelectedNode: (nodeId) => {
    set({ selectedNode: nodeId });
  },

  saveWorkflow: (name) => {
    const current = get().currentWorkflow;
    if (current) {
      const updatedWorkflow = {
        ...current,
        name,
        updatedAt: new Date(),
      };
      
      set((state) => ({
        currentWorkflow: updatedWorkflow,
        workflows: state.workflows.map(w => 
          w.id === current.id ? updatedWorkflow : w
        ),
      }));
    }
  },

  loadWorkflow: (workflowOrId) => {
    if (typeof workflowOrId === 'string') {
      // Load existing workflow by ID
      const workflow = get().workflows.find(w => w.id === workflowOrId);
      if (workflow) {
        set({ currentWorkflow: workflow });
      }
    } else {
      // Load workflow object (e.g., from template)
      const workflow: NoCodeWorkflow = {
        ...workflowOrId,
        updatedAt: new Date(),
        createdAt: workflowOrId.createdAt instanceof Date ? workflowOrId.createdAt : new Date(workflowOrId.createdAt),
        lastModified: workflowOrId.lastModified ? 
          (workflowOrId.lastModified instanceof Date ? workflowOrId.lastModified : new Date(workflowOrId.lastModified)) 
          : new Date()
      };
      set({ currentWorkflow: workflow });
    }
  },

  deleteWorkflow: (id) => {
    set((state) => ({
      workflows: state.workflows.filter(w => w.id !== id),
      currentWorkflow: state.currentWorkflow?.id === id ? null : state.currentWorkflow,
    }));
  },

  compileWorkflow: async () => {
    const current = get().currentWorkflow;
    if (!current) return;

    set({ isCompiling: true });

    try {
      // If workflow has a UUID, use API compilation
      if (current.id !== 'default') {
        const result = await noCodeGraphQLApiClient.compileWorkflow(current.id);
        set({ 
          compilationResult: result.generated_code,
          isCompiling: false 
        });
      } else {
        // Fallback to local compilation for unsaved workflows
        await new Promise(resolve => setTimeout(resolve, 2000));
        const pythonCode = generatePythonCode(current.nodes, current.edges);
        set({ 
          compilationResult: pythonCode,
          isCompiling: false 
        });
      }
    } catch (error) {
      console.error('Compilation error:', error);
      set({ 
        compilationResult: null,
        isCompiling: false 
      });
    }
  },

  syncWithApi: async () => {
    try {
      const workflows = await noCodeGraphQLApiClient.getWorkflows();
      const convertedWorkflows: NoCodeWorkflow[] = workflows.map(apiWorkflow => ({
        id: apiWorkflow.uuid,
        name: apiWorkflow.name,
        description: apiWorkflow.description,
        nodes: apiWorkflow.workflow_data.nodes || [],
        edges: apiWorkflow.workflow_data.edges || [],
        parameters: {},
        createdAt: apiWorkflow.created_at,
        lastModified: apiWorkflow.updated_at,
        updatedAt: new Date(apiWorkflow.updated_at),
      }));
      
      set({ workflows: convertedWorkflows });
    } catch (error) {
      console.error('Failed to sync workflows:', error);
    }
  },

  createWorkflowOnServer: async (name: string, description?: string) => {
    const current = get().currentWorkflow;
    if (!current) return;

    try {
      const workflowData: WorkflowData = {
        nodes: current.nodes.map(node => ({
          id: node.id,
          type: node.type!,
          position: node.position,
          data: node.data,
        })),
        edges: current.edges.map(edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle || undefined,
          targetHandle: edge.targetHandle || undefined,
        })),
      };

      const newWorkflow = await noCodeGraphQLApiClient.createWorkflow({
        name,
        description,
        workflow_data: workflowData,
        category: 'custom',
        execution_mode: 'backtest',
      });

      // Update current workflow with server data
      const updatedWorkflow: NoCodeWorkflow = {
        id: newWorkflow.uuid,
        name: newWorkflow.name,
        description: newWorkflow.description,
        nodes: current.nodes,
        edges: current.edges,
        parameters: {},
        createdAt: newWorkflow.created_at,
        lastModified: newWorkflow.updated_at,
        updatedAt: new Date(newWorkflow.updated_at),
      };

      set({
        currentWorkflow: updatedWorkflow,
        workflows: [...get().workflows, updatedWorkflow],
      });
    } catch (error) {
      console.error('Failed to create workflow on server:', error);
      throw error;
    }
  },

  updateNodeParameters: (nodeId, parameters) => set((state) => {
    const current = state.currentWorkflow;
    if (!current) {
      console.warn('No current workflow found when updating node parameters');
      return state;
    }

    console.log('Updating node parameters:', { nodeId, parameters }); // Debug log

    const updatedNodes = current.nodes.map(node => {
      if (node.id === nodeId) {
        const updatedNode = { 
          ...node, 
          data: { 
            ...node.data, 
            parameters: { 
              ...node.data.parameters, 
              ...parameters 
            },
            // Update label if name parameter changed
            label: parameters.name || node.data.label,
            // Mark as modified for visual feedback
            isModified: true,
            lastModified: new Date().toISOString()
          } 
        };
        console.log('Updated node:', updatedNode); // Debug log
        return updatedNode;
      }
      return node;
    });

    const newWorkflow = {
      ...current,
      nodes: updatedNodes,
      updatedAt: new Date(),
      // Mark workflow as having unsaved changes
      hasUnsavedChanges: true,
    };

    console.log('Store updated with new parameters'); // Debug log
    
    return {
      ...state,
      currentWorkflow: newWorkflow,
    };
  }),

  addNode: (node) => {
    const current = get().currentWorkflow;
    if (!current) {
      console.log('No current workflow found when adding node'); // Debug log
      return;
    }

    console.log('Adding node to store:', node); // Debug log
    console.log('Current nodes count:', current.nodes.length); // Debug log

    set({
      currentWorkflow: {
        ...current,
        nodes: [...current.nodes, node],
        updatedAt: new Date(),
      },
    });

    console.log('Node added, new count:', get().currentWorkflow?.nodes.length); // Debug log
  },

  removeNode: (nodeId) => {
    const current = get().currentWorkflow;
    if (!current) {
      console.log('No current workflow found when removing node'); // Debug log
      return;
    }

    console.log('Removing node from store:', nodeId); // Debug log
    console.log('Current nodes before removal:', current.nodes.length); // Debug log

    const updatedNodes = current.nodes.filter(node => node.id !== nodeId);
    const updatedEdges = current.edges.filter(
      edge => edge.source !== nodeId && edge.target !== nodeId
    );

    console.log('Nodes after removal:', updatedNodes.length); // Debug log

    set({
      currentWorkflow: {
        ...current,
        nodes: updatedNodes,
        edges: updatedEdges,
        updatedAt: new Date(),
      },
    });

    console.log('Store updated, new node count:', get().currentWorkflow?.nodes.length); // Debug log
  },

  duplicateNode: (nodeId) => {
    const current = get().currentWorkflow;
    if (!current) return;

    const nodeToDuplicate = current.nodes.find(node => node.id === nodeId);
    if (!nodeToDuplicate) return;

    const duplicatedNode = {
      ...nodeToDuplicate,
      id: `${nodeToDuplicate.type}-${Date.now()}`,
      position: {
        x: nodeToDuplicate.position.x + 50,
        y: nodeToDuplicate.position.y + 50,
      },
    };

    set({
      currentWorkflow: {
        ...current,
        nodes: [...current.nodes, duplicatedNode],
        updatedAt: new Date(),
      },
    });
  },
}));

// Helper function to generate Python code from workflow
function generatePythonCode(nodes: Node[], edges: Edge[]): string {
  let code = `
import pandas as pd
import numpy as np
from typing import Dict, Any
import talib

class GeneratedStrategy:
    def __init__(self, parameters: Dict[str, Any] = None):
        self.parameters = parameters or {}
        
    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generated strategy execution logic
        """
        signals = pd.DataFrame(index=data.index)
        
`;

  // Process each node to generate corresponding code
  nodes.forEach(node => {
    switch (node.type) {
      case 'technicalIndicator':
        code += generateIndicatorCode(node);
        break;
      case 'condition':
        code += generateConditionCode(node);
        break;
      case 'action':
        code += generateActionCode(node);
        break;
    }
  });

  code += `
        return signals
        
    def backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Backtest the strategy
        """
        signals = self.execute(data)
        # Implement backtesting logic
        return {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0
        }
`;

  return code;
}

function generateIndicatorCode(node: Node): string {
  const { parameters } = node.data;
  const indicatorType = parameters?.indicator || 'SMA';
  
  switch (indicatorType) {
    case 'SMA':
      return `        # Simple Moving Average
        signals['sma_${parameters?.period || 20}'] = talib.SMA(data['close'], timeperiod=${parameters?.period || 20})
        
`;
    case 'RSI':
      return `        # Relative Strength Index
        signals['rsi'] = talib.RSI(data['close'], timeperiod=${parameters?.period || 14})
        
`;
    default:
      return `        # ${indicatorType}
        signals['${indicatorType.toLowerCase()}'] = data['close']  # Placeholder
        
`;
  }
}

function generateConditionCode(node: Node): string {
  const { parameters } = node.data;
  return `        # Condition: ${parameters?.condition || 'Generic condition'}
        condition_${node.id} = ${parameters?.expression || 'True'}
        
`;
}

function generateActionCode(node: Node): string {
  const { parameters } = node.data;
  return `        # Action: ${parameters?.action || 'Generic action'}
        if condition_${node.id}:
            signals['signal'] = ${parameters?.signal || '1'}
        
`;
}