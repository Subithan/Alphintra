#!/usr/bin/env python3
"""
Test script to verify the Java code structure of the code-validation-service
"""

import os
import re
from pathlib import Path

def test_java_structure():
    """Test the Java project structure"""
    service_path = Path("/Users/usubithan/Documents/Alphintra/src/backend/code-validation-service")
    
    print("🧪 Testing Code Validation Service Structure...")
    
    # Check for required files
    required_files = [
        "pom.xml",
        "Dockerfile",
        "README.md",
        "src/main/java/com/alphintra/validation/CodeValidationApplication.java",
        "src/main/java/com/alphintra/validation/controller/ValidationController.java",
        "src/main/java/com/alphintra/validation/service/CodeValidationService.java",
        "src/main/java/com/alphintra/validation/service/SecurityScanService.java",
        "src/main/java/com/alphintra/validation/service/PerformanceTestService.java",
        "src/main/java/com/alphintra/validation/dto/ValidationResponse.java",
        "src/main/java/com/alphintra/validation/config/SecurityConfig.java",
        "src/main/resources/application.properties"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = service_path / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    # Check Java class structure
    print("\n🔍 Checking Java class structure...")
    
    # Check main application class
    app_file = service_path / "src/main/java/com/alphintra/validation/CodeValidationApplication.java"
    with open(app_file, 'r') as f:
        content = f.read()
        if "@SpringBootApplication" in content and "SpringApplication.run" in content:
            print("✅ Main application class is properly structured")
        else:
            print("❌ Main application class missing Spring Boot annotations")
            return False
    
    # Check controller class
    controller_file = service_path / "src/main/java/com/alphintra/validation/controller/ValidationController.java"
    with open(controller_file, 'r') as f:
        content = f.read()
        required_endpoints = [
            "@PostMapping(\"/code/validate\")",
            "@PostMapping(\"/security/scan\")",
            "@PostMapping(\"/performance/test\")",
            "@PostMapping(\"/model/validate\")",
            "@GetMapping(\"/health\")"
        ]
        
        for endpoint in required_endpoints:
            if endpoint in content:
                print(f"✅ Controller has {endpoint}")
            else:
                print(f"❌ Controller missing {endpoint}")
                return False
    
    # Check service classes
    service_files = [
        ("CodeValidationService", "validatePythonCode"),
        ("SecurityScanService", "performSecurityScan"),
        ("PerformanceTestService", "performPerformanceTest")
    ]
    
    for service_name, method_name in service_files:
        service_file = service_path / f"src/main/java/com/alphintra/validation/service/{service_name}.java"
        with open(service_file, 'r') as f:
            content = f.read()
            if f"@Service" in content and method_name in content:
                print(f"✅ {service_name} is properly structured")
            else:
                print(f"❌ {service_name} missing @Service annotation or {method_name} method")
                return False
    
    # Check DTOs
    dto_file = service_path / "src/main/java/com/alphintra/validation/dto/ValidationResponse.java"
    with open(dto_file, 'r') as f:
        content = f.read()
        required_dtos = [
            "class ValidationResponse",
            "class ValidationIssue", 
            "class SecurityScanResponse",
            "class PerformanceTestResponse",
            "class ModelValidationResponse"
        ]
        
        for dto in required_dtos:
            if dto in content:
                print(f"✅ DTO {dto} exists")
            else:
                print(f"❌ DTO {dto} missing")
                return False
    
    # Check Maven configuration
    pom_file = service_path / "pom.xml"
    with open(pom_file, 'r') as f:
        content = f.read()
        if "spring-boot-starter-web" in content and "lombok" in content:
            print("✅ Maven configuration has required dependencies")
        else:
            print("❌ Maven configuration missing required dependencies")
            return False
    
    # Check application properties
    props_file = service_path / "src/main/resources/application.properties"
    with open(props_file, 'r') as f:
        content = f.read()
        if "server.port=8005" in content and "validation.security" in content:
            print("✅ Application properties properly configured")
        else:
            print("❌ Application properties missing required configuration")
            return False
    
    print("\n🎉 All structure tests passed!")
    return True

def test_api_endpoints():
    """Test API endpoint definitions"""
    print("\n📡 Testing API endpoint definitions...")
    
    controller_file = Path("/Users/usubithan/Documents/Alphintra/src/backend/code-validation-service/src/main/java/com/alphintra/validation/controller/ValidationController.java")
    
    with open(controller_file, 'r') as f:
        content = f.read()
        
        endpoints = [
            ("/api/validation/code/validate", "Post"),
            ("/api/validation/security/scan", "Post"),
            ("/api/validation/performance/test", "Post"),
            ("/api/validation/model/validate", "Post"),
            ("/api/validation/health", "Get")
        ]
        
        for endpoint, method in endpoints:
            endpoint_path = endpoint.split("/api/validation")[1]
            if f'@{method}Mapping("{endpoint_path}")' in content:
                print(f"✅ {method} {endpoint}")
            else:
                print(f"❌ Missing {method} {endpoint}")
                print(f"    Looking for: @{method}Mapping(\"{endpoint_path}\")")
                return False
    
    print("✅ All API endpoints properly defined")
    return True

def test_security_features():
    """Test security scanning features"""
    print("\n🛡️ Testing security scanning features...")
    
    security_service = Path("/Users/usubithan/Documents/Alphintra/src/backend/code-validation-service/src/main/java/com/alphintra/validation/service/SecurityScanService.java")
    
    with open(security_service, 'r') as f:
        content = f.read()
        
        security_patterns = [
            "exec\\\\s*\\\\(",
            "eval\\\\s*\\\\(",
            "subprocess\\\\.",
            "pickle\\\\.load",
            "password\\\\s*=\\\\s*"
        ]
        
        for pattern in security_patterns:
            if pattern in content:
                print(f"✅ Security pattern: {pattern}")
            else:
                print(f"❌ Missing security pattern: {pattern}")
                return False
    
    print("✅ Security scanning features properly implemented")
    return True

def main():
    """Main test execution"""
    print("🚀 Code Validation Service - Structure Test")
    print("=" * 50)
    
    tests = [
        ("Java Structure", test_java_structure),
        ("API Endpoints", test_api_endpoints),
        ("Security Features", test_security_features)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Code Validation Service is properly structured!")
        print("\n📋 Next Steps:")
        print("1. Run 'mvn clean compile' to build the service")
        print("2. Run 'mvn spring-boot:run' to start the service")
        print("3. Test endpoints at http://localhost:8005")
        print("4. View API docs at http://localhost:8005/swagger-ui.html")
        return True
    else:
        print("⚠️ Some tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    main()