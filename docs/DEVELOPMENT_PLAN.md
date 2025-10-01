# Alphintra No-Code → AI-ML Integration Plan

## Phase 1: Service Bridge Foundation
**Goal**: Connect no-code-service with ai-ml-strategy-service for workflow → training pipeline

### 1.1 No-Code Service Extensions

#### 1.1.1 Execution Mode API Endpoint
**File**: `src/backend/no-code-service/main.py` (line 480+)
**Problem Solved**: Dual code generation modes - strategy vs model training
- [x] Add `ExecutionModeRequest` model with mode and config fields
- [x] Create `POST /api/workflows/{workflow_id}/execution-mode` endpoint  
- [x] Implement workflow validation and user authorization
- [x] **Strategy Mode**: Use existing code_generator for immediate strategy code
- [x] **Model Mode**: Generate training code + forward to ai-ml-strategy-service (placeholder)
- [x] Store execution mode in database for tracking (pending schema updates)
- [x] Return structured response with next_action based on mode

#### 1.1.2 Workflow-to-Training Converter  
**File**: `src/backend/no-code-service/workflow_converter.py` (new)
**Problem Solved**: Convert visual workflow to ML training configuration
- [x] Create `WorkflowConverter` class
- [x] Implement `convert_to_training_config(workflow_data)` method
- [x] **Node Mapping**: dataSource → dataset requirements for training
- [x] **Node Mapping**: technicalIndicator → feature engineering pipeline
- [x] **Node Mapping**: condition → target/label generation logic
- [x] **Node Mapping**: action → trading signal optimization targets
- [x] **Node Mapping**: risk → constraint parameters for training
- [x] Add validation for required node types for ML training
- [x] Add error handling for malformed workflow data

#### 1.1.3 HTTP Client for AI-ML Service
**File**: `src/backend/no-code-service/clients/aiml_client.py` (new)
- [x] Create `AIMLClient` class with httpx AsyncClient
- [x] Implement `create_training_job_from_workflow()` method
- [x] Implement `get_training_job_status()` method
- [x] Implement `get_training_job_results()` method
- [x] Add circuit breaker pattern for failures
- [x] Add retry logic with exponential backoff
- [x] Add authentication token handling
- [x] Add comprehensive error handling and logging

#### 1.1.4 Database Schema Updates
**File**: `src/backend/no-code-service/models.py`
- [x] Add execution_mode column to NoCodeWorkflow model
- [x] Add aiml_training_job_id column to NoCodeWorkflow model  
- [x] Add execution_metadata JSON column to NoCodeWorkflow model
- [x] Create ExecutionHistory table with required fields
- [x] Create database migration script
- [x] Test migration on development database
- [x] Update existing queries to handle new columns
- [x] Add database indexes for performance

### 1.2 AI-ML Service Integration

#### 1.2.1 Workflow Ingestion Endpoint
**File**: `src/backend/ai-ml-strategy-service/app/api/endpoints/training.py` (after line 100)
- [x] Add `WorkflowTrainingRequest` model with required fields
- [x] Create `POST /api/training/from-workflow` endpoint
- [x] Add user authentication and authorization checks
- [x] Implement workflow definition validation
- [x] Add rate limiting for workflow submissions
- [x] Return training job ID and status response
- [x] Add comprehensive error handling
- [x] Add logging for workflow ingestion events

#### 1.2.2 Workflow Definition Parser
**File**: `src/backend/ai-ml-strategy-service/app/services/workflow_parser.py` (new)
- [x] Create `WorkflowParser` class  
- [x] Implement `parse_data_sources(nodes)` method
- [x] Implement `parse_indicators(nodes)` method
- [x] Implement `parse_conditions(nodes)` method
- [x] Implement `parse_actions(nodes)` method
- [x] Add validation for required node types
- [x] Add error handling for unsupported nodes
- [x] Add logging for parsing operations

#### 1.2.3 Strategy Creation from Workflow  
**File**: `src/backend/ai-ml-strategy-service/app/services/strategy_generator.py` (new)
- [x] Create `StrategyGenerator` class
- [x] Implement `generate_from_workflow(parsed_data)` method
- [x] Add Python code template system
- [x] Add feature engineering code generation
- [x] Add target generation code creation
- [x] Add strategy execution logic
- [x] Add code validation and syntax checking
- [x] Add comprehensive error handling

