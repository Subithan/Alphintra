#!/bin/bash
#
# This script triggers a Cloud Build for the customer-support-service service.
# It is designed to be run from within this directory.
#
set -e

echo "🚀 Triggering Cloud Build for customer-support-service..."

gcloud beta builds submit --config cloudbuild.yaml . --verbosity=info

echo "✅ Build submitted successfully."