'use client'

import React, { useEffect, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'

// Disable static generation for this page as it uses searchParams
export const dynamic = 'force-dynamic';
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { TrainingDashboard } from '@/components/no-code/TrainingDashboard'
import { useExecutionStore, useTrainingJob } from '@/lib/stores/execution-store'
import { ArrowLeft, ExternalLink, Settings, AlertCircle } from 'lucide-react'

interface TrainingPageParams extends Record<string, string> {
  id: string // workflow id
  jobId: string // training job id
}

export default function TrainingJobPage() {
  const params = useParams<TrainingPageParams>()
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const workflowId = parseInt(params.id)
  const jobId = params.jobId
  
  const [workflowName, setWorkflowName] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const trainingJob = useTrainingJob(jobId)
  const { 
    updateTrainingJob, 
    openTrainingDashboard,
    setCurrentWorkflow,
    setExecutionStatus
  } = useExecutionStore()
  
  // Check if this is a fresh navigation or returning from another page
  const autoStart = searchParams.get('autoStart') === 'true'
  const fromExecution = searchParams.get('from') === 'execute'
  
  useEffect(() => {
    // Set context
    setCurrentWorkflow(workflowId)
    openTrainingDashboard(jobId)
    
    // Load initial data
    loadTrainingJobInfo()
    
    // Start monitoring if job exists
    if (trainingJob) {
      setExecutionStatus('monitoring')
    }
  }, [workflowId, jobId])
  
  const loadTrainingJobInfo = async () => {
    try {
      setIsLoading(true)
      
      // If we have the training job in store, use its data
      if (trainingJob) {
        setWorkflowName(trainingJob.workflowName)
        setIsLoading(false)
        return
      }
      
      // Otherwise fetch job info from API
      const response = await fetch(`/api/training/jobs/${jobId}`)
      if (!response.ok) {
        throw new Error('Failed to load training job')
      }
      
      const jobData = await response.json()
      setWorkflowName(jobData.workflow_name || `Workflow ${workflowId}`)
      
      // Update store with fetched data
      updateTrainingJob(jobId, {
        ...jobData,
        workflowId,
        workflowName: jobData.workflow_name || `Workflow ${workflowId}`,
        lastUpdated: new Date().toISOString()
      })
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load training job')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleTrainingComplete = (results: any) => {
    setExecutionStatus('completed')
    
    // Navigate to results page
    router.push(`/workflows/${workflowId}/results/training?jobId=${jobId}&executionId=${Date.now()}`)
  }
  
  const handleCancel = async () => {
    try {
      const response = await fetch(`/api/training/jobs/${jobId}/cancel`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error('Failed to cancel training job')
      }
      
      // Navigate back to execution page
      router.push(`/workflows/${workflowId}/execute?from=training`)
    } catch (err) {
      console.error('Failed to cancel training:', err)
    }
  }
  
  const handlePause = async () => {
    try {
      await fetch(`/api/training/jobs/${jobId}/pause`, { method: 'POST' })
    } catch (err) {
      console.error('Failed to pause training:', err)
    }
  }
  
  const handleResume = async () => {
    try {
      await fetch(`/api/training/jobs/${jobId}/resume`, { method: 'POST' })
    } catch (err) {
      console.error('Failed to resume training:', err)
    }
  }
  
  const handleBackToWorkflow = () => {
    router.push(`/strategy-hub?workflow=${workflowId}`)
  }
  
  const handleEditExecution = () => {
    router.push(`/workflows/${workflowId}/execute?from=training&jobId=${jobId}`)
  }
  
  const getStatusBadgeColor = (status?: string) => {
    switch (status) {
      case 'queued':
        return 'bg-yellow-100 text-yellow-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'cancelled':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }
  
  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-muted-foreground">Loading training job...</p>
          </div>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="container mx-auto py-8">
        <div className="max-w-2xl mx-auto">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <div className="mt-4 flex space-x-2">
            <Button variant="outline" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
            <Button onClick={() => window.location.reload()}>
              Try Again
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
              <Button variant="ghost" onClick={handleBackToWorkflow}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Workflow
              </Button>
              <div className="h-6 border-l border-gray-300" />
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Training Monitor</h1>
                <p className="text-muted-foreground">
                  Monitoring AI optimization for "{workflowName}"
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Badge variant="outline">Job ID: {jobId}</Badge>
              {trainingJob?.status && (
                <Badge className={getStatusBadgeColor(trainingJob.status)}>
                  {trainingJob.status.toUpperCase()}
                </Badge>
              )}
              <Button variant="outline" size="sm" onClick={handleEditExecution}>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
          
          {/* Context Alerts */}
          {fromExecution && (
            <div className="mb-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Training job started successfully. You can monitor progress below or navigate away and return later.
                </AlertDescription>
              </Alert>
            </div>
          )}
          
          {autoStart && (
            <div className="mb-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Training resumed from previous session. Current progress is displayed below.
                </AlertDescription>
              </Alert>
            </div>
          )}
        </div>
        
        {/* Training Dashboard */}
        <div className="space-y-6">
          <TrainingDashboard
            jobId={jobId}
            workflowName={workflowName}
            onTrainingComplete={handleTrainingComplete}
            onCancel={handleCancel}
            onPause={handlePause}
            onResume={handleResume}
          />
          
          {/* Action Links */}
          <div className="flex justify-center space-x-4 pt-6 border-t">
            <Button variant="outline" onClick={handleEditExecution}>
              <Settings className="h-4 w-4 mr-2" />
              Modify Settings
            </Button>
            
            <Button variant="outline" onClick={() => window.open(`/api/training/jobs/${jobId}/logs`, '_blank')}>
              <ExternalLink className="h-4 w-4 mr-2" />
              View Full Logs
            </Button>
            
            {trainingJob?.status === 'completed' && (
              <Button onClick={() => router.push(`/workflows/${workflowId}/results/training?jobId=${jobId}`)}>
                View Results
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
