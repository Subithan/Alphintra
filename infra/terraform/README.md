# Terraform Structure

This directory defines reproducible cloud infrastructure aligned with the Gateway & Observability plan. Environments (`dev`, `staging`, `prod`) share reusable modules and Google Cloud provider configuration.

## Layout

```
infra/terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── providers.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars.example
│   │   └── outputs.tf
│   ├── staging/
│   └── prod/
└── modules/
    ├── network/
    ├── artifact-registry/
    └── workload-identity/
```

Each environment mirrors the same files; override only the variables necessary for that stage.

## Bootstrap Commands

1. Install Terraform ≥ 1.5.
2. Authenticate with Google Cloud (`gcloud auth application-default login`).
3. Copy `terraform.tfvars.example` to `terraform.tfvars` and fill environment-specific values.
4. Initialize and apply:

```bash
cd infra/terraform/environments/dev
terraform init
terraform plan
terraform apply
```

Repeat for `staging` and `prod`.

## Managed Resources

- **Network** – Dedicated VPC and subnets per environment (no more reliance on the default network).
- **Artifact Registry** – Regional Docker repositories aligned with deployment targets.
- **Workload Identity** – Google service accounts mapped to Kubernetes service accounts with least-privilege IAM roles.

Future modules will add Cloud SQL, Memorystore, Secret Manager, and Config Connector bindings.
