# Auth Service Bootstrap Checklist

The following commands provision the runtime dependencies for the auth service and service gateway inside the existing `alphintra` namespace.

## 1. Database & Secrets

Create the database and user inside the shared Cloud SQL instance (Terraform handles this when `auth_database_password` is provided):

```bash
cd infra/terraform/environments/dev # or staging/prod
terraform init
terraform apply -var auth_database_password="<secure-password>"
```

The Terraform module creates the `alphintra_auth_service` database, the `alphintra` user, and stores the password in Secret Manager as `auth-service-db-password`.

## 2. Kubernetes Secrets

Synchronise the database credentials into Kubernetes (replace placeholders with Secret Manager values):

```bash
kubectl create secret generic auth-service-secrets \
  --namespace alphintra \
  --from-literal=DB_HOST="/cloudsql/alphintra-472817:us-central1:alphintra-db-instance" \
  --from-literal=DB_PORT="5432" \
  --from-literal=DB_NAME="alphintra_auth_service" \
  --from-literal=DB_USERNAME="alphintra" \
  --from-literal=DB_PASSWORD="<db-password>" \
  --from-literal=JWT_SECRET="<jwt-secret>"

kubectl create secret generic service-gateway-secrets \
  --namespace alphintra \
  --from-literal=REDIS_HOST="redis-gateway.platform" \
  --from-literal=REDIS_PORT="6379" \
  --from-literal=REDIS_PASSWORD="<redis-password>" \
  --from-literal=GATEWAY_JWT_SECRET="<jwt-secret>"
```

> Replace `<db-password>`, `<jwt-secret>`, and `<redis-password>` with values from Secret Manager.

## 3. Deploy Workloads

Deploy both services into the existing namespace:

```bash
kubectl apply -k infra/kubernetes/environments/dev
# or
kubectl apply -k infra/kubernetes/environments/staging
kubectl apply -k infra/kubernetes/environments/prod
```

Verify the pods and services:

```bash
kubectl get pods -n alphintra -l app=auth-service
kubectl get pods -n alphintra -l app=service-gateway
kubectl get svc -n alphintra auth-service service-gateway
```

The deployments reuse the existing `alphintra` namespace and coexist with `no-code-service`, `frontend`, `redis`, and other workloads.
