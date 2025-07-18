import { gql } from '@apollo/client';

// Fragment definitions for reusable parts
export const WORKFLOW_FRAGMENT = gql`
  fragment WorkflowFragment on Workflow {
    id
    uuid
    name
    description
    category
    tags
    workflow_data {
      nodes {
        id
        type
        position
        data
      }
      edges {
        id
        source
        target
        sourceHandle
        targetHandle
      }
    }
    generated_code
    generated_code_language
    generated_requirements
    compilation_status
    compilation_errors
    validation_status
    validation_errors
    deployment_status
    execution_mode
    version
    parent_workflow_id
    is_template
    is_public
    total_executions
    successful_executions
    avg_performance_score
    last_execution_at
    created_at
    updated_at
    published_at
  }
`;

export const EXECUTION_FRAGMENT = gql`
  fragment ExecutionFragment on Execution {
    id
    uuid
    workflow_id
    execution_type
    symbols
    timeframe
    start_date
    end_date
    initial_capital
    status
    progress
    current_step
    final_capital
    total_return
    total_return_percent
    sharpe_ratio
    max_drawdown_percent
    total_trades
    winning_trades
    trades_data
    performance_metrics
    execution_logs
    error_logs
    started_at
    completed_at
    created_at
  }
`;

export const COMPONENT_FRAGMENT = gql`
  fragment ComponentFragment on Component {
    id
    uuid
    name
    display_name
    description
    category
    subcategory
    component_type
    input_schema
    output_schema
    parameters_schema
    default_parameters
    code_template
    imports_required
    dependencies
    ui_config
    icon
    is_builtin
    is_public
    usage_count
    rating
    created_at
    updated_at
  }
`;

export const TEMPLATE_FRAGMENT = gql`
  fragment TemplateFragment on Template {
    id
    uuid
    name
    description
    category
    difficulty_level
    template_data {
      nodes {
        id
        type
        position
        data
      }
      edges {
        id
        source
        target
        sourceHandle
        targetHandle
      }
    }
    preview_image_url
    author_id
    is_featured
    is_public
    usage_count
    rating
    keywords
    estimated_time_minutes
    expected_performance
    created_at
    updated_at
  }
`;

// Queries
export const GET_WORKFLOWS = gql`
  ${WORKFLOW_FRAGMENT}
  query GetWorkflows($filters: WorkflowFilters) {
    workflows(filters: $filters) {
      workflows {
        ...WorkflowFragment
      }
      total
      hasMore
    }
  }
`;

export const GET_WORKFLOW = gql`
  ${WORKFLOW_FRAGMENT}
  query GetWorkflow($workflowId: String!) {
    workflow(workflowId: $workflowId) {
      ...WorkflowFragment
    }
  }
`;

export const GET_EXECUTIONS = gql`
  ${EXECUTION_FRAGMENT}
  query GetExecutions($workflowId: String, $filters: ExecutionFilters) {
    executions(workflowId: $workflowId, filters: $filters) {
      executions {
        ...ExecutionFragment
      }
      total
      hasMore
    }
  }
`;

export const GET_EXECUTION = gql`
  ${EXECUTION_FRAGMENT}
  query GetExecution($executionId: String!) {
    execution(executionId: $executionId) {
      ...ExecutionFragment
    }
  }
`;

export const GET_COMPONENTS = gql`
  ${COMPONENT_FRAGMENT}
  query GetComponents($category: String, $isBuiltin: Boolean) {
    components(category: $category, isBuiltin: $isBuiltin) {
      ...ComponentFragment
    }
  }
`;

export const GET_TEMPLATES = gql`
  ${TEMPLATE_FRAGMENT}
  query GetTemplates($category: String, $difficultyLevel: String, $isFeatured: Boolean) {
    templates(category: $category, difficultyLevel: $difficultyLevel, isFeatured: $isFeatured) {
      ...TemplateFragment
    }
  }
`;

export const GET_WORKFLOW_HISTORY = gql`
  query GetWorkflowHistory($workflowId: String!, $limit: Int, $offset: Int) {
    workflowHistory(workflowId: $workflowId, limit: $limit, offset: $offset) {
      id
      action_type
      description
      user_name
      version
      timestamp
      metadata
    }
  }
`;

// Mutations
export const CREATE_WORKFLOW = gql`
  ${WORKFLOW_FRAGMENT}
  mutation CreateWorkflow($input: WorkflowCreateInput!) {
    createWorkflow(input: $input) {
      ...WorkflowFragment
    }
  }
`;

