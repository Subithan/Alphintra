// No-Code Service API Client
// Handles all API calls related to workflow management, compilation, and execution

import { BaseApiClient } from './api-client';

// Types for No-Code API
export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    parameters?: Record<string, any>;
    [key: string]: any;
  };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface WorkflowData {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Workflow {
  id: number;
  uuid: string;
  name: string;
  description?: string;
  category: string;
  tags: string[];
  workflow_data: WorkflowData;
  generated_code?: string;
  generated_code_language: string;
  generated_requirements: string[];
  compilation_status: 'pending' | 'compiling' | 'compiled' | 'failed';
  compilation_errors: any[];
  validation_status: string;
  validation_errors: any[];
  deployment_status: string;
  execution_mode: 'backtest' | 'paper_trade' | 'live_trade';
  version: number;
  is_template: boolean;
  is_public: boolean;
  total_executions: number;
  successful_executions: number;
  avg_performance_score?: number;
  last_execution_at?: string;
  created_at: string;
  updated_at: string;
  published_at?: string;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  category?: string;
  tags?: string[];
  workflow_data?: WorkflowData;
  execution_mode?: 'backtest' | 'paper_trade' | 'live_trade';
}

export interface WorkflowUpdate {
  name?: string;
  description?: string;
  category?: string;
  tags?: string[];
  workflow_data?: WorkflowData;
  execution_mode?: string;
  is_public?: boolean;
}

export interface ExecutionConfig {
  execution_type: 'backtest' | 'paper_trade' | 'live_trade';
  symbols: string[];
  timeframe: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d';
  start_date?: string;
  end_date?: string;
  initial_capital: number;
  parameters?: Record<string, any>;
}

export interface Execution {
  id: number;
  uuid: string;
  workflow_id: number;
  execution_type: string;
  symbols: string[];
  timeframe: string;
  start_date?: string;
  end_date?: string;
  initial_capital: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_step?: string;
  final_capital?: number;
  total_return?: number;
  total_return_percent?: number;
  sharpe_ratio?: number;
  max_drawdown_percent?: number;
  total_trades: number;
  winning_trades: number;
  trades_data: any[];
  performance_metrics: Record<string, any>;
  execution_logs: any[];
  error_logs: any[];
  started_at: string;
  completed_at?: string;
  created_at: string;
}

export interface CompilationResult {
  workflow_id: string;
  generated_code: string;
  requirements: string[];
  status: 'compiling' | 'compiled' | 'failed';
  errors: any[];
  created_at: string;
}

export interface Component {
  id: number;
  uuid: string;
  name: string;
  display_name: string;
  description?: string;
  category: string;
  subcategory?: string;
  component_type: string;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  parameters_schema: Record<string, any>;
  default_parameters: Record<string, any>;
  code_template: string;
  imports_required: string[];
  dependencies: string[];
  ui_config: Record<string, any>;
  icon?: string;
  is_builtin: boolean;
  is_public: boolean;
  usage_count: number;
  rating?: number;
  created_at: string;
  updated_at: string;
}

export interface Template {
  id: number;
  uuid: string;
  name: string;
  description?: string;
  category: string;
  difficulty_level: string;
  template_data: WorkflowData;
  preview_image_url?: string;
  author_id?: number;
  is_featured: boolean;
  is_public: boolean;
  usage_count: number;
  rating?: number;
  keywords: string[];
  estimated_time_minutes?: number;
  expected_performance: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface WorkflowFilters {
  skip?: number;
  limit?: number;
  category?: string;
  is_public?: boolean;
}

export interface ComponentFilters {
  category?: string;
  is_builtin?: boolean;
}

export interface TemplateFilters {
  category?: string;
  difficulty_level?: string;
  is_featured?: boolean;
}

export class NoCodeApiClient extends BaseApiClient {
  constructor() {
    super({
      baseUrl: process.env.NEXT_PUBLIC_NOCODE_API_URL || 'http://localhost:8004',
    });
  }

  // Workflow Management
  async createWorkflow(workflow: WorkflowCreate): Promise<Workflow> {
    return this.requestWithRetry<Workflow>('/api/workflows', {
      method: 'POST',
      body: JSON.stringify(workflow),
    });
  }

  async getWorkflows(filters: WorkflowFilters = {}): Promise<Workflow[]> {
    const queryString = this.buildQueryString(filters);
    const endpoint = queryString ? `/api/workflows?${queryString}` : '/api/workflows';
    return this.requestWithRetry<Workflow[]>(endpoint);
  }

  async getWorkflow(workflowId: string): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(`/api/workflows/${workflowId}`);
  }

  async updateWorkflow(workflowId: string, updates: WorkflowUpdate): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(`/api/workflows/${workflowId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteWorkflow(workflowId: string): Promise<{ message: string }> {
    return this.requestWithRetry<{ message: string }>(`/api/workflows/${workflowId}`, {
      method: 'DELETE',
    });
  }

  // Code Generation
  async compileWorkflow(workflowId: string): Promise<CompilationResult> {
    return this.requestWithRetry<CompilationResult>(`/api/workflows/${workflowId}/compile`, {
      method: 'POST',
    });
  }

  // Execution
  async executeWorkflow(workflowId: string, config: ExecutionConfig): Promise<Execution> {
    return this.requestWithRetry<Execution>(`/api/workflows/${workflowId}/execute`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getExecution(executionId: string): Promise<Execution> {
    return this.requestWithRetry<Execution>(`/api/executions/${executionId}`);
  }

  // Component Library
  async getComponents(filters: ComponentFilters = {}): Promise<Component[]> {
    const queryString = this.buildQueryString(filters);
    const endpoint = queryString ? `/api/components?${queryString}` : '/api/components';
    return this.requestWithRetry<Component[]>(endpoint);
  }

  // Template Library
  async getTemplates(filters: TemplateFilters = {}): Promise<Template[]> {
    const queryString = this.buildQueryString(filters);
    const endpoint = queryString ? `/api/templates?${queryString}` : '/api/templates';
    return this.requestWithRetry<Template[]>(endpoint);
  }

  async createWorkflowFromTemplate(templateId: string, workflowName: string): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(`/api/templates/${templateId}/use`, {
      method: 'POST',
      body: JSON.stringify({ workflow_name: workflowName }),
    });
  }

  // Health Check - override base class method to match expected interface
  async healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    timestamp: string;
    services: Record<string, 'up' | 'down'>;
  }> {
    const result = await this.request<{
      status: string;
      service: string;
      version: string;
    }>('/health');
    
    // Transform the response to match the base class interface
    return {
      status: result.status === 'ok' ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      services: {
        [result.service]: result.status === 'ok' ? 'up' : 'down'
      }
    };
  }
}

// Export singleton instance
export const noCodeApiClient = new NoCodeApiClient();