#### 1.2.4 Training Job Creation Enhancement
**File**: `src/backend/ai-ml-strategy-service/app/services/training_job_manager.py` (line 200+)  
- [x] Add `create_job_from_workflow()` method to existing class
- [x] Implement workflow config to training job conversion
- [x] Add strategy creation from workflow data
- [x] Add database record creation for workflow jobs
- [x] Add job queue submission logic
- [x] Add status tracking for workflow-generated jobs
- [x] Add cleanup handling for failed jobs
- [x] Add integration with existing training infrastructure

### 1.3 Testing & Validation

#### 1.3.1 Unit Tests  
**Files**: `src/backend/no-code-service/tests/`, `src/backend/ai-ml-strategy-service/tests/`
- [x] Test execution mode endpoint with valid workflows
- [x] Test execution mode endpoint with invalid workflows  
- [x] Test workflow converter with all node types
- [x] Test workflow converter with malformed data
- [x] Test AI-ML client methods with mock responses
- [x] Test AI-ML client error scenarios
- [x] Test database model changes and migrations
- [x] Test new API endpoints with authentication

#### 1.3.2 Integration Tests
**Files**: `tests/integration/`
- [ ] Test complete workflow → strategy generation flow
- [ ] Test complete workflow → training job creation flow
- [ ] Test service communication with network delays
- [ ] Test service communication with authentication failures
- [ ] Test database consistency across services
- [ ] Test concurrent workflow processing
- [ ] Test error propagation between services
- [ ] Test performance under load

#### 1.3.3 Error Scenarios
**Files**: `tests/error_scenarios/`  
- [x] Test network failures during AI-ML service calls
- [x] Test invalid workflow definitions handling
- [x] Test training job creation failures
- [x] Test database transaction rollbacks
- [x] Test authentication token expiry scenarios
- [x] Test service unavailability graceful handling
- [x] Test malformed response handling
- [x] Test timeout scenarios and recovery

## Phase 2: Frontend Execution Mode Selection  
**Goal**: Add UI for users to choose strategy vs model execution

### 2.1 Execution Mode Selector Component
**File**: `src/frontend/components/no-code/ExecutionModeSelector.tsx` (new)
- [x] Create component with workflowId and onModeSelect props
- [x] Add two-card layout design for mode selection
- [x] Create strategy mode card with quick execution messaging
- [x] Create model mode card with ML optimization messaging  
- [x] Add config panel for strategy parameters
- [x] Add config panel for model training settings
- [x] Implement API call to execution mode endpoint
- [x] Add loading states and error handling
- [x] Add redirect logic based on selected mode
- [x] Add form validation for required parameters

### 2.2 Training Progress Dashboard
**File**: `src/frontend/components/no-code/TrainingDashboard.tsx` (new)
- [x] Create TrainingState interface with job status fields
- [x] Set up WebSocket connection to ai-ml-strategy-service
- [x] Add progress bar with percentage and ETA display
- [x] Create real-time logs stream component
- [x] Add resource usage metrics display (CPU/GPU/Memory)
- [x] Create training metrics charts (loss, accuracy)
- [x] Add cancel/pause training controls
- [x] Implement auto-refresh for job status
- [x] Add error state handling and retry logic
- [x] Add completion celebration and results display

### 2.3 Workflow Editor Integration
**File**: `src/frontend/components/no-code/NoCodeWorkflowEditor.tsx` (line 200+)
- [x] Add "Execute Workflow" button to toolbar
- [x] Create modal state for ExecutionModeSelector
- [x] Add button click handler to show mode selector
- [x] Implement mode selection result handling
- [x] Add navigation logic for strategy vs model results
- [x] Update workflow save logic to enable execution
- [x] Add execution status indicator to workflow
- [x] Add breadcrumb navigation for execution flow

