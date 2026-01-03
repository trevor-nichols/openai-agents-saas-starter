resource "google_project_service" "required" {
  for_each = var.enable_project_services ? local.required_project_services : toset([])

  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "main" {
  name                    = local.network_name
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
  description             = "VPC network for ${local.name_prefix}."

  depends_on = [google_project_service.required]
}

resource "google_compute_subnetwork" "main" {
  name                     = local.subnet_name
  ip_cidr_range            = var.vpc_subnet_cidr
  region                   = var.region
  network                  = google_compute_network.main.id
  private_ip_google_access = true
  description              = "Primary subnet for ${local.name_prefix}."

  depends_on = [google_project_service.required]
}

resource "google_vpc_access_connector" "main" {
  name          = local.vpc_connector_name
  region        = var.region
  network       = google_compute_network.main.name
  ip_cidr_range = var.vpc_connector_cidr

  depends_on = [google_project_service.required]
}

resource "google_compute_global_address" "private_services_range" {
  count = var.enable_private_service_access ? 1 : 0

  name          = local.private_service_range_name
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = var.private_service_cidr_prefix
  network       = google_compute_network.main.id
  description   = "Private Service Access range for ${local.name_prefix}."

  depends_on = [google_project_service.required]
}

resource "google_service_networking_connection" "private_services" {
  count = var.enable_private_service_access ? 1 : 0

  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_services_range[0].name]

  depends_on = [google_project_service.required]
}
