# Alphintra Terraform Infrastructure

## Overview
This directory contains Terraform configurations for provisioning Alphintra Trading Platform infrastructure on Google Cloud Platform (GCP) and local development environments.

## Directory Structure
```
terraform/
├── modules/                # Reusable Terraform modules
│   ├── vpc/               # VPC and networking
│   ├── gke/               # Google Kubernetes Engine
│   ├── cloudsql/          # Cloud SQL databases
│   ├── pubsub/            # Pub/Sub topics and subscriptions
│   ├── vertex-ai/         # Vertex AI resources
│   ├── monitoring/        # Monitoring and logging
│   └── security/          # Security and IAM
├── environments/          # Environment-specific configurations
│   ├── dev/              # Development environment
│   ├── staging/          # Staging environment
│   └── prod/             # Production environment
├── global/               # Global resources (DNS, IAM, etc.)
└── locals/               # Local development simulation
```

## Usage

### Prerequisites
```bash
# Install Terraform
brew install terraform

# Install Terragrunt (optional but recommended)
brew install terragrunt

# Authenticate with GCP
gcloud auth application-default login
```

### Development Environment
```bash
# Plan development environment
cd environments/dev
terraform plan

# Apply development environment
terraform apply

# Destroy development environment
terraform destroy
```

### Production Environment
```bash
# Plan production environment
cd environments/prod
terraform plan

# Apply production environment (with approval)
terraform apply

# Destroy production environment (with approval)
terraform destroy
```

## Modules Documentation
Each module contains its own README with usage examples and variable descriptions.

## State Management
- **Local Development**: Local state files
- **Production**: Remote state in GCS bucket with state locking