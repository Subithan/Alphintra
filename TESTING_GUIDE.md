# Production-Ready K3D Optimization Testing Guide

## 🎯 **Phase 1 & 2 Complete - Ready for Testing**

I've completed the container optimization and resource right-sizing phases. Here's your comprehensive testing guide:

## 📋 **Pre-Testing Setup**

### 1. Clean Environment Setup
```bash
# Remove any existing cluster
k3d cluster delete alphintra-cluster

# Set up optimized cluster
cd /Users/usubithan/Documents/Alphintra/infra/scripts
./setup-k8s-cluster.sh
```

### 2. Build with Direct Docker Build (Recommended)
```bash
# Build all services with direct Docker builds (NO Google Cloud project required)
# Note: Replaces deprecated cloud-build-local package
./scripts/build-with-cloud-build-local.sh

# OR use Google Cloud Build (requires Google Cloud Project)
./scripts/build-with-cloud-build.sh

# OR use pre-built optimized images
./k8s/deploy-optimized.sh
```

### 3. Deploy with Direct Docker Build Images
```bash
# Deploy with direct Docker build images (Recommended)
./k8s/deploy-with-cloud-build-local.sh

# OR deploy with Google Cloud Build images
./k8s/deploy-with-cloud-build.sh
```

## 🧪 **Testing Phases**

### **Phase 1 Testing: Container Optimization Validation**

#### A. Image Size Validation
```bash
# Check optimized image sizes (should be 70% smaller)
docker images localhost:5001/alphintra/*

# Expected results with direct Docker build:
# - API Gateway: ~150MB (Google Distroless)
# - Auth Service: ~140MB (Google Distroless)
# - Trading API: ~120MB (Alpine Python)
# - GraphQL Gateway: ~125MB (Alpine Python)
# - Strategy Engine: ~115MB (Alpine Python)
```

#### B. Container Startup Time
```bash
# Monitor pod startup times
kubectl get pods -n alphintra -w

# Expected results:
# - All pods should start within 60-90 seconds
# - No more than 3 minutes for complete deployment
```

### **Phase 2 Testing: Resource Right-Sizing Validation**

#### A. Memory Usage Check
```bash
# Monitor memory usage (should be <3GB total)
kubectl top pods -n alphintra
kubectl top nodes

# Calculate total memory usage
kubectl top pods -n alphintra --no-headers | awk '{sum += $3} END {print "Total Memory: " sum "Mi"}'

# Expected: <3000Mi total
```

#### B. CPU Usage Check
```bash
# Monitor CPU usage (should be <1500m total)
kubectl top pods -n alphintra --no-headers | awk '{sum += $4} END {print "Total CPU: " sum "m"}'

# Expected: <1500m total
```

## 🔧 **Functionality Testing**

### **API Gateway Testing**
```bash
# Health check
curl http://localhost:8080/actuator/health

# Expected: {"status":"UP",...}
```

### **Trading API Testing**
```bash
# Portfolio endpoint
curl http://localhost:8080/api/trading/portfolio

# Expected: JSON array with portfolio data
```

### **GraphQL Gateway Testing**
```bash
# GraphQL query
curl -X POST http://localhost:8080/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ portfolio { symbol quantity } }"}'

# Expected: JSON response with portfolio data
```

## 📊 **Performance Testing**

### **Load Testing**
```bash
# Install hey (if not already installed)
# brew install hey  # macOS

# Test API Gateway under load
hey -n 1000 -c 10 http://localhost:8080/actuator/health

# Expected:
# - Response time: <200ms average
# - Success rate: >99%
# - No memory spikes above limits
```

## 📋 **Success Criteria**

### **Performance Targets**
- ✅ Total memory usage: <3GB
- ✅ Total CPU usage: <1.5 cores
- ✅ Container image sizes: 70% reduction
- ✅ Startup time: <4 minutes
- ✅ Response time: <200ms average

### **Functionality Targets**
- ✅ All endpoints responding correctly
- ✅ Service-to-service communication working
- ✅ Database connectivity stable
- ✅ Monitoring stack operational

## 📊 **Reporting Results**

After testing, please provide:

1. **Resource Usage Report**
   - Memory usage screenshot
   - CPU usage screenshot
   - Node resource utilization

2. **Performance Results**
   - API response times
   - Load test results
   - Startup time measurements

3. **Functionality Validation**
   - All endpoint test results
   - Service health status
   - Database connectivity

4. **Issues Found**
   - Any errors or warnings
   - Performance bottlenecks
   - Resource limit violations

## 🚀 **Next Steps**

Once Phase 1 & 2 testing is complete and successful, we'll proceed to:
- Phase 3: Istio optimization
- Phase 4: Database optimization
- Phase 5: Final integration testing

This optimized configuration should give you a production-ready platform with significantly reduced resource usage while maintaining all functionality!