#!/bin/bash
#
# Trigger Cloud Build for the no-code-service.
# Ensures the image tag used for build and push is explicit and consistent.
#
set -euo pipefail

SERVICE_NAME="no-code-service"
PROJECT_ID=${PROJECT_ID:-"alphintra-472817"}

# Compute a deterministic image tag (SHORT_SHA), fallback to 'latest' if not a git repo
if git rev-parse --short HEAD >/dev/null 2>&1; then
  IMAGE_TAG=$(git rev-parse --short HEAD)
else
  IMAGE_TAG="latest"
fi

echo "🚀 Triggering Cloud Build for ${SERVICE_NAME}..."
echo "   Project: ${PROJECT_ID}"
echo "   Image tag: ${IMAGE_TAG}"

gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions=_SERVICE_NAME=${SERVICE_NAME},_PROJECT_ID=${PROJECT_ID},_COMMIT_SHA=${IMAGE_TAG} \
  . --verbosity=info

echo "✅ Build submitted successfully."
