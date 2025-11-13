# Alphintra Cloud Architecture - Quick Reference

This document provides a quick reference summary of the Alphintra platform's cloud architecture.

---

## 📋 Quick Facts

| Attribute | Value |
|-----------|-------|
| **Cloud Provider** | Google Cloud Platform (GCP) |
| **Project ID** | `alphintra-472817` |
| **Project Number** | `999709622705` |
| **Primary Region** | `us-central1` |
| **Secondary Region** | `europe-west1` (for trading egress) |
| **Kubernetes Version** | 1.33.5-gke.1080000 |
| **Service Mesh** | Istio (ASM 1.17.2) |
| **Total Services** | 9 microservices + frontend |
| **Total Nodes** | 5 (3 default + 2 NAT pool) |

---

## 🌐 Access Points

### External Access
- **Main Ingress**: `34.172.120.224` (Istio Gateway)
- **Production Domain**: `alphintra.com`, `api.alphintra.com`
- **Dev Domain**: `*.alphintra.dev`

### Internal Services
- **GKE Cluster**: `alphintra-cluster` (us-central1-a)
- **Cloud SQL**: `alphintra-db-instance` (10.6.124.3)
- **Redis**: In-cluster (34.118.237.57)

---

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────────┐
│  Internet / Users                       │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  Edge Layer                             │
│  • Cloud Load Balancer (34.172.120.224)│
│  • Cloud Armor (DDoS Protection)       │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  Service Mesh Layer (Istio)            │
│  • Ingress Gateway (:80, :443, :15443) │
│  • mTLS between all services           │
│  • JWT validation                       │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  API Gateway Layer                      │
│  • service-gateway (:8080)             │
│  • Rate limiting (Redis)                │
│  • Request routing                      │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  Microservices Layer                    │
│  • auth-service (:8009)                │
│  • trading-engine (:8008)              │
│  • wallet-service (:8011)              │
│  • marketplace-service (:8200)         │
│  • ai-ml-strategy-service (:8002)      │
│  • no-code-service (:8006)             │
│  • customer-support-service (:8010)    │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  Data Layer                             │
│  • Cloud SQL PostgreSQL (10.6.124.3)   │
│  • Redis Cache (34.118.237.57)         │
└─────────────────────────────────────────┘
```

---

## 🔐 Security Overview

### Authentication & Authorization
- **Method**: JWT (HMAC-SHA256)
- **Issuer**: auth-service
- **Validation**: Istio RequestAuthentication + service-gateway
- **Storage**: Secret Manager

### Network Security
- **mTLS**: Strict mode (PeerAuthentication)
- **Firewall**: GCP firewall rules + Istio AuthorizationPolicy
- **Cloud SQL**: Private IP only (10.6.124.0/24)
- **Egress**: NAT Gateway (34.134.209.61)

### Identity & Access
- **Workload Identity**: Enabled (alphintra-472817.svc.id.goog)
- **Service Accounts**: Per-service GCP SA mapped to K8s SA
- **IAM Roles**: Least-privilege (cloudsql.client, secretmanager.secretAccessor)

---

## 📦 Service Inventory

| Service | Type | Port | Language | Purpose |
|---------|------|------|----------|---------|
| **service-gateway** | API Gateway | 8080 | Spring Cloud Gateway | Rate limiting, routing, JWT |
| **auth-service** | Backend | 8009 | Spring Boot | Authentication, Stripe billing |
| **trading-engine** | Backend | 8008 | Spring Boot | Order execution |
| **wallet-service** | Backend | 8011 | Spring Boot | Digital wallet |
| **marketplace-service** | Backend | 8200 | Spring Boot | Strategy marketplace |
| **customer-support** | Backend | 8010/8011 | Spring Boot | Support tickets |
| **ai-ml-strategy** | Backend | 8002 | FastAPI (Python) | AI/ML strategies |
| **no-code-service** | Backend | 8006 | FastAPI (Python) | Visual workflows |
| **redis** | Cache | 6379 | Redis | Session cache |
| **frontend-app** | Frontend | 3000 | Next.js | Web UI |

---

## 💾 Data Stores

### Cloud SQL (PostgreSQL 15)
- **Instance**: `alphintra-db-instance`
- **IP**: 10.6.124.3 (private)
- **Region**: us-central1
- **Connection**: Cloud SQL Proxy sidecar
- **Databases**:
  - `auth_db` - User authentication
  - `wallet_db` - Wallet transactions
  - `trading_db` - Order history
  - `customer_support_db` - Support tickets

### Redis
- **Type**: In-cluster deployment
- **Service IP**: 34.118.237.57
- **Port**: 6379
- **Use Cases**: Rate limiting, session cache
- **Future**: Migrate to Memorystore

---

## 🚀 CI/CD Pipeline

### Build Process
```
Developer Push → GitHub → GitHub Actions
    ↓
