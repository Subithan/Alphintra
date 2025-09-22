'use client'

import React, { useEffect, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'

// Disable static generation for this page as it uses searchParams
export const dynamic = 'force-dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ExecutionModeSelector } from '@/components/no-code/ExecutionModeSelector'
import { useExecutionStore, useCurrentExecution } from '@/lib/stores/execution-store'
import { useNoCodeStore } from '@/lib/stores/no-code-store'
import { ArrowLeft, Clock, CheckCircle, AlertCircle } from 'lucide-react'

interface WorkflowData {
  id: number
  name: string
  description?: string
  complexity?: 'simple' | 'medium' | 'complex'
  nodeCount: number
  edgeCount: number
  createdAt: string
  updatedAt: string
}

export default function ExecuteWorkflowPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const workflowId = parseInt(params.id as string)
  
  const [workflow, setWorkflow] = useState<WorkflowData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const { currentWorkflow } = useNoCodeStore()
  const currentExecution = useCurrentExecution()
  const { 
    startExecution, 
    setCurrentWorkflow, 
    setExecutionStatus,
    lastError
  } = useExecutionStore()
  
  // Check if there's a returning flow from another page
  const returnFrom = searchParams.get('from')
  const executionId = searchParams.get('executionId')
  
  useEffect(() => {
    // Set current workflow context
    setCurrentWorkflow(workflowId)
    
    // Load workflow data
    loadWorkflowData()
  }, [workflowId])
  
  const loadWorkflowData = async () => {
    try {
      setIsLoading(true)
      
      // First try to use current workflow from store if it matches
      if (currentWorkflow && currentWorkflow.id === workflowId) {
        setWorkflow({
          id: currentWorkflow.id,
          name: currentWorkflow.name || `Workflow ${workflowId}`,
          description: currentWorkflow.description,
          complexity: getWorkflowComplexity(currentWorkflow),
          nodeCount: currentWorkflow.nodes?.length || 0,
          edgeCount: currentWorkflow.edges?.length || 0,
          createdAt: currentWorkflow.createdAt || new Date().toISOString(),
          updatedAt: currentWorkflow.updatedAt || new Date().toISOString()
        })
        setIsLoading(false)
        return
      }
      
      // Otherwise fetch from API
      const response = await fetch(`/api/workflows/${workflowId}`)
      if (!response.ok) {
        throw new Error('Failed to load workflow')
      }
      
      const workflowData = await response.json()
      setWorkflow(workflowData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workflow')
    } finally {
      setIsLoading(false)
    }
  }
  
  const getWorkflowComplexity = (workflow: any): 'simple' | 'medium' | 'complex' => {
    if (!workflow.nodes) return 'simple'
    
    const nodeCount = workflow.nodes.length
    const edgeCount = workflow.edges?.length || 0
    const totalComplexity = nodeCount + edgeCount
    
    if (totalComplexity <= 5) return 'simple'
    if (totalComplexity <= 15) return 'medium'
    return 'complex'
  }
  
  const getEstimatedDuration = (complexity: string, nodeCount: number) => {
    const baseDurations = {
      simple: { strategy: '< 30 seconds', model: '30-60 minutes' },
      medium: { strategy: '< 1 minute', model: '1-4 hours' },
      complex: { strategy: '< 2 minutes', model: '4-12 hours' }
    }
    
    return baseDurations[complexity as keyof typeof baseDurations] || baseDurations.medium
  }
  
  const handleModeSelect = async (mode: 'strategy' | 'model', config: any) => {
    try {
      setExecutionStatus('executing')
      await startExecution(workflowId, mode, config)
      
      // Navigate based on execution mode
      if (mode === 'strategy') {
        // For strategy mode, navigate to results page
        router.push(`/workflows/${workflowId}/results/strategy?executionId=${Date.now()}`)
      } else {
        // For model mode, navigate to training dashboard
        const jobId = currentExecution.jobId
        if (jobId) {
          router.push(`/workflows/${workflowId}/training/${jobId}`)
        }
      }
    } catch (error) {
      console.error('Execution failed:', error)
    }
  }
  
  const handleCancel = () => {
    router.back()
  }
  
  const handleBackToEditor = () => {
    router.push(`/strategy-hub?workflow=${workflowId}`)
  }
  
  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-muted-foreground">Loading workflow...</p>
          </div>
        </div>
      </div>
    )
  }
  
  if (error || !workflow) {
    return (
      <div className="container mx-auto py-8">
        <div className="max-w-2xl mx-auto">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error || 'Workflow not found'}
            </AlertDescription>
          </Alert>
          <div className="mt-4">
            <Button variant="outline" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={handleBackToEditor}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Editor
              </Button>
              <div className="h-6 border-l border-gray-300" />
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Execute Workflow</h1>
                <p className="text-muted-foreground">
                  Choose how you want to execute "{workflow.name}"
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Badge variant="outline">
                {workflow.nodeCount} nodes, {workflow.edgeCount} connections
              </Badge>
              <Badge className={
                workflow.complexity === 'simple' ? 'bg-green-100 text-green-800' :
                workflow.complexity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }>
                {workflow.complexity} complexity
              </Badge>
            </div>
          </div>
          
          {/* Workflow Overview Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span>Workflow Ready</span>
              </CardTitle>
              <CardDescription>
                Your workflow has been validated and is ready for execution
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 border rounded">
                  <div className="text-2xl font-bold text-blue-600">{workflow.nodeCount}</div>
                  <div className="text-sm text-muted-foreground">Components</div>
                </div>
                <div className="text-center p-4 border rounded">
                  <div className="text-2xl font-bold text-purple-600">{workflow.edgeCount}</div>
                  <div className="text-sm text-muted-foreground">Connections</div>
                </div>
                <div className="text-center p-4 border rounded">
                  <div className="text-2xl font-bold text-orange-600 capitalize">{workflow.complexity}</div>
                  <div className="text-sm text-muted-foreground">Complexity</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Return Context Alert */}
        {returnFrom && (
          <div className="mb-6">
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                {returnFrom === 'training' && 'Training in progress. You can change execution settings or start a new execution.'}
                {returnFrom === 'results' && 'Previous execution completed. You can run the workflow again with different settings.'}
              </AlertDescription>
            </Alert>
          </div>
        )}
        
        {/* Error Display */}
        {lastError && (
          <div className="mb-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {lastError}
              </AlertDescription>
            </Alert>
          </div>
        )}
        
        {/* Execution Mode Selector */}
        <ExecutionModeSelector
          workflowId={workflow.id}
          workflowName={workflow.name}
          workflowComplexity={workflow.complexity}
          onModeSelect={handleModeSelect}
          onCancel={handleCancel}
          isLoading={currentExecution.status === 'executing'}
          estimatedDuration={getEstimatedDuration(workflow.complexity || 'medium', workflow.nodeCount)}
        />
      </div>
    </div>
  )
}