export const UPDATE_WORKFLOW = gql`
  ${WORKFLOW_FRAGMENT}
  mutation UpdateWorkflow($workflowId: String!, $input: WorkflowUpdateInput!) {
    updateWorkflow(workflowId: $workflowId, input: $input) {
      ...WorkflowFragment
    }
  }
`;

export const DELETE_WORKFLOW = gql`
  mutation DeleteWorkflow($workflowId: String!) {
    deleteWorkflow(workflowId: $workflowId)
  }
`;

export const COMPILE_WORKFLOW = gql`
  mutation CompileWorkflow($workflowId: String!) {
    compileWorkflow(workflowId: $workflowId) {
      workflow_id
      generated_code
      requirements
      status
      errors
      created_at
    }
  }
`;

export const EXECUTE_WORKFLOW = gql`
  ${EXECUTION_FRAGMENT}
  mutation ExecuteWorkflow($workflowId: String!, $input: ExecutionCreateInput!) {
    executeWorkflow(workflowId: $workflowId, input: $input) {
      ...ExecutionFragment
    }
  }
`;

export const CREATE_WORKFLOW_FROM_TEMPLATE = gql`
  ${WORKFLOW_FRAGMENT}
  mutation CreateWorkflowFromTemplate($templateId: String!, $workflowName: String!) {
    createWorkflowFromTemplate(templateId: $templateId, workflowName: $workflowName) {
      ...WorkflowFragment
    }
  }
`;

// Subscriptions
export const EXECUTION_UPDATES = gql`
  ${EXECUTION_FRAGMENT}
  subscription ExecutionUpdates($executionId: String!) {
    executionUpdates(executionId: $executionId) {
      ...ExecutionFragment
    }
  }
`;

export const WORKFLOW_UPDATES = gql`
  ${WORKFLOW_FRAGMENT}
  subscription WorkflowUpdates($workflowId: String!) {
    workflowUpdates(workflowId: $workflowId) {
      ...WorkflowFragment
    }
  }
`;

// Input types for TypeScript
export interface WorkflowFilters {
  skip?: number;
  limit?: number;
  category?: string;
  is_public?: boolean;
  search?: string;
}

export interface ExecutionFilters {
  skip?: number;
  limit?: number;
  status?: string;
  execution_type?: string;
}

export interface WorkflowCreateInput {
  name: string;
  description?: string;
  category?: string;
  tags?: string[];
  workflow_data?: {
    nodes: Array<{
      id: string;
      type: string;
      position: { [key: string]: any };
      data: { [key: string]: any };
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      sourceHandle?: string;
      targetHandle?: string;
    }>;
  };
  execution_mode?: string;
}

export interface WorkflowUpdateInput {
  name?: string;
  description?: string;
  category?: string;
  tags?: string[];
  workflow_data?: {
    nodes: Array<{
      id: string;
      type: string;
      position: { [key: string]: any };
      data: { [key: string]: any };
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      sourceHandle?: string;
      targetHandle?: string;
    }>;
  };
  execution_mode?: string;
  is_public?: boolean;
}

export interface ExecutionCreateInput {
  execution_type: string;
  symbols: string[];
  timeframe: string;
  start_date?: string;
  end_date?: string;
  initial_capital: number;
  parameters?: { [key: string]: any };
}

// Response types
export interface WorkflowsResponse {
  workflows: Array<{
    id: number;
    uuid: string;
    name: string;
    description?: string;
    category: string;
    tags: string[];
    workflow_data: {
      nodes: Array<{
        id: string;
        type: string;
        position: { [key: string]: any };
        data: { [key: string]: any };
      }>;
      edges: Array<{
        id: string;
        source: string;
        target: string;
        sourceHandle?: string;
        targetHandle?: string;
      }>;
    };
    generated_code?: string;
    generated_code_language: string;
    generated_requirements: string[];
    compilation_status: string;
    compilation_errors: any[];
    validation_status: string;
    validation_errors: any[];
    deployment_status: string;
    execution_mode: string;
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
  }>;
  total: number;
  hasMore: boolean;
}

export interface ExecutionsResponse {
  executions: Array<{
    id: number;
    uuid: string;
    workflow_id: number;
    execution_type: string;
    symbols: string[];
    timeframe: string;
    start_date?: string;
    end_date?: string;
    initial_capital: number;
    status: string;
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
    performance_metrics: { [key: string]: any };
    execution_logs: any[];
    error_logs: any[];
    started_at: string;
    completed_at?: string;
    created_at: string;
  }>;
  total: number;
  hasMore: boolean;
}