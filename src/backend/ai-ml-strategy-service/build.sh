#!/bin/bash
#
# This script triggers a Cloud Build for the ai-ml-strategy-service.
# It is designed to be run from within this directory.
#
set -e

echo "🚀 Triggering Cloud Build for ai-ml-strategy-service..."

COMMIT_SHA=${COMMIT_SHA:-$(git rev-parse --short HEAD 2>/dev/null || echo manual)}
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions=_COMMIT_SHA=${COMMIT_SHA} \
  .

echo "✅ Build submitted successfully."
