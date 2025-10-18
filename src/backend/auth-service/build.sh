#!/bin/bash
#
# This script triggers a Cloud Build for the auth-service service.
# It is designed to be run from within this directory.
#
set -e

echo "🚀 Triggering Cloud Build for auth-service..."

gcloud beta builds submit --config cloudbuild.yaml . --verbosity=info

echo "✅ Build submitted successfully."