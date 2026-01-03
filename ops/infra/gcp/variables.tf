variable "project_name" {
  type        = string
  description = "Base project name used for resource naming."
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev/staging/prod)."
}

variable "project_id" {
  type        = string
  description = "GCP project ID hosting the resources."
}

variable "gcp_sm_project_id" {
  type        = string
  description = "Optional GCP project ID hosting Secret Manager secrets when different from project_id."
  default     = ""
}

variable "region" {
  type        = string
  description = "GCP region for Cloud Run and managed services."
  default     = "us-central1"
}

variable "enable_project_services" {
  type        = bool
  description = "Enable required GCP APIs (Cloud Run, Cloud SQL, Secret Manager, Memorystore, Storage, IAM, VPC access, Service Networking)."
  default     = true
}

variable "vpc_subnet_cidr" {
  type        = string
  description = "CIDR range for the primary VPC subnet."
  default     = "10.30.0.0/16"
}

variable "vpc_connector_cidr" {
  type        = string
  description = "CIDR range for the Serverless VPC Access connector."
  default     = "10.8.0.0/28"
}

variable "enable_private_service_access" {
  type        = bool
  description = "Enable Private Service Access for Cloud SQL and Memorystore."
  default     = true
}

variable "private_service_cidr_prefix" {
  type        = number
  description = "CIDR prefix length for the Private Service Access range."
  default     = 16
  validation {
    condition     = var.private_service_cidr_prefix >= 16 && var.private_service_cidr_prefix <= 24
    error_message = "private_service_cidr_prefix must be between 16 and 24."
  }
}

variable "api_image" {
  type        = string
  description = "Container image for the API service."
}

variable "web_image" {
  type        = string
  description = "Container image for the web app."
}

variable "worker_image" {
  type        = string
  description = "Optional worker image (defaults to api_image when empty)."
  default     = ""
}

