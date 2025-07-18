# 🔐 Alphintra Platform Secrets Management

This document explains how to manage secrets in the Alphintra trading platform securely.

## 📋 Overview

The Alphintra platform uses Kubernetes secrets to store sensitive information such as:
- Database passwords
- API keys
- JWT signing secrets
- Encryption keys
- OAuth credentials
- SMTP configurations

## 🚀 Quick Start

### 1. Interactive Secrets Setup
```bash
# During cluster setup (recommended)
make k8s-setup
# Choose "Y" when prompted for interactive secrets setup

# Or run separately
make k8s-secrets
```

### 2. Use Default Secrets (Testing Only)
```bash
# During cluster setup, choose "N" for quick testing
make k8s-setup
```

## 🔧 Commands

### Setup & Management
```bash
# Set up secrets interactively
make k8s-secrets

# List all secrets
./scripts/manage-secrets.sh list

# View secret details (without values)
./scripts/manage-secrets.sh view alphintra-secrets

# Export secret values (be careful!)
./scripts/manage-secrets.sh export alphintra-secrets

# Delete a specific secret
./scripts/manage-secrets.sh delete api-keys

# Reset all secrets
./scripts/manage-secrets.sh reset

# Backup all secrets (encrypted)
./scripts/manage-secrets.sh backup
```

### Direct Kubernetes Commands
```bash
# List secrets in all namespaces
kubectl get secrets -A

# View secret details
kubectl describe secret alphintra-secrets -n alphintra

# Export secret values (base64 decoded)
kubectl get secret alphintra-secrets -n alphintra -o jsonpath='{.data}' | jq -r 'to_entries[] | "\(.key): \(.value | @base64d)"'

# Create a new secret manually
kubectl create secret generic my-secret --from-literal=key1=value1 -n alphintra
```

## 📊 Secret Categories

### 1. Core Platform Secrets (`alphintra-secrets`)
**Namespace:** `alphintra`

| Key | Description | Required |
|-----|-------------|----------|
| `jwt-secret` | JWT token signing secret | ✅ |
| `postgres-password` | PostgreSQL admin password | ✅ |
| `redis-password` | Redis authentication password | ✅ |
| `internal-service-token` | Service-to-service authentication | ✅ |
| `encryption-key` | Data encryption key | ✅ |
| `minio-access-key` | MinIO/S3 access key | ✅ |
| `minio-secret-key` | MinIO/S3 secret key | ✅ |

### 2. Authentication Secrets (`auth-secrets`)
**Namespace:** `alphintra`

| Key | Description | Required |
|-----|-------------|----------|
| `oauth-client-id` | OAuth provider client ID | ❌ |
| `oauth-client-secret` | OAuth provider client secret | ❌ |

### 3. API Keys (`api-keys`)
**Namespace:** `alphintra`

| Key | Description | Required |
|-----|-------------|----------|
| `alpha-vantage-key` | Alpha Vantage API key (market data) | ❌ |
| `coinapi-key` | CoinAPI key (crypto data) | ❌ |

### 4. Monitoring Secrets (`monitoring-secrets`)
**Namespace:** `monitoring`

| Key | Description | Required |
|-----|-------------|----------|
| `grafana-admin-password` | Grafana admin user password | ✅ |

### 5. SMTP Secrets (`smtp-secrets`)
**Namespace:** `monitoring`

| Key | Description | Required |
|-----|-------------|----------|
| `smtp-host` | SMTP server hostname | ❌ |
| `smtp-port` | SMTP server port | ❌ |
| `smtp-username` | SMTP authentication username | ❌ |
| `smtp-password` | SMTP authentication password | ❌ |

## 🔒 Security Best Practices

### 1. Development Environment
- Use interactive setup for realistic testing
- Never commit secrets to version control
- Use different secrets for each environment

### 2. Production Environment
- **Always** use interactive setup
- Use strong, unique passwords
- Enable encryption at rest in Kubernetes
- Regularly rotate secrets
- Use external secret management (HashiCorp Vault, AWS Secrets Manager)

### 3. Secret Rotation
```bash
# 1. Backup current secrets
./scripts/manage-secrets.sh backup

# 2. Update specific secret
kubectl patch secret alphintra-secrets -n alphintra --type='json' -p='[{"op": "replace", "path": "/data/jwt-secret", "value":"'$(echo -n "new-jwt-secret" | base64)'"}]'

# 3. Restart affected services
kubectl rollout restart deployment/api-gateway -n alphintra
kubectl rollout restart deployment/auth-service -n alphintra
```

## 📁 File Locations

```
infra/
├── scripts/
│   ├── setup-secrets.sh         # Interactive secrets setup
│   └── manage-secrets.sh        # Secrets management utilities
├── .secrets/                    # Local secrets summaries (git-ignored)
│   └── secrets-summary-dev.txt  # Non-sensitive summary
└── docs/
    └── SECRETS_MANAGEMENT.md    # This documentation
```

## 🚨 Troubleshooting

### Secret Not Found
```bash
# Check if secret exists
kubectl get secrets -A | grep secret-name

# Check namespace
kubectl get secrets -n alphintra
kubectl get secrets -n monitoring
```

### Permission Denied
```bash
# Check if you're in the right context
kubectl config current-context

# Should show: k3d-alphintra-cluster
```

### Invalid Secret Values
```bash
# View secret details
kubectl describe secret alphintra-secrets -n alphintra

# Check if values are base64 encoded
kubectl get secret alphintra-secrets -n alphintra -o yaml
```

### Reset Everything
```bash
# Complete reset (nuclear option)
./scripts/manage-secrets.sh reset

# Or manual reset
kubectl delete secrets --all -n alphintra
kubectl delete secrets --all -n monitoring
make k8s-secrets
```

## 🔧 Integration with Services

### Spring Boot Services
Services automatically read secrets through environment variables:
```yaml
env:
- name: JWT_SECRET
  valueFrom:
    secretKeyRef:
      name: alphintra-secrets
      key: jwt-secret
```

### Python Services
Services read secrets via environment variables or mounted volumes:
```python
import os
jwt_secret = os.getenv('JWT_SECRET')
```

### Grafana Configuration
Grafana reads admin password from monitoring-secrets:
```yaml
env:
- name: GF_SECURITY_ADMIN_PASSWORD
  valueFrom:
    secretKeyRef:
      name: monitoring-secrets
      key: grafana-admin-password
```

## 📞 Support

If you need help with secrets management:
1. Check this documentation
2. Run `./scripts/manage-secrets.sh help`
3. Review the interactive setup prompts
4. Check Kubernetes documentation for advanced use cases

---

**⚠️ Remember:** Never commit secrets to version control. Always use secure secret management practices in production environments.