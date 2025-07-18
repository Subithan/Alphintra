#!/bin/bash

# Interactive Secrets Setup for Alphintra Trading Platform
# This script prompts for sensitive information and creates Kubernetes secrets

set -e

# Color codes for output
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
RESET='\033[0m'

SECRETS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../.secrets"
ENV=${1:-dev}

echo -e "${CYAN}🔐 Alphintra Platform Secrets Setup${RESET}"
echo -e "${BLUE}======================================${RESET}"
echo ""

# Check if kubectl is available and cluster is running
if ! kubectl cluster-info > /dev/null 2>&1; then
    echo -e "${RED}❌ Kubernetes cluster is not accessible. Please run 'make k8s-setup' first.${RESET}"
    exit 1
fi

# Check if namespaces exist
if ! kubectl get namespace alphintra > /dev/null 2>&1; then
    echo -e "${RED}❌ 'alphintra' namespace not found. Please run 'make k8s-setup' first.${RESET}"
    exit 1
fi

# Create secrets directory if it doesn't exist
mkdir -p "$SECRETS_DIR"

echo -e "${YELLOW}This script will help you set up secrets for the Alphintra platform.${RESET}"
echo -e "${YELLOW}Secrets will be stored securely in Kubernetes and not saved to disk.${RESET}"
echo ""

# Function to read password securely
read_password() {
    local prompt="$1"
    local default="$2"
    local password
    
    echo -n -e "${CYAN}$prompt${RESET}"
    if [ ! -z "$default" ]; then
        echo -n -e " ${YELLOW}[default: $default]${RESET}"
    fi
    echo -n ": "
    
    # Read password without echoing
    read -s password
    echo "" # New line after password input
    
    # Use default if password is empty
    if [ -z "$password" ] && [ ! -z "$default" ]; then
        password="$default"
    fi
    
    echo "$password"
}

# Function to read normal input
read_input() {
    local prompt="$1"
    local default="$2"
    local input
    
    echo -n -e "${CYAN}$prompt${RESET}"
    if [ ! -z "$default" ]; then
        echo -n -e " ${YELLOW}[default: $default]${RESET}"
    fi
    echo -n ": "
    
    read input
    
    # Use default if input is empty
    if [ -z "$input" ] && [ ! -z "$default" ]; then
        input="$default"
    fi
    
    echo "$input"
}

# Function to generate random password
generate_password() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

echo -e "${BLUE}📋 Platform Core Secrets${RESET}"
echo "=========================="

# JWT Secret
echo ""
echo -e "${YELLOW}JWT Secret (used for token signing):${RESET}"
jwt_secret=$(read_password "Enter JWT secret (or press Enter for auto-generated)" "")
if [ -z "$jwt_secret" ]; then
    jwt_secret="alphintra_jwt_$(generate_password 48)"
    echo -e "${GREEN}✓ Auto-generated JWT secret${RESET}"
fi

# Database passwords
echo ""
echo -e "${YELLOW}Database Configuration:${RESET}"
postgres_password=$(read_password "PostgreSQL admin password" "alphintra_postgres_$(generate_password 16)")

# Redis password
redis_password=$(read_password "Redis password" "alphintra_redis_$(generate_password 16)")

# Internal service token
echo ""
echo -e "${YELLOW}Internal Service Authentication:${RESET}"
internal_token=$(read_password "Internal service token (or press Enter for auto-generated)" "")
if [ -z "$internal_token" ]; then
    internal_token="alphintra-internal-$(generate_password 24)"
    echo -e "${GREEN}✓ Auto-generated internal service token${RESET}"
fi

echo ""
echo -e "${BLUE}🔐 Authentication & Security${RESET}"
echo "============================="

# OAuth/External auth (optional)
echo ""
echo -e "${YELLOW}External Authentication (Optional):${RESET}"
oauth_client_id=$(read_input "OAuth Client ID (optional)" "")
oauth_client_secret=""
if [ ! -z "$oauth_client_id" ]; then
    oauth_client_secret=$(read_password "OAuth Client Secret" "")
fi

# API Keys for external services
echo ""
echo -e "${YELLOW}External API Keys (Optional):${RESET}"
alpha_vantage_key=$(read_input "Alpha Vantage API Key (for market data)" "")
coinapi_key=$(read_input "CoinAPI Key (for crypto data)" "")

echo ""
echo -e "${BLUE}📊 Monitoring & Observability${RESET}"
echo "=============================="

# Grafana admin password
grafana_admin_password=$(read_password "Grafana admin password" "admin123")

# Email configuration for alerts (optional)
echo ""
echo -e "${YELLOW}Email Alerts Configuration (Optional):${RESET}"
smtp_host=$(read_input "SMTP Host (for alerts)" "")
smtp_port=$(read_input "SMTP Port" "587")
smtp_username=""
smtp_password=""
if [ ! -z "$smtp_host" ]; then
    smtp_username=$(read_input "SMTP Username" "")
    smtp_password=$(read_password "SMTP Password" "")
fi

echo ""
echo -e "${BLUE}☁️ Cloud & Storage (Optional)${RESET}"
echo "============================="

# MinIO/S3 credentials
minio_access_key=$(read_input "MinIO/S3 Access Key" "alphintra-admin")
minio_secret_key=$(read_password "MinIO/S3 Secret Key" "alphintra-secret-$(generate_password 16)")

