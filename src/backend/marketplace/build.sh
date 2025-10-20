#!/bin/bash
#
# Trigger Cloud Build for the Marketplace service using the optimized pipeline.
# Provides a consistent image tag derived from the current git revision.
#
set -euo pipefail

SERVICE_NAME="marketplace-service"
PROJECT_ID=${PROJECT_ID:-"alphintra-472817"}

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  IMAGE_TAG=$(git rev-parse --short HEAD)
else
  IMAGE_TAG="latest"
fi

echo "🚀 Triggering Cloud Build for ${SERVICE_NAME}"
echo "   Project: ${PROJECT_ID}"
echo "   Image tag: ${IMAGE_TAG}"

gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions=_SERVICE_NAME=${SERVICE_NAME},_PROJECT_ID=${PROJECT_ID},_COMMIT_SHA=${IMAGE_TAG} \
  . --verbosity=info

echo "✅ Build submitted successfully."
