import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import { useCallback, useEffect } from 'react'
import { useExecutionStore } from './stores/execution-store'

/**
 * Hook for handling back/forward navigation with execution state synchronization
 */
export function useExecutionNavigation() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { syncFromURL, getURLState, cacheTrainingJobStatus, loadCachedTrainingJob } = useExecutionStore()

  // Sync URL parameters to execution store on route changes
  useEffect(() => {
    syncFromURL(searchParams)
  }, [searchParams, syncFromURL])

  // Navigate to execution flow pages with proper URL state
  const navigateToExecution = useCallback((workflowId: number, from?: string) => {
    const params = new URLSearchParams()
    if (from) params.set('from', from)
    
    const query = params.toString()
    router.push(`/workflows/${workflowId}/execute${query ? `?${query}` : ''}`)
  }, [router])

  const navigateToTraining = useCallback((workflowId: number, jobId: string, options?: {
    from?: string
    autoStart?: boolean
  }) => {
    const params = new URLSearchParams()
    if (options?.from) params.set('from', options.from)
    if (options?.autoStart) params.set('autoStart', 'true')
    
    // Cache training job status before navigation
    cacheTrainingJobStatus(jobId)
    
    const query = params.toString()
    router.push(`/workflows/${workflowId}/training/${jobId}${query ? `?${query}` : ''}`)
  }, [router, cacheTrainingJobStatus])

  const navigateToResults = useCallback((workflowId: number, executionType: 'strategy' | 'training', options?: {
    jobId?: string
    executionId?: string
  }) => {
    const params = new URLSearchParams()
    if (options?.jobId) params.set('jobId', options.jobId)
    if (options?.executionId) params.set('executionId', options.executionId)
    
    const query = params.toString()
    router.push(`/workflows/${workflowId}/results/${executionType}${query ? `?${query}` : ''}`)
  }, [router])

  const navigateToWorkflowEditor = useCallback((workflowId?: number) => {
    if (workflowId) {
      router.push(`/strategy-hub?workflow=${workflowId}`)
    } else {
      router.push('/strategy-hub')
    }
  }, [router])

  // Handle browser back/forward buttons
  const handleBrowserNavigation = useCallback(() => {
    // Sync state when user uses browser navigation
    syncFromURL(new URLSearchParams(window.location.search))
  }, [syncFromURL])

  // Listen for browser navigation events
  useEffect(() => {
    window.addEventListener('popstate', handleBrowserNavigation)
    return () => window.removeEventListener('popstate', handleBrowserNavigation)
  }, [handleBrowserNavigation])

  // Get current navigation context
  const getNavigationContext = useCallback(() => {
    const isExecutePage = pathname.includes('/execute')
    const isTrainingPage = pathname.includes('/training/')
    const isResultsPage = pathname.includes('/results/')
    const isWorkflowEditor = pathname.includes('/strategy-hub')
    
    return {
      isExecutePage,
      isTrainingPage,
      isResultsPage,
      isWorkflowEditor,
      currentPath: pathname,
      searchParams: Object.fromEntries(searchParams.entries())
    }
  }, [pathname, searchParams])

  return {
    navigateToExecution,
    navigateToTraining,
    navigateToResults,
    navigateToWorkflowEditor,
    getNavigationContext,
    currentPath: pathname,
    searchParams: Object.fromEntries(searchParams.entries())
  }
}

/**
 * Hook for handling training job deep linking and caching
 */
export function useTrainingJobLink(jobId: string) {
  const { 
    generateShareableLink, 
    isSharedSession, 
    loadCachedTrainingJob, 
    cacheTrainingJobStatus 
  } = useExecutionStore()

  const shareableLink = generateShareableLink(jobId)
  const isShared = isSharedSession()
  
  // Load cached data on mount if available
  useEffect(() => {
    const cachedData = loadCachedTrainingJob(jobId)
    if (cachedData && !isShared) {
      // Use cached data to initialize UI while fresh data loads
      console.log('Using cached training job data:', cachedData)
    }
  }, [jobId, loadCachedTrainingJob, isShared])

  // Cache job status periodically during training
  const enablePeriodicCaching = useCallback(() => {
    const interval = setInterval(() => {
      cacheTrainingJobStatus(jobId)
    }, 30000) // Cache every 30 seconds

    return () => clearInterval(interval)
  }, [jobId, cacheTrainingJobStatus])

  const copyShareableLink = useCallback(async () => {
    if (shareableLink) {
      try {
        await navigator.clipboard.writeText(shareableLink)
        return true
      } catch (error) {
        console.error('Failed to copy link:', error)
        return false
      }
    }
    return false
  }, [shareableLink])

  return {
    shareableLink,
    isShared,
    copyShareableLink,
    enablePeriodicCaching
  }
}

/**
 * Utility function to build workflow URLs with state preservation
 */
export function buildWorkflowURL(workflowId: number, page: 'edit' | 'execute' | 'training' | 'results', options?: {
  jobId?: string
  executionType?: 'strategy' | 'training'
  executionId?: string
  preserveState?: boolean
}) {
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : ''
  
  let path: string
  switch (page) {
    case 'edit':
      path = `/strategy-hub?workflow=${workflowId}`
      break
    case 'execute':
      path = `/workflows/${workflowId}/execute`
      break
    case 'training':
      if (!options?.jobId) throw new Error('jobId is required for training page')
      path = `/workflows/${workflowId}/training/${options.jobId}`
      break
    case 'results':
      if (!options?.executionType) throw new Error('executionType is required for results page')
      path = `/workflows/${workflowId}/results/${options.executionType}`
      break
    default:
      throw new Error(`Unknown page type: ${page}`)
  }
  
  // Add query parameters
  const params = new URLSearchParams()
  if (options?.jobId && page === 'results') params.set('jobId', options.jobId)
  if (options?.executionId) params.set('executionId', options.executionId)
  
  // Preserve current execution state if requested
  if (options?.preserveState && typeof window !== 'undefined') {
    const currentParams = new URLSearchParams(window.location.search)
    const stateParams = ['mode', 'status', 'from']
    
    stateParams.forEach(param => {
      const value = currentParams.get(param)
      if (value && !params.has(param)) {
        params.set(param, value)
      }
    })
  }
  
  const query = params.toString()
  return `${baseUrl}${path}${query ? `?${query}` : ''}`
}

/**
 * Check if current page is part of workflow execution flow
 */
export function isWorkflowExecutionPage(pathname: string): boolean {
  return pathname.includes('/workflows/') && 
         (pathname.includes('/execute') || 
          pathname.includes('/training/') || 
          pathname.includes('/results/'))
}

/**
 * Extract workflow ID from current pathname
 */
export function extractWorkflowId(pathname: string): number | null {
  const match = pathname.match(/\/workflows\/(\d+)/)
  return match ? parseInt(match[1]) : null
}

/**
 * Extract job ID from training page pathname
 */
export function extractJobId(pathname: string): string | null {
  const match = pathname.match(/\/training\/([^/?]+)/)
  return match ? match[1] : null
}