import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Request/Response Types
interface CodeGenerationRequest {
  prompt: string
  context?: string
  language?: string
  complexity_level?: 'beginner' | 'intermediate' | 'advanced'
  include_comments?: boolean
  max_tokens?: number
  preferred_provider?: 'openai' | 'anthropic' | 'gemini'
}

interface CodeExplanationRequest {
  code: string
  context?: string
  focus_areas?: string[]
  preferred_provider?: 'openai' | 'anthropic' | 'gemini'
}

interface CodeOptimizationRequest {
  code: string
  optimization_type?: 'performance' | 'readability' | 'security' | 'memory' | 'trading_specific'
  context?: string
  preserve_functionality?: boolean
  preferred_provider?: 'openai' | 'anthropic' | 'gemini'
}

interface CodeDebuggingRequest {
  code: string
  error_message?: string
  context?: string
  preferred_provider?: 'openai' | 'anthropic' | 'gemini'
}

export interface CodeGenerationResponse {
  success: boolean
  code: string
  explanation: string
  suggestions: string[]
  estimated_complexity: string
  tokens_used: number
  execution_time: number
  provider: string
  confidence_score: number
  request_id: string
}

interface CodeExplanationResponse {
  success: boolean
  explanation: string
  key_concepts: string[]
  potential_issues: string[]
  improvement_suggestions: string[]
  complexity_analysis: string
  tokens_used: number
  provider: string
  request_id: string
}

interface CodeOptimizationResponse {
  success: boolean
  optimized_code: string
  changes_made: string[]
  performance_impact: string
  risk_assessment: string
  before_after_comparison: any
  tokens_used: number
  provider: string
  request_id: string
}

interface CodeDebuggingResponse {
  success: boolean
  issue_analysis: string
  suggested_fixes: string[]
  corrected_code?: string
  explanation: string
  prevention_tips: string[]
  tokens_used: number
  provider: string
  request_id: string
}

interface TestGenerationResponse {
  success: boolean
  test_code: string
  test_cases: string[]
  coverage_analysis: string
  testing_strategy: string
  mock_data_suggestions: string[]
  tokens_used: number
  provider: string
  request_id: string
}

// Store State
interface AICodeState {
  // Operation states
  isGenerating: boolean
  isExplaining: boolean
  isOptimizing: boolean
  isDebugging: boolean
  isGeneratingTests: boolean

  // Current operation results
  lastGeneration: CodeGenerationResponse | null
  lastExplanation: CodeExplanationResponse | null
  lastOptimization: CodeOptimizationResponse | null
  lastDebugging: CodeDebuggingResponse | null
  lastTestGeneration: TestGenerationResponse | null

  // Settings
  settings: {
    defaultProvider: 'openai' | 'anthropic' | 'gemini'
    defaultComplexity: 'beginner' | 'intermediate' | 'advanced'
    includeComments: boolean
    maxTokens: number
    contextMode: 'full' | 'selection' | 'none'
    autoExplain: boolean
    autoOptimize: boolean
  }
  
  // Usage tracking
  usage: {
    totalRequests: number
    totalTokens: number
    requestsToday: number
    tokensToday: number
    lastResetDate: string
    operationCounts: {
      generate: number
      explain: number
      optimize: number
      debug: number
      test: number
    }
  }
  
  // Error handling
  error: string | null
  
  // History
  history: Array<{
    id: string
    type: 'generate' | 'explain' | 'optimize' | 'debug' | 'test'
    request: any
    response: any
    timestamp: string
  }>
}

interface AICodeActions {
  // Core operations
  generateCode: (request: CodeGenerationRequest) => Promise<CodeGenerationResponse>
  explainCode: (request: CodeExplanationRequest) => Promise<CodeExplanationResponse>
  optimizeCode: (request: CodeOptimizationRequest) => Promise<CodeOptimizationResponse>
  debugCode: (request: CodeDebuggingRequest) => Promise<CodeDebuggingResponse>
  generateTests: (request: { code: string; context?: string; test_type?: string }) => Promise<TestGenerationResponse>
  
