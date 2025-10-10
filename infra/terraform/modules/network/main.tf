resource "google_compute_network" "this" {
  name                    = var.network_name
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = var.routing_mode
}

resource "google_compute_subnetwork" "this" {
  for_each                  = { for subnet in var.subnets : subnet.name => subnet }
  name                      = each.value.name
  project                   = var.project_id
  region                    = each.value.region
  ip_cidr_range             = each.value.ip_cidr_range
  network                   = google_compute_network.this.id
  private_ip_google_access  = true
  stack_type                = "IPV4_ONLY"

  dynamic "secondary_ip_range" {
    for_each = each.value.secondary_ip_ranges
    content {
      range_name    = secondary_ip_range.value.range_name
      ip_cidr_range = secondary_ip_range.value.ip_cidr_range
    }
  }
}
