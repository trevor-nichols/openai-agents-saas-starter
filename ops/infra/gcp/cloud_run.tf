resource "google_cloud_run_v2_service" "api" {
  name     = "${local.name_prefix}-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.runtime.email

    containers {
      image = var.api_image

      ports {
        container_port = local.api_container_port
      }

      resources {
        limits = {
          cpu    = tostring(var.api_cpu)
          memory = var.api_memory
        }
      }

      dynamic "env" {
        for_each = local.api_env_list
        content {
          name  = env.value.name
          value = env.value.value
        }
      }

      dynamic "env" {
        for_each = local.api_secret_list
        content {
          name = env.value.name
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = local.api_container_port
        }
      }

      startup_probe {
        http_get {
          path = "/health/ready"
          port = local.api_container_port
        }
      }
    }

    scaling {
      min_instance_count = var.api_min_instances
      max_instance_count = var.api_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.main.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service" "web" {
  name     = "${local.name_prefix}-web"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.runtime.email

    containers {
      image = var.web_image

      ports {
        container_port = local.web_container_port
      }

      resources {
        limits = {
          cpu    = tostring(var.web_cpu)
          memory = var.web_memory
        }
      }

      dynamic "env" {
        for_each = local.web_env_list
        content {
          name  = env.value.name
          value = env.value.value
        }
      }

      dynamic "env" {
        for_each = local.web_secret_list
        content {
          name = env.value.name
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }

      liveness_probe {
        http_get {
          path = "/api/health"
          port = local.web_container_port
        }
      }

      startup_probe {
        http_get {
          path = "/api/health/ready"
          port = local.web_container_port
        }
      }
    }

    scaling {
      min_instance_count = var.web_min_instances
      max_instance_count = var.web_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.main.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service" "worker" {
  count    = local.worker_enabled ? 1 : 0
  name     = "${local.name_prefix}-worker"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.runtime.email

    containers {
      image = local.worker_image

      ports {
        container_port = local.api_container_port
      }

      resources {
        limits = {
          cpu    = tostring(var.worker_cpu)
          memory = var.worker_memory
        }
      }

      dynamic "env" {
        for_each = local.worker_env_list
        content {
          name  = env.value.name
          value = env.value.value
        }
      }

      dynamic "env" {
        for_each = local.worker_secret_list
        content {
          name = env.value.name
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }
    }

    scaling {
      min_instance_count = var.worker_min_instances
      max_instance_count = var.worker_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.main.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}
