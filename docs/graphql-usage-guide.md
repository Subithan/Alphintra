# GraphQL Usage Guide for Alphintra No-Code Service

This guide covers how to effectively use GraphQL in the Alphintra no-code service, including queries, mutations, subscriptions, and best practices.

## Table of Contents

1. [Overview](#overview)
2. [Setting Up](#setting-up)
3. [Basic Queries](#basic-queries)
4. [Mutations](#mutations)
5. [Subscriptions](#subscriptions)
6. [Frontend Integration](#frontend-integration)
7. [Backend Development](#backend-development)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

Our GraphQL implementation uses a hybrid approach:
- **GraphQL**: Complex queries, real-time subscriptions, batch operations
- **REST**: File uploads, health checks, external integrations

### Architecture Components

```
Frontend (React + Apollo Client) 
    ↓
GraphQL Endpoint (/graphql)
    ↓
Strawberry GraphQL + FastAPI
    ↓
PostgreSQL Database
```

## Setting Up

### Environment Variables

Add these to your `.env` file:

```bash
# GraphQL Configuration
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:8004/graphql
NEXT_PUBLIC_GRAPHQL_WS_URL=ws://localhost:8004/graphql

# Development Settings
NEXT_PUBLIC_MOCK_API=false
NODE_ENV=development
```

### Dependencies

Backend:
```bash
pip install strawberry-graphql[fastapi]==0.219.0
pip install strawberry-graphql[subscriptions]==0.219.0
```

Frontend:
```bash
npm install @apollo/client graphql graphql-ws
```

## Basic Queries

### 1. Fetching Workflows

**GraphQL Query:**
```graphql
query GetWorkflows($filters: WorkflowFilters) {
  workflows(filters: $filters) {
    workflows {
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
      compilation_status
      execution_mode
      created_at
      updated_at
    }
    total
    hasMore
  }
}
```

**Variables:**
```json
{
  "filters": {
    "limit": 10,
    "skip": 0,
    "category": "trading",
    "search": "strategy"
  }
}
```

**React Hook Usage:**
```typescript
import { useWorkflows } from '@/lib/hooks/use-no-code';

function WorkflowList() {
  const { data: workflows, loading, error } = useWorkflows({
    limit: 10,
    category: 'trading'
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {workflows?.map(workflow => (
        <div key={workflow.uuid}>
          <h3>{workflow.name}</h3>
          <p>{workflow.description}</p>
          <span>Status: {workflow.compilation_status}</span>
        </div>
      ))}
    </div>
  );
}
```

### 2. Fetching Single Workflow

**GraphQL Query:**
```graphql
query GetWorkflow($workflowId: String!) {
  workflow(workflowId: $workflowId) {
    id
    uuid
    name
    description
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
      }
    }
    generated_code
    compilation_status
    compilation_errors
  }
}
```

**React Hook Usage:**
```typescript
import { useWorkflow } from '@/lib/hooks/use-no-code';

function WorkflowDetail({ workflowId }: { workflowId: string }) {
  const { data: workflow, loading, error } = useWorkflow(workflowId);

  if (loading) return <div>Loading workflow...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!workflow) return <div>Workflow not found</div>;

  return (
    <div>
      <h1>{workflow.name}</h1>
      <p>{workflow.description}</p>
      <div>
        <h3>Nodes: {workflow.workflow_data.nodes.length}</h3>
        <h3>Edges: {workflow.workflow_data.edges.length}</h3>
      </div>
      {workflow.generated_code && (
        <pre><code>{workflow.generated_code}</code></pre>
      )}
    </div>
  );
}
```

### 3. Fetching Components and Templates

**Components Query:**
```graphql
query GetComponents($category: String, $isBuiltin: Boolean) {
  components(category: $category, isBuiltin: $isBuiltin) {
    id
    uuid
    name
    display_name
    description
    category
    component_type
    parameters_schema
    ui_config
    icon
  }
}
```

**Templates Query:**
```graphql
query GetTemplates($category: String, $isFeatured: Boolean) {
  templates(category: $category, isFeatured: $isFeatured) {
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
        data
      }
    }
    usage_count
    rating
  }
}
```

## Mutations

### 1. Creating a Workflow

**GraphQL Mutation:**
```graphql
mutation CreateWorkflow($input: WorkflowCreateInput!) {
  createWorkflow(input: $input) {
    id
    uuid
    name
    description
    category
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
      }
    }
    created_at
  }
}
```

**React Hook Usage:**
```typescript
import { useCreateWorkflow } from '@/lib/hooks/use-no-code';

function CreateWorkflowForm() {
  const createWorkflow = useCreateWorkflow();

  const handleCreate = async () => {
    try {
      const newWorkflow = await createWorkflow.mutateAsync({
        name: "My Trading Strategy",
        description: "A momentum-based trading strategy",
        category: "trading",
        tags: ["momentum", "technical-analysis"],
        workflow_data: {
          nodes: [
            {
              id: "1",
              type: "technicalIndicator",
              position: { x: 100, y: 100 },
              data: {
                label: "RSI Indicator",
                parameters: { period: 14 }
              }
            }
          ],
          edges: []
        },
        execution_mode: "backtest"
      });
      
      console.log('Created workflow:', newWorkflow);
    } catch (error) {
      console.error('Failed to create workflow:', error);
    }
  };

  return (
    <button 
      onClick={handleCreate}
      disabled={createWorkflow.isPending}
    >
      {createWorkflow.isPending ? 'Creating...' : 'Create Workflow'}
    </button>
  );
}
```

### 2. Updating a Workflow

**GraphQL Mutation:**
```graphql
mutation UpdateWorkflow($workflowId: String!, $input: WorkflowUpdateInput!) {
  updateWorkflow(workflowId: $workflowId, input: $input) {
    id
    uuid
    name
    description
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
      }
    }
    updated_at
  }
}
```

**React Hook Usage:**
```typescript
import { useUpdateWorkflow } from '@/lib/hooks/use-no-code';

function WorkflowEditor({ workflowId }: { workflowId: string }) {
  const updateWorkflow = useUpdateWorkflow();

  const handleSave = async (nodes: Node[], edges: Edge[]) => {
    try {
      await updateWorkflow.mutateAsync({
        workflowId,
        updates: {
          workflow_data: {
            nodes: nodes.map(node => ({
              id: node.id,
              type: node.type!,
              position: node.position,
              data: node.data
            })),
            edges: edges.map(edge => ({
              id: edge.id,
              source: edge.source,
              target: edge.target,
              sourceHandle: edge.sourceHandle,
              targetHandle: edge.targetHandle
            }))
          }
        }
      });
      
      console.log('Workflow saved successfully');
    } catch (error) {
      console.error('Failed to save workflow:', error);
    }
  };

  return (
    <button 
      onClick={() => handleSave(nodes, edges)}
      disabled={updateWorkflow.isPending}
    >
      {updateWorkflow.isPending ? 'Saving...' : 'Save Workflow'}
    </button>
  );
}
```

### 3. Compiling a Workflow

**GraphQL Mutation:**
```graphql
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
```

**React Hook Usage:**
```typescript
import { useCompileWorkflow } from '@/lib/hooks/use-no-code';

function CompileButton({ workflowId }: { workflowId: string }) {
  const compileWorkflow = useCompileWorkflow();

  const handleCompile = async () => {
    try {
      const result = await compileWorkflow.mutateAsync(workflowId);
      
      if (result.status === 'compiled') {
        console.log('Compilation successful!');
        console.log('Generated code:', result.generated_code);
      } else {
        console.error('Compilation failed:', result.errors);
      }
    } catch (error) {
      console.error('Compilation error:', error);
    }
  };

  return (
    <button 
      onClick={handleCompile}
      disabled={compileWorkflow.isPending}
    >
      {compileWorkflow.isPending ? 'Compiling...' : 'Compile Workflow'}
    </button>
  );
}
```

### 4. Executing a Workflow

**GraphQL Mutation:**
```graphql
mutation ExecuteWorkflow($workflowId: String!, $input: ExecutionCreateInput!) {
  executeWorkflow(workflowId: $workflowId, input: $input) {
    id
    uuid
    execution_type
    symbols
    timeframe
    initial_capital
    status
    progress
    started_at
  }
}
```

**React Hook Usage:**
```typescript
import { useExecuteWorkflow } from '@/lib/hooks/use-no-code';

function ExecuteButton({ workflowId }: { workflowId: string }) {
  const executeWorkflow = useExecuteWorkflow();

  const handleExecute = async () => {
    try {
      const execution = await executeWorkflow.mutateAsync({
        workflowId,
        config: {
          execution_type: "backtest",
          symbols: ["AAPL", "GOOGL", "MSFT"],
          timeframe: "1d",
          start_date: "2023-01-01",
          end_date: "2023-12-31",
          initial_capital: 100000,
          parameters: {
            risk_per_trade: 0.02,
            max_positions: 5
          }
        }
      });
      
      console.log('Execution started:', execution);
    } catch (error) {
      console.error('Execution failed:', error);
    }
  };

  return (
    <button 
      onClick={handleExecute}
      disabled={executeWorkflow.isPending}
    >
      {executeWorkflow.isPending ? 'Starting...' : 'Execute Backtest'}
    </button>
  );
}
```

## Subscriptions

### 1. Execution Updates

**GraphQL Subscription:**
```graphql
subscription ExecutionUpdates($executionId: String!) {
  executionUpdates(executionId: $executionId) {
    id
    uuid
    status
    progress
    current_step
    final_capital
    total_return_percent
    performance_metrics
    error_logs
  }
}
```

**React Hook Usage:**
```typescript
import { useExecutionWithSubscription } from '@/lib/hooks/use-no-code';

function ExecutionMonitor({ executionId }: { executionId: string }) {
  const { data: execution, subscription } = useExecutionWithSubscription(executionId);

  return (
    <div>
      <h3>Execution Status</h3>
      <p>Status: {execution?.status}</p>
      <p>Progress: {execution?.progress}%</p>
      <p>Current Step: {execution?.current_step}</p>
      
      {execution?.status === 'completed' && (
        <div>
          <h4>Results</h4>
          <p>Final Capital: ${execution.final_capital}</p>
          <p>Return: {execution.total_return_percent}%</p>
        </div>
      )}
      
      <div>
        Subscription: {subscription.isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>
    </div>
  );
}
```

### 2. Workflow Updates

**GraphQL Subscription:**
```graphql
subscription WorkflowUpdates($workflowId: String!) {
  workflowUpdates(workflowId: $workflowId) {
    id
    uuid
    name
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
      }
    }
    compilation_status
    updated_at
  }
}
```

**React Hook Usage:**
```typescript
import { useWorkflowWithSubscription } from '@/lib/hooks/use-no-code';

function CollaborativeWorkflowEditor({ workflowId }: { workflowId: string }) {
  const { data: workflow, subscription } = useWorkflowWithSubscription(workflowId);

  return (
    <div>
      <h3>{workflow?.name}</h3>
      <p>Last updated: {workflow?.updated_at}</p>
      
      <div>
        Real-time updates: {subscription.isConnected ? '🟢 Active' : '🔴 Inactive'}
      </div>
      
      {/* Workflow editor components */}
      <WorkflowCanvas 
        nodes={workflow?.workflow_data.nodes || []}
        edges={workflow?.workflow_data.edges || []}
      />
    </div>
  );
}
```

## Frontend Integration

### Apollo Client Setup

```typescript
// lib/graphql/apollo-client.ts
import { ApolloClient, InMemoryCache, createHttpLink, split } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8004/graphql',
});

const wsLink = new GraphQLWsLink(createClient({
  url: process.env.NEXT_PUBLIC_GRAPHQL_WS_URL || 'ws://localhost:8004/graphql',
}));

const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink,
);

export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
});
```

### Provider Setup

```typescript
// components/providers.tsx
import { ApolloProvider } from '@apollo/client';
import { apolloClient } from '@/lib/graphql/apollo-client';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ApolloProvider client={apolloClient}>
      {children}
    </ApolloProvider>
  );
}
```

### Direct Apollo Usage

```typescript
import { useQuery, useMutation, useSubscription } from '@apollo/client';
import { GET_WORKFLOWS, CREATE_WORKFLOW, EXECUTION_UPDATES } from '@/lib/graphql/operations';

function WorkflowComponent() {
  // Query
  const { data, loading, error } = useQuery(GET_WORKFLOWS, {
    variables: { filters: { limit: 10 } }
  });

  // Mutation
  const [createWorkflow, { loading: creating }] = useMutation(CREATE_WORKFLOW, {
    refetchQueries: [GET_WORKFLOWS]
  });

  // Subscription
  const { data: executionData } = useSubscription(EXECUTION_UPDATES, {
    variables: { executionId: 'some-execution-id' }
  });

  return (
    <div>
      {/* Component JSX */}
    </div>
  );
}
```

## Backend Development

### Adding New Queries

1. **Define GraphQL Type:**
```python
# graphql_schema.py
@strawberry.type
class WorkflowStatistics:
    total_workflows: int
    active_executions: int
    success_rate: float
    avg_performance: float
```

2. **Add to Query Class:**
```python
# graphql_resolvers.py
@strawberry.type
class Query:
    @strawberry.field
    def workflow_statistics(
        self,
        info: Info,
        user_id: Optional[str] = None
    ) -> WorkflowStatistics:
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        # Calculate statistics
        total = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.user_id == current_user.id
        ).count()
        
        active = db.query(NoCodeExecution).filter(
            NoCodeExecution.user_id == current_user.id,
            NoCodeExecution.status.in_(['pending', 'running'])
        ).count()
        
        return WorkflowStatistics(
            total_workflows=total,
            active_executions=active,
            success_rate=85.5,
            avg_performance=12.3
        )
```

3. **Add Frontend Operation:**
```typescript
// lib/graphql/operations.ts
export const GET_WORKFLOW_STATISTICS = gql`
  query GetWorkflowStatistics($userId: String) {
    workflowStatistics(userId: $userId) {
      totalWorkflows
      activeExecutions
      successRate
      avgPerformance
    }
  }
`;
```

### Adding New Mutations

1. **Define Input Type:**
```python
@strawberry.input
class WorkflowCloneInput:
    source_workflow_id: str
    new_name: str
    copy_executions: bool = False
```

2. **Add to Mutation Class:**
```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    def clone_workflow(
        self,
        info: Info,
        input: WorkflowCloneInput
    ) -> Optional[Workflow]:
        db = get_db_session(info)
        current_user = get_current_user(info)
        
        # Implementation logic
        source_workflow = db.query(NoCodeWorkflow).filter(
            NoCodeWorkflow.uuid == input.source_workflow_id,
            NoCodeWorkflow.user_id == current_user.id
        ).first()
        
        if not source_workflow:
            return None
        
        # Clone workflow
        cloned_workflow = NoCodeWorkflow(
            name=input.new_name,
            description=f"Cloned from {source_workflow.name}",
            category=source_workflow.category,
            user_id=current_user.id,
            workflow_data=source_workflow.workflow_data,
            parent_workflow_id=source_workflow.id
        )
        
        db.add(cloned_workflow)
        db.commit()
        db.refresh(cloned_workflow)
        
        return convert_db_workflow_to_graphql(cloned_workflow)
```

### Adding New Subscriptions

1. **Add to Subscription Class:**
```python
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def user_activity(
        self,
        info: Info,
        user_id: str
    ) -> AsyncGenerator[str, None]:
        # Implementation for real-time user activity
        while True:
            # Get latest activity
            activity = f"User activity at {datetime.now()}"
            yield activity
            await asyncio.sleep(5)  # Update every 5 seconds
```

## Best Practices

### 1. Query Optimization

**Use Fragments for Reusability:**
```graphql
fragment WorkflowBasic on Workflow {
  id
  uuid
  name
  description
  category
  compilation_status
  created_at
  updated_at
}

query GetWorkflows {
  workflows {
    workflows {
      ...WorkflowBasic
    }
  }
}

query GetWorkflow($id: String!) {
  workflow(workflowId: $id) {
    ...WorkflowBasic
    workflow_data {
      nodes {
        id
        type
        position
        data
      }
    }
  }
}
```

**Request Only Needed Fields:**
```graphql
# Good - Only request what you need
query GetWorkflowNames {
  workflows {
    workflows {
      uuid
      name
      category
    }
  }
}

# Bad - Requesting unnecessary data
query GetWorkflowNames {
  workflows {
    workflows {
      id
      uuid
      name
      description
      category
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
        }
      }
      generated_code
      compilation_errors
    }
  }
}
```

### 2. Error Handling

**Frontend Error Handling:**
```typescript
import { ApolloError } from '@apollo/client';

function WorkflowList() {
  const { data, loading, error } = useWorkflows();

  if (loading) return <LoadingSpinner />;
  
  if (error) {
    // Handle different error types
    if (error.networkError) {
      return <div>Network error: Please check your connection</div>;
    }
    
    if (error.graphQLErrors?.length > 0) {
      return (
        <div>
          {error.graphQLErrors.map((err, i) => (
            <div key={i}>GraphQL error: {err.message}</div>
          ))}
        </div>
      );
    }
    
    return <div>Unknown error occurred</div>;
  }

  return (
    <div>
      {data?.map(workflow => (
        <WorkflowCard key={workflow.uuid} workflow={workflow} />
      ))}
    </div>
  );
}
```

**Backend Error Handling:**
```python
from strawberry import field
import logging

@strawberry.type
class Query:
    @strawberry.field
    def workflow(self, info: Info, workflow_id: str) -> Optional[Workflow]:
        try:
            db = get_db_session(info)
            current_user = get_current_user(info)
            
            workflow = db.query(NoCodeWorkflow).filter(
                NoCodeWorkflow.uuid == workflow_id,
                or_(
                    NoCodeWorkflow.user_id == current_user.id,
                    NoCodeWorkflow.is_public == True
                )
            ).first()
            
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            return convert_db_workflow_to_graphql(workflow)
            
        except Exception as e:
            logging.error(f"Error fetching workflow {workflow_id}: {str(e)}")
            raise e
```

### 3. Caching Strategies

**Apollo Client Cache Configuration:**
```typescript
import { InMemoryCache } from '@apollo/client';

const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        workflows: {
          keyArgs: ['filters', ['category', 'search']],
          merge(existing, incoming, { args }) {
            if (!args?.filters?.skip || args.filters.skip === 0) {
              return incoming;
            }
            // Merge for pagination
            return {
              ...incoming,
              workflows: [
                ...(existing?.workflows || []),
                ...incoming.workflows,
              ],
            };
          },
        },
      },
    },
    Workflow: {
      fields: {
        workflow_data: {
          merge: true, // Deep merge workflow data
        },
      },
    },
  },
});
```

**Optimistic Updates:**
```typescript
const [updateWorkflow] = useMutation(UPDATE_WORKFLOW, {
  optimisticResponse: (variables) => ({
    updateWorkflow: {
      __typename: 'Workflow',
      ...variables.input,
      updated_at: new Date().toISOString(),
    },
  }),
  update: (cache, { data }) => {
    if (data?.updateWorkflow) {
      cache.writeQuery({
        query: GET_WORKFLOW,
        variables: { workflowId: data.updateWorkflow.uuid },
        data: { workflow: data.updateWorkflow },
      });
    }
  },
});
```

### 4. Subscription Management

**Automatic Cleanup:**
```typescript
function useExecutionSubscription(executionId: string) {
  const queryClient = useQueryClient();
  
  useEffect(() => {
    if (!executionId) return;

    const unsubscribe = noCodeGraphQLApiClient.subscribeToExecutionUpdates(
      executionId,
      (updatedExecution) => {
        queryClient.setQueryData(
          ['execution', executionId],
          updatedExecution
        );
      }
    );

    return unsubscribe; // Cleanup on unmount
  }, [executionId, queryClient]);
}
```

**Conditional Subscriptions:**
```typescript
function ExecutionMonitor({ executionId }: { executionId: string }) {
  const { data: execution } = useExecution(executionId);
  
  // Only subscribe if execution is active
  const shouldSubscribe = execution?.status === 'running' || execution?.status === 'pending';
  
  const subscription = useExecutionSubscription(
    shouldSubscribe ? executionId : null
  );
  
  return (
    <div>
      <p>Status: {execution?.status}</p>
      {shouldSubscribe && (
        <p>Watching for updates... {subscription.isConnected ? '🟢' : '🔴'}</p>
      )}
    </div>
  );
}
```

## Troubleshooting

### Common Issues

**1. WebSocket Connection Failures**
```typescript
// Check WebSocket URL configuration
console.log('GraphQL WS URL:', process.env.NEXT_PUBLIC_GRAPHQL_WS_URL);

// Add connection error handling
const wsLink = new GraphQLWsLink(createClient({
  url: process.env.NEXT_PUBLIC_GRAPHQL_WS_URL,
  on: {
    error: (error) => {
      console.error('WebSocket error:', error);
    },
    closed: () => {
      console.log('WebSocket connection closed');
    },
  },
}));
```

**2. Authentication Issues**
```typescript
// Ensure auth token is included
const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('auth_token');
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
    }
  };
});
```

**3. Type Mismatches**
```typescript
// Use proper type assertions
const workflow = data?.workflow as Workflow | undefined;

// Check for null/undefined
if (!workflow) {
  console.warn('Workflow not found');
  return;
}
```

**4. Cache Inconsistencies**
```typescript
// Clear cache when needed
import { apolloClient } from '@/lib/graphql/apollo-client';

const handleLogout = () => {
  apolloClient.clearStore();
  localStorage.removeItem('auth_token');
};
```

### Debugging Tips

**1. Enable GraphQL Debugging:**
```typescript
// Add to Apollo Client configuration
const client = new ApolloClient({
  link: from([
    new ApolloLink((operation, forward) => {
      console.log('GraphQL Operation:', operation.operationName);
      console.log('Variables:', operation.variables);
      return forward(operation);
    }),
    splitLink,
  ]),
  cache,
  defaultOptions: {
    watchQuery: { errorPolicy: 'all' },
    query: { errorPolicy: 'all' },
  },
});
```

**2. Backend Logging:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@strawberry.field
def workflow(self, info: Info, workflow_id: str) -> Optional[Workflow]:
    logger.info(f"Fetching workflow: {workflow_id}")
    # Implementation
```

**3. Network Inspection:**
- Use browser DevTools Network tab
- Check GraphQL endpoint responses
- Verify WebSocket connections in DevTools

This guide should provide a comprehensive foundation for working with GraphQL in the Alphintra no-code service. Remember to always follow the established patterns and refer to the existing codebase for consistency.