# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Commands
```bash
# Frontend development
cd src/frontend
npm run dev                # Start development server (http://localhost:3000)
npm run build             # Build for production  
npm run lint              # Run ESLint
npm run type-check        # TypeScript type checking

# Platform deployment
make deploy-all           # Deploy complete platform to cloud (30-45 min)
make quick-deploy         # Deploy locally with Docker (5 min)
make status              # Check platform health
make destroy-all         # Destroy entire platform (DESTRUCTIVE)

# Backend services
cd src/backend/no-code-service
python main.py           # Start no-code service
python init_database.py # Initialize database

# Kubernetes operations
cd infra/kubernetes
./scripts/k8s/deploy.sh         # Deploy to Kubernetes
./scripts/k8s/deploy-minimal.sh # Minimal deployment
kubectl get pods -n alphintra   # Check service status
```

## Architecture Overview

### High-Level Structure
Alphintra is an enterprise-grade algorithmic trading platform with microservices architecture:

**Core Components:**
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **API Gateway**: Spring Boot with Eureka service discovery
- **Trading Engine**: Ultra-low latency Java service (<1ms)
- **No-Code Console**: Visual workflow builder using React Flow
- **AI/ML Services**: Python-based strategy engines with LLM integration
- **Infrastructure**: Kubernetes on multi-cloud (GCP/AWS/Azure)

### Key Microservices
- **Auth Service**: Spring Boot authentication/authorization
- **Trading API**: FastAPI for order management and execution
- **No-Code Service**: FastAPI for visual strategy building
- **Strategy Engine**: Python ML pipeline for backtesting
- **Market Data Service**: Real-time data processing
- **Risk Management**: Portfolio and compliance monitoring
- **Gateway**: Spring Cloud Gateway with load balancing

### No-Code Console Architecture
The visual workflow builder is the platform's flagship feature:

**Frontend Stack:**
- React Flow v11 for visual node editor
- Zustand for state management
- Monaco Editor for code viewing
- Custom node types: TechnicalIndicator, Condition, Action, DataSource, Risk, Logic

**Key Components:**
- `NoCodeWorkflowEditor.tsx`: Main visual editor using React Flow
- `TechnicalIndicatorNode.tsx`: Multi-output indicator nodes (ADX, MACD, Bollinger Bands)
- `connection-manager.ts`: Handles node connection rules and validation
- `workflow-validation.ts`: Validates workflow structure and data types

**Backend Integration:**
- FastAPI service at `/api/workflows`
- GraphQL resolvers for complex queries
- PostgreSQL for workflow persistence
- Code generation to executable Python strategies

### Database Architecture
- **PostgreSQL**: Primary transactional data (users, workflows, trades)
- **TimescaleDB**: Time-series market data and metrics
- **Redis**: Caching and session management
- **InfluxDB**: Monitoring and observability data

### Frontend Application Structure
```
src/frontend/
├── app/                    # Next.js app router
│   ├── (auth)/            # Authentication pages
│   ├── (user)/            # User dashboard pages
│   └── strategy-hub/      # No-code console entry
├── components/
│   ├── no-code/           # Visual workflow builder
│   │   ├── nodes/         # Custom React Flow nodes
│   │   ├── edges/         # Custom connection types
│   │   └── configuration/ # Node parameter panels
│   └── ui/               # Reusable UI components
├── lib/
│   ├── stores/           # Zustand state management
│   ├── api/              # API client functions
│   └── workflow-*.ts     # Workflow processing utilities
```

## Critical Development Notes

### No-Code Console Development
When working with the visual workflow builder:
- Node types must be registered in `nodeTypes` object in `NoCodeWorkflowEditor.tsx`
- All nodes use Zustand store for state management via `useNoCodeStore`
- Connection rules are defined in `connection-manager.ts` - add new rules when creating multi-output indicators
- Handle IDs follow pattern `{outputId}-output` (e.g., `adx-output`, `di_plus-output`)
- Workflow validation happens in `workflow-validation.ts` for type checking and structure validation

### Multi-Output Technical Indicators
Technical indicators like ADX, MACD, Bollinger Bands have multiple outputs:
- ADX: `adx-output`, `di_plus-output`, `di_minus-output`
- MACD: `macd-output`, `signal-output`, `histogram-output`
- Bollinger Bands: `upper-output`, `middle-output`, `lower-output`, `width-output`

Each output requires connection rules in `connection-manager.ts` and proper type handling in `workflow-validation.ts`.

### API Integration Patterns
- **GraphQL**: Used for complex no-code workflow queries via Apollo Client
- **REST**: Standard CRUD operations using axios
- **WebSocket**: Real-time market data and trade updates
- **Authentication**: JWT tokens with Spring Security integration

### Deployment Architecture
- **Local**: Docker Compose with hot-reload for development
- **Kubernetes**: Multi-environment deployments (dev/staging/prod)
- **Cloud**: Terraform-managed infrastructure on GCP/AWS/Azure
- **Monitoring**: Prometheus/Grafana stack with custom dashboards

### Testing Approach
- **Frontend**: React Testing Library + Jest
- **Backend**: Spring Boot Test + PyTest
- **Integration**: Kubernetes-based end-to-end testing
- **Performance**: JMeter for trading engine latency testing (<1ms requirement)

## Key Configuration Files
- `src/frontend/package.json`: Frontend dependencies and scripts
- `docker-compose.yml`: Local development environment
- `infra/kubernetes/base/`: Kubernetes deployment configurations
- `Makefile`: Platform deployment orchestration
- `src/backend/*/application.yml`: Spring Boot service configurations

## Platform Access Points
**Local Development:**
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8080
- No-Code Service: http://localhost:8001
- Monitoring: http://localhost:3001

**Production:**
- Trading Dashboard: https://trading.alphintra.com
- API Gateway: https://api.alphintra.com
- Monitoring: https://grafana.alphintra.com