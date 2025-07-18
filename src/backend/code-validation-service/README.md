# Alphintra Code Validation Service

A comprehensive microservice for validating, scanning, and performance testing of user-generated code within the Alphintra trading platform.

## Features

### 🔍 Code Validation
- **Syntax Validation**: Python syntax checking and compilation verification
- **Structure Validation**: Ensures required methods and class structure
- **Import Validation**: Checks for required dependencies and imports
- **Performance Hints**: Suggests optimizations for better performance

### 🛡️ Security Scanning
- **Pattern-based Security Analysis**: Detects dangerous operations and vulnerabilities
- **CWE Mapping**: Maps security issues to Common Weakness Enumeration
- **Risk Assessment**: Provides overall risk ratings (LOW, MEDIUM, HIGH, CRITICAL)
- **Remediation Suggestions**: Offers specific guidance for fixing security issues

### ⚡ Performance Testing
- **Static Performance Analysis**: Identifies performance anti-patterns
- **Algorithm Complexity Analysis**: Estimates Big-O complexity
- **Resource Usage Simulation**: Estimates memory and CPU usage
- **Optimization Recommendations**: Suggests specific performance improvements

### 🤖 Model Validation
- **Model File Validation**: Checks trained ML model files
- **Performance Metrics**: Validates model accuracy and performance
- **File Size and Format Validation**: Ensures models meet platform requirements

## API Endpoints

### Code Validation
```http
POST /api/validation/code/validate
Content-Type: application/json

{
  "code": "python code string",
  "workflowId": "workflow-uuid",
  "language": "python",
  "options": {
    "enableSecurityScan": true,
    "enablePerformanceCheck": true,
    "securityLevel": "MODERATE"
  }
}
```

### Security Scanning
```http
POST /api/validation/security/scan
Content-Type: application/json

{
  "code": "python code string",
  "workflowId": "workflow-uuid",
  "scanLevel": "COMPREHENSIVE"
}
```

### Performance Testing
```http
POST /api/validation/performance/test
Content-Type: application/json

{
  "code": "python code string",
  "workflowId": "workflow-uuid",
  "testDurationSeconds": 60,
  "config": {
    "maxMemoryMB": 512,
    "maxExecutionTimeSeconds": 300
  }
}
```

### Model Validation
```http
POST /api/validation/model/validate
Content-Type: application/json

{
  "modelPath": "/path/to/model.pkl",
  "datasetPath": "/path/to/dataset.csv",
  "workflowId": "workflow-uuid",
  "config": {
    "minAccuracy": 0.8,
    "minSharpeRatio": 1.5
  }
}
```

## Security Features

### Detected Vulnerabilities
- **Code Injection**: `exec()`, `eval()` usage
- **Command Injection**: `subprocess`, `os.system()` usage
- **Insecure Deserialization**: `pickle.load()` usage
- **Hardcoded Credentials**: API keys, passwords in code
- **SQL Injection**: Dynamic SQL query construction
- **Path Traversal**: Unsafe file operations
- **External Requests**: Unvalidated HTTP requests

### Risk Levels
- **CRITICAL**: Immediate security threat requiring immediate action
- **HIGH**: Significant security risk that should be addressed soon
- **MEDIUM**: Moderate security concern requiring review
- **LOW**: Minor security consideration for improvement

## Performance Analysis

### Detected Anti-patterns
- **Nested Loops**: O(n²) or higher complexity
- **Inefficient Pandas Operations**: `iterrows()`, `apply(lambda)`
- **String Concatenation**: Inefficient string building in loops
- **Repeated Computations**: Calculations inside loops
- **Inefficient Data Structures**: Wrong choice for use case

### Metrics Provided
- **Execution Time**: Estimated runtime in seconds
- **Memory Usage**: Peak memory consumption in MB
- **CPU Usage**: Processor utilization percentage
- **Operations per Second**: Throughput estimation
- **Complexity Rating**: Big-O notation estimate

## Configuration

### Environment Variables
- `ADMIN_PASSWORD`: Admin user password (default: admin123)
- `PYTHON_SERVICE_URL`: External Python execution service
- `ML_SERVICE_URL`: Machine learning validation service

### Application Properties
```properties
# Performance limits
validation.performance.max-execution-time-seconds=300
validation.performance.max-memory-mb=1024

# Security settings
validation.security.enable-deep-scan=true
validation.security.max-code-size-mb=5

# Code validation
validation.code.python-executable=python3
validation.code.max-lines=10000
```

## Build and Deployment

### Local Development
```bash
# Build the application
mvn clean compile

# Run tests
mvn test

# Start the application
mvn spring-boot:run
```

### Docker Deployment
```bash
# Build Docker image
docker build -t alphintra/code-validation-service:1.0.0 .

# Run container
docker run -p 8005:8005 \
  -e ADMIN_PASSWORD=your-secure-password \
  alphintra/code-validation-service:1.0.0
```

### Production Deployment
```bash
# Build production JAR
mvn clean package -Pprod

# Run with production profile
java -jar target/code-validation-service-1.0.0.jar \
  --spring.profiles.active=production \
  --server.port=8005
```

## Monitoring and Health

### Health Checks
- **Application Health**: `/actuator/health`
- **Service Info**: `/actuator/info`
- **Metrics**: `/actuator/metrics`
- **Prometheus**: `/actuator/prometheus`

### Logging
- **Console Logging**: Structured JSON logs for development
- **File Logging**: Rotating log files for production
- **Security Events**: Detailed security scan logging
- **Performance Metrics**: Execution time and resource usage

## Integration

### With No-Code Service
The code validation service integrates with the no-code workflow builder to:
1. Validate generated Python code before execution
2. Scan for security vulnerabilities in user workflows
3. Provide performance optimization recommendations
4. Ensure code quality and safety standards

### API Client Example
```python
import requests

# Validate code
response = requests.post('http://localhost:8005/api/validation/code/validate', 
    json={
        'code': 'def strategy(): return {"signal": "buy"}',
        'workflowId': 'workflow-123',
        'language': 'python'
    },
    auth=('admin', 'admin123')
)

validation_result = response.json()
print(f"Validation success: {validation_result['success']}")
```

## Testing

### Unit Tests
```bash
mvn test
```

### Integration Tests
```bash
mvn verify
```

### Security Tests
```bash
mvn verify -Psecurity
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   No-Code       │───▶│  Code Validation │───▶│   Security      │
│   Service       │    │     Service      │    │   Scanner       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Performance    │
                       │     Tester       │
                       └──────────────────┘
```

## Contributing

1. Follow Spring Boot best practices
2. Add unit tests for new features
3. Update documentation for API changes
4. Run security scans before committing
5. Use proper error handling and logging

## License

Copyright © 2024 Alphintra. All rights reserved.