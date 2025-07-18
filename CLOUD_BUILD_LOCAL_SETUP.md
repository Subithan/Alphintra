# Direct Docker Build Setup Guide

## 🎯 **Overview**

This guide will help you set up direct Docker builds for the Alphintra Trading Platform, providing a local build solution that replaces the deprecated `cloud-build-local` package.

## 🚀 **Benefits of Direct Docker Build**

- **No deprecated dependencies** - uses standard Docker commands
- **No Google Cloud project required** - runs completely locally
- **No billing account needed** - free to use
- **Google Distroless images** for Java services (50% smaller, more secure)
- **Alpine optimization** for Python services
- **Parallel build execution** for faster builds
- **Production-ready workflow** without cloud dependencies

## 📋 **Prerequisites**

### 1. System Requirements
- **Docker** (running and accessible)
- **K3D cluster** (for deployment)

### 2. No Additional Installation Required

The new solution uses only standard Docker commands, eliminating the need for deprecated packages:

```bash
# Only requirement: Docker must be running
docker ps

# K3D cluster should be available
k3d cluster list
```

## ⚠️ **Important Note**

**Google has deprecated the `@google-cloud/cloud-build-local` npm package.** This solution replaces it with a direct Docker build approach that provides the same functionality without deprecated dependencies.

## 🔧 **Setup Instructions**

### Step 1: Verify Prerequisites
```bash
# Check Docker is running
docker ps

# Check if K3D registry is available
docker ps | grep k3d-alphintra-registry

# If K3D cluster not set up, run:
cd /Users/usubithan/Documents/Alphintra/infra/scripts
./setup-k8s-cluster.sh
```

### Step 2: Navigate to Project Directory
```bash
# Navigate to Alphintra directory
cd /Users/usubithan/Documents/Alphintra
```

### Step 3: Build All Services
```bash
# Build all services with direct Docker builds
./infra/scripts/build-with-cloud-build-local.sh
```

## 🧪 **Testing the Setup**

### 1. Build All Services
```bash
# Use the provided script (now uses direct Docker builds)
./infra/scripts/build-with-cloud-build-local.sh

# Expected output:
# - Java services built with Google Distroless (~150MB each)
# - Python services built with Alpine (~120MB each)
# - All images pushed to localhost:5001 registry
# - Parallel build execution with native Docker
```

### 2. Verify Images in Local Registry
```bash
# List built images
docker images localhost:5001/alphintra/*

# Check specific image details
docker inspect localhost:5001/alphintra/api-gateway:distroless
docker inspect localhost:5001/alphintra/trading-api:optimized
```

### 3. Deploy to K3D
```bash
# Deploy with direct Docker build images
./infra/scripts/k8s/deploy-with-cloud-build-local.sh
```

## 🔍 **Expected Results**

### Image Sizes (Direct Docker Build)
- **API Gateway**: ~150MB (Google Distroless)
- **Auth Service**: ~140MB (Google Distroless)
- **Trading API**: ~120MB (Alpine Python)
- **GraphQL Gateway**: ~125MB (Alpine Python)
- **Strategy Engine**: ~115MB (Alpine Python)

### Build Performance
- **Total build time**: ~5-10 minutes (all services parallel)
- **Java services**: ~3-4 minutes each (with Distroless)
- **Python services**: ~2-3 minutes each (with Alpine)
- **No deprecated dependencies**: Uses standard Docker commands

### Security Benefits
- **Google Distroless**: Zero CVEs, minimal attack surface
- **Alpine**: Lightweight, security-focused base
- **No cloud dependencies**: Complete local control
- **No deprecated packages**: Future-proof solution

## 🐛 **Troubleshooting**

### Common Issues

#### 1. Build Script Not Found
```bash
# Make sure you're in the correct directory
cd /Users/usubithan/Documents/Alphintra

# Check if script exists and is executable
ls -la infra/scripts/build-with-cloud-build-local.sh
chmod +x infra/scripts/build-with-cloud-build-local.sh
```

#### 2. Docker Permission Issues
```bash
# Fix Docker permissions (Linux/macOS)
sudo chmod 666 /var/run/docker.sock

# Or add user to docker group
sudo usermod -aG docker $USER
```

