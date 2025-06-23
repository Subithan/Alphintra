terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Notification channels
resource "google_monitoring_notification_channel" "channels" {
  for_each = var.notification_channels

  display_name = each.value.display_name
  type         = each.value.type
  labels       = each.value.labels
  project      = var.project_id

  lifecycle {
    create_before_destroy = true
  }
}

# Alert policies
resource "google_monitoring_alert_policy" "policies" {
  for_each = var.alert_policies

  display_name = each.value.display_name
  project      = var.project_id

  combiner = "OR"

  dynamic "conditions" {
    for_each = each.value.conditions
    content {
      display_name = conditions.value.display_name

      condition_threshold {
        filter          = conditions.value.condition_threshold.filter
        comparison      = conditions.value.condition_threshold.comparison
        threshold_value = conditions.value.condition_threshold.threshold_value
        duration        = conditions.value.condition_threshold.duration

        aggregations {
          alignment_period   = "60s"
          per_series_aligner = "ALIGN_RATE"
        }
      }
    }
  }

  notification_channels = [
    for channel in google_monitoring_notification_channel.channels : channel.name
  ]

  alert_strategy {
    auto_close = "1800s"
  }
}