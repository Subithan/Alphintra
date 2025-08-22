"use client"

import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Play, 
  Pause, 
  Square, 
  Clock, 
  Cpu, 
  HardDrive, 
  Zap, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle, 
  XCircle,
  Activity,
  BarChart3,
  Download,
  RefreshCw,
  Eye,
  Timer
} from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

interface TrainingMetrics {
  current_trial: number
  total_trials: number
  best_score: number
  current_score?: number
  trials_remaining: number
  convergence_achieved?: boolean
  best_parameters?: Record<string, any>
  validation_metrics?: {
    cv_score: number
    stability_score: number
    out_of_sample_sharpe?: number
    walk_forward_stability?: number
  }
}

interface ResourceUsage {
  cpu_percent: number
  memory_percent: number
  gpu_percent?: number
  gpu_memory_percent?: number
  disk_io_mb_per_sec: number
  network_io_mb_per_sec: number
}

interface TrainingState {
  job_id: string
  workflow_id: number
  workflow_name: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout'
  progress: number
  current_step: string
  started_at?: string
  estimated_completion?: string
  elapsed_minutes: number
  estimated_remaining_minutes: number
  queue_position?: number
  metrics?: TrainingMetrics
  resource_usage?: ResourceUsage
  logs: Array<{
    timestamp: string
    level: 'info' | 'warning' | 'error' | 'debug'
    message: string
  }>
  performance_history: Array<{
    timestamp: string
    trial: number
    score: number
    parameters: Record<string, any>
  }>
}

interface TrainingDashboardProps {
  jobId: string
  workflowName: string
  onTrainingComplete?: (results: any) => void
  onCancel?: () => void
  onPause?: () => void
  onResume?: () => void
  refreshInterval?: number
}

