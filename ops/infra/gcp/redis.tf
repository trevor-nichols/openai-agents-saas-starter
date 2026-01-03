resource "google_redis_instance" "main" {
  name                    = local.redis_instance_name
  region                  = var.region
  tier                    = upper(var.redis_tier)
  memory_size_gb          = var.redis_memory_size_gb
  redis_version           = var.redis_version
  authorized_network      = google_compute_network.main.id
  connect_mode            = var.enable_private_service_access ? "PRIVATE_SERVICE_ACCESS" : "DIRECT_PEERING"
  reserved_ip_range       = var.enable_private_service_access ? google_compute_global_address.private_services_range[0].name : null
  auth_enabled            = var.redis_auth_enabled
  transit_encryption_mode = upper(var.redis_transit_encryption_mode)

  depends_on = [google_service_networking_connection.private_services]
}
