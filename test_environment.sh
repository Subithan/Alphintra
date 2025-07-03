#!/bin/bash

# Quick Start Testing Script for No-Code Environment
# This script automates the setup and testing process

set -e  # Exit on any error

echo "🚀 Starting No-Code Environment Testing"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
echo -e "\n${BLUE}📋 Checking Prerequisites...${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python $PYTHON_VERSION found"
else
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js $NODE_VERSION found"
else
    print_error "Node.js not found. Please install Node.js 16+"
    exit 1
fi

# Check PostgreSQL
if command -v psql &> /dev/null; then
    print_status "PostgreSQL found"
else
    print_warning "PostgreSQL not found. You'll need to set up the database manually."
fi

# Test file structure
echo -e "\n${BLUE}📁 Checking File Structure...${NC}"

required_files=(
    "databases/postgresql/init-nocode-schema.sql"
    "src/backend/no-code-service/main.py"
    "src/backend/no-code-service/requirements.txt"
    "src/frontend/lib/api/no-code-api.ts"
    "src/frontend/components/no-code/WorkflowBuilder.tsx"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        print_status "$file exists"
    else
        print_error "$file missing"
        all_files_exist=false
    fi
done

if [[ "$all_files_exist" = false ]]; then
    print_error "Some required files are missing. Please ensure all components are installed."
    exit 1
fi

# Run system tests
echo -e "\n${BLUE}🧪 Running System Tests...${NC}"

# Backend tests
print_info "Testing backend structure..."
cd src/backend/no-code-service
if python3 test_integration.py; then
    print_status "Backend structure tests passed"
else
    print_error "Backend structure tests failed"
    exit 1
fi
cd ../../..

# Frontend tests  
print_info "Testing frontend integration..."
if node test_frontend_integration.js; then
    print_status "Frontend integration tests passed"
else
    print_error "Frontend integration tests failed"
    exit 1
fi

# Complete system test
print_info "Testing complete system integration..."
if node test_complete_no_code_system.js; then
    print_status "Complete system tests passed"
else
    print_error "Complete system tests failed"
    exit 1
fi

# Database setup instructions
echo -e "\n${BLUE}🗄️  Database Setup Instructions${NC}"
echo "To complete the testing setup, run these commands:"
echo ""
echo "1. Create PostgreSQL database:"
echo "   createdb alphintra_db"
echo ""
echo "2. Create user:"
echo "   psql alphintra_db -c \"CREATE USER alphintra_user WITH PASSWORD 'alphintra_password';\""
echo "   psql alphintra_db -c \"GRANT ALL PRIVILEGES ON DATABASE alphintra_db TO alphintra_user;\""
echo ""
echo "3. Initialize schema:"
echo "   psql -U alphintra_user -d alphintra_db -f databases/postgresql/init-nocode-schema.sql"

# Backend setup instructions
echo -e "\n${BLUE}🔧 Backend Setup Instructions${NC}"
echo "To start the backend service:"
echo ""
echo "1. Navigate to backend directory:"
echo "   cd src/backend/no-code-service"
echo ""
echo "2. Create virtual environment:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
echo ""
echo "3. Install dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "4. Set environment variable:"
echo "   export DATABASE_URL=\"postgresql://alphintra_user:alphintra_password@localhost:5432/alphintra_db\""
echo ""
echo "5. Start service:"
echo "   python main.py"
echo ""
echo "   Service will run on: http://localhost:8004"

# Frontend setup instructions
echo -e "\n${BLUE}🌐 Frontend Setup Instructions${NC}"
echo "To start the frontend:"
echo ""
echo "1. Navigate to frontend directory:"
echo "   cd src/frontend"
echo ""
echo "2. Install dependencies (if not done):"
echo "   npm install"
echo ""
echo "3. Install additional React Flow dependencies:"
echo "   npm install reactflow @tanstack/react-query"
echo ""
echo "4. Start development server:"
echo "   npm run dev"
echo ""
echo "   Frontend will run on: http://localhost:3000"

# Testing instructions
echo -e "\n${BLUE}🧪 Manual Testing Instructions${NC}"
echo "Follow the comprehensive testing guide:"
echo ""
echo "1. Open TESTING_GUIDE.md for detailed step-by-step instructions"
echo "2. Test each phase: Database → Backend → Frontend → E2E → Templates"
echo "3. Verify all checkpoints pass"
echo ""

# Summary
echo -e "\n${GREEN}🎉 Environment Testing Setup Complete!${NC}"
echo ""
echo "Summary of what's ready:"
echo "✅ All system components verified"
echo "✅ File structure validated"  
echo "✅ Integration tests passed"
echo "✅ Setup instructions provided"
echo ""
echo "Next steps:"
echo "1. Set up PostgreSQL database (see instructions above)"
echo "2. Start backend service (see instructions above)"
echo "3. Start frontend development server"
echo "4. Follow TESTING_GUIDE.md for complete validation"
echo ""
echo "🚀 Your no-code trading strategy environment is ready for testing!"