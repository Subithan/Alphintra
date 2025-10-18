import { apolloClient } from '../graphql/apollo-client';
import { BaseApiClient } from './api-client';
import { gatewayHttpBaseUrl } from '../config/gateway';
import {
  GET_WORKFLOWS,
  GET_WORKFLOW,
  GET_EXECUTIONS,
  GET_EXECUTION,
  GET_COMPONENTS,
  GET_TEMPLATES,
  GET_WORKFLOW_HISTORY,
  CREATE_WORKFLOW,
  UPDATE_WORKFLOW,
  DELETE_WORKFLOW,
  COMPILE_WORKFLOW,
  EXECUTE_WORKFLOW,
  CREATE_WORKFLOW_FROM_TEMPLATE,
  EXECUTION_UPDATES,
  WORKFLOW_UPDATES,
  type WorkflowFilters as GraphQLWorkflowFilters,
  type ExecutionFilters,
  type WorkflowCreateInput,
  type WorkflowUpdateInput,
  type ExecutionCreateInput,
  type WorkflowsResponse,
  type ExecutionsResponse,
} from '../graphql/operations';

// Import types from the original API client
import type {
  Workflow,
  Execution,
  Component,
  Template,
  WorkflowCreate,
  WorkflowUpdate,
  ExecutionConfig,
  CompilationResult,
  WorkflowFilters as OriginalWorkflowFilters,
  ComponentFilters,
  TemplateFilters,
  WorkflowVersion,
  WorkflowVersionDetails,
  WorkflowData,
} from './no-code-api';

// Re-export types for use in other modules
export type {
  Workflow,
  Execution,
  Component,
  Template,
  WorkflowCreate,
  WorkflowUpdate,
  ExecutionConfig,
  CompilationResult,
  ComponentFilters,
  TemplateFilters,
  WorkflowVersion,
  WorkflowVersionDetails,
  WorkflowData,
};

export type WorkflowFilters = OriginalWorkflowFilters;

export class NoCodeGraphQLApiClient extends BaseApiClient {
  private restClient: BaseApiClient;

  constructor() {
    super({
      baseUrl: gatewayHttpBaseUrl,
    });
    
    // Keep REST client for file operations and legacy endpoints
    this.restClient = new BaseApiClient({
      baseUrl: gatewayHttpBaseUrl,
    });
  }

  // GraphQL-based workflow operations
  async getWorkflows(filters: OriginalWorkflowFilters = {}): Promise<Workflow[]> {
    try {
      const graphqlFilters: GraphQLWorkflowFilters = {
        skip: filters.skip,
        limit: filters.limit,
        category: filters.category,
        is_public: filters.is_public,
      };

      const { data } = await apolloClient.query({
        query: GET_WORKFLOWS,
        variables: { filters: graphqlFilters },
        fetchPolicy: 'cache-first',
      });

      return data.workflows.workflows.map(this.transformGraphQLWorkflow);
    } catch (error) {
      console.error('GraphQL getWorkflows error:', error);
      // Fallback to REST API
      return this.getWorkflowsREST(filters);
    }
  }

  async getWorkflow(workflowId: string): Promise<Workflow> {
    try {
      const { data } = await apolloClient.query({
        query: GET_WORKFLOW,
        variables: { workflowId },
        fetchPolicy: 'cache-first',
      });

      if (!data.workflow) {
        throw new Error('Workflow not found');
      }

      return this.transformGraphQLWorkflow(data.workflow);
    } catch (error) {
      console.error('GraphQL getWorkflow error:', error);
      // Fallback to REST API
      return this.getWorkflowREST(workflowId);
    }
  }

  async createWorkflow(workflow: WorkflowCreate): Promise<Workflow> {
    try {
      const input: WorkflowCreateInput = {
        name: workflow.name,
        description: workflow.description,
        category: workflow.category,
        tags: workflow.tags,
        workflow_data: workflow.workflow_data,
        execution_mode: workflow.execution_mode,
      };

      const { data } = await apolloClient.mutate({
        mutation: CREATE_WORKFLOW,
        variables: { input },
        refetchQueries: [GET_WORKFLOWS],
      });

      return this.transformGraphQLWorkflow(data.createWorkflow);
    } catch (error) {
      console.error('GraphQL createWorkflow error:', error);
      // Fallback to REST API
      return this.createWorkflowREST(workflow);
    }
  }