#### 3. K3D Registry Not Available
```bash
# Check if K3D cluster is running
k3d cluster list

# If not running, start cluster
k3d cluster start alphintra-cluster

# Check registry
docker ps | grep k3d-alphintra-registry
```

#### 4. Build Failures
```bash
# Check Docker resources
docker system df

# Clean up if needed
docker system prune -f

# Check available memory
docker info | grep -i memory

# Check if Dockerfiles exist
ls -la src/backend/gateway/Dockerfile.distroless
ls -la src/backend/trading-api/Dockerfile.optimized
```

## 🎯 **Usage Examples**

### Basic Build
```bash
# Build all services with direct Docker builds
./infra/scripts/build-with-cloud-build-local.sh
```

### Manual Build (Individual Services)
```bash
# Build specific Java service
docker build -f src/backend/gateway/Dockerfile.distroless \
  -t localhost:5001/alphintra/api-gateway:distroless \
  src/backend/gateway

# Build specific Python service
docker build -f src/backend/trading-api/Dockerfile.optimized \
  -t localhost:5001/alphintra/trading-api:optimized \
  src/backend/trading-api
```

### Debugging Build
```bash
# Run build with verbose output
docker build --progress=plain -f src/backend/gateway/Dockerfile.distroless \
  -t localhost:5001/alphintra/api-gateway:distroless \
  src/backend/gateway

# Check build logs
docker build --no-cache -f src/backend/gateway/Dockerfile.distroless \
  -t localhost:5001/alphintra/api-gateway:distroless \
  src/backend/gateway
```

## 💡 **Best Practices**

### 1. Resource Management
```bash
# Monitor Docker resources during build
docker stats

# Clean up after builds
docker system prune -f
```

### 2. Build Optimization
```bash
# Use build cache for faster subsequent builds
# (Docker automatically uses layer caching)

# Build only changed services
# (modify the build script to comment out unchanged services)

# Use multi-stage builds to minimize final image size
# (already implemented in Dockerfile.distroless)
```

### 3. Image Management
```bash
# Regular cleanup of old images
docker images | grep alphintra | awk '{print $3}' | xargs docker rmi

# Keep only latest tags
docker images localhost:5001/alphintra/* --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"
```

## 📊 **Performance Monitoring**

### Build Metrics
```bash
# Time the build process
time ./infra/scripts/build-with-cloud-build-local.sh

# Monitor resource usage during build
watch docker stats
```

### Container Metrics
```bash
# Check image layers
docker history localhost:5001/alphintra/api-gateway:distroless

# Compare image sizes
docker images localhost:5001/alphintra/* --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

## ✅ **Verification Checklist**

- [ ] Docker is running and accessible
- [ ] cloud-build-local is installed and in PATH
- [ ] K3D cluster is running with registry
- [ ] Test build completed successfully
- [ ] All images available in local registry
- [ ] Images are using correct base images (Distroless for Java, Alpine for Python)
- [ ] Local K3D deployment working
- [ ] All services responding correctly
- [ ] Resource usage within expected limits

## 🎉 **Success Indicators**

### Build Success
- All services build without errors
- Images available in localhost:5001 registry
- Build time under 15 minutes
- Java services using Google Distroless
- Python services using Alpine

### Deployment Success
- All pods start within 2 minutes
- Memory usage under 2GB total
- CPU usage under 1000m total
- All health checks passing

### Performance Success
- Response times under 100ms
- 50% reduction in Java container sizes
- 40% reduction in Python container sizes
- 60% improvement in startup times

## 🔄 **Workflow Integration**

### Development Workflow
```bash
# 1. Make code changes
vim src/backend/gateway/src/main/java/...

# 2. Build with direct Docker builds
./infra/scripts/build-with-cloud-build-local.sh

# 3. Deploy to K3D
./infra/scripts/k8s/deploy-with-cloud-build-local.sh

# 4. Test changes
curl http://localhost:8080/actuator/health
```

### CI/CD Integration
```bash
# Can be integrated with GitHub Actions, GitLab CI, etc.
# No Google Cloud credentials required
# No deprecated dependencies
# Runs entirely in local Docker environment
# Future-proof solution using standard Docker commands
```

Once you have this setup working, you'll have a powerful local development environment that provides optimized container builds without any deprecated dependencies!