output "repositories" {
  description = "Managed Artifact Registry repositories."
  value = {
    for id, repo in google_artifact_registry_repository.this :
    id => {
      id        = repo.id
      location  = repo.location
      format    = repo.format
      endpoint  = repo.repository_id
    }
  }
}
