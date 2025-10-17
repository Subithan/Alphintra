# Auth Service Runbook

## Overview

The auth service issues and validates JWT tokens, manages user profiles/KYC metadata, and serves `/api/auth`, `/api/users`, and `/api/kyc` routes. It is a Spring Boot 3 application with Flyway migrations and structured JSON logging.

## Deployments

- **Images**: `us-central1-docker.pkg.dev/alphintra-472817/alphintra/auth-service:<tag>` (built by Cloud Build via `cloudbuild.yaml`).
- **Kubernetes**: Base manifests under `infra/kubernetes/base/auth-service`; overlays for each environment reside in `infra/kubernetes/environments/{dev,staging,prod}`.
- **Service account**: Pods run as `auth-service` ServiceAccount with Workload Identity bindings to access Cloud SQL/Secret Manager.
- **Mesh**: Namespace is labelled for Istio injection; mTLS and JWT guardrails are defined under `infra/kubernetes/istio/base`.
- **Namespace**: Deploy into the existing `alphintra` namespace – no additional namespaces are created by the overlays.
- **Bootstrap**: Follow `docs/deployment/auth-service-bootstrap.md` to create the Cloud SQL database/user, Secret Manager entry, and Kubernetes secrets before applying the manifests.

### Deploy Steps

1. Ensure Terraform state applied for Artifact Registry, networking, and Workload Identity (see `infra/terraform/environments/<env>`).
2. Create/update Secret Manager entries:
   - `auth-db-username`, `auth-db-password`, `auth-db-host`, `auth-db-name`, `auth-jwt-secret`, `auth-kyc-api-key`.
3. Sync secrets into Kubernetes (Secret Manager CSI or External Secrets) so `auth-service-secrets` contains the keys referenced in Deployment env vars.
4. Build & push image:
   ```bash
   gcloud builds submit \
     --config=src/backend/auth-service/cloudbuild.yaml \
     --substitutions=_COMMIT_SHA=$(git rev-parse HEAD),_SERVICE_NAME=auth-service
   ```
5. Deploy with Kustomize:
   ```bash
   kubectl apply -k infra/kubernetes/environments/<env>
   ```
6. Verify rollout:
   ```bash
   kubectl -n auth-service-<env> rollout status deploy/auth-service
   kubectl -n auth-service-<env> get pods
   ```

## Configuration

| Variable | Source | Description |
| --- | --- | --- |
| `SPRING_PROFILES_ACTIVE` | ConfigMap / patch | `dev` for local cluster, `cloud` for staging/prod. |
| `DB_HOST/PORT/NAME/USERNAME/PASSWORD` | Secret `auth-service-secrets` | Cloud SQL connection parameters (use IAM auth proxy in prod). |
| `JWT_SECRET` | Secret `auth-service-secrets` | Base64-encoded symmetric key (≥64 bytes) for HS512. |
| `KYC_ENDPOINT` | ConfigMap override per environment | External KYC provider endpoint. |
| `KYC_API_KEY` | Secret `auth-service-secrets` | API key for third-party KYC provider. |
| `LOG_LEVEL` | ConfigMap override | Logging threshold consumed by Spring (maps to `logging.level.root`). |

Additional properties may be set through `application-cloud.yml` with Secret Manager integration.

## Health & Monitoring

- **Probes**: `/actuator/health/liveness` and `/actuator/health/readiness` exposed on port `8009`.
- **Metrics**: Enable scraping via Prometheus annotations (add in overlay) for actuator metrics.
- **Logs**: JSON structured logs with `service=auth-service`. Forward to Cloud Logging / ELK.
- **Tracing**: Configure OpenTelemetry agent via environment variables if tracing is required (`OTEL_EXPORTER_OTLP_ENDPOINT`).

## Run Operations

### Migrations

- Flyway runs automatically on startup (`baselineOnMigrate=true`). For manual execution:
  ```bash
  mvn -pl src/backend/auth-service -am flyway:migrate \
    -Dflyway.url=jdbc:postgresql://<host>:<port>/<db> \
    -Dflyway.user=<user> -Dflyway.password=<password>
  ```

### Scaling

- Adjust `spec.replicas` in environment patch or attach an HPA manifest.
- For prod, verify min replicas meet latency SLOs and configure `topologySpreadConstraints` as needed.

### Secrets Rotation

1. Update Secret Manager entry (e.g., `auth-jwt-secret`).
2. Trigger CSI/ExternalSecret sync or `kubectl rollout restart deploy/auth-service` to reload environment variables.
3. Monitor authentication metrics for elevated failures.

### Incident Response

- **Symptom**: Login failures / 401.
  - Check Cloud Logging for `Invalid email or password` vs token parsing errors.
  - Validate DB connectivity (Cloud SQL instance status, network). Use `kubectl exec` to run `pg_isready` if needed.
  - Inspect sidecar logs: `kubectl logs deploy/auth-service -c istio-proxy` for JWT or mTLS failures.
- **Symptom**: Increased 5xx.
  - Inspect readiness probe status, verify dependencies (KYC provider) reachable.
  - Review recent deployments via `kubectl rollout history`.
- **Symptom**: Migration failure.
  - Flyway prints structured errors on startup; check for schema drift. Use `flyway repair` before retrying.

## Local Development

```bash
cd src/backend/auth-service
export DB_HOST=localhost DB_PORT=5432 DB_NAME=auth_dev \
       DB_USERNAME=postgres DB_PASSWORD=postgres JWT_SECRET=$(openssl rand -base64 64)
mvn spring-boot:run
```

Use Docker Compose (`infra/docker/dev/docker-compose.minimal.yml`) to start PostgreSQL if needed. Flyway will initialize schema automatically.

## Contact & Ownership

- **Primary owner**: Platform Security Team
- **On-call escalation**: #alphintra-auth (Slack) / PagerDuty schedule `alphintra-auth`.
- **Documentation**: `docs/auth-service-assessment.md`, `docs/gateway/overview.md` (future), `plan.md` Phase 1.
