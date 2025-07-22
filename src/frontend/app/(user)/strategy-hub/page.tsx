'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, FileText, Calendar, Tag, User } from 'lucide-react';
import { NoCodeApiClient, Workflow } from '@/lib/api/no-code-api';

export default function StrategyHubPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const noCodeApi = new NoCodeApiClient();

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      const workflowData = await noCodeApi.getWorkflows();
      setWorkflows(workflowData);
      setError(null);
    } catch (err) {
      setError('Failed to load workflows. Please try again.');
      console.error('Error fetching workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    window.open('/strategy-hub/no-code-console', '_blank');
  };

  const handleWorkflowClick = (workflow: Workflow) => {
    window.open(`/strategy-hub/no-code-console?workflow=${workflow.uuid}`, '_blank');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compiled':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
      case 'compiling':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex justify-between items-center mb-8">
          <div>
            <div className="h-8 w-64 bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
            <div className="h-4 w-96 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          </div>
          <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardHeader>
                <div className="h-6 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              </CardHeader>
              <CardContent>
                <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              </CardContent>
              <CardFooter>
                <div className="h-8 w-full bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <div className="text-red-500 mb-4">⚠️</div>
          <h3 className="text-lg font-semibold mb-2">Failed to Load Workflows</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <Button onClick={fetchWorkflows} variant="outline">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Strategy Hub</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage your no-code trading workflows and create new strategies
          </p>
        </div>
        <Button onClick={handleCreateNew} size="lg">
          <Plus className="mr-2 h-4 w-4" />
          Create New Model
        </Button>
      </div>

      {/* Workflows Grid */}
      {workflows.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold mb-2">No workflows yet</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Get started by creating your first trading strategy workflow
          </p>
          <Button onClick={handleCreateNew}>
            <Plus className="mr-2 h-4 w-4" />
            Create Your First Model
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map((workflow) => (
            <Card 
              key={workflow.uuid} 
              className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
              onClick={() => handleWorkflowClick(workflow)}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg font-semibold truncate">
                      {workflow.name}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {workflow.description || 'No description provided'}
                    </CardDescription>
                  </div>
                  <Badge 
                    className={`ml-2 ${getStatusColor(workflow.compilation_status)}`}
                    variant="secondary"
                  >
                    {workflow.compilation_status}
                  </Badge>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-3">
                  {/* Category */}
                  <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                    <Tag className="mr-2 h-3 w-3" />
                    <span className="capitalize">{workflow.category}</span>
                  </div>

                  {/* Tags */}
                  {workflow.tags && workflow.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {workflow.tags.slice(0, 3).map((tag, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      {workflow.tags.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{workflow.tags.length - 3} more
                        </Badge>
                      )}
                    </div>
                  )}

                  {/* Updated Date */}
                  <div className="flex items-center text-xs text-gray-500 dark:text-gray-500">
                    <Calendar className="mr-1 h-3 w-3" />
                    Updated {formatDate(workflow.updated_at)}
                  </div>

                  {/* Execution Mode */}
                  <div className="flex items-center text-xs">
                    <User className="mr-1 h-3 w-3" />
                    <span className="capitalize">{workflow.execution_mode.replace('_', ' ')}</span>
                  </div>
                </div>
              </CardContent>

              <CardFooter>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleWorkflowClick(workflow);
                  }}
                >
                  Open Workflow
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}