// React hooks for no-code workflow management
// Provides convenient React Query hooks for API interactions

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  noCodeApiClient, 
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
} from '../api/no-code-api';

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
    queryFn: () => noCodeApiClient.getWorkflows(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useWorkflow(workflowId: string) {
  return useQuery({
    queryKey: noCodeKeys.workflow(workflowId),
    queryFn: () => noCodeApiClient.getWorkflow(workflowId),
    enabled: !!workflowId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workflow: WorkflowCreate) => noCodeApiClient.createWorkflow(workflow),
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
      noCodeApiClient.updateWorkflow(workflowId, updates),
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
    mutationFn: (workflowId: string) => noCodeApiClient.deleteWorkflow(workflowId),
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
    mutationFn: (workflowId: string) => noCodeApiClient.compileWorkflow(workflowId),
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
    queryFn: () => noCodeApiClient.getExecution(executionId),
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
      noCodeApiClient.executeWorkflow(workflowId, config),
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
    queryFn: () => noCodeApiClient.getComponents(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes - components change rarely
  });
}

// Template library hooks
export function useTemplates(filters?: TemplateFilters) {
  return useQuery({
    queryKey: [...noCodeKeys.templates, filters],
    queryFn: () => noCodeApiClient.getTemplates(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useCreateWorkflowFromTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ templateId, workflowName }: { templateId: string; workflowName: string }) =>
      noCodeApiClient.createWorkflowFromTemplate(templateId, workflowName),
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
    queryFn: () => noCodeApiClient.healthCheck(),
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
        queryFn: () => noCodeApiClient.getWorkflow(workflowId),
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