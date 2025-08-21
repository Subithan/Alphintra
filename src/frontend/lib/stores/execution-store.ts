import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface ExecutionState {
  // Current execution context
  currentWorkflowId: number | null
  currentExecutionMode: 'strategy' | 'model' | null
  currentJobId: string | null
  currentExecutionStatus: 'idle' | 'configuring' | 'executing' | 'monitoring' | 'completed' | 'failed'
  
  // Execution history
  executionHistory: ExecutionRecord[]
  
  // Training job monitoring
  trainingJobs: Record<string, TrainingJobState>
  
  // UI state
  isExecutionModalOpen: boolean
  isTrainingDashboardOpen: boolean
  activeTab: string
  
  // Error handling
  lastError: string | null
  retryCount: number
}

export interface ExecutionRecord {
  id: string
  workflowId: number
  workflowName: string
  mode: 'strategy' | 'model'
  jobId?: string
  status: 'success' | 'failed' | 'cancelled'
  startedAt: string
  completedAt?: string
  duration?: number
  config: any
  results?: any
}

export interface TrainingJobState {
  jobId: string
  workflowId: number
  workflowName: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout'
  progress: number
  currentStep: string
  startedAt: string
  estimatedCompletion?: string
  elapsedMinutes: number
  estimatedRemainingMinutes: number
  queuePosition?: number
  metrics?: {
    currentTrial: number
    totalTrials: number
    bestScore: number
    currentScore?: number
    trialsRemaining: number
    convergenceAchieved?: boolean
  }
  resourceUsage?: {
    cpuPercent: number
    memoryPercent: number
    gpuPercent?: number
    gpuMemoryPercent?: number
    diskIoMbPerSec: number
    networkIoMbPerSec: number
  }
  logs: Array<{
    timestamp: string
    level: 'info' | 'warning' | 'error' | 'debug'
    message: string
  }>
  lastUpdated: string
}

interface ExecutionActions {
  // Execution flow management
  startExecution: (workflowId: number, mode: 'strategy' | 'model', config: any) => Promise<void>
  setExecutionMode: (mode: 'strategy' | 'model' | null) => void
  setCurrentWorkflow: (workflowId: number | null) => void
  setExecutionStatus: (status: ExecutionState['currentExecutionStatus']) => void
  
  // Training job management
  createTrainingJob: (jobId: string, workflowId: number, workflowName: string) => void
  updateTrainingJob: (jobId: string, updates: Partial<TrainingJobState>) => void
  removeTrainingJob: (jobId: string) => void
  addTrainingLog: (jobId: string, log: TrainingJobState['logs'][0]) => void
  
  // Execution history
  addExecutionRecord: (record: Omit<ExecutionRecord, 'id'>) => void
  updateExecutionRecord: (id: string, updates: Partial<ExecutionRecord>) => void
  clearExecutionHistory: () => void
  
  // UI state management
  openExecutionModal: () => void
  closeExecutionModal: () => void
  openTrainingDashboard: (jobId: string) => void
  closeTrainingDashboard: () => void
  setActiveTab: (tab: string) => void
  
  // Error handling
  setError: (error: string | null) => void
  incrementRetryCount: () => void
  resetRetryCount: () => void
  
  // Utility actions
  reset: () => void
  getTrainingJob: (jobId: string) => TrainingJobState | undefined
  getExecutionRecord: (id: string) => ExecutionRecord | undefined
  
  // URL state management
  syncFromURL: (params: URLSearchParams) => void
  getURLState: () => string
  
  // Browser storage for training job caching
  cacheTrainingJobStatus: (jobId: string) => void
  loadCachedTrainingJob: (jobId: string) => any | null
  clearTrainingJobCache: (jobId: string) => void
  
  // Deep linking support
  generateShareableLink: (jobId: string) => string | null
  isSharedSession: () => boolean
}

type ExecutionStore = ExecutionState & ExecutionActions

const initialState: ExecutionState = {
  currentWorkflowId: null,
  currentExecutionMode: null,
  currentJobId: null,
  currentExecutionStatus: 'idle',
  executionHistory: [],
  trainingJobs: {},
  isExecutionModalOpen: false,
  isTrainingDashboardOpen: false,
  activeTab: 'overview',
  lastError: null,
  retryCount: 0
}

