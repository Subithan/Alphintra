// No-Code Service API Client
// Handles all API calls related to workflow management, compilation, and execution

import { BaseApiClient } from "./api-client";

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
  compilation_status: "pending" | "compiling" | "compiled" | "failed";
  compilation_errors: any[];
  validation_status: string;
  validation_errors: any[];
  deployment_status: string;
  execution_mode: "backtest" | "paper_trade" | "live_trade";
  version: number;
  parent_workflow_id?: number;
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

export interface WorkflowVersion {
  id: number;
  uuid: string;
  name: string;
  version: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
  changes_summary?: string;
  parent_workflow_id?: number;
}

export interface WorkflowVersionDetails extends Workflow {
  parent_workflow?: Workflow;
  child_versions?: WorkflowVersion[];
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  category?: string;
  tags?: string[];
  workflow_data?: WorkflowData;
  execution_mode?: "backtest" | "paper_trade" | "live_trade";
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
  execution_type: "backtest" | "paper_trade" | "live_trade";
  symbols: string[];
  timeframe: "1m" | "5m" | "15m" | "30m" | "1h" | "4h" | "1d";
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
  status: "pending" | "running" | "completed" | "failed";
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
  status: "compiling" | "compiled" | "failed";
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
      baseUrl:
        process.env.NEXT_PUBLIC_NOCODE_API_URL || "http://localhost:8006",
    });

    // Debug logging only in development mode and when explicitly enabled
    if (
      process.env.NODE_ENV === "development" &&
      process.env.NEXT_PUBLIC_DEBUG_API === "true"
    ) {
      console.log("🔧 NoCodeApiClient Debug:", {
        baseUrl: this.config.baseUrl,
      });
    }
  }

  // Workflow Management
  async createWorkflow(workflow: WorkflowCreate): Promise<Workflow> {
    return this.requestWithRetry<Workflow>("/api/workflows", {
      method: "POST",
      body: JSON.stringify(workflow),
    });
  }

  async getWorkflows(filters: WorkflowFilters = {}): Promise<Workflow[]> {
    const queryString = this.buildQueryString(filters);
    const endpoint = queryString
      ? `/api/workflows?${queryString}`
      : "/api/workflows";
    return this.requestWithRetry<Workflow[]>(endpoint);
  }

  async getWorkflow(workflowId: string): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(`/api/workflows/${workflowId}`);
  }

  async updateWorkflow(
    workflowId: string,
    updates: WorkflowUpdate,
  ): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(`/api/workflows/${workflowId}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    });
  }

  async deleteWorkflow(workflowId: string): Promise<{ message: string }> {
    return this.requestWithRetry<{ message: string }>(
      `/api/workflows/${workflowId}`,
      {
        method: "DELETE",
      },
    );
  }

  // Code Generation
  async compileWorkflow(workflowId: string): Promise<CompilationResult> {
    return this.requestWithRetry<CompilationResult>(
      `/api/workflows/${workflowId}/compile`,
      {
        method: "POST",
      },
    );
  }

  // Execution Mode
  async setExecutionMode(
    workflowId: string,
    config: {
      mode:
        | "strategy"
        | "model"
        | "hybrid"
        | "backtesting"
        | "paper_trading"
        | "research";
      config: Record<string, any>;
    },
  ): Promise<{
    execution_id: string;
    mode: string;
    status: string;
    next_action?: string;
    generated_code?: string;
    requirements?: string[];
    training_job_id?: string;
    estimated_duration?: string;
    message?: string;
    errors?: string[];
  }> {
    return this.requestWithRetry(
      `/api/workflows/${workflowId}/execution-mode`,
      {
        method: "POST",
        body: JSON.stringify(config),
      },
    );
  }

  // Execution
  async executeWorkflow(
    workflowId: string,
    config: ExecutionConfig,
  ): Promise<Execution> {
    return this.requestWithRetry<Execution>(
      `/api/workflows/${workflowId}/execute`,
      {
        method: "POST",
        body: JSON.stringify(config),
      },
    );
  }

  async getExecution(executionId: string): Promise<Execution> {
    return this.requestWithRetry<Execution>(`/api/executions/${executionId}`);
  }

  // Component Library
  async getComponents(filters: ComponentFilters = {}): Promise<Component[]> {
    const queryString = this.buildQueryString(filters);
    const endpoint = queryString
      ? `/api/components?${queryString}`
      : "/api/components";
    return this.requestWithRetry<Component[]>(endpoint);
  }

  // Template Library
  async getTemplates(filters: TemplateFilters = {}): Promise<Template[]> {
    const queryString = this.buildQueryString(filters);
    const endpoint = queryString
      ? `/api/templates?${queryString}`
      : "/api/templates";
    return this.requestWithRetry<Template[]>(endpoint);
  }

  async createWorkflowFromTemplate(
    templateId: string,
    workflowName: string,
  ): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(`/api/templates/${templateId}/use`, {
      method: "POST",
      body: JSON.stringify({ workflow_name: workflowName }),
    });
  }

  // Workflow Import/Export
  async exportWorkflow(
    workflowId: string,
    format: "json" | "yaml" = "json",
  ): Promise<string> {
    return this.requestWithRetry<string>(
      `/api/workflows/${workflowId}/export?format=${format}`,
    );
  }

  async importWorkflow(
    data: string,
    format: "json" | "yaml" = "json",
  ): Promise<Workflow> {
    return this.requestWithRetry<Workflow>("/api/workflows/import", {
      method: "POST",
      body: JSON.stringify({ data, format }),
    });
  }

  // Workflow Execution Control
  async stopExecution(executionId: string): Promise<{ message: string }> {
    return this.requestWithRetry<{ message: string }>(
      `/api/executions/${executionId}/stop`,
      {
        method: "POST",
      },
    );
  }

  async resetWorkflow(workflowId: string): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(
      `/api/workflows/${workflowId}/reset`,
      {
        method: "POST",
      },
    );
  }

  // Code Generation
  async generateCode(
    workflowId: string,
    options: {
      language: "python" | "javascript";
      framework?: "backtesting.py" | "zipline" | "custom";
      includeComments?: boolean;
    } = { language: "python" },
  ): Promise<{
    code: string;
    dependencies: string[];
    documentation: string;
  }> {
    return this.requestWithRetry(`/api/workflows/${workflowId}/generate-code`, {
      method: "POST",
      body: JSON.stringify(options),
    });
  }

  // Workflow Testing
  async testWorkflow(
    workflowId: string,
    testConfig: {
      testType: "validation" | "backtest" | "paper_trade";
      parameters?: Record<string, any>;
    },
  ): Promise<{
    testId: string;
    status: "running" | "completed" | "failed";
    results?: any;
  }> {
    return this.requestWithRetry(`/api/workflows/${workflowId}/test`, {
      method: "POST",
      body: JSON.stringify(testConfig),
    });
  }

  // Search functionality
  async searchWorkflows(
    query: string,
    filters: {
      category?: string;
      tags?: string[];
      isPublic?: boolean;
      limit?: number;
      offset?: number;
    } = {},
  ): Promise<{
    workflows: Workflow[];
    total: number;
    hasMore: boolean;
  }> {
    const params = new URLSearchParams({ query });
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        if (Array.isArray(value)) {
          value.forEach((v) => params.append(key, v));
        } else {
          params.append(key, value.toString());
        }
      }
    });

    return this.requestWithRetry(`/api/workflows/search?${params.toString()}`);
  }

  async searchNodes(
    workflowId: string,
    query: string,
  ): Promise<{
    nodes: WorkflowNode[];
    matches: Array<{
      nodeId: string;
      field: string;
      value: string;
    }>;
  }> {
    return this.requestWithRetry(
      `/api/workflows/${workflowId}/search-nodes?query=${encodeURIComponent(query)}`,
    );
  }

  // Workflow Validation
  async validateWorkflow(workflowId: string): Promise<{
    valid: boolean;
    errors: Array<{
      nodeId?: string;
      message: string;
      severity: "error" | "warning" | "info";
    }>;
    warnings: Array<{
      nodeId?: string;
      message: string;
    }>;
  }> {
    return this.requestWithRetry(`/api/workflows/${workflowId}/validate`, {
      method: "POST",
    });
  }

  // Workflow Duplication
  async duplicateWorkflow(
    workflowId: string,
    newName: string,
  ): Promise<Workflow> {
    return this.requestWithRetry(`/api/workflows/${workflowId}/duplicate`, {
      method: "POST",
      body: JSON.stringify({ name: newName }),
    });
  }

  // Auto-save functionality
  async autoSaveWorkflow(
    workflowId: string,
    workflowData: WorkflowData,
  ): Promise<{ saved: boolean; timestamp: string }> {
    return this.requestWithRetry(`/api/workflows/${workflowId}/auto-save`, {
      method: "PUT",
      body: JSON.stringify({ workflow_data: workflowData }),
    });
  }

  // Execution Logs
  async getExecutionLogs(
    executionId: string,
    options: {
      limit?: number;
      offset?: number;
      level?: "error" | "warning" | "info" | "debug";
    } = {},
  ): Promise<{
    logs: Array<{
      timestamp: string;
      level: string;
      message: string;
      nodeId?: string;
    }>;
    total: number;
    hasMore: boolean;
  }> {
    const params = new URLSearchParams();
    Object.entries(options).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    const query = params.toString();
    const endpoint = query
      ? `/api/executions/${executionId}/logs?${query}`
      : `/api/executions/${executionId}/logs`;
    return this.requestWithRetry(endpoint);
  }

  // Real-time execution updates via Server-Sent Events
  createExecutionEventSource(executionId: string): EventSource {
    const url = `${this.config.baseUrl}/api/executions/${executionId}/events`;
    return new EventSource(url);
  }

  // Settings management
  async getUserSettings(): Promise<{
    preferences: Record<string, any>;
    theme: string;
    autoSave: boolean;
    notifications: boolean;
  }> {
    return this.requestWithRetry("/api/user/settings");
  }

  async updateUserSettings(settings: {
    preferences?: Record<string, any>;
    theme?: string;
    autoSave?: boolean;
    notifications?: boolean;
  }): Promise<{ updated: boolean }> {
    return this.requestWithRetry("/api/user/settings", {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  }

  // Workflow Versioning
  async createVersion(
    workflowId: string,
    options: {
      name?: string;
      changes_summary?: string;
      workflow_data?: WorkflowData;
    } = {},
  ): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(
      `/api/workflows/${workflowId}/versions`,
      {
        method: "POST",
        body: JSON.stringify(options),
      },
    );
  }

  async getVersions(workflowId: string): Promise<WorkflowVersion[]> {
    return this.requestWithRetry<WorkflowVersion[]>(
      `/api/workflows/${workflowId}/versions`,
    );
  }

  async getVersion(
    workflowId: string,
    version: number,
  ): Promise<WorkflowVersionDetails> {
    return this.requestWithRetry<WorkflowVersionDetails>(
      `/api/workflows/${workflowId}/versions/${version}`,
    );
  }

  async restoreVersion(workflowId: string, version: number): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(
      `/api/workflows/${workflowId}/versions/${version}/restore`,
      {
        method: "POST",
      },
    );
  }

  async compareVersions(
    workflowId: string,
    fromVersion: number,
    toVersion: number,
  ): Promise<{
    added_nodes: WorkflowNode[];
    removed_nodes: WorkflowNode[];
    modified_nodes: Array<{
      node_id: string;
      changes: Record<string, any>;
    }>;
    added_edges: WorkflowEdge[];
    removed_edges: WorkflowEdge[];
    metadata_changes: Record<string, any>;
  }> {
    return this.requestWithRetry(
      `/api/workflows/${workflowId}/versions/compare?from=${fromVersion}&to=${toVersion}`,
    );
  }

  async deleteVersion(
    workflowId: string,
    version: number,
  ): Promise<{ message: string }> {
    return this.requestWithRetry<{ message: string }>(
      `/api/workflows/${workflowId}/versions/${version}`,
      {
        method: "DELETE",
      },
    );
  }

  // Workflow History and Activity
  async getWorkflowHistory(
    workflowId: string,
    options: {
      limit?: number;
      offset?: number;
      action_type?: "created" | "updated" | "executed" | "shared" | "versioned";
    } = {},
  ): Promise<{
    activities: Array<{
      id: string;
      action_type: string;
      description: string;
      user_name?: string;
      version?: number;
      timestamp: string;
      metadata?: Record<string, any>;
    }>;
    total: number;
    hasMore: boolean;
  }> {
    const params = new URLSearchParams();
    Object.entries(options).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    const query = params.toString();
    const endpoint = query
      ? `/api/workflows/${workflowId}/history?${query}`
      : `/api/workflows/${workflowId}/history`;
    return this.requestWithRetry(endpoint);
  }

  // Workflow Branching
  async createBranch(
    workflowId: string,
    branchName: string,
    fromVersion?: number,
  ): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(
      `/api/workflows/${workflowId}/branch`,
      {
        method: "POST",
        body: JSON.stringify({
          branch_name: branchName,
          from_version: fromVersion,
        }),
      },
    );
  }

  async getBranches(workflowId: string): Promise<
    Array<{
      id: number;
      name: string;
      version: number;
      created_at: string;
      created_by?: string;
    }>
  > {
    return this.requestWithRetry(`/api/workflows/${workflowId}/branches`);
  }

  async mergeBranch(
    workflowId: string,
    branchId: number,
    strategy: "replace" | "merge" = "merge",
  ): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(
      `/api/workflows/${workflowId}/branches/${branchId}/merge`,
      {
        method: "POST",
        body: JSON.stringify({ strategy }),
      },
    );
  }

  // Health Check - override base class method to match expected interface
  async healthCheck(): Promise<{
    status: "healthy" | "unhealthy";
    timestamp: string;
    services: Record<string, "up" | "down">;
  }> {
    const result = await this.request<{
      status: string;
      service: string;
      version: string;
    }>("/health");

    // Transform the response to match the base class interface
    return {
      status: result.status === "ok" ? "healthy" : "unhealthy",
      timestamp: new Date().toISOString(),
      services: {
        [result.service]: result.status === "ok" ? "up" : "down",
      },
    };
  }
}

// Export singleton instance
export const noCodeApiClient = new NoCodeApiClient();
