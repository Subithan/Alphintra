#!/usr/bin/env bash
set -euo pipefail

# Creates Cloud SQL database and user for ai-ml-strategy-service,
# and optionally creates Kubernetes secrets for connection.

PROJECT_ID=${PROJECT_ID:-alphintra-472817}
INSTANCE=${INSTANCE:-alphintra-db-instance}
REGION=${REGION:-us-central1}
DB_NAME=${DB_NAME:-alphintra_ai_ml_strategy_service}
DB_USER=${DB_USER:-ai_ml_user}
DB_PASSWORD=${DB_PASSWORD:-alphintra@123}
NAMESPACE=${NAMESPACE:-alphintra}

echo "Using project: ${PROJECT_ID}, instance: ${INSTANCE}, region: ${REGION}"

# Ensure gcloud project
gcloud config set project "${PROJECT_ID}" 1>/dev/null

echo "Creating database ${DB_NAME} if not exists..."
if gcloud sql databases list --instance="${INSTANCE}" --project="${PROJECT_ID}" --format="value(name)" | grep -qx "${DB_NAME}"; then
  echo "Database ${DB_NAME} already exists."
else
  gcloud sql databases create "${DB_NAME}" --instance="${INSTANCE}" --project="${PROJECT_ID}"
fi

echo "Ensuring user ${DB_USER} exists..."
if gcloud sql users list --instance="${INSTANCE}" --project="${PROJECT_ID}" --format="value(name)" | grep -qx "${DB_USER}"; then
  echo "User exists; updating password."
  gcloud sql users set-password "${DB_USER}" --instance="${INSTANCE}" --project="${PROJECT_ID}" --password "${DB_PASSWORD}"
else
  gcloud sql users create "${DB_USER}" --instance="${INSTANCE}" --project="${PROJECT_ID}" --password "${DB_PASSWORD}"
fi

CONN_NAME=$(gcloud sql instances describe "${INSTANCE}" --project "${PROJECT_ID}" --format='value(connectionName)')
echo "Connection name: ${CONN_NAME}"

ENC_PW=$(python3 - <<'PY'
import urllib.parse, os
pw = os.environ.get('DB_PASSWORD','')
print(urllib.parse.quote(pw, safe=''))
PY
)
APP_DB_URL="postgresql+psycopg2://${DB_USER}:${ENC_PW}@127.0.0.1:5432/${DB_NAME}"
echo "App DATABASE_URL (via Cloud SQL Proxy): ${APP_DB_URL}"

if command -v kubectl >/dev/null 2>&1; then
  echo "Creating/Updating Kubernetes secret ai-ml-strategy-service-secrets in namespace ${NAMESPACE}..."
  kubectl -n "${NAMESPACE}" create secret generic ai-ml-strategy-service-secrets \
    --from-literal=cloud-sql-connection-name="${CONN_NAME}" \
    --from-literal=DATABASE_URL="${APP_DB_URL}" \
    --dry-run=client -o yaml | kubectl apply -f -
  echo "Note: Create secret cloudsql-sa-secret with your Cloud SQL Service Account JSON as service-account.json if not present:"
  echo "  kubectl -n ${NAMESPACE} create secret generic cloudsql-sa-secret --from-file=service-account.json=/path/to/key.json"
else
  echo "kubectl not found; skipping Kubernetes secret creation."
fi

echo "Done."
