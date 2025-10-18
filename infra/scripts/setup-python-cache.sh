#!/bin/bash

# GCS Python Cache Bucket Setup Script
# Creates and configures the Python dependency cache bucket for Cloud Build optimization

set -e

# Configuration
PROJECT_ID="alphintra-472817"
BUCKET_NAME="${PROJECT_ID}-python-cache"
REGION="us-central1"
CACHE_RETENTION_DAYS=30

echo "🚀 Setting up Python cache bucket for Cloud Build optimization..."

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed or not in PATH"
    exit 1
fi

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [[ "$CURRENT_PROJECT" != "$PROJECT_ID" ]]; then
    echo "📝 Switching to project: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"
fi

echo "🪣 Creating GCS bucket: $BUCKET_NAME"

# Create the bucket
if gsutil ls -b "gs://$BUCKET_NAME" &> /dev/null; then
    echo "✅ Bucket $BUCKET_NAME already exists"
else
    gsutil mb -l "$REGION" "gs://$BUCKET_NAME"
    echo "✅ Created bucket: $BUCKET_NAME"
fi

# Set lifecycle management for cache optimization
echo "📋 Setting lifecycle rules for cache optimization..."

cat > lifecycle-config.json << EOF
{
  "rule": [
    {
      "action": {
        "type": "Delete"
      },
      "condition": {
        "age": $CACHE_RETENTION_DAYS
      }
    }
  ]
}
EOF

gsutil lifecycle set lifecycle-config.json "gs://$BUCKET_NAME"
echo "✅ Lifecycle rules configured (retention: $CACHE_RETENTION_DAYS days)"

# Clean up temporary lifecycle config
rm -f lifecycle-config.json

# Get Cloud Build service account
CLOUD_BUILD_SA=$(gcloud projects get-iam-policy "$PROJECT_ID" --format="value(bindings.members)" \
  --filter="role:roles/cloudbuild.builds.builder" | grep -o "serviceAccount:[^,]*" | head -1 | cut -d: -f2)

if [[ -z "$CLOUD_BUILD_SA" ]]; then
    echo "⚠️  Warning: Could not automatically detect Cloud Build service account"
    echo "   Please ensure the Cloud Build service account has storage permissions"
else
    echo "🔐 Granting permissions to Cloud Build service account: $CLOUD_BUILD_SA"

    # Grant necessary permissions for Cloud Build to access the cache bucket
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:$CLOUD_BUILD_SA" \
      --role="roles/storage.objectViewer" \
      --condition=None \
      --quiet

    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:$CLOUD_BUILD_SA" \
      --role="roles/storage.objectCreator" \
      --condition=None \
      --quiet

    echo "✅ Storage permissions granted to Cloud Build service account"
fi

# Set bucket permissions for uniform bucket-level access
echo "🔒 Setting uniform bucket-level access..."
gsutil uniformbucketlevelaccess set on "gs://$BUCKET_NAME"

# Create initial cache directory structure
echo "📁 Creating initial cache directory structure..."
gsutil -m touch "gs://$BUCKET_NAME/.gitkeep" 2>/dev/null || true

# Display bucket information
echo ""
echo "🎉 Python cache bucket setup completed!"
echo ""
echo "Bucket Details:"
echo "  Name: gs://$BUCKET_NAME"
echo "  Region: $REGION"
echo "  Retention: $CACHE_RETENTION_DAYS days"
echo "  Service Account: ${CLOUD_BUILD_SA:-'Please configure manually'}"
echo ""

# Test bucket access
echo "🧪 Testing bucket access..."
if gsutil ls "gs://$BUCKET_NAME" &> /dev/null; then
    echo "✅ Bucket access test successful"
else
    echo "❌ Bucket access test failed"
    echo "   Please check permissions and try again"
    exit 1
fi

echo ""
echo "🚀 Usage in Cloud Build:"
echo "  The bucket will store Python package dependencies as compressed tarballs"
echo "  Cache will be automatically restored/saved by Cloud Build configuration"
echo "  Expected cache size: 50-200MB depending on dependencies"
echo ""
echo "💡 Cache Strategy:"
echo "  - Dependencies from requirements.txt are cached in site-packages"
echo "  - Cache validation uses requirements.txt checksum"
echo "  - Cache corruption detection and automatic recovery"
echo "  - 30-day retention to balance storage costs and performance"
echo ""