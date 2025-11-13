# Alphintra Platform - Cloud Architecture Diagram

This document captures the deployed architecture of the Alphintra platform on Google Cloud Platform. The topology was cross-checked against the source tree under `infra/` and the active GCP project `alphintra-472817` via `gcloud`/`kubectl` on 2025-11-05.

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "External"
        Users[Users / Clients]
        Providers[External Providers\nStripe, Binance, Email/KYC APIs]
    end

    subgraph "GCP Project alphintra-472817"
        subgraph "Edge Layer"
            FrontLB[HTTPS Load Balancer\nalphintra.com · 34.98.73.110]
            IstioLB[Istio IngressGateway\napi.alphintra.com · 34.172.120.224]
        end

        subgraph "GKE Cluster - alphintra-cluster\nus-central1-a · GKE 1.33.5"
            subgraph "default namespace"
                Frontend[frontend-app\nNext.js · Port 3000]
            end
            subgraph "alphintra namespace"
                Gateway[service-gateway\nSpring Boot · Port 8080]
                Auth[auth-service\nSpring Boot · Port 8009]
                Trading[trading-engine\nSpring Boot · Port 8008]
                Wallet[wallet-service\nSpring Boot · Port 8011]
                Marketplace[marketplace-service\nFastAPI · Port 8200]
                NoCode[no-code-service\nNode · Port 8006]
                AIML[ai-ml-strategy-service\nPython · Port 8002]
                Support[customer-support-service\nSpring Boot · Ports 8010/8011]
                Redis[Redis Deployment\nIn-cluster Cache · 6379]
            end
        end

        CloudSQL[(Cloud SQL Postgres 15\nalphintra-db-instance · 10.6.124.3)]
        Registry[Container Registry & Artifact Registry]
        Secrets[Secret Manager]
        CloudBuild[Cloud Build Pipelines]
        Observability[Cloud Logging & Managed Prometheus]
        CloudNAT[Cloud NAT · 34.134.209.61]
    end

    Users -->|HTTPS alphintra.com| FrontLB --> Frontend
    Frontend -->|API calls https://api.alphintra.com| IstioLB --> Gateway
    Gateway --> Auth
    Gateway --> Trading
    Gateway --> Wallet
    Gateway --> Marketplace
    Gateway --> NoCode
    Gateway --> AIML
    Gateway --> Support
    Gateway --> Redis
    Auth -.->|Cloud SQL Proxy| CloudSQL
    Trading -.->|Cloud SQL Proxy| CloudSQL
    Wallet -.->|Cloud SQL Proxy| CloudSQL
    Marketplace -.->|Cloud SQL Proxy| CloudSQL
    AIML -.->|Cloud SQL Proxy| CloudSQL
    NoCode -.->|Cloud SQL Proxy| CloudSQL
    Support -.->|Cloud SQL Proxy| CloudSQL
    CloudBuild --> Registry
    Registry -->|Images| Gateway
    Registry -->|Images| Frontend
    Registry -->|Images| Trading
    Secrets --> Auth
    Secrets --> Gateway
    Trading -->|Egress via NAT| CloudNAT --> Providers
    AIML -->|Egress via NAT| CloudNAT