variable "enable_worker_service" {
  type        = bool
  description = "Deploy a dedicated worker service for billing retries."
  default     = false
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

variable "worker_cpu" {
  type        = number
  description = "CPU cores for the worker container."
  default     = 1
}

variable "worker_memory" {
  type        = string
  description = "Memory for the worker container (Gi)."
  default     = "2Gi"
}

variable "api_min_instances" {
  type        = number
  description = "Minimum number of API instances."
  default     = 0
}

variable "api_max_instances" {
  type        = number
  description = "Maximum number of API instances."
  default     = 10
  validation {
    condition     = var.api_max_instances >= var.api_min_instances
    error_message = "api_max_instances must be >= api_min_instances."
  }
}

variable "web_min_instances" {
  type        = number
  description = "Minimum number of web instances."
  default     = 0
}

variable "web_max_instances" {
  type        = number
  description = "Maximum number of web instances."
  default     = 10
  validation {
    condition     = var.web_max_instances >= var.web_min_instances
    error_message = "web_max_instances must be >= web_min_instances."
  }
}

variable "worker_min_instances" {
  type        = number
  description = "Minimum number of worker instances."
  default     = 0
}

variable "worker_max_instances" {
  type        = number
  description = "Maximum number of worker instances."
  default     = 5
  validation {
    condition     = var.worker_max_instances >= var.worker_min_instances
    error_message = "worker_max_instances must be >= worker_min_instances."
  }
}

variable "api_base_url" {
  type        = string
  description = "Public API base URL for the web app (e.g. https://api.example.com)."
  default     = ""
  validation {
    condition     = length(trimspace(var.api_base_url)) > 0
    error_message = "api_base_url must be set for Cloud Run deployments."
  }
}

variable "app_public_url" {
  type        = string
  description = "Public web URL used by the API service (e.g. https://app.example.com)."
  default     = ""
  validation {
    condition     = length(trimspace(var.app_public_url)) > 0
    error_message = "app_public_url must be set for Cloud Run deployments."
  }
}

variable "secrets_provider" {
  type        = string
  description = "Secrets provider used by the API service (SECRETS_PROVIDER). Default posture assumes gcp_sm."
  default     = "gcp_sm"
}

variable "auth_key_storage_provider" {
  type        = string
  description = "Secrets provider used for key storage (AUTH_KEY_STORAGE_PROVIDER). Defaults to secrets_provider."
  default     = ""
}

variable "auth_key_secret_name" {
  type        = string
  description = "Secret Manager name for the Ed25519 keyset JSON (AUTH_KEY_SECRET_NAME)."
  default     = ""
  validation {
    condition = (
      (trimspace(var.auth_key_storage_provider) != "" ? var.auth_key_storage_provider : var.secrets_provider) != "gcp_sm"
      || length(trimspace(var.auth_key_secret_name)) > 0
      || contains(keys(var.api_env), "AUTH_KEY_SECRET_NAME")
      || contains(keys(var.api_secrets), "AUTH_KEY_SECRET_NAME")
    )
    error_message = "auth_key_secret_name is required when auth_key_storage_provider=gcp_sm (or provide AUTH_KEY_SECRET_NAME via api_env/api_secrets)."
  }
}

variable "gcp_sm_signing_secret_name" {
  type        = string
  description = "Secret Manager secret name containing the signing secret."
  default     = ""
  validation {
    condition = (
      var.secrets_provider != "gcp_sm"
      || length(trimspace(var.gcp_sm_signing_secret_name)) > 0
      || contains(keys(var.api_env), "GCP_SM_SIGNING_SECRET_NAME")
      || contains(keys(var.api_secrets), "GCP_SM_SIGNING_SECRET_NAME")
    )
    error_message = "gcp_sm_signing_secret_name is required when secrets_provider=gcp_sm (or provide GCP_SM_SIGNING_SECRET_NAME via api_env/api_secrets)."
  }
}

variable "storage_provider" {
  type        = string
  description = "Storage provider for the API service (STORAGE_PROVIDER)."
  default     = "gcs"
  validation {
    condition     = var.storage_provider == "gcs"
    error_message = "storage_provider must be \"gcs\" for the GCP blueprint."
  }
}

variable "storage_bucket_name" {
  type        = string
  description = "GCS bucket name for object storage."
  default     = "assets"
}

variable "storage_location" {
  type        = string
  description = "GCS bucket location (defaults to region)."
  default     = ""
}

variable "storage_uniform_access" {
  type        = bool
  description = "Enable uniform bucket-level access."
  default     = true
}

variable "storage_versioning_enabled" {
  type        = bool
  description = "Enable object versioning."
  default     = true
}

variable "storage_force_destroy" {
  type        = bool
  description = "Allow bucket deletion with objects (dev only)."
  default     = false
}

variable "api_env" {
  type        = map(string)
  description = "Additional non-sensitive env vars for the API service."
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
  description = "Additional non-sensitive env vars for the web service."
  default     = {}
}

variable "api_secrets" {
  type        = map(string)
  description = "Secret references for the API service (Secret Manager resource IDs)."
  default = {
    DATABASE_URL = ""
    REDIS_URL    = ""
  }
  validation {
    condition = (
      length(trimspace(lookup(var.api_secrets, "DATABASE_URL", ""))) > 0
      && length(trimspace(lookup(var.api_secrets, "REDIS_URL", ""))) > 0
    )
    error_message = "api_secrets must provide DATABASE_URL and REDIS_URL secret names for production deployments."
  }
}

variable "web_secrets" {
  type        = map(string)
  description = "Secret references for the web service (Secret Manager resource IDs)."
  default     = {}
  sensitive   = true
}

variable "registry_server" {
  type        = string
  description = "Container registry server hostname (ghcr.io, <registry>.pkg.dev)."
  default     = ""
}

variable "registry_username" {
  type        = string
  description = "Container registry username (required for non-native registries)."
  default     = ""
}

variable "registry_password" {
  type        = string
  description = "Container registry password/token (required for non-native registries)."
  default     = ""
  sensitive   = true
}

variable "db_name" {
  type        = string
  description = "Postgres database name."
  default     = "agent_app"
}

variable "db_username" {
  type        = string
  description = "Postgres admin username."
  default     = "agent_admin"
}

variable "db_password" {
  type        = string
  description = "Postgres admin password."
  sensitive   = true
  validation {
    condition     = length(trimspace(var.db_password)) > 0
    error_message = "db_password must be set for Cloud SQL Postgres."
  }
}

variable "db_tier" {
  type        = string
  description = "Cloud SQL machine tier."
  default     = "db-custom-1-3840"
}

variable "db_disk_type" {
  type        = string
  description = "Cloud SQL disk type."
  default     = "PD_SSD"
}

variable "db_disk_size_gb" {
  type        = number
  description = "Cloud SQL disk size (GB)."
  default     = 50
}

variable "db_disk_autoresize" {
  type        = bool
  description = "Enable automatic disk resize."
  default     = true
}

variable "db_availability_type" {
  type        = string
  description = "Availability type (ZONAL or REGIONAL)."
  default     = "ZONAL"
  validation {
    condition     = contains(["ZONAL", "REGIONAL"], upper(var.db_availability_type))
    error_message = "db_availability_type must be ZONAL or REGIONAL."
  }
}

variable "db_backup_enabled" {
  type        = bool
  description = "Enable Cloud SQL automated backups."
  default     = true
}

variable "db_backup_start_time" {
  type        = string
  description = "Backup start time (HH:MM, UTC)."
  default     = "03:00"
}

variable "db_backup_retention_count" {
  type        = number
  description = "Number of backups to retain."
  default     = 7
}

variable "db_point_in_time_recovery_enabled" {
  type        = bool
  description = "Enable point-in-time recovery."
  default     = true
}

variable "db_deletion_protection" {
  type        = bool
  description = "Prevent accidental deletion of the Cloud SQL instance."
  default     = true
}

variable "db_public_ipv4_enabled" {
  type        = bool
  description = "Expose Cloud SQL via public IPv4 (not recommended)."
  default     = false
  validation {
    condition     = var.enable_private_service_access || var.db_public_ipv4_enabled
    error_message = "db_public_ipv4_enabled must be true when enable_private_service_access=false."
  }
}

variable "redis_tier" {
  type        = string
  description = "Memorystore tier (BASIC or STANDARD_HA)."
  default     = "BASIC"
  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], upper(var.redis_tier))
    error_message = "redis_tier must be BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size_gb" {
  type        = number
  description = "Memorystore memory size in GB."
  default     = 1
  validation {
    condition     = var.redis_memory_size_gb >= 1
    error_message = "redis_memory_size_gb must be at least 1."
  }
}

variable "redis_version" {
  type        = string
  description = "Memorystore Redis version."
  default     = "REDIS_7_0"
}

variable "redis_auth_enabled" {
  type        = bool
  description = "Enable Redis AUTH."
  default     = true
}

variable "redis_transit_encryption_mode" {
  type        = string
  description = "Transit encryption mode for Redis (SERVER_AUTHENTICATION or DISABLED)."
  default     = "SERVER_AUTHENTICATION"
  validation {
    condition     = contains(["SERVER_AUTHENTICATION", "DISABLED"], upper(var.redis_transit_encryption_mode))
    error_message = "redis_transit_encryption_mode must be SERVER_AUTHENTICATION or DISABLED."
  }
}
