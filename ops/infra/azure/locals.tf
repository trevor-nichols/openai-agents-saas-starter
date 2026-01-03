locals {
  name_prefix        = "${var.project_name}-${var.environment}"
  api_container_port = 8000
  web_container_port = 3000

  secrets_provider          = trimspace(var.secrets_provider)
  auth_key_storage_provider = trimspace(var.auth_key_storage_provider) != "" ? var.auth_key_storage_provider : local.secrets_provider
  auth_key_secret_name      = trimspace(var.auth_key_secret_name)
  api_base_url              = trimspace(var.api_base_url)
  app_public_url            = trimspace(var.app_public_url)
  registry_server           = trimspace(var.registry_server)
  registry_enabled          = local.registry_server != ""

  default_api_host         = "${local.name_prefix}-api.${azurerm_container_app_environment.main.default_domain}"
  default_web_host         = "${local.name_prefix}-web.${azurerm_container_app_environment.main.default_domain}"
  default_api_base_url     = "https://${local.default_api_host}"
  default_app_public_url   = "https://${local.default_web_host}"
  api_base_url_effective   = local.api_base_url != "" ? local.api_base_url : local.default_api_base_url
  app_public_url_effective = local.app_public_url != "" ? local.app_public_url : local.default_app_public_url
  api_base_host            = element(split("/", replace(replace(local.api_base_url_effective, "https://", ""), "http://", "")), 0)
  api_allowed_hosts        = join(",", compact([local.api_base_host, "127.0.0.1", "localhost"]))

  api_env_base = merge(
    {
      PORT                      = tostring(local.api_container_port)
      ENVIRONMENT               = var.environment
      SECRETS_PROVIDER          = local.secrets_provider
      AUTH_KEY_STORAGE_BACKEND  = "secret-manager"
      AUTH_KEY_STORAGE_PROVIDER = local.auth_key_storage_provider
      STORAGE_PROVIDER          = var.storage_provider
      AZURE_BLOB_ACCOUNT_URL    = azurerm_storage_account.main.primary_blob_endpoint
      AZURE_BLOB_CONTAINER      = azurerm_storage_container.main.name
      ALLOWED_HOSTS             = local.api_allowed_hosts
      ALLOWED_ORIGINS           = local.app_public_url_effective
    },
    { APP_PUBLIC_URL = local.app_public_url_effective },
    (local.secrets_provider == "azure_kv" || local.auth_key_storage_provider == "azure_kv") ? {
      AZURE_KEY_VAULT_URL = azurerm_key_vault.main.vault_uri
    } : {},
    local.secrets_provider == "azure_kv" ? {
      AZURE_KV_SIGNING_SECRET_NAME = var.auth_signing_secret_name
    } : {},
    local.auth_key_secret_name != "" ? { AUTH_KEY_SECRET_NAME = local.auth_key_secret_name } : {}
  )

  web_env_base = merge(
    {
      PORT = tostring(local.web_container_port)
    },
    { API_BASE_URL = local.api_base_url_effective }
  )

  api_env_combined = merge(local.api_env_base, var.api_env)
  web_env_combined = merge(local.web_env_base, var.web_env)

  api_secret_list = [
    for key, value in var.api_secrets : { name = key, valueFrom = value }
    if length(trimspace(value)) > 0
  ]

  web_secret_list = [
    for key, value in var.web_secrets : { name = key, valueFrom = value }
    if length(trimspace(value)) > 0
  ]
}