```

- Production workloads run in the `alphintra` namespace; only the UI lives in `default`.
- Every backend pod (except `service-gateway`) embeds a Cloud SQL proxy sidecar for private-IP connectivity to the shared PostgreSQL instance.
- Container images are published to both `gcr.io/alphintra-472817/*` (legacy) and `us-central1-docker.pkg.dev/alphintra-472817/alphintra/*`.

---

## 2. Network & Access Topology

```mermaid
graph TB
    subgraph Internet
        Client[Client Browser / Mobile]
        MarketAPIs[External Market APIs]
    end

    subgraph "default VPC · 10.128.0.0/20"
        subgraph "Node Subnet"
            Node1[GKE node\n10.128.0.39 · e2-medium]
            Node2[GKE node\n10.128.0.41 · e2-medium]
            Node3[GKE node\n10.128.0.42 · e2-medium]
            Node4[NAT node\n10.128.0.43 · e2-standard-2]
            Node5[NAT node\n10.128.0.44 · e2-standard-2]
        end

        subgraph "Pod CIDR 10.32.0.0/14"
            GatewayPod[service-gateway Pod\n10.32.x.x]
            AuthPod[auth-service Pod\n10.32.x.x]
            TradingPod[trading-engine Pod\n10.32.x.x]
            OtherPods[Other backend pods\n10.32.x.x]
        end

        subgraph "Service CIDR 34.118.224.0/20"
            GatewaySvc[service-gateway · 34.118.237.137]
            AuthSvc[auth-service · 34.118.230.101]
            RedisSvc[redis · 34.118.237.57]
            FrontSvc[frontend-app · 34.118.228.160]
        end

        CloudNAT[Cloud NAT · 34.134.209.61]
    end

    HTTPSLB[HTTPS LB · 34.98.73.110] --> FrontSvc --> FrontendNode[frontend-app Pod]
    Client -->|HTTPS 443| HTTPSLB
    Client -->|HTTPS 443| IstioLB[Istio ingressgateway · 34.172.120.224]
    IstioLB --> GatewaySvc --> GatewayPod
    GatewayPod --> CloudNAT --> MarketAPIs
```

- The running cluster is attached to the Google-managed `default` VPC; the Terraform-created `alphintra-dev-vpc` is not in use.
- Istio components are installed for the ingress gateway, but namespaces are not labeled for sidecar injection, so in-cluster service traffic is plain HTTP.
- Outbound Internet access flows through Cloud NAT; the reserved static IPs `binance-proxy-eu` and `trading-egress-eu` are not currently bound to resources.

---

## 3. End-to-End Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant GCLB as HTTPS Load Balancer
    participant Frontend as frontend-app (Next.js)
    participant APILB as Istio IngressGateway
    participant Gateway as service-gateway
    participant Redis
    participant Auth as auth-service
    participant Trading as trading-engine
    participant SQL as Cloud SQL (Postgres)
    participant NAT as Cloud NAT
    participant Market as External APIs

    Client->>GCLB: HTTPS GET alphintra.com
    GCLB->>Frontend: Forward via NEG (port 3000)
    Frontend->>Client: SSR/Static assets
    Client->>APILB: HTTPS api.alphintra.com
    APILB->>Gateway: HTTP 8080
    Gateway->>Redis: Rate-limit & session lookup
    alt Authentication
        Gateway->>Auth: /api/auth/*
        Auth->>SQL: Query alphintra_auth_service
        SQL-->>Auth: User record
        Auth-->>Gateway: JWT / status
    end
    alt Trading action
        Gateway->>Trading: /api/trading/*
        Trading->>SQL: Read/Write alphintra_trading_engine
        SQL-->>Trading: Portfolio / order data
        Trading->>NAT: Outbound HTTPS
        NAT->>Market: Binance / market API
        Market-->>NAT: Execution result
        NAT-->>Trading: Response
    end
    Gateway-->>APILB: JSON payload
    APILB-->>Client: API response
```

- Service-to-service calls are HTTP within the cluster; request authentication is enforced at the gateway rather than through Istio AuthorizationPolicies.
- Each workload reaches Cloud SQL through a sidecar proxy bound to `127.0.0.1:5432`, using private IP connectivity.

---

## 4. Backend Service Relationships

```mermaid
graph LR
    Gateway[service-gateway]
    Auth[auth-service]
    Trading[trading-engine]
    Wallet[wallet-service]
    Marketplace[marketplace-service]
    NoCode[no-code-service]
    AIML[ai-ml-strategy-service]
    Support[customer-support-service]
    Redis[(Redis Deployment\nalphintra namespace)]
    subgraph "Cloud SQL databases (alphintra-db-instance)"
        AuthDB[(alphintra_auth_service)]
        TradingDB[(alphintra_trading_engine)]
        WalletDB[(alphintra_wallet_service)]
        MarketDB[(alphintra_market_place)]
        NoCodeDB[(alphintra_nocode)]
        AIMLDB[(alphintra_ai_ml_strategy_service)]
        SupportDB[(alphintra_customer_support)]
    end

    Gateway --> Auth
    Gateway --> Trading
    Gateway --> Wallet
    Gateway --> Marketplace
    Gateway --> NoCode
    Gateway --> AIML
    Gateway --> Support
    Gateway --> Redis
    Auth -.-> AuthDB
    Trading -.-> TradingDB
    Wallet -.-> WalletDB
    Marketplace -.-> MarketDB
    NoCode -.-> NoCodeDB
    AIML -.-> AIMLDB
    Support -.-> SupportDB
```

- `service-gateway` fronts all public endpoints and reaches downstream services via the cluster DNS entries configured in `service-gateway-config`.
- Redis runs as an in-cluster Deployment with an `emptyDir` volume; there is no managed Memorystore instance yet.
- Workload Identity is enabled for selected service accounts (`auth-service`, `no-code-service`, etc.); others still depend on secrets for GCP access.

---

## 5. Observability & Operations

```mermaid
graph TB
    subgraph "In-cluster telemetry"
        GatewayLogs[service-gateway logs]
        TradingMetrics[Prometheus annotations\n(trading-engine, ai-ml, etc.)]
        CloudSQLProxyLogs[Cloud SQL proxy logs]
    end

    subgraph "Google Managed Services"
        Logging[Cloud Logging]
        GMP[Google Managed Prometheus\n(gmp-system collectors)]
        Monitoring[Cloud Monitoring]
    end

    subgraph "Alerting"
        Email[Email / PagerDuty (planned)]
    end

    GatewayLogs --> Logging
    CloudSQLProxyLogs --> Logging
    TradingMetrics --> GMP --> Monitoring
    Logging --> Monitoring
    Monitoring --> Email
```

- Google Managed Prometheus collectors (`gmp-system`) are active; no self-hosted Prometheus/Grafana stack is deployed despite manifests for one.
- The `observability` namespace, OpenTelemetry collector, and Grafana dashboards in the repository are not applied to the cluster.
- Cert-manager is issuing TLS for `api.alphintra.com`; the NGINX ingress described in manifests is absent, leaving only the GCE/NEG ingress path.

---

## 6. CI/CD Pipeline

```mermaid
graph LR
    Dev[Developer Commit / PR]
    GitHub[GitHub Repository\nalphintra/platform]
    Actions[GitHub Actions\n(cd-dev-*.yml)]
    CloudBuild[Cloud Build\nservice cloudbuild.yaml]
    Registry[gcr.io & Artifact Registry]
    Kustomize[kubectl apply -k infra/kubernetes/environments/dev]
    GKE[alphintra-cluster (GKE)]
    Namespace[alphintra namespace]

    Dev --> GitHub --> Actions --> CloudBuild
    CloudBuild --> Registry
    CloudBuild --> Kustomize --> GKE --> Namespace
```

- Dev/staging deployments rely on GitHub Actions invoking Cloud Build, which builds and pushes images before applying manifests with Kustomize.
- The blue/green deployment logic and ArgoCD GitOps flow described in earlier docs are not implemented in the current workflows.
- Production releases are triggered manually through `workflow_dispatch`; there is no automated canary or traffic-shifting stage.

---

## 7. Infrastructure as Code Coverage

```mermaid
graph TB
    subgraph "Terraform (infra/terraform)"
        DevEnv[environments/dev]
        Modules[modules/*]
    end
    Modules --> Network[VPC alphintra-dev-vpc]
    Modules --> Subnet[dev-apps-subnet]
    Modules --> Artifact[Artifact Registry alphintra-dev]
    Modules --> CloudSQL[(Cloud SQL alphintra-db-instance)]
    Modules --> WorkloadID[Workload Identity bindings]
    DevEnv --> Modules
```

- Terraform provisions the supporting VPC, Artifact Registry, Cloud SQL database, and Workload Identity bindings but does **not** manage the running GKE cluster.
- The live workloads remain on the `default` VPC; applying Terraform changes will not touch current cluster networking until the cluster is re-homed.

---

## 8. Known Gaps & Follow-ups

- Istio sidecar injection is not enabled for `alphintra`, so mTLS and AuthorizationPolicies defined under `infra/kubernetes/istio` are currently ineffective.
- No NetworkPolicies are deployed; intra-cluster traffic is fully open.
- The `alphintra-dev` namespace contains only a dormant `wallet-service` Service with no backing pods—verify whether it is still required.
- Observability manifests (Prometheus/Grafana/Alertmanager, OpenTelemetry collector) are present in the repo but not applied to the cluster.
- Reserved IPs `binance-proxy-eu` and `trading-egress-eu` have no forwarding rules or instances attached yet.
- Redis runs as a single-pod Deployment with a hard-coded password and `emptyDir` volume; consider migrating to Memorystore for production reliability.
