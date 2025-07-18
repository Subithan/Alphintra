# Code Validation Service - Quick Start Guide

## 🔧 VS Code Setup

### 1. Install Required Extensions
Run this command in VS Code terminal:
```bash
code --install-extension vscjava.vscode-java-pack
code --install-extension vmware.vscode-spring-boot
code --install-extension pivotal.vscode-boot-dev-pack
```

### 2. Fix Java Path Issues
If you see red underlines in Java files:

1. **Press** `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. **Type**: "Java: Reload Projects"
3. **Select** it and wait for reload
4. **If still red**, try "Java: Restart Language Server"

### 3. Configure Java Home
Add this to your VS Code settings.json:
```json
{
    "java.home": "/opt/homebrew/Cellar/openjdk/23.0.2/libexec/openjdk.jdk/Contents/Home",
    "java.configuration.updateBuildConfiguration": "automatic"
}
```

## 🚀 Running the Service

### Option 1: Using the Run Script
```bash
cd src/backend/code-validation-service
./run_service.sh
```

### Option 2: Using Maven Directly
```bash
cd src/backend/code-validation-service
mvn clean compile
mvn spring-boot:run
```

### Option 3: Using VS Code
1. Open the project in VS Code
2. Press F5 or go to Run > Start Debugging
3. Select "Debug Code Validation Service"

## 🧪 Testing the Service

Once running, test these endpoints:

### Health Check
```bash
curl http://localhost:8005/actuator/health
```

### Code Validation
```bash
curl -X POST http://localhost:8005/api/validation/code/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic YWRtaW46ZGV2MTIz" \
  -d '{
    "code": "def strategy(): return {\"signal\": \"buy\"}",
    "workflowId": "test-123",
    "language": "python"
  }'
```

### Security Scan
```bash
curl -X POST http://localhost:8005/api/validation/security/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic YWRtaW46ZGV2MTIz" \
  -d '{
    "code": "import pandas as pd",
    "workflowId": "test-123",
    "scanLevel": "COMPREHENSIVE"
  }'
```

## 🔑 Authentication

Default credentials:
- **Username**: admin
- **Password**: dev123 (development mode)

Base64 encoded: `YWRtaW46ZGV2MTIz`

## 📊 Service URLs

- **Service**: http://localhost:8005
- **Health**: http://localhost:8005/actuator/health
- **Metrics**: http://localhost:8005/actuator/metrics
- **API Docs**: http://localhost:8005/swagger-ui.html

## 🐛 Troubleshooting

### Java Compilation Errors
1. Ensure Java 17+ is installed
2. Check that JAVA_HOME is set correctly
3. Reload VS Code Java projects
4. Clear Maven cache: `mvn clean`

### Maven Dependency Issues
1. Check internet connection
2. Clear Maven cache: `rm -rf ~/.m2/repository`
3. Re-run: `mvn clean compile`

### VS Code Red Underlines
1. Install Java extensions
2. Restart Language Server
3. Check Java path in settings
4. Reload window: `Cmd+R` (macOS) or `Ctrl+R` (Windows)

## ✅ Success Indicators

✅ Service starts without errors
✅ Health endpoint returns 200 OK
✅ VS Code shows no red underlines
✅ API endpoints respond correctly
✅ Authentication works with test credentials
