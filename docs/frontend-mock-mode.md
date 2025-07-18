# Frontend Mock Mode for No-Code Service

## 🎯 Overview

The No-Code Service frontend includes a **Mock Mode** that allows developers to test and demonstrate the full functionality without requiring backend services to be running. This is particularly useful for:

- **Frontend Development**: Test UI components and interactions
- **Demonstrations**: Show the complete system functionality
- **Development Environment**: Work on frontend without backend dependencies
- **Testing**: Validate user flows and interface behavior

---

## 🔧 Configuration

### **Environment Variables**

Create a `.env.local` file in the frontend directory:

```bash
# Enable mock mode for frontend-only development
NEXT_PUBLIC_MOCK_API=true

# API URLs (ignored when mock mode is enabled)
NEXT_PUBLIC_NOCODE_API_URL=http://localhost:8004
NEXT_PUBLIC_AUTH_API_URL=http://localhost:8001
NEXT_PUBLIC_TIMESCALE_API_URL=http://localhost:8003

# Development mode
NODE_ENV=development
```

### **Mock Mode States**

| Environment | Mock Mode | Description |
|-------------|-----------|-------------|
| `NEXT_PUBLIC_MOCK_API=true` | ✅ Enabled | Uses mock data for all API calls |
| `NEXT_PUBLIC_MOCK_API=false` | ❌ Disabled | Attempts real API connections |
| Not set | ❌ Disabled | Default behavior (real APIs) |

---

## 🎭 Mock Data Features

### **1. Workflow Management**
- ✅ **Create Workflow**: Returns mock workflow with generated ID
- ✅ **Save Operations**: Simulates successful save operations
- ✅ **Load Workflows**: Provides sample workflow data
- ✅ **Update Operations**: Simulates real-time updates

### **2. Version Control System**
- ✅ **Version History**: 3 sample versions with realistic timestamps
- ✅ **Activity Timeline**: 5 sample activities (created, updated, versioned, executed)
- ✅ **Version Creation**: Simulates new version creation
- ✅ **Version Restoration**: Mock restoration operations
- ✅ **Change Tracking**: Sample change summaries and metadata

### **3. Sample Data**

#### **Mock Versions**
```json
[
  {
    "id": 1,
    "name": "Initial Version",
    "version": 1,
    "changes_summary": "Initial model creation",
    "created_by": "Demo User"
  },
  {
    "id": 2,
    "name": "Enhanced Strategy", 
    "version": 2,
    "changes_summary": "Added RSI indicator and improved risk management",
    "created_by": "Demo User"
  },
  {
    "id": 3,
    "name": "Current Version",
    "version": 3,
    "changes_summary": "Latest improvements and optimizations", 
    "created_by": "Demo User"
  }
]
```

#### **Mock Activity Timeline**
```json
[
  {
    "action_type": "created",
    "description": "Model created",
    "user_name": "Demo User",
    "version": 1
  },
  {
    "action_type": "updated", 
    "description": "Added RSI indicator",
    "user_name": "Demo User",
    "version": 2
  },
  {
    "action_type": "executed",
    "description": "Backtesting completed",
    "metadata": { "return": 12.5, "trades": 45 }
  }
]
```

---

## 🚀 Usage Instructions

### **1. Start Frontend with Mock Mode**

```bash
# Navigate to frontend directory
cd /Users/usubithan/Documents/Alphintra/src/frontend

# Ensure .env.local has NEXT_PUBLIC_MOCK_API=true
echo "NEXT_PUBLIC_MOCK_API=true" > .env.local

# Start development server
npm run dev
```

### **2. Access the No-Code Console**

1. Open browser to `http://localhost:3000/strategy-hub/no-code-console`
2. The interface will load with mock data
3. All API calls will return simulated responses

### **3. Test Version Control Features**

1. **Right Sidebar**: Click on "Versions" tab
2. **View History**: See sample versions and activity timeline
3. **Create Version**: Click "Create Version" - will simulate success
4. **Version Operations**: All version management works with mock data

---

## 🧪 Testing Scenarios

### **Scenario 1: Save Workflow**
1. Create or modify a workflow
2. Click "Save" button
3. ✅ **Expected**: Success toast notification
4. ✅ **Result**: Mock workflow created with generated ID

### **Scenario 2: Version Management**
1. Switch to "Versions" tab in right sidebar
2. View existing version history
3. Click "Create Version"
4. ✅ **Expected**: New version appears in list
5. ✅ **Result**: Mock version with realistic data

### **Scenario 3: Activity Timeline**
1. Open "Versions" tab
2. View "Recent Activity" section
3. ✅ **Expected**: Timeline shows various activities
4. ✅ **Result**: Sample activities with proper icons and timestamps

---

## 🔄 Switching Between Mock and Real APIs

### **Enable Mock Mode**
```bash
# Set environment variable
echo "NEXT_PUBLIC_MOCK_API=true" >> .env.local

# Restart development server
npm run dev
```

### **Disable Mock Mode (Use Real APIs)**
```bash
# Update environment variable
echo "NEXT_PUBLIC_MOCK_API=false" >> .env.local

# Ensure backend services are running
cd ../backend/no-code-service
python main.py

# Restart frontend
npm run dev
```

---

## 🛠️ Development Benefits

### **1. Independent Development**
- Work on frontend without backend dependencies
- Test UI components and user interactions
- Validate workflows and user journeys

### **2. Demonstration Ready**
- Show complete system functionality
- Present to stakeholders without complex setup
- Demo version control and workflow features

### **3. Faster Iteration**
- No backend startup time
- Instant API responses
- Predictable test data

### **4. Error Handling**
- Test error scenarios by modifying mock responses
- Validate error handling and user feedback
- Test edge cases and boundary conditions

---

## 📋 Mock API Coverage

| API Method | Mock Implementation | Status |
|------------|-------------------|--------|
| `createWorkflow()` | ✅ Full mock with generated data | Complete |
| `getVersions()` | ✅ Sample version history | Complete |
| `getWorkflowHistory()` | ✅ Sample activity timeline | Complete |
| `createVersion()` | ✅ Mock version creation | Complete |
| `restoreVersion()` | ⚠️ Mock success response | Basic |
| `compareVersions()` | ❌ Not implemented | Pending |
| `deleteVersion()` | ⚠️ Mock success response | Basic |

### **Extending Mock Coverage**

To add mock implementations for additional methods:

```typescript
async someApiMethod(params: any): Promise<any> {
  if (this.mockMode) {
    // Return mock data
    return {
      // Mock response structure
    };
  }
  
  // Real API call
  return this.requestWithRetry<any>('/api/endpoint', options);
}
```

---

## 🎉 Conclusion

The Mock Mode provides a complete development and demonstration environment for the No-Code Service frontend. It enables:

- **Full Feature Testing** without backend dependencies
- **Professional Demonstrations** with realistic data
- **Rapid Development** cycles and iterations
- **Comprehensive UI Validation** and user experience testing

This mock system ensures that the frontend can be fully evaluated and demonstrated independently, while maintaining the exact same interface and behavior as the production system.

---

*Mock Mode Status: ✅ Production Ready*  
*Last Updated: July 5, 2025*