# Alphintra Platform - AI Coding Assistant Instructions

## Architecture Overview

Alphintra is a microservices-based algorithmic trading platform with the following key components:

### Core Services & Ports
- **Frontend**: Next.js 15 + TypeScript (localhost:3000)
- **API Gateway**: Spring Boot (localhost:8080)
- **Auth Service**: Spring Boot (localhost:8001)
- **AI/ML Strategy Service**: Python FastAPI (localhost:8002)
- **No-Code Service**: Python FastAPI (localhost:8006)
- **Trading API**: FastAPI (localhost:8003)
- **Market Data Service**: Python (localhost:8005)
- **Backtest Service**: Python (localhost:8007)

### Data Layer
- **PostgreSQL**: Primary transactional data (localhost:5432)
- **TimescaleDB**: Time-series market data (localhost:5433)
- **Redis**: Caching/session management (localhost:6379)
- **Kafka**: Event streaming (localhost:9092)

## Critical Development Patterns

### No-Code Workflow Builder (React Flow)
When working with visual workflow components:

**Node Registration**: All custom nodes must be registered in `NoCodeWorkflowEditor.tsx`:
```typescript
const nodeTypes = {
  technicalIndicator: TechnicalIndicatorNode,
  condition: ConditionNode,
  action: ActionNode,
  // ... register new nodes here
};
```

**Multi-Output Technical Indicators**: Indicators like ADX, MACD, Bollinger Bands have multiple outputs:
- ADX: `adx-output`, `di_plus-output`, `di_minus-output`
- MACD: `macd-output`, `signal-output`, `histogram-output`
- Bollinger Bands: `upper-output`, `middle-output`, `lower-output`, `width-output`

**Connection Rules**: Define in `lib/connection-manager.ts`:
```typescript
export const connectionRules: ConnectionRule[] = [
  {
    id: 'adx-to-condition',
    sourceType: 'technicalIndicator',
    targetType: 'condition',
    sourceHandle: 'adx-output',
    targetHandle: 'input',
    dataType: 'number'
  }
  // Add rules for each output handle
];
```

**State Management**: Use Zustand store (`useNoCodeStore`) for all workflow state:
```typescript
const { currentWorkflow, updateNode, addConnection } = useNoCodeStore();
```

### API Client Patterns

**BaseApiClient Usage**: Extend for service-specific clients:
```typescript
export class FileManagementApi extends BaseApiClient {
  constructor() {
    super({
      baseUrl: process.env.NEXT_PUBLIC_AI_ML_SERVICE_URL || 'http://localhost:8002',
      timeout: 60000, // File operations need longer timeout
    });
  }
}
```

**Error Handling**: Preserve ApiError instances, enhance network diagnostics:
```typescript
try {
  return await this.request(endpoint, options);
} catch (error) {
  if (error instanceof ApiError) {
    throw error; // Preserve structured API errors
  }
  // Enhance network error messages with context
  throw new Error(`Network error: ${error.message} | ${method} ${endpoint}`);
}
```

**Environment Variables**: Frontend uses `NEXT_PUBLIC_*` prefix:
- `NEXT_PUBLIC_API_BASE_URL`: Gateway (default: localhost:8000)
- `NEXT_PUBLIC_AI_ML_SERVICE_URL`: AI/ML service (default: localhost:8002)
- `NEXT_PUBLIC_AUTH_API_URL`: Auth service (default: localhost:8001)

### Backend Service Patterns

**FastAPI Services**: Standard structure in `src/backend/{service-name}/`:
```
app/
├── main.py              # FastAPI app instance
├── api/
│   ├── routes.py        # Route definitions
│   └── endpoints/       # Endpoint implementations
├── core/
│   ├── config.py        # Pydantic settings
│   └── database.py      # DB connections
├── models/              # SQLAlchemy models
└── services/            # Business logic
```

**Configuration**: Use Pydantic settings with environment variables:
```python
class Settings(BaseSettings):
    PORT: int = Field(default=8002)
    DATABASE_URL: str = Field(default="postgresql://...")
    REDIS_URL: str = Field(default="redis://localhost:6379")

settings = get_settings()
```

### Deployment & Development Workflow

**Local Development**:
```bash
# Full platform
make quick-deploy

# Individual services
cd src/backend/ai-ml-strategy-service
python -m uvicorn main:app --reload --port 8002

# Frontend
cd src/frontend
npm run dev
```

**Docker Development**:
```bash
# Build specific service
docker-compose -f infra/docker/dev/docker-compose.minimal.yml build ai-ml-strategy-service

# Start services
docker-compose -f infra/docker/dev/docker-compose.minimal.yml up -d
```

**Health Checks**:
```bash
# Service health
curl http://localhost:8002/health

# Platform status
make status
```

### Database Patterns

**PostgreSQL**: Use async SQLAlchemy with connection pooling:
```python
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
async_session = sessionmaker(engine, class_=AsyncSession)
```

**Redis**: Use redis-py with connection pooling:
```python
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
```

### Testing Patterns

**Frontend**: React Testing Library + Jest:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { NoCodeWorkflowEditor } from './NoCodeWorkflowEditor';

test('renders workflow editor', () => {
  render(<NoCodeWorkflowEditor />);
  expect(screen.getByText('Workflow Editor')).toBeInTheDocument();
});
```

**Backend**: Pytest with async support:
```python
@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    response = await client.post("/api/files/projects", json={"name": "test"})
    assert response.status_code == 201
```

### Key Files & Directories

**Reference Implementations**:
- `src/frontend/components/no-code/nodes/TechnicalIndicatorNode.tsx`: Multi-output node pattern
- `src/frontend/lib/api/file-management-api.ts`: Service-specific API client
- `src/backend/ai-ml-strategy-service/app/api/endpoints/files.py`: FastAPI endpoint structure
- `src/frontend/lib/connection-manager.ts`: Node connection rules
- `docker-compose.yml`: Service orchestration
- `Makefile`: Deployment automation

**Configuration**:
- `src/frontend/.env.local`: Frontend environment variables
- `src/backend/*/requirements.txt`: Python dependencies
- `src/frontend/package.json`: Node.js dependencies
- `infra/kubernetes/`: Production deployments

### Common Pitfalls

1. **Missing Dependencies**: Always check `requirements.txt` when adding Python packages
2. **Port Conflicts**: Each service runs on different ports (8001-8007)
3. **Environment Variables**: Frontend needs `NEXT_PUBLIC_` prefix for client-side access
4. **Node Registration**: New React Flow nodes must be registered in `nodeTypes`
5. **Connection Rules**: Multi-output nodes need rules for each handle
6. **API Timeouts**: File operations use 60s timeout, others use 30s
7. **Database URLs**: Use service names in Docker (`postgres:5432`) vs localhost for development

### Performance Considerations

- **API Retries**: BaseApiClient automatically retries network failures
- **Database Pooling**: Use connection pooling for all database operations
- **Redis Caching**: Cache frequently accessed data with TTL
- **File Operations**: Use async file operations for large files
- **WebSocket**: Use for real-time data, REST for CRUD operations</content>
<parameter name="filePath">/Users/usubithan/Documents/Alphintra/.github/copilot-instructions.md
