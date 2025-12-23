resource "azurerm_container_app_environment" "main" {
  name                       = "${local.name_prefix}-cae"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  infrastructure_subnet_id   = var.enable_private_networking ? azurerm_subnet.container_apps[0].id : null
}

resource "azurerm_container_app" "api" {
  name                         = "${local.name_prefix}-api"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  template {
    container {
      name   = "api"
      image  = var.api_image
      cpu    = var.api_cpu
      memory = var.api_memory

      dynamic "env" {
        for_each = local.api_env_combined
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.api_secret_list
        content {
          name        = env.value.name
          secret_name = env.value.name
        }
      }

      liveness_probe {
        transport = "HTTP"
        port      = local.api_container_port
        path      = "/health"
      }

      readiness_probe {
        transport = "HTTP"
        port      = local.api_container_port
        path      = "/health/ready"
      }

      startup_probe {
        transport = "HTTP"
        port      = local.api_container_port
        path      = "/health"
      }
    }
  }

  dynamic "secret" {
    for_each = local.api_secret_list
    content {
      name                = secret.value.name
      identity            = "System"
      key_vault_secret_id = secret.value.valueFrom
    }
  }

  dynamic "secret" {
    for_each = local.registry_enabled && length(trimspace(var.registry_password_secret_id)) > 0 ? { registry_password = var.registry_password_secret_id } : {}
    content {
      name                = "registry-password"
      identity            = "System"
      key_vault_secret_id = secret.value
    }
  }

  dynamic "secret" {
    for_each = local.registry_enabled && length(trimspace(var.registry_password_secret_id)) == 0 ? { registry_password = var.registry_password } : {}
    content {
      name  = "registry-password"
      value = secret.value
    }
  }

  dynamic "registry" {
    for_each = local.registry_enabled ? [1] : []
    content {
      server               = local.registry_server
      username             = var.registry_username
      password_secret_name = "registry-password"
    }
  }

  ingress {
    external_enabled = true
    target_port      = local.api_container_port
    transport        = "auto"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}

resource "azurerm_container_app" "web" {
  name                         = "${local.name_prefix}-web"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  template {
    container {
      name   = "web"
      image  = var.web_image
      cpu    = var.web_cpu
      memory = var.web_memory

      dynamic "env" {
        for_each = local.web_env_combined
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.web_secret_list
        content {
          name        = env.value.name
          secret_name = env.value.name
        }
      }

      liveness_probe {
        transport = "HTTP"
        port      = local.web_container_port
        path      = "/api/health"
      }

      readiness_probe {
        transport = "HTTP"
        port      = local.web_container_port
        path      = "/api/health/ready"
      }

      startup_probe {
        transport = "HTTP"
        port      = local.web_container_port
        path      = "/api/health"
      }
    }
  }

  dynamic "secret" {
    for_each = local.web_secret_list
    content {
      name                = secret.value.name
      identity            = "System"
      key_vault_secret_id = secret.value.valueFrom
    }
  }

  dynamic "secret" {
    for_each = local.registry_enabled && length(trimspace(var.registry_password_secret_id)) > 0 ? { registry_password = var.registry_password_secret_id } : {}
    content {
      name                = "registry-password"
      identity            = "System"
      key_vault_secret_id = secret.value
    }
  }

  dynamic "secret" {
    for_each = local.registry_enabled && length(trimspace(var.registry_password_secret_id)) == 0 ? { registry_password = var.registry_password } : {}
    content {
      name  = "registry-password"
      value = secret.value
    }
  }

  dynamic "registry" {
    for_each = local.registry_enabled ? [1] : []
    content {
      server               = local.registry_server
      username             = var.registry_username
      password_secret_name = "registry-password"
    }
  }

  ingress {
    external_enabled = true
    target_port      = local.web_container_port
    transport        = "auto"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}
