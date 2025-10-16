# Auth Service Assessment

## API Surface

| Endpoint | Method | Auth | Description | Request DTO |
| --- | --- | --- | --- | --- |
| `/api/auth/register` | POST | Public | Registers a new user and returns JWT + profile. | `RegisterRequest` |
| `/api/auth/login` | POST | Public | Authenticates existing user by email/password. | `AuthRequest` |
| `/api/auth/validate` | POST | Public | Validates a JWT and returns boolean. | `TokenValidationRequest` |
| `/api/users/me` | GET | JWT | Fetches current user profile (sanitized, no password). | – |
| `/api/users/me` | PUT | JWT | Updates current user profile (partial fields). | `UserUpdateRequest` |
| `/api/kyc/documents` | POST | JWT | Submits KYC document metadata for async processing. | `KycDocumentRequest` |
| `/api/kyc/status` | GET | JWT | Retrieves KYC status for current user. | – |

## DTO Summary

- `RegisterRequest`: username/email/password validated (length, pattern) plus first/last name.
- `AuthRequest`: email/password with format checks.
- `TokenValidationRequest`: wraps bearer token for validation endpoint.
- `UserUpdateRequest`: optional profile fields with length, format, and past-date constraints.
- `KycDocumentRequest`: requires document type (≤50 characters).
- `AuthResponse`: sanitized profile (`UserProfile`) and JWT string.
- `UserProfile`: immutable view exposing `id`, `username`, `email`, `firstName`, `lastName`, `kycStatus`, and role names.

## Persistence Model

Flyway migration `db/migration/V1__init_schema.sql` creates:

- `users`: core identity record; includes KYC fields (`date_of_birth`, `kyc_status`, contact info). Default admin user and timestamps.
- `roles`: bootstrap roles (`USER`, `ADMIN`, `KYC_ADMIN`).
- `user_roles`: many-to-many mapping.
- `kyc_documents`: tracks submitted documents and status per user.
- Indexes on usernames, emails, role names, and join tables to support authentication lookups.
- Seed data linking `admin` user to `ADMIN` role.

## Security & Config Highlights

- JWT secrets, database credentials, and KYC provider keys injected via environment variables / Secret Manager overlay (`application-cloud.yml`).
- Workload Identity-ready: deployment references Google-managed service account and Kubernetes secret keys.
- Structured JSON logging via `logback-spring.xml` (Logstash encoder) with consistent `service` field.
- CORS restricted by `app.security.allowed-origins` property (configurable per environment).

## Testing Coverage Additions

- Unit tests (`AuthServiceTest`) exercise registration/duplicate checks and authentication failures.
- Controller slice tests (`AuthControllerTest`) validate request validation and JSON responses.
- Integration test (`AuthApiIntegrationTest`) spins up PostgreSQL Testcontainers, exercises register/login flow with Flyway migrations.
- JaCoCo reports generated during `mvn clean verify` (goal attached to `verify`).

## Outstanding Considerations

- Implement rollback/compensation for KYC document submission once upstream provider is integrated.
- Replace placeholder KYC endpoints per environment with actual provider URLs via ConfigMaps or service discovery.
- Observe Flyway migrations on Cloud SQL for production (baseline existing schema if running outside Terraform).
- Add caching/token revocation once gateway introduces JWT introspection endpoint.

## Observability & Mesh Alignment

- Prometheus scraping is enabled through `infra/kubernetes/observability/base/servicemonitor-auth.yaml`.
- Istio mTLS/JWT enforcement uses `requestauthentication-jwt.yaml` and `authorizationpolicy-gateway.yaml`—auth-service pods require sidecars in injected namespaces.
- Use the Grafana gateway dashboard to monitor auth 5xx/latency during deployments; update alert thresholds alongside SLO changes.
