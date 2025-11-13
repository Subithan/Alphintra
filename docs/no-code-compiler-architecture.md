# No-Code Compiler Architecture

Context: the frontend workflow builder stores a workflow as JSON (`nodes`, `edges`, `parameters`) and posts the payload to `src/backend/no-code-service`. The backend must deterministically transform that graph into a production-ready Python trading strategy that can be backtested, trained, or deployed.

This document describes the compiler we should implement (or finish hardening) inside `src/backend/no-code-service`.

---

## High-Level Goals

1. **Deterministic pipelines** – every workflow with the same nodes/edges must produce identical Python code so we can diff/verify builds.
2. **Correct-by-construction** – catch invalid graphs, missing parameters, and type mismatches before emitting code.
3. **Extensible node support** – adding a new frontend component should only require registering a handler and (optionally) templates, not rewriting the compiler.
4. **Multi-target output** – compile for backtests, training jobs, and live trading by switching adapters instead of patching templates.
5. **Observability** – surface compiler warnings/errors back to the UI via `ValidationResult` objects so users understand failures quickly.

---

## Input / Output Contracts

| Stage | Data |
| --- | --- |
| **Input** | JSON blob from frontend `{ "nodes": [...], "edges": [...], "parameters": {...} }` |
| **Output** | `CompilationResult` (`python_code`, validation list, metadata) consumed by API responses and persisted for backtests |

Existing types such as `schemas.ValidationResult` and `CompilationResult` (see `src/backend/no-code-service/workflow_compiler.py`) stay in place, but the implementation will be swapped to the new pipeline.

---

## Compiler Pipeline

```
JSON -> Normalization -> IR Graph -> Semantic Analysis + Type Inference
     -> Execution Plan -> Optimization Passes -> Code Generation
     -> Post-Compilation Validation + Packaging
```

### 1. Normalization Layer
- Module: `src/backend/no-code-service/ir.py`
- Responsibilities:
  - Validate JSON schema (node IDs, types, handles).
  - Strip UI-only metadata and build canonical `Workflow` graph objects (`Node`, `Edge`).
  - Attach connection metadata (handle IDs, `dataType`, etc.) when converting edges.
- Output: `Workflow` instance referenced throughout compilation.

### 2. Semantic Analysis & Type System
- Module: new `semantic_analyzer.py`.
- Uses connection metadata defined in `src/frontend/lib/connection-manager.ts` (see cheatsheet `docs/no-code-workflow-cheatsheet.md`) mirrored server-side.
- Tasks:
  - Ensure required node types exist (data sources, actions, outputs).
  - Validate each node’s parameters against schema definitions pulled from `node_handlers`.
  - Perform data-type propagation (`OHLCV`, `NUMERIC`, `SIGNAL`, `EXECUTION`, `RISK_METRICS`, etc.) leveraging enums already declared in `enhanced_code_generator.py`.
  - Produce `TypedNode`/`DataFlowEdge` (see existing definitions in `enhanced_code_generator.py:42` onwards).
- Errors/warnings bubble into `CompilationContext.errors`.

### 3. Execution Planner
- Module: `execution_planner.py`.
- Uses topological sort (`Workflow.adjacency()` / `in_degree()` already implemented).
- Responsibilities:
  - Break graph into stages (data prep → indicator calc → condition/logic → execution → risk/output).
  - Detect parallelizable segments and annotate nodes with `execution_order`.
  - Emit dependency chains for each action/risk node so codegen can generate functions in dependency order.

### 4. Optimization Passes
- Module: reuse `EnhancedCodeGenerator` hooks (`_dead_code_elimination`, `_common_subexpression_elimination`, etc.).
- Run against the `CompilationContext`:
  - Remove unreachable nodes/edges.
  - Collapse duplicated computations (same indicator config reused multiple times).
  - Propagate constants (fixed thresholds, static dataset filters).
  - Flag expensive constructs for caching (e.g., multi-timeframe aggregator reusing resampled frames).

### 5. Code Generation
- Module: `src/backend/no-code-service/enhanced_code_generator.py` (already structured as compiler).
- Mechanism:
  - Node handlers live in `src/backend/no-code-service/node_handlers/`. Each handler exposes:
    ```python
    class BaseNodeHandler:
        type = "technicalIndicator"
        input_handles = {"data-input": DataType.OHLCV}
        output_handles = {"output-1": DataType.NUMERIC, ...}
        def emit(self, node: TypedNode, ctx: CompilationContext) -> GeneratedSnippet:
            ...
    ```
  - The generator walks the execution plan, asks each handler for its AST/code snippet, and merges them into strategy scaffolding (imports, initialization, `handle_data`/`on_bar` functions, etc.).
  - Output adapters (training/backtesting/live) live under `clients/` or a new `emitters/` package so the same AST can be serialized differently.
- Deliverables:
  - Python module string (via `ast.unparse` or templating).
  - Metadata (list of required datasets, indicator caches, risk controls) saved alongside the code for runtime orchestration.

