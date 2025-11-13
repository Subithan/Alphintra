# No-Code API Contract Snapshot

Authoritative reference for the current No-Code service interface. Updated as part of Phase 0 to stabilize contracts before extending the compiler.

---

## 1. GraphQL Schema (Stawberry/FastAPI)

### Core Types

| Type | Key Fields (excerpt) | Notes |
| --- | --- | --- |
| `Workflow` | `uuid`, `name`, `workflow_data`, `generated_code`, `compilation_status`, `validation_status`, `compiler_version` | `compiler_version` surfaces the codegen build that produced `generated_code`. |
| `WorkflowsConnection` | `workflows`, `total`, `hasMore` | Returned by `Query.workflows(filters)` with pagination. |
| `Execution` | `workflow_id`, `execution_type`, `status`, `performance_metrics` | |
| `Component` | `component_type`, `input_schema`, `parameters_schema`, `code_template` | Metadata for palette components. |
| `CompilationResult` | `workflow_id`, `generated_code`, `status`, `errors`, `created_at` | Returned by compilation mutations/subscriptions. |

### Queries

| Operation | Signature | Description |
| --- | --- | --- |
| `workflows(filters: WorkflowFilters)` | Returns `WorkflowsConnection` | Lists workflows accessible to the current user. |
| `workflow(workflow_id: ID!)` | Returns `Workflow` | Fetch specific workflow with `compiler_version`. |
| `executions(workflow_id?, filters?)` | Returns `ExecutionsConnection` | List executions, optionally filtered. |
| `execution(execution_id: ID!)` | Returns `Execution` | Fetch single execution. |
| `components`, `templates` | Various | Surface palette metadata. |

### Mutations (excerpt)

| Operation | Description |
| --- | --- |
| `createWorkflow(input: WorkflowCreateInput)` | Persist workflow graph. |
| `updateWorkflow(id: ID!, input: WorkflowUpdateInput)` | Update metadata or graph. |
| `generateCode(workflowId: ID!)` | Triggers backend compiler, returns `CompilationResult`. |
| `createExecution(workflowId: ID!, input: ExecutionCreateInput)` | Launch backtest/training/live execution. |

### Subscriptions

| Sub | Payload |
| --- | --- |
| `workflowUpdates(workflowId: ID!)` | Streams `Workflow` mutations including new `compiler_version`. |
| `executionUpdates(executionId: ID!)` | Streams execution status/log updates. |

### GraphQL Contract Notes

1. `workflow_data` is strongly typed (nodes/edges) to match the frontend React Flow JSON.
2. `compiler_version` is now part of every workflow response, enabling UI badges and regression triage.
3. All JSON blobs use the custom `JSON` scalar defined in `graphql_schema.py`.

---

## 2. REST Endpoints (FastAPI in `main.py`)

| Method & Path | Purpose | Response Includes |
| --- | --- | --- |
| `GET /health` | Liveness probe | Service + DB health flags. |
| `GET /ready` | Readiness probe | Confirms DB + GCS connectivity. |
| `POST /api/workflows/create-sample` | Seeds demo workflow | Returns workflow metadata plus `compiler_version`. |
| `GET /api/workflows/debug/list` | Lists workflows (debug) | Array of workflow dicts. |
| `POST /api/workflows/{workflow_id}/generate-code` | Runs compiler | Includes `generated_code`, `compiler_version`, validation info. |
| `GET /api/workflows/{workflow_id}/generated-code` | Fetch previously generated code | Same metadata as compile endpoint. |
| `POST /api/workflows/{workflow_id}/execution-mode` | Toggles execution mode | Reflects updated workflow record. |
| `GET /api/workflows/strategies/list` | Lists compiled strategies for dashboard | Each entry carries `compiler_version`. |
| `GET /api/workflows/{workflow_id}/strategy-details` | Detailed strategy metadata | Includes `compiler_version`, code metrics. |
| `GET /api/workflows/strategies/database-overview` | Aggregate stats | Aggregated counts + latest `compiler_version`. |
| `POST /api/workflows/{workflow_id}/backtest` | Triggers backtest (delegates to backtest-service) | Execution UUID plus initial metrics. |
| `GET /api/backtest/symbols` | Supported tickers | Static list. |
| `GET /api/backtest/health` | Backtest subsystem health | Proxy health info. |

All endpoints require auth (gateway or service token) in production deployments.

---

## 3. Versioning & Compatibility

- `compiler_version` currently resolves to `Enhanced v2.0`. All workflow and strategy API responses must include the field so clients can reason about regenerated code vs. stored artifacts.
- When compiler semantics change, bump the version constant in one place (`src/backend/no-code-service/constants.py` once introduced) and migrate workflows if necessary.
- GraphQL consumers should request `compiler_version` in queries immediately to avoid nullable fallback once older rows are backfilled.

---

## 4. Testing & Validation Expectations

- GraphQL schema changes require updating this document and adding regression coverage (unit tests for conversion helpers + end-to-end snapshots once the service is deployed).
- REST endpoints should be exercised through FastAPI integration tests or post-deployment smoke tests (curl/HTTPie). Every compile response must carry both `generated_code` and `compiler_version`.

This snapshot should be refreshed whenever fields/endpoints change so downstream clients (frontend, mobile, automation) remain in sync with the backend contract.
