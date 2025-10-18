variable "project_id" {
  description = "GCP project id"
  type        = string
}

variable "instance_name" {
  description = "Existing Cloud SQL instance name"
  type        = string
}

variable "database_name" {
  description = "Database name to create"
  type        = string
}

variable "db_user" {
  description = "Database user to create"
  type        = string
}

variable "db_password" {
  description = "Password for database user"
  type        = string
  sensitive   = true
}

variable "secret_name" {
  description = "Secret Manager secret name to store DB password"
  type        = string
}

variable "charset" {
  description = "Database charset"
  type        = string
  default     = "UTF8"
}

variable "collation" {
  description = "Database collation"
  type        = string
  default     = "en_US.UTF8"
}
