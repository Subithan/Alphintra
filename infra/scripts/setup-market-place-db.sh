#!/bin/bash

# Marketplace Service Database Setup Script
# Creates the "alphintra_market_place" database and the "market_place" user
# on the shared Cloud SQL instance. Safe to re-run – operations are idempotent.

set -euo pipefail

PROJECT_ID=${PROJECT_ID:-"alphintra-472817"}
REGION=${REGION:-"us-central1"}
INSTANCE_NAME=${INSTANCE_NAME:-"alphintra-db-instance"}
DATABASE_NAME=${DATABASE_NAME:-"alphintra_market_place"}
DB_USER=${DB_USER:-"market_place"}
DB_PASSWORD=${DB_PASSWORD:-"alphintra@123"}

INFO_PREFIX="[marketplace-db]"

log() {
  echo "${INFO_PREFIX} $1"
}

if ! command -v gcloud >/dev/null 2>&1; then
  echo "❌ gcloud CLI is required but not installed." >&2
  exit 1
fi

log "Using project: ${PROJECT_ID}"
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [[ "${CURRENT_PROJECT}" != "${PROJECT_ID}" ]]; then
  log "Switching gcloud project to ${PROJECT_ID}"
  gcloud config set project "${PROJECT_ID}" >/dev/null
fi

log "Checking Cloud SQL instance ${INSTANCE_NAME}"
if ! gcloud sql instances describe "${INSTANCE_NAME}" --format="value(state)" >/dev/null 2>&1; then
  echo "❌ Cloud SQL instance '${INSTANCE_NAME}' not found." >&2
  exit 1
fi

INSTANCE_STATE=$(gcloud sql instances describe "${INSTANCE_NAME}" --format="value(state)")
log "Instance state: ${INSTANCE_STATE}"

log "Ensuring database ${DATABASE_NAME} exists"
if gcloud sql databases list --instance="${INSTANCE_NAME}" --filter="name:${DATABASE_NAME}" --format="value(name)" | grep -q "${DATABASE_NAME}"; then
  log "Database already present"
else
  gcloud sql databases create "${DATABASE_NAME}" --instance="${INSTANCE_NAME}"
  log "Database created"
fi

log "Ensuring user ${DB_USER} exists"
if gcloud sql users list --instance="${INSTANCE_NAME}" --filter="name:${DB_USER}" --format="value(name)" | grep -q "${DB_USER}"; then
  log "User exists – updating password"
  gcloud sql users set-password "${DB_USER}" --host="%" --instance="${INSTANCE_NAME}" --password="${DB_PASSWORD}"
else
  gcloud sql users create "${DB_USER}" --host="%" --instance="${INSTANCE_NAME}" --password="${DB_PASSWORD}"
  log "User created"
fi

log "Granting privileges on ${DATABASE_NAME}"
gcloud sql connect "${INSTANCE_NAME}" --user=postgres <<'SQL'
\c ${DATABASE_NAME};
GRANT ALL PRIVILEGES ON DATABASE ${DATABASE_NAME} TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};
\q
SQL

log "Testing connection with service credentials"
gcloud sql connect "${INSTANCE_NAME}" --user="${DB_USER}" --database="${DATABASE_NAME}" <<'SQL'
SELECT current_database(), current_user;
\q
SQL

cat <<SUMMARY

✅ Marketplace database ready!
  Project: ${PROJECT_ID}
  Instance: ${INSTANCE_NAME}
  Region: ${REGION}
  Database: ${DATABASE_NAME}
  User: ${DB_USER}
  Connection string: postgresql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5432/${DATABASE_NAME}

SUMMARY