  async updateWorkflow(workflowId: string, updates: WorkflowUpdate): Promise<Workflow> {
    try {
      const input: WorkflowUpdateInput = {
        name: updates.name,
        description: updates.description,
        category: updates.category,
        tags: updates.tags,
        workflow_data: updates.workflow_data,
        execution_mode: updates.execution_mode,
        is_public: updates.is_public,
      };

      const { data } = await apolloClient.mutate({
        mutation: UPDATE_WORKFLOW,
        variables: { workflowId, input },
        refetchQueries: [GET_WORKFLOWS, GET_WORKFLOW],
      });

      if (!data.updateWorkflow) {
        throw new Error('Failed to update workflow');
      }

      return this.transformGraphQLWorkflow(data.updateWorkflow);
    } catch (error) {
      console.error('GraphQL updateWorkflow error:', error);
      // Fallback to REST API
      return this.updateWorkflowREST(workflowId, updates);
    }
  }

  async deleteWorkflow(workflowId: string): Promise<{ message: string }> {
    try {
      const { data } = await apolloClient.mutate({
        mutation: DELETE_WORKFLOW,
        variables: { workflowId },
        refetchQueries: [GET_WORKFLOWS],
      });

      if (!data.deleteWorkflow) {
        throw new Error('Failed to delete workflow');
      }

      return { message: 'Workflow deleted successfully' };
    } catch (error) {
      console.error('GraphQL deleteWorkflow error:', error);
      // Fallback to REST API
      return this.deleteWorkflowREST(workflowId);
    }
  }

  // GraphQL-based execution operations
  async getExecutions(workflowId?: string, filters: ExecutionFilters = {}): Promise<Execution[]> {
    try {
      const { data } = await apolloClient.query({
        query: GET_EXECUTIONS,
        variables: { workflowId, filters },
        fetchPolicy: 'cache-first',
      });

      return data.executions.executions.map(this.transformGraphQLExecution);
    } catch (error) {
      console.error('GraphQL getExecutions error:', error);
      throw error;
    }
  }

  async getExecution(executionId: string): Promise<Execution> {
    try {
      const { data } = await apolloClient.query({
        query: GET_EXECUTION,
        variables: { executionId },
        fetchPolicy: 'cache-first',
      });

      if (!data.execution) {
        throw new Error('Execution not found');
      }

      return this.transformGraphQLExecution(data.execution);
    } catch (error) {
      console.error('GraphQL getExecution error:', error);
      throw error;
    }
  }

  async executeWorkflow(workflowId: string, config: ExecutionConfig): Promise<Execution> {
    try {
      const input: ExecutionCreateInput = {
        execution_type: config.execution_type,
        symbols: config.symbols,
        timeframe: config.timeframe,
        start_date: config.start_date,
        end_date: config.end_date,
        initial_capital: config.initial_capital,
        parameters: config.parameters,
      };

      const { data } = await apolloClient.mutate({
        mutation: EXECUTE_WORKFLOW,
        variables: { workflowId, input },
        refetchQueries: [GET_EXECUTIONS],
      });

      if (!data.executeWorkflow) {
        throw new Error('Failed to execute workflow');
      }

      return this.transformGraphQLExecution(data.executeWorkflow);
    } catch (error) {
      console.error('GraphQL executeWorkflow error:', error);
      throw error;
    }
  }

  // GraphQL-based compilation
  async compileWorkflow(workflowId: string): Promise<CompilationResult> {
    try {
      const { data } = await apolloClient.mutate({
        mutation: COMPILE_WORKFLOW,
        variables: { workflowId },
        refetchQueries: [GET_WORKFLOW],
      });

      if (!data.compileWorkflow) {
        throw new Error('Failed to compile workflow');
      }

      return {
        workflow_id: data.compileWorkflow.workflow_id,
        generated_code: data.compileWorkflow.generated_code,
        requirements: data.compileWorkflow.requirements,
        status: data.compileWorkflow.status as 'compiling' | 'compiled' | 'failed',
        errors: data.compileWorkflow.errors,
        created_at: data.compileWorkflow.created_at,
      };
    } catch (error) {
      console.error('GraphQL compileWorkflow error:', error);
      throw error;
    }
  }

  // GraphQL-based component and template operations
  async getComponents(filters: ComponentFilters = {}): Promise<Component[]> {
    try {
      const { data } = await apolloClient.query({
        query: GET_COMPONENTS,
        variables: {
          category: filters.category,
          isBuiltin: filters.is_builtin,
        },
        fetchPolicy: 'cache-first',
      });

      return data.components.map(this.transformGraphQLComponent);
    } catch (error) {
      console.error('GraphQL getComponents error:', error);
      throw error;
    }
  }

  async getTemplates(filters: TemplateFilters = {}): Promise<Template[]> {
    try {
      const { data } = await apolloClient.query({
        query: GET_TEMPLATES,
        variables: {
          category: filters.category,
          difficultyLevel: filters.difficulty_level,
          isFeatured: filters.is_featured,
        },
        fetchPolicy: 'cache-first',
      });

      return data.templates.map(this.transformGraphQLTemplate);
    } catch (error) {
      console.error('GraphQL getTemplates error:', error);
      throw error;
    }
  }