### 6. Post-Compilation Validation
- Modules: `validate_generated_code.py`, `workflow_compiler.py`.
- Steps:
  - Run `ast.parse` to ensure syntax correctness.
  - Optionally execute fast static simulations (unit sample) to confirm indicator outputs exist.
  - Feed validation results back through GraphQL to power the frontend Validation Panel.

---

## Module Structure

```
src/backend/no-code-service/
├── ir.py                      # Canonical graph model (already present)
├── semantic_analyzer.py       # Type + parameter verification
├── execution_planner.py       # Topological ordering & stage tagging
├── enhanced_code_generator.py # Handles context, optimization, code emission
├── node_handlers/
│   ├── data_source.py
│   ├── technical_indicator.py
│   ├── condition.py
│   ├── logic.py
│   ├── action.py
│   ├── risk.py
│   └── advanced/*.py          # e.g., sentiment, regime detection
├── compiler_service.py        # Facade used by FastAPI/GraphQL resolvers
└── validators/
    ├── structural.py          # Graph-level checks
    ├── runtime.py             # Executes generated code in sandbox
    └── reporters.py           # Formats ValidationResult instances
```

`workflow_compiler.py` becomes a thin façade that instantiates `CompilerService` and returns `CompilationResult`, preserving public APIs.

---

## Node Handler Contract

All handlers share a base class (pseudo-code):

```python
class NodeHandler(Protocol):
    type: str
    input_handles: Dict[str, DataType]
    output_handles: Dict[str, DataType]

    def validate(self, node: TypedNode, ctx: CompilationContext) -> List[CompilationError]:
        ...

    def emit(self, node: TypedNode, ctx: CompilationContext) -> GeneratedSnippet:
        ...
```

`GeneratedSnippet` contains:
- `imports`: set of import strings.
- `state_defs`: dataclass/field declarations.
- `setup_code`: initialization inside `initialize_strategy()`.
- `on_bar_code`: the per-bar logic piece.
- `helpers`: reusable helper functions.

Handlers register themselves in `HANDLER_REGISTRY` (`node_handlers/__init__.py`), which the generator consumes.

---

## Strategy Template

Templates live in `templates/` or inside the generator, but follow this skeleton:

```python
class Strategy(BaseStrategy):
    def __init__(self, config):
        ...

    def on_start(self):
        {{setup_code}}

    def on_bar(self, bar):
        {{data_fetch}}
        {{indicator_calls}}
        {{condition_logic}}
        {{risk_checks}}
        {{action_dispatch}}

    def on_order_filled(...):
        {{risk_monitoring}}
```

Different output modes adjust base classes or helper imports:
- **Backtest**: extend `BacktestStrategy`, rely on pandas/polars.
- **Live**: hook into `trading-engine` clients.
- **Training/Research**: emit functions consumed by AI/ML services.

---

## Validation & Observability

- Structural checks (missing nodes, circular dependencies, disconnected subgraphs) run in the semantic analyzer.
- Runtime validation executes lightweight simulations using `validate_generated_code.py`.
- Results are serialized back through GraphQL (`graphql_resolvers.py`) so the frontend Validation Panel can display errors/warnings per node.

Additionally, log structured telemetry per compilation:
- Workflow ID, git hash of compiler, checksum of output.
- Timing per stage (normalization/analyzer/planner/generator/validation).

---

## Extending the Compiler

1. **New component**: add schema on frontend + register `NodeHandler` subclass backend.
2. **New connection rule**: update frontend connection manager and mirror rule in the semantic analyzer.
3. **New target mode**: implement emitter class that consumes `GeneratedSnippet` bundles and formats them for the new runtime.
4. **Optimizations**: push additional passes into `EnhancedCodeGenerator.optimization_passes`.

---

## Next Steps

1. Build the missing modules (`semantic_analyzer.py`, `execution_planner.py`, `compiler_service.py`) reusing existing IR and enhanced generator structures.
2. Incrementally migrate `workflow_compiler.py` to delegate into the new pipeline; keep current API surface intact.
3. Add golden-sample JSON workflows plus expected Python outputs under `tests/backend/no_code_service/` to prevent regressions.
4. Wire `graphql_resolvers.py` to the new `CompilerService` and expose richer validation metadata to the frontend.

With this architecture in place, the backend can reliably convert the JSON graph delivered by the frontend into executable, auditable Python strategies.

---

## End-to-End Implementation Plan

The following plan breaks the compiler build-out into phases that cover every component currently exposed in the frontend palette (data sources, custom datasets, the full catalog of technical indicators, advanced analytics, conditions, logic gates, risk controls, actions, outputs).

### Phase 0 – Project Setup
1. **Stabilize API contracts**
   - Snapshot existing GraphQL schema/REST payloads (`graphql_schema.py`, `graphql_resolvers.py`).
   - Define versioning strategy for compiler outputs and expose a `compiler_version` field in responses.
2. **Test harness**
   - Create `tests/backend/no_code_service/fixtures/` with representative workflow JSON for each component category (data-only, single indicator, multi-output indicator, nested logic, advanced analytics, risk loops).
   - Add pytest helpers to compile a workflow and compare against golden Python files (AST normalized to avoid formatting drift).