Cloud Build (E2_HIGHCPU_8)
    ↓
1. Restore Cache (GCS: gs://alphintra-*-cache)
2. Build (Maven/Python parallel)
3. Docker Build & Push (Artifact Registry)
4. Update Cache (GCS)
    ↓
Artifact Registry (us-central1-docker.pkg.dev)
```

### Deployment Flow
```
Dev: Push to main → Auto-deploy (kubectl apply)
Staging: Tag v* → ArgoCD sync → Canary (20%)
Prod: Manual promotion → ArgoCD sync → Blue/Green
```

### Build Times
- **Target**: <60 seconds (with cache)
- **Machine**: E2_HIGHCPU_8 (8 vCPU, 8 GB)
- **Optimization**: Maven/Python/Node cache in GCS

---

## 📊 Observability

### Metrics
- **Tool**: Prometheus + Grafana
- **Namespace**: `observability`
- **ServiceMonitors**: auth-service, service-gateway
- **Dashboards**: Gateway overview (RPS, latency, errors)

### Logging
- **Format**: JSON structured logs
- **Destination**: Cloud Logging
- **Fields**: service, level, timestamp, correlation-id

### Tracing (Planned)
- **Tool**: OpenTelemetry + Cloud Trace
- **Sampling**: 100% dev, 1-10% prod

### Alerts (Planned)
- Gateway latency > 750ms (5 min)
- Auth error rate > 2% (10 min)
- Pod crash loop
- High memory usage > 90% (15 min)

---

## 🌍 Network Configuration

### VPC & Subnets
- **Primary VPC**: `default` (auto-mode)
- **Node Subnet**: 10.128.0.0/20 (us-central1)
- **Pod Network**: 10.32.0.0/14 (secondary range)
- **Service CIDR**: 34.118.224.0/20 (GKE managed)

### External IPs
| Name | IP | Purpose |
|------|-----|---------|
| Istio Ingress | 34.172.120.224 | Main entry point |
| NAT Gateway | 34.134.209.61 | Outbound traffic |
| Binance Proxy EU | 34.38.218.227 | Binance API calls |
| Trading Egress EU | 34.78.35.4 | Trading API calls |

### Firewall Rules
- `allow-web-traffic`: 0.0.0.0/0 → :80,:443
- `allow-gclb-health-checks`: 35.191.0.0/16, 130.211.0.0/22 → :31712
- `default-allow-internal`: 10.128.0.0/9 → All protocols
- `gke-alphintra-cluster-*`: Pod-to-pod communication

---

## 📁 Repository Structure

```
Alphintra/
├── infra/
│   ├── terraform/                   # Infrastructure as Code
│   │   ├── modules/                 # Reusable modules
│   │   │   ├── network/
│   │   │   ├── artifact-registry/
│   │   │   ├── cloudsql-database/
│   │   │   └── workload-identity/
│   │   └── environments/            # Per-environment config
│   │       ├── dev/
│   │       ├── staging/
│   │       └── prod/
│   ├── kubernetes/                  # K8s manifests
│   │   ├── base/                    # Base deployments
│   │   │   ├── auth-service/
│   │   │   ├── gateway/
│   │   │   └── redis.yaml
│   │   ├── environments/            # Kustomize overlays
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   ├── istio/                   # Service mesh config
│   │   │   ├── base/
│   │   │   └── overlays/
│   │   └── observability/           # Monitoring stack
│   ├── gitops/
│   │   └── argocd/                  # ArgoCD applications
│   └── scripts/                     # Deployment scripts
├── src/
│   ├── backend/                     # Microservices
│   │   ├── auth-service/
│   │   ├── service-gateway/
│   │   ├── trading-engine/
│   │   ├── ai-ml-strategy-service/
│   │   └── ...
│   └── frontend/                    # Next.js app
├── .github/
│   └── workflows/                   # CI/CD pipelines
└── docs/
    └── deployment/                  # Architecture docs
```

---

## 🛠️ Common Operations

### View Service Status
```bash
kubectl get deployments -n alphintra
kubectl get pods -l app=auth-service -n alphintra
kubectl rollout status deployment/auth-service -n alphintra
```

### View Logs
```bash
kubectl logs -f deployment/auth-service -n alphintra
kubectl logs deployment/auth-service -c istio-proxy -n alphintra
```

### Deploy Changes
```bash
# Dev environment
kubectl apply -k infra/kubernetes/environments/dev

# Production (via ArgoCD)
# Update infra/gitops/argocd/service-gateway-auth.yaml
git push origin main
```

### Restart Service
```bash
kubectl rollout restart deployment/auth-service -n alphintra
```

### Port Forward
```bash
# Access service locally
kubectl port-forward svc/service-gateway 8080:80 -n alphintra

# Access Grafana
kubectl port-forward svc/monitoring-grafana 3000:80 -n observability
```

### Check Istio Config
```bash
istioctl proxy-status
istioctl analyze -n alphintra
kubectl get gateway,virtualservice -n istio-system
```

### Database Access
```bash
# Via Cloud SQL proxy
kubectl port-forward deployment/auth-service 5432:5432 -n alphintra
psql -h localhost -U alphintra_user -d auth_db
```

---

## 📈 Capacity & Scaling

### Current Configuration (Dev)
- **Node Pool**: 5 nodes (3 e2-medium + 2 e2-standard-2)
- **Service Replicas**: 1 per service
- **HPA**: Configured for service-gateway only

### Production Recommendations
- **GKE**: Regional cluster (3 zones)
- **Node Pool**: 6-12 nodes (e2-standard-4 or n2-standard-4)
- **Service Replicas**: 2-3 minimum per service
- **HPA**: All services with CPU/memory targets
- **Cloud SQL**: HA with read replicas
- **Redis**: Memorystore Standard tier

### Auto-Scaling Targets
- **service-gateway**: Min 2, Max 10, Target CPU 70%
- **auth-service**: Min 2, Max 5, Target CPU 70%
- **trading-engine**: Min 2, Max 8, Target CPU 60%

---

## 💰 Cost Breakdown (Estimated)

### Current Dev Environment
| Component | Estimated Monthly Cost |
|-----------|----------------------|
| GKE Cluster (5 nodes) | ~$250 |
| Cloud SQL (single instance) | ~$100 |
| Artifact Registry | ~$10 |
| Cloud Storage (caches) | ~$5 |
| Load Balancer | ~$20 |
| Cloud Build (100 builds/month) | ~$10 |
| **Total** | **~$395/month** |

### Production Environment (Estimated)
| Component | Estimated Monthly Cost |
|-----------|----------------------|
| GKE Regional Cluster (12 nodes) | ~$800 |
| Cloud SQL HA + replicas | ~$400 |
| Memorystore Redis (Standard HA) | ~$150 |
| Artifact Registry | ~$30 |
| Cloud CDN + Armor | ~$100 |
| Load Balancer (regional) | ~$50 |
| Cloud Build (500 builds/month) | ~$50 |
| Egress (5 TB) | ~$200 |
| **Total** | **~$1,780/month** |

**Note**: Actual costs vary based on usage. Consider committed use discounts for 30-40% savings.

---

## 🔄 Disaster Recovery

### Current State
- **Backups**: Cloud SQL automated daily backups
- **RTO**: ~30 minutes (manual recovery)
- **RPO**: ~15 minutes (database)
- **HA**: Single-zone (not production-ready)

### Production Plan
- **GKE**: Regional cluster (3 zones)
- **Cloud SQL**: HA with automatic failover
- **Backups**: Point-in-time recovery (7 days)
- **Multi-Region**: DR replica in europe-west1
- **RTO Target**: <5 minutes
- **RPO Target**: <1 minute

---

## 📞 Troubleshooting Contacts

### Quick Diagnostics
```bash
# Check cluster health
gcloud container clusters describe alphintra-cluster --zone us-central1-a

# Check service health
kubectl get componentstatuses
kubectl get nodes
kubectl top nodes
kubectl top pods -n alphintra

# Check recent events
kubectl get events -n alphintra --sort-by='.lastTimestamp' | tail -20

# Check Istio health
kubectl get pods -n istio-system
istioctl version

# Check Cloud SQL connectivity
gcloud sql instances describe alphintra-db-instance
```

### Common Issues

**Pod Not Starting**
1. `kubectl describe pod <pod-name> -n alphintra`
2. Check events for image pull errors
3. Verify secrets exist: `kubectl get secrets -n alphintra`
4. Check resource limits

**Service Unreachable**
1. Verify service exists: `kubectl get svc <service-name> -n alphintra`
2. Check endpoints: `kubectl get endpoints <service-name> -n alphintra`
3. Test internal DNS: `kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://<service>.alphintra.svc.cluster.local:<port>`

**Database Connection Issues**
1. Check Cloud SQL proxy logs: `kubectl logs <pod> -c cloud-sql-proxy -n alphintra`
2. Verify Workload Identity: `kubectl get sa <service-account> -n alphintra -o yaml`
3. Test connection: `gcloud sql connect alphintra-db-instance --user=postgres`

**High Latency**
1. Check Grafana dashboards
2. Review service logs for slow queries
3. Check Istio metrics: `istioctl dashboard prometheus`
4. Verify HPA status: `kubectl get hpa -n alphintra`

---

## 📚 Documentation Links

### Internal Docs
- [Full Architecture Document](./CLOUD_ARCHITECTURE.md)
- [Architecture Diagrams](./ARCHITECTURE_DIAGRAMS.md)
- [Gateway Overview](../gateway/overview.md)
- [Istio Rollout Plan](../mesh/istio-rollout.md)
- [Observability Stack](../observability/README.md)

### External Resources
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [Istio Documentation](https://istio.io/latest/docs/)
- [Spring Cloud Gateway Docs](https://spring.io/projects/spring-cloud-gateway)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

---

## 🗺️ Roadmap Snapshot

### Q1 2025
- ✅ Deploy dev environment on GKE
- ✅ Implement Istio service mesh
- ✅ Set up CI/CD with Cloud Build
- ✅ Deploy 9 core services
- 🔄 Complete observability stack
- 🔄 Implement comprehensive monitoring

### Q2 2025
- 📋 Launch staging environment
- 📋 Enable GKE regional cluster
- 📋 Implement Cloud SQL HA
- 📋 Deploy Memorystore Redis
- 📋 Complete security audit

### Q3 2025
- 📋 Launch production environment
- 📋 Multi-region DR setup
- 📋 SOC 2 Type II compliance
- 📋 Performance optimization

**Legend**: ✅ Complete | 🔄 In Progress | 📋 Planned

---

**Document Version**: 1.0  
**Last Updated**: November 4, 2025  
**Next Review**: December 4, 2025