  // Settings management
  updateSettings: (settings: Partial<AICodeState['settings']>) => void
  resetSettings: () => void
  
  // Usage management
  resetUsage: () => void
  getUsageStats: () => AICodeState['usage']
  
  // History management
  addToHistory: (entry: Omit<AICodeState['history'][0], 'id' | 'timestamp'>) => void
  clearHistory: () => void
  getHistoryByType: (type: AICodeState['history'][0]['type']) => AICodeState['history']
  
  // Error handling
  setError: (error: string | null) => void
  clearError: () => void
}

type AICodeStore = AICodeState & AICodeActions

const defaultSettings: AICodeState['settings'] = {
  defaultProvider: 'gemini',
  defaultComplexity: 'intermediate',
  includeComments: true,
  maxTokens: 2000,
  contextMode: 'full',
  autoExplain: false,
  autoOptimize: false
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  let data: any = null

  try {
    data = await response.json()
  } catch (error) {
    data = null
  }

  if (!response.ok) {
    const message =
      (data && (data.message || data.detail)) ||
      (typeof data === 'string' ? data : `Request failed with status ${response.status}`)

    throw new Error(message)
  }

  return data as T
}

const initialUsage: AICodeState['usage'] = {
  totalRequests: 0,
  totalTokens: 0,
  requestsToday: 0,
  tokensToday: 0,
  lastResetDate: new Date().toDateString(),
  operationCounts: {
    generate: 0,
    explain: 0,
    optimize: 0,
    debug: 0,
    test: 0
  }
}

const SUPPORTED_PROVIDERS: Array<AICodeState['settings']['defaultProvider']> = ['gemini']

const normalizeProvider = (
  requested?: 'openai' | 'anthropic' | 'gemini'
): 'gemini' => {
  return SUPPORTED_PROVIDERS.includes(requested as any) ? (requested as 'gemini') : 'gemini'
}

const initialState: AICodeState = {
  isGenerating: false,
  isExplaining: false,
  isOptimizing: false,
  isDebugging: false,
  isGeneratingTests: false,
  
  lastGeneration: null,
  lastExplanation: null,
  lastOptimization: null,
  lastDebugging: null,
  lastTestGeneration: null,
  
  settings: defaultSettings,
  usage: initialUsage,
  error: null,
  history: []
}