### 2.4 Navigation and State Management
**Files**: Multiple
- [x] Create `src/frontend/lib/stores/execution-store.ts` with Zustand
- [x] Add execution state management (mode, jobId, status)
- [x] Create `/workflows/[id]/execute/page.tsx` route
- [x] Create `/workflows/[id]/training/[jobId]/page.tsx` route  
- [x] Create `/workflows/[id]/results/[executionType]/page.tsx` route
- [x] Add URL state persistence for execution flow
- [x] Add browser storage for training job status caching
- [x] Update navigation components with new routes
- [x] Add back/forward navigation handling
- [x] Add deep linking support for shared training jobs

## Phase 3: AI Code Editor Features  
**Goal**: Enable advanced users to create custom ML models with AI assistance

### 3.1 AI Code Service (Backend)

> **Update (Security Hardening)**: The original AI code service and its endpoints were decommissioned to remove direct LLM provider dependencies from the core platform. These capabilities are now intentionally disabled on the backend until a hardened alternative is delivered.

### 3.2 AI Code Endpoints

> **Update (Security Hardening)**: The `/api/ai/*` routes were removed from the FastAPI service. Frontend requests now terminate at the Next.js proxy layer, which responds with a clear message that the AI assistant is unavailable.

### 3.3 Enhanced IDE Interface
**File**: `src/frontend/components/ide/EnhancedIDE.tsx` (new)

**Architecture**: Monaco Editor + AI Assistant Panel
**Layout**: 
- Left: File explorer and project structure
- Center: Code editor with AI inline suggestions  
- Right: AI assistant chat panel
- Bottom: Terminal, logs, and test results

**AI Features**:
- **Inline Suggestions**: Real-time code completion with AI
- **Chat Interface**: Natural language code generation requests
- **Code Explanation**: Hover over code for AI explanations
- **Auto-debugging**: AI-powered error detection and fixes
- **Test Generation**: Automatic unit test creation

**Editor Modes**:
- **Traditional Mode**: Full IDE features without AI
- **AI-Assisted Mode**: AI suggestions and chat enabled
- **AI-First Mode**: Natural language programming interface

**Seamless Switching**: 
```typescript
const [editorMode, setEditorMode] = useState<'traditional' | 'ai-assisted' | 'ai-first'>('ai-assisted');

const switchMode = (newMode: EditorMode) => {
  // Preserve current code and context
  // Adjust UI layout for new mode
  // Initialize mode-specific features
  setEditorMode(newMode);
};
```

### 3.4 Project Management System
**File**: `src/frontend/components/ide/ProjectManager.tsx` (new)

**Purpose**: Manage complex ML projects with multiple files
**Features**:
- File/folder structure management
- Git integration for version control
- Dependency management (requirements.txt, package.json)
- Environment management (dev/staging/prod)
- Deployment configuration

**Project Templates**:
- Deep Learning Trading Model
- Ensemble Strategy Framework  
- Real-time Prediction Service
- Custom Indicator Library
- Backtesting Framework

## Phase 4: Advanced Model Deployment & Serving
**Goal**: Deploy trained models as production prediction services

### 4.1 Model Registry and Versioning ✅
**File**: `src/backend/ai-ml-strategy-service/app/services/model_registry.py` (new)

**Features**:
- [x] Model artifact storage (weights, metadata, code)
- [x] Version management with semantic versioning  
- [x] Model lineage tracking (dataset, training config, parent models)
- [x] Performance benchmarking across versions
- [x] A/B testing framework for model comparison
- [x] Database models for Model, ModelVersion, ModelDeployment, ModelABTest, ModelMetrics
- [x] ModelRegistry service class with artifact storage backends (S3, GCS, local)
- [x] Model validation, comparison, and promotion capabilities
- [x] RESTful API endpoints for model management operations
- [x] File upload handling for model artifacts
- [x] Model version promotion workflow
- [x] A/B test creation and management
- [x] Model lineage and ancestry tracking

**Database Schema**: 
```python
class ModelVersion(Base):
    id, model_id, version, artifacts_path, metadata,
    performance_metrics, deployment_status, created_at
    
class ModelDeployment(Base):
    id, model_version_id, deployment_config, k8s_config,
    endpoint_url, status, health_metrics, created_at
```

