# Deployment Prerequisites

This checklist consolidates the minimum Google Cloud resources and IAM grants required before deploying the Alphintra gateway and auth services. It aligns with the Terraform modules under `infra/terraform`.

## 1. Core Infrastructure

- Dedicated VPC per environment (`alphintra-{dev,staging,prod}-vpc`) with subnet CIDR ranges reserved for GKE (`pods`, `services`) and private access enabled.
- Cloud NAT attached to each environment subnet if workloads need outbound internet access (configure once GKE cluster is provisioned).
- Firewall rules:
  - Allow internal traffic within the VPC CIDR blocks.
  - Permit health checks from Google Load Balancer (`130.211.0.0/22`, `35.191.0.0/16`).
  - Restrict SSH/RDP to break-glass accounts only.
- Cloud Armor policies created per environment (attach to Istio ingress via NEG) to enforce IP allow-lists and rate limiting at the edge.
- Existing Kubernetes namespace `alphintra` is reused for auth-service and service-gateway; ensure RBAC and quotas are configured there.

## 2. Artifact Registry

- Regional Docker repositories:
  - `alphintra-dev` (`us-central1`)
  - `alphintra-staging` (`us-central1`)
  - `alphintra-prod` (`us-central1`)
- Enable vulnerability scanning (`artifactregistry.googleapis.com` + `containerscanning.googleapis.com`).
- Grant the CI service account `roles/artifactregistry.writer`.

## 3. Workload Identity & Service Accounts

- Google service accounts (created via Terraform):
  - `auth-cloudsql-{dev,stg,prd}` with roles:
    - `roles/cloudsql.client`
    - `roles/secretmanager.secretAccessor`
    - `roles/logging.logWriter`
  - `gateway-runtime-{dev,stg,prd}` with roles:
    - `roles/monitoring.metricWriter`
    - `roles/cloudtrace.agent`
    - `roles/logging.logWriter`
- Map the above to Kubernetes service accounts (`auth-service/auth-service`, `gateway/gateway`) using Workload Identity.
- Ensure the GKE cluster is created with Workload Identity enabled (`--workload-pool=alphintra-472817.svc.id.goog`).

## 4. Cloud SQL & Memorystore

- PostgreSQL instance `alphintra-db-instance` (us-central1) with IAM DB Authentication enabled.
- Read replica (optional) for staging/prod once load testing starts.
- Memorystore instances per environment (to be created) sized according to gateway rate limiting expectations; reserve `10.64.0.0/24` ranges for Redis VPC peering.

## 5. Cloud Build & GitHub Actions

- Create a Cloud Storage bucket `gs://alphintra-build-artifacts` for build logs (optional; defaults work without it).
- Configure GitHub OIDC Workload Identity Federation with:
  - Provider ID (`secrets.GCP_WORKLOAD_IDENTITY_PROVIDER`)
  - Service account email (`secrets.GCP_SERVICE_ACCOUNT`)
- Grant Cloud Build SA `roles/cloudbuild.builds.editor`, `roles/run.admin` (if deploying to Cloud Run), and `roles/container.admin` (for GKE deploy).
- Add `_COMMIT_SHA` substitution to Cloud Build triggers that target `auth-service` (and later `service-gateway`).

## 6. Secret Management

- Provision Secret Manager secrets for:
  - `AUTH_JWT_SECRET`
  - `AUTH_DB_PASSWORD`
  - `GATEWAY_JWT_PUBLIC_KEY`
  - `REDIS_URL` (per environment)
- Assign the corresponding Workload Identity accounts `roles/secretmanager.secretAccessor`.
- Plan Config Connector or Secret Store CSI driver for syncing into Kubernetes.

## 7. Observability Tooling

- Enable APIs: `monitoring.googleapis.com`, `logging.googleapis.com`, `cloudtrace.googleapis.com`, `cloudprofiler.googleapis.com`.
- Reserve namespaces in Kubernetes for system components: `istio-system`, `observability`, `gateway`, `auth-service`.
- Set up Cloud Monitoring notification channels (email, PagerDuty) before alert policies go live.

Keep this document updated as new dependencies (e.g., Cloud Armor, Memorystore) are introduced in later phases.
