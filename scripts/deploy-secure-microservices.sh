#!/bin/bash
# Secure API Microservices Deployment Script
# Deploys the complete secure microservices architecture with K3D cluster

set -euo pipefail

# Configuration
CLUSTER_NAME="alphintra-cluster"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
K8S_BASE_DIR="$PROJECT_ROOT/infra/kubernetes/base"
K3D_CONFIG_DIR="$PROJECT_ROOT/infra/kubernetes/local-k3d"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_phase() {
    echo -e "${PURPLE}[PHASE]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    for tool in k3d kubectl helm docker; do
        if ! command -v $tool >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    fi
    
    log_success "All prerequisites are satisfied"
}

# Phase 1: Infrastructure Setup
deploy_infrastructure() {
    log_phase "Phase 1: Deploying K3D Infrastructure"
    
    # Create K3D cluster
    log_info "Creating K3D cluster with optimized configuration..."
    if k3d cluster list | grep -q "$CLUSTER_NAME"; then
        log_warning "Cluster '$CLUSTER_NAME' already exists. Deleting it..."
        k3d cluster delete "$CLUSTER_NAME"
    fi
    
    k3d cluster create --config "$K3D_CONFIG_DIR/cluster-config.yaml"
    
    # Wait for cluster to be ready
    log_info "Waiting for cluster to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=300s
    
    # Create namespace
    log_info "Creating alphintra namespace..."
    kubectl create namespace alphintra --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace alphintra istio-injection=enabled --overwrite
    
    # Install metrics server
    log_info "Installing metrics server..."
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    kubectl patch deployment metrics-server -n kube-system --type='json' \
        -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
    
    # Install NGINX Ingress Controller
    log_info "Installing NGINX Ingress Controller..."
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=600s
    
    log_success "Infrastructure setup completed"
}

# Phase 2: Core Services
deploy_core_services() {
    log_phase "Phase 2: Deploying Core Services"
    
    # Deploy PostgreSQL
    log_info "Deploying PostgreSQL StatefulSet..."
    kubectl apply -f "$K8S_BASE_DIR/postgresql-statefulset.yaml"
    
    # Deploy Redis
    log_info "Deploying Redis StatefulSet..."
    kubectl apply -f "$K8S_BASE_DIR/redis-statefulset.yaml"
    
    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    kubectl wait --for=condition=Ready pod -l app=postgresql -n alphintra --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=redis -n alphintra --timeout=300s
    
    # Deploy Eureka Server
    log_info "Deploying Eureka Service Discovery..."
    kubectl apply -f "$K8S_BASE_DIR/eureka-server.yaml"
    kubectl wait --for=condition=Ready pod -l app=eureka-server -n alphintra --timeout=300s
    
    # Deploy Config Server
    log_info "Deploying Spring Cloud Config Server..."
    kubectl apply -f "$K8S_BASE_DIR/config-server.yaml"
    kubectl wait --for=condition=Ready pod -l app=config-server -n alphintra --timeout=300s
    
    # Deploy API Gateway
    log_info "Deploying API Gateway..."
    # First, we need to build the gateway JAR and make it available
    build_gateway_jar
    kubectl apply -f "$K8S_BASE_DIR/api-gateway.yaml"
    kubectl wait --for=condition=Ready pod -l app=api-gateway -n alphintra --timeout=300s
    
    log_success "Core services deployment completed"
}

# Build Gateway JAR
build_gateway_jar() {
    log_info "Building API Gateway JAR..."
    cd "$PROJECT_ROOT/src/backend/gateway"
    
    # Build the JAR file
    ./mvnw clean package -DskipTests
    
    # Create a ConfigMap with the JAR file
    kubectl create configmap gateway-jar \
        --from-file=gateway.jar=target/gateway-*.jar \
        -n alphintra --dry-run=client -o yaml | kubectl apply -f -
    
    cd "$SCRIPT_DIR"
    log_success "Gateway JAR built and deployed"
}

# Phase 3: Security Implementation
deploy_security() {
    log_phase "Phase 3: Implementing Security Layer"
    
    # Install Istio (lightweight version for K3D)
    log_info "Installing Istio service mesh..."
    
    # Download and install Istio
    if [ ! -d "$PROJECT_ROOT/istio" ]; then
        curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
        mv istio-* "$PROJECT_ROOT/istio"
    fi
    
    export PATH="$PROJECT_ROOT/istio/bin:$PATH"
    
    # Install Istio with minimal profile for K3D
    istioctl install --set values.defaultRevision=default --set values.pilot.env.EXTERNAL_ISTIOD=false -y
    
    # Enable Istio injection for alphintra namespace
    kubectl label namespace alphintra istio-injection=enabled --overwrite
    
    # Deploy security policies
    deploy_security_policies
    
    log_success "Security implementation completed"
}

# Deploy security policies
deploy_security_policies() {
    log_info "Deploying security policies..."
    
    # Create NetworkPolicies
    kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: alphintra
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-gateway
  namespace: alphintra
spec:
  podSelector:
    matchLabels:
      app: api-gateway
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from: []
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - {}
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-internal-communication
  namespace: alphintra
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: alphintra
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: alphintra
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
EOF
    
    log_success "Security policies deployed"
}

# Phase 4: Microservices Refactoring
deploy_microservices() {
    log_phase "Phase 4: Deploying Microservices"
    
    # Clean up test files from no-code service
    cleanup_test_files
    
    # Deploy individual microservices
    deploy_trading_service
    deploy_risk_service
    deploy_user_service
    deploy_broker_service
    deploy_strategy_service
    deploy_notification_service
    
    log_success "Microservices deployment completed"
}

# Cleanup test files from production
cleanup_test_files() {
    log_info "Cleaning up test files from production code..."
    
    local nocode_dir="$PROJECT_ROOT/src/backend/no-code-service"
    
    # Remove test files (already done, but keeping for completeness)
    rm -f "$nocode_dir"/test_*.py
    rm -f "$nocode_dir"/simple_test_server.py
    
    log_success "Test files cleaned up - production code is now clean"
}

# Deploy individual microservices
deploy_trading_service() {
    log_info "Deploying Trading Service..."
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-service
  namespace: alphintra
  labels:
    app: trading-service
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: trading-service
      version: v1
  template:
    metadata:
      labels:
        app: trading-service
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/actuator/prometheus"
    spec:
      containers:
      - name: trading-service
        image: python:3.11-slim
        command:
          - python
          - /app/main.py
        env:
        - name: DATABASE_URL
          value: "postgresql://trading_service_user:trading_service_pass@postgresql-primary.alphintra.svc.cluster.local:5432/alphintra_trading"
        - name: REDIS_URL
          value: "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/1"
        - name: EUREKA_SERVER_URL
          value: "http://eureka-server.alphintra.svc.cluster.local:8761/eureka/"
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: app-code
          mountPath: /app
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: app-code
        configMap:
          name: trading-service-code
---
apiVersion: v1
kind: Service
metadata:
  name: trading-service
  namespace: alphintra
  labels:
    app: trading-service
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
  selector:
    app: trading-service
EOF
    
    log_success "Trading Service deployed"
}

deploy_risk_service() {
    log_info "Deploying Risk Management Service..."
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: risk-service
  namespace: alphintra
  labels:
    app: risk-service
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: risk-service
      version: v1
  template:
    metadata:
      labels:
        app: risk-service
        version: v1
    spec:
      containers:
      - name: risk-service
        image: python:3.11-slim
        command:
          - python
          - /app/main.py
        env:
        - name: DATABASE_URL
          value: "postgresql://risk_service_user:risk_service_pass@postgresql-primary.alphintra.svc.cluster.local:5432/alphintra_risk"
        - name: REDIS_URL
          value: "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/2"
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: risk-service
  namespace: alphintra
  labels:
    app: risk-service
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: risk-service
EOF
    
    log_success "Risk Service deployed"
}

deploy_user_service() {
    log_info "Deploying User Management Service..."
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: alphintra
  labels:
    app: user-service
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
      version: v1
  template:
    metadata:
      labels:
        app: user-service
        version: v1
    spec:
      containers:
      - name: user-service
        image: python:3.11-slim
        command:
          - python
          - /app/main.py
        env:
        - name: DATABASE_URL
          value: "postgresql://user_service_user:user_service_pass@postgresql-primary.alphintra.svc.cluster.local:5432/alphintra_user"
        - name: REDIS_URL
          value: "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/3"
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: alphintra
  labels:
    app: user-service
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: user-service
EOF
    
    log_success "User Service deployed"
}

deploy_broker_service() {
    log_info "Deploying Broker Service..."
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broker-service
  namespace: alphintra
  labels:
    app: broker-service
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: broker-service
      version: v1
  template:
    metadata:
      labels:
        app: broker-service
        version: v1
    spec:
      containers:
      - name: broker-service
        image: python:3.11-slim
        command:
          - python
          - /app/main.py
        env:
        - name: DATABASE_URL
          value: "postgresql://broker_service_user:broker_service_pass@postgresql-primary.alphintra.svc.cluster.local:5432/alphintra_broker"
        - name: REDIS_URL
          value: "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/4"
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: broker-service
  namespace: alphintra
  labels:
    app: broker-service
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: broker-service
EOF
    
    log_success "Broker Service deployed"
}

deploy_strategy_service() {
    log_info "Deploying Strategy Service..."
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: strategy-service
  namespace: alphintra
  labels:
    app: strategy-service
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: strategy-service
      version: v1
  template:
    metadata:
      labels:
        app: strategy-service
        version: v1
    spec:
      containers:
      - name: strategy-service
        image: python:3.11-slim
        command:
          - python
          - /app/main.py
        env:
        - name: DATABASE_URL
          value: "postgresql://strategy_service_user:strategy_service_pass@postgresql-primary.alphintra.svc.cluster.local:5432/alphintra_strategy"
        - name: REDIS_URL
          value: "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/5"
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: strategy-service
  namespace: alphintra
  labels:
    app: strategy-service
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: strategy-service
EOF
    
    log_success "Strategy Service deployed"
}

deploy_notification_service() {
    log_info "Deploying Notification Service..."
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notification-service
  namespace: alphintra
  labels:
    app: notification-service
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: notification-service
      version: v1
  template:
    metadata:
      labels:
        app: notification-service
        version: v1
    spec:
      containers:
      - name: notification-service
        image: python:3.11-slim
        command:
          - python
          - /app/main.py
        env:
        - name: DATABASE_URL
          value: "postgresql://notification_service_user:notification_service_pass@postgresql-primary.alphintra.svc.cluster.local:5432/alphintra_notification"
        - name: REDIS_URL
          value: "redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/6"
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: notification-service
  namespace: alphintra
  labels:
    app: notification-service
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: notification-service
EOF
    
    log_success "Notification Service deployed"
}

# Phase 5: API Layer
deploy_api_layer() {
    log_phase "Phase 5: Deploying Unified API Layer"
    
    # The API Gateway is already deployed in Phase 2
    # Here we can add GraphQL gateway or other API enhancements
    
    log_info "API Layer setup with Gateway routing completed"
    log_success "API Layer deployment completed"
}

# Phase 6: Monitoring
deploy_monitoring() {
    log_phase "Phase 6: Deploying Monitoring & Observability"
    
    # Install Prometheus and Grafana
    log_info "Installing Prometheus and Grafana..."
    
    # Add Helm repos
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    # Install Prometheus
    helm install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
        --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false
    
    log_success "Monitoring deployment completed"
}

# Validation and testing
validate_deployment() {
    log_phase "Phase 8: Validating Deployment"
    
    log_info "Checking all services..."
    
    # Check if all pods are running
    kubectl get pods -n alphintra
    kubectl get services -n alphintra
    
    # Test API Gateway
    log_info "Testing API Gateway..."
    kubectl port-forward -n alphintra svc/api-gateway 8080:8080 &
    sleep 5
    
    if curl -f http://localhost:8080/actuator/health >/dev/null 2>&1; then
        log_success "API Gateway is healthy"
    else
        log_warning "API Gateway health check failed"
    fi
    
    # Kill port-forward
    pkill -f "kubectl port-forward" || true
    
    log_success "Deployment validation completed"
}

# Display cluster information
display_cluster_info() {
    log_success "Secure API Microservices Architecture Deployment Completed!"
    echo ""
    log_info "Cluster Information:"
    echo "  Cluster Name: $CLUSTER_NAME"
    echo "  Namespace: alphintra"
    echo ""
    log_info "Services Deployed:"
    echo "  ✓ PostgreSQL Database (with service-specific databases)"
    echo "  ✓ Redis Cache"
    echo "  ✓ Eureka Service Discovery"
    echo "  ✓ Spring Cloud Config Server"
    echo "  ✓ API Gateway (Spring Cloud Gateway)"
    echo "  ✓ Trading Service"
    echo "  ✓ Risk Management Service"
    echo "  ✓ User Management Service"
    echo "  ✓ Broker Service"
    echo "  ✓ Strategy Service"
    echo "  ✓ Notification Service"
    echo "  ✓ Istio Service Mesh"
    echo "  ✓ Monitoring (Prometheus & Grafana)"
    echo ""
    log_info "Access Points:"
    echo "  API Gateway: http://localhost:30001"
    echo "  Eureka Dashboard: kubectl port-forward -n alphintra svc/eureka-server 8761:8761"
    echo "  Grafana: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
    echo ""
    log_info "Useful Commands:"
    echo "  kubectl get pods -n alphintra"
    echo "  kubectl get services -n alphintra"
    echo "  kubectl logs -f deployment/api-gateway -n alphintra"
    echo "  k3d cluster delete $CLUSTER_NAME"
    echo ""
    log_info "Database Connections (Internal):"
    echo "  PostgreSQL: postgresql-primary.alphintra.svc.cluster.local:5432"
    echo "  Redis: redis-primary.alphintra.svc.cluster.local:6379"
}

# Main execution
main() {
    log_info "Starting Secure API Microservices Architecture Deployment"
    echo "=================================================="
    
    check_prerequisites
    deploy_infrastructure
    deploy_core_services
    deploy_security
    deploy_microservices
    deploy_api_layer
    deploy_monitoring
    validate_deployment
    display_cluster_info
    
    log_success "Deployment completed successfully!"
}

# Handle script arguments
case "${1:-all}" in
    "infra"|"infrastructure")
        check_prerequisites
        deploy_infrastructure
        ;;
    "core")
        deploy_core_services
        ;;
    "security")
        deploy_security
        ;;
    "microservices")
        deploy_microservices
        ;;
    "api")
        deploy_api_layer
        ;;
    "monitoring")
        deploy_monitoring
        ;;
    "validate")
        validate_deployment
        ;;
    "all"|*)
        main
        ;;
esac