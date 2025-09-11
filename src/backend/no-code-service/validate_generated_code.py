#!/usr/bin/env python3
"""
Validate Generated Code Quality
Tests the generated code for syntax errors and basic structure
"""

import ast
import os
import sys


def validate_python_syntax(filename):
    """Validate that the generated Python code has correct syntax."""
    print(f"🔍 Validating {filename}...")
    
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found!")
        return False
    
    try:
        with open(filename, 'r') as f:
            code = f.read()
        
        # Parse the code to check syntax
        tree = ast.parse(code)
        print(f"✅ Syntax is valid!")
        
        # Check for basic structure
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        
        print(f"📊 Code Analysis:")
        print(f"   - Classes: {len(classes)}")
        print(f"   - Functions: {len(functions)}")
        print(f"   - Imports: {len(imports)}")
        print(f"   - Lines: {len(code.splitlines())}")
        
        # Check for main class patterns
        class_names = [cls.name for cls in classes]
        expected_classes = ['StrategyPipeline', 'BacktestingEngine', 'LiveTradingEngine', 'ResearchPipeline']
        found_classes = [cls for cls in expected_classes if cls in class_names]
        
        if found_classes:
            print(f"✅ Found expected classes: {found_classes}")
        else:
            print(f"⚠️  No expected strategy classes found")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax Error: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def validate_all_generated_files():
    """Validate all generated Python files."""
    print("🧪 Validating All Generated Code Files")
    print("=" * 50)
    
    generated_files = []
    
    # Find all generated Python files
    for filename in os.listdir('.'):
        if filename.startswith(('generated_', 'test_', 'simple_')) and filename.endswith('.py'):
            generated_files.append(filename)
    
    if not generated_files:
        print("❌ No generated files found!")
        print("Run the tests first to generate code files.")
        return False
    
    print(f"Found {len(generated_files)} generated files:")
    for f in generated_files:
        print(f"  - {f}")
    
    print("\n" + "=" * 50)
    
    all_valid = True
    for filename in generated_files:
        valid = validate_python_syntax(filename)
        all_valid = all_valid and valid
        print()
    
    print("=" * 50)
    if all_valid:
        print("🎉 All generated files are syntactically valid!")
    else:
        print("❌ Some files have syntax errors!")
    
    return all_valid


def check_code_quality(filename):
    """Check code quality metrics."""
    if not os.path.exists(filename):
        return
    
    with open(filename, 'r') as f:
        code = f.read()
    
    lines = code.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    comment_lines = [line for line in lines if line.strip().startswith('#')]
    docstring_lines = [line for line in lines if '"""' in line or "'''" in line]
    
    print(f"📈 Quality Metrics for {filename}:")
    print(f"   - Total lines: {len(lines)}")
    print(f"   - Code lines: {len(non_empty_lines)}")
    print(f"   - Comment lines: {len(comment_lines)}")
    print(f"   - Documentation: {len(docstring_lines)} docstring markers")
    print(f"   - Comment ratio: {len(comment_lines) / len(non_empty_lines) * 100:.1f}%")


def main():
    """Main validation function."""
    if len(sys.argv) > 1:
        # Validate specific file
        filename = sys.argv[1]
        validate_python_syntax(filename)
        check_code_quality(filename)
    else:
        # Validate all generated files
        validate_all_generated_files()


if __name__ == "__main__":
    main()