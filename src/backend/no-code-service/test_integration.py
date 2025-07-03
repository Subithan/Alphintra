#!/usr/bin/env python3
"""
Simple integration test for the no-code service
This tests the API structure and database schema without requiring external dependencies
"""

import sys
import os
from typing import Dict, Any

def test_api_structure():
    """Test that the API file structure is correct"""
    print("Testing API file structure...")
    
    required_files = [
        'main.py',
        'models.py', 
        'schemas_updated.py',
        'workflow_compiler_updated.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def test_database_schema():
    """Test database schema without connecting to database"""
    print("Testing database schema structure...")
    
    try:
        with open('models.py', 'r') as f:
            models_content = f.read()
        
        required_models = [
            'class User(Base):',
            'class NoCodeWorkflow(Base):',
            'class NoCodeComponent(Base):',
            'class NoCodeExecution(Base):',
            'class NoCodeTemplate(Base):'
        ]
        
        missing_models = []
        for model in required_models:
            if model not in models_content:
                missing_models.append(model)
        
        if missing_models:
            print(f"❌ Missing required models: {missing_models}")
            return False
        
        print("✅ All required database models present")
        return True
        
    except Exception as e:
        print(f"❌ Error reading models file: {e}")
        return False

def test_workflow_compiler():
    """Test workflow compiler structure"""
    print("Testing workflow compiler structure...")
    
    try:
        with open('workflow_compiler_updated.py', 'r') as f:
            compiler_content = f.read()
        
        required_methods = [
            'def compile_workflow(',
            'def _validate_workflow(',
            'def _topological_sort(',
            'def _generate_node_code('
        ]
        
        missing_methods = []
        for method in required_methods:
            if method not in compiler_content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing required compiler methods: {missing_methods}")
            return False
        
        print("✅ Workflow compiler structure is complete")
        return True
        
    except Exception as e:
        print(f"❌ Error reading compiler file: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint structure without running the server"""
    print("Testing API endpoint structure...")
    
    try:
        with open('main.py', 'r') as f:
            main_content = f.read()
        
        required_endpoints = [
            '@app.post("/api/workflows"',
            '@app.get("/api/workflows"',
            '@app.get("/api/workflows/{workflow_id}"',
            '@app.put("/api/workflows/{workflow_id}"',
            '@app.delete("/api/workflows/{workflow_id}"',
            '@app.post("/api/workflows/{workflow_id}/compile"',
            '@app.post("/api/workflows/{workflow_id}/execute"',
            '@app.get("/api/executions/{execution_id}"',
            '@app.get("/api/components"',
            '@app.get("/api/templates"'
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in main_content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Missing required API endpoints: {missing_endpoints}")
            return False
        
        print("✅ All required API endpoints present")
        return True
        
    except Exception as e:
        print(f"❌ Error reading main file: {e}")
        return False

def test_schema_types():
    """Test Pydantic schema types"""
    print("Testing Pydantic schema types...")
    
    try:
        with open('schemas_updated.py', 'r') as f:
            schemas_content = f.read()
        
        required_schemas = [
            'class WorkflowCreate(BaseModel):',
            'class WorkflowResponse(BaseModel):',
            'class ExecutionCreate(BaseModel):',
            'class ExecutionResponse(BaseModel):',
            'class CompilationResponse(BaseModel):',
            'class ComponentResponse(BaseModel):',
            'class TemplateResponse(BaseModel):'
        ]
        
        missing_schemas = []
        for schema in required_schemas:
            if schema not in schemas_content:
                missing_schemas.append(schema)
        
        if missing_schemas:
            print(f"❌ Missing required schemas: {missing_schemas}")
            return False
        
        print("✅ All required Pydantic schemas present")
        return True
        
    except Exception as e:
        print(f"❌ Error reading schemas file: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting No-Code Service Integration Tests\n")
    
    tests = [
        test_api_structure,
        test_database_schema,
        test_workflow_compiler,
        test_api_endpoints,
        test_schema_types
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test failed with exception: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! The no-code service is properly structured.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    success = main()
    sys.exit(0 if success else 1)