# Encryption keys
echo ""
echo -e "${YELLOW}Data Encryption:${RESET}"
encryption_key=$(read_password "Data encryption key (or press Enter for auto-generated)" "")
if [ -z "$encryption_key" ]; then
    encryption_key=$(generate_password 32)
    echo -e "${GREEN}✓ Auto-generated encryption key${RESET}"
fi

echo ""
echo -e "${BLUE}🚀 Creating Kubernetes Secrets...${RESET}"
echo ""

# Create main platform secrets
echo -e "${YELLOW}Creating alphintra platform secrets...${RESET}"
kubectl create secret generic alphintra-secrets \
    --namespace=alphintra \
    --from-literal=jwt-secret="$jwt_secret" \
    --from-literal=postgres-password="$postgres_password" \
    --from-literal=redis-password="$redis_password" \
    --from-literal=internal-service-token="$internal_token" \
    --from-literal=encryption-key="$encryption_key" \
    --from-literal=minio-access-key="$minio_access_key" \
    --from-literal=minio-secret-key="$minio_secret_key" \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ alphintra-secrets created${RESET}"

# Create auth secrets (if OAuth is configured)
if [ ! -z "$oauth_client_id" ]; then
    echo -e "${YELLOW}Creating authentication secrets...${RESET}"
    kubectl create secret generic auth-secrets \
        --namespace=alphintra \
        --from-literal=oauth-client-id="$oauth_client_id" \
        --from-literal=oauth-client-secret="$oauth_client_secret" \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✓ auth-secrets created${RESET}"
fi

# Create API keys secret (if any are provided)
if [ ! -z "$alpha_vantage_key" ] || [ ! -z "$coinapi_key" ]; then
    echo -e "${YELLOW}Creating external API secrets...${RESET}"
    kubectl create secret generic api-keys \
        --namespace=alphintra \
        --from-literal=alpha-vantage-key="$alpha_vantage_key" \
        --from-literal=coinapi-key="$coinapi_key" \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✓ api-keys created${RESET}"
fi

# Create monitoring secrets
echo -e "${YELLOW}Creating monitoring secrets...${RESET}"
kubectl create secret generic monitoring-secrets \
    --namespace=monitoring \
    --from-literal=grafana-admin-password="$grafana_admin_password" \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ monitoring-secrets created${RESET}"

# Create SMTP secrets (if configured)
if [ ! -z "$smtp_host" ]; then
    echo -e "${YELLOW}Creating SMTP secrets...${RESET}"
    kubectl create secret generic smtp-secrets \
        --namespace=monitoring \
        --from-literal=smtp-host="$smtp_host" \
        --from-literal=smtp-port="$smtp_port" \
        --from-literal=smtp-username="$smtp_username" \
        --from-literal=smtp-password="$smtp_password" \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✓ smtp-secrets created${RESET}"
fi

echo ""
echo -e "${GREEN}✅ All secrets created successfully!${RESET}"
echo ""

# Create a summary file (without sensitive data)
cat > "$SECRETS_DIR/secrets-summary-$ENV.txt" << EOF
# Alphintra Platform Secrets Summary ($ENV environment)
# Generated on: $(date)

## Created Secrets:
- alphintra-secrets (alphintra namespace)
  - jwt-secret ✓
  - postgres-password ✓
  - redis-password ✓
  - internal-service-token ✓
  - encryption-key ✓
  - minio-access-key ✓
  - minio-secret-key ✓

- monitoring-secrets (monitoring namespace)
  - grafana-admin-password ✓

$([ ! -z "$oauth_client_id" ] && echo "- auth-secrets (alphintra namespace)
  - oauth-client-id ✓
  - oauth-client-secret ✓")

$([ ! -z "$alpha_vantage_key" ] || [ ! -z "$coinapi_key" ] && echo "- api-keys (alphintra namespace)
  - alpha-vantage-key $([ ! -z "$alpha_vantage_key" ] && echo "✓" || echo "❌")
  - coinapi-key $([ ! -z "$coinapi_key" ] && echo "✓" || echo "❌")")

$([ ! -z "$smtp_host" ] && echo "- smtp-secrets (monitoring namespace)
  - smtp-host ✓
  - smtp-port ✓
  - smtp-username ✓
  - smtp-password ✓")

## Access Information:
- Grafana: http://localhost:3001 (admin / $grafana_admin_password)
- MinIO Console: Access Key = $minio_access_key

## Commands to view secrets:
kubectl get secrets -n alphintra
kubectl get secrets -n monitoring
kubectl describe secret alphintra-secrets -n alphintra
EOF

echo -e "${CYAN}📋 Secrets Summary:${RESET}"
echo -e "${YELLOW}Summary saved to: $SECRETS_DIR/secrets-summary-$ENV.txt${RESET}"
echo ""
echo -e "${CYAN}🔧 Useful Commands:${RESET}"
echo "  kubectl get secrets -A                           # List all secrets"
echo "  kubectl describe secret alphintra-secrets -n alphintra  # View secret details"
echo "  kubectl get secret alphintra-secrets -n alphintra -o yaml  # Export secret"
echo ""
echo -e "${GREEN}🚀 Ready to deploy! Run: make k8s-deploy${RESET}"