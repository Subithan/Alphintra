// React hooks for no-code workflow management
// Provides convenient React Query hooks for API interactions

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { 
  noCodeGraphQLApiClient, 
  type Workflow, 
  type WorkflowCreate, 
  type WorkflowUpdate,
  type ExecutionConfig,
  type Execution,
  type Component,
  type Template,
  type WorkflowFilters,
  type ComponentFilters,
  type TemplateFilters
} from '../api/no-code-graphql-api';

// Query keys for React Query caching
export const noCodeKeys = {
  workflows: ['workflows'] as const,
  workflow: (id: string) => ['workflow', id] as const,
  executions: ['executions'] as const,
  execution: (id: string) => ['execution', id] as const,
  components: ['components'] as const,
  templates: ['templates'] as const,
} as const;

// Workflow hooks
export function useWorkflows(filters?: WorkflowFilters) {
  return useQuery({
    queryKey: [...noCodeKeys.workflows, filters],
    queryFn: () => noCodeGraphQLApiClient.getWorkflows(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useWorkflow(workflowId: string) {
  return useQuery({
    queryKey: noCodeKeys.workflow(workflowId),
    queryFn: () => noCodeGraphQLApiClient.getWorkflow(workflowId),
    enabled: !!workflowId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workflow: WorkflowCreate) => noCodeGraphQLApiClient.createWorkflow(workflow),
    onSuccess: (newWorkflow) => {
      // Invalidate workflows list to refetch
      queryClient.invalidateQueries({ queryKey: noCodeKeys.workflows });
      
      // Add the new workflow to the cache
      queryClient.setQueryData(
        noCodeKeys.workflow(newWorkflow.uuid),
        newWorkflow
      );
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workflowId, updates }: { workflowId: string; updates: WorkflowUpdate }) =>
      noCodeGraphQLApiClient.updateWorkflow(workflowId, updates),
    onSuccess: (updatedWorkflow, { workflowId }) => {
      // Update the specific workflow in cache
      queryClient.setQueryData(
        noCodeKeys.workflow(workflowId),
        updatedWorkflow
      );
      
      // Invalidate workflows list to refetch
      queryClient.invalidateQueries({ queryKey: noCodeKeys.workflows });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workflowId: string) => noCodeGraphQLApiClient.deleteWorkflow(workflowId),
    onSuccess: (_, workflowId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: noCodeKeys.workflow(workflowId) });
      
      // Invalidate workflows list to refetch
      queryClient.invalidateQueries({ queryKey: noCodeKeys.workflows });
    },
  });
}

// Compilation hooks
export function useCompileWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workflowId: string) => noCodeGraphQLApiClient.compileWorkflow(workflowId),
    onSuccess: (compilationResult, workflowId) => {
      // Update the workflow in cache with compilation results
      queryClient.setQueryData(
        noCodeKeys.workflow(workflowId),
        (oldData: Workflow | undefined) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            generated_code: compilationResult.generated_code,
            generated_requirements: compilationResult.requirements,
            compilation_status: compilationResult.status as any,
            compilation_errors: compilationResult.errors,
          };
        }
      );
    },
  });
}

// Execution hooks
export function useExecution(executionId: string) {
  return useQuery({
    queryKey: noCodeKeys.execution(executionId),
    queryFn: () => noCodeGraphQLApiClient.getExecution(executionId),
    enabled: !!executionId,
    refetchInterval: (query) => {
      // Poll every 2 seconds if execution is in progress
      const execution = query.state.data as Execution | undefined;
      if (execution?.status === 'running' || execution?.status === 'pending') {
        return 2000;
      }
      return false;
    },
  });
}

export function useExecuteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workflowId, config }: { workflowId: string; config: ExecutionConfig }) =>
      noCodeGraphQLApiClient.executeWorkflow(workflowId, config),
    onSuccess: (execution) => {
      // Add execution to cache
      queryClient.setQueryData(
        noCodeKeys.execution(execution.uuid),
        execution
      );
      
      // Invalidate executions list
      queryClient.invalidateQueries({ queryKey: noCodeKeys.executions });
    },
  });
}

// Component library hooks
export function useComponents(filters?: ComponentFilters) {
  return useQuery({
    queryKey: [...noCodeKeys.components, filters],
    queryFn: () => noCodeGraphQLApiClient.getComponents(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes - components change rarely
  });
}

// Template library hooks
export function useTemplates(filters?: TemplateFilters) {
  return useQuery({
    queryKey: [...noCodeKeys.templates, filters],
    queryFn: () => noCodeGraphQLApiClient.getTemplates(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useCreateWorkflowFromTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ templateId, workflowName }: { templateId: string; workflowName: string }) =>
      noCodeGraphQLApiClient.createWorkflowFromTemplate(templateId, workflowName),
    onSuccess: (newWorkflow) => {
      // Add to cache
      queryClient.setQueryData(
        noCodeKeys.workflow(newWorkflow.uuid),
        newWorkflow
      );
      
      // Invalidate workflows list
      queryClient.invalidateQueries({ queryKey: noCodeKeys.workflows });
    },
  });
}