export const useExecutionStore = create<ExecutionStore>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      // Execution flow management
      startExecution: async (workflowId: number, mode: 'strategy' | 'model', config: any) => {
        const executionRecord: Omit<ExecutionRecord, 'id'> = {
          workflowId,
          workflowName: `Workflow ${workflowId}`,
          mode,
          status: 'success', // Will be updated based on result
          startedAt: new Date().toISOString(),
          config
        }
        
        set({ 
          currentWorkflowId: workflowId,
          currentExecutionMode: mode,
          currentExecutionStatus: 'executing',
          lastError: null
        })
        
        try {
          // API call would be made here in real implementation
          const response = await fetch(`/api/workflows/${workflowId}/execution-mode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, config })
          })
          
          if (!response.ok) {
            throw new Error('Execution failed')
          }
          
          const result = await response.json()
          
          if (mode === 'model' && result.training_job_id) {
            get().createTrainingJob(result.training_job_id, workflowId, executionRecord.workflowName)
            set({ 
              currentJobId: result.training_job_id,
              currentExecutionStatus: 'monitoring'
            })
          } else {
            set({ currentExecutionStatus: 'completed' })
          }
          
          get().addExecutionRecord({
            ...executionRecord,
            jobId: result.training_job_id,
            status: 'success',
            completedAt: new Date().toISOString(),
            results: result
          })
        } catch (error) {
          set({ 
            currentExecutionStatus: 'failed',
            lastError: error instanceof Error ? error.message : 'Unknown error'
          })
          
          get().addExecutionRecord({
            ...executionRecord,
            status: 'failed',
            completedAt: new Date().toISOString()
          })
        }
      },
      
      setExecutionMode: (mode) => set({ currentExecutionMode: mode }),
      setCurrentWorkflow: (workflowId) => set({ currentWorkflowId: workflowId }),
      setExecutionStatus: (status) => set({ currentExecutionStatus: status }),
      
      // Training job management
      createTrainingJob: (jobId: string, workflowId: number, workflowName: string) => {
        const newJob: TrainingJobState = {
          jobId,
          workflowId,
          workflowName,
          status: 'queued',
          progress: 0,
          currentStep: 'Initializing...',
          startedAt: new Date().toISOString(),
          elapsedMinutes: 0,
          estimatedRemainingMinutes: 0,
          logs: [{
            timestamp: new Date().toISOString(),
            level: 'info',
            message: 'Training job created'
          }],
          lastUpdated: new Date().toISOString()
        }
        
        set(state => ({
          trainingJobs: {
            ...state.trainingJobs,
            [jobId]: newJob
          }
        }))
      },
      
      updateTrainingJob: (jobId: string, updates: Partial<TrainingJobState>) => {
        set(state => ({
          trainingJobs: {
            ...state.trainingJobs,
            [jobId]: {
              ...state.trainingJobs[jobId],
              ...updates,
              lastUpdated: new Date().toISOString()
            }
          }
        }))
      },
      
      removeTrainingJob: (jobId: string) => {
        set(state => {
          const newJobs = { ...state.trainingJobs }
          delete newJobs[jobId]
          return { trainingJobs: newJobs }
        })
      },
      
      addTrainingLog: (jobId: string, log: TrainingJobState['logs'][0]) => {
        set(state => {
          const job = state.trainingJobs[jobId]
          if (!job) return state
          
          return {
            trainingJobs: {
              ...state.trainingJobs,
              [jobId]: {
                ...job,
                logs: [...job.logs, log],
                lastUpdated: new Date().toISOString()
              }
            }
          }
        })
      },
      
      // Execution history
      addExecutionRecord: (record: Omit<ExecutionRecord, 'id'>) => {
        const id = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        set(state => ({
          executionHistory: [
            { ...record, id },
            ...state.executionHistory
          ].slice(0, 50) // Keep only last 50 records
        }))
      },
      
      updateExecutionRecord: (id: string, updates: Partial<ExecutionRecord>) => {
        set(state => ({
          executionHistory: state.executionHistory.map(record =>
            record.id === id ? { ...record, ...updates } : record
          )
        }))
      },
      
      clearExecutionHistory: () => set({ executionHistory: [] }),
      
      // UI state management
      openExecutionModal: () => set({ isExecutionModalOpen: true }),
      closeExecutionModal: () => set({ isExecutionModalOpen: false }),
      openTrainingDashboard: (jobId: string) => set({ 
        isTrainingDashboardOpen: true,
        currentJobId: jobId
      }),
      closeTrainingDashboard: () => set({ 
        isTrainingDashboardOpen: false,
        currentJobId: null
      }),
      setActiveTab: (tab: string) => set({ activeTab: tab }),
      
      // Error handling
      setError: (error: string | null) => set({ lastError: error }),
      incrementRetryCount: () => set(state => ({ retryCount: state.retryCount + 1 })),
      resetRetryCount: () => set({ retryCount: 0 }),
      
      // Utility actions
      reset: () => set(initialState),
      getTrainingJob: (jobId: string) => get().trainingJobs[jobId],
      getExecutionRecord: (id: string) => get().executionHistory.find(r => r.id === id),
      
      // URL state management
      syncFromURL: (params: URLSearchParams) => {
        const workflowId = params.get('workflow')
        const jobId = params.get('jobId')
        const mode = params.get('mode') as 'strategy' | 'model' | null
        const status = params.get('status') as ExecutionState['currentExecutionStatus'] | null
        
        if (workflowId) set({ currentWorkflowId: parseInt(workflowId) })
        if (jobId) set({ currentJobId: jobId })
        if (mode) set({ currentExecutionMode: mode })
        if (status) set({ currentExecutionStatus: status })
      },
      
      getURLState: () => {
        const state = get()
        const params = new URLSearchParams()
        
        if (state.currentWorkflowId) params.set('workflow', state.currentWorkflowId.toString())
        if (state.currentJobId) params.set('jobId', state.currentJobId)
        if (state.currentExecutionMode) params.set('mode', state.currentExecutionMode)
        if (state.currentExecutionStatus !== 'idle') params.set('status', state.currentExecutionStatus)
        
        return params.toString()
      },
      
      // Browser storage for training job caching
      cacheTrainingJobStatus: (jobId: string) => {
        const job = get().trainingJobs[jobId]
        if (job) {
          try {
            localStorage.setItem(`training_job_${jobId}`, JSON.stringify({
              status: job.status,
              progress: job.progress,
              lastUpdated: job.lastUpdated,
              cached: true
            }))
          } catch (error) {
            console.warn('Failed to cache training job status:', error)
          }
        }
      },
      
      loadCachedTrainingJob: (jobId: string) => {
        try {
          const cached = localStorage.getItem(`training_job_${jobId}`)
          if (cached) {
            const data = JSON.parse(cached)
            // Only use cached data if it's recent (within 5 minutes)
            const cacheAge = Date.now() - new Date(data.lastUpdated).getTime()
            if (cacheAge < 5 * 60 * 1000) { // 5 minutes
              return data
            } else {
              // Remove stale cache
              localStorage.removeItem(`training_job_${jobId}`)
            }
          }
        } catch (error) {
          console.warn('Failed to load cached training job:', error)
        }
        return null
      },
      
      clearTrainingJobCache: (jobId: string) => {
        try {
          localStorage.removeItem(`training_job_${jobId}`)
        } catch (error) {
          console.warn('Failed to clear training job cache:', error)
        }
      },
      
      // Deep linking support
      generateShareableLink: (jobId: string) => {
        const job = get().trainingJobs[jobId]
        if (!job) return null
        
        const baseUrl = typeof window !== 'undefined' ? window.location.origin : ''
        return `${baseUrl}/workflows/${job.workflowId}/training/${jobId}?shared=true`
      },
      
      isSharedSession: () => {
        if (typeof window === 'undefined') return false
        return new URLSearchParams(window.location.search).get('shared') === 'true'
      }
    }),
    {
      name: 'execution-store',
      // Only persist certain fields
      partialize: (state) => ({
        executionHistory: state.executionHistory,
        trainingJobs: state.trainingJobs,
        currentWorkflowId: state.currentWorkflowId,
        currentJobId: state.currentJobId
      })
    }
  )
)

// Selector hooks for better performance
export const useCurrentExecution = () => useExecutionStore(state => ({
  workflowId: state.currentWorkflowId,
  mode: state.currentExecutionMode,
  jobId: state.currentJobId,
  status: state.currentExecutionStatus
}))

export const useTrainingJob = (jobId: string | null) => 
  useExecutionStore(state => jobId ? state.trainingJobs[jobId] : null)

export const useExecutionHistory = () => 
  useExecutionStore(state => state.executionHistory)

export const useExecutionModal = () => useExecutionStore(state => ({
  isOpen: state.isExecutionModalOpen,
  open: state.openExecutionModal,
  close: state.closeExecutionModal
}))

export const useTrainingDashboard = () => useExecutionStore(state => ({
  isOpen: state.isTrainingDashboardOpen,
  jobId: state.currentJobId,
  open: state.openTrainingDashboard,
  close: state.closeTrainingDashboard
}))