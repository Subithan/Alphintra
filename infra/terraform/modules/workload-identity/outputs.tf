output "service_accounts" {
  description = "Emails of created Google service accounts."
  value = {
    for name, sa in google_service_account.workload :
    name => sa.email
  }
}