export const useAICodeStore = create<AICodeStore>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      generateCode: async (request: CodeGenerationRequest) => {
        set({ isGenerating: true, error: null })
        
        try {
          const response = await fetch('/api/ai/generate', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(typeof window !== 'undefined' && localStorage.getItem('alphintra_auth_token')
                ? { 'Authorization': `Bearer ${localStorage.getItem('alphintra_auth_token')}` }
                : {}),
            },
            body: JSON.stringify({
              ...request,
              preferred_provider: normalizeProvider(
                request.preferred_provider || get().settings.defaultProvider
              ),
              complexity_level: request.complexity_level || get().settings.defaultComplexity,
              include_comments: request.include_comments ?? get().settings.includeComments,
              max_tokens: request.max_tokens || get().settings.maxTokens
            })
          })
          
          const result = await parseJsonResponse<CodeGenerationResponse>(response)
          
          set({ 
            lastGeneration: result,
            isGenerating: false 
          })
          
          // Update usage stats
          const state = get()
          const today = new Date().toDateString()
          const isNewDay = state.usage.lastResetDate !== today
          
          set({
            usage: {
              ...state.usage,
              totalRequests: state.usage.totalRequests + 1,
              totalTokens: state.usage.totalTokens + result.tokens_used,
              requestsToday: isNewDay ? 1 : state.usage.requestsToday + 1,
              tokensToday: isNewDay ? result.tokens_used : state.usage.tokensToday + result.tokens_used,
              lastResetDate: today,
              operationCounts: {
                ...state.usage.operationCounts,
                generate: state.usage.operationCounts.generate + 1
              }
            }
          })
          
          // Add to history
          get().addToHistory({
            type: 'generate',
            request,
            response: result
          })
          
          return result
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to generate code'
          set({ error: errorMessage, isGenerating: false })
          throw error
        }
      },

      explainCode: async (request: CodeExplanationRequest) => {
        set({ isExplaining: true, error: null })
        
        try {
          const response = await fetch('/api/ai/explain', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(typeof window !== 'undefined' && localStorage.getItem('alphintra_auth_token')
                ? { 'Authorization': `Bearer ${localStorage.getItem('alphintra_auth_token')}` }
                : {}),
            },
            body: JSON.stringify({
              ...request,
              preferred_provider: normalizeProvider(
                request.preferred_provider || get().settings.defaultProvider
              )
            })
          })
          
          const result = await parseJsonResponse<CodeExplanationResponse>(response)
          
          set({ 
            lastExplanation: result,
            isExplaining: false 
          })
          
          // Update usage stats
          const state = get()
          const today = new Date().toDateString()
          const isNewDay = state.usage.lastResetDate !== today
          
          set({
            usage: {
              ...state.usage,
              totalRequests: state.usage.totalRequests + 1,
              totalTokens: state.usage.totalTokens + result.tokens_used,
              requestsToday: isNewDay ? 1 : state.usage.requestsToday + 1,
              tokensToday: isNewDay ? result.tokens_used : state.usage.tokensToday + result.tokens_used,
              lastResetDate: today,
              operationCounts: {
                ...state.usage.operationCounts,
                explain: state.usage.operationCounts.explain + 1
              }
            }
          })
          
          // Add to history
          get().addToHistory({
            type: 'explain',
            request,
            response: result
          })
          
          return result
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to explain code'
          set({ error: errorMessage, isExplaining: false })
          throw error
        }
      },

      optimizeCode: async (request: CodeOptimizationRequest) => {
        set({ isOptimizing: true, error: null })
        
        try {
          const response = await fetch('/api/ai/optimize', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(typeof window !== 'undefined' && localStorage.getItem('alphintra_auth_token')
                ? { 'Authorization': `Bearer ${localStorage.getItem('alphintra_auth_token')}` }
                : {}),
            },
            body: JSON.stringify({
              ...request,
              preferred_provider: normalizeProvider(
                request.preferred_provider || get().settings.defaultProvider
              )
            })
          })
          
          const result = await parseJsonResponse<CodeOptimizationResponse>(response)
          
          set({ 
            lastOptimization: result,
            isOptimizing: false 
          })
          
          // Update usage stats
          const state = get()
          const today = new Date().toDateString()
          const isNewDay = state.usage.lastResetDate !== today
          
          set({
            usage: {
              ...state.usage,
              totalRequests: state.usage.totalRequests + 1,
              totalTokens: state.usage.totalTokens + result.tokens_used,
              requestsToday: isNewDay ? 1 : state.usage.requestsToday + 1,
              tokensToday: isNewDay ? result.tokens_used : state.usage.tokensToday + result.tokens_used,
              lastResetDate: today,
              operationCounts: {
                ...state.usage.operationCounts,
                optimize: state.usage.operationCounts.optimize + 1
              }
            }
          })
          
          // Add to history
          get().addToHistory({
            type: 'optimize',
            request,
            response: result
          })
          
          return result
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to optimize code'
          set({ error: errorMessage, isOptimizing: false })
          throw error
        }
      },

      debugCode: async (request: CodeDebuggingRequest) => {
        set({ isDebugging: true, error: null })
        
        try {
          const response = await fetch('/api/ai/debug', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(typeof window !== 'undefined' && localStorage.getItem('alphintra_auth_token')
                ? { 'Authorization': `Bearer ${localStorage.getItem('alphintra_auth_token')}` }
                : {}),
            },
            body: JSON.stringify({
              ...request,
              preferred_provider: normalizeProvider(
                request.preferred_provider || get().settings.defaultProvider
              )
            })
          })
          
          const result = await parseJsonResponse<CodeDebuggingResponse>(response)
          
          set({ 
            lastDebugging: result,
            isDebugging: false 
          })
          
          // Update usage stats
          const state = get()
          const today = new Date().toDateString()
          const isNewDay = state.usage.lastResetDate !== today
          
          set({
            usage: {
              ...state.usage,
              totalRequests: state.usage.totalRequests + 1,
              totalTokens: state.usage.totalTokens + result.tokens_used,
              requestsToday: isNewDay ? 1 : state.usage.requestsToday + 1,
              tokensToday: isNewDay ? result.tokens_used : state.usage.tokensToday + result.tokens_used,
              lastResetDate: today,
              operationCounts: {
                ...state.usage.operationCounts,
                debug: state.usage.operationCounts.debug + 1
              }
            }
          })
          
          // Add to history
          get().addToHistory({
            type: 'debug',
            request,
            response: result
          })
          
          return result
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to debug code'
          set({ error: errorMessage, isDebugging: false })
          throw error
        }
      },

      generateTests: async (request: { code: string; context?: string; test_type?: string }) => {
        set({ isGeneratingTests: true, error: null })
        
        try {
          const response = await fetch('/api/ai/tests', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(typeof window !== 'undefined' && localStorage.getItem('alphintra_auth_token')
                ? { 'Authorization': `Bearer ${localStorage.getItem('alphintra_auth_token')}` }
                : {}),
            },
            body: JSON.stringify({
              ...request,
              test_type: request.test_type || 'unit',
              preferred_provider: normalizeProvider(get().settings.defaultProvider)
            })
          })
          
          const result = await parseJsonResponse<TestGenerationResponse>(response)
          
          set({ 
            lastTestGeneration: result,
            isGeneratingTests: false 
          })
          
          // Update usage stats
          const state = get()
          const today = new Date().toDateString()
          const isNewDay = state.usage.lastResetDate !== today
          
          set({
            usage: {
              ...state.usage,
              totalRequests: state.usage.totalRequests + 1,
              totalTokens: state.usage.totalTokens + result.tokens_used,
              requestsToday: isNewDay ? 1 : state.usage.requestsToday + 1,
              tokensToday: isNewDay ? result.tokens_used : state.usage.tokensToday + result.tokens_used,
              lastResetDate: today,
              operationCounts: {
                ...state.usage.operationCounts,
                test: state.usage.operationCounts.test + 1
              }
            }
          })
          
          // Add to history
          get().addToHistory({
            type: 'test',
            request,
            response: result
          })
          
          return result
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to generate tests'
          set({ error: errorMessage, isGeneratingTests: false })
          throw error
        }
      },

      updateSettings: (newSettings: Partial<AICodeState['settings']>) => {
        set(state => ({
          settings: { ...state.settings, ...newSettings }
        }))
      },

      resetSettings: () => {
        set({ settings: { ...defaultSettings } })
      },

      resetUsage: () => {
        set({ usage: { ...initialUsage } })
      },

      getUsageStats: () => get().usage,

      addToHistory: (entry: Omit<AICodeState['history'][0], 'id' | 'timestamp'>) => {
        const newEntry = {
          ...entry,
          id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date().toISOString()
        }
        
        set(state => ({
          history: [newEntry, ...state.history].slice(0, 100) // Keep only last 100 entries
        }))
      },

      clearHistory: () => {
        set({ history: [] })
      },

      getHistoryByType: (type: AICodeState['history'][0]['type']) => {
        return get().history.filter(entry => entry.type === type)
      },

      setError: (error: string | null) => {
        set({ error })
      },

      clearError: () => {
        set({ error: null })
      }
    }),
    {
      name: 'ai-code-store',
      partialize: (state) => ({
        settings: state.settings,
        usage: state.usage,
        history: state.history.slice(0, 50) // Persist only last 50 history entries
      })
    }
  )
)

// Selector hooks for performance
export const useAICodeSettings = () => useAICodeStore(state => state.settings)
export const useAICodeUsage = () => useAICodeStore(state => state.usage)
export const useAICodeHistory = () => useAICodeStore(state => state.history)
export const useAICodeError = () => useAICodeStore(state => state.error)

export const useAICodeOperationStates = () => useAICodeStore(state => ({
  isGenerating: state.isGenerating,
  isExplaining: state.isExplaining,
  isOptimizing: state.isOptimizing,
  isDebugging: state.isDebugging,
  isGeneratingTests: state.isGeneratingTests
}))