### 4.2 Kubernetes Model Serving ✅
**File**: `src/backend/ai-ml-strategy-service/app/services/k8s_deployment.py` (new)

**Deployment Pipeline**:
- [x] Package model artifacts with serving code
- [x] Build Docker image with model server
- [x] Create Kubernetes deployment manifest  
- [x] Deploy with auto-scaling and health checks
- [x] Expose prediction endpoint via ingress
- [x] Configure monitoring and logging
- [x] KubernetesModelDeployment service class with full deployment lifecycle
- [x] Docker image building with FastAPI serving code generation
- [x] Kubernetes resource management (Deployment, Service, HPA, Ingress)
- [x] Deployment scaling and update operations
- [x] Resource cleanup and pod restart capabilities
- [x] RESTful API endpoints for deployment management

**Serving Infrastructure**:
- **Model Server**: FastAPI-based prediction service
- **Load Balancer**: NGINX ingress with SSL termination
- **Auto-scaling**: HPA based on request volume and latency
- **Health Checks**: Liveness and readiness probes
- **Resource Limits**: CPU/memory/GPU quotas per model

### 4.3 Real-time Prediction Pipeline ✅
**File**: `src/backend/ai-ml-strategy-service/app/services/prediction_service.py` (new)

**Architecture**: 
```
Market Data Stream → Feature Engineering → Model Prediction → Trading Signal → Risk Check → Order Execution
```

**Components**:
- [x] **Stream Processor**: Real-time data ingestion and preprocessing
- [x] **Feature Cache**: Redis-based feature store for low-latency access
- [x] **Prediction Queue**: Async prediction processing with priority queuing  
- [x] **Signal Aggregator**: Combine multiple model predictions
- [x] **Risk Manager**: Real-time risk checks and position limits
- [x] PredictionService class with caching, rate limiting, and circuit breakers
- [x] Batch prediction support with concurrency control
- [x] Performance metrics tracking (latency percentiles, error rates)
- [x] Background task processing with queue management
- [x] RESTful API endpoints for prediction requests and monitoring

**Performance Requirements**:
- Sub-100ms prediction latency (95th percentile)
- 10,000+ predictions per second throughput
- 99.9% uptime availability
- Automatic failover to backup models

### 4.4 Model Performance Monitoring ✅
**File**: `src/backend/ai-ml-strategy-service/app/services/model_monitor.py` (new)

**Monitoring Metrics**:
- [x] **Prediction Performance**: Accuracy, precision, recall over time
- [x] **System Performance**: Latency, throughput, error rates
- [x] **Data Drift**: Feature distribution changes detection (PSI, KS, Chi-square)
- [x] **Model Degradation**: Performance decline alerts
- [x] **Business Impact**: P&L attribution to model predictions
- [x] ModelMonitoringService with comprehensive health tracking
- [x] Data drift detection using multiple statistical tests
- [x] Performance degradation monitoring with configurable thresholds
- [x] Alert management with cooldown and notification systems
- [x] RESTful API endpoints for monitoring setup and management

**Alerting System**:
- Performance degradation beyond thresholds
- Data quality issues in input features
- Prediction service downtime or errors
- Unusual prediction patterns or outliers

**Dashboards**: Grafana-based monitoring with real-time metrics

### 4.5 Model Lifecycle Management ✅
**File**: `src/backend/ai-ml-strategy-service/app/services/model_lifecycle.py` (new)

**Automated Pipeline**:
1. [x] **Continuous Training**: Retrain models on new data with cron scheduling
2. [x] **Validation**: Automated testing on holdout datasets
3. [x] **Staging Deployment**: Deploy to staging environment with K8s
4. [x] **A/B Testing**: Gradual rollout with performance comparison
5. [x] **Production Deployment**: Full rollout if performance validated
6. [x] **Monitoring**: Continuous monitoring and alerting integration
7. [x] **Rollback**: Automatic rollback if issues detected
- [x] ModelLifecycleService with full automation capabilities
- [x] Lifecycle stages and automated transitions
- [x] Background task management for scheduled operations
- [x] Event logging and audit trail
- [x] RESTful API endpoints for lifecycle management

