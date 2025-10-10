# Cloud Baseline Inventory

The following inventory captures the current Google Cloud Platform state for `alphintra-472817`. Data was collected with the Google Cloud SDK on the date of this commit to unblock Phase 0 decisions.

## Project

| Field | Value |
| --- | --- |
| Project ID | `alphintra-472817` |
| Project Name | `Alphintra` |
| Project Number | `999709622705` |
| Lifecycle | `ACTIVE` |

Query:

```bash
gcloud projects describe alphintra-472817 --format=json
```

## Networking

| Attribute | Value |
| --- | --- |
| Default VPC | `default` (auto subnet mode) |
| Routing Mode | `REGIONAL` |
| Subnet Regions | Auto-created subnets across all public regions |

The project currently relies on the default network. A dedicated VPC should be introduced before production rollout.

Query:

```bash
gcloud compute networks list --format=json
```

## Artifact Registry

| Repository | Location | Format | Notes |
| --- | --- | --- | --- |
| `projects/alphintra-472817/locations/us/repositories/gcr.io` | `us` | Docker | Legacy GCR compatibility repository |
| `projects/alphintra-472817/locations/us-central1/repositories/alphintra` | `us-central1` | Docker | Primary container image registry (`satisfiesPzi: true`) |

Both repositories were confirmed via:

```bash
gcloud artifacts repositories list --project=alphintra-472817 --format=json
```

## Cloud SQL

| Instance | Region | Version | Tier | Primary Address |
| --- | --- | --- | --- | --- |
| `alphintra-db-instance` | `us-central1` | PostgreSQL 15.14 | `db-g1-small` | `34.136.69.240` |

Important configuration highlights:
- SSL optional (`sslMode: ALLOW_UNENCRYPTED_AND_ENCRYPTED`)
- Backups disabled; retention window configured but inactive
- Storage auto-resize enabled (10 GB base)

Query:

```bash
gcloud sql instances list --project=alphintra-472817 --format=json
```

## Memorystore (Redis)

| Region | Instances |
| --- | --- |
| `us-central1` | _None_ |

The Redis API was enabled as part of this inventory; no instances exist yet.

Query:

```bash
gcloud redis instances list --project=alphintra-472817 --region=us-central1 --format=json
```

## Next Steps

- Stand up dedicated VPC, subnetworks, and Cloud NAT aligned with deployment regions.
- Enable vulnerability scanning on Artifact Registry repositories.
- Configure automated backups and IAM database auth for Cloud SQL.
- Provision Memorystore instances per environment (dev/staging/prod) once gateway caching is implemented.
