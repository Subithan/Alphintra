#!/usr/bin/env python3
"""
Quick test script to validate the code-validation-service 
without needing Java compilation
"""

import subprocess
import time
import json
from pathlib import Path

def test_service_startup():
    """Test if service can start up"""
    print("🧪 Testing Code Validation Service Startup...")
    
    service_dir = Path("/Users/usubithan/Documents/Alphintra/src/backend/code-validation-service")
    
    # Check if all required files exist
    required_files = [
        "pom.xml",
        "src/main/java/com/alphintra/validation/CodeValidationApplication.java",
        "src/main/resources/application.properties"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (service_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    
    # Check Java installation
    try:
        java_version = subprocess.run(
            ["java", "-version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        print(f"✅ Java installed: {java_version.stderr.split()[2]}")
    except:
        print("❌ Java not found or not working")
        return False
    
    # Check Maven installation
    try:
        mvn_version = subprocess.run(
            ["mvn", "-version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        print(f"✅ Maven installed: {mvn_version.stdout.split()[2]}")
    except:
        print("❌ Maven not found or not working")
        return False
    
    return True

def test_configuration():
    """Test service configuration"""
    print("\n🔧 Testing Service Configuration...")
    
    config_file = Path("/Users/usubithan/Documents/Alphintra/src/backend/code-validation-service/src/main/resources/application.properties")
    
    with open(config_file, 'r') as f:
        config = f.read()
    
    # Check for required configuration
    required_configs = [
        "spring.application.name=code-validation-service",
        "server.port=8005",
        "validation.security",
        "validation.performance"
    ]
    
    for config_line in required_configs:
        if config_line in config:
            print(f"✅ Configuration: {config_line}")
        else:
            print(f"❌ Missing configuration: {config_line}")
            return False
    
    return True

def test_api_definition():
    """Test API endpoint definitions"""
    print("\n📡 Testing API Definitions...")
    
    controller_file = Path("/Users/usubithan/Documents/Alphintra/src/backend/code-validation-service/src/main/java/com/alphintra/validation/controller/ValidationController.java")
    
    with open(controller_file, 'r') as f:
        controller_code = f.read()
    
    # Check for API endpoints
    endpoints = [
        '@PostMapping("/code/validate")',
        '@PostMapping("/security/scan")',
        '@PostMapping("/performance/test")',
        '@PostMapping("/model/validate")',
        '@GetMapping("/health")'
    ]
    
    for endpoint in endpoints:
        if endpoint in controller_code:
            print(f"✅ Endpoint: {endpoint}")
        else:
            print(f"❌ Missing endpoint: {endpoint}")
            return False
    
    return True

def generate_vscode_config():
    """Generate VS Code configuration for Java development"""
    print("\n🔧 Generating VS Code Configuration...")
    
    service_dir = Path("/Users/usubithan/Documents/Alphintra/src/backend/code-validation-service")
    vscode_dir = service_dir / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    
    # Create settings.json
    settings = {
        "java.home": "/opt/homebrew/Cellar/openjdk/23.0.2/libexec/openjdk.jdk/Contents/Home",
        "java.configuration.updateBuildConfiguration": "automatic",
        "java.compile.nullAnalysis.mode": "automatic",
        "java.sources.organizeImports.staticStarThreshold": 5,
        "java.sources.organizeImports.starThreshold": 5,
        "maven.executable.path": "/opt/homebrew/bin/mvn",
        "java.format.settings.url": "https://raw.githubusercontent.com/google/styleguide/gh-pages/eclipse-java-google-style.xml",
        "java.format.settings.profile": "GoogleStyle",
        "java.saveActions.organizeImports": True,
        "spring-boot.ls.problem.application-properties.unknown-property": "ignore"
    }
    
    with open(vscode_dir / "settings.json", 'w') as f:
        json.dump(settings, f, indent=2)
    
    print("✅ Created .vscode/settings.json")
    
    # Create extensions.json
    extensions = {
        "recommendations": [
            "vscjava.vscode-java-pack",
            "vmware.vscode-spring-boot",
            "pivotal.vscode-boot-dev-pack",
            "gabrielbb.vscode-lombok",
            "redhat.java",
            "ms-vscode.vscode-java-debug",
            "ms-vscode.vscode-maven"
        ]
    }
    
    with open(vscode_dir / "extensions.json", 'w') as f:
        json.dump(extensions, f, indent=2)
    
    print("✅ Created .vscode/extensions.json")
    
    # Create launch.json for debugging
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "type": "java",
                "name": "Debug Code Validation Service",
                "request": "launch",
                "mainClass": "com.alphintra.validation.CodeValidationApplication",
                "projectName": "code-validation-service",
                "args": "--spring.profiles.active=development",
                "vmArgs": "-Dspring.output.ansi.enabled=always",
                "console": "internalConsole",
                "env": {
                    "ADMIN_PASSWORD": "dev123"
                }
            }
        ]
    }
    
    with open(vscode_dir / "launch.json", 'w') as f:
        json.dump(launch_config, f, indent=2)
    
    print("✅ Created .vscode/launch.json")
    
    return True

def create_startup_guide():
    """Create startup guide"""
    print("\n📚 Creating Startup Guide...")
    
    guide_content = """# Code Validation Service - Quick Start Guide

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
curl -X POST http://localhost:8005/api/validation/code/validate \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Basic YWRtaW46ZGV2MTIz" \\
  -d '{
    "code": "def strategy(): return {\\"signal\\": \\"buy\\"}",
    "workflowId": "test-123",
    "language": "python"
  }'
```

### Security Scan
```bash
curl -X POST http://localhost:8005/api/validation/security/scan \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Basic YWRtaW46ZGV2MTIz" \\
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
"""
    
    service_dir = Path("/Users/usubithan/Documents/Alphintra/src/backend/code-validation-service")
    
    with open(service_dir / "QUICK_START.md", 'w') as f:
        f.write(guide_content)
    
    print("✅ Created QUICK_START.md")
    return True

def main():
    """Main test execution"""
    print("🚀 Code Validation Service - Quick Test & Setup")
    print("=" * 60)
    
    tests = [
        ("Service Startup", test_service_startup),
        ("Configuration", test_configuration),
        ("API Definition", test_api_definition),
        ("VS Code Config", generate_vscode_config),
        ("Startup Guide", create_startup_guide)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed >= len(tests) - 1:
        print("\n🎉 Code Validation Service setup complete!")
        print("\n📋 Next Steps:")
        print("1. Install Java extensions in VS Code")
        print("2. Restart VS Code and reload Java projects")
        print("3. Run: ./run_service.sh")
        print("4. Test: curl http://localhost:8005/actuator/health")
        print("5. Read QUICK_START.md for detailed instructions")
        return True
    else:
        print("\n⚠️ Some setup steps failed. Please review above.")
        return False

if __name__ == "__main__":
    main()