**Configuration**:
```python
class ModelLifecycleConfig:
    retrain_schedule: str = "daily"
    validation_threshold: float = 0.8
    ab_test_duration: int = 168  # hours
    rollout_percentage: int = 10  # gradual rollout
    performance_threshold: float = 0.05  # improvement required
```

## Phase 5: Enterprise Features (Future)
**Goal**: Enterprise-grade features for institutional users

### 5.1 Multi-tenancy and User Management
- Organization-level access controls
- Resource quotas and billing
- Audit logging and compliance
- SSO integration (SAML/OIDC)

### 5.2 Advanced Risk Management  
- Real-time portfolio risk monitoring
- Regulatory compliance checks
- Position limits and risk controls
- Stress testing and scenario analysis

### 5.3 Market Data Integration
- Multiple data vendor support
- Alternative data sources (sentiment, satellite, etc.)
- Data quality monitoring
- Cost optimization across providers

### 5.4 Performance Attribution
- Model contribution analysis
- Strategy performance decomposition
- Risk-adjusted returns calculation
- Benchmark comparison and analysis

---

## Implementation Order
1. **Phase 1.1**: No-code service extensions (Week 1)
2. **Phase 1.2**: AI-ML service integration (Week 2)  
3. **Phase 1.3**: Testing & validation (Week 3)
4. **Phase 2**: Frontend execution mode (Week 4)
5. **Phase 3**: AI code editor (Week 5-7)
6. **Phase 4**: Advanced deployment (Week 8-10)
7. **Phase 5**: Enterprise features (Month 3-4)

## User Journey Coverage

### Basic User (No-Code Strategy)
1. Create workflow via drag-and-drop → ✅ Covered in existing frontend
2. Choose "Strategy Mode" → ✅ Phase 2.1 ExecutionModeSelector
3. Get generated strategy code → ✅ Phase 1.1.1 existing code_generator
4. Backtest and deploy → ✅ Existing ai-ml-strategy-service

### Pro User (Parameter Optimization)  
1. Create workflow via drag-and-drop → ✅ Covered in existing frontend
2. Choose "Model Mode" → ✅ Phase 2.1 ExecutionModeSelector  
3. Training job created → ✅ Phase 1.2 workflow ingestion
4. Monitor training progress → ✅ Phase 2.2 TrainingDashboard
5. Get optimized parameters → ✅ Phase 1.2.4 training job completion
6. Deploy optimized strategy → ✅ Existing ai-ml-strategy-service

### Premium User (Custom AI Models)
1. Access IDE interface → ✅ Phase 3.3 EnhancedIDE
2. Use AI to generate complex models → ✅ Phase 3.1 AI code service
3. Switch between AI-assisted and traditional coding → ✅ Phase 3.3 seamless switching
4. Deploy custom models for predictions → ✅ Phase 4.2 Kubernetes serving
5. Monitor model performance → ✅ Phase 4.4 performance monitoring
6. Continuous model improvement → ✅ Phase 4.5 lifecycle management

## Core Problem Resolution

### ❌ **Original Problem**: Dual Code Generation Confusion
**Current State**: No-code service has two competing code generation engines
- `workflow_compiler_updated.py` → Generates trading strategy code (hardcoded templates)
- `code_generator.py` + node handlers → Generates ML training scripts (flexible system)
- Users confused about which path to take
- No clear execution mode selection

### ✅ **Solution**: Unified Workflow with Execution Mode Selection

#### **Strategy Mode** (Immediate Execution)
1. User creates workflow → Visual nodes/edges
2. User selects "Strategy Mode" → Use my parameters as-is
3. System uses existing `code_generator.py` + node handlers
4. **Output**: Python strategy code with user's specified thresholds
5. Direct execution via existing ai-ml-strategy-service backtesting

#### **Model Mode** (Parameter Optimization) 
1. User creates workflow → Same visual nodes/edges  
2. User selects "Model Mode" → Find optimal parameters via ML
3. System converts workflow to training configuration
4. **Output**: Training job in ai-ml-strategy-service
5. ML finds optimal parameters → Generates optimized strategy code
6. Execution with ML-discovered optimal thresholds

