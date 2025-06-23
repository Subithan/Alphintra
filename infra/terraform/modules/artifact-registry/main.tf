terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

resource "google_artifact_registry_repository" "repo" {
  location      = var.location
  repository_id = var.repository_id
  description   = var.description
  format        = var.format
  project       = var.project_id

  labels = {
    environment = "production"
    managed-by  = "terraform"
  }
}

resource "google_artifact_registry_repository_iam_member" "member" {
  count = length(var.members)

  project    = var.project_id
  location   = var.location
  repository = google_artifact_registry_repository.repo.name
  role       = "roles/artifactregistry.reader"
  member     = var.members[count.index]
}