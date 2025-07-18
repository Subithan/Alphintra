import { useState, useCallback, useEffect, useRef } from 'react';
import { Node, Edge } from 'reactflow';
import { noCodeApiClient, Workflow, WorkflowData, Execution } from '@/lib/api/no-code-api';
import { useToast } from '@/components/ui/use-toast';

export interface UseWorkflowOptions {
  workflowId?: string;
  autoSave?: boolean;
  autoSaveInterval?: number; // in milliseconds
}

export interface WorkflowState {
  workflow: Workflow | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  isDirty: boolean;
  lastSaved: Date | null;
}

export interface WorkflowActions {
  // Core operations
  loadWorkflow: (id: string) => Promise<void>;
  saveWorkflow: (name?: string) => Promise<void>;
  updateWorkflowData: (nodes: Node[], edges: Edge[]) => void;
  resetWorkflow: () => Promise<void>;
  
  // Import/Export
  exportWorkflow: (format?: 'json' | 'yaml') => Promise<string>;
  importWorkflow: (data: string, format?: 'json' | 'yaml') => Promise<void>;
  
  // Utility
  clearError: () => void;
  markClean: () => void;
}

export function useWorkflow(options: UseWorkflowOptions = {}): [WorkflowState, WorkflowActions] {
  const { workflowId, autoSave = true, autoSaveInterval = 30000 } = options;
  const { toast } = useToast();
  
  const [state, setState] = useState<WorkflowState>({
    workflow: null,
    loading: false,
    saving: false,
    error: null,
    isDirty: false,
    lastSaved: null,
  });

  const autoSaveRef = useRef<NodeJS.Timeout>();
  const lastDataRef = useRef<WorkflowData | null>(null);

  // Auto-save functionality
  const performAutoSave = useCallback(async () => {
    if (!state.workflow || !state.isDirty || state.saving) return;

    try {
      setState(prev => ({ ...prev, saving: true }));
      
      await noCodeApiClient.autoSaveWorkflow(
        state.workflow.uuid,
        state.workflow.workflow_data
      );
      
      setState(prev => ({ 
        ...prev, 
        saving: false, 
        isDirty: false, 
        lastSaved: new Date() 
      }));
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        saving: false, 
        error: error instanceof Error ? error.message : 'Auto-save failed' 
      }));
    }
  }, [state.workflow, state.isDirty, state.saving]);

  // Set up auto-save interval
  useEffect(() => {
    if (autoSave && state.isDirty && state.workflow) {
      autoSaveRef.current = setTimeout(performAutoSave, autoSaveInterval);
    }

    return () => {
      if (autoSaveRef.current) {
        clearTimeout(autoSaveRef.current);
      }
    };
  }, [autoSave, state.isDirty, state.workflow, autoSaveInterval, performAutoSave]);

  // Load initial workflow
  useEffect(() => {
    if (workflowId) {
      loadWorkflow(workflowId);
    }
  }, [workflowId]);

  const loadWorkflow = useCallback(async (id: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const workflow = await noCodeApiClient.getWorkflow(id);
      lastDataRef.current = workflow.workflow_data;
      
      setState(prev => ({ 
        ...prev, 
        workflow, 
        loading: false, 
        isDirty: false,
        lastSaved: new Date(workflow.updated_at)
      }));
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error instanceof Error ? error.message : 'Failed to load workflow' 
      }));
      
      toast({
        title: "Error",
        description: "Failed to load workflow",
        variant: "destructive",
      });
    }
  }, [toast]);

  const saveWorkflow = useCallback(async (name?: string) => {
    if (!state.workflow) return;

    setState(prev => ({ ...prev, saving: true, error: null }));
    
    try {
      const updateData: any = { workflow_data: state.workflow.workflow_data };
      if (name) updateData.name = name;

      const updatedWorkflow = await noCodeApiClient.updateWorkflow(
        state.workflow.uuid, 
        updateData
      );
      
      setState(prev => ({ 
        ...prev, 
        workflow: updatedWorkflow, 
        saving: false, 
        isDirty: false,
        lastSaved: new Date()
      }));
      
      toast({
        title: "Success",
        description: "Workflow saved successfully",
      });
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        saving: false, 
        error: error instanceof Error ? error.message : 'Failed to save workflow' 
      }));
      
      toast({
        title: "Error",
        description: "Failed to save workflow",
        variant: "destructive",
      });
    }
  }, [state.workflow, toast]);

  const updateWorkflowData = useCallback((nodes: Node[], edges: Edge[]) => {
    if (!state.workflow) return;

    const newData: WorkflowData = { 
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.type || 'default',
        position: node.position,
        data: node.data,
      })), 
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle || undefined,
        targetHandle: edge.targetHandle || undefined,
      }))
    };
    
    // Check if data actually changed
    const hasChanged = JSON.stringify(newData) !== JSON.stringify(lastDataRef.current);
    
    if (hasChanged) {
      setState(prev => ({
        ...prev,
        workflow: prev.workflow ? {
          ...prev.workflow,
          workflow_data: newData
        } : null,
        isDirty: true
      }));
      
      lastDataRef.current = newData;
    }
  }, [state.workflow]);

  const resetWorkflow = useCallback(async () => {
    if (!state.workflow) return;

    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const resetWorkflow = await noCodeApiClient.resetWorkflow(state.workflow.uuid);
      lastDataRef.current = resetWorkflow.workflow_data;
      
      setState(prev => ({ 
        ...prev, 
        workflow: resetWorkflow, 
        loading: false, 
        isDirty: false,
        lastSaved: new Date(resetWorkflow.updated_at)
      }));
      
      toast({
        title: "Success",
        description: "Workflow reset successfully",
      });
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error instanceof Error ? error.message : 'Failed to reset workflow' 
      }));
      
      toast({
        title: "Error",
        description: "Failed to reset workflow",
        variant: "destructive",
      });
    }
  }, [state.workflow, toast]);

  const exportWorkflow = useCallback(async (format: 'json' | 'yaml' = 'json'): Promise<string> => {
    if (!state.workflow) throw new Error('No workflow to export');

    try {
      const exportedData = await noCodeApiClient.exportWorkflow(state.workflow.uuid, format);
      
      toast({
        title: "Success",
        description: "Workflow exported successfully",
      });
      
      return exportedData;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to export workflow';
      
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
      
      throw error;
    }
  }, [state.workflow, toast]);

  const importWorkflow = useCallback(async (data: string, format: 'json' | 'yaml' = 'json') => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const importedWorkflow = await noCodeApiClient.importWorkflow(data, format);
      lastDataRef.current = importedWorkflow.workflow_data;
      
      setState(prev => ({ 
        ...prev, 
        workflow: importedWorkflow, 
        loading: false, 
        isDirty: false,
        lastSaved: new Date(importedWorkflow.updated_at)
      }));
      
      toast({
        title: "Success",
        description: "Workflow imported successfully",
      });
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error instanceof Error ? error.message : 'Failed to import workflow' 
      }));
      
      toast({
        title: "Error",
        description: "Failed to import workflow",
        variant: "destructive",
      });
    }
  }, [toast]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const markClean = useCallback(() => {
    setState(prev => ({ ...prev, isDirty: false }));
  }, []);

  const actions: WorkflowActions = {
    loadWorkflow,
    saveWorkflow,
    updateWorkflowData,
    resetWorkflow,
    exportWorkflow,
    importWorkflow,
    clearError,
    markClean,
  };

  return [state, actions];
}

