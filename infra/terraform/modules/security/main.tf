terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Binary Authorization policy
resource "google_binary_authorization_policy" "policy" {
  project = var.project_id

  default_admission_rule {
    evaluation_mode  = var.binary_authorization_policy.default_admission_rule.evaluation_mode
    enforcement_mode = var.binary_authorization_policy.default_admission_rule.enforcement_mode
  }
}

# Secret Manager secrets
resource "google_secret_manager_secret" "secrets" {
  for_each = var.secrets

  secret_id = each.value.secret_id
  project   = var.project_id

  replication {
    automatic = true
  }

  labels = {
    environment = var.environment
    managed-by  = "terraform"
  }
}

resource "google_secret_manager_secret_version" "secret_versions" {
  for_each = var.secrets

  secret      = google_secret_manager_secret.secrets[each.key].id
  secret_data = each.value.data
}