### Phase 1 – Core Infrastructure
1. **Normalization & IR**
   - Extend `ir.py` to carry connection metadata (handle IDs, `dataType`, optional transformation info imported from a mirrored connection rules table).
   - Implement JSON schema validation using `pydantic` models (optional but recommended) so malformed workflows fail fast.
2. **Semantic Analyzer**
   - New module `semantic_analyzer.py`:
     - Load backend copy of component metadata (node types, handle definitions, parameter schemas) derived from frontend cheat sheet.
     - Validate required nodes (at least one data source, at least one action, at least one output).
     - Check parameter completeness per node category (e.g., SMA requires `period`; MACD requires `fastPeriod`, `slowPeriod`, `signalPeriod`; all condition subtypes enforce their special fields).
     - Enforce connection rules for every edge using mirrored logic from `src/frontend/lib/connection-manager.ts`.
     - Propagate `DataType` along edges and record mismatches (e.g., numeric data feeding a signal-only handle).
3. **Execution Planner**
   - New module `execution_planner.py`:
     - Perform topological sort and annotate each node with `execution_order`.
     - Group nodes into pipeline stages (Data Prep, Indicator, Analytics, Condition, Logic, Risk, Action, Output).
     - Detect parallelizable paths (multiple indicators from same data feed) for potential optimization hints.
     - Output plan consumed by code generator.

### Phase 2 – Node Handler Coverage
1. **Data sources**
   - Handlers: `data_source.py`, `custom_dataset.py`.
   - Responsibilities: produce dataset loading code (system feed adapters vs. CSV uploads), apply normalization/missing value handling.
2. **Technical indicators**
   - Handler factory pattern that maps indicator IDs to specific TA-library functions (TA-Lib, pandas TA, or in-house implementations).
   - Support multi-output indicators (Bollinger, MACD, Stochastic, Ichimoku, Volume Profile, Market Structure) by emitting named series and storing them in context.
3. **Advanced analytics**
   - Market Regime Detection: integrate existing ML models from `ai-ml-strategy-service` or placeholder heuristics; expose outputs for trend/sideways/volatile.
   - Multi-Timeframe Analysis: emit resampling logic and caching to avoid recomputation.
   - Correlation Analysis: handle dual data inputs, produce correlation coefficients/time series.
   - Sentiment Analysis: hook into `inference-service` endpoints and map outputs to positive/neutral/negative handles.
4. **Conditions & Logic**
   - Condition handler reads `condition` parameter to decide evaluation template (comparison, crossover, pattern, etc.).
   - Logic handler merges boolean signals with configurable gate types and input counts.
5. **Actions & Outputs**
   - Action handler generates order construction code (position sizing, order type, TP/SL, trailing stops, hedging).
   - Output handler logs/emits signals to downstream clients (training dashboards, execution dashboards).
6. **Risk Management**
   - Handler enforces position sizing, drawdown monitoring, VaR, leverage caps, emergency actions, and can gate downstream action execution.

### Phase 3 – Code Generation & Optimization
1. **EnhancedCodeGenerator integration**
   - Ensure every handler registers in `HANDLER_REGISTRY`.
   - Implement `GeneratedSnippet` merging logic to avoid duplicate imports/state definitions.
   - Support output modes (backtest/live/training) via emitter classes under `emitters/`.
2. **Optimization passes**
   - Flesh out `_dead_code_elimination`, `_common_subexpression_elimination`, `_constant_folding`, `_loop_optimization` to actually transform the AST or intermediate representation.
   - Add caching hints for repeated indicator computations or multi-timeframe resampling.
3. **Runtime adapters**
   - Build connectors to `backtest-service`, `trading-engine`, and `ai-ml-strategy-service` so compiled code can be executed in all runtimes without manual edits.

### Phase 4 – Validation & Tooling
1. **Static validation**
   - Extend `validate_generated_code.py` to run `ast.parse`, `compile`, and lint (flake8/ruff) checks.
   - Add optional dry-run that injects sample OHLCV data and ensures every indicator output/condition path evaluates without raising.
2. **Telemetry**
   - Log compile-time metrics (duration per stage, number of nodes/edges, optimization hits) and store in database for analytics.
3. **Developer ergonomics**
   - Provide `scripts/compile_workflow.py` CLI to compile a workflow JSON locally.
   - Document the process in `docs/no-code-compiler-architecture.md` (this file) and update service README.

### Phase 5 – QA & Rollout
1. **Regression suite**
   - Run full matrix of fixture workflows covering all frontend components.
   - Integrate into CI (Cloud Build trigger) to block deployments when compiler regressions occur.
2. **Shadow mode**
   - Deploy new compiler alongside existing implementation, compare outputs and runtime behavior using selected user workflows.
3. **Cutover**
   - Once parity is confirmed, switch GraphQL resolvers to new compiler and remove legacy code paths.
4. **Post-launch monitoring**
   - Watch telemetry dashboards and error logs; add auto-rollbacks or feature flags if needed.

Following this plan ensures the compiler handles every component exposed in the frontend and produces reliable Python strategies end-to-end.
