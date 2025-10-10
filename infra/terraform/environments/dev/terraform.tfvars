project_id = "alphintra-472817"

region = "us-central1"
zone   = "us-central1-c"

network_name = "alphintra-dev-vpc"

subnets = [
  {
    name          = "dev-apps-subnet"
    region        = "us-central1"
    ip_cidr_range = "10.10.0.0/24"
    secondary_ip_ranges = [
      {
        range_name    = "dev-pods"
        ip_cidr_range = "10.10.8.0/21"
      },
      {
        range_name    = "dev-services"
        ip_cidr_range = "10.10.16.0/21"
      }
    ]
  }
]

artifact_registry_repositories = [
  {
    repository_id = "alphintra-dev"
    location      = "us-central1"
    format        = "DOCKER"
    description   = "Container images for dev workloads"
    labels = {
      environment = "dev"
      service     = "platform"
    }
  }
]

workload_identity_project = "alphintra-472817"

workload_identity_service_accounts = [
  {
    name         = "auth-cloudsql"
    account_id   = "auth-cloudsql-dev"
    display_name = "Auth Service Cloud SQL (dev)"
    roles = [
      "roles/cloudsql.client",
      "roles/secretmanager.secretAccessor",
      "roles/logging.logWriter"
    ]
    kubernetes_service_accounts = [
      {
        namespace = "auth-service"
        name      = "auth-service"
      }
    ]
  },
  {
    name         = "gateway-runtime"
    account_id   = "gateway-runtime-dev"
    display_name = "Gateway Runtime (dev)"
    roles = [
      "roles/monitoring.metricWriter",
      "roles/cloudtrace.agent",
      "roles/logging.logWriter"
    ]
    kubernetes_service_accounts = [
      {
        namespace = "gateway"
        name      = "gateway"
      }
    ]
  }
]

cloudsql_instance_name     = "alphintra-db-instance"
auth_database_name         = "alphintra_auth_service"
auth_database_user         = "alphintra"
auth_database_password     = "alphintra123"
auth_database_secret_name  = "auth-service-db-password"