// Hook for workflow execution
export function useWorkflowExecution(workflowId?: string) {
  const [execution, setExecution] = useState<Execution | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const startExecution = useCallback(async (config: {
    execution_type: 'backtest' | 'paper_trade' | 'live_trade';
    symbols: string[];
    timeframe: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d';
    start_date?: string;
    end_date?: string;
    initial_capital: number;
    parameters?: Record<string, any>;
  }) => {
    if (!workflowId) return;

    setLoading(true);
    setError(null);

    try {
      const newExecution = await noCodeApiClient.executeWorkflow(workflowId, config);
      setExecution(newExecution);
      
      toast({
        title: "Success",
        description: "Workflow execution started",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start execution';
      setError(message);
      
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [workflowId, toast]);

  const stopExecution = useCallback(async () => {
    if (!execution) return;

    try {
      await noCodeApiClient.stopExecution(execution.uuid);
      setExecution(prev => prev ? { ...prev, status: 'failed' } : null);
      
      toast({
        title: "Success",
        description: "Execution stopped",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to stop execution",
        variant: "destructive",
      });
    }
  }, [execution, toast]);

  const refreshExecution = useCallback(async () => {
    if (!execution) return;

    try {
      const updatedExecution = await noCodeApiClient.getExecution(execution.uuid);
      setExecution(updatedExecution);
    } catch (error) {
      console.error('Failed to refresh execution:', error);
    }
  }, [execution]);

  return {
    execution,
    loading,
    error,
    startExecution,
    stopExecution,
    refreshExecution,
  };
}