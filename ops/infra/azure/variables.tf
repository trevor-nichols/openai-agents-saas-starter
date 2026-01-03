variable "project_name" {
  type        = string
  description = "Base project name used for resource naming."
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev/staging/prod)."
}

variable "region" {
  type        = string
  description = "Azure region."
  default     = "eastus"
}

variable "enable_private_networking" {
  type        = bool
  description = "Enable private networking for database/redis via VNet + private endpoints."
  default     = true
}

variable "vnet_address_space" {
  type        = string
  description = "Address space for the VNet."
  default     = "10.30.0.0/16"
}

variable "containerapps_subnet_cidr" {
  type        = string
  description = "CIDR for the Container Apps infrastructure subnet."
  default     = "10.30.0.0/23"
}

variable "postgres_subnet_cidr" {
  type        = string
  description = "CIDR for the Postgres delegated subnet."
  default     = "10.30.2.0/24"
}

variable "private_endpoints_subnet_cidr" {
  type        = string
  description = "CIDR for the private endpoints subnet."
  default     = "10.30.3.0/24"
}

variable "api_image" {
  type        = string
  description = "Container image for the API service."
}

variable "web_image" {
  type        = string
  description = "Container image for the web app."
}

variable "secrets_provider" {
  type        = string
  description = "Secrets provider used by the API service (SECRETS_PROVIDER). Default posture assumes azure_kv."
  default     = "azure_kv"
}

variable "api_base_url" {
  type        = string
  description = "Public API base URL for the web app (e.g. https://api.example.com)."
  default     = ""
}

variable "app_public_url" {
  type        = string
  description = "Public web URL used by the API service (e.g. https://app.example.com)."
  default     = ""
}

variable "registry_server" {
  type        = string
  description = "Container registry server hostname (ghcr.io, <registry>.azurecr.io)."
  default     = ""
}

variable "registry_username" {
  type        = string
  description = "Container registry username (required when registry_server is set)."
  default     = ""
  validation {
    condition     = var.registry_server == "" || length(trimspace(var.registry_username)) > 0
    error_message = "registry_username is required when registry_server is set."
  }
}

variable "registry_password" {
  type        = string
  description = "Container registry password/token (required when registry_server is set)."
  default     = ""
  sensitive   = true
  validation {
    condition     = var.registry_server == "" || length(trimspace(var.registry_password)) > 0 || length(trimspace(var.registry_password_secret_id)) > 0
    error_message = "registry_password or registry_password_secret_id is required when registry_server is set."
  }
}

variable "registry_password_secret_id" {
  type        = string
  description = "Key Vault secret ID containing the registry password/token."
  default     = ""
}

variable "api_cpu" {
  type        = number
  description = "CPU cores for the API container."
  default     = 1
}

variable "api_memory" {
  type        = string
  description = "Memory for the API container (Gi)."
  default     = "2Gi"
}

variable "web_cpu" {
  type        = number
  description = "CPU cores for the web container."
  default     = 1
}

variable "web_memory" {
  type        = string
  description = "Memory for the web container (Gi)."
  default     = "2Gi"
}

variable "db_admin_username" {
  type        = string
  description = "Postgres admin username."
  default     = "agent_admin"
}

variable "db_admin_password" {
  type        = string
  description = "Postgres admin password."
  sensitive   = true
}

variable "db_public_network_access_enabled" {
  type        = bool
  description = "Allow public network access to Postgres (not recommended)."
  default     = false
}

variable "db_name" {
  type        = string
  description = "Postgres database name."
  default     = "agent_app"
}

variable "redis_sku_name" {
  type        = string
  description = "Redis SKU name."
  default     = "Standard"
  validation {
    condition     = !(var.enable_private_networking && var.redis_sku_name == "Basic")
    error_message = "redis_sku_name must be Standard or Premium when enable_private_networking=true."
  }
}

variable "redis_capacity" {
  type        = number
  description = "Redis capacity tier."
  default     = 0
}

variable "redis_public_network_access_enabled" {
  type        = bool
  description = "Allow public network access to Redis (not recommended)."
  default     = false
}

variable "storage_account_name" {
  type        = string
  description = "Storage account name for Blob storage (must be globally unique)."
}

variable "storage_bucket_name" {
  type        = string
  description = "Blob container name for object storage."
  default     = "assets"
}

variable "storage_provider" {
  type        = string
  description = "Storage provider for the API service (STORAGE_PROVIDER)."
  default     = "azure_blob"
  validation {
    condition     = var.storage_provider == "azure_blob"
    error_message = "storage_provider must be \"azure_blob\" for the Azure blueprint."
  }
}

variable "key_vault_name" {
  type        = string
  description = "Key Vault name (must be globally unique)."
}

variable "log_analytics_name" {
  type        = string
  description = "Log Analytics workspace name."
}

variable "auth_signing_secret_name" {
  type        = string
  description = "Key Vault secret name containing the signing secret."
  default     = ""
  validation {
    condition = (
      var.secrets_provider != "azure_kv"
      || length(trimspace(var.auth_signing_secret_name)) > 0
      || contains(keys(var.api_env), "AZURE_KV_SIGNING_SECRET_NAME")
      || contains(keys(var.api_secrets), "AZURE_KV_SIGNING_SECRET_NAME")
    )
    error_message = "auth_signing_secret_name is required when secrets_provider=azure_kv (or provide AZURE_KV_SIGNING_SECRET_NAME via api_env/api_secrets)."
  }
}

variable "auth_key_secret_name" {
  type        = string
  description = "Key Vault secret name for the Ed25519 keyset JSON (AUTH_KEY_SECRET_NAME)."
  default     = ""
  validation {
    condition = (
      length(trimspace(var.auth_key_secret_name)) > 0
      || contains(keys(var.api_env), "AUTH_KEY_SECRET_NAME")
      || contains(keys(var.api_secrets), "AUTH_KEY_SECRET_NAME")
    )
    error_message = "auth_key_secret_name is required for secret-manager key storage (or provide AUTH_KEY_SECRET_NAME via api_env/api_secrets)."
  }
}

variable "auth_key_storage_provider" {
  type        = string
  description = "Secrets provider used for key storage (AUTH_KEY_STORAGE_PROVIDER). Defaults to secrets_provider."
  default     = ""
}

variable "api_env" {
  type        = map(string)
  description = "Additional environment variables for the API container."
  default     = {}
  validation {
    condition = (
      !contains(keys(var.api_env), "DATABASE_URL")
      && !contains(keys(var.api_env), "REDIS_URL")
    )
    error_message = "DATABASE_URL and REDIS_URL must be provided via api_secrets, not api_env."
  }
}

variable "web_env" {
  type        = map(string)
  description = "Additional environment variables for the web container."
  default     = {}
}

variable "api_secrets" {
  type        = map(string)
  description = "Map of API secret env var name to Key Vault secret ID."
  default = {
    DATABASE_URL = ""
    REDIS_URL    = ""
  }
  sensitive = true
  validation {
    condition = (
      length(trimspace(lookup(var.api_secrets, "DATABASE_URL", ""))) > 0
      && length(trimspace(lookup(var.api_secrets, "REDIS_URL", ""))) > 0
    )
    error_message = "api_secrets must provide DATABASE_URL and REDIS_URL secret IDs for production deployments."
  }
}

variable "web_secrets" {
  type        = map(string)
  description = "Map of web secret env var name to Key Vault secret ID."
  default     = {}
  sensitive   = true
}