### Implementation Architecture
```
Visual Workflow (nodes + edges)
        ↓
Execution Mode Selection
   ↙         ↘
Strategy Mode   Model Mode
   ↓              ↓
Direct Code      Training Config
Generation       Conversion
   ↓              ↓
Strategy Code    AI-ML Service
   ↓              ↓
Execute         Train Model
                   ↓
                Optimized Strategy
                   ↓
                 Execute
```

### Technical Architecture Coverage

### Service Communication Issues (Solved)
- **No-code → AI-ML integration**: Phase 1.1.3 HTTP client with retry logic
- **Authentication across services**: Existing JWT validation extended
- **Error propagation**: Structured error responses with user context
- **Network failures**: Circuit breaker pattern with graceful fallbacks

### Dual Code Generation Confusion (Resolved)
- **Single workflow creation**: Same visual interface for both modes
- **Clear mode separation**: Strategy vs Model selection after workflow creation
- **Code generation routing**: Strategy mode → existing generator, Model mode → training pipeline
- **Legacy system handling**: Gradual deprecation of old compiler with feature flags

### AI/ML Capabilities Consolidation (Implemented)
- **All AI features in ai-ml-strategy-service**: No separate AI service needed
- **LLM integration**: Phase 3.1 with multiple provider support
- **Model serving**: Phase 4 comprehensive deployment pipeline
- **Real-time predictions**: Phase 4.3 sub-100ms latency pipeline

### User Experience Complexity (Simplified)
- **Progressive disclosure**: Basic → Pro → Premium feature tiers
- **Execution mode selection**: Clear two-option choice with guidance
- **Training progress**: Real-time updates with cancellation options
- **Error handling**: User-friendly messages with actionable steps

## Success Metrics
- [ ] **Basic Users**: Create and deploy strategy in <5 minutes
- [ ] **Pro Users**: Complete training job and get optimized parameters
- [ ] **Premium Users**: Deploy custom model with <100ms prediction latency
- [ ] **System Performance**: 99.9% uptime, <2s response times
- [ ] **User Adoption**: 80% completion rate for workflows
- [ ] **Business Impact**: 3x model performance vs manual strategies

## Risk Mitigation & Contingency Plans

### Technical Risks
- **Service communication failures**: 
  - Mitigation: Circuit breaker, retry logic, graceful degradation
  - Contingency: Offline mode for strategy generation
- **Training job failures**: 
  - Mitigation: Comprehensive error reporting, automatic retries
  - Contingency: Fallback to simpler optimization algorithms
- **Model serving downtime**:
  - Mitigation: Multi-region deployment, health checks
  - Contingency: Automatic failover to backup models
- **LLM API limitations**:
  - Mitigation: Multiple provider integration, response caching
  - Contingency: Local model fallback for critical features

### Business Risks  
- **User complexity**: 
  - Mitigation: Progressive feature disclosure, comprehensive onboarding
  - Contingency: Simplified UI mode for basic users
- **Performance expectations**:
  - Mitigation: Clear SLA communication, real-time status updates
  - Contingency: Performance guarantees with compensation
- **Competitive pressure**:
  - Mitigation: Unique AI-assisted workflow approach
  - Contingency: Open-source components to build ecosystem

### Operational Risks
- **Resource scaling**:
  - Mitigation: Auto-scaling Kubernetes infrastructure
  - Contingency: Manual resource allocation procedures
- **Data security**:
  - Mitigation: Encryption at rest/transit, audit logging
  - Contingency: Incident response procedures, compliance checks
- **Team bandwidth**:
  - Mitigation: Phased rollout, automated testing
  - Contingency: External contractor support for non-critical features

## Quality Gates
- **Phase 1**: Integration tests pass, <2s API response times
- **Phase 2**: 95% user task completion rate in usability testing
- **Phase 3**: AI code generation 80% accuracy on standard tasks
- **Phase 4**: Model serving meets <100ms latency requirement
- **Overall**: End-to-end user journey completion in <10 minutes

## Rollback Plans
- **Database migrations**: Backward-compatible schemas with rollback scripts
- **Service deployments**: Blue-green deployment with instant rollback capability  
- **Feature flags**: Gradual rollout with immediate disable switches
- **Model deployments**: Automatic rollback on performance degradation