// Health check hook
export function useNoCodeHealthCheck() {
  return useQuery({
    queryKey: ['no-code-health'],
    queryFn: () => noCodeGraphQLApiClient.healthCheck(),
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
  });
}

// Optimistic updates hook for workflow data
export function useOptimisticWorkflowUpdate() {
  const queryClient = useQueryClient();

  return {
    updateWorkflowData: (workflowId: string, updates: Partial<Workflow>) => {
      queryClient.setQueryData(
        noCodeKeys.workflow(workflowId),
        (oldData: Workflow | undefined) => {
          if (!oldData) return oldData;
          return { ...oldData, ...updates };
        }
      );
    },
    
    revertWorkflowData: (workflowId: string) => {
      queryClient.invalidateQueries({ queryKey: noCodeKeys.workflow(workflowId) });
    },
  };
}

// Prefetch utilities
export function usePrefetchWorkflow() {
  const queryClient = useQueryClient();

  return {
    prefetchWorkflow: (workflowId: string) => {
      queryClient.prefetchQuery({
        queryKey: noCodeKeys.workflow(workflowId),
        queryFn: () => noCodeGraphQLApiClient.getWorkflow(workflowId),
        staleTime: 2 * 60 * 1000,
      });
    },
  };
}

// Custom hook for workflow operations with loading states
export function useWorkflowOperations() {
  const createWorkflow = useCreateWorkflow();
  const updateWorkflow = useUpdateWorkflow();
  const deleteWorkflow = useDeleteWorkflow();
  const compileWorkflow = useCompileWorkflow();
  const executeWorkflow = useExecuteWorkflow();

  return {
    createWorkflow: createWorkflow.mutateAsync,
    updateWorkflow: updateWorkflow.mutateAsync,
    deleteWorkflow: deleteWorkflow.mutateAsync,
    compileWorkflow: compileWorkflow.mutateAsync,
    executeWorkflow: executeWorkflow.mutateAsync,
    
    isCreating: createWorkflow.isPending,
    isUpdating: updateWorkflow.isPending,
    isDeleting: deleteWorkflow.isPending,
    isCompiling: compileWorkflow.isPending,
    isExecuting: executeWorkflow.isPending,
    
    errors: {
      create: createWorkflow.error,
      update: updateWorkflow.error,
      delete: deleteWorkflow.error,
      compile: compileWorkflow.error,
      execute: executeWorkflow.error,
    },
  };
}

// GraphQL subscription hooks for real-time updates
export function useExecutionSubscription(executionId: string) {
  const queryClient = useQueryClient();
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!executionId) return;

    // Subscribe to execution updates
    const unsubscribe = noCodeGraphQLApiClient.subscribeToExecutionUpdates(
      executionId,
      (updatedExecution) => {
        // Update the execution in cache
        queryClient.setQueryData(
          noCodeKeys.execution(executionId),
          updatedExecution
        );
      }
    );

    unsubscribeRef.current = unsubscribe;

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, [executionId, queryClient]);

  return {
    isConnected: !!unsubscribeRef.current,
    disconnect: () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
    },
  };
}

export function useWorkflowSubscription(workflowId: string) {
  const queryClient = useQueryClient();
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!workflowId) return;

    // Subscribe to workflow updates
    const unsubscribe = noCodeGraphQLApiClient.subscribeToWorkflowUpdates(
      workflowId,
      (updatedWorkflow) => {
        // Update the workflow in cache
        queryClient.setQueryData(
          noCodeKeys.workflow(workflowId),
          updatedWorkflow
        );

        // Also invalidate workflows list to ensure consistency
        queryClient.invalidateQueries({ 
          queryKey: noCodeKeys.workflows,
          exact: false 
        });
      }
    );

    unsubscribeRef.current = unsubscribe;

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, [workflowId, queryClient]);

  return {
    isConnected: !!unsubscribeRef.current,
    disconnect: () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
    },
  };
}

// Enhanced execution hook with subscription support
export function useExecutionWithSubscription(executionId: string) {
  const executionQuery = useExecution(executionId);
  const subscription = useExecutionSubscription(executionId);

  return {
    ...executionQuery,
    subscription,
  };
}

// Enhanced workflow hook with subscription support
export function useWorkflowWithSubscription(workflowId: string) {
  const workflowQuery = useWorkflow(workflowId);
  const subscription = useWorkflowSubscription(workflowId);

  return {
    ...workflowQuery,
    subscription,
  };
}