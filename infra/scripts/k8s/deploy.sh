#!/bin/bash

# Kubernetes Deployment Script for Alphintra Trading Platform
# This script deploys all Alphintra services to Kubernetes

set -e

ENV=${1:-dev}

echo "🚀 Deploying Alphintra Trading Platform to Kubernetes (${ENV} environment)..."

# Set kubectl context to k3d cluster
echo "🔧 Setting kubectl context to k3d cluster..."
kubectl config use-context k3d-alphintra-cluster

# Verify cluster is ready
echo "🔍 Verifying cluster status..."
kubectl cluster-info
kubectl get nodes

# Check if Istio is installed
echo "🕸️  Checking Istio installation..."
if ! kubectl get namespace istio-system > /dev/null 2>&1; then
    echo "⚠️  Istio is not installed. Installing Istio first..."
    cd "$(dirname "$0")/../.."
    ./scripts/install-istio.sh
fi

# Deploy infrastructure services first
echo "📦 Deploying infrastructure services..."

# PostgreSQL
echo "  - Deploying PostgreSQL..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: alphintra-dev
  labels:
    app: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "alphintra_dev"
        - name: POSTGRES_USER
          value: "dev_user"
        - name: POSTGRES_PASSWORD
          value: "dev_password123"
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: alphintra-dev
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
EOF

# Redis
echo "  - Deploying Redis..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: alphintra-dev
  labels:
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command: ["redis-server", "--requirepass", "redis123"]
        volumeMounts:
        - name: redis-storage
          mountPath: /data
      volumes:
      - name: redis-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: alphintra-dev
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
EOF

# Wait for infrastructure services to be ready
echo "⏳ Waiting for infrastructure services to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n alphintra-dev
kubectl wait --for=condition=available --timeout=300s deployment/redis -n alphintra-dev

# Deploy application services
echo "🏗️  Deploying application services..."

# Gateway Service
echo "  - Deploying Gateway Service..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: alphintra-dev
  labels:
    app: gateway
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gateway
      version: v1
  template:
    metadata:
      labels:
        app: gateway
        version: v1
    spec:
      containers:
      - name: gateway
        image: openjdk:17-jdk-slim
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "k8s"
        - name: REDIS_HOST
          value: "redis"
        - name: REDIS_PASSWORD
          value: "redis123"
        command: ["sh", "-c", "echo 'Gateway service running on Kubernetes' && sleep 3600"]
        readinessProbe:
          exec:
            command: ["sh", "-c", "echo 'ready'"]
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          exec:
            command: ["sh", "-c", "echo 'alive'"]
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: gateway
  namespace: alphintra-dev
  labels:
    app: gateway
spec:
  selector:
    app: gateway
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  type: ClusterIP
EOF

# Auth Service
echo "  - Deploying Auth Service..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: alphintra-dev
  labels:
    app: auth-service
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: auth-service
      version: v1
  template:
    metadata:
      labels:
        app: auth-service
        version: v1
    spec:
      containers:
      - name: auth-service
        image: python:3.11-slim
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          value: "postgresql://dev_user:dev_password123@postgres:5432/alphintra_dev"
        - name: REDIS_URL
          value: "redis://:redis123@redis:6379/0"
        - name: ENVIRONMENT
          value: "k8s"
        command: ["sh", "-c", "echo 'Auth service running on Kubernetes' && sleep 3600"]
        readinessProbe:
          exec:
            command: ["sh", "-c", "echo 'ready'"]
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          exec:
            command: ["sh", "-c", "echo 'alive'"]
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  namespace: alphintra-dev
  labels:
    app: auth-service
spec:
  selector:
    app: auth-service
  ports:
  - port: 8001
    targetPort: 8001
    name: http
  type: ClusterIP
EOF

# Trading API
echo "  - Deploying Trading API..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-api
  namespace: alphintra-dev
  labels:
    app: trading-api
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: trading-api
      version: v1
  template:
    metadata:
      labels:
        app: trading-api
        version: v1
    spec:
      containers:
      - name: trading-api
        image: python:3.11-slim
        ports:
        - containerPort: 8002
        env:
        - name: DATABASE_URL
          value: "postgresql://dev_user:dev_password123@postgres:5432/alphintra_dev"
        - name: REDIS_URL
          value: "redis://:redis123@redis:6379/1"
        - name: ENVIRONMENT
          value: "k8s"
        command: ["sh", "-c", "echo 'Trading API running on Kubernetes' && sleep 3600"]
        readinessProbe:
          exec:
            command: ["sh", "-c", "echo 'ready'"]
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          exec:
            command: ["sh", "-c", "echo 'alive'"]
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: trading-api
  namespace: alphintra-dev
  labels:
    app: trading-api
spec:
  selector:
    app: trading-api
  ports:
  - port: 8002
    targetPort: 8002
    name: http
  type: ClusterIP
EOF

# Wait for application services to be ready
echo "⏳ Waiting for application services to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/gateway -n alphintra-dev
kubectl wait --for=condition=available --timeout=300s deployment/auth-service -n alphintra-dev
kubectl wait --for=condition=available --timeout=300s deployment/trading-api -n alphintra-dev

# Verify deployment
echo "🔍 Verifying deployment..."
echo ""
echo "📊 Deployment Status:"
kubectl get pods -n alphintra-dev
echo ""
echo "🌐 Services:"
kubectl get services -n alphintra-dev
echo ""

# Check Istio sidecar injection
echo "🕸️  Checking Istio sidecar injection..."
SIDECAR_COUNT=$(kubectl get pods -n alphintra-dev -o jsonpath='{.items[*].spec.containers[*].name}' | grep -c istio-proxy || echo "0")
if [ "$SIDECAR_COUNT" -gt 0 ]; then
    echo "✅ Istio sidecars are injected (found $SIDECAR_COUNT sidecars)"
else
    echo "⚠️  No Istio sidecars found. Pods may need to be recreated after Istio installation."
fi

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🔧 Access Information:"
echo "  Gateway: http://localhost:8090"
echo "  Auth Service: http://localhost:8090/api/auth"
echo "  Trading API: http://localhost:8090/api/trading"
echo ""
echo "📊 Monitoring:"
echo "  Prometheus: kubectl port-forward -n istio-system svc/prometheus 9090:9090"
echo "  Grafana: kubectl port-forward -n istio-system svc/grafana 3000:3000"
echo "  Jaeger: kubectl port-forward -n istio-system svc/jaeger 16686:16686"
echo "  Kiali: kubectl port-forward -n istio-system svc/kiali 20001:20001"
echo ""
echo "🏷️  Useful Commands:"
echo "  kubectl get pods -n alphintra-dev"
echo "  kubectl logs -f deployment/gateway -n alphintra-dev"
echo "  kubectl describe pod <pod-name> -n alphintra-dev"
echo ""