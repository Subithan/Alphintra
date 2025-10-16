resource "google_sql_database" "this" {
  name     = var.database_name
  instance = var.instance_name
  project  = var.project_id
  charset  = var.charset
  collation = var.collation
}

resource "google_sql_user" "this" {
  name     = var.db_user
  instance = var.instance_name
  project  = var.project_id
  password = var.db_password
}

resource "google_secret_manager_secret" "password" {
  secret_id = var.secret_name
  project   = var.project_id
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "password" {
  secret      = google_secret_manager_secret.password.id
  secret_data = var.db_password
}

output "database_self_link" {
  value = google_sql_database.this.self_link
}

output "secret_id" {
  value = google_secret_manager_secret.password.id
}
