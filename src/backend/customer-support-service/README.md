# Customer Support Service

A comprehensive customer support system for the Alphintra trading platform, providing ticketing, user assistance, knowledge base management, and AI-powered support tools.

## Features

### Core Functionality
- **Smart Ticket Management**: Automated ticket routing, priority determination, and agent assignment
- **Multi-channel Communication**: Support for chat, email, phone, and video calls
- **Escalation Management**: Automatic and manual ticket escalation based on SLA and complexity
- **Knowledge Base**: Searchable articles with auto-learning capabilities
- **AI Assistant**: Intelligent response suggestions and sentiment analysis
- **Real-time Collaboration**: WebSocket-based real-time updates and agent collaboration

### Security & Privacy
- **Role-based Access Control**: L1-L4 agent levels with appropriate permissions
- **Data Masking**: Automatic PII masking based on agent access level
- **Consent Management**: User consent tracking for sensitive data access
- **Audit Logging**: Comprehensive audit trail for compliance

### Analytics & Reporting
- **Performance Metrics**: Agent performance tracking and SLA monitoring
- **Customer Satisfaction**: Rating system and feedback collection
- **Reporting Dashboard**: Real-time analytics and trend analysis

## Quick Start

### Prerequisites
- Java 17+
- Maven 3.8+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Local Development

1. **Clone and navigate to the service directory:**
   ```bash
   cd src/backend/customer-support-service
   ```

2. **Set up the database:**
   ```sql
   CREATE DATABASE alphintra_support;
   CREATE USER support_user WITH PASSWORD 'support_pass';
   GRANT ALL PRIVILEGES ON DATABASE alphintra_support TO support_user;
   ```

3. **Configure application properties:**
   ```yaml
   # src/main/resources/application-local.yml
   spring:
     datasource:
       url: jdbc:postgresql://localhost:5432/alphintra_support
       username: support_user
       password: support_pass
   ```

4. **Run the application:**
   ```bash
   mvn spring-boot:run -Dspring-boot.run.profiles=local
   ```

5. **Access the service:**
   - API: http://localhost:8085/api/support
   - Swagger UI: http://localhost:8085/api/support/swagger-ui.html
   - Health Check: http://localhost:8085/api/support/actuator/health

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t alphintra/customer-support-service .
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

## API Documentation

### Authentication
All endpoints require authentication except for public endpoints like satisfaction ratings.

```bash
# Get JWT token from auth service
curl -X POST http://localhost:8081/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"agent", "password":"password"}'

# Use token in subsequent requests
curl -X GET http://localhost:8085/api/support/tickets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Core Endpoints

#### Tickets
```bash
# Create a ticket
POST /api/support/tickets
{
  "userId": "uuid",
  "title": "Cannot access trading dashboard",
  "description": "Getting 500 error when trying to login",
  "category": "TECHNICAL",
  "tags": ["login", "error"]
}

# Get tickets (with filtering)
GET /api/support/tickets?status=OPEN&priority=HIGH&page=0&size=20

# Get specific ticket
GET /api/support/tickets/{ticketId}

# Update ticket
PUT /api/support/tickets/{ticketId}
{
  "status": "IN_PROGRESS",
  "priority": "HIGH",
  "assignedAgentId": "agent-001"
}

# Escalate ticket
POST /api/support/tickets/{ticketId}/escalate
{
  "targetLevel": "L3_SPECIALIST",
  "reason": "Requires technical expertise"
}
```

#### Communications
```bash
# Add communication to ticket
POST /api/support/tickets/{ticketId}/communications
{
  "content": "I've looked into your issue...",
  "communicationType": "MESSAGE",
  "isInternal": false
}

# Get ticket communications
GET /api/support/tickets/{ticketId}/communications
```

#### Agent Management
```bash
# Get available agents
GET /api/support/agents

