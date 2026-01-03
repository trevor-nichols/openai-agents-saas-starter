resource "google_sql_database_instance" "main" {
  name             = "${local.name_prefix}-pg"
  database_version = "POSTGRES_16"
  region           = var.region

  deletion_protection = var.db_deletion_protection

  settings {
    tier              = var.db_tier
    disk_type         = var.db_disk_type
    disk_size         = var.db_disk_size_gb
    disk_autoresize   = var.db_disk_autoresize
    availability_type = upper(var.db_availability_type)

    ip_configuration {
      ipv4_enabled    = var.db_public_ipv4_enabled
      private_network = var.enable_private_service_access ? google_compute_network.main.id : null
    }

    backup_configuration {
      enabled                        = var.db_backup_enabled
      start_time                     = var.db_backup_start_time
      point_in_time_recovery_enabled = var.db_backup_enabled && var.db_point_in_time_recovery_enabled

      dynamic "backup_retention_settings" {
        for_each = var.db_backup_enabled ? [1] : []
        content {
          retained_backups = var.db_backup_retention_count
          retention_unit   = "COUNT"
        }
      }
    }
  }

  depends_on = [google_service_networking_connection.private_services]
}

resource "google_sql_database" "main" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "main" {
  name     = var.db_username
  instance = google_sql_database_instance.main.name
  password = var.db_password
}
