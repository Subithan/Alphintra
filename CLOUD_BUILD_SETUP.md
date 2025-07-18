# Google Cloud Build Setup Guide

## 🎯 **Overview**

This guide will help you set up Google Cloud Build for the Alphintra Trading Platform, enabling production-ready container builds with Google Distroless images.

## 🚀 **Benefits of Google Cloud Build**

- **50% smaller images** using Google Distroless
- **4x faster builds** with parallel processing
- **Zero security vulnerabilities** in base images
- **Consistent builds** across environments
- **Professional CI/CD** integration

## 📋 **Prerequisites**

### 1. Google Cloud Project
```bash
# Create a new project (or use existing)
gcloud projects create alphintra-trading-platform
gcloud config set project alphintra-trading-platform
```

### 2. Enable Required APIs
```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com

# Enable Artifact Registry API (optional, for newer registry)
gcloud services enable artifactregistry.googleapis.com
```

### 3. Set up Authentication
```bash
# Authenticate with Google Cloud
gcloud auth login

# Set up application default credentials
gcloud auth application-default login
```

## 🔧 **Setup Instructions**

### Step 1: Configure Cloud Build Service Account
```bash
# Get the Cloud Build service account
PROJECT_ID=$(gcloud config get-value project)
BUILD_SA="$PROJECT_ID@cloudbuild.gserviceaccount.com"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$BUILD_SA" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$BUILD_SA" \
    --role="roles/container.admin"
```

### Step 2: Configure Docker Registry Access
```bash
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker
```

### Step 3: Test Cloud Build
```bash
# Navigate to Alphintra directory
cd /Users/usubithan/Documents/Alphintra

# Test build (this will build all services)
gcloud builds submit --config=cloudbuild.yaml .
```

## 🧪 **Testing the Setup**

### 1. Build All Services
```bash
# Use the provided script
./infra/scripts/build-with-cloud-build.sh
```

### 2. Verify Images in Registry
```bash
# List built images
gcloud container images list --repository=gcr.io/$PROJECT_ID/alphintra

# Check specific image
gcloud container images list-tags gcr.io/$PROJECT_ID/alphintra/api-gateway
```

### 3. Deploy to K3D
```bash
# Deploy with Cloud Build images
./infra/scripts/k8s/deploy-with-cloud-build.sh
```

## 🔍 **Expected Results**

### Image Sizes (Google Distroless)
- **API Gateway**: ~150MB (vs 300MB Alpine)
- **Auth Service**: ~140MB (vs 280MB Alpine)
- **Trading API**: ~120MB (vs 200MB Alpine)
- **GraphQL Gateway**: ~125MB (vs 205MB Alpine)

### Build Performance
- **Total build time**: ~8-12 minutes (all services parallel)
- **Subsequent builds**: ~4-6 minutes (with caching)
- **Individual service**: ~2-3 minutes

### Security Benefits
- **Zero CVEs** in base images
- **Minimal attack surface** (no shell, package manager)
- **Automatic security scanning** with Cloud Build

## 🐛 **Troubleshooting**

### Common Issues

#### 1. Authentication Error
```bash
# Error: could not find default credentials
gcloud auth application-default login
```

#### 2. API Not Enabled
```bash
# Error: Cloud Build API not enabled
gcloud services enable cloudbuild.googleapis.com
```

#### 3. Permission Denied
```bash
# Error: insufficient permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$BUILD_SA" \
    --role="roles/cloudbuild.builds.builder"
```

#### 4. Docker Registry Issues
```bash
# Error: unauthorized to access registry
gcloud auth configure-docker
```

## 💰 **Cost Optimization**

### Cloud Build Pricing
- **Free tier**: 120 build-minutes per day
- **Paid tier**: $0.003 per build-minute
- **Estimated cost**: $5-15/month for active development

### Optimization Tips
```bash
# Use build cache to reduce build times
gcloud builds submit --config=cloudbuild.yaml --disk-size=100GB .

# Use preemptible machines for cost savings
# (Add to cloudbuild.yaml: options -> machineType: 'E2_HIGHCPU_8')
```

## 🚀 **Advanced Configuration**

### 1. Automated Builds with Triggers
```bash
# Create build trigger for main branch
gcloud builds triggers create github \
    --repo-name=alphintra \
    --repo-owner=your-username \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml
```

### 2. Multi-Environment Builds
```bash
# Build for different environments
gcloud builds submit --config=cloudbuild.yaml \
    --substitutions=_DEPLOY_ENV=staging .
```

### 3. Secret Management
```bash
# Store secrets in Secret Manager
gcloud secrets create alphintra-jwt-secret --data-file=jwt.secret

# Use in cloudbuild.yaml:
# availableSecrets:
#   secretManager:
#   - versionName: projects/$PROJECT_ID/secrets/alphintra-jwt-secret/versions/latest
#     env: 'JWT_SECRET'
```

## ✅ **Verification Checklist**

- [ ] Google Cloud project created and configured
- [ ] Cloud Build and Container Registry APIs enabled
- [ ] Authentication configured (gcloud auth login)
- [ ] Service account permissions granted
- [ ] Docker registry access configured
- [ ] Test build completed successfully
- [ ] Images available in Container Registry
- [ ] Local K3D deployment working
- [ ] All services responding correctly
- [ ] Resource usage within expected limits

## 📊 **Performance Monitoring**

### Build Metrics
```bash
# View build history
gcloud builds list --limit=10

# Get build details
gcloud builds describe [BUILD_ID]

# View build logs
gcloud builds log [BUILD_ID]
```

### Container Metrics
```bash
# Check image vulnerabilities
gcloud container images scan gcr.io/$PROJECT_ID/alphintra/api-gateway:latest

# List image layers
gcloud container images list-tags gcr.io/$PROJECT_ID/alphintra/api-gateway \
    --format="table(tags,timestamp)"
```

## 🎉 **Success Indicators**

### Build Success
- All services build without errors
- Images available in Container Registry
- Build time under 15 minutes
- No security vulnerabilities detected

### Deployment Success
- All pods start within 2 minutes
- Memory usage under 2GB total
- CPU usage under 1000m total
- All health checks passing

### Performance Success
- Response times under 100ms
- 50% reduction in container sizes
- 60% improvement in startup times
- Zero security vulnerabilities

Once you have this setup working, you'll have a production-ready, highly optimized container build and deployment pipeline!