# Update agent status
PUT /api/support/agents/{agentId}/status
{
  "status": "AVAILABLE"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `DB_NAME` | Database name | alphintra_support |
| `DB_USERNAME` | Database username | postgres |
| `DB_PASSWORD` | Database password | - |
| `REDIS_HOST` | Redis host | localhost |
| `REDIS_PORT` | Redis port | 6379 |
| `JWT_ISSUER_URI` | JWT issuer URI | http://localhost:8081/auth |
| `OPENAI_API_KEY` | OpenAI API key for AI features | - |

### Application Properties

```yaml
support:
  ai:
    enabled: true
    openai:
      api-key: ${OPENAI_API_KEY}
      model: gpt-4
      max-tokens: 500
  
  ticket:
    auto-assignment: true
    escalation:
      auto-escalate-after-hours: 24
      max-escalation-level: 3
  
  security:
    data-masking:
      enabled: true
    consent:
      default-duration-hours: 4
      max-duration-hours: 24
```

## Database Schema

The service uses PostgreSQL with the following main tables:

- `support_tickets`: Core ticket information
- `support_agents`: Agent profiles and capabilities
- `communications`: Ticket communications and interactions
- `knowledge_base_articles`: KB articles and documentation
- `audit_logs`: Audit trail for compliance
- `user_consent_records`: User consent tracking

## Testing

### Unit Tests
```bash
# Run unit tests
mvn test

# Run specific test class
mvn test -Dtest=TicketServiceTest

# Run with coverage
mvn test jacoco:report
```

### Integration Tests
```bash
# Run integration tests
mvn verify

# Run with test containers
mvn verify -Dspring.profiles.active=integration-test
```

### API Testing
```bash
# Import Postman collection
curl -o support-api.postman.json \
  http://localhost:8085/api/support/v3/api-docs

# Or use curl scripts
./scripts/test-api.sh
```

## Monitoring

### Health Checks
- **Application Health**: `/actuator/health`
- **Database Health**: `/actuator/health/db`
- **Redis Health**: `/actuator/health/redis`

### Metrics
- **Prometheus**: `/actuator/prometheus`
- **Custom Metrics**: Ticket creation rate, resolution time, agent performance

### Logging
```yaml
logging:
  level:
    com.alphintra.customersupport: INFO
    org.springframework.security: WARN
  pattern:
    file: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
```

## Security

### Access Control
- **L1 Agents**: Basic ticket access, limited user data
- **L2 Agents**: Extended access, technical tickets
- **L3 Specialists**: Full access, complex issues
- **L4 Managers**: Administrative access, all features

### Data Protection
- **Encryption**: All sensitive data encrypted at rest and in transit
- **Masking**: PII automatically masked based on access level
- **Consent**: User consent required for detailed data access
- **Audit**: All data access logged and monitored

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database connectivity
   pg_isready -h localhost -p 5432
   
   # Check user permissions
   psql -h localhost -U support_user -d alphintra_support -c "\dt"
   ```

2. **Redis Connection Issues**
   ```bash
   # Check Redis connectivity
   redis-cli ping
   
   # Check Redis logs
   redis-cli monitor
   ```

3. **Authentication Issues**
   ```bash
   # Verify JWT token
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8085/api/support/actuator/health
   ```

### Debug Mode
```bash
# Enable debug logging
export LOGGING_LEVEL_COM_ALPHINTRA_CUSTOMERSUPPORT=DEBUG

# Run with debug profile
mvn spring-boot:run -Dspring-boot.run.profiles=debug
```

## Development

### Architecture
- **Spring Boot 3.2**: Main framework
- **Spring Security**: Authentication and authorization
- **Spring Data JPA**: Database access
- **Spring WebSocket**: Real-time communication
- **PostgreSQL**: Primary database
- **Redis**: Caching and session management
- **OpenAPI 3**: API documentation

### Code Structure
```
src/main/java/com/alphintra/customersupport/
├── controller/     # REST controllers
├── service/        # Business logic
├── repository/     # Data access
├── entity/         # JPA entities
├── dto/           # Data transfer objects
├── config/        # Configuration classes
├── security/      # Security configuration
└── websocket/     # WebSocket handlers
```

### Contributing
1. Follow Spring Boot coding conventions
2. Write unit tests for all service methods
3. Update API documentation for new endpoints
4. Use meaningful commit messages
5. Follow the existing code structure

## License

Copyright (c) 2024 Alphintra. All rights reserved.