export function TrainingDashboard({
  jobId,
  workflowName,
  onTrainingComplete,
  onCancel,
  onPause,
  onResume,
  refreshInterval = 5000
}: TrainingDashboardProps) {
  const [trainingState, setTrainingState] = useState<TrainingState | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [selectedTab, setSelectedTab] = useState('overview')
  const wsRef = useRef<WebSocket | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Initialize WebSocket connection or polling
  useEffect(() => {
    const initializeConnection = async () => {
      try {
        // Try WebSocket first for real-time updates
        const wsUrl = `ws://localhost:8002/training/jobs/${jobId}/updates`
        const ws = new WebSocket(wsUrl)
        
        ws.onopen = () => {
          console.log('WebSocket connected for training updates')
          wsRef.current = ws
          setIsLoading(false)
        }
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            updateTrainingState(data)
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err)
          }
        }
        
        ws.onerror = () => {
          console.log('WebSocket failed, falling back to polling')
          fallbackToPolling()
        }
        
        ws.onclose = () => {
          if (wsRef.current === ws) {
            console.log('WebSocket closed, attempting to reconnect')
            setTimeout(initializeConnection, 5000)
          }
        }
        
        // Set timeout for WebSocket connection
        setTimeout(() => {
          if (ws.readyState === WebSocket.CONNECTING) {
            ws.close()
            fallbackToPolling()
          }
        }, 10000)
        
      } catch (error) {
        console.error('Failed to establish WebSocket connection:', error)
        fallbackToPolling()
      }
    }

    const fallbackToPolling = () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      
      // Start polling
      const poll = async () => {
        try {
          const response = await fetch(`/api/training/jobs/${jobId}`)
          if (response.ok) {
            const data = await response.json()
            updateTrainingState(data)
            setIsLoading(false)
          } else {
            throw new Error(`Failed to fetch training status: ${response.status}`)
          }
        } catch (err) {
          console.error('Polling error:', err)
          setError(err instanceof Error ? err.message : 'Failed to fetch training status')
        }
      }
      
      poll() // Initial poll
      if (autoRefresh) {
        intervalRef.current = setInterval(poll, refreshInterval)
      }
    }

    initializeConnection()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [jobId, refreshInterval, autoRefresh])

  // Handle training completion
  useEffect(() => {
    if (trainingState?.status === 'completed' && onTrainingComplete) {
      onTrainingComplete(trainingState)
    }
  }, [trainingState?.status, onTrainingComplete])

  const updateTrainingState = (data: Partial<TrainingState>) => {
    setTrainingState(prev => {
      if (!prev) {
        return data as TrainingState
      }
      
      return {
        ...prev,
        ...data,
        logs: data.logs ? [...(prev.logs || []), ...data.logs] : prev.logs,
        performance_history: data.performance_history 
          ? [...(prev.performance_history || []), ...data.performance_history]
          : prev.performance_history
      }
    })
    setError(null)
  }

  const handleAction = async (action: 'pause' | 'resume' | 'cancel') => {
    try {
      const response = await fetch(`/api/training/jobs/${jobId}/${action}`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error(`Failed to ${action} training job`)
      }
      
      // Trigger callbacks
      switch (action) {
        case 'pause':
          onPause?.()
          break
        case 'resume':
          onResume?.()
          break
        case 'cancel':
          onCancel?.()
          break
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} training`)
    }
  }

  const getStatusColor = (status: string) => {
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
      case 'timeout':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'queued':
        return <Clock className="h-4 w-4" />
      case 'running':
        return <Play className="h-4 w-4" />
      case 'completed':
        return <CheckCircle className="h-4 w-4" />
      case 'failed':
        return <XCircle className="h-4 w-4" />
      case 'cancelled':
        return <Square className="h-4 w-4" />
      default:
        return <AlertCircle className="h-4 w-4" />
    }
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes}m`
    }
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return `${hours}h ${remainingMinutes}m`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center space-y-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-muted-foreground">Loading training status...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!trainingState) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>No training data available</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Training Dashboard</h2>
          <p className="text-muted-foreground">{workflowName}</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto' : 'Manual'}
          </Button>
          {trainingState.status === 'running' && (
            <>
              <Button variant="outline" size="sm" onClick={() => handleAction('pause')}>
                <Pause className="h-4 w-4" />
                Pause
              </Button>
              <Button variant="destructive" size="sm" onClick={() => handleAction('cancel')}>
                <Square className="h-4 w-4" />
                Cancel
              </Button>
            </>
          )}
          {trainingState.status === 'paused' && (
            <Button variant="outline" size="sm" onClick={() => handleAction('resume')}>
              <Play className="h-4 w-4" />
              Resume
            </Button>
          )}
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              {getStatusIcon(trainingState.status)}
              <Badge className={getStatusColor(trainingState.status)}>
                {trainingState.status.toUpperCase()}
              </Badge>
            </div>
            <div className="mt-2">
              <p className="text-sm text-muted-foreground">Current Status</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-blue-600" />
              <span className="text-2xl font-bold">{Math.round(trainingState.progress * 100)}%</span>
            </div>
            <div className="mt-2">
              <p className="text-sm text-muted-foreground">Progress</p>
              <Progress value={trainingState.progress * 100} className="mt-1" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Timer className="h-5 w-5 text-green-600" />
              <span className="text-2xl font-bold">{formatDuration(trainingState.elapsed_minutes)}</span>
            </div>
            <div className="mt-2">
              <p className="text-sm text-muted-foreground">Elapsed Time</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-orange-600" />
              <span className="text-2xl font-bold">
                {trainingState.estimated_remaining_minutes > 0 
                  ? formatDuration(trainingState.estimated_remaining_minutes)
                  : '—'
                }
              </span>
            </div>
            <div className="mt-2">
              <p className="text-sm text-muted-foreground">Est. Remaining</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Current Step */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center space-x-2 mb-2">
            <Eye className="h-5 w-5 text-blue-600" />
            <h3 className="font-semibold">Current Step</h3>
          </div>
          <p className="text-lg">{trainingState.current_step}</p>
          {trainingState.status === 'queued' && trainingState.queue_position && (
            <p className="text-sm text-muted-foreground mt-1">
              Position in queue: {trainingState.queue_position}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Detailed Information Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Training Metrics */}
          {trainingState.metrics && (
            <Card>
              <CardHeader>
                <CardTitle>Optimization Progress</CardTitle>
                <CardDescription>Current trial performance and parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {trainingState.metrics.current_trial}
                    </p>
                    <p className="text-sm text-muted-foreground">Current Trial</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">
                      {trainingState.metrics.best_score.toFixed(4)}
                    </p>
                    <p className="text-sm text-muted-foreground">Best Score</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-orange-600">
                      {trainingState.metrics.trials_remaining}
                    </p>
                    <p className="text-sm text-muted-foreground">Trials Remaining</p>
                  </div>
                </div>

                <Progress 
                  value={(trainingState.metrics.current_trial / trainingState.metrics.total_trials) * 100} 
                  className="h-2"
                />

                {trainingState.metrics.convergence_achieved && (
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      Convergence achieved! The optimization has found stable parameters.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}

          {/* Best Parameters */}
          {trainingState.metrics?.best_parameters && (
            <Card>
              <CardHeader>
                <CardTitle>Best Parameters Found</CardTitle>
                <CardDescription>Current optimal parameter values</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.entries(trainingState.metrics.best_parameters).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center p-2 bg-muted/20 rounded">
                      <span className="font-medium">{key}</span>
                      <Badge variant="outline">
                        {typeof value === 'number' ? value.toFixed(4) : String(value)}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          {/* Performance Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Performance History</CardTitle>
              <CardDescription>Score progression over optimization trials</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trainingState.performance_history}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="trial" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value, name) => [
                        typeof value === 'number' ? value.toFixed(4) : value,
                        name
                      ]}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="score" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Validation Metrics */}
          {trainingState.metrics?.validation_metrics && (
            <Card>
              <CardHeader>
                <CardTitle>Validation Metrics</CardTitle>
                <CardDescription>Out-of-sample performance validation</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="text-center p-4 border rounded">
                    <p className="text-xl font-bold">
                      {trainingState.metrics.validation_metrics.cv_score.toFixed(4)}
                    </p>
                    <p className="text-sm text-muted-foreground">Cross-Validation Score</p>
                  </div>
                  <div className="text-center p-4 border rounded">
                    <p className="text-xl font-bold">
                      {trainingState.metrics.validation_metrics.stability_score.toFixed(4)}
                    </p>
                    <p className="text-sm text-muted-foreground">Stability Score</p>
                  </div>
                  {trainingState.metrics.validation_metrics.out_of_sample_sharpe && (
                    <div className="text-center p-4 border rounded">
                      <p className="text-xl font-bold">
                        {trainingState.metrics.validation_metrics.out_of_sample_sharpe.toFixed(4)}
                      </p>
                      <p className="text-sm text-muted-foreground">Out-of-Sample Sharpe</p>
                    </div>
                  )}
                  {trainingState.metrics.validation_metrics.walk_forward_stability && (
                    <div className="text-center p-4 border rounded">
                      <p className="text-xl font-bold">
                        {trainingState.metrics.validation_metrics.walk_forward_stability.toFixed(4)}
                      </p>
                      <p className="text-sm text-muted-foreground">Walk-Forward Stability</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          {/* Resource Usage */}
          {trainingState.resource_usage && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Cpu className="h-5 w-5" />
                    <span>CPU Usage</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Usage</span>
                      <span>{Math.round(trainingState.resource_usage.cpu_percent)}%</span>
                    </div>
                    <Progress value={trainingState.resource_usage.cpu_percent} />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <HardDrive className="h-5 w-5" />
                    <span>Memory Usage</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Usage</span>
                      <span>{Math.round(trainingState.resource_usage.memory_percent)}%</span>
                    </div>
                    <Progress value={trainingState.resource_usage.memory_percent} />
                  </div>
                </CardContent>
              </Card>

              {trainingState.resource_usage.gpu_percent !== undefined && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Zap className="h-5 w-5" />
                      <span>GPU Usage</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>GPU</span>
                        <span>{Math.round(trainingState.resource_usage.gpu_percent)}%</span>
                      </div>
                      <Progress value={trainingState.resource_usage.gpu_percent} />
                      {trainingState.resource_usage.gpu_memory_percent !== undefined && (
                        <>
                          <div className="flex justify-between">
                            <span>GPU Memory</span>
                            <span>{Math.round(trainingState.resource_usage.gpu_memory_percent)}%</span>
                          </div>
                          <Progress value={trainingState.resource_usage.gpu_memory_percent} />
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle>I/O Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Disk I/O</span>
                      <span>{trainingState.resource_usage.disk_io_mb_per_sec.toFixed(1)} MB/s</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Network I/O</span>
                      <span>{trainingState.resource_usage.network_io_mb_per_sec.toFixed(1)} MB/s</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Training Logs</CardTitle>
              <CardDescription>Real-time training process logs</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-80 w-full border rounded p-2">
                <div className="space-y-1 font-mono text-sm">
                  {trainingState.logs.map((log, index) => (
                    <div key={index} className="flex space-x-2">
                      <span className="text-muted-foreground text-xs">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <Badge 
                        variant={
                          log.level === 'error' ? 'destructive' : 
                          log.level === 'warning' ? 'outline' : 
                          'secondary'
                        }
                        className="text-xs"
                      >
                        {log.level}
                      </Badge>
                      <span className="flex-1">{log.message}</span>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Download Results Button */}
      {trainingState.status === 'completed' && (
        <div className="flex justify-center">
          <Button className="flex items-center space-x-2">
            <Download className="h-4 w-4" />
            <span>Download Training Results</span>
          </Button>
        </div>
      )}
    </div>
  )
}