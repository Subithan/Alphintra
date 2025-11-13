# Alphintra Platform - Cloud Architecture Documentation

**Project**: Alphintra Algorithmic Trading Platform  
**GCP Project ID**: `alphintra-472817`  
**Project Number**: `999709622705`  
**Region**: `us-central1` (Primary)  
**Last Updated**: November 4, 2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Infrastructure Components](#infrastructure-components)
4. [Microservices Architecture](#microservices-architecture)
5. [Network Architecture](#network-architecture)
6. [Security & Identity](#security--identity)
7. [Data Layer](#data-layer)
8. [Service Mesh & Traffic Management](#service-mesh--traffic-management)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Observability & Monitoring](#observability--monitoring)
11. [Deployment Strategy](#deployment-strategy)
12. [Disaster Recovery & High Availability](#disaster-recovery--high-availability)

---

## Executive Summary

The Alphintra platform is a cloud-native, microservices-based algorithmic trading platform deployed on **Google Cloud Platform (GCP)**. The architecture leverages:

- **Google Kubernetes Engine (GKE)** for container orchestration
- **Istio Service Mesh** for traffic management, security, and observability
- **Cloud SQL (PostgreSQL)** for transactional data
- **Artifact Registry** for container image management
- **Cloud Build** for CI/CD automation
- **GitHub Actions** for workflow orchestration
- **ArgoCD** for GitOps-based deployments

The platform serves three environments: **dev**, **staging**, and **prod**, with infrastructure provisioned through **Terraform** and application deployments managed through **Kustomize** overlays.

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Internet / Users                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    External Load Balancer                            │
│                    (34.172.120.224)                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Istio Ingress Gateway                          │
│                  (istio-ingressgateway service)                      │
│              HTTP:80 / HTTPS:443 / mTLS:15443                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GKE Cluster: alphintra-cluster                    │
│                   Location: us-central1-a                            │
│                   K8s Version: 1.33.5-gke.1080000                    │
│                   Node Count: 5 nodes                                │
├─────────────────────────────────────────────────────────────────────┤
│  Namespaces:                                                         │
│  - alphintra (main workloads)                                        │
│  - istio-system (service mesh)                                       │
│  - observability (monitoring stack)                                  │
│  - cert-manager (TLS certificates)                                   │
│  - default (legacy/frontend)                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Container Orchestration** | Google Kubernetes Engine (GKE) | 1.33.5 |
| **Service Mesh** | Istio | ASM 1.17.2 |
| **Frontend** | Next.js | 15.x |
| **API Gateway** | Spring Cloud Gateway | 3.2.x |
| **Backend Services** | Spring Boot / FastAPI | 3.2.x / 0.11x+ |
| **Databases** | Cloud SQL PostgreSQL | 15 |
| **Caching** | Redis (In-cluster) | 7.x |
| **Message Queue** | Kafka (Planned) | - |
| **Container Registry** | Artifact Registry | - |
| **IaC** | Terraform | 1.5+ |
| **GitOps** | ArgoCD | Latest |
| **Monitoring** | Prometheus + Grafana | Operator Stack |

---

## Infrastructure Components

### 1. Google Kubernetes Engine (GKE)

**Cluster Name**: `alphintra-cluster`  
**Location**: `us-central1-a` (zonal)  
**Master Version**: `1.33.5-gke.1080000`  
**Node Pools**:

1. **Default Pool** (3 nodes)
   - Machine Type: `e2-medium` (2 vCPU, 4 GB memory)
   - Purpose: General workloads
   - Internal IPs: `10.128.0.39`, `10.128.0.41`, `10.128.0.42`

2. **NAT Backend Pool** (2 nodes)
   - Machine Type: `e2-standard-2` (2 vCPU, 8 GB memory)
   - Purpose: Egress traffic and external API calls
   - Internal IPs: `10.128.0.43`, `10.128.0.44`

**Pod CIDR**: `10.32.0.0/14` (secondary range)  
**Service CIDR**: `34.118.224.0/20` (GKE managed)

### 2. Cloud SQL

**Instance Name**: `alphintra-db-instance`  
**Database Engine**: PostgreSQL 15  
**Region**: `us-central1`  
**Internal IP**: `10.6.124.3`  
**Connection Method**: Private IP + Cloud SQL Proxy sidecar  
**High Availability**: Single instance (planned for HA in prod)

**Databases**:
- `auth_db` - User authentication and authorization
- `wallet_db` - Digital wallet and transactions
- `trading_db` - Order execution and trading history
- `customer_support_db` - Support tickets and chat
- Additional service-specific databases

**Access Pattern**: Cloud SQL Proxy sidecar injected into pods requiring database access

### 3. Artifact Registry

**Repositories**:

| Repository | Location | Format | Size | Purpose |
|------------|----------|--------|------|---------|
| `gcr.io` | `us` (multi-region) | Docker | 29 GB | Legacy GCR compatibility |
| `alphintra` | `us-central1` | Docker | 873 MB | Production images |
| `alphintra-dev` | `us-central1` | Docker | 0 MB | Development images |

**Image Naming Convention**:
```
us-central1-docker.pkg.dev/alphintra-472817/alphintra/{service-name}:{tag}
```

**Vulnerability Scanning**: Enabled via Container Scanning API

### 4. Networking

**VPC Networks**:

1. **default** (Primary, Auto-mode)
   - CIDR: Auto-generated per region
   - us-central1 subnet: `10.128.0.0/20`
   - Pod secondary range: `10.32.0.0/14`
   - Service peering: `servicenetworking-googleapis-com` (for Cloud SQL)

2. **alphintra-dev-vpc** (Custom, under construction)
   - Purpose: Dedicated dev environment isolation
   - Managed via Terraform

**External IPs**:

| Name | IP Address | Region | Purpose |
|------|------------|--------|---------|
| Istio Ingress LB | `34.172.120.224` | us-central1 | Main entry point |
| `nat-auto-ip-*` | `34.134.209.61` | us-central1 | NAT gateway for outbound |
| `binance-proxy-eu` | `34.38.218.227` | europe-west1 | Binance API proxy |
| `trading-egress-eu` | `34.78.35.4` | europe-west1 | Trading engine egress |
| GKE Ingress | `34.98.73.110` | Global | Legacy ingress |

**Firewall Rules**:

| Rule Name | Direction | Source | Protocol/Port | Purpose |
|-----------|-----------|--------|---------------|---------|
| `allow-gclb-health-checks` | Ingress | `35.191.0.0/16`, `130.211.0.0/22` | TCP/31712 | GCP Load Balancer health checks |
| `allow-web-traffic` | Ingress | `0.0.0.0/0` | TCP/80,443 | Public HTTP/HTTPS |
| `default-allow-internal` | Ingress | `10.128.0.0/9` | All TCP/UDP/ICMP | Internal VPC communication |
| `gke-alphintra-cluster-a74edd6c-all` | Ingress | `10.32.0.0/14` | All protocols | Pod-to-pod communication |

### 5. Storage

**Cloud Storage Buckets**:
- `gs://alphintra-472817-mvn-cache` - Maven dependency cache (build optimization)
- `gs://alphintra-472817-python-cache` - Python pip cache
- `gs://alphintra-472817-node-cache` - NPM/Node cache

### 6. Secret Management

**Secret Manager Secrets**:
- `auth-service-db-password` - Auth service database credentials
- JWT secrets and API keys stored per service

**Access**: Via Workload Identity and `secretmanager.secretAccessor` IAM role

---

## Microservices Architecture

### Service Inventory

| Service | Language/Framework | Port | Namespace | Status | Purpose |
|---------|-------------------|------|-----------|--------|---------|
| **service-gateway** | Spring Cloud Gateway | 8080 | alphintra | Running | API Gateway, rate limiting, JWT validation |
| **auth-service** | Spring Boot | 8009 | alphintra | Running | Authentication, authorization, user management, subscriptions (Stripe) |
| **trading-engine** | Spring Boot | 8008 | alphintra | Running | Order execution, position management |
| **wallet-service** | Spring Boot | 8011 | alphintra | Running | Digital wallet, balance management |
| **marketplace-service** | Spring Boot | 8200 | alphintra | Running | Strategy marketplace |
| **customer-support-service** | Spring Boot | 8010/8011 | alphintra | Running | Support tickets, chat |
| **ai-ml-strategy-service** | FastAPI (Python) | 8002 | alphintra | Running | AI/ML strategy development, backtesting |
| **no-code-service** | FastAPI (Python) | 8006 | alphintra | Running | Visual workflow builder, no-code strategy creation |
| **redis** | Redis | 6379 | alphintra | Running | Session cache, rate limiter backend |
| **frontend-app** | Next.js | 3000 | default | Running | Web application UI |

### Service Communication Patterns

```
Client Request
    ↓
Istio Ingress Gateway (mTLS + JWT validation)
    ↓
service-gateway (8080) [Rate Limiting + Routing]
    ├─→ auth-service (8009) [Authentication]
    ├─→ trading-engine (8008) [Trading Operations]
    ├─→ wallet-service (8011) [Balance Management]
    ├─→ marketplace-service (8200) [Strategy Marketplace]
    ├─→ ai-ml-strategy-service (8002) [AI/ML Strategies]
    ├─→ no-code-service (8006) [Visual Workflow]
    └─→ customer-support-service (8010) [Support]
```

### Service Discovery

- **Internal DNS**: Kubernetes DNS (CoreDNS)
- **Service Naming**: `{service-name}.{namespace}.svc.cluster.local`
- **Example**: `http://auth-service.alphintra.svc.cluster.local:8009`

### Service Mesh Features

- **mTLS**: Strict mutual TLS between all services
- **Traffic Management**: Istio VirtualServices and DestinationRules
- **Observability**: Distributed tracing, metrics, access logs
- **Circuit Breaking**: Automatic failure detection and isolation
- **Retry Logic**: Configurable retry policies per route

---

## Network Architecture

### Ingress Architecture

```
Internet
    ↓
External Load Balancer (34.172.120.224)
    ↓
┌─────────────────────────────────────────┐
│  Istio Ingress Gateway                  │
│  - Port 80 (HTTP)                       │
│  - Port 443 (HTTPS/TLS)                 │
│  - Port 15443 (mTLS)                    │
│  - Hosts: *.alphintra.dev,             │
│           alphintra.com,                │
│           api.alphintra.com             │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Virtual Service: gateway-external      │
│  - CORS enabled                         │
│  - Retry: 3 attempts                    │
│  - Timeout: 30s                         │
│  - Route: service-gateway:80            │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  service-gateway Deployment             │
│  - JWT validation                       │
│  - Rate limiting (Redis)                │
│  - Request routing                      │
└─────────────────────────────────────────┘
```

### VPC Peering

- **Cloud SQL Private Connection**: `servicenetworking-googleapis-com` peering
- **IP Range**: `10.6.124.0/24` (google-managed-services)

### Egress Architecture

**NAT Gateway**:
- IP: `34.134.209.61`
- Purpose: Outbound internet access for pods
- Region: us-central1

**Dedicated Egress IPs**:
- **Binance Proxy (EU)**: `34.38.218.227` - europe-west1
- **Trading Egress (EU)**: `34.78.35.4` - europe-west1

---

## Security & Identity

### Workload Identity

**Enabled**: GKE cluster configured with Workload Identity  
**Workload Pool**: `alphintra-472817.svc.id.goog`

**Service Accounts**:

| GCP Service Account | K8s Service Account | Namespace | IAM Roles |
|---------------------|---------------------|-----------|-----------|
| `auth-cloudsql-dev@` | `auth-service` | alphintra | `cloudsql.client`, `secretmanager.secretAccessor`, `logging.logWriter` |
| `gateway-runtime-dev@` | `service-gateway` | alphintra | `monitoring.metricWriter`, `cloudtrace.agent`, `logging.logWriter` |
| `gke-nocode-sa@` | `no-code-service` | alphintra | Custom permissions for AI/ML |
| `trading-engine@` | `trading-engine` | alphintra | Trading-specific permissions |
| `github-actions-deployer@` | - | - | CI/CD deployment permissions |
| `github-ci-deployer@` | - | - | Legacy CI/CD account |

### Authentication & Authorization

**JWT-based Authentication**:
- **Issuer**: auth-service
- **Algorithm**: HMAC-SHA256
- **Secret Storage**: Secret Manager
- **Validation**: Istio RequestAuthentication + service-gateway

**Istio Security Policies**:

1. **PeerAuthentication** (`peerauthentication-default.yaml`):
   - Mode: `STRICT` (mandatory mTLS)
   - Applied to: All services in mesh

2. **RequestAuthentication** (`requestauthentication-jwt.yaml`):
   - JWKS discovery from auth-service
   - Applied to: Gateway workloads

3. **AuthorizationPolicy**:
   - `authorizationpolicy-gateway.yaml`: Controls access to gateway
   - `authorizationpolicy-gateway-allow-all.yaml`: Temporary dev policy
   - `authorizationpolicy-trading-public.yaml`: Public trading endpoints

### TLS/SSL

**Certificate Management**:
- **Tool**: cert-manager
- **Issuer**: Let's Encrypt (configured in `letsencrypt-issuer.yaml`)
- **Certificate**: `alphintra-gateway-tls` (for `*.alphintra.dev`)
- **Storage**: Kubernetes Secret in `istio-system` namespace

### Security Scanning

**Container Vulnerability Scanning**:
- **Tool**: Trivy, Snyk (GitHub Actions)
- **Workflow**: `.github/workflows/security-scan.yml`
- **Frequency**: On PR, before prod promotion

---

## Data Layer

### Cloud SQL Architecture

**Connection Method**:
```
Pod (e.g., auth-service)
    ├─→ Main Container (Spring Boot) :8009
    └─→ Cloud SQL Proxy Sidecar :5432
            ↓
    Cloud SQL Private IP (10.6.124.3:5432)
            ↓
    PostgreSQL Database
```

**Sidecar Configuration** (example from `auth-service-cloudsql.yaml`):
```yaml
- name: cloud-sql-proxy
  image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.10.1
  args:
    - "--structured-logs"
    - "--port=5432"
    - "--address=0.0.0.0"
    - "--private-ip"
    - "alphintra-472817:us-central1:alphintra-db-instance"
  resources:
    requests:
      cpu: 10m
      memory: 32Mi
    limits:
      cpu: 100m
      memory: 128Mi
```

### Redis Caching

**Deployment**: In-cluster Redis (StatefulSet/Deployment)  
**Service**: `redis.alphintra.svc.cluster.local:6379`  
**Purpose**:
- Session management
- Rate limiter backend (service-gateway)
- Cache layer for frequently accessed data

**Future**: Migrate to Memorystore Redis for managed HA

### Time-Series Data (Planned)

**TimescaleDB**: Planned for market data (localhost:5433 in docs, not yet deployed)  
**Use Cases**: Historical price data, tick data, strategy backtesting

---

## Service Mesh & Traffic Management

### Istio Components

**Namespace**: `istio-system`

**Control Plane**:
- `istiod` (primary) - ClusterIP: `34.118.233.60`
- `istiod-asm-1172-1` (ASM) - ClusterIP: `34.118.232.245`

**Data Plane**:
- `istio-ingressgateway` (LoadBalancer)
  - External IP: `34.172.120.224`
  - Ports: `80, 443, 15021, 15012, 15443`

### Traffic Management

**Gateway Configuration** (`ingress-gateway.yaml`):
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: alphintra-ingress-gateway
spec:
  servers:
    - port: 80 (HTTP)
    - port: 443 (HTTPS/TLS)
  hosts:
    - "*.alphintra.dev"
    - "alphintra.com"
    - "api.alphintra.com"
```

**Virtual Service** (`virtualservice-gateway.yaml`):
- CORS enabled with credentials
- 3 retry attempts, 3s per-try timeout
- 30s total timeout
- Routes all traffic to `service-gateway:80`

**Destination Rules**:
- `destinationrule-auth.yaml` - mTLS and connection pooling for auth-service
- `destinationrule-gateway.yaml` - Gateway-specific traffic policies

### Canary Deployments

**Strategy**: Traffic splitting via VirtualService weights
**Example**:
```yaml
http:
  - route:
      - destination:
          host: service-gateway
          subset: stable
        weight: 80
      - destination:
          host: service-gateway
          subset: canary
        weight: 20
```

**Rollback**: Flip weights to 100/0 for stable subset

---

## CI/CD Pipeline

### Build Pipeline (Cloud Build)

**Trigger Mechanism**:
1. GitHub Actions workflows (`.github/workflows/cd-dev-*.yml`)
2. Direct Cloud Build triggers (limited to no-code-service)

**Build Process** (Example: auth-service):

```
Phase 1: Cache Restoration (120s timeout)
    ↓
    gsutil cp gs://{cache-bucket}/maven_cache.tar.gz → /root/.m2
    ↓
Phase 2: Parallel Build (300s timeout)
    ├─→ Package JAR (mvn clean package -DskipTests)
    └─→ Run Tests (mvn test)
    ↓
Phase 3: Docker Build & Push
    ↓
    docker build -t us-central1-docker.pkg.dev/.../auth-service:{sha}
    ↓
    docker push to Artifact Registry
    ↓
Phase 4: Update Cache (Non-blocking)
    ↓
    tar -czf /tmp/maven_cache.tar.gz /root/.m2
    ↓
    gsutil cp /tmp/maven_cache.tar.gz gs://{cache-bucket}/
```

**Machine Type**: `E2_HIGHCPU_8` (8 vCPU, 8 GB memory)  
**Target Build Time**: <60 seconds (Maven/Python cached builds)

### Deployment Pipeline

**GitHub Actions Workflow** (Example: `cd-dev-auth-service.yml`):

```yaml
1. Checkout code
2. Authenticate to GCP (service account key)
3. Submit build to Cloud Build
4. Configure kubectl
5. Deploy manifests (kubectl apply -k infra/kubernetes/environments/dev)
6. Verify deployment (kubectl rollout status)
```

**Deployment Target**:
- **Dev**: Automatic on push to `main` branch
- **Staging**: Tagged releases (`v*`)
- **Prod**: Manual promotion via ArgoCD

### GitOps (ArgoCD)

**Namespace**: `argocd`  
**Application**: `service-gateway-auth`

**Configuration** (`service-gateway-auth.yaml`):
```yaml
spec:
  source:
    repoURL: https://github.com/alphintra/platform.git
    targetRevision: main
    path: infra/kubernetes/environments/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: gateway
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**Sync Behavior**: Automated pruning and self-healing enabled

### Image Tagging Strategy

**Dev**: `latest` + `{git-sha}`  
**Staging/Prod**: Immutable tags (`v1.2.3`, `{git-sha}`)

**Kustomization** (per environment):
```yaml
images:
  - name: us-central1-docker.pkg.dev/alphintra-472817/alphintra/auth-service
    newTag: latest  # or specific version
```

---

## Observability & Monitoring

### Monitoring Stack

**Namespace**: `observability`

**Components**:
1. **Prometheus Operator** - Metrics collection
2. **Grafana** - Dashboard and visualization
3. **Alertmanager** - Alert routing and notifications
4. **OpenTelemetry Collector** (planned) - Distributed tracing

**Installation Method**: Helm (kube-prometheus-stack)

### Service Monitoring

**ServiceMonitors**:
- `servicemonitor-auth.yaml` - Auth service metrics
- `servicemonitor-gateway.yaml` - Gateway metrics

**Metrics Endpoints**:
- Spring Boot services: `/actuator/prometheus`
- FastAPI services: `/metrics` (Prometheus client)

### Dashboards

**Grafana Dashboards**:
- `grafana-dashboard-gateway.yaml` - Gateway request rate, latency (p50/p95/p99), error rate
- Custom dashboards for each service (to be added)

**Key Metrics**:
- Request rate (RPS)
- Latency percentiles (p50, p95, p99)
- Error rate (4xx, 5xx)
- Saturation (CPU, memory, connections)

### Alerting

**Alert Rules** (Planned):
- `GatewayLatencyHigh`: p95 > 750ms for 5 minutes
- `AuthErrorRateHigh`: 5xx rate > 2% for 10 minutes
- `PodCrashLooping`: CrashLoopBackOff status
- `HighMemoryUsage`: Memory > 90% for 15 minutes

**Notification Channels**: Email, PagerDuty (to be configured)

### Logging

**Structured Logging**:
- Format: JSON
- Fields: `service`, `level`, `timestamp`, `message`, `correlation-id`
- Destination: Google Cloud Logging

**Correlation IDs**: Injected by service-gateway, propagated across services

### Distributed Tracing (Planned)

**Tool**: OpenTelemetry + Cloud Trace / Jaeger  
**Sampling**: 100% in dev, 1-10% in prod  
**Span Propagation**: W3C Trace Context headers

---

## Deployment Strategy

### Environment Promotion Flow

```
Dev Environment
    ↓ (automatic on main branch)
GitHub Push → Cloud Build → Kubectl Apply
    ↓
    ↓ (tagged release v*)
Staging Environment
    ↓
ArgoCD Sync → Canary Deployment (20% traffic)
    ↓
    ↓ (validation: metrics + manual approval)
Production Environment
    ↓
ArgoCD Sync → Blue/Green or Canary
    ↓
Rollout Complete (100% traffic)
```

### Rollout Strategy

**Dev**:
- Strategy: `RollingUpdate`
- Max Unavailable: 0
- Max Surge: 1
- Replicas: 1

**Staging**:
- Strategy: Canary (20/80 split)
- Duration: 30 minutes
- Validation: Automated metrics + manual approval

**Prod**:
- Strategy: Canary or Blue/Green
- Traffic Split: 10/90 → 50/50 → 100/0
- Validation: SLO compliance (latency <600ms p95, error rate <1%)
- Duration: 2-4 hours

### Rollback Procedure

**Automated Rollback Triggers**:
- Error rate > 5% for 5 minutes
- Latency > 2s p95 for 5 minutes
- Pod crash loop

**Manual Rollback**:
```bash
kubectl rollout undo deployment/{service-name} -n alphintra
kubectl scale deploy/{service-name}-canary --replicas=0 -n alphintra
```

### Health Checks

**All Services**:
- **Readiness Probe**: `/actuator/health/readiness` (Spring Boot) or `/health` (FastAPI)
- **Liveness Probe**: `/actuator/health/liveness` (Spring Boot) or `/health` (FastAPI)
- **Startup Probe**: `/actuator/health` (longer timeout for initialization)

**Example** (auth-service):
```yaml
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8009
  initialDelaySeconds: 20
  periodSeconds: 10
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8009
  initialDelaySeconds: 30
  periodSeconds: 30
startupProbe:
  httpGet:
    path: /actuator/health
    port: 8009
  failureThreshold: 30
  periodSeconds: 10
```

---

## Disaster Recovery & High Availability

### High Availability Configuration

**GKE Cluster**:
- **Current**: Zonal (us-central1-a) - Single zone
- **Recommended**: Regional (us-central1) - Multi-zone for HA
- **Node Pools**: 2 pools (default + NAT backend)
- **Auto-Scaling**: Not yet configured (static 5 nodes)

**Services**:
- **Replicas**: 1 per service (dev), 2-3+ (staging/prod recommended)
- **HPA** (Horizontal Pod Autoscaler): Configured for service-gateway
  - Target CPU: 70%
  - Min Replicas: 1 (dev), 2 (prod)
  - Max Replicas: 5 (dev), 10 (prod)

**Cloud SQL**:
- **Current**: Single instance (no HA)
- **Recommended**: Enable HA with failover replica
- **Backups**: Automated daily backups (to be verified)

### Disaster Recovery

**Backup Strategy**:
- **Kubernetes Manifests**: Git repository (infra/kubernetes)
- **Secrets**: Secret Manager (automated backup)
- **Database**: Cloud SQL automated backups
- **Container Images**: Artifact Registry (immutable, versioned)

**RTO/RPO Targets** (to be formalized):
- **RTO** (Recovery Time Objective): <30 minutes
- **RPO** (Recovery Point Objective): <15 minutes (database)

**DR Procedures**:
1. **Database Restore**: Cloud SQL point-in-time recovery
2. **Cluster Recreation**: Terraform apply + kubectl apply
3. **Service Recovery**: ArgoCD re-sync or manual kubectl apply
4. **DNS Failover**: Update DNS to backup region (future)

### Multi-Region Strategy (Future)

**Planned**:
- **Primary Region**: us-central1
- **Secondary Region**: europe-west1 (Binance proxy already deployed here)
- **Global Load Balancer**: Cloud CDN + Cloud Armor
- **Data Replication**: Cloud SQL cross-region read replicas

---

## Infrastructure Management

### Terraform Modules

**Location**: `infra/terraform/modules/`

**Modules**:
1. **network** - VPC, subnets, firewall rules
2. **artifact-registry** - Container repositories
3. **cloudsql-database** - PostgreSQL instances and databases
4. **workload-identity** - GCP-to-K8s service account bindings

**Environments**: `infra/terraform/environments/{dev,staging,prod}/`

**State Management**: Terraform Cloud or GCS backend (to be configured)

### Kubernetes Configuration Management

**Tool**: Kustomize

**Structure**:
```
infra/kubernetes/
├── base/                    # Base manifests (Deployment, Service, etc.)
│   ├── auth-service/
│   ├── gateway/
│   └── redis.yaml
├── environments/            # Environment-specific overlays
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   ├── staging/
│   └── prod/
├── istio/                   # Istio mesh configuration
│   ├── base/
│   └── overlays/
└── observability/           # Monitoring stack
    └── base/
```

**Deployment Command**:
```bash
kubectl apply -k infra/kubernetes/environments/dev
```

### Secret Management

**Strategy**:
- **Development**: Kubernetes Secrets (base64-encoded)
- **Production**: Secret Manager + Workload Identity
- **Future**: Secret Store CSI Driver for automatic sync

**Secret Lifecycle**:
1. Store in Secret Manager
2. Grant `secretmanager.secretAccessor` to Workload Identity SA
3. Application reads via Secret Manager API or mounted volume

---

## Cost Optimization

**Current Optimizations**:
1. **Build Caching**: GCS buckets for Maven/Python/Node caches (reduces build time & cost)
2. **E2_HIGHCPU_8 Build Machines**: Fast builds (<60s) reduce Cloud Build minutes
3. **Preemptible Nodes**: Not yet enabled (consider for dev/staging)
4. **HPA**: Auto-scale pods based on CPU (reduce over-provisioning)

**Future Optimizations**:
1. **Spot VMs**: Use for non-critical workloads
2. **Committed Use Discounts**: 1-year or 3-year commitments for GKE/Cloud SQL
3. **Regional vs Zonal**: Regional GKE costs ~2x but provides HA
4. **Memorystore**: Right-size Redis tier (Basic vs Standard HA)
5. **Cloud CDN**: Cache static frontend assets, reduce egress costs

---

## Compliance & Governance

**Current State**: Development environment, no formal compliance

**Future Requirements** (for production):
- **SOC 2 Type II**: Audit logging, access controls, incident response
- **GDPR**: Data residency, right to deletion, consent management
- **PCI DSS** (if handling payment data): Encryption, network segmentation
- **Logging Retention**: 90 days (default), 1 year+ for compliance

**Audit Logging**:
- **GCP Audit Logs**: Admin activity, data access (to be enabled)
- **K8s Audit Logs**: API server audit policy (to be configured)
- **Application Logs**: Structured JSON logs with correlation IDs

---

## Troubleshooting & Operations

### Common Operations

**View Logs**:
```bash
# Service logs
kubectl logs -f deployment/auth-service -n alphintra

# Istio sidecar logs
kubectl logs deployment/auth-service -c istio-proxy -n alphintra

# Cloud SQL proxy logs
kubectl logs deployment/auth-service -c cloud-sql-proxy -n alphintra
```

**Check Service Health**:
```bash
# All services
kubectl get deployments -n alphintra

# Specific service
kubectl rollout status deployment/auth-service -n alphintra
kubectl get pods -l app=auth-service -n alphintra
```

**Verify Istio Configuration**:
```bash
# Check sidecar injection
kubectl get pods -n alphintra -o jsonpath='{.items[*].spec.containers[*].name}'

# Analyze Istio config
istioctl analyze -n alphintra

# Check proxy status
istioctl proxy-status
```

**Database Connection Test**:
```bash
# Port-forward to Cloud SQL proxy
kubectl port-forward deployment/auth-service 5432:5432 -n alphintra

# Connect with psql
psql -h localhost -U alphintra_user -d auth_db
```

**Restart Service**:
```bash
kubectl rollout restart deployment/auth-service -n alphintra
```

### Debugging Checklist

1. **Pod Not Starting**:
   - Check events: `kubectl describe pod {pod-name} -n alphintra`
   - Check logs: `kubectl logs {pod-name} -n alphintra`
   - Verify secrets exist: `kubectl get secrets -n alphintra`

2. **Service Unreachable**:
   - Check service: `kubectl get svc {service-name} -n alphintra`
   - Check endpoints: `kubectl get endpoints {service-name} -n alphintra`
   - Test from within cluster: `kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://{service-name}.alphintra.svc.cluster.local:{port}/actuator/health`

3. **High Latency**:
   - Check Grafana dashboards
   - Review Istio metrics: `istioctl dashboard prometheus`
   - Check database performance: Cloud SQL Insights

4. **mTLS Errors**:
   - Verify PeerAuthentication: `kubectl get peerauthentication -n alphintra`
   - Check certificate expiry: `kubectl get certificates -n istio-system`
   - Inspect Envoy logs: `kubectl logs {pod-name} -c istio-proxy -n alphintra`

---

## Roadmap & Future Enhancements

### Short-Term (1-3 months)
- [ ] Enable GKE regional cluster (multi-zone HA)
- [ ] Implement Cloud SQL HA with read replicas
- [ ] Configure Memorystore Redis (replace in-cluster Redis)
- [ ] Complete staging environment setup
- [ ] Enable auto-scaling for all services (HPA)
- [ ] Implement comprehensive alerting rules
- [ ] Set up distributed tracing (OpenTelemetry)

### Mid-Term (3-6 months)
- [ ] Migrate to dedicated VPCs per environment
- [ ] Implement Kafka for event streaming
- [ ] Deploy TimescaleDB for time-series data
- [ ] Implement Secret Store CSI Driver
- [ ] Set up multi-region DR (europe-west1)
- [ ] Enable Cloud Armor policies
- [ ] Implement cost optimization (spot VMs, committed use)

### Long-Term (6-12 months)
- [ ] Achieve SOC 2 Type II compliance
- [ ] Implement global multi-region active-active
- [ ] Move to Anthos for hybrid/multi-cloud
- [ ] Implement advanced observability (APM, RUM)
- [ ] Zero-downtime deployment with progressive delivery
- [ ] Chaos engineering and resilience testing

---

## References & Documentation

**Internal Documentation**:
- [Gateway Overview](../gateway/overview.md)
- [Auth Service Runbook](../auth-service-runbook.md)
- [Istio Rollout Plan](../mesh/istio-rollout.md)
- [Observability Stack](../observability/README.md)
- [Rollout Strategy](rollout-strategy.md)
- [Prerequisites](prerequisites.md)
- [Cloud Baseline](cloud-baseline.md)

**External Resources**:
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Istio Documentation](https://istio.io/latest/docs/)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Spring Cloud Gateway](https://spring.io/projects/spring-cloud-gateway)

---

## Appendix

### A. GCP APIs Enabled

```
artifactregistry.googleapis.com
compute.googleapis.com
container.googleapis.com
containerregistry.googleapis.com
logging.googleapis.com
monitoring.googleapis.com
redis.googleapis.com
sqladmin.googleapis.com
secretmanager.googleapis.com
```

### B. Service Port Mapping

| Service | Internal Port | External Port (via Ingress) |
|---------|---------------|----------------------------|
| service-gateway | 8080 | 80/443 (HTTPS) |
| auth-service | 8009 | N/A (internal only) |
| trading-engine | 8008 | N/A |
| wallet-service | 8011 | N/A |
| marketplace-service | 8200 | N/A |
| ai-ml-strategy-service | 8002 | N/A |
| no-code-service | 8006 | N/A |
| customer-support-service | 8010/8011 | N/A |
| redis | 6379 | N/A |
| frontend-app | 3000 | 80/443 (separate ingress) |

### C. kubectl Quick Reference

```bash
# Set default namespace
kubectl config set-context --current --namespace=alphintra

# Get all resources
kubectl get all -n alphintra

# Describe resource
kubectl describe {resource-type} {resource-name} -n alphintra

# Exec into pod
kubectl exec -it {pod-name} -n alphintra -- /bin/bash

# Port-forward service
kubectl port-forward svc/{service-name} {local-port}:{remote-port} -n alphintra

# View events
kubectl get events -n alphintra --sort-by='.lastTimestamp'

# Apply kustomization
kubectl apply -k infra/kubernetes/environments/dev

# Diff before apply
kubectl diff -k infra/kubernetes/environments/dev
```

### D. gcloud Quick Reference

```bash
# Set project
gcloud config set project alphintra-472817

# Get cluster credentials
gcloud container clusters get-credentials alphintra-cluster --zone us-central1-a

# List resources
gcloud compute instances list
gcloud sql instances list
gcloud artifacts repositories list

# Submit build
gcloud builds submit --config=cloudbuild.yaml --substitutions=_COMMIT_SHA=$(git rev-parse HEAD)

# View logs
gcloud logging read "resource.type=k8s_container AND resource.labels.container_name=auth-service" --limit 50 --format json
```

---

**Document Version**: 1.0  
**Last Updated**: November 4, 2025  
**Maintained By**: Alphintra Platform Team  
**Review Frequency**: Monthly
