// Example component showing integration with no-code API
// This demonstrates how to use the new API hooks in a React component

import React from 'react';
import { useWorkflows, useDeleteWorkflow } from '../../lib/hooks/use-no-code';
import type { Workflow } from '../../lib/api/no-code-api';

interface WorkflowListProps {
  onSelectWorkflow?: (workflowId: string) => void;
  onCreateWorkflow?: () => void;
}

export const WorkflowList: React.FC<WorkflowListProps> = ({
  onSelectWorkflow,
  onCreateWorkflow,
}) => {
  const { 
    data: workflows, 
    isLoading, 
    error, 
    refetch 
  } = useWorkflows();
  
  const deleteWorkflowMutation = useDeleteWorkflow();

  const handleDeleteWorkflow = async (workflowId: string, workflowName: string) => {
    if (window.confirm(`Are you sure you want to delete "${workflowName}"?`)) {
      try {
        await deleteWorkflowMutation.mutateAsync(workflowId);
      } catch (error) {
        console.error('Failed to delete workflow:', error);
        alert('Failed to delete workflow. Please try again.');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading workflows...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-red-800 font-medium">Failed to load workflows</h3>
        <p className="text-red-600 text-sm mt-1">
          {error instanceof Error ? error.message : 'An unexpected error occurred'}
        </p>
        <button
          onClick={() => refetch()}
          className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">My Workflows</h2>
        {onCreateWorkflow && (
          <button
            onClick={onCreateWorkflow}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create New Workflow
          </button>
        )}
      </div>

      {!workflows || workflows.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <div className="text-gray-400 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No workflows yet</h3>
          <p className="text-gray-600 mb-4">Get started by creating your first trading strategy workflow.</p>
          {onCreateWorkflow && (
            <button
              onClick={onCreateWorkflow}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Your First Workflow
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workflows?.map((workflow: Workflow) => (
            <div
              key={workflow.uuid}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-medium text-gray-900 truncate flex-1">
                  {workflow.name}
                </h3>
                <div className="flex space-x-1 ml-2">
                  {onSelectWorkflow && (
                    <button
                      onClick={() => onSelectWorkflow(workflow.uuid)}
                      className="text-blue-600 hover:text-blue-800 p-1"
                      title="Open workflow"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteWorkflow(workflow.uuid, workflow.name)}
                    className="text-red-600 hover:text-red-800 p-1"
                    title="Delete workflow"
                    disabled={deleteWorkflowMutation.isPending}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
              
              {workflow.description && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                  {workflow.description}
                </p>
              )}
              
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span className="flex items-center">
                  <span className={`inline-block w-2 h-2 rounded-full mr-1 ${
                    workflow.compilation_status === 'compiled' ? 'bg-green-400' :
                    workflow.compilation_status === 'failed' ? 'bg-red-400' :
                    workflow.compilation_status === 'compiling' ? 'bg-yellow-400' :
                    'bg-gray-400'
                  }`}></span>
                  {workflow.compilation_status}
                </span>
                <span>
                  {workflow.total_executions} executions
                </span>
              </div>
              
              <div className="mt-2 text-xs text-gray-400">
                Updated {new Date(workflow.updated_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WorkflowList;