locals {
  wi_project = coalesce(var.workload_identity_project, var.project_id)

  account_roles = flatten([
    for sa in var.service_accounts : [
      for role in sa.roles : {
        key  = "${sa.name}:${role}"
        name = sa.name
        role = role
      }
    ]
  ])

  workload_identity_pairs = flatten([
    for sa in var.service_accounts : [
      for ksa in lookup(sa, "kubernetes_service_accounts", []) : {
        key       = "${sa.name}:${ksa.namespace}/${ksa.name}"
        name      = sa.name
        namespace = ksa.namespace
        ksa_name  = ksa.name
      }
    ]
  ])
}

resource "google_service_account" "workload" {
  for_each     = { for sa in var.service_accounts : sa.name => sa }
  project      = var.project_id
  account_id   = each.value.account_id
  display_name = each.value.display_name
  description  = try(each.value.description, null)
}

resource "google_project_iam_member" "workload_roles" {
  for_each = { for item in local.account_roles : item.key => item }
  project  = var.project_id
  role     = each.value.role
  member   = "serviceAccount:${google_service_account.workload[each.value.name].email}"
}

resource "google_service_account_iam_member" "workload_identity" {
  for_each = { for item in local.workload_identity_pairs : item.key => item }

  service_account_id = google_service_account.workload[each.value.name].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${local.wi_project}.svc.id.goog[${each.value.namespace}/${each.value.ksa_name}]"
}