  async createWorkflowFromTemplate(templateId: string, workflowName: string): Promise<Workflow> {
    try {
      const { data } = await apolloClient.mutate({
        mutation: CREATE_WORKFLOW_FROM_TEMPLATE,
        variables: { templateId, workflowName },
        refetchQueries: [GET_WORKFLOWS],
      });

      if (!data.createWorkflowFromTemplate) {
        throw new Error('Failed to create workflow from template');
      }

      return this.transformGraphQLWorkflow(data.createWorkflowFromTemplate);
    } catch (error) {
      console.error('GraphQL createWorkflowFromTemplate error:', error);
      throw error;
    }
  }

  // Real-time subscriptions
  subscribeToExecutionUpdates(executionId: string, callback: (execution: Execution) => void) {
    const subscription = apolloClient.subscribe({
      query: EXECUTION_UPDATES,
      variables: { executionId },
    }).subscribe({
      next: ({ data }) => {
        if (data?.executionUpdates) {
          callback(this.transformGraphQLExecution(data.executionUpdates));
        }
      },
      error: (error) => {
        console.error('Execution subscription error:', error);
      },
    });

    return () => subscription.unsubscribe();
  }

  subscribeToWorkflowUpdates(workflowId: string, callback: (workflow: Workflow) => void) {
    const subscription = apolloClient.subscribe({
      query: WORKFLOW_UPDATES,
      variables: { workflowId },
    }).subscribe({
      next: ({ data }) => {
        if (data?.workflowUpdates) {
          callback(this.transformGraphQLWorkflow(data.workflowUpdates));
        }
      },
      error: (error) => {
        console.error('Workflow subscription error:', error);
      },
    });

    return () => subscription.unsubscribe();
  }

  // REST operations for file handling and legacy endpoints
  async exportWorkflow(workflowId: string, format: 'json' | 'yaml' = 'json'): Promise<string> {
    return this.requestWithRetry<string>(`/api/workflows/${workflowId}/export?format=${format}`);
  }

  async importWorkflow(data: string, format: 'json' | 'yaml' = 'json'): Promise<Workflow> {
    return this.requestWithRetry<Workflow>('/api/workflows/import', {
      method: 'POST',
      body: JSON.stringify({ data, format }),
    });
  }

  // Versioning operations (keeping REST for now)
  async getVersions(workflowId: string): Promise<WorkflowVersion[]> {
    return this.requestWithRetry<WorkflowVersion[]>(`/api/workflows/${workflowId}/versions`);
  }

  async getVersion(workflowId: string, version: number): Promise<WorkflowVersionDetails> {
    return this.requestWithRetry<WorkflowVersionDetails>(`/api/workflows/${workflowId}/versions/${version}`);
  }

  async createVersion(workflowId: string, options: {
    name?: string;
    changes_summary?: string;
    workflow_data?: any;
  } = {}): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(`/api/workflows/${workflowId}/versions`, {
      method: 'POST',
      body: JSON.stringify(options),
    });
  }

  // Transformation helpers
  private transformGraphQLWorkflow(gqlWorkflow: any): Workflow {
    return {
      id: gqlWorkflow.id,
      uuid: gqlWorkflow.uuid,
      name: gqlWorkflow.name,
      description: gqlWorkflow.description,
      category: gqlWorkflow.category,
      tags: gqlWorkflow.tags,
      workflow_data: {
        nodes: gqlWorkflow.workflow_data.nodes,
        edges: gqlWorkflow.workflow_data.edges,
      },
      generated_code: gqlWorkflow.generated_code,
      generated_code_language: gqlWorkflow.generated_code_language,
      generated_requirements: gqlWorkflow.generated_requirements,
      compilation_status: gqlWorkflow.compilation_status,
      compilation_errors: gqlWorkflow.compilation_errors,
      validation_status: gqlWorkflow.validation_status,
      validation_errors: gqlWorkflow.validation_errors,
      deployment_status: gqlWorkflow.deployment_status,
      execution_mode: gqlWorkflow.execution_mode,
      version: gqlWorkflow.version,
      parent_workflow_id: gqlWorkflow.parent_workflow_id,
      is_template: gqlWorkflow.is_template,
      is_public: gqlWorkflow.is_public,
      total_executions: gqlWorkflow.total_executions,
      successful_executions: gqlWorkflow.successful_executions,
      avg_performance_score: gqlWorkflow.avg_performance_score,
      last_execution_at: gqlWorkflow.last_execution_at,
      created_at: gqlWorkflow.created_at,
      updated_at: gqlWorkflow.updated_at,
      published_at: gqlWorkflow.published_at,
    };
  }

  private transformGraphQLExecution(gqlExecution: any): Execution {
    return {
      id: gqlExecution.id,
      uuid: gqlExecution.uuid,
      workflow_id: gqlExecution.workflow_id,
      execution_type: gqlExecution.execution_type,
      symbols: gqlExecution.symbols,
      timeframe: gqlExecution.timeframe,
      start_date: gqlExecution.start_date,
      end_date: gqlExecution.end_date,
      initial_capital: gqlExecution.initial_capital,
      status: gqlExecution.status,
      progress: gqlExecution.progress,
      current_step: gqlExecution.current_step,
      final_capital: gqlExecution.final_capital,
      total_return: gqlExecution.total_return,
      total_return_percent: gqlExecution.total_return_percent,
      sharpe_ratio: gqlExecution.sharpe_ratio,
      max_drawdown_percent: gqlExecution.max_drawdown_percent,
      total_trades: gqlExecution.total_trades,
      winning_trades: gqlExecution.winning_trades,
      trades_data: gqlExecution.trades_data,
      performance_metrics: gqlExecution.performance_metrics,
      execution_logs: gqlExecution.execution_logs,
      error_logs: gqlExecution.error_logs,
      started_at: gqlExecution.started_at,
      completed_at: gqlExecution.completed_at,
      created_at: gqlExecution.created_at,
    };
  }

  private transformGraphQLComponent(gqlComponent: any): Component {
    return {
      id: gqlComponent.id,
      uuid: gqlComponent.uuid,
      name: gqlComponent.name,
      display_name: gqlComponent.display_name,
      description: gqlComponent.description,
      category: gqlComponent.category,
      subcategory: gqlComponent.subcategory,
      component_type: gqlComponent.component_type,
      input_schema: gqlComponent.input_schema,
      output_schema: gqlComponent.output_schema,
      parameters_schema: gqlComponent.parameters_schema,
      default_parameters: gqlComponent.default_parameters,
      code_template: gqlComponent.code_template,
      imports_required: gqlComponent.imports_required,
      dependencies: gqlComponent.dependencies,
      ui_config: gqlComponent.ui_config,
      icon: gqlComponent.icon,
      is_builtin: gqlComponent.is_builtin,
      is_public: gqlComponent.is_public,
      usage_count: gqlComponent.usage_count,
      rating: gqlComponent.rating,
      created_at: gqlComponent.created_at,
      updated_at: gqlComponent.updated_at,
    };
  }

  private transformGraphQLTemplate(gqlTemplate: any): Template {
    return {
      id: gqlTemplate.id,
      uuid: gqlTemplate.uuid,
      name: gqlTemplate.name,
      description: gqlTemplate.description,
      category: gqlTemplate.category,
      difficulty_level: gqlTemplate.difficulty_level,
      template_data: {
        nodes: gqlTemplate.template_data.nodes,
        edges: gqlTemplate.template_data.edges,
      },
      preview_image_url: gqlTemplate.preview_image_url,
      author_id: gqlTemplate.author_id,
      is_featured: gqlTemplate.is_featured,
      is_public: gqlTemplate.is_public,
      usage_count: gqlTemplate.usage_count,
      rating: gqlTemplate.rating,
      keywords: gqlTemplate.keywords,
      estimated_time_minutes: gqlTemplate.estimated_time_minutes,
      expected_performance: gqlTemplate.expected_performance,
      created_at: gqlTemplate.created_at,
      updated_at: gqlTemplate.updated_at,
    };
  }

  // REST fallback methods
  private async getWorkflowsREST(filters: OriginalWorkflowFilters = {}): Promise<Workflow[]> {
    const queryString = this.buildQueryString(filters);
    const endpoint = queryString ? `/api/workflows?${queryString}` : '/api/workflows';
    return this.requestWithRetry<Workflow[]>(endpoint);
  }

  private async getWorkflowREST(workflowId: string): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(`/api/workflows/${workflowId}`);
  }

  private async createWorkflowREST(workflow: WorkflowCreate): Promise<Workflow> {
    return this.requestWithRetry<Workflow>('/api/workflows', {
      method: 'POST',
      body: JSON.stringify(workflow),
    });
  }

  private async updateWorkflowREST(workflowId: string, updates: WorkflowUpdate): Promise<Workflow> {
    return this.requestWithRetry<Workflow>(`/api/workflows/${workflowId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  private async deleteWorkflowREST(workflowId: string): Promise<{ message: string }> {
    return this.requestWithRetry<{ message: string }>(`/api/workflows/${workflowId}`, {
      method: 'DELETE',
    });
  }

  // Health check
  async healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    timestamp: string;
    services: Record<string, 'up' | 'down'>;
  }> {
    return this.requestWithRetry('/health').then((result: any) => ({
      status: result.status === 'healthy' ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      services: {
        'no-code-service': result.status === 'healthy' ? 'up' : 'down'
      }
    }));
  }
}

// Export singleton instance
export const noCodeGraphQLApiClient = new NoCodeGraphQLApiClient();
