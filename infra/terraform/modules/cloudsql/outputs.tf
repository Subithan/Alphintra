# Outputs for Cloud SQL Module

output "instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.name
}

output "instance_id" {
  description = "ID of the Cloud SQL instance"
  value       = google_sql_database_instance.main.id
}

output "connection_name" {
  description = "Connection name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.connection_name
}

output "private_ip_address" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "public_ip_address" {
  description = "Public IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.public_ip_address
}

output "self_link" {
  description = "Self link of the Cloud SQL instance"
  value       = google_sql_database_instance.main.self_link
}

output "server_ca_cert" {
  description = "Server CA certificate of the Cloud SQL instance"
  value       = google_sql_database_instance.main.server_ca_cert
  sensitive   = true
}

output "database_names" {
  description = "Names of the created databases"
  value       = [for db in google_sql_database.databases : db.name]
}

output "database_users" {
  description = "Names of the created database users"
  value       = [for user in google_sql_user.users : user.name]
}

output "database_passwords" {
  description = "Database user passwords"
  value       = { for k, v in random_password.db_password : k => v.result }
  sensitive   = true
}

output "read_replica_name" {
  description = "Name of the read replica instance"
  value       = var.create_read_replica ? google_sql_database_instance.read_replica[0].name : null
}

output "read_replica_connection_name" {
  description = "Connection name of the read replica instance"
  value       = var.create_read_replica ? google_sql_database_instance.read_replica[0].connection_name : null
}

output "read_replica_private_ip" {
  description = "Private IP address of the read replica"
  value       = var.create_read_replica ? google_sql_database_instance.read_replica[0].private_ip_address : null
}

output "secret_manager_secret_ids" {
  description = "Secret Manager secret IDs for database passwords"
  value       = var.store_passwords_in_secret_manager ? { for k, v in google_secret_manager_secret.db_passwords : k => v.secret_id } : {}
}

# Connection strings for applications
output "jdbc_connection_string" {
  description = "JDBC connection string for applications"
  value       = "jdbc:postgresql://google/${google_sql_database.databases["trading_db"].name}?cloudSqlInstance=${google_sql_database_instance.main.connection_name}&socketFactory=com.google.cloud.sql.postgres.SocketFactory&useSSL=true"
}

output "psql_connection_command" {
  description = "psql connection command"
  value       = "gcloud sql connect ${google_sql_database_instance.main.name} --user=postgres --database=${google_sql_database.databases["trading_db"].name}"
}

output "cloud_sql_proxy_command" {
  description = "Cloud SQL Proxy connection command"
  value       = "cloud_sql_proxy -instances=${google_sql_database_instance.main.connection_name}=tcp:5432"
}