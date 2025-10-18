resource "google_project_service" "artifact_registry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"
}

resource "google_artifact_registry_repository" "this" {
  for_each      = { for repo in var.repositories : repo.repository_id => repo }
  project       = var.project_id
  location      = each.value.location
  repository_id = each.value.repository_id
  format        = each.value.format
  description   = try(each.value.description, null)
  kms_key_name  = try(each.value.kms_key_name, null)
  labels        = try(each.value.labels, null)

  depends_on = [google_project_service.artifact_registry]
}
