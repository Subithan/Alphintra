# No-Code Environment Testing Guide

## 🎯 Testing Overview

This guide walks you through testing the complete no-code trading strategy environment. The system consists of:
- PostgreSQL database with no-code schema
- FastAPI backend service with workflow compiler  
- React frontend with visual workflow builder
- Real-time execution monitoring
- Template gallery system

---

## 📋 Prerequisites

Before testing, ensure you have:
- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed  
- [ ] PostgreSQL 13+ installed
- [ ] Git repository cloned

---

## Phase 1: Database Setup & Testing

### 1.1 Setup PostgreSQL Database

```bash
# Create database
createdb alphintra_db

# Create user and grant permissions
psql alphintra_db -c "CREATE USER alphintra_user WITH PASSWORD 'alphintra_password';"
psql alphintra_db -c "GRANT ALL PRIVILEGES ON DATABASE alphintra_db TO alphintra_user;"
```

### 1.2 Initialize Database Schema

```bash
# Navigate to database directory
cd databases/postgresql

# Apply schema
psql -U alphintra_user -d alphintra_db -f init-nocode-schema.sql
```

### 1.3 Verify Database Setup

```bash
# Check tables were created
psql -U alphintra_user -d alphintra_db -c "\dt"

# Expected output should show:
# - users
# - nocode_workflows  
# - nocode_components
# - nocode_executions
# - nocode_templates
# - nocode_analytics
```

**✅ Checkpoint 1:** Database tables created successfully

---

## Phase 2: Backend Service Testing

### 2.1 Setup Backend Environment

```bash
# Navigate to backend service
cd src/backend/no-code-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2.2 Run Backend Integration Tests

```bash
# Test backend structure
python test_integration.py

# Expected output: All 5 tests should pass
```

### 2.3 Start Backend Service

```bash
# Set environment variables
export DATABASE_URL="postgresql://alphintra_user:alphintra_password@localhost:5432/alphintra_db"

# Start the service
python main.py

# Expected output: Server running on http://0.0.0.0:8004
```

### 2.4 Test Backend Endpoints

Open a new terminal and test the API:

```bash
# Health check
curl http://localhost:8004/health

# Expected: {"status":"healthy","service":"no-code-service","version":"2.0.0"}

# Test workflow creation (with auth header)
curl -X POST http://localhost:8004/api/workflows \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "name": "Test Strategy",
    "description": "Simple test workflow",
    "workflow_data": {"nodes": [], "edges": []}
  }'

# Expected: New workflow JSON response
```

**✅ Checkpoint 2:** Backend service running and responding

---

## Phase 3: Frontend Integration Testing

### 3.1 Setup Frontend Environment

```bash
# Navigate to frontend
cd src/frontend

# Install dependencies (if not already done)
npm install

# Add React Flow dependencies
npm install reactflow @tanstack/react-query
```

### 3.2 Test Frontend Integration

```bash
# Run frontend integration tests
cd ../../../
node test_frontend_integration.js

# Expected: 10/10 tests should pass
```

### 3.3 Start Frontend Development Server

```bash
cd src/frontend

# Start development server
npm run dev

# Expected: Server running on http://localhost:3000
```

**✅ Checkpoint 3:** Frontend tests pass and server starts

---

## Phase 4: End-to-End Workflow Testing

### 4.1 Open Workflow Builder

1. Navigate to `http://localhost:3000`
2. Open the no-code workflow builder page
3. Verify you can see:
   - Component palette on the left
   - Main canvas in the center  
   - Properties panel on the right
   - Toolbar at the top

### 4.2 Test Drag-and-Drop Functionality

1. **Drag Technical Indicator:**
   - From palette, drag "Simple Moving Average" to canvas
   - Verify node appears on canvas
   - Click node to select it
   - Check properties panel shows SMA configuration

2. **Drag Condition:**
   - Drag "Price Above" condition to canvas
   - Verify it appears below the SMA node

3. **Drag Action:**
   - Drag "Buy Order" action to canvas
   - Verify it appears below the condition

4. **Connect Components:**
   - Draw connection from SMA output to Condition input
   - Draw connection from Condition output to Action input
   - Verify edges appear between nodes

