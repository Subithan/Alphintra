module "network" {
  source      = "../../modules/network"
  project_id  = var.project_id
  network_name = var.network_name
  routing_mode = "GLOBAL"
  subnets      = var.subnets
}

module "artifact_registry" {
  source      = "../../modules/artifact-registry"
  project_id  = var.project_id
  repositories = var.artifact_registry_repositories
}

module "workload_identity" {
  source                    = "../../modules/workload-identity"
  project_id                = var.project_id
  workload_identity_project = var.workload_identity_project
  service_accounts          = var.workload_identity_service_accounts
}

module "auth_service_database" {
  source        = "../../modules/cloudsql-database"
  project_id    = var.project_id
  instance_name = var.cloudsql_instance_name
  database_name = var.auth_database_name
  db_user       = var.auth_database_user
  db_password   = var.auth_database_password
  secret_name   = var.auth_database_secret_name
}