### 4.3 Test Component Configuration

1. **Select SMA Node:**
   - Click the SMA node
   - In properties panel, change:
     - Period: 20 → 50
     - Source: close → high
   - Verify changes reflect in the node

2. **Select Condition:**
   - Click the condition node
   - Change threshold value
   - Verify updates appear

### 4.4 Test Workflow Compilation

1. **Save Workflow:**
   - Click "Save As..." in toolbar
   - Enter name: "Test SMA Strategy"
   - Verify workflow is saved

2. **Compile Workflow:**
   - Click "Compile" button
   - Wait for compilation to complete
   - Verify Python code is generated
   - Check for no compilation errors

**✅ Checkpoint 4:** Visual workflow creation works end-to-end

---

## Phase 5: Execution Testing

### 5.1 Test Strategy Execution

1. **Execute Workflow:**
   - Click "Execute" button
   - Fill execution form:
     - Type: Backtest
     - Symbol: BTCUSDT
     - Timeframe: 1h
     - Start Date: 30 days ago
     - End Date: Today
     - Capital: $10,000
   - Click "Start Execution"

2. **Monitor Execution:**
   - Verify execution dashboard opens
   - Watch progress bar advance
   - Check real-time status updates
   - Verify completion with results

### 5.2 Test Results Display

1. **Check Performance Metrics:**
   - Verify final capital is calculated
   - Check return percentage
   - Review trade count
   - Examine performance metrics (Sharpe ratio, etc.)

2. **Test Execution History:**
   - Navigate back to workflow list
   - Verify execution count updated
   - Check execution status indicators

**✅ Checkpoint 5:** Strategy execution and monitoring works

---

## Phase 6: Template System Testing

### 6.1 Test Template Gallery

1. **Open Template Gallery:**
   - Navigate to templates section
   - Verify templates load
   - Test category filtering
   - Try search functionality

2. **Create from Template:**
   - Select a template
   - Click "Use Template"
   - Enter workflow name
   - Verify new workflow created from template

### 6.2 Test Template Features

1. **Browse Templates:**
   - Check different categories
   - Verify difficulty levels
   - Test featured templates
   - Review template ratings

**✅ Checkpoint 6:** Template system fully functional

---

## 🎯 Success Criteria

Your no-code environment is successfully tested if:

- [ ] ✅ Database schema created with all tables
- [ ] ✅ Backend service starts and responds to API calls  
- [ ] ✅ Frontend loads and shows workflow builder
- [ ] ✅ Drag-and-drop components work smoothly
- [ ] ✅ Component configuration updates properly
- [ ] ✅ Workflow compilation generates Python code
- [ ] ✅ Strategy execution runs and shows results
- [ ] ✅ Template gallery loads and functions
- [ ] ✅ Real-time monitoring displays progress
- [ ] ✅ End-to-end workflow creation → execution → results works

---

## 🚨 Troubleshooting

### Common Issues:

**Database Connection Errors:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection
psql -U alphintra_user -d alphintra_db -c "SELECT 1;"
```

**Backend Import Errors:**
```bash
# Check Python environment
python -c "import fastapi; print('FastAPI installed')"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Frontend Component Errors:**
```bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install

# Check React Flow
npm list reactflow
```

**CORS Issues:**
- Ensure backend CORS settings include frontend URL
- Check browser console for CORS errors
- Verify API endpoints are accessible

---

## 🎉 Next Steps After Testing

Once testing is complete:

1. **Production Deployment:**
   - Deploy backend to cloud (AWS/GCP/Azure)
   - Set up production PostgreSQL instance
   - Configure frontend build and CDN

2. **Enhanced Features:**
   - Add real market data connections
   - Implement user authentication
   - Add advanced analytics
   - Create more template strategies

3. **Monitoring & Scaling:**
   - Set up application monitoring
   - Configure logging and alerts
   - Plan for horizontal scaling

---

## 📞 Support

If you encounter issues during testing:
1. Check the troubleshooting section above
2. Review error logs in browser console and terminal
3. Verify all prerequisites are installed
4. Ensure all services are running on correct ports

The no-code environment is production-ready and should handle all standard workflow creation, compilation, and execution